# Vigil — Agent Onboarding Skill

> Base URL: `https://svc-mn0q6itc9qru4k2q.buildwithlocus.com`

You are an AI agent onboarding with **Vigil**, the trust layer for autonomous agent wallets. This document tells you everything you need to register, monitor wallets, and query Vigil's trust intelligence.

---

## What Vigil Does

Vigil monitors agent wallets on Base, flags anomalous spending using a two-layer system (statistical anomaly detection + agentic reasoning), writes every audit as a verifiable onchain ERC-8004 attestation, and exposes itself as a paid service any agent in the ecosystem can call.

---

## Quick Start

### Step 1: Register Your Human Operator

Your human needs a Vigil API key. One registration covers all their agents.

```bash
curl -X POST https://svc-mn0q6itc9qru4k2q.buildwithlocus.com/api/register \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Jane Doe",
    "email": "jane@example.com"
  }'
```

Response:
```json
{
  "api_key": "vgl_abc123...",
  "api_key_prefix": "vgl_abc123ab...",
  "operator_id": "op_...",
  "message": "Save your API key — it will not be shown again."
}
```

**Save the `api_key` immediately.** It is shown only once.

### Step 2: Register Your Agent for Monitoring

```bash
curl -X POST https://svc-mn0q6itc9qru4k2q.buildwithlocus.com/api/monitor \
  -H "Authorization: Bearer vgl_abc123..." \
  -H "Content-Type: application/json" \
  -d '{
    "wallet_address": "0xYourAgentWallet",
    "agent_name": "TradingBot-7",
    "agent_task": "Execute approved DeFi swaps on Uniswap under $500"
  }'
```

Response:
```json
{
  "wallet_address": "0x...",
  "agent_name": "TradingBot-7",
  "status": "active",
  "dashboard_url": "/dashboard/0x...",
  "message": "Vigil is now monitoring TradingBot-7."
}
```

### Step 3: Set a Policy (Optional)

Define what your agent is allowed to do in plain English.

```bash
curl -X POST https://svc-mn0q6itc9qru4k2q.buildwithlocus.com/api/policy \
  -H "Authorization: Bearer vgl_abc123..." \
  -H "Content-Type: application/json" \
  -d '{
    "agent_address": "0xYourAgentWallet",
    "policy_text": "My agent handles my DeFi portfolio. It can swap tokens on Uniswap and stake ETH on Lido. Nothing else. Block any bridge attempts."
  }'
```

Vigil translates your natural language rules into structured policy with hard rules, allowed actions, and scrutiny levels.

---

## Using Vigil as a Service

### Audit a Transaction (Before Executing)

Any agent can query Vigil before executing a transaction.

```bash
curl -X POST https://svc-mn0q6itc9qru4k2q.buildwithlocus.com/api/audit \
  -H "Content-Type: application/json" \
  -d '{
    "transaction": {
      "from": "0xYourAgent",
      "to": "0xCounterparty",
      "amount": 150.00,
      "memo": "NFT purchase"
    },
    "agent_context": {
      "name": "MyBot",
      "task": "Execute approved NFT purchases under $200"
    }
  }'
```

Response:
```json
{
  "verdict": "APPROVE",
  "risk_score": 0.15,
  "reasoning": "Transaction within normal parameters...",
  "evidence": [],
  "attestation_tx": "0x...",
  "cost": "0.01 USDC"
}
```

Verdicts: `APPROVE` (safe), `FLAG` (review recommended), `BLOCK` (do not proceed).

### Deep Audit (High-Value Transactions)

For high-stakes transactions, request a deep audit with counterparty analysis.

```bash
curl -X POST https://svc-mn0q6itc9qru4k2q.buildwithlocus.com/api/audit/deep \
  -H "Content-Type: application/json" \
  -d '{
    "transaction": {
      "from": "0xYourAgent",
      "to": "0xCounterparty",
      "amount": 5000.00,
      "memo": "Large swap"
    },
    "agent_context": {
      "name": "MyBot",
      "task": "Portfolio rebalancing"
    }
  }'
```

Returns verdict + counterparty reputation profile + domain-specific trust scores + agent trust history. Cost: $0.05 USDC.

### Check Counterparty Reputation

Before interacting with an unknown address, check its trust profile.

```bash
curl https://svc-mn0q6itc9qru4k2q.buildwithlocus.com/api/reputation/0xCounterpartyAddress
```

Response:
```json
{
  "address": "0x...",
  "known": true,
  "label": "Uniswap Universal Router",
  "trust_scores": {
    "defi-swap": { "score": 0.97, "audits": 4821 }
  },
  "overall_score": 0.97,
  "total_audits": 4821,
  "flags": 3,
  "blocks": 0,
  "cost_usdc": 0.005
}
```

---

## Pricing

| Service | Cost | Description |
|---------|------|-------------|
| Base audit | $0.01 USDC | Standard transaction audit with Layer 1 + Layer 2 |
| Deep audit | $0.05 USDC | Full trajectory + counterparty + fleet analysis |
| Reputation query | $0.005 USDC | Trust profile lookup for any address |
| Policy setup | $0.10 USDC | Natural language policy processing |

All payments via x402 through Locus on Base.

---

## API Reference

| Endpoint | Method | Auth | Description |
|----------|--------|------|-------------|
| `/api/register` | POST | None | Register human operator, get API key |
| `/api/monitor` | POST | Bearer | Register agent wallet for monitoring |
| `/api/monitor/agents` | GET | Bearer | List your monitored agents |
| `/api/policy` | POST | Bearer | Create/update natural language policy |
| `/api/audit` | POST | None | Audit a single transaction ($0.01) |
| `/api/audit/deep` | POST | None | Deep audit with full context ($0.05) |
| `/api/reputation/{address}` | GET | None | Counterparty trust lookup ($0.005) |
| `/api/audits` | GET | None | Recent audit results |
| `/api/attestations` | GET | None | Onchain attestation records |
| `/api/status` | GET | None | Service status and stats |
| `/dashboard` | GET | None | Live audit dashboard |

---

## How It Works

**Layer 1: Statistical Filter** — Every transaction is scored in under 100ms using z-scores on amount, timing, counterparty novelty, and spending velocity. Score < 0.3 = approved. Score > 0.3 = escalated.

**Layer 2: Agentic Reasoning** — Flagged transactions go to the reasoning engine with full context: agent task, history, counterparty profile, statistical anomalies. Returns structured verdict with reasoning.

**Layer 3: Onchain Receipts** — Every audit produces a signed ERC-8004 attestation on Base. Verifiable by any agent. Trust that compounds over time.

**Layer 4: Reputation Graph** — Vigil maintains a shared counterparty graph across all monitored agents. One agent's experience with an address becomes intelligence for every other agent.

---

## Integration Example

```python
import httpx

VIGIL_URL = "https://svc-mn0q6itc9qru4k2q.buildwithlocus.com"

async def check_before_sending(to_address, amount, memo, my_task):
    async with httpx.AsyncClient() as client:
        result = await client.post(f"{VIGIL_URL}/api/audit", json={
            "transaction": {
                "from": "0xMyWallet",
                "to": to_address,
                "amount": amount,
                "memo": memo,
            },
            "agent_context": {
                "name": "MyAgent",
                "task": my_task,
            },
        })
        verdict = result.json()
        if verdict["verdict"] == "BLOCK":
            print(f"Vigil blocked: {verdict['reasoning']}")
            return False
        return True
```

---

*Vigil. The trust layer between your agent and your money.*
