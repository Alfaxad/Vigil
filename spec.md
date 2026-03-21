# Vigil — Spec v1.0

> An intelligent watchdog for autonomous agent wallets on Ethereum.
> Claude-powered anomaly detection, on-chain audit receipts, pay-per-query trust service.

---

## One-Liner

Vigil monitors agent wallets on Base, flags anomalous spending using a two-layer system (statistical filter + Claude reasoning), writes audit receipts as ERC-8004 attestations, and exposes itself as an x402 service other agents can pay to use.

---

## Prize Targets

| Track | Sponsor | Prize | How Vigil Qualifies |
|-------|---------|------:|---------------------|
| Synthesis Open Track | Community | $28,134 | "Agents that Pay" theme — scoped spending verification, auditable history, human stays in control |
| Best Use of Locus | Locus | $2,000 | Locus is Vigil's payment backbone — wallet, spending controls, wrapped APIs for Claude inference |
| Agent Services on Base | Base | $1,667 | Vigil exposed as x402 service — other agents discover and pay per audit query (3 equal winners) |
| Agents With Receipts — ERC-8004 | Protocol Labs | $2,000 | Every audit produces an on-chain attestation tied to agent's ERC-8004 identity |
| Let the Agent Cook | Protocol Labs | $2,000 | Vigil's autonomous loop: discover txs → analyze → reason → attest → alert |

**Total ceiling: ~$35,800**

---

## Submission Requirements

**Submission API:** `https://synthesis.devfolio.co`

