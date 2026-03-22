import asyncio
import logging
from contextlib import asynccontextmanager

from typing import Optional
from fastapi import FastAPI, Request, Cookie
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from src.config import get_settings
from src.locus.client import LocusClient
from src.service.monitor import MonitorService
from src.auditor.engine import AuditEngine
from src.auditor.reputation import ReputationGraph
from src.auditor.policy import PolicyEngine
from src.service.guardian import GuardianRegistry

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("vigil")

# Global state
locus_client: LocusClient | None = None
monitor_service: MonitorService | None = None
audit_engine: AuditEngine | None = None
reputation_graph: ReputationGraph | None = None
policy_engine: PolicyEngine | None = None
guardian: GuardianRegistry | None = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global locus_client, monitor_service, audit_engine, reputation_graph, policy_engine, guardian

    settings = get_settings()
    locus_client = LocusClient()
    reputation_graph = ReputationGraph()
    policy_engine = PolicyEngine(locus_client)
    guardian = GuardianRegistry()
    audit_engine = AuditEngine(locus_client, reputation_graph)
    monitor_service = MonitorService(locus_client, audit_engine)

    # Start background monitoring
    monitor_task = asyncio.create_task(monitor_service.run())
    logger.info("Vigil started — monitoring agent wallets on Base via Locus")

    status = await locus_client.get_status()
    logger.info(f"Wallet status: {status.wallet_status} ({status.wallet_address})")

    try:
        balance = await locus_client.get_balance()
        logger.info(f"Wallet balance: {balance.balance} {balance.currency}")
    except Exception as e:
        logger.warning(f"Could not fetch balance: {e}")

    yield

    monitor_service.stop()
    monitor_task.cancel()
    await locus_client.close()
    logger.info("Vigil shutdown complete")


app = FastAPI(
    title="Vigil",
    description="Intelligent watchdog for autonomous agent wallets on Ethereum",
    version="1.0.0",
    lifespan=lifespan,
)

templates = Jinja2Templates(directory="src/dashboard/templates")


def _auth(request: Request) -> Optional[str]:
    """Extract and validate API key from Bearer token. Returns key or None."""
    auth = request.headers.get("Authorization", "")
    if not auth.startswith("Bearer "):
        return None
    api_key = auth[7:]
    if guardian and guardian.get_operator_by_key(api_key):
        return api_key
    return None


@app.get("/.well-known/x402")
async def x402_pricing():
    """Expose x402 pricing info so other agents can discover Vigil as a paid service."""
    from src.integrations.x402 import get_audit_pricing
    return get_audit_pricing()


@app.get("/", response_class=HTMLResponse)
async def landing(request: Request):
    return templates.TemplateResponse("landing.html", {"request": request})


@app.get("/developer", response_class=HTMLResponse)
async def docs_page(request: Request):
    return templates.TemplateResponse("docs.html", {"request": request})


@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})


@app.post("/api/auth/login")
async def auth_login(request: Request):
    """Authenticate with API key and set session cookie."""
    if not guardian:
        return JSONResponse({"error": "Not initialized"}, status_code=503)
    body = await request.json()
    api_key = body.get("api_key", "")
    operator = guardian.get_operator_by_key(api_key)
    if not operator:
        return JSONResponse({"error": "Invalid API key"}, status_code=401)
    response = JSONResponse({"success": True, "name": operator.name})
    response.set_cookie(
        key="vigil_session",
        value=api_key,
        httponly=True,
        max_age=86400 * 7,  # 7 days
        samesite="lax",
    )
    return response


@app.get("/api/auth/logout")
async def auth_logout():
    response = RedirectResponse(url="/", status_code=302)
    response.delete_cookie("vigil_session")
    return response


@app.get("/skill.md")
async def skill_md():
    """Serve the Vigil onboarding skill file for agents."""
    import pathlib
    skill_path = pathlib.Path("src/dashboard/templates/skill.md")
    content = skill_path.read_text()
    from fastapi.responses import PlainTextResponse
    return PlainTextResponse(content, media_type="text/markdown")


@app.post("/api/register")
async def register_operator(request: Request):
    """Register a human operator and get an API key."""
    if not guardian:
        return JSONResponse({"error": "Not initialized"}, status_code=503)
    body = await request.json()
    result = guardian.register_operator(
        name=body.get("name", ""),
        email=body.get("email", ""),
    )
    return result


@app.post("/api/regenerate-key")
async def regenerate_key(request: Request):
    """Regenerate API key for an existing operator using their operator_id."""
    if not guardian:
        return JSONResponse({"error": "Not initialized"}, status_code=503)
    body = await request.json()
    operator_id = body.get("operator_id", "")
    if not operator_id:
        return JSONResponse({"error": "operator_id is required"}, status_code=400)
    result = guardian.regenerate_key(operator_id)
    if "error" in result:
        return JSONResponse(result, status_code=result.get("status", 400))
    return result


