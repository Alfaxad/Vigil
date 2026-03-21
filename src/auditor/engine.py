import logging
from src.locus.client import LocusClient
from src.locus.models import Transaction
from src.auditor.statistical import compute_features, compute_risk_score
from src.auditor.reasoning import invoke_claude
from src.auditor.models import AuditResult, Verdict
from src.chain.erc8004 import ERC8004Attestor
from src.auditor.reputation import ReputationGraph
from src.integrations.uniswap import UniswapVerifier
from src.config import get_settings

logger = logging.getLogger("vigil.engine")


class AuditEngine:
    def __init__(self, locus_client: LocusClient, reputation_graph: ReputationGraph | None = None):
        self.locus = locus_client
        self.settings = get_settings()
        self.attestor = ERC8004Attestor()
        self.reputation = reputation_graph or ReputationGraph()
        self.uniswap = UniswapVerifier()

    async def audit_transaction(
        self,
        tx: Transaction,
        agent_name: str = "",
        agent_task: str = "",
        history: list[Transaction] | None = None,
    ) -> AuditResult:
        history = history or []

        # Layer 1: Statistical analysis
        features = compute_features(tx, history)
        statistical_score = compute_risk_score(features)

        # Uniswap verification for DeFi swaps
        domain = self.reputation.categorize_transaction(tx.to_address or "", tx.memo or "")
        if domain == "defi-swap" and tx.to_address:
            try:
                swap_check = await self.uniswap.verify_swap_transaction(
                    tx.to_address, tx.amount, tx.memo or ""
                )
                statistical_score = max(0.0, min(1.0, statistical_score + swap_check.get("risk_modifier", 0.0)))
                if swap_check.get("warning"):
                    logger.warning(f"Uniswap check: {swap_check['warning']}")
            except Exception as e:
                logger.debug(f"Uniswap verification skipped: {e}")

        # Below review threshold — approve immediately
        if statistical_score < self.settings.risk_threshold_review:
            result = AuditResult(
                tx_hash=tx.tx_hash,
                statistical_score=statistical_score,
                features=features,
                verdict=Verdict.APPROVE,
                risk_score=statistical_score,
                reasoning=f"Transaction within normal parameters. Statistical score: {statistical_score:.3f}",
                evidence=[],
                recommended_action="No action needed",
                layer2_invoked=False,
            )
            # Still write attestation for clean transactions
            try:
                attestation_hash = await self.attestor.attest(
                    result, tx.from_address or ""
                )
                result.attestation_tx = attestation_hash
            except Exception as e:
                logger.warning(f"Attestation failed: {e}")
            # Record in reputation graph
            self.reputation.record_interaction(
                tx.to_address or "", tx.from_address or "",
                result.verdict.value, tx.amount, tx.memo or "",
            )
            return result

        # Layer 2: Claude reasoning for flagged transactions
        logger.info(
            f"Escalating to Layer 2: tx={tx.tx_hash or tx.id} "
            f"score={statistical_score:.3f}"
        )

        result = await invoke_claude(
            self.locus,
            tx,
            features,
            statistical_score,
            agent_name,
            agent_task,
            history,
        )

        # If above alert threshold, ensure at least FLAG verdict
        if (
            statistical_score >= self.settings.risk_threshold_alert
            and result.verdict == Verdict.APPROVE
        ):
            result.verdict = Verdict.FLAG
            result.reasoning += (
                " [Vigil override: statistical score exceeds alert threshold]"
            )

        # Write ERC-8004 attestation
        try:
            attestation_hash = await self.attestor.attest(
                result, tx.from_address or ""
            )
            result.attestation_tx = attestation_hash
        except Exception as e:
            logger.warning(f"Attestation failed: {e}")

        # Record in reputation graph
        self.reputation.record_interaction(
            tx.to_address or "", tx.from_address or "",
            result.verdict.value, tx.amount, tx.memo or "",
        )

        return result