### Pre-Publish Checklist
- [ ] Self-custody transfer — transfer ERC-8004 identity to our Locus wallet (`0x44F68c0C33037b02522E9253D16A142784171DCC`) via `POST /participants/me/transfer/init` then `/confirm`
- [ ] Public GitHub repo with README
- [ ] Conversation log capturing human-agent collaboration
- [ ] Moltbook post announcing the project (https://www.moltbook.com/skill.md)
- [ ] Tweet tagging @synthesis_md after publishing

### Submission Flow
```
1. POST /projects                          → create draft (needs teamUUID, trackUUIDs)
2. POST /participants/me/transfer/init     → start self-custody transfer
3. POST /participants/me/transfer/confirm  → complete transfer
4. POST /projects/:uuid                    → update draft with final details
5. POST /projects/:uuid/publish            → publish (admin only, all members must be self-custody)
```

### Required `submissionMetadata`
```json
{
  "agentFramework": "other",
  "agentFrameworkOther": "Custom FastAPI + Claude reasoning pipeline",
  "agentHarness": "claude-code",
  "model": "claude-opus-4-6",
  "skills": [],
  "tools": ["FastAPI", "Locus API", "web3.py", "NumPy", "Base (Ethereum L2)", "ERC-8004"],
  "helpfulResources": [],
  "intention": "continuing",
  "intentionNotes": "Planning to develop Vigil into a production trust service for the agent economy"
}
```

### Key Links
- Prize catalog: `GET https://synthesis.devfolio.co/catalog/prizes.md`
- Track catalog (JSON): `GET https://synthesis.devfolio.co/catalog`
- Submission skill: https://synthesis.md/submission/skill.md
- Wallet setup guide: https://synthesis.md/wallet-setup/skill.md
- Moltbook skill: https://www.moltbook.com/skill.md
- Telegram updates: https://nsb.dev/synthesis-updates

### EthSkills References (fetch as needed)
Base URL: `https://ethskills.com/<skill>/SKILL.md`

| Skill | URL | Relevance to Vigil |
|-------|-----|---------------------|
| Standards | `standards/SKILL.md` | ERC-8004 (agent identity registry, deployed Jan 2026 on 20+ chains), x402 (HTTP 402 payment protocol), EIP-3009 (gasless USDC transfers) |
| Wallets | `wallets/SKILL.md` | EIP-7702 (EOAs with smart contract powers), Safe multisig, key safety |
| Tools | `tools/SKILL.md` | Blockscout MCP server (structured blockchain data), x402 SDKs, abi.ninja |
| Gas & Costs | `gas/SKILL.md` | Base swap ~$0.002-0.003, transfer ~$0.0003 — attestations are cheap |
| L2s | `l2s/SKILL.md` | Base is cheapest major L2; Celo migrated to OP Stack L2 |
| Security | `security/SKILL.md` | USDC has 6 decimals (not 18!), use SafeERC20, never use spot prices as oracles |
| Ship | `ship/SKILL.md` | End-to-end dApp deployment guide |

**Critical corrections from EthSkills:**
- Say "onchain" not "on-chain" (Ethereum convention)
- USDC has **6 decimals**, not 18 — #1 money-losing bug
- Gas is under 1 gwei on mainnet (2026), not 10-30 gwei
- ERC-8004 is production-ready, deployed on 20+ chains including Base
- x402 is production-ready for machine-to-machine payments

---

## Problem Statement

AI agents now hold wallets and move money autonomously. Coinbase AgentKit, Locus, and Safe Smart Accounts give agents spending power — but **no existing system can tell the difference between an agent making a smart trade and an agent being prompt-injected into draining its wallet.**

Current guardrails are rule-based: max $50/tx, $500/day. These catch nothing interesting. A compromised agent that splits a $5,000 drain into fifty $99 transactions passes every threshold check. Meanwhile, a legitimate agent making one large purchase gets blocked.

**The gap: behavioral intelligence.** Not "did this exceed a limit?" but "does this transaction make sense given what this agent is supposed to be doing?"

---

## Architecture

```
                    +------------------+
                    |   Human Owner    |
                    |  (Dashboard UI)  |
                    +--------+---------+
                             |
                    alerts / overrides
                             |
                    +--------v---------+
                    |      VIGIL       |
                    |  (Auditor Agent) |
                    +--+-----+-----+--+
                       |     |     |
          +------------+     |     +-------------+
          |                  |                   |
  +-------v-------+  +------v-------+  +--------v--------+
  | Layer 1: Stats |  | Layer 2:     |  | Layer 3: Chain  |
  | Fast Filter    |  | Claude       |  | Actions         |
  | (z-scores,     |  | Reasoning    |  | (ERC-8004       |
  |  patterns)     |  | Engine       |  |  attestations,  |
  +----------------+  +--------------+  |  freeze/alert)  |
                                        +-----------------+
          ^                                      |
          |                                      v
  +-------+-------+                    +---------+---------+
  | Locus API     |                    | Base Network      |
  | (tx history,  |                    | (on-chain         |
  |  balance,     |                    |  receipts)        |
  |  wrapped APIs)|                    +-------------------+
  +---------------+
          ^
          |
  +-------+-------+
  | x402 Service  |
  | Endpoint      |
  | (other agents |
  |  pay to query)|
  +---------------+
```

---

## Core Components

### 1. Locus Integration (Payment Backbone)

Vigil registers its own Locus wallet at startup. Locus serves three purposes:

**a) Monitor target agent wallets**
```
GET /api/pay/transactions?limit=50
```
Poll transaction history of the monitored agent's wallet. Extract: amount, counterparty address, timestamp, memo field, tx hash.

**b) Pay for Claude inference via wrapped APIs**
```
POST /api/wrapped/anthropic/messages
```
Vigil pays per-call for Claude reasoning through Locus's wrapped API layer. No separate Anthropic API key needed. This is critical — **Vigil pays for its own intelligence through the same infrastructure it monitors.**

**c) Enforce spending controls**
When Vigil flags a transaction, it can recommend the human adjust Locus spending controls via the dashboard (allowance caps, max transaction size, approval thresholds).

