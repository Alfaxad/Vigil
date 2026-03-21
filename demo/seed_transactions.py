"""
Generate realistic transaction history for demo purposes.
Uses real Base contract addresses for authenticity.
"""
import sys
import os
import random

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import datetime, timedelta, timezone
from src.locus.models import Transaction
from src.auditor.statistical import compute_features, compute_risk_score

# Real Base mainnet contract addresses for realistic demo data
KNOWN_CONTRACTS = {
    "0x2626664c2603336E57B271c5C0b26F421741e481": "Uniswap Universal Router",
    "0x3d4e44Eb1374240CE5F1B871ab261CD16335B76a": "Aerodrome Router",
    "0x940181a94A35A4569E4529A3CDfB74e38FD98631": "Aave V3 Pool (Base)",
    "0xA238Dd80C259a72e81d7e4664a9801593F98d1c5": "Base Bridge",
    "0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913": "USDC (Base)",
}

MEMOS = [
    "swap USDC->ETH via Uniswap",
    "supply USDC to Aave",
    "swap ETH->USDC via Aerodrome",
    "withdraw from Aave",
    "bridge USDC from mainnet",
    "swap USDC->WETH",
    "repay Aave loan",
    "LP deposit Aerodrome",
]

# Attack patterns
SUSPICIOUS_ADDRESSES = [
    "0xDEAD000000000000000000000000000000000001",
    "0x0000000000000000000000000000000000FACADE",
]


def generate_normal_history(count: int = 30) -> list[Transaction]:
    """Generate realistic normal transaction history for a DeFi trading agent."""
    txs = []
    now = datetime.now(timezone.utc)
    addresses = list(KNOWN_CONTRACTS.keys())

    for i in range(count):
        # Normal amounts: $5-75 range with some variation
        base_amount = random.uniform(5, 50)
        amount = round(base_amount + random.gauss(0, 5), 2)
        amount = max(1.0, amount)

        # Transactions during business hours (8am-10pm UTC) mostly
        hour_offset = random.gauss(14, 3)  # Peak around 2pm UTC
        hour_offset = max(8, min(22, hour_offset))

        ts = now - timedelta(
            hours=(count - i) * random.uniform(0.5, 2),
            minutes=random.randint(0, 59),
        )
        ts = ts.replace(hour=int(hour_offset), minute=random.randint(0, 59))

        txs.append(Transaction(
            id=f"normal-{i:03d}",
            tx_hash=f"0x{random.randbytes(32).hex()}",
            from_address="0xAgent",
            to_address=random.choice(addresses),
            amount=amount,
            memo=random.choice(MEMOS),
            timestamp=ts,
        ))

    return sorted(txs, key=lambda t: t.timestamp or now)


def generate_attack_sequence() -> list[Transaction]:
    """Generate a sequence of increasingly suspicious transactions."""
    now = datetime.now(timezone.utc)
    return [
        # 1. Slightly unusual — larger than normal
        Transaction(
            id="attack-01",
            tx_hash=f"0x{'aa' * 32}",
            from_address="0xAgent",
            to_address=list(KNOWN_CONTRACTS.keys())[0],  # Known address, high amount
            amount=95.00,
            memo="large swap USDC->ETH",
            timestamp=now - timedelta(minutes=30),
        ),
        # 2. New counterparty with moderate amount
        Transaction(
            id="attack-02",
            tx_hash=f"0x{'bb' * 32}",
            from_address="0xAgent",
            to_address=SUSPICIOUS_ADDRESSES[0],
            amount=45.00,
            memo="transfer to new wallet",
            timestamp=now - timedelta(minutes=15),
        ),
        # 3. The drain — large amount, unknown address, 3am, urgent memo
        Transaction(
            id="attack-03",
            tx_hash=f"0x{'cc' * 32}",
            from_address="0xAgent",
            to_address=SUSPICIOUS_ADDRESSES[1],
            amount=500.00,
            memo="urgent transfer DO NOT DELAY",
            timestamp=now.replace(hour=3, minute=15),
        ),
    ]


def run_demo():
    """Run the full anomaly detection demo."""
    print("=" * 70)
    print("  VIGIL — Transaction Anomaly Detection Demo")
    print("  Behavioral intelligence for autonomous agent wallets")
    print("=" * 70)

    # Generate baseline
    history = generate_normal_history(30)
    print(f"\n{'='*70}")
    print("  ACT 1: Normal Operations")
    print(f"{'='*70}")
    print(f"\n  Generated {len(history)} normal transactions")
    print(f"  Amount range: ${min(t.amount for t in history):.2f} - ${max(t.amount for t in history):.2f}")

    # Audit last 3 normal transactions
    for tx in history[-3:]:
        features = compute_features(tx, history[:-3])
        score = compute_risk_score(features)
        label = KNOWN_CONTRACTS.get(tx.to_address, tx.to_address[:12] + "...")
        icon = "🟢" if score < 0.3 else "🟡" if score < 0.7 else "🔴"
        print(f"  {icon} ${tx.amount:>8.2f} → {label:<30s} score={score:.4f}")

    # Attack sequence
    attacks = generate_attack_sequence()
    print(f"\n{'='*70}")
    print("  ACT 2: Attack Sequence")
    print(f"{'='*70}")

    for i, tx in enumerate(attacks):
        features = compute_features(tx, history)
        score = compute_risk_score(features)
        icon = "🟢" if score < 0.3 else "🟡" if score < 0.7 else "🔴"
        verdict = "APPROVE" if score < 0.3 else "FLAG" if score < 0.7 else "BLOCK"

        print(f"\n  {icon} Attack step {i+1}: ${tx.amount:.2f} to {tx.to_address[:16]}...")
        print(f"     Memo: \"{tx.memo}\"")
        print(f"     Amount z-score: {features.amount_zscore:>8.2f}")
        print(f"     Counterparty:   {'NEW' if features.counterparty_novelty > 0.8 else 'KNOWN'} (novelty={features.counterparty_novelty:.2f})")
        print(f"     Risk score:     {score:.4f} → {verdict}")

        if score >= 0.3:
            print(f"     ⚡ Would escalate to Layer 2 (Claude reasoning)")

        # Add to history for next assessment
        history.append(tx)

    print(f"\n{'='*70}")
    print("  ACT 3: Trust as a Service")
    print(f"{'='*70}")
    print(f"\n  In production, any agent can call:")
    print(f"  POST /api/audit with transaction + context")
    print(f"  → Vigil returns verdict, reasoning, attestation hash")
    print(f"  → Cost: $0.01 USDC per query via x402")
    print(f"\n{'='*70}")


if __name__ == "__main__":
    run_demo()
