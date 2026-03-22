"""
Natural language policy engine.
Humans define agent rules in plain English. Claude structures them.
"""
import json
import logging
from dataclasses import dataclass, field
from typing import Optional
from src.locus.client import LocusClient

logger = logging.getLogger("vigil.policy")

POLICY_SYSTEM_PROMPT = """You are Vigil's policy engine. You translate a human's natural language description of what their agent is allowed to do into a structured policy document.

Given a policy description, produce a JSON object with this structure:
{
  "hard_rules": [
    {"action": "bridge", "verdict": "BLOCK", "alert": true, "reason": "Human explicitly blocked bridges"}
  ],
  "allowed_actions": [
    {"action": "swap", "protocols": ["uniswap-v2", "uniswap-v3"], "constraints": {}}
  ],
  "scrutiny_levels": {
    "known_bluechip": "low",
    "known_other": "medium",
    "unknown": "high"
  },
  "limits": {
    "daily": null,
    "per_transaction": null
  },
  "notes": "Any clarifications or suggestions for the human"
}

Rules:
- Extract explicit restrictions as hard_rules (always blocked)
- Extract permitted actions as allowed_actions
- Infer scrutiny levels from the human's tone and specificity
- If limits aren't specified, leave them null and mention it in notes
- Be precise about which protocols are mentioned
- If the human is vague, err on the side of more restrictive interpretation

Respond with ONLY the JSON object."""


@dataclass
class AgentPolicy:
    agent_address: str
    policy_text: str
    structured_policy: dict = field(default_factory=dict)
    created_at: Optional[str] = None
    policy_id: str = ""


class PolicyEngine:
    def __init__(self, locus_client: LocusClient):
        self.locus = locus_client
        self._policies: dict[str, AgentPolicy] = {}

    async def create_policy(self, agent_address: str, policy_text: str) -> dict:
        prompt = f"""The human has described their agent's policy:

"{policy_text}"

The agent's address is: {agent_address}

Translate this into a structured policy document."""

        try:
            response = await self.locus.call_claude(
                messages=[{"role": "user", "content": prompt}],
                max_tokens=800,
                system=POLICY_SYSTEM_PROMPT,
            )

            text = response.strip()
            if text.startswith("```"):
                text = text.split("\n", 1)[1] if "\n" in text else text[3:]
                text = text.rsplit("```", 1)[0]

            structured = json.loads(text)

        except (json.JSONDecodeError, Exception) as e:
            logger.error(f"Policy parsing failed: {e}")
            structured = {
                "hard_rules": [],
                "allowed_actions": [],
                "scrutiny_levels": {"unknown": "high"},
                "limits": {"daily": None, "per_transaction": None},
                "notes": f"Policy could not be fully parsed. Raw text preserved. Error: {str(e)}",
            }

        from datetime import datetime, timezone

        policy = AgentPolicy(
            agent_address=agent_address,
            policy_text=policy_text,
            structured_policy=structured,
            created_at=datetime.now(timezone.utc).isoformat(),
            policy_id=f"pol_{agent_address[:8]}_{int(datetime.now(timezone.utc).timestamp())}",
        )

        self._policies[agent_address.lower()] = policy

        return {
            "policy_id": policy.policy_id,
            "agent_address": agent_address,
            "structured_policy": structured,
            "vigil_notes": structured.get("notes", ""),
            "cost_usdc": 0.10,
        }

    def get_policy(self, agent_address: str) -> Optional[AgentPolicy]:
        return self._policies.get((agent_address or "").lower())

    def check_hard_rules(self, to_address: str, amount: float, memo: str) -> dict:
        """Check all policies' hard rules against a transaction. Returns {"blocked": bool, "reason": str}."""
        for addr, policy in self._policies.items():
            if not policy.structured_policy:
                continue
            for rule in policy.structured_policy.get("hard_rules", []):
                rule_text = rule.get("condition", "").lower()
                # Amount-based rules
                if "amount" in rule_text or "$" in rule_text:
                    try:
                        import re
                        nums = re.findall(r'[\d,]+\.?\d*', rule_text)
                        if nums:
                            limit = float(nums[-1].replace(",", ""))
                            if ("exceed" in rule_text or "over" in rule_text or "above" in rule_text) and amount > limit:
                                return {"blocked": True, "reason": rule.get("reason", f"Amount ${amount} exceeds policy limit ${limit}")}
                    except (ValueError, IndexError):
                        pass
                # Keyword-based rules
                if "block" in rule_text and any(kw in (memo or "").lower() for kw in ["bridge", "unknown", "mixer"]):
                    if any(kw in rule_text for kw in ["bridge", "unknown", "mixer"]):
                        return {"blocked": True, "reason": rule.get("reason", f"Transaction type blocked by policy")}
        return {"blocked": False}

    def get_all_policies(self) -> list[dict]:
        """Return all policies for display."""
        return [
            {
                "agent_address": p.agent_address,
                "policy_text": p.policy_text,
                "type": p.policy_type,
                "active": p.active,
                "created_at": p.created_at.isoformat(),
            }
            for p in self._policies.values()
        ]
