# Vigil

> The trust layer between your agent and your money.
> Real-time behavioral intelligence for agent wallets on Ethereum.

---

## The Problem

We are entering an economy where AI agents act on behalf of humans. They hold wallets. They move money. They sign contracts, hire other agents, negotiate deals, stake collateral, and access services — all autonomously.

The infrastructure for these actions exists. Coinbase AgentKit gives agents wallets. Locus gives them spending controls. Uniswap gives them swap routing. MetaMask Delegation Framework gives them scoped permissions. ERC-8004 gives them on-chain identity.

What none of this gives them is trust.

Not trust as a brand badge or a verification checkmark. Trust as a real-time, contextual, continuously evaluated signal: **should this agent be doing this specific thing right now, given everything we know?**

Today, the answer to that question is a config file. Max $50 per transaction. $500 per day. Approved addresses only. These are not trust — they are constraints. They cripple the agent's usefulness to keep the human safe. A compromised agent that splits a $5,000 drain into fifty small transactions passes every check. A legitimate agent making one large authorized purchase gets blocked. The system cannot tell the difference because it was never designed to understand intent.

Trust is not a threshold. Trust is intelligence.

Vigil is that intelligence.

---

## What Vigil Is

Vigil is an autonomous agent whose purpose is to evaluate the trustworthiness of other agents' actions in real time.

It is not a monitoring dashboard. It is not a spending limiter. It is not a rules engine with a chatbot wrapper.

Vigil is a **full economic actor** in the agentic ecosystem. It has its own wallet, its own on-chain identity, its own reputation history, and its own revenue model. It sells trust as a service — and it backs that service with its track record.

Any agent in the ecosystem can query Vigil before executing a high-stakes action. Vigil returns a verdict — approve, flag, or block — backed by contextual reasoning, behavioral analysis, and its accumulated intelligence across every agent it has ever observed.

Vigil is powered by Claude. Not as an API wrapper, but as a reasoning core that understands why an agent might be doing something, not just what it is doing.

---

## Architecture

Vigil operates through five layers. Each layer builds on the one below it. Together they produce trust verdicts that are contextual, intelligent, and economically meaningful.

```
+------------------------------------------------------------------+
|                         VIGIL AGENT                               |
|                                                                   |
|  +------------------------------------------------------------+  |
|  | Layer 5: ECONOMICS                                          |  |
|  | x402 pricing, revenue tracking, cost management,            |  |
|  | self-sustaining operation                                   |  |
|  +------------------------------------------------------------+  |
|  | Layer 4: REPUTATION                                         |  |
|  | ERC-8004 attestations, verdict history, accuracy tracking,  |  |
|  | domain-specific trust scores                                |  |
|  +------------------------------------------------------------+  |
|  | Layer 3: JUDGMENT                                           |  |
|  | Claude reasoning engine, intent analysis, policy matching,  |  |
|  | prompt injection detection, objective drift analysis        |  |
|  +------------------------------------------------------------+  |
|  | Layer 2: POLICY                                             |  |
|  | Natural language policy engine, human-defined boundaries,   |  |
|  | adaptive autonomy thresholds                                |  |
|  +------------------------------------------------------------+  |
|  | Layer 1: PERCEPTION                                         |  |
|  | Transaction monitoring, counterparty graph, fleet awareness,|  |
|  | behavioral baselines, ecosystem-wide pattern recognition    |  |
|  +------------------------------------------------------------+  |
|                                                                   |
|  Wallet: Locus (Base)    Identity: ERC-8004    Brain: Claude      |
+------------------------------------------------------------------+
```

---

## Layer 1: Perception

Vigil sees the agentic economy.

### Transaction Monitoring

Every agent Vigil protects has its wallet transactions monitored in real time. Vigil polls transaction history through Locus APIs and maintains a rolling behavioral profile for each agent:

- **Amount distribution:** mean, standard deviation, percentiles of transaction values
- **Timing patterns:** typical active hours, inter-transaction intervals, burst vs. steady spending
- **Counterparty map:** which addresses the agent interacts with, frequency, trust level of each
- **Gas behavior:** typical gas prices, speed preferences, deviation from network median
- **Category fingerprint:** what the agent spends on — swaps, NFTs, services, transfers

