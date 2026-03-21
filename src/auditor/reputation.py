"""
Counterparty reputation graph and domain-specific trust scoring.
Tracks addresses across all monitored agents to build shared intelligence.
"""
import logging
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional

logger = logging.getLogger("vigil.reputation")


# Transaction categories for domain-specific trust
DOMAIN_CATEGORIES = {
    "defi-swap": ["swap", "exchange", "trade", "uniswap", "aerodrome", "sushiswap"],
    "defi-stake": ["stake", "unstake", "steth", "lido", "deposit", "withdraw"],
    "defi-lend": ["lend", "borrow", "aave", "compound", "supply", "repay"],
    "nft-trade": ["nft", "mint", "bid", "auction", "opensea", "rare"],
    "transfer": ["transfer", "send", "payment"],
    "bridge": ["bridge", "cross-chain", "relay"],
    "agent-hire": ["service", "hire", "x402", "api"],
}

# Known contract addresses on Base for automatic categorization
KNOWN_CONTRACTS = {
    "0x2626664c2603336e57b271c5c0b26f421741e481": ("Uniswap Universal Router", "defi-swap"),
    "0x3d4e44eb1374240ce5f1b871ab261cd16335b76a": ("Aerodrome Router", "defi-swap"),
    "0x940181a94a35a4569e4529a3cdfb74e38fd98631": ("Aave V3 Pool", "defi-lend"),
    "0xa238dd80c259a72e81d7e4664a9801593f98d1c5": ("Base Bridge", "bridge"),
    "0x833589fcd6edb6e08f4c7c32d4f71b54bda02913": ("USDC", "transfer"),
}


@dataclass
class CounterpartyProfile:
    address: str
    first_seen: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    last_seen: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    total_interactions: int = 0
    clean_interactions: int = 0
    flagged_interactions: int = 0
    blocked_interactions: int = 0
    total_volume: float = 0.0
    known_label: Optional[str] = None
    known_category: Optional[str] = None
    interacting_agents: set = field(default_factory=set)

    @property
    def trust_score(self) -> float:
        if self.total_interactions == 0:
            return 0.5  # Unknown
        clean_ratio = self.clean_interactions / self.total_interactions
        # Discount by sample size (more data = more confidence)
        confidence = min(self.total_interactions / 100, 1.0)
        return 0.5 + (clean_ratio - 0.5) * confidence

    @property
    def is_known(self) -> bool:
        return self.known_label is not None or self.total_interactions >= 5


@dataclass
class DomainScore:
    domain: str
    score: float = 0.0
    audits: int = 0
    clean: int = 0
    flagged: int = 0
    blocked: int = 0

    def update(self, verdict: str):
        self.audits += 1
        if verdict == "APPROVE":
            self.clean += 1
        elif verdict == "FLAG":
            self.flagged += 1
        elif verdict == "BLOCK":
            self.blocked += 1
        if self.audits > 0:
            self.score = self.clean / self.audits


class ReputationGraph:
    """Shared counterparty reputation graph across all monitored agents."""

    def __init__(self):
        self._counterparties: dict[str, CounterpartyProfile] = {}
        self._agent_domains: dict[str, dict[str, DomainScore]] = defaultdict(
            lambda: defaultdict(lambda: DomainScore(domain="unknown"))
        )
        self._total_audits = 0
        self._total_approved = 0
        self._total_flagged = 0
        self._total_blocked = 0

        # Pre-populate known contracts
        for addr, (label, category) in KNOWN_CONTRACTS.items():
            self._counterparties[addr.lower()] = CounterpartyProfile(
                address=addr.lower(),
                known_label=label,
                known_category=category,
                clean_interactions=100,  # Pre-trusted
                total_interactions=100,
            )

    def categorize_transaction(self, to_address: str, memo: str = "") -> str:
        addr = (to_address or "").lower()

        # Check known contracts first
        if addr in KNOWN_CONTRACTS:
            return KNOWN_CONTRACTS[addr][1]

        # Fall back to memo-based categorization
        memo_lower = (memo or "").lower()
        for domain, keywords in DOMAIN_CATEGORIES.items():
            if any(kw in memo_lower for kw in keywords):
                return domain

        return "transfer"  # Default

    def record_interaction(
        self,
        counterparty_address: str,
        agent_address: str,
        verdict: str,
        amount: float,
        memo: str = "",
    ):
        addr = (counterparty_address or "").lower()
        if not addr:
            return

        # Update counterparty profile
        if addr not in self._counterparties:
            self._counterparties[addr] = CounterpartyProfile(address=addr)

        cp = self._counterparties[addr]
        cp.total_interactions += 1
        cp.total_volume += amount
        cp.last_seen = datetime.now(timezone.utc)
        cp.interacting_agents.add(agent_address)

        if verdict == "APPROVE":
            cp.clean_interactions += 1
            self._total_approved += 1
        elif verdict == "FLAG":
            cp.flagged_interactions += 1
            self._total_flagged += 1
        elif verdict == "BLOCK":
            cp.blocked_interactions += 1
            self._total_blocked += 1

        self._total_audits += 1

        # Update domain scores for the agent
        domain = self.categorize_transaction(counterparty_address, memo)
        agent_addr = (agent_address or "").lower()
        self._agent_domains[agent_addr][domain].domain = domain
        self._agent_domains[agent_addr][domain].update(verdict)

    def get_counterparty(self, address: str) -> Optional[CounterpartyProfile]:
        return self._counterparties.get((address or "").lower())

    def get_counterparty_risk(self, address: str) -> float:
        cp = self.get_counterparty(address)
        if cp is None:
            return 1.0  # Unknown = max risk
        return 1.0 - cp.trust_score

    def get_agent_trust_scores(self, agent_address: str) -> dict:
        addr = (agent_address or "").lower()
        domains = self._agent_domains.get(addr, {})
        result = {}
        for domain, score in domains.items():
            if score.audits > 0:
                result[domain] = {
                    "score": round(score.score, 3),
                    "audits": score.audits,
                    "clean": score.clean,
                    "flagged": score.flagged,
                    "blocked": score.blocked,
                }
        return result

    def get_address_reputation(self, address: str) -> dict:
        addr = (address or "").lower()
        cp = self._counterparties.get(addr)

        if cp is None:
            return {
                "address": address,
                "known": False,
                "trust_scores": {},
                "overall_score": 0.5,
                "total_audits": 0,
                "flags": 0,
                "blocks": 0,
                "last_audit": None,
            }

        # Get domain scores if this address is also a monitored agent
        domain_scores = self.get_agent_trust_scores(address)

        return {
            "address": address,
            "known": cp.is_known,
            "label": cp.known_label,
            "trust_scores": domain_scores if domain_scores else {
                cp.known_category or "general": {
                    "score": round(cp.trust_score, 3),
                    "audits": cp.total_interactions,
                }
            },
            "overall_score": round(cp.trust_score, 3),
            "total_audits": cp.total_interactions,
            "total_volume": round(cp.total_volume, 2),
            "flags": cp.flagged_interactions,
            "blocks": cp.blocked_interactions,
            "unique_agents": len(cp.interacting_agents),
            "first_seen": cp.first_seen.isoformat(),
            "last_audit": cp.last_seen.isoformat(),
        }

    def get_stats(self) -> dict:
        return {
            "total_counterparties": len(self._counterparties),
            "known_counterparties": sum(
                1 for cp in self._counterparties.values() if cp.is_known
            ),
            "total_audits": self._total_audits,
            "approved": self._total_approved,
            "flagged": self._total_flagged,
            "blocked": self._total_blocked,
        }
