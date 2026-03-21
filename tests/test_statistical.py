import pytest
from datetime import datetime, timedelta
from src.auditor.statistical import compute_features, compute_risk_score
from src.locus.models import Transaction


def make_tx(amount: float, to: str = "0xAAA", hours_ago: float = 0, memo: str = "") -> Transaction:
    return Transaction(
        id=f"tx-{amount}-{hours_ago}",
        tx_hash=f"0x{int(amount * 100):064x}",
        from_address="0xAgent",
        to_address=to,
        amount=amount,
        memo=memo,
        timestamp=datetime.utcnow() - timedelta(hours=hours_ago),
    )


def make_normal_history(n: int = 20) -> list[Transaction]:
    """Generate a history of normal $10-30 txs to known addresses."""
    txs = []
    for i in range(n):
        txs.append(make_tx(
            amount=15 + (i % 10),
            to="0xAAA" if i % 3 != 0 else "0xBBB",
            hours_ago=n - i,
        ))
    return txs


class TestComputeFeatures:
    def test_empty_history(self):
        tx = make_tx(100)
        features = compute_features(tx, [])
        assert features.counterparty_novelty == 1.0
        assert features.amount_zscore == 0.0

    def test_normal_tx_low_zscore(self):
        history = make_normal_history()
        tx = make_tx(20, to="0xAAA", hours_ago=0)
        features = compute_features(tx, history)
        assert abs(features.amount_zscore) < 2.0

    def test_anomalous_amount_high_zscore(self):
        history = make_normal_history()
        tx = make_tx(500, to="0xAAA", hours_ago=0)
        features = compute_features(tx, history)
        assert features.amount_zscore > 2.0

    def test_new_counterparty_high_novelty(self):
        history = make_normal_history()
        tx = make_tx(20, to="0xNEVER_SEEN", hours_ago=0)
        features = compute_features(tx, history)
        assert features.counterparty_novelty == 1.0

    def test_known_counterparty_low_novelty(self):
        history = [make_tx(15, to="0xFRIEND", hours_ago=i) for i in range(15)]
        tx = make_tx(20, to="0xFRIEND", hours_ago=0)
        features = compute_features(tx, history)
        assert features.counterparty_novelty == 0.0


class TestComputeRiskScore:
    def test_normal_tx_low_risk(self):
        history = make_normal_history()
        tx = make_tx(20, to="0xAAA", hours_ago=0)
        features = compute_features(tx, history)
        score = compute_risk_score(features)
        assert score < 0.35, f"Normal tx should be low risk, got {score}"

    def test_anomalous_tx_high_risk(self):
        history = make_normal_history()
        tx = make_tx(500, to="0xNEW_ADDRESS", hours_ago=0)
        features = compute_features(tx, history)
        score = compute_risk_score(features)
        assert score > 0.3, f"Anomalous tx should be flagged, got {score}"

    def test_score_bounded(self):
        history = make_normal_history()
        tx = make_tx(10000, to="0xATTACKER", hours_ago=0)
        features = compute_features(tx, history)
        score = compute_risk_score(features)
        assert 0.0 <= score <= 1.0

    def test_slightly_unusual_medium_risk(self):
        history = make_normal_history()
        # Slightly higher amount, new counterparty
        tx = make_tx(50, to="0xNEW", hours_ago=0)
        features = compute_features(tx, history)
        score = compute_risk_score(features)
        # Should be in review range, not necessarily blocked
        assert score > 0.1