This profile is the agent's behavioral baseline. It is not static. It evolves continuously as the agent operates. A new agent has a thin profile and gets scrutinized more heavily. A mature agent with 10,000 consistent transactions gets wider latitude.

### Counterparty Reputation Graph

Vigil does not evaluate transactions in isolation. It maintains a graph of every address it has ever seen across every agent it monitors.

When Agent A sends funds to Address X, Vigil knows:
- How many Vigil-monitored agents have interacted with Address X
- The outcomes of those interactions (clean, disputed, fraudulent)
- Whether Address X has been flagged by other trust providers
- The age and activity pattern of Address X itself
- Whether Address X is a known contract (DEX router, NFT marketplace, bridge) or an unknown EOA

This graph is shared across all agents Vigil monitors. One agent's experience with a counterparty becomes intelligence for every other agent. This is how trust scales — not through individual vigilance but through collective observation.

### Fleet Awareness

A human running multiple agents needs Vigil to see them as a fleet, not as isolated wallets.

If Agent A is compromised after interacting with a specific contract, Vigil immediately heightens scrutiny on every other agent in the fleet that touched that same contract. If Agent B starts exhibiting the same behavioral shifts that preceded Agent A's compromise, Vigil flags it before the attack materializes.

Fleet awareness also detects coordination attacks. If three agents in a fleet simultaneously attempt unusual transactions to different addresses, Vigil recognizes this as a correlated event — even if each individual transaction looks borderline acceptable.

### Statistical Anomaly Filter

The first pass on every transaction is a fast statistical filter. No LLM calls. Pure computation. Under 100ms.

Features extracted per transaction:

```
amount_zscore          — standard deviations from agent's mean
time_delta_zscore      — time since last tx vs. typical interval
counterparty_novelty   — 0.0 (well-known) to 1.0 (never seen)
amount_velocity_1h     — spend rate vs. historical hourly average
amount_velocity_6h     — spend rate vs. historical 6h average
amount_velocity_24h    — spend rate vs. historical daily average
gas_price_ratio        — gas price vs. network median
hour_anomaly           — time of day vs. agent's activity distribution
category_deviation     — transaction type vs. agent's typical category mix
fleet_correlation      — similarity to concurrent fleet transactions
counterparty_risk      — reputation score from counterparty graph
```

Weighted combination produces a risk score from 0.0 to 1.0:
- **< 0.3** → PASS. Log the audit. No further action.
- **0.3 - 0.7** → REVIEW. Escalate to Layer 3 (Claude reasoning).
- **> 0.7** → ALERT. Escalate to Layer 3 + notify human immediately.

This filter handles the volume. The vast majority of transactions pass through Layer 1 in milliseconds. Claude only gets invoked when something warrants deeper investigation.

---

## Layer 2: Policy

Vigil speaks human.

### Natural Language Policy Engine

The human defines what their agent is allowed to do in plain English. No config files. No JSON schemas. No allowlists.

**Example policy conversation:**

```
Human: "My agent handles my DeFi portfolio. It can swap tokens on
Uniswap and stake ETH on Lido. Nothing else. If it tries to bridge
funds to another chain, block it and tell me. Be aggressive on
unknown contracts. Lenient on blue chip protocols."

Vigil: "Understood. I've set up the following policy:

  ALLOWED ACTIONS:
  - Token swaps via Uniswap (any pair, any amount within daily limit)
  - ETH staking via Lido (stake/unstake, wstETH wrapping)

  BLOCKED ACTIONS:
  - Cross-chain bridge transactions (immediate block + alert)
  - Any interaction with contracts not in Uniswap/Lido ecosystem

  SCRUTINY LEVELS:
  - Known blue chip protocols (Uniswap, Lido, Aave, Compound):
    low scrutiny, Layer 1 filter only unless statistical anomaly
  - Unknown contracts: high scrutiny, always escalate to reasoning

  DAILY LIMITS:
  - Not specified. Want me to suggest one based on your current
    portfolio size?

  I'll refine this as I learn your agent's patterns. You can update
  this policy anytime by telling me what to change."
```

