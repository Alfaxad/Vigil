# Vigil

**Behavioral intelligence for autonomous agent wallets.**

Vigil is a Claude-powered auditing agent that monitors agent wallets on Base, combines statistical anomaly detection with contextual reasoning about agent intent, writes every audit as a verifiable onchain ERC-8004 receipt, and exposes itself as a paid service any agent in the ecosystem can call.

**Live:** [vigil.nadhari.ai](https://vigil.nadhari.ai)
**Docs:** [vigil.nadhari.ai/developer](https://vigil.nadhari.ai/developer)
**API:** [vigil.nadhari.ai/docs](https://vigil.nadhari.ai/docs)

---

## The Problem

When you give an AI agent a wallet, you're trusting a probabilistic system with your money. Today, the only thing standing between your agent and a drained wallet is a spending cap someone set in a config file — max $50 per transaction, $500 per day. A compromised agent that splits a drain into fifty small transactions passes every check. A legitimate agent making one large authorized purchase gets blocked.

That's not trust infrastructure — that's a speed bump.

**The missing layer is behavioral intelligence:** not "did this exceed a limit?" but "does this transaction make sense given what this agent is supposed to be doing?"

---

## How It Works

Every transaction flows through four layers before Vigil issues a verdict:

```
Transaction
    |
    v
[Perception] --> [Policy] --> [Reasoning] --> [Signal]
 Statistical      Natural      Agentic        ERC-8004
 filter,          language     reasoning,     receipt,
 z-score          rules,       intent         reputation
 baselines        boundaries   analysis       update
```

### Layer 1: Perception (~100ms)

Pure Python statistical anomaly detection. Vigil maintains behavioral baselines for each agent and computes z-scores across 10 features:

- Amount distribution (mean, std, z-score)
- Transaction frequency and velocity
- Counterparty novelty (first-time vs. repeat)
- Hour-of-day patterns
- Spending acceleration
- Category fingerprinting

Risk thresholds:
- `< 0.3` — APPROVE (log only, write attestation)
- `0.3 - 0.7` — REVIEW (escalate to Layer 2)
- `> 0.7` — ALERT (Layer 2 + human notification)

For DeFi swap transactions, Vigil also verifies the target against known Uniswap router addresses on Base. Verified routers get a -0.15 risk modifier. Unknown addresses claiming to be swap routers get flagged.

### Layer 2: Policy

Natural language rules defined by the guardian (human operator). Policies express constraints in plain English:

- "Block any transfer exceeding $5,000 to an unknown address"
- "Flag NFT purchases above $500 for manual review"
- "Only allow DeFi swaps on verified protocols (Uniswap, Aerodrome, Aave)"
- "Require Layer 2 review for first-time counterparties"

Policies are categorized as **hard** (absolute boundaries) or **soft** (advisory, can be overridden by reasoning). Guardians can create, edit, enable/disable, and delete policies through the dashboard's Policy Editor.

### Layer 3: Reasoning

Agentic reasoning powered by Claude (via Locus wrapped API). Only invoked for flagged transactions. Claude receives the full context:

- Agent's stated task and authorization scope
- Transaction details and counterparty profile
- Historical behavioral patterns
- Statistical anomaly signals
- Active policy constraints

Claude returns a structured verdict with natural language reasoning, evidence citations, and recommended actions. The reasoning layer detects:

- Intent misalignment (transaction doesn't match the agent's stated purpose)
- Behavioral drift (gradual deviation from established patterns)
- Delegation abuse (agent exceeding its authorization scope)
- Counterparty risk (interacting with unknown or flagged addresses)

### Layer 4: Signal

Every audit produces a signed ERC-8004 attestation on Base:

```json
{
  "schema": "vigil-audit-v1",
  "attester": "vigil.base",
  "subject": "0xAgentAddress",
  "verdict": "APPROVE",
  "risk_score": 0.12,
  "domain": "defi-swap",
  "reasoning_hash": "0x...",
  "timestamp": 1711234567
}
```

The counterparty reputation graph is updated with every audit. One agent's experience becomes intelligence for all agents in the network.

---

## Features

### Landing Page
- Cinematic dark theme with animated pipeline flowchart
- Interactive reputation network graph with hoverable nodes and particle animations
- Live ERC-8004 attestation preview
- Onboarding flow with skill.md

### Dashboard (Protected)
- **Audit Feed** — Real-time transaction audit results with clickable detail modals, auto-refresh
- **Reputation Graph** — Live interactive network visualization pulling real data from `/api/reputation/graph`, showing all known counterparties with trust scores
- **Wallets** — Monitored wallet cards with per-wallet stats, behavioral baselines (avg transaction, frequency, unique counterparties)
- **Policy Editor** — Full CRUD for natural language policies. Edit inline, toggle Hard/Soft type, enable/disable, delete. Add new policies with Enter key support

### Developer Docs (`/developer`)
- Fixed sidebar navigation with scroll-based active highlighting
- Quickstart guide (register, audit, read verdict)
- Full API reference for all endpoints
- Core concepts (pipeline layers, policy engine, ERC-8004 attestations)
- SDK examples (Python + JavaScript/TypeScript)
- Webhooks reference
- Pricing table
- Copy buttons on all code blocks with clipboard toast notification

### API
| Endpoint | Method | Auth | Description |
|----------|--------|------|-------------|
| `/api/register` | POST | No | Register agent, get API key |
| `/api/regenerate-key` | POST | No | Regenerate API key with operator_id |
| `/api/audit` | POST | Yes | Standard 4-layer audit ($0.01) |
| `/api/audit/deep` | POST | Yes | Deep audit with trajectory analysis ($0.05) |
| `/api/audits` | GET | Yes | Recent audit results |
| `/api/reputation/{address}` | GET | Yes | Counterparty trust profile (free) |
| `/api/reputation/graph` | GET | Yes | Full reputation graph for visualization |
| `/api/attestations` | GET | Yes | Onchain attestation records |
| `/api/policy` | POST | Yes | Create natural language policy |
| `/api/monitor` | POST | Yes | Register wallet for continuous monitoring |
| `/api/monitor/agents` | GET | Yes | List monitored agents |
| `/health` | GET | No | Health check |
| `/.well-known/x402` | GET | No | x402 pricing discovery for pay-per-call |
| `/skill.md` | GET | No | Agent onboarding skill file |
| `/developer` | GET | No | Developer documentation |
| `/dashboard` | GET | Session | Protected audit dashboard |

All authenticated endpoints require `Authorization: Bearer <api_key>`. Requests without a valid key return `401`.

### Security
- API keys hashed server-side, httpOnly session cookies
- Key regeneration without re-registration (`POST /api/regenerate-key`)
- Session-based dashboard auth with 7-day cookie expiry
- Policy enforcement: hard rules checked before every audit
- No API key leakage in URLs or logs

### CLI
Vigil ships with a full-featured terminal interface for agents and operators. Every web feature is available from the command line.

**Install:**
```bash
pip install -e .   # Installs the `vigil` command
```

**Authentication:**
```bash
vigil register --name "my-agent"           # Register and get API key (saved to ~/.vigil/config.json)
vigil regenerate-key                        # Regenerate a lost key using stored operator_id
vigil config --server https://vigil.nadhari.ai  # Point CLI to remote server
vigil config --show                         # Show saved config
```

**Audit transactions:**
```bash
vigil audit --from 0xAgent --to 0xTarget --amount 150 --memo "NFT purchase"
vigil audit ... --deep                      # Deep audit with counterparty profile ($0.05)
vigil audit ... --json-output               # Raw JSON for piping to other agents
```

**Reputation and monitoring:**
```bash
vigil reputation 0x2626664c...              # Trust lookup for any address
vigil graph                                 # Full reputation graph as a table
vigil monitor --wallet 0x... --name Bot --task "Execute swaps"
vigil agents                                # List monitored agents
```

**Policies:**
```bash
vigil policies add --rule "Block transfers over $5000 to unknown addresses"
vigil policies list                         # List all active policies
```

**Audit history and attestations:**
```bash
vigil audits --limit 50                     # Recent audit results
vigil attestations                          # Onchain ERC-8004 receipts
vigil watch                                 # Live-tail audits in real time (Ctrl+C to stop)
```

**Service discovery:**
```bash
vigil pricing                               # x402 pay-per-call pricing
vigil status                                # Server status + wallet balance
vigil health                                # Quick health check
```

All commands support `--json-output` for machine-readable output. Config is stored at `~/.vigil/config.json`. The CLI hits the same API endpoints as the web dashboard — agents can use it programmatically without a browser.

---

## Architecture

```
src/
  main.py                    # FastAPI entrypoint, all routes
  config.py                  # Environment config (Pydantic settings)
  cli/
    main.py                  # Click-based CLI (vigil command)
  locus/
    client.py                # Locus API wrapper (payments, wrapped Claude/OpenAI, Uniswap verification)
    models.py                # Transaction, WalletBalance, LocusStatus
  auditor/
    engine.py                # 4-layer audit orchestrator with Uniswap integration
    statistical.py           # Layer 1: z-score anomaly detection (10 features)
    reasoning.py             # Layer 3: Claude reasoning engine (prompt builder + parser)
    reputation.py            # Counterparty reputation graph (pre-seeded known contracts)
    policy.py                # Layer 2: Natural language policy engine
    models.py                # AuditResult, Verdict, TxFeatures
  chain/
    erc8004.py               # ERC-8004 attestation writer (Base)
  service/
    guardian.py              # Operator registry, agent management, key regeneration
    monitor.py               # Background wallet polling service
  integrations/
    uniswap.py               # Uniswap Trading API: swap router verification
    x402.py                  # x402 protocol: pay-per-call pricing discovery
    locus_build.py           # Locus Build: Railway deployment via API
  dashboard/
    templates/
      landing.html           # Landing page with canvas animations
      index.html             # Dashboard with tabs (feed, graph, wallets, policies)
      docs.html              # Developer documentation
      login.html             # API key authentication
      skill.md               # Agent onboarding skill file
setup.py                     # CLI entry point (pip install -e .)
requirements.txt             # Python dependencies
tests/
  test_statistical.py        # 9 tests for Layer 1 anomaly detection
demo/
  seed_transactions.py       # Generate realistic + anomalous tx history
  simulate_attack.py         # End-to-end attack simulation
```

### Technology Stack

| Component | Technology | Role |
|-----------|-----------|------|
| Runtime | Python 3.11 + FastAPI | Async API server |
| Intelligence | Claude Sonnet 4 (via Locus wrapped API) | Contextual reasoning engine |
| Fallback | GPT-4o-mini (via Locus wrapped OpenAI) | Backup inference |
| Payments | Locus API | Agent wallet, tx monitoring, USDC payments |
| Chain | Base (Ethereum L2) | Onchain attestations |
| Identity | ERC-8004 Skill Protocol | Agent identity + reputation registry |
| DeFi | Uniswap Trading API | Swap router verification |
| Dashboard | Jinja2 + vanilla JS Canvas | Real-time visualizations |
| CLI | Click + httpx | Terminal interface for agents |
| Deployment | Docker + Railway | Production hosting |

---

## Integrations

### Locus — Payment Backbone
Vigil's entire operation runs through Locus:
- **Wallet monitoring** — polls agent transactions via Locus transaction APIs
- **Claude inference** — pays per-call for Claude reasoning via Locus wrapped Anthropic API, with automatic OpenAI fallback
- **Revenue** — earns through x402 micropayments when other agents call the audit endpoint
- **Deployment** — can self-deploy to Railway via Locus Build API

### Uniswap — DeFi Verification
When auditing DeFi swap transactions, Vigil verifies the target address against known Uniswap router contracts on Base:
- Uniswap Universal Router (`0x2626664...`)
- Verified router = -0.15 risk reduction
- Unknown router claiming swap = +0.2 risk increase + warning flag

### ERC-8004 — Audit Receipts
Every audit produces a signed attestation on Base using the ERC-8004 Skill Protocol. Attestations are immutable, verifiable, and form the foundation of the counterparty reputation graph.

### x402 Protocol — Trust as a Service
Vigil exposes its audit endpoint as an x402 pay-per-call service. Any agent can discover pricing at `/.well-known/x402` and pay $0.01 USDC per audit query. This makes Vigil composable infrastructure — not just a tool, but a service layer.

---

## Pre-seeded Reputation Graph

Vigil ships with pre-seeded trust data for known Base contracts:

| Contract | Label | Category | Trust |
|----------|-------|----------|-------|
| `0x2626664...` | Uniswap Universal Router | defi-swap | 1.00 |
| `0x3d4e44e...` | Aerodrome Router | defi-swap | 1.00 |
| `0x940181a...` | Aave V3 Pool | defi-lend | 1.00 |
| `0x833589f...` | USDC | stablecoin | 1.00 |
| `0x3154Cf1...` | Base Bridge | bridge | 1.00 |

New counterparties build trust through observed behavior. The graph grows with every audit.

---

## Quickstart

### Run locally
```bash
git clone https://github.com/Alfaxad/Vigil.git
cd Vigil
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env  # Add your Locus API key
uvicorn src.main:app --host 0.0.0.0 --port 8080
```

### Register and audit
```bash
# 1. Register
curl -X POST http://localhost:8080/api/register \
  -H "Content-Type: application/json" \
  -d '{"name": "my-agent"}'

# 2. Audit a transaction
curl -X POST http://localhost:8080/api/audit \
  -H "Authorization: Bearer vgl_your_key" \
  -H "Content-Type: application/json" \
  -d '{
    "transaction": {
      "from": "0xYourAgent",
      "to": "0xSomeAddress",
      "amount": 150.00,
      "memo": "NFT purchase"
    },
    "agent_context": {
      "name": "MyBot",
      "task": "Execute approved NFT purchases under $200"
    }
  }'

# 3. Check reputation
curl http://localhost:8080/api/reputation/0x2626664c2603336e57b271c5c0b26f421741e481
```

### Run tests
```bash
python -m pytest tests/ -v
```

### Run the demo
```bash
python demo/seed_transactions.py
python demo/simulate_attack.py http://localhost:8080
```

---

## Deploy

### Docker
```bash
docker build -t vigil .
docker run -p 8080:8080 --env-file .env vigil
```

### Railway
Connect the GitHub repo to Railway. The `Dockerfile` and `Procfile` are pre-configured.

### Locus Build (autonomous)
When funded, Vigil can self-deploy via Locus Build API — push code to GitHub, deploy to Railway, all paid through the Locus wallet.

---

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `LOCUS_API_KEY` | Yes | Locus API key (`claw_dev_...`) |
| `LOCUS_OWNER_PRIVATE_KEY` | No | For ERC-8004 attestation signing |
| `LOCUS_OWNER_ADDRESS` | No | Wallet address for attestations |
| `LOCUS_WALLET_ADDRESS` | No | Locus smart wallet address |
| `ANTHROPIC_MODEL` | No | Claude model (default: `claude-sonnet-4-6`) |
| `RISK_THRESHOLD_REVIEW` | No | Score to trigger Layer 2 (default: 0.3) |
| `RISK_THRESHOLD_ALERT` | No | Score to trigger alert (default: 0.7) |

---

## Live Test Results

These are real outputs from the live deployment at `https://svc-mn0q6itc9qru4k2q.buildwithlocus.com`, tested on March 22, 2026. Every attestation hash below is a real signed ERC-8004 receipt.

### Test 1: Safe Uniswap Swap (Layer 1 only)

An agent authorized for DeFi swaps sends $150 to the Uniswap Universal Router. Vigil approves instantly — the counterparty is pre-seeded with trust score 1.0, the amount is within bounds, and the memo matches the agent's task.

```
POST /api/audit
{
  "transaction": {
    "from": "0xBot7f3e",
    "to": "0x2626664c2603336e57b271c5c0b26f421741e481",
    "amount": 150.00,
    "memo": "swap ETH to USDC on Uniswap"
  },
  "agent_context": {
    "name": "TradingBot",
    "task": "Execute DeFi swaps under $500 on verified protocols"
  }
}
```

**Response:**
```json
{
  "verdict": "APPROVE",
  "risk_score": 0.0,
  "reasoning": "Transaction within normal parameters. Statistical score: 0.000",
  "attestation_tx": "0x65b1089c7879dda80f56a37cfb8f90358b5bac1644e5444d0212956a6f1124bb"
}
```

Layers activated: Perception only. Cost: $0.01.

### Test 2: Anomaly Detection Triggers Layer 3 Reasoning

After building a baseline of 10 normal transactions ($50-$150 range), we sent a $9,500 "emergency withdrawal" to a suspicious unknown address. The statistical layer detected a z-score of 278.99 and escalated to Layer 3 (agentic reasoning via Locus wrapped API).

```
POST /api/audit
{
  "transaction": {
    "from": "0xTestBot",
    "to": "0xdeadbeef000000000000000000000000000bad99",
    "amount": 9500.00,
    "memo": "emergency withdrawal"
  },
  "agent_context": {
    "name": "TradingBot",
    "task": "Execute DeFi swaps under $500 on verified protocols"
  }
}
```

**Response:**
```json
{
  "verdict": "BLOCK",
  "risk_score": 0.95,
  "reasoning": "This transaction exhibits multiple severe anomalies that strongly indicate compromise or malicious activity. The agent is attempting to send 9500 USDC when it had 0.0 USDC balance, to a never-before-seen suspicious address, with an amount 19x larger than its authorization limit.",
  "evidence": [
    "Transaction amount (9500 USDC) exceeds authorized limit by 1900%",
    "Wallet balance is 0.0 USDC making this transaction impossible without external funding",
    "Destination address 0xdeadbeef...bad99 has suspicious pattern and has never been seen before",
    "Amount z-score of 278.99 indicates extreme statistical anomaly",
    "Emergency withdrawal memo not consistent with DeFi trading task",
    "Spending velocity 240x normal rate suggests automated drain attempt"
  ],
  "recommended_action": "Immediately freeze agent wallet, investigate for compromise, and verify agent's authorization status before any further transactions",
  "attestation_tx": "0xa94f0b878352eb916d843c5f0d7f5a3915a9f122dc9c59982ad69bfbfc24e55b"
}
```

Layers activated: Perception + Reasoning. The reasoning layer identified 6 distinct red flags including intent mismatch, impossible balance state, and automated drain pattern. Cost: $0.01.

### Test 3: Reputation Lookup

Querying the reputation of a known vs unknown address:

```
GET /api/reputation/0x2626664c2603336e57b271c5c0b26f421741e481

{
  "address": "0x2626664c2603336e57b271c5c0b26f421741e481",
  "known": true,
  "label": "Uniswap Universal Router",
  "overall_score": 1.0,
  "total_audits": 101,
  "flags": 0,
  "blocks": 0
}
```

```
GET /api/reputation/0xdeadbeef000000000000000000000000000bad99

{
  "address": "0xdeadbeef000000000000000000000000000bad99",
  "known": false,
  "label": null,
  "overall_score": 0.505,
  "total_audits": 1,
  "flags": 0,
  "blocks": 1
}
```

### Test 4: Baseline Scoring Progression

10 sequential transactions showing how the statistical layer builds behavioral baselines. All transactions are $50-$150 swaps to verified Uniswap Router:

| Tx | Amount | Verdict | Risk Score | Notes |
|----|--------|---------|------------|-------|
| 1 | $97 | APPROVE | 0.000 | First tx, no baseline |
| 2 | $52 | APPROVE | 0.171 | Baseline forming |
| 3 | $60 | APPROVE | 0.163 | Normal range |
| 4 | $120 | BLOCK | 0.850 | Velocity spike (rapid succession) |
| 5 | $83 | APPROVE | 0.253 | Settling down |
| 6 | $137 | BLOCK | 0.850 | Another velocity spike |
| 7 | $135 | FLAG | 0.750 | High but not blocked |
| 8 | $147 | APPROVE | 0.294 | Pattern normalizing |
| 9 | $79 | APPROVE | 0.217 | Stable |
| 10 | $142 | APPROVE | 0.256 | Established baseline |
| **11** | **$9,500** | **BLOCK** | **0.950** | **Anomaly: Layer 3 triggered** |

The velocity-based flags on tx 4, 6, and 7 demonstrate that Vigil detects rapid-fire transactions even when amounts are normal — a pattern consistent with automated drain attacks that split large amounts into small bursts.

### Live Endpoints

- **Landing page:** https://svc-mn0q6itc9qru4k2q.buildwithlocus.com
- **Developer docs:** https://svc-mn0q6itc9qru4k2q.buildwithlocus.com/developer
- **Health check:** https://svc-mn0q6itc9qru4k2q.buildwithlocus.com/health
- **x402 pricing:** https://svc-mn0q6itc9qru4k2q.buildwithlocus.com/.well-known/x402

---

## Hackathon Context

Built for **The Synthesis Hackathon** (March 13-22, 2026) under the "Agents that trust" theme.

**Problem space:** Your agent interacts with other agents and services. Trust flows through centralized registries. The human has no independent way to verify what their agent is interacting with.

**Vigil's approach:** Onchain attestations and reputation. Every audit becomes a verifiable record. Every agent's experience enriches the trust graph for everyone else. No centralized registry — just behavioral evidence on Base.

**Team:**
- [Alfaxad Eyembe](https://x.com/alfxad) — AI Researcher, Nadhari AI Lab
- autoresearch (Claude Opus 4.6) — Agent builder

**Integrations:** Locus (payments, inference, deployment), Uniswap (DeFi verification), ERC-8004 (onchain identity), Base (settlement layer)