@app.post("/api/monitor")
async def register_monitor(request: Request):
    """Register an agent wallet for continuous Guardian monitoring."""
    if not guardian:
        return JSONResponse({"error": "Not initialized"}, status_code=503)
    auth = request.headers.get("Authorization", "")
    api_key = auth.replace("Bearer ", "") if auth.startswith("Bearer ") else ""
    if not api_key:
        return JSONResponse({"error": "Authorization: Bearer <api_key> required"}, status_code=401)

    body = await request.json()
    result = guardian.register_agent(
        api_key=api_key,
        wallet_address=body.get("wallet_address", ""),
        agent_name=body.get("agent_name", ""),
        agent_task=body.get("agent_task", ""),
    )
    if "error" in result:
        return JSONResponse(result, status_code=result.get("status", 400))
    return result


@app.get("/api/monitor/agents")
async def list_monitored_agents(request: Request):
    """List all agents monitored by the authenticated operator."""
    if not guardian:
        return JSONResponse({"error": "Not initialized"}, status_code=503)
    auth = request.headers.get("Authorization", "")
    api_key = auth.replace("Bearer ", "") if auth.startswith("Bearer ") else ""
    if not api_key:
        return JSONResponse({"error": "Authorization: Bearer <api_key> required"}, status_code=401)

    agents = guardian.get_operator_agents(api_key)
    return {"agents": agents, "total": len(agents)}


@app.get("/health")
async def health():
    return {"status": "ok", "service": "vigil", "version": "1.0.0"}


@app.get("/api/status")
async def get_status():
    if not locus_client:
        return JSONResponse({"error": "Not initialized"}, status_code=503)

    balance = await locus_client.get_balance()
    audit_stats = monitor_service.get_stats() if monitor_service else {}

    return {
        "status": "running",
        "wallet": {
            "address": balance.wallet_address,
            "balance": balance.balance,
            "currency": balance.currency,
        },
        "audits": audit_stats,
    }


@app.get("/api/audits")
async def get_audits(request: Request, limit: int = 50):
    if not monitor_service:
        return JSONResponse({"error": "Not initialized"}, status_code=503)
    if not _auth(request):
        return JSONResponse({"error": "Authorization: Bearer <api_key> required"}, status_code=401)
    audits = monitor_service.get_recent_audits(limit)
    return {
        "audits": [
            {
                "tx_hash": a.tx_hash,
                "statistical_score": round(a.statistical_score, 4),
                "verdict": a.verdict.value,
                "risk_score": round(a.risk_score, 4),
                "risk_level": a.risk_level.value,
                "reasoning": a.reasoning,
                "evidence": a.evidence,
                "recommended_action": a.recommended_action,
                "attestation_tx": a.attestation_tx,
                "timestamp": a.timestamp.isoformat(),
                "layer2_invoked": a.layer2_invoked,
            }
            for a in audits
        ],
        "total": len(audits),
    }


@app.post("/api/audit")
async def request_audit(request: Request):
    """x402 service endpoint — other agents pay to get transactions audited."""
    if not audit_engine:
        return JSONResponse({"error": "Not initialized"}, status_code=503)

    # Auth required
    api_key = _auth(request)
    if not api_key:
        return JSONResponse({"error": "Authorization: Bearer <api_key> required"}, status_code=401)

    body = await request.json()
    tx_data = body.get("transaction", {})
    agent_context = body.get("agent_context", {})

    from src.locus.models import Transaction
    from datetime import datetime

    tx = Transaction(
        tx_hash=tx_data.get("tx_hash"),
        from_address=tx_data.get("from", ""),
        to_address=tx_data.get("to", ""),
        amount=float(tx_data.get("amount", 0)),
        memo=tx_data.get("memo", ""),
        timestamp=datetime.utcnow(),
    )

    # Layer 2: Policy check before audit
    if policy_engine:
        policy_result = policy_engine.check_hard_rules(tx.to_address or "", tx.amount, tx.memo or "")
        if policy_result.get("blocked"):
            return {
                "verdict": "BLOCK",
                "risk_score": 1.0,
                "reasoning": f"Blocked by policy: {policy_result['reason']}",
                "evidence": [policy_result["reason"]],
                "recommended_action": "Transaction blocked by guardian policy",
                "attestation_tx": None,
                "cost": "0.01 USDC",
            }

    # Use monitor's tx history for better anomaly baseline
    history = list(monitor_service._tx_history) if monitor_service else []

    result = await audit_engine.audit_transaction(
        tx,
        agent_name=agent_context.get("name", "Unknown"),
        agent_task=agent_context.get("task", ""),
        history=history,
    )

    # Add to tx history so future audits have baseline
    if monitor_service:
        monitor_service._tx_history.append(tx)

    # Update guardian stats for the operator's agents
    if guardian:
        guardian.record_audit(api_key, result.verdict.value)

    return {
        "verdict": result.verdict.value,
        "risk_score": round(result.risk_score, 4),
        "reasoning": result.reasoning,
        "evidence": result.evidence,
        "recommended_action": result.recommended_action,
        "attestation_tx": result.attestation_tx,
        "cost": "0.01 USDC",
    }