Claude translates the human's intent into a structured policy document that combines three types of rules:

**Hard rules** — binary, no exceptions. "Never bridge to another chain." These are enforced at Layer 1 speed. If a transaction matches a hard rule, it is blocked before Claude is ever invoked.

**Soft rules** — contextual, judgment-required. "Be aggressive on unknown contracts." These inform Claude's reasoning in Layer 3. They set the sensitivity threshold, not the decision.

**Adaptive rules** — evolve over time. "Lenient on blue chips." As the agent's history grows, Vigil adjusts what "lenient" means in practice. A new agent gets tighter bounds. A mature agent with a clean track record gets more freedom.

### Adaptive Autonomy

The policy is not static. As Vigil observes an agent operating safely over time, it can suggest loosening constraints:

```
Vigil: "Your agent has executed 500 Uniswap swaps over 3 months
with zero flagged transactions. Its behavioral profile is stable
and consistent. Currently I'm escalating to reasoning on any swap
above $500. Would you like me to raise that to $1,000?"
```

The human always decides. Vigil suggests. This is how trust grows naturally — through demonstrated competence, not through configuration changes.

### Policy Inheritance for Fleets

When a human runs multiple agents, policies can be hierarchical:

- **Fleet policy:** rules that apply to all agents ("never interact with sanctioned addresses")
- **Role policy:** rules for a class of agents ("all trading agents have a $10K daily limit")
- **Individual policy:** rules for one specific agent ("this agent only trades ETH/USDC pair")

More specific policies override more general ones. This lets the human manage 50 agents without writing 50 separate policy documents.

---

## Layer 3: Judgment

Vigil reasons about intent.

### Claude as the Reasoning Core

When Layer 1 flags a transaction, Claude receives the full context:

```
SYSTEM PROMPT:
You are Vigil's judgment engine. You evaluate whether a flagged
transaction is consistent with an agent's authorized behavior.

You receive:
- The flagged transaction details
- The agent's human-defined policy
- The agent's behavioral baseline (statistical profile)
- Recent transaction history
- Counterparty reputation data from Vigil's graph
- Fleet context (if applicable)
- The specific statistical anomalies that triggered this review

Your task: determine whether this transaction represents:
1. APPROVED behavior within the agent's mandate
2. FLAGGED behavior that warrants human review
3. BLOCKED behavior that should not proceed

For every verdict, explain your reasoning in 2-3 sentences.
Identify specific evidence that supports your conclusion.
If blocking, recommend what the human should investigate.

Respond with structured JSON only.
```

```
USER PROMPT:
## Flagged Transaction
- Amount: 2,500 USDC
- To: 0x7a250d5630B4cF539739dF2C5dAcb4c659F2488D (Uniswap V2 Router)
- Action: Swap USDC → WETH
- Memo: "Rebalance portfolio"
- Timestamp: 2026-03-21T14:32:00Z
- Statistical risk score: 0.45

## Agent Policy
ALLOWED: Token swaps via Uniswap, ETH staking via Lido
BLOCKED: Cross-chain bridges
SCRUTINY: Low on blue chip protocols
DAILY LIMIT: $5,000 (current daily spend: $1,200)

## Behavioral Baseline
- Mean transaction: $340 USDC (std: $180)
- This transaction: 7.3x mean (2.1 sigma)
- Typical daily transactions: 8-12
- Today so far: 4 transactions
- Counterparty (Uniswap Router): seen 347 times, 100% clean
- Active hours: 09:00-22:00 UTC (current time: within range)

## Fleet Context
- No correlated unusual activity across fleet
- 2 other agents interacted with Uniswap Router today (normal)

## Statistical Anomalies
- amount_zscore: 2.1 (elevated but not extreme)
- counterparty_novelty: 0.0 (very well known)
- amount_velocity_24h: 0.74 (74% of daily limit used after this tx)
```

Claude's reasoning:

