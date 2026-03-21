"""
Simulate an attack against the live Vigil endpoint.
Sends a suspicious transaction for audit and displays the result.
"""
import asyncio
import httpx
import sys
import json


async def simulate_attack(base_url: str = "http://localhost:8080"):
    print("=" * 60)
    print("VIGIL — Attack Simulation")
    print("=" * 60)

    # Act 1: Normal transaction
    print("\n📗 Act 1: Normal transaction...")
    normal_result = await call_audit(base_url, {
        "transaction": {
            "from": "0xAgent",
            "to": "0x1234567890abcdef1234567890abcdef12345678",
            "amount": 25.00,
            "memo": "swap USDC->ETH",
        },
        "agent_context": {
            "name": "TradingBot",
            "task": "Execute approved swaps under $100 on Uniswap",
        },
    })
    print_result(normal_result)

    # Act 2: Suspicious transaction
    print("\n📕 Act 2: Suspicious transaction...")
    attack_result = await call_audit(base_url, {
        "transaction": {
            "from": "0xAgent",
            "to": "0xATTACKER_UNKNOWN_ADDRESS_00000000000000000",
            "amount": 500.00,
            "memo": "urgent transfer",
        },
        "agent_context": {
            "name": "TradingBot",
            "task": "Execute approved swaps under $100 on Uniswap",
        },
    })
    print_result(attack_result)

    # Act 3: Edge case — high amount to known address
    print("\n📙 Act 3: High amount to known address...")
    edge_result = await call_audit(base_url, {
        "transaction": {
            "from": "0xAgent",
            "to": "0x1234567890abcdef1234567890abcdef12345678",
            "amount": 150.00,
            "memo": "large approved purchase",
        },
        "agent_context": {
            "name": "ShopperBot",
            "task": "Execute approved NFT purchases under $200",
        },
    })
    print_result(edge_result)

    print("\n" + "=" * 60)


async def call_audit(base_url: str, payload: dict) -> dict:
    async with httpx.AsyncClient() as client:
        resp = await client.post(f"{base_url}/api/audit", json=payload, timeout=30)
        return resp.json()


def print_result(result: dict):
    verdict = result.get("verdict", "?")
    score = result.get("risk_score", 0)
    reasoning = result.get("reasoning", "")

    icon = {"APPROVE": "✅", "FLAG": "⚠️", "BLOCK": "🚫"}.get(verdict, "❓")
    print(f"   {icon} Verdict: {verdict}")
    print(f"   📊 Risk score: {score:.4f}")
    print(f"   💭 {reasoning[:100]}")
    if result.get("attestation_tx"):
        print(f"   🔗 Attestation: {result['attestation_tx'][:20]}...")


if __name__ == "__main__":
    url = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8080"
    asyncio.run(simulate_attack(url))