@app.get("/api/attestations")
async def get_attestations(request: Request, limit: int = 50):
    if not audit_engine:
        return JSONResponse({"error": "Not initialized"}, status_code=503)
    if not _auth(request):
        return JSONResponse({"error": "Authorization: Bearer <api_key> required"}, status_code=401)
    attestations = audit_engine.attestor.get_attestations(limit)
    return {
        "attestations": attestations,
        "total": audit_engine.attestor.get_attestation_count(),
    }


@app.get("/api/reputation/graph")
async def get_reputation_graph():
    """Get all nodes and edges for the reputation graph visualization."""
    if not reputation_graph:
        return JSONResponse({"error": "Not initialized"}, status_code=503)
    counterparties = reputation_graph._counterparties
    nodes = []
    for addr, cp in counterparties.items():
        trust = cp.clean_interactions / max(cp.total_interactions, 1)
        nodes.append({
            "address": cp.address,
            "label": cp.known_label or cp.address[:10] + "...",
            "trust_score": round(trust, 2),
            "total_interactions": cp.total_interactions,
            "category": cp.known_category or "unknown",
            "flags": cp.flagged_interactions,
        })
    return {
        "nodes": nodes,
        "total_audits": reputation_graph._total_audits,
        "total_approved": reputation_graph._total_approved,
        "total_flagged": reputation_graph._total_flagged,
        "total_blocked": reputation_graph._total_blocked,
    }


@app.get("/api/reputation/{address}")
async def get_reputation(request: Request, address: str):
    """Query trust profile for any address based on Vigil's attestation history. Free."""
    if not reputation_graph:
        return JSONResponse({"error": "Not initialized"}, status_code=503)
    if not _auth(request):
        return JSONResponse({"error": "Authorization: Bearer <api_key> required"}, status_code=401)
    rep = reputation_graph.get_address_reputation(address)
    return rep


@app.post("/api/policy")
async def create_policy(request: Request):
    """Create or update a natural language policy for an agent."""
    if not policy_engine:
        return JSONResponse({"error": "Not initialized"}, status_code=503)
    if not _auth(request):
        return JSONResponse({"error": "Authorization: Bearer <api_key> required"}, status_code=401)
    body = await request.json()
    agent_address = body.get("agent_address", "")
    policy_text = body.get("policy_text", "")
    if not policy_text:
        return JSONResponse({"error": "policy_text is required"}, status_code=400)
    result = await policy_engine.create_policy(agent_address, policy_text)
    return result


@app.post("/api/audit/deep")
async def deep_audit(request: Request):
    """Deep audit with trajectory analysis and counterparty graph lookup."""
    if not audit_engine or not reputation_graph:
        return JSONResponse({"error": "Not initialized"}, status_code=503)
    api_key = _auth(request)
    if not api_key:
        return JSONResponse({"error": "Authorization: Bearer <api_key> required"}, status_code=401)

    body = await request.json()
    tx_data = body.get("transaction", {})
    agent_context = body.get("agent_context", {})

    from src.locus.models import Transaction
    from datetime import datetime, timezone

    tx = Transaction(
        tx_hash=tx_data.get("tx_hash"),
        from_address=tx_data.get("from", ""),
        to_address=tx_data.get("to", ""),
        amount=float(tx_data.get("amount", 0)),
        memo=tx_data.get("memo", ""),
        timestamp=datetime.now(timezone.utc),
    )

    history = list(monitor_service._tx_history) if monitor_service else []

    result = await audit_engine.audit_transaction(
        tx,
        agent_name=agent_context.get("name", "Unknown"),
        agent_task=agent_context.get("task", ""),
        history=history,
    )

    # Add to tx history so future audits have baseline
    if monitor_service:
        monitor_service._tx_history.append(tx)

    # Counterparty profile
    counterparty = reputation_graph.get_address_reputation(tx.to_address or "")

    # Domain categorization
    domain = reputation_graph.categorize_transaction(
        tx.to_address or "", tx.memo or ""
    )

    return {
        "verdict": result.verdict.value,
        "risk_score": round(result.risk_score, 4),
        "reasoning": result.reasoning,
        "evidence": result.evidence,
        "recommended_action": result.recommended_action,
        "attestation_tx": result.attestation_tx,
        "domain": domain,
        "counterparty_profile": counterparty,
        "agent_trust_scores": reputation_graph.get_agent_trust_scores(
            tx.from_address or ""
        ),
        "cost_usdc": 0.05,
    }


@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request):
    # Require login
    session_key = request.cookies.get("vigil_session")
    if not session_key or not (guardian and guardian.get_operator_by_key(session_key)):
        return RedirectResponse(url="/login", status_code=302)

    audits = monitor_service.get_recent_audits(50) if monitor_service else []
    stats = monitor_service.get_stats() if monitor_service else {}

    balance = None
    if locus_client:
        try:
            balance = await locus_client.get_balance()
        except Exception:
            pass

    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "audits": audits,
            "stats": stats,
            "balance": balance,
        },
    )