```json
{
  "verdict": "APPROVE",
  "risk_score": 0.22,
  "reasoning": "Transaction is a standard Uniswap swap to a verified router contract the agent has used 347 times. Amount is above average but within daily policy limits. The 2.1 sigma deviation is explained by portfolio rebalancing, which naturally involves larger single transactions. All other signals are baseline.",
  "evidence": [
    "Counterparty is Uniswap V2 Router (verified, 347 prior clean interactions)",
    "Action type (swap) explicitly allowed by policy",
    "Within daily spending limit ($3,700 of $5,000 remaining)",
    "No fleet correlation anomalies"
  ],
  "recommended_action": "None. Transaction is consistent with authorized behavior."
}
```

This is not classification. Claude considers the intersection of statistical signals, human policy, behavioral history, counterparty reputation, and fleet context. It explains *why* the transaction is or isn't consistent with the agent's mandate. A trained classifier can detect outliers. Claude can detect *misalignment*.

### Prompt Injection Detection

The deepest threat to an autonomous agent is not a bad transaction. It is a compromised reasoning process.

If an agent's LLM is manipulated — through prompt injection, adversarial inputs, or corrupted context — the agent may change its objectives while appearing to function normally. The transactions look intentional. They pass statistical checks. But they serve the attacker's goals, not the human's.

Vigil watches for signals of objective drift:

**Behavioral trajectory analysis.** Vigil tracks not just the current transaction but the *trend* of the last N transactions. A gradual shift in counterparty selection, increasing amounts to a specific address, or a slow pivot from swaps to transfers might not trigger statistical anomalies on any single transaction — but the trajectory is anomalous.

```
Week 1: Agent swaps on Uniswap (100% of transactions)
Week 2: Agent swaps on Uniswap (92%), 2 small transfers to new address
Week 3: Agent swaps on Uniswap (78%), increasing transfers to same address
Week 4: Agent swaps on Uniswap (45%), large transfer to same address
```

No single transaction in this sequence would flag. The trend is the signal.

**Memo and context analysis.** Agent transactions often include memos or metadata. Vigil analyzes whether the language in memos shifts over time. A trading agent that starts including memos like "urgent" or "time-sensitive" when it never did before might be operating under injected urgency.

**Decision pattern analysis.** Vigil can compare the agent's recent decisions against its historical decision patterns. If a trading agent that historically evaluated 5-10 options before executing a swap suddenly starts executing instantly, the decision-making process itself has changed — even if the outcomes look similar.

When Vigil detects objective drift, it doesn't just flag the current transaction. It escalates the entire behavioral trajectory to the human with a narrative explanation:

```
Vigil Alert: Possible Objective Drift Detected

Your agent TradingBot-7 has shown a gradual behavioral shift
over the past 14 days. While individual transactions have been
within normal parameters, the overall trajectory shows:

- 55% reduction in Uniswap swap activity
- 340% increase in direct transfers to address 0xABC...
- Address 0xABC... has no prior history with any Vigil-monitored agent
- Transfer amounts are increasing: $20 → $50 → $120 → $300

This pattern is consistent with gradual objective manipulation.
The agent may be operating under altered instructions.

Recommended: Pause agent operations and inspect its current
system prompt and context window for unauthorized modifications.
```

### Delegation-Aware Reasoning

Agents operate under permission scopes — session keys with expiration and spending limits, MetaMask Delegation Framework caveats, Safe allowance modules. A transaction can be within its technical permission scope and still be wrong.

Vigil understands three distinct questions:

1. **Can the agent do this?** (Delegation scope — what the smart contract allows)
2. **Is the agent trying to do this?** (Transaction intent — what the action accomplishes)
3. **Should the agent do this?** (Policy alignment — what the human actually wants)

A compromised agent might find creative ways to stay within its delegation scope while violating the human's intent. For example: an agent with permission to "swap any token on Uniswap" could technically swap USDC for a worthless token as a way to drain the wallet. The delegation allows it. The human's intent forbids it. Vigil catches the gap.

