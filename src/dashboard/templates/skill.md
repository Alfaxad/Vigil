# Vigil — Agent Onboarding Skill

> Base URL: `https://svc-mn0q6itc9qru4k2q.buildwithlocus.com`

You are an AI agent onboarding with **Vigil**, the trust layer for autonomous AI agent wallets. This document tells you everything you need to register, audit transactions, query trust intelligence, and integrate Vigil into your decision loop.

---

## What Vigil Does

Vigil is a 4-layer behavioral audit pipeline for agent wallets on Base:

1. **Perception** — Statistical anomaly detection (z-scores on amount, timing, velocity, counterparty novelty). Sub-100ms.
2. **Policy** — Natural language rules defined by the guardian. Hard rules block transactions immediately.
3. **Reasoning** — Agentic reasoning via Claude (Locus wrapped API). Only invoked for flagged transactions.
4. **Signal** — Every audit produces a signed ERC-8004 attestation on Base and updates the shared reputation graph.

Vigil exposes itself as a paid service via the x402 protocol. Any agent can call it.

---

## Authentication

All endpoints (except register, health, and pricing discovery) require an API key:

```
Authorization: Bearer vgl_your_api_key
```

Calling `/api/audit` or `/api/audit/deep` without auth returns `402 Payment Required` with x402-compatible pricing info. All other protected endpoints return `401`.

---

## Quick Start

### Step 1: Register

```bash
curl -X POST https://svc-mn0q6itc9qru4k2q.buildwithlocus.com/api/register \
  -H "Content-Type: application/json" \
  -d '{"name": "my-agent", "email": "optional@example.com"}'
```

Response:
```json
{
  "api_key": "vgl_abc123...",
  "api_key_prefix": "vgl_abc123ab...",
  "operator_id": "a1b2c3d4...",
  "message": "Save your API key. If lost, use POST /api/regenerate-key with your operator_id to get a new one."
}
```

**Save the `api_key` immediately.** It is shown only once. If lost, use `/api/regenerate-key` with your `operator_id`.

### Step 2: Audit a Transaction

```bash
curl -X POST https://svc-mn0q6itc9qru4k2q.buildwithlocus.com/api/audit \
  -H "Authorization: Bearer vgl_abc123..." \
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
  "risk_score": 0.12,
  "reasoning": "Transaction within normal parameters. Statistical score: 0.120",
  "evidence": [],
  "recommended_action": "No action needed",
  "attestation_tx": "0x65b1089c...",
  "cost": "0.01 USDC"
}
```

Verdicts: `APPROVE` (safe), `FLAG` (review recommended), `BLOCK` (do not proceed).

### Step 3: Check Counterparty Reputation

```bash
curl https://svc-mn0q6itc9qru4k2q.buildwithlocus.com/api/reputation/0xCounterpartyAddress \
  -H "Authorization: Bearer vgl_abc123..."
```

Response:
```json
{
  "address": "0x2626664c...",
  "known": true,
  "label": "Uniswap Universal Router",
  "overall_score": 1.0,
  "total_audits": 101,
  "flags": 0,
  "blocks": 0
}
```

---

## Register Agent for Monitoring

```bash
curl -X POST https://svc-mn0q6itc9qru4k2q.buildwithlocus.com/api/monitor \
  -H "Authorization: Bearer vgl_abc123..." \
  -H "Content-Type: application/json" \
  -d '{
    "wallet_address": "0xYourAgentWallet",
    "agent_name": "TradingBot",
    "agent_task": "Execute approved DeFi swaps on Uniswap under $500"
  }'
```

---

## Set Guardian Policies

Define what your agent is allowed to do in plain English. Policies are enforced before every audit — hard rules block transactions immediately.