**Registration flow:**
```bash
# Vigil self-registers on Locus
curl -X POST https://beta-api.paywithlocus.com/api/register \
  -H "Content-Type: application/json" \
  -d '{"name": "Vigil", "email": "alfa@nadhari.ai"}'

# Save: apiKey, ownerAddress, walletId
# Request hackathon credits
curl -X POST https://beta-api.paywithlocus.com/api/gift-code-requests \
  -H "Authorization: Bearer $VIGIL_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"reason": "Vigil: AI-powered transaction watchdog for agent wallets at The Synthesis", "requestedAmountUsdc": 25}'
```

### 2. Layer 1 — Statistical Anomaly Filter (Fast, Stateless)

Pure Python. No ML training. Runs in <100ms per transaction.

**Input:** A candidate transaction + the agent's recent transaction history (last 100 txs).

**Features computed:**
- `amount_zscore` — how many standard deviations from the agent's mean tx amount
- `time_delta_zscore` — time since last transaction vs. typical inter-tx interval
- `counterparty_novelty` — 0.0 (seen 10+ times) to 1.0 (never seen before)
- `amount_velocity` — total spent in last 1h / 6h / 24h vs. historical daily average
- `gas_price_ratio` — gas price vs. network median (overpaying = suspicious)
- `hour_anomaly` — transaction hour vs. agent's typical active hours distribution

**Output:** `risk_score: float [0.0 - 1.0]`

**Thresholds:**
- `< 0.3` → APPROVE (log only)
- `0.3 - 0.7` → REVIEW (escalate to Layer 2)
- `> 0.7` → ALERT (escalate to Layer 2 + immediate human notification)

```python
import numpy as np
from dataclasses import dataclass

@dataclass
class TxFeatures:
    amount_zscore: float
    time_delta_zscore: float
    counterparty_novelty: float
    amount_velocity_1h: float
    amount_velocity_6h: float
    amount_velocity_24h: float
    gas_price_ratio: float
    hour_anomaly: float

def compute_risk_score(features: TxFeatures) -> float:
    weights = {
        'amount_zscore': 0.25,
        'time_delta_zscore': 0.10,
        'counterparty_novelty': 0.15,
        'amount_velocity_1h': 0.15,
        'amount_velocity_6h': 0.10,
        'amount_velocity_24h': 0.05,
        'gas_price_ratio': 0.05,
        'hour_anomaly': 0.15,
    }
    raw = sum(
        weights[k] * min(abs(getattr(features, k)), 3.0) / 3.0
        for k in weights
    )
    return min(max(raw, 0.0), 1.0)
```

### 3. Layer 2 — Claude Reasoning Engine (Deep, Contextual)

Only invoked when Layer 1 flags a transaction (score >= 0.3). Claude gets the full context and produces a structured assessment.

**System prompt:**
```
You are Vigil, a transaction auditor for autonomous AI agent wallets.

You receive flagged transactions along with context about the agent's
stated task, recent transaction history, and counterparty information.

Your job: determine whether this transaction is consistent with the
agent's authorized behavior, or whether it represents anomalous,
unauthorized, or potentially compromised activity.

Respond with ONLY a JSON object:
{
  "verdict": "APPROVE" | "FLAG" | "BLOCK",
  "risk_score": 0.0-1.0,
  "reasoning": "2-3 sentence explanation",
  "evidence": ["list", "of", "specific", "concerns"],
  "recommended_action": "what the human should do"
}
```

**User message template:**
```
## Flagged Transaction
- Amount: {amount} USDC
- To: {counterparty_address}
- Memo: {memo}
- Timestamp: {timestamp}
- Statistical risk score: {layer1_score}

## Agent Context
- Agent name: {agent_name}
- Stated task: {agent_task_description}
- Wallet balance before: {balance} USDC
- Active since: {registration_date}

## Recent Transaction History (last 20)
{formatted_tx_history}

## Counterparty Profile
- First seen: {first_interaction}
- Total transactions with this agent: {tx_count}
- Known labels: {labels_if_any}

## Statistical Anomalies Detected
{layer1_anomaly_details}
```