```
Delegation scope: Swap any ERC-20 token via Uniswap Router
Transaction intent: Swap 5,000 USDC for TOKEN_XYZ
Policy check: Agent is authorized to swap — but TOKEN_XYZ has:
  - 2 days of trading history
  - $12,000 total liquidity
  - No Vigil-monitored agent has ever interacted with it
  - Slippage at this amount would be >40%

Verdict: BLOCK
Reasoning: While the swap action is within delegation scope,
the specific token has characteristics consistent with a
liquidity trap. The 40% slippage effectively transfers value
to the pool creator. This does not align with the portfolio
management objective defined in the agent's policy.
```

---

## Layer 4: Reputation

Vigil accumulates trust capital.

### ERC-8004 Attestations

Every audit Vigil performs produces an on-chain attestation written to the ERC-8004 Reputation Registry on Base. This attestation is a public, verifiable record:

```json
{
  "attester": "vigil.eth (0xVIGIL...)",
  "subject": "tradingbot-7.eth (0xAGENT...)",
  "schema": "vigil-audit-v1",
  "data": {
    "tx_hash": "0xABC...",
    "verdict": "APPROVE",
    "risk_score": 22,
    "category": "defi-swap",
    "layer1_score": 45,
    "layer2_invoked": true,
    "timestamp": 1711025520
  },
  "tags": ["vigil-audit", "clean", "defi"],
  "signature": "0xSIG..."
}
```

These attestations serve multiple purposes:

**For the audited agent:** A clean audit history is a trust asset. An agent with 1,000 Vigil-approved transactions is more trustworthy to counterparties than an agent with no audit trail. The attestations are portable — they live on-chain, not in Vigil's database.

**For the ecosystem:** Any agent or service can query the ERC-8004 Reputation Registry to check whether an address has been audited by Vigil. Before transacting with an unknown agent, you check: has Vigil seen this agent before? What was the verdict history?

**For Vigil itself:** The attestation record is Vigil's track record. If Vigil has written 50,000 attestations and 99.8% of approved transactions were clean, that accuracy rate is verifiable by anyone. This is what makes Vigil's future verdicts credible.

### Verdict History and Accuracy Tracking

Vigil tracks its own performance:

- **Approval accuracy:** what percentage of APPROVED transactions were actually clean
- **Flag precision:** what percentage of FLAGGED transactions were confirmed suspicious by the human
- **Block recall:** how many actual attacks did Vigil catch before execution
- **False positive rate:** how often Vigil escalates transactions that turn out to be fine

These metrics are computed from feedback loops:
- Human overrides (human approves a blocked transaction, or reports a missed attack)
- On-chain outcomes (a flagged counterparty later gets reported for fraud)
- Fleet correlations (a pattern Vigil flagged in one agent appears in another)

The metrics are published periodically as summary attestations:

```json
{
  "attester": "vigil.eth",
  "subject": "vigil.eth",
  "schema": "vigil-performance-v1",
  "data": {
    "period": "2026-03",
    "total_audits": 12847,
    "approvals": 11923,
    "flags": 801,
    "blocks": 123,
    "confirmed_threats_caught": 119,
    "false_positive_rate": 0.034,
    "approval_accuracy": 0.998
  }
}
```

Any agent in the ecosystem can verify these numbers on-chain.

### Domain-Specific Trust

Not all trust is equal. An agent that Vigil has audited 5,000 times for DeFi swaps has a strong trust profile *in DeFi swaps*. That says nothing about whether the same agent should be trusted with NFT purchases or cross-chain bridges.

Vigil categorizes its attestations by domain:
- `defi-swap` — token exchanges
- `defi-stake` — staking and unstaking
- `defi-lend` — lending and borrowing
- `nft-trade` — NFT purchases and sales
- `transfer` — direct value transfers
- `contract-interaction` — generic contract calls
- `agent-hire` — paying another agent for services
- `bridge` — cross-chain operations

When an external agent queries Vigil about a counterparty, Vigil returns domain-specific trust scores:

```json
{
  "agent": "0xAGENT...",
  "trust_scores": {
    "defi-swap": { "score": 0.97, "sample_size": 4821 },
    "defi-stake": { "score": 0.94, "sample_size": 340 },
    "nft-trade": { "score": 0.71, "sample_size": 23 },
    "transfer": { "score": 0.88, "sample_size": 156 }
  },
  "overall": 0.94,
  "last_audit": "2026-03-21T14:32:00Z",
  "total_audits": 5340
}
```

A trust score of 0.71 with 23 samples means "limited data, moderate confidence." A score of 0.97 with 4,821 samples means "strong track record, high confidence." The querying agent decides its own risk threshold.

---

## Layer 5: Economics

Vigil sustains itself.

### x402 Service Pricing

Vigil charges per audit query via the x402 protocol through Locus. Pricing is dynamic:

**Base audit:** $0.01 USDC
A standard transaction audit. Layer 1 statistical filter, Layer 2 Claude reasoning if triggered, ERC-8004 attestation written.

**Deep audit:** $0.05 USDC
Full behavioral trajectory analysis, counterparty graph lookup, fleet correlation check. Used for high-value transactions or unknown counterparties.

**Reputation query:** $0.005 USDC
No new audit. Returns the trust profile of an address based on Vigil's existing attestation history. Fast, cheap, high volume.

**Policy setup:** $0.10 USDC
Claude processes a natural language policy document and creates a structured policy for a new agent.

### Cost Structure

Vigil's costs are transparent:

- **Claude Sonnet inference:** ~$0.003-0.01 per reasoning call (via Locus wrapped API)
- **ERC-8004 attestation gas:** negligible on Base (sub-cent)
- **Locus platform fee:** included in wrapped API pricing
- **Statistical filter:** zero marginal cost (pure computation)

At $0.01 per base audit, Vigil operates at a small margin on audits that escalate to Layer 2, and a large margin on audits that resolve at Layer 1. The blended margin is healthy because most transactions are routine — Layer 1 handles them without invoking Claude.

### Revenue Model

Vigil earns from three streams:

1. **Guardian subscriptions:** A human points Vigil at their agent's wallet. Vigil monitors continuously. Each audited transaction generates revenue.

2. **Oracle queries:** External agents call Vigil's x402 endpoint for one-off audit verdicts or reputation lookups. Pay-per-query, no subscription.

3. **Fleet contracts:** A human running multiple agents pays a flat rate for fleet-wide monitoring with shared intelligence.

The unit economics improve with scale. The counterparty reputation graph becomes more valuable with more agents. The behavioral models become more accurate with more data. The false positive rate drops. The service becomes cheaper to operate and more valuable to customers simultaneously.

---

## Interaction Modes

### Mode 1: Guardian (Continuous Monitoring)

The human registers their agent's wallet with Vigil. Vigil monitors every transaction in real time.

```
Human → Vigil: "Watch this wallet: 0xAGENT..."
Human → Vigil: "Here's the policy: [natural language rules]"
Vigil: Monitoring. Dashboard live at vigil.nadhari.ai/dashboard/0xAGENT

[Agent makes transactions]
Vigil: [Layer 1 pass] Tx #1: $45 USDC swap on Uniswap. Clean. ✓
Vigil: [Layer 1 pass] Tx #2: $30 USDC swap on Uniswap. Clean. ✓
Vigil: [Layer 1 flag → Layer 2] Tx #3: $2,500 USDC to unknown address.
       BLOCKED. Reasoning: "Amount 7x typical, counterparty never seen,
       no match to any allowed action in policy."
Vigil → Human: Alert. Transaction blocked. Review required.
```

### Mode 2: Oracle (Pre-Transaction Query)

An agent is about to execute a transaction. It calls Vigil first.

```
Agent → Vigil (x402): {
  "transaction": { "to": "0xDEX...", "amount": 500, "action": "swap" },
  "context": { "task": "portfolio rebalancing", "history_hash": "0x..." }
}

Vigil → Agent: {
  "verdict": "APPROVE",
  "risk_score": 0.15,
  "reasoning": "Standard swap to verified DEX. Within behavioral norms.",
  "attestation": "0xATTESTATION_TX...",
  "cost": "0.01 USDC"
}

Agent: Proceeds with transaction.
```