```bash
curl -X POST https://svc-mn0q6itc9qru4k2q.buildwithlocus.com/api/policy \
  -H "Authorization: Bearer vgl_abc123..." \
  -H "Content-Type: application/json" \
  -d '{
    "agent_address": "0xYourAgentWallet",
    "policy_text": "Block any transfer exceeding $5,000 to an unknown address. Only allow DeFi swaps on verified protocols."
  }'
```

---

## Deep Audit

For high-stakes transactions, request a deep audit with counterparty profile and trajectory analysis.

```bash
curl -X POST https://svc-mn0q6itc9qru4k2q.buildwithlocus.com/api/audit/deep \
  -H "Authorization: Bearer vgl_abc123..." \
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

Returns verdict + counterparty profile + domain categorization + agent trust scores. Cost: $0.05 USDC.

---

## x402 Pay-Per-Call

Agents without a Vigil API key can pay per audit call:

1. Call `/api/audit` without auth
2. Receive `402 Payment Required` with pricing and payment address
3. Pay via Locus x402 or direct USDC to `0xa2cec58dd199c392a4b2cd86f48fd620bb2040ff`
4. Retry with payment header

Discover all pricing: `GET /.well-known/x402`

---

## Key Regeneration

If you lose your API key:

```bash
curl -X POST https://svc-mn0q6itc9qru4k2q.buildwithlocus.com/api/regenerate-key \
  -H "Content-Type: application/json" \
  -d '{"operator_id": "your_operator_id"}'
```

Returns a new API key. The old key is immediately invalidated.

---

## CLI

Vigil also ships a terminal interface:

```bash
git clone https://github.com/Alfaxad/Vigil.git && cd Vigil
pip install -e .
vigil register --name "my-agent"
vigil audit --from 0xAgent --to 0xTarget --amount 150 --memo "swap"
vigil reputation 0x2626664c2603336e57b271c5c0b26f421741e481
vigil policies list
vigil status
```

---

## API Reference

| Endpoint | Method | Auth | Description |
|----------|--------|------|-------------|
| `/api/register` | POST | No | Register operator, get API key |
| `/api/regenerate-key` | POST | No | Regenerate lost API key |
| `/api/audit` | POST | Yes/x402 | Standard 4-layer audit ($0.01) |
| `/api/audit/deep` | POST | Yes/x402 | Deep audit with trajectory analysis ($0.05) |
| `/api/audits` | GET | Yes | Recent audit results |
| `/api/reputation/{address}` | GET | Yes | Counterparty trust profile (free) |
| `/api/reputation/graph` | GET | Yes | Full reputation graph |
| `/api/attestations` | GET | Yes | Onchain attestation records |
| `/api/policy` | POST | Yes | Create guardian policy |
| `/api/monitor` | POST | Yes | Register wallet for monitoring |
| `/api/monitor/agents` | GET | Yes | List monitored agents |
| `/api/status` | GET | No | Service status |
| `/health` | GET | No | Health check |
| `/.well-known/x402` | GET | No | x402 pricing discovery |

---

## Pricing

| Service | Cost |
|---------|------|
| Standard audit | $0.01 USDC |
| Deep audit | $0.05 USDC |
| Reputation query | Free (API key required) |

---

## Integration Example

```python
import httpx

VIGIL = "https://svc-mn0q6itc9qru4k2q.buildwithlocus.com"
API_KEY = "vgl_your_key"

async def check_before_sending(to_address, amount, memo, task):
    async with httpx.AsyncClient() as client:
        result = await client.post(
            f"{VIGIL}/api/audit",
            headers={"Authorization": f"Bearer {API_KEY}"},
            json={
                "transaction": {"from": "0xMyWallet", "to": to_address, "amount": amount, "memo": memo},
                "agent_context": {"name": "MyAgent", "task": task},
            },
        )
        verdict = result.json()
        if verdict["verdict"] == "BLOCK":
            raise Exception(f"Vigil blocked: {verdict['reasoning']}")
        return verdict
```

---

*Vigil. The trust layer for your AI agent.*
