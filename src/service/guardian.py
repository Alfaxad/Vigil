"""
Guardian service — register wallets for continuous monitoring.
Manages monitored agents, human operators, and API keys.
"""
import hashlib
import secrets
import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional

logger = logging.getLogger("vigil.guardian")


@dataclass
class MonitoredAgent:
    wallet_address: str
    agent_name: str
    agent_task: str = ""
    policy_id: Optional[str] = None
    registered_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    status: str = "active"
    total_audits: int = 0
    last_audit: Optional[datetime] = None


@dataclass
class HumanOperator:
    api_key: str
    name: str = ""
    email: str = ""
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    agents: list[str] = field(default_factory=list)  # wallet addresses

    @property
    def api_key_prefix(self) -> str:
        return self.api_key[:12] + "..."


def generate_api_key() -> str:
    return "vgl_" + secrets.token_hex(24)


class GuardianRegistry:
    def __init__(self):
        self._agents: dict[str, MonitoredAgent] = {}
        self._operators: dict[str, HumanOperator] = {}  # keyed by api_key
        self._key_to_operator: dict[str, str] = {}  # api_key -> operator id

    def register_operator(self, name: str = "", email: str = "") -> dict:
        api_key = generate_api_key()
        operator = HumanOperator(
            api_key=api_key,
            name=name,
            email=email,
        )
        op_id = hashlib.sha256(api_key.encode()).hexdigest()[:16]
        self._operators[op_id] = operator
        self._key_to_operator[api_key] = op_id

        logger.info(f"Operator registered: {name or 'anonymous'} ({op_id})")

        return {
            "api_key": api_key,
            "api_key_prefix": operator.api_key_prefix,
            "operator_id": op_id,
            "message": "Save your API key. If lost, use POST /api/regenerate-key with your operator_id to get a new one.",
        }

    def regenerate_key(self, operator_id: str) -> dict:
        """Regenerate API key for an existing operator without re-registering."""
        operator = self._operators.get(operator_id)
        if not operator:
            return {"error": "Operator not found", "status": 404}

        # Remove old key mapping
        old_key = operator.api_key
        self._key_to_operator.pop(old_key, None)

        # Generate new key
        new_key = generate_api_key()
        operator.api_key = new_key
        self._key_to_operator[new_key] = operator_id

        logger.info(f"Key regenerated for operator {operator_id}")

        return {
            "api_key": new_key,
            "api_key_prefix": operator.api_key_prefix,
            "operator_id": operator_id,
            "message": "New API key generated. Your old key is now invalid.",
        }

    def get_operator_by_key(self, api_key: str) -> Optional[HumanOperator]:
        op_id = self._key_to_operator.get(api_key)
        if op_id:
            return self._operators.get(op_id)
        return None

    def register_agent(
        self,
        api_key: str,
        wallet_address: str,
        agent_name: str,
        agent_task: str = "",
    ) -> dict:
        operator = self.get_operator_by_key(api_key)
        if not operator:
            return {"error": "Invalid API key", "status": 401}

        addr = wallet_address.lower()
        agent = MonitoredAgent(
            wallet_address=addr,
            agent_name=agent_name,
            agent_task=agent_task,
        )
        self._agents[addr] = agent
        operator.agents.append(addr)

        logger.info(f"Agent registered for monitoring: {agent_name} ({addr[:12]}...)")

        return {
            "wallet_address": addr,
            "agent_name": agent_name,
            "status": "active",
            "dashboard_url": f"/dashboard/{addr}",
            "message": f"Vigil is now monitoring {agent_name}. View the dashboard or query /api/audits/{addr} for results.",
        }

    def get_agent(self, wallet_address: str) -> Optional[MonitoredAgent]:
        return self._agents.get((wallet_address or "").lower())

    def get_operator_agents(self, api_key: str) -> list[dict]:
        operator = self.get_operator_by_key(api_key)
        if not operator:
            return []
        result = []
        for addr in operator.agents:
            agent = self._agents.get(addr)
            if agent:
                result.append({
                    "wallet_address": agent.wallet_address,
                    "agent_name": agent.agent_name,
                    "status": agent.status,
                    "total_audits": agent.total_audits,
                    "last_audit": agent.last_audit.isoformat() if agent.last_audit else None,
                    "registered_at": agent.registered_at.isoformat(),
                })
        return result

    def record_audit(self, api_key: str, verdict: str):
        """Record an audit against the operator's agents."""
        operator = self.get_operator_by_key(api_key)
        if not operator or not operator.agents:
            return
        # Update the first agent's stats (most recent registered)
        for addr in operator.agents:
            agent = self._agents.get(addr)
            if agent:
                agent.total_audits += 1
                agent.last_audit = datetime.now(timezone.utc)

    def get_stats(self) -> dict:
        return {
            "total_operators": len(self._operators),
            "total_monitored_agents": len(self._agents),
            "active_agents": sum(
                1 for a in self._agents.values() if a.status == "active"
            ),
        }