### Mode 3: Reputation Lookup

An agent wants to know if a counterparty is trustworthy before engaging.

```
Agent → Vigil (x402): {
  "query": "reputation",
  "address": "0xUNKNOWN..."
}

Vigil → Agent: {
  "address": "0xUNKNOWN...",
  "known": true,
  "trust_scores": {
    "defi-swap": { "score": 0.92, "sample_size": 234 },
    "transfer": { "score": 0.67, "sample_size": 12 }
  },
  "flags": 3,
  "last_seen": "2026-03-20T08:15:00Z",
  "cost": "0.005 USDC"
}
```

### Mode 4: Policy Conversation

The human updates their agent's policy through natural dialogue.

```
Human: "My agent has been running well for a month. I want to let it
start providing liquidity on Uniswap V3, not just swapping. Max
$2,000 per position. Only for ETH/USDC and ETH/USDT pairs."

Vigil: "Updated your policy. Changes:

  ADDED:
  - Liquidity provision on Uniswap V3
  - Allowed pairs: ETH/USDC, ETH/USDT
  - Max position size: $2,000

  UNCHANGED:
  - Swaps: allowed (any pair)
  - Staking: allowed (Lido only)
  - Bridges: blocked

  Note: Liquidity provision is a new action type for this agent.
  I'll apply elevated scrutiny for the first 20 LP transactions
  while I build a behavioral baseline for this action category.
  After that, scrutiny will adjust based on the pattern."
```

---

## What Vigil Does Not Do

**Vigil does not custody funds.** Vigil never holds or moves the human's money. It observes, evaluates, and attests. In Guardian mode, Vigil can recommend blocking a transaction through the human's spending control interface (Locus dashboard, Safe approval queue). It does not have the keys.

**Vigil does not replace the human.** Every block and every flag is a recommendation. The human can override. Vigil's role is to surface information the human cannot see — behavioral anomalies, counterparty risks, policy violations — and present it clearly. The human decides.

**Vigil does not guarantee outcomes.** An APPROVED verdict means Vigil's analysis found no anomalies given available information. It is not insurance. It is intelligence.

**Vigil does not see private data.** Vigil analyzes on-chain transactions and metadata. It does not access the agent's system prompt, conversation history, or private keys. Its analysis is based on observable behavior, not internal state. This is a feature: Vigil works the same way whether the agent is powered by Claude, GPT, Gemini, or a custom model.

---

## The Trust Marketplace

Vigil is one trust provider. It should not be the only one.

The architecture is designed for a marketplace of trust agents. Multiple Vigil instances — or entirely different trust providers — can write attestations to the ERC-8004 Reputation Registry. A querying agent can check verdicts from multiple providers and form its own assessment.

This creates healthy dynamics:

- **Competition on accuracy.** A trust provider with a higher approval accuracy rate earns more business.
- **Specialization.** Vigil-DeFi might specialize in decentralized finance transactions. Vigil-NFT might specialize in marketplace activity. A bridge-focused trust agent might emerge for cross-chain operations.
- **Redundancy.** No single trust provider is a point of failure. If Vigil goes offline, other providers continue attesting.
- **Verifiability.** Every provider's track record is on-chain. Claims of accuracy are auditable by anyone.

The agentic economy needs trust infrastructure as fundamental as DNS is to the web. Not one provider. A protocol. Vigil is the first implementation.

---

## Technical Requirements

| Component | Technology | Purpose |
|-----------|-----------|---------|
| Runtime | Python 3.11+ | Core agent logic |
| Web framework | FastAPI | API endpoints, dashboard, x402 service |
| Reasoning engine | Claude Sonnet 4 | Intent analysis, policy processing, drift detection |
| LLM access | Locus wrapped API | Pay-per-call Claude inference in USDC |
| Wallet | Locus | Vigil's own wallet on Base, transaction monitoring |
| On-chain identity | ERC-8004 | Vigil's identity + attestation writing |
| Network | Base (Ethereum L2) | Low-cost attestations, primary deployment chain |
| Dashboard | Jinja2 + htmx | Server-rendered real-time audit feed |
| Deployment | Railway | Persistent process, auto-deploy from GitHub |
| Domain | vigil.nadhari.ai | CNAME to Railway deployment |

