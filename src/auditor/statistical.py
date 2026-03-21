import numpy as np
from datetime import datetime, timedelta
from src.auditor.models import TxFeatures
from src.locus.models import Transaction


def compute_features(tx: Transaction, history: list[Transaction]) -> TxFeatures:
    if not history:
        return TxFeatures(counterparty_novelty=1.0)

    amounts = [t.amount for t in history if t.amount > 0]
    timestamps = [t.timestamp for t in history if t.timestamp]

    # Amount z-score
    amount_zscore = 0.0
    if len(amounts) >= 3:
        mean_amt = np.mean(amounts)
        std_amt = np.std(amounts)
        if std_amt > 0:
            amount_zscore = (tx.amount - mean_amt) / std_amt

    # Time delta z-score
    time_delta_zscore = 0.0
    if len(timestamps) >= 3 and tx.timestamp:
        deltas = []
        sorted_ts = sorted(timestamps)
        for i in range(1, len(sorted_ts)):
            delta = (sorted_ts[i] - sorted_ts[i - 1]).total_seconds()
            if delta > 0:
                deltas.append(delta)
        if deltas:
            current_delta = (tx.timestamp - sorted_ts[-1]).total_seconds()
            mean_delta = np.mean(deltas)
            std_delta = np.std(deltas)
            if std_delta > 0:
                time_delta_zscore = (current_delta - mean_delta) / std_delta

    # Counterparty novelty
    counterparty_novelty = 1.0
    if tx.to_address:
        seen_count = sum(
            1 for t in history if t.to_address == tx.to_address
        )
        if seen_count >= 10:
            counterparty_novelty = 0.0
        else:
            counterparty_novelty = 1.0 - (seen_count / 10.0)

    # Amount velocity (spending rate)
    now = tx.timestamp or datetime.utcnow()

    def velocity(hours: int) -> float:
        cutoff = now - timedelta(hours=hours)
        recent_spend = sum(
            t.amount
            for t in history
            if t.timestamp and t.timestamp >= cutoff and t.amount > 0
        )
        if not amounts:
            return 0.0
        daily_avg = np.mean(amounts) * (len(amounts) / max(1, len(set(
            t.timestamp.date() for t in history if t.timestamp
        ))))
        if daily_avg <= 0:
            return 0.0
        expected = daily_avg * (hours / 24.0)
        return (recent_spend + tx.amount) / max(expected, 0.01)

    velocity_1h = velocity(1)
    velocity_6h = velocity(6)
    velocity_24h = velocity(24)

    # Gas price ratio (placeholder — would need chain data)
    gas_price_ratio = 0.0

    # Hour anomaly
    hour_anomaly = 0.0
    if tx.timestamp:
        tx_hour = tx.timestamp.hour
        hours = [t.timestamp.hour for t in history if t.timestamp]
        if hours:
            hour_counts = np.zeros(24)
            for h in hours:
                hour_counts[h] += 1
            hour_dist = hour_counts / max(hour_counts.sum(), 1)
            if hour_dist[tx_hour] < 0.02:
                hour_anomaly = 1.0
            else:
                median_freq = np.median(hour_dist[hour_dist > 0])
                if median_freq > 0:
                    hour_anomaly = max(
                        0, 1.0 - (hour_dist[tx_hour] / median_freq)
                    )

    return TxFeatures(
        amount_zscore=amount_zscore,
        time_delta_zscore=time_delta_zscore,
        counterparty_novelty=counterparty_novelty,
        amount_velocity_1h=velocity_1h,
        amount_velocity_6h=velocity_6h,
        amount_velocity_24h=velocity_24h,
        gas_price_ratio=gas_price_ratio,
        hour_anomaly=hour_anomaly,
    )


def compute_risk_score(features: TxFeatures) -> float:
    weights = {
        "amount_zscore": 0.25,
        "time_delta_zscore": 0.10,
        "counterparty_novelty": 0.15,
        "amount_velocity_1h": 0.15,
        "amount_velocity_6h": 0.10,
        "amount_velocity_24h": 0.05,
        "gas_price_ratio": 0.05,
        "hour_anomaly": 0.15,
    }
    raw = sum(
        weights[k] * min(abs(getattr(features, k)), 3.0) / 3.0
        for k in weights
    )
    return min(max(raw, 0.0), 1.0)
