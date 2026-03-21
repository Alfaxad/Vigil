from dataclasses import dataclass, field
from enum import Enum
from typing import Optional
from datetime import datetime


class Verdict(str, Enum):
    APPROVE = "APPROVE"
    FLAG = "FLAG"
    BLOCK = "BLOCK"


class RiskLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class TxFeatures:
    amount_zscore: float = 0.0
    time_delta_zscore: float = 0.0
    counterparty_novelty: float = 0.0
    amount_velocity_1h: float = 0.0
    amount_velocity_6h: float = 0.0
    amount_velocity_24h: float = 0.0
    gas_price_ratio: float = 0.0
    hour_anomaly: float = 0.0


@dataclass
class AuditResult:
    tx_hash: Optional[str] = None
    statistical_score: float = 0.0
    features: Optional[TxFeatures] = None
    verdict: Verdict = Verdict.APPROVE
    risk_score: float = 0.0
    reasoning: str = ""
    evidence: list[str] = field(default_factory=list)
    recommended_action: str = ""
    attestation_tx: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.utcnow)
    layer2_invoked: bool = False

    @property
    def risk_level(self) -> RiskLevel:
        if self.risk_score < 0.3:
            return RiskLevel.LOW
        elif self.risk_score < 0.7:
            return RiskLevel.MEDIUM
        elif self.risk_score < 0.9:
            return RiskLevel.HIGH
        return RiskLevel.CRITICAL