---

## API Reference

### POST /api/audit
Request a transaction audit (Oracle mode).

```json
// Request
{
  "transaction": {
    "from": "0x...",
    "to": "0x...",
    "amount": 500.00,
    "token": "USDC",
    "action": "swap",
    "memo": "Portfolio rebalance"
  },
  "agent_context": {
    "name": "TradingBot-7",
    "task": "Execute approved DeFi operations",
    "erc8004_id": "0x..."
  }
}

// Response
{
  "verdict": "APPROVE",
  "risk_score": 0.15,
  "reasoning": "Standard swap to verified Uniswap Router. Amount within behavioral norms. Counterparty seen 347 times with 100% clean history.",
  "evidence": [
    "Verified contract: Uniswap V2 Router",
    "Counterparty trust score: 0.99 (4,821 samples)",
    "Amount: 1.4 sigma (within normal range)",
    "Action type matches agent policy"
  ],
  "attestation_tx": "0x...",
  "cost_usdc": 0.01
}
```

### POST /api/audit/deep
Request a deep audit with full behavioral trajectory and fleet analysis.

```json
// Request
{
  "transaction": { ... },
  "agent_context": { ... },
  "include": ["trajectory", "fleet", "counterparty_graph"]
}

// Response
{
  "verdict": "FLAG",
  "risk_score": 0.58,
  "reasoning": "...",
  "trajectory_analysis": {
    "trend": "shifting",
    "details": "Transfer frequency to 0xABC... increased 340% over 14 days",
    "drift_confidence": 0.72
  },
  "fleet_context": {
    "correlated_anomalies": 0,
    "fleet_health": "normal"
  },
  "counterparty_profile": {
    "address": "0xABC...",
    "first_seen": "2026-03-07",
    "vigil_interactions": 3,
    "trust_score": 0.41
  },
  "attestation_tx": "0x...",
  "cost_usdc": 0.05
}
```

### GET /api/reputation/{address}
Query trust profile for an address.

```json
// Response
{
  "address": "0x...",
  "known": true,
  "trust_scores": {
    "defi-swap": { "score": 0.97, "audits": 4821 },
    "transfer": { "score": 0.88, "audits": 156 }
  },
  "overall_score": 0.94,
  "total_audits": 5340,
  "flags": 7,
  "blocks": 2,
  "last_audit": "2026-03-21T14:32:00Z",
  "cost_usdc": 0.005
}
```

### POST /api/policy
Create or update a natural language policy.

```json
// Request
{
  "agent_address": "0x...",
  "policy_text": "My agent handles my DeFi portfolio. It can swap tokens on Uniswap and stake ETH on Lido. Nothing else. Block any bridge attempts."
}

// Response
{
  "policy_id": "pol_...",
  "structured_policy": {
    "hard_rules": [
      { "action": "bridge", "verdict": "BLOCK", "alert": true }
    ],
    "allowed_actions": [
      { "action": "swap", "protocols": ["uniswap-v2", "uniswap-v3"] },
      { "action": "stake", "protocols": ["lido"] }
    ],
    "scrutiny_levels": {
      "known_bluechip": "low",
      "known_other": "medium",
      "unknown": "high"
    },
    "limits": {
      "daily": null,
      "per_transaction": null
    }
  },
  "vigil_notes": "No daily limit specified. Recommend setting one based on portfolio size. Elevated scrutiny will apply for first 50 transactions while baseline is established.",
  "cost_usdc": 0.10
}
```

### GET /api/monitor/{wallet_address}
Register a wallet for continuous Guardian monitoring.

### GET /dashboard/{wallet_address}
Live web dashboard for a monitored wallet.

---

*Vigil. The trust layer between your agent and your money.*

*Built by Nadhari AI Lab. Powered by Claude. Attested on Base.*