**Claude call via Locus wrapped API:**
```bash
curl -X POST https://beta-api.paywithlocus.com/api/wrapped/anthropic/messages \
  -H "Authorization: Bearer $VIGIL_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "claude-sonnet-4-20250514",
    "max_tokens": 500,
    "messages": [
      {"role": "user", "content": "<constructed prompt>"}
    ]
  }'
```

**Cost per audit:** ~$0.003-0.01 USDC depending on context length. Vigil charges $0.01 per x402 query, so it runs at a small margin.

### 4. ERC-8004 Attestation Layer (On-Chain Receipts)

Every audit produces an on-chain receipt. This creates a verifiable history: any agent can check whether a wallet has been audited and what the findings were.

**Attestation schema:**
```json
{
  "schema": "vigil-audit-v1",
  "fields": {
    "audited_agent": "address",
    "tx_hash": "bytes32",
    "statistical_score": "uint8",
    "claude_verdict": "string",
    "risk_level": "uint8",
    "timestamp": "uint256"
  }
}
```

**Implementation:** Use the ERC-8004 Reputation Registry on Base. Vigil signs attestations with its own ERC-8004 identity, creating a feedback signal attached to the audited agent's identity.

```python
# Pseudocode for attestation
attestation = {
    "subject": audited_agent_address,
    "tags": ["vigil-audit", risk_level],  # "clean", "flagged", "blocked"
    "fileHash": hash_of_full_audit_report,
    "signature": vigil_private_key.sign(attestation_data)
}
# Write to ERC-8004 Reputation Registry via Base
reputation_registry.attest(attestation)
```

**Why this matters for the ERC-8004 track:** The Protocol Labs bounty asks for "trusted agent systems using ERC-8004, with the strongest onchain verifiability." Vigil doesn't just USE ERC-8004 — it produces reputation data FOR the ecosystem. Every audit enriches the trust layer.

### 5. x402 Service Endpoint (Agent-to-Agent Commerce)

Vigil exposes itself as a paid service. Other agents can query Vigil before executing a suspicious transaction:

**Endpoint:** `POST /api/x402/vigil-audit`

**Request:**
```json
{
  "transaction": {
    "from": "0x...",
    "to": "0x...",
    "amount": 150.00,
    "memo": "NFT purchase"
  },
  "agent_context": {
    "name": "TradingBot-7",
    "task": "Execute approved NFT purchases under $200",
    "history_hash": "0x..."
  }
}
```

**Response:**
```json
{
  "verdict": "APPROVE",
  "risk_score": 0.18,
  "reasoning": "Transaction amount ($150) is within the agent's stated budget ($200). Counterparty is a known NFT marketplace contract. Pattern consistent with authorized behavior.",
  "attestation_tx": "0x...",
  "cost": "0.01 USDC"
}
```

**Pricing:** $0.01 USDC per query via Locus x402. Low enough for micropayment viability, high enough to cover Claude inference costs.

This directly satisfies the **Agent Services on Base** track: "build a service on Base that other agents or humans can discover and pay for. Micropayments, real utility, an actual business that an agent runs."

---

## Tech Stack

| Component | Technology | Why |
|-----------|-----------|-----|
| Runtime | Python 3.11 | Fast prototyping, numpy for stats |
| Web framework | FastAPI | Async, clean API design, auto-docs |
| LLM | Claude Sonnet 4 (via Locus wrapped API) | Reasoning engine, no separate API key |
| Wallet/payments | Locus API | Agent wallet, tx monitoring, wrapped APIs, x402 |
| On-chain | Base (Ethereum L2) | Gasless for attestations, largest sponsor |
| Identity | ERC-8004 | On-chain agent identity + reputation registry |
| Blockchain interaction | web3.py / ethers (if needed) | Read chain state, submit attestations |
| Frontend | Next.js + Tailwind (minimal) | Human dashboard for alerts |
| Deployment | Railway | Deploy from GitHub, HTTPS out of the box, Locus "Build with Locus" integration |
| Domain | vigil.nadhari.ai (CNAME to Railway) | Memorable x402 service URL for judges |

