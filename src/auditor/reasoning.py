import json
import logging
from src.locus.client import LocusClient
from src.locus.models import Transaction
from src.auditor.models import TxFeatures, AuditResult, Verdict

logger = logging.getLogger("vigil.reasoning")

SYSTEM_PROMPT = """You are Vigil, a transaction auditor for autonomous AI agent wallets.

You receive flagged transactions along with context about the agent's
stated task, recent transaction history, and counterparty information.

Your job: determine whether this transaction is consistent with the
agent's authorized behavior, or whether it represents anomalous,
unauthorized, or potentially compromised activity.

Respond with ONLY a JSON object:
{
  "verdict": "APPROVE" | "FLAG" | "BLOCK",
  "risk_score": 0.0-1.0,
  "reasoning": "2-3 sentence explanation",
  "evidence": ["list", "of", "specific", "concerns"],
  "recommended_action": "what the human should do"
}"""


def build_prompt(
    tx: Transaction,
    features: TxFeatures,
    statistical_score: float,
    agent_name: str,
    agent_task: str,
    history: list[Transaction],
    balance: float = 0.0,
) -> str:
    # Format recent history
    history_lines = []
    recent = history[-20:] if len(history) > 20 else history
    for h in recent:
        history_lines.append(
            f"  - {h.timestamp}: {h.amount} USDC to {h.to_address or 'unknown'} "
            f"({h.memo or 'no memo'})"
        )
    history_str = "\n".join(history_lines) if history_lines else "  No history available"

    # Count counterparty interactions
    cp_count = sum(1 for h in history if h.to_address == tx.to_address)
    first_seen = "never"
    for h in history:
        if h.to_address == tx.to_address and h.timestamp:
            first_seen = str(h.timestamp)
            break

    # Build anomaly details
    anomalies = []
    if abs(features.amount_zscore) > 2:
        anomalies.append(f"Amount z-score: {features.amount_zscore:.2f} (>2 std devs from mean)")
    if features.counterparty_novelty > 0.8:
        anomalies.append(f"Counterparty novelty: {features.counterparty_novelty:.2f} (rarely or never seen)")
    if features.hour_anomaly > 0.7:
        anomalies.append(f"Hour anomaly: {features.hour_anomaly:.2f} (unusual time of day)")
    if features.amount_velocity_1h > 2:
        anomalies.append(f"1h velocity: {features.amount_velocity_1h:.2f}x normal spending rate")
    if features.time_delta_zscore > 2:
        anomalies.append(f"Time delta z-score: {features.time_delta_zscore:.2f} (unusual timing)")

    anomaly_str = "\n".join(f"- {a}" for a in anomalies) if anomalies else "- None specific"

    return f"""## Flagged Transaction
- Amount: {tx.amount} USDC
- To: {tx.to_address or 'unknown'}
- Memo: {tx.memo or 'none'}
- Timestamp: {tx.timestamp}
- Statistical risk score: {statistical_score:.4f}

## Agent Context
- Agent name: {agent_name}
- Stated task: {agent_task or 'not specified'}
- Wallet balance before: {balance} USDC

## Recent Transaction History (last {len(recent)})
{history_str}

## Counterparty Profile
- First seen: {first_seen}
- Total transactions with this agent: {cp_count}

## Statistical Anomalies Detected
{anomaly_str}"""


async def invoke_claude(
    locus: LocusClient,
    tx: Transaction,
    features: TxFeatures,
    statistical_score: float,
    agent_name: str,
    agent_task: str,
    history: list[Transaction],
) -> AuditResult:
    prompt = build_prompt(
        tx, features, statistical_score, agent_name, agent_task, history
    )

    try:
        response_text = await locus.call_claude(
            messages=[{"role": "user", "content": prompt}],
            max_tokens=500,
            system=SYSTEM_PROMPT,
        )

        # Parse JSON response
        # Handle potential markdown code blocks
        text = response_text.strip()
        if text.startswith("```"):
            text = text.split("\n", 1)[1] if "\n" in text else text[3:]
            text = text.rsplit("```", 1)[0]

        data = json.loads(text)

        return AuditResult(
            tx_hash=tx.tx_hash,
            statistical_score=statistical_score,
            features=features,
            verdict=Verdict(data.get("verdict", "FLAG")),
            risk_score=float(data.get("risk_score", statistical_score)),
            reasoning=data.get("reasoning", ""),
            evidence=data.get("evidence", []),
            recommended_action=data.get("recommended_action", ""),
            layer2_invoked=True,
        )

    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse Claude response: {e}")
        return AuditResult(
            tx_hash=tx.tx_hash,
            statistical_score=statistical_score,
            features=features,
            verdict=Verdict.FLAG,
            risk_score=statistical_score,
            reasoning=f"Claude response could not be parsed. Statistical score: {statistical_score:.3f}",
            evidence=["parse_error"],
            recommended_action="Manual review recommended",
            layer2_invoked=True,
        )

    except Exception as e:
        logger.error(f"Claude reasoning failed: {e}")
        return AuditResult(
            tx_hash=tx.tx_hash,
            statistical_score=statistical_score,
            features=features,
            verdict=Verdict.FLAG if statistical_score > 0.5 else Verdict.APPROVE,
            risk_score=statistical_score,
            reasoning=f"Layer 2 unavailable. Falling back to statistical score: {statistical_score:.3f}",
            evidence=["layer2_unavailable"],
            recommended_action="Review manually — Claude reasoning unavailable",
            layer2_invoked=False,
        )
