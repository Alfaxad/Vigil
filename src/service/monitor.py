import asyncio
import logging
from collections import deque
from datetime import datetime

from src.locus.client import LocusClient
from src.locus.models import Transaction
from src.auditor.engine import AuditEngine
from src.auditor.models import AuditResult
from src.config import get_settings

logger = logging.getLogger("vigil.monitor")


class MonitorService:
    def __init__(self, locus_client: LocusClient, audit_engine: AuditEngine):
        self.locus = locus_client
        self.engine = audit_engine
        self.settings = get_settings()
        self._running = False
        self._seen_tx_ids: set[str] = set()
        self._audit_history: deque[AuditResult] = deque(maxlen=500)
        self._tx_history: deque[Transaction] = deque(maxlen=200)
        self._stats = {
            "total_audited": 0,
            "approved": 0,
            "flagged": 0,
            "blocked": 0,
            "layer2_invocations": 0,
        }

    def stop(self):
        self._running = False

    def get_recent_audits(self, limit: int = 50) -> list[AuditResult]:
        return list(self._audit_history)[-limit:]

    def get_stats(self) -> dict:
        return {**self._stats, "tx_history_size": len(self._tx_history)}

    async def run(self):
        self._running = True
        logger.info(
            f"Monitor started — polling every {self.settings.monitor_interval_seconds}s"
        )

        # Initial load of transaction history
        try:
            initial_txs = await self.locus.get_transactions(limit=100)
            for tx in initial_txs:
                tx_id = tx.id or tx.tx_hash or ""
                self._seen_tx_ids.add(tx_id)
                self._tx_history.append(tx)
            logger.info(f"Loaded {len(initial_txs)} historical transactions")
        except Exception as e:
            logger.warning(f"Could not load initial transactions: {e}")

        while self._running:
            try:
                await self._poll_cycle()
            except Exception as e:
                logger.error(f"Monitor poll error: {e}")

            await asyncio.sleep(self.settings.monitor_interval_seconds)

    async def _poll_cycle(self):
        txs = await self.locus.get_transactions(limit=50)

        new_txs = []
        for tx in txs:
            tx_id = tx.id or tx.tx_hash or ""
            if tx_id and tx_id not in self._seen_tx_ids:
                self._seen_tx_ids.add(tx_id)
                new_txs.append(tx)
                self._tx_history.append(tx)

        if not new_txs:
            return

        logger.info(f"Found {len(new_txs)} new transaction(s)")

        for tx in new_txs:
            result = await self.engine.audit_transaction(
                tx,
                agent_name="MonitoredAgent",
                agent_task="",
                history=list(self._tx_history),
            )

            self._audit_history.append(result)
            self._stats["total_audited"] += 1

            if result.verdict.value == "APPROVE":
                self._stats["approved"] += 1
            elif result.verdict.value == "FLAG":
                self._stats["flagged"] += 1
            elif result.verdict.value == "BLOCK":
                self._stats["blocked"] += 1

            if result.layer2_invoked:
                self._stats["layer2_invocations"] += 1

            logger.info(
                f"Audit: tx={tx.tx_hash or tx.id} "
                f"amount={tx.amount} "
                f"score={result.statistical_score:.3f} "
                f"verdict={result.verdict.value} "
                f"risk={result.risk_score:.3f}"
            )