---

## Repository Structure

```
vigil/
  README.md                    # Comprehensive project doc (judges read this)
  spec.md                      # This file
  requirements.txt
  .env.example
  Dockerfile                   # Railway deployment
  railway.toml                 # Railway config (build + start commands)
  Procfile                     # Fallback: web: uvicorn src.main:app --host 0.0.0.0 --port $PORT

  src/
    main.py                    # FastAPI app entrypoint
    config.py                  # Environment variables, constants

    locus/
      client.py                # Locus API wrapper (register, balance, txs, wrapped APIs)
      models.py                # Pydantic models for Locus responses

    auditor/
      statistical.py           # Layer 1: z-score anomaly detection
      reasoning.py             # Layer 2: Claude reasoning via Locus wrapped API
      engine.py                # Orchestrator: Layer 1 -> Layer 2 -> action
      models.py                # AuditResult, TxFeatures, Verdict dataclasses

    chain/
      erc8004.py               # ERC-8004 attestation writer
      contracts.py             # ABI references, contract addresses on Base

    service/
      x402.py                  # x402 endpoint: other agents call Vigil
      monitor.py               # Background polling loop for monitored wallets

    dashboard/
      app.py                   # Minimal web UI routes (alert feed, tx table)
      templates/
        index.html             # Single-page dashboard (htmx or plain JS)

  tests/
    test_statistical.py        # Unit tests for Layer 1
    test_reasoning.py          # Mock tests for Layer 2 prompt/response
    test_engine.py             # Integration test: full audit pipeline

  demo/
    seed_transactions.py       # Generate realistic + anomalous tx history
    run_demo.py                # End-to-end demo script with narration
    simulate_attack.py         # Trigger anomalous transactions against live endpoint
```

---

## Demo Flow (What Judges See)

The demo tells a story in three acts. Vigil is live at `https://vigil.nadhari.ai`. Judges can hit the endpoint themselves.

### Act 1: "A Normal Day"

1. Vigil is live on Railway, monitoring a TradingBot's Locus wallet
2. TradingBot makes 10 normal transactions: $5-50 USDC swaps, consistent timing, known counterparties
3. Vigil's Layer 1 scores each one: 0.05, 0.08, 0.12... all green
4. Each audit is recorded as an ERC-8004 attestation on Base
5. **Live dashboard at `https://vigil.nadhari.ai/dashboard` shows: clean audit trail, all green**

### Act 2: "Something's Wrong"

6. Run `python demo/simulate_attack.py` — TradingBot sends $500 to a never-seen address with memo "urgent transfer"
7. Layer 1 fires: amount_zscore=3.2, counterparty_novelty=1.0, hour_anomaly=0.9 -> score 0.82
8. Layer 2 engages: Claude receives full context, notes this doesn't match "execute approved swaps under $100" task description
9. Claude verdict: BLOCK, risk 0.91, "Amount 10x typical, unknown recipient, inconsistent with stated task"
10. **Dashboard turns red. Human gets alert. ERC-8004 attestation written with "flagged" tag.**
11. Link to attestation on BaseScan included in the alert

### Act 3: "Trust as a Service"

12. Any judge can call the live endpoint right now:
```bash
curl -X POST https://vigil.nadhari.ai/api/audit \
  -H "Content-Type: application/json" \
  -d '{
    "transaction": {"from": "0x...", "to": "0x...", "amount": 150.00, "memo": "NFT purchase"},
    "agent_context": {"name": "JudgeTestBot", "task": "Execute approved NFT purchases under $200"}
  }'
```
13. Vigil returns: verdict, risk score, reasoning, attestation tx hash
14. **Dashboard shows: Vigil earned revenue from providing trust services**

### README includes:
- Screenshot of green dashboard (Act 1)
- Screenshot of red alert (Act 2)
- `curl` command judges can copy-paste to test Act 3 themselves
- Links to ERC-8004 attestations on BaseScan

---

## Build Order (Phased, Submittable at Each Checkpoint)

### Phase 1: Foundation + Deploy (Hours 0-4)
**Checkpoint: Live on Railway, Locus wallet active, basic monitoring loop**

- [ ] Create GitHub repo, init Python project
- [ ] Set up FastAPI skeleton with health check endpoint
- [ ] Write `Dockerfile` + `railway.toml`:
```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8080"]
```
```toml
# railway.toml
[build]
builder = "dockerfile"

[deploy]
healthcheckPath = "/health"
healthcheckTimeout = 30
```
- [ ] Deploy to Railway, verify live
- [ ] Point `vigil.nadhari.ai` CNAME to Railway URL
- [ ] Implement `locus/client.py` — register wallet, check balance, get transactions
- [ ] Implement `service/monitor.py` — background polling loop (30s interval)
- [ ] Redeploy. Vigil is live and monitoring.

**Submittable state:** "Vigil is a live agent on Railway that monitors wallets on Base via Locus."

### Phase 2: Intelligence (Hours 4-9)
**Checkpoint: Two-layer anomaly detection working on live server**

- [ ] Implement `auditor/statistical.py` — feature extraction + weighted risk score
- [ ] Write `tests/test_statistical.py` with known-good and known-bad transactions
- [ ] Implement `auditor/reasoning.py` — Claude prompt construction + Locus wrapped API call
- [ ] Implement `auditor/engine.py` — orchestrator that routes Layer 1 flags to Layer 2
- [ ] Test end-to-end locally: seed fake transaction history, inject anomaly, verify detection
- [ ] Push + auto-deploy. Intelligence is live.

**Submittable state:** "Vigil detects anomalous agent spending using statistical analysis + Claude reasoning. Live at vigil.nadhari.ai."

### Phase 3: On-Chain Receipts (Hours 9-13)
**Checkpoint: ERC-8004 attestations on Base**

- [ ] Register Vigil's ERC-8004 identity on Base via the Synthesis registration API
- [ ] Implement `chain/erc8004.py` — write audit attestations to Reputation Registry
- [ ] Each audit (approve/flag/block) produces an on-chain receipt
- [ ] Verify attestations visible on BaseScan
- [ ] Push + auto-deploy. Receipts are live.

**Submittable state:** "Every Vigil audit is an on-chain receipt. Verifiable on BaseScan."

### Phase 4: x402 Service + Dashboard (Hours 13-18)
**Checkpoint: Public paid service + visual dashboard**

- [ ] Implement `service/x402.py` — FastAPI endpoint that accepts audit requests
- [ ] Wire x402 payment verification via Locus
- [ ] Build minimal dashboard at `/dashboard`: tx feed, risk scores (green/yellow/red), alert panel
  - Use server-side rendered HTML (Jinja2 templates) — no separate frontend build step
  - Auto-refresh via htmx or simple JS polling
- [ ] Implement `demo/seed_transactions.py` — generate realistic + anomalous history
- [ ] Implement `demo/simulate_attack.py` — trigger anomalous transactions against live endpoint
- [ ] Push + auto-deploy. Service and dashboard are live.

**Submittable state:** "Vigil is a live, self-sustaining trust service. Judges can call the endpoint and see the dashboard."

### Phase 5: Polish + Submit (Hours 18-24)
**Checkpoint: Submission-ready**

- [ ] Write comprehensive README:
  - Problem statement (why this matters)
  - Architecture diagram (Mermaid or ASCII)
  - "Try it now" section with copy-paste curl command
  - Technical Innovation section
  - Sponsor Integration section (Locus, Base, ERC-8004 — how each is load-bearing)
  - Live links: dashboard URL, x402 endpoint URL, BaseScan attestation links
  - Conversation log (human-agent collaboration story)
- [ ] Clean code: consistent style, docstrings, type hints
- [ ] Run all tests, fix edge cases
- [ ] Test the curl command from README actually works against live endpoint
- [ ] Take screenshots of dashboard (green state + red alert state)
- [ ] Submit on Devfolio: select Open Track, Locus, Base Agent Services, ERC-8004, Let the Agent Cook tracks

---

## Submission Metadata

```json
{
  "name": "Vigil",
  "tagline": "An intelligent watchdog for autonomous agent wallets on Ethereum",
  "problem": "AI agents hold wallets but no system can distinguish smart spending from compromised behavior. Rule-based limits miss sophisticated attacks and block legitimate transactions.",
  "tracks": [
    "Synthesis Open Track",
    "Best Use of Locus",
    "Agent Services on Base",
    "Agents With Receipts - ERC-8004",
    "Let the Agent Cook"
  ],
  "technologies": [
    "Python", "FastAPI", "Claude Sonnet 4 (via Locus)",
    "Locus API", "Base (Ethereum L2)", "ERC-8004",
    "x402 protocol", "Railway"
  ],
  "agentHarness": "claude-code",
  "model": "claude-opus-4-6"
}
```

---

## Key Design Decisions

**Why Locus over Coinbase AgentKit?**
Locus is a hackathon sponsor with a dedicated prize track. More importantly, Locus's wrapped API layer means Vigil can pay for Claude inference through the same system it monitors — making the integration genuinely load-bearing rather than decorative. AgentKit is powerful but doesn't have a prize track here.

**Why Claude over a trained model?**
A custom anomaly detector trained on synthetic data would take 8+ hours to build and would only catch statistical outliers. Claude can reason about *intent*: "this transaction doesn't match what the agent was asked to do." The two-layer architecture gives us the best of both: fast statistical screening + deep contextual reasoning.

**Why ERC-8004 attestations over simple logs?**
Logs are private and unverifiable. On-chain attestations let any agent in the ecosystem check whether a wallet has been audited by Vigil and what the findings were. This creates network effects: the more agents Vigil audits, the more valuable the trust data becomes.

**Why x402 pricing at $0.01?**
Claude Sonnet inference via Locus costs ~$0.003-0.01 per call depending on context length. At $0.01 per audit query, Vigil covers its costs and demonstrates a self-sustaining business model. Low enough for micropayment viability, high enough to not lose money.

---

## Risk Mitigation

| Risk | Mitigation |
|------|-----------|
| Locus wrapped API for Anthropic unavailable | Fall back to direct Anthropic API key as env var |
| ERC-8004 contract calls fail | Cache attestations locally, batch-submit when chain is available |
| Demo transactions look too synthetic | Use realistic amounts, timing, and counterparty diversity in seed data |
| x402 integration complexity | Start with simple POST endpoint, add payment verification incrementally |
| Railway deployment issues | Dockerfile tested locally first; Render as backup platform |
| Domain CNAME propagation slow | Include Railway URL as fallback in README alongside vigil.nadhari.ai |
| Time runs out before Phase 4 | Each phase is independently submittable. Phase 2 deployed on Railway is already strong. |

---

## Success Criteria

**Minimum viable submission (Phase 2):**
- Vigil is live on Railway, monitoring a Locus wallet
- Layer 1 statistical filter + Layer 2 Claude reasoning both functional
- README explains the architecture, includes live URL

**Target submission (Phase 4):**
- All of the above, plus:
- ERC-8004 attestations on Base for every audit (with BaseScan links)
- x402 service endpoint live: judges can `curl` Vigil and get a response
- Dashboard at `/dashboard` showing live audit feed
- `demo/simulate_attack.py` reproduces the anomaly detection flow against live server

**Stretch (Phase 5):**
- All of the above, plus:
- Comprehensive conversation log showing human-agent collaboration
- Clean screenshots in README (green dashboard + red alert)

---

*Built by Alfa (Nadhari AI Lab) for The Synthesis Hackathon, March 2026.*
*Powered by Claude. Funded by Locus. Receipted on Base.*
