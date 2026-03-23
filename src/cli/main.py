"""
Vigil CLI — Terminal interface for autonomous agents and operators.

Usage:
    vigil register --name "my-agent"
    vigil audit --from 0x... --to 0x... --amount 150 --memo "NFT purchase"
    vigil reputation 0x2626664c2603336e57b271c5c0b26f421741e481
    vigil status
    vigil policies list
    vigil monitor --wallet 0x... --name "TradingBot" --task "Execute swaps"
"""

import click
import httpx
import json
import os
import sys
from pathlib import Path
from datetime import datetime

# Config file for storing API key and server URL
CONFIG_DIR = Path.home() / ".vigil"
CONFIG_FILE = CONFIG_DIR / "config.json"

# ANSI color codes
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
BLUE = "\033[94m"
CYAN = "\033[96m"
DIM = "\033[2m"
BOLD = "\033[1m"
RESET = "\033[0m"
PURPLE = "\033[95m"


def load_config():
    """Load CLI config from ~/.vigil/config.json"""
    if CONFIG_FILE.exists():
        return json.loads(CONFIG_FILE.read_text())
    return {}


def save_config(config):
    """Save CLI config to ~/.vigil/config.json"""
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    CONFIG_FILE.write_text(json.dumps(config, indent=2))


def get_server():
    """Get the Vigil server URL."""
    config = load_config()
    return config.get("server", os.environ.get("VIGIL_SERVER", "http://localhost:8080"))


def get_api_key():
    """Get the stored API key."""
    config = load_config()
    key = config.get("api_key", os.environ.get("VIGIL_API_KEY", ""))
    if not key:
        click.echo(f"{RED}No API key configured. Run: vigil register --name <name>{RESET}")
        sys.exit(1)
    return key


def api_request(method, path, json_data=None, auth=True, params=None):
    """Make an API request to the Vigil server."""
    server = get_server()
    url = f"{server}{path}"
    headers = {"Content-Type": "application/json"}
    if auth:
        headers["Authorization"] = f"Bearer {get_api_key()}"
    try:
        response = httpx.request(method, url, json=json_data, headers=headers, params=params, timeout=30)
        return response
    except httpx.ConnectError:
        click.echo(f"{RED}Could not connect to Vigil server at {server}{RESET}")
        click.echo(f"{DIM}Start the server with: uvicorn src.main:app --port 8080{RESET}")
        sys.exit(1)
    except Exception as e:
        click.echo(f"{RED}Request failed: {e}{RESET}")
        sys.exit(1)


def print_header():
    """Print the Vigil CLI header."""
    click.echo(f"""
{GREEN}{BOLD}  Vigil{RESET} {DIM}v1.0.0{RESET}
{DIM}  The trust layer for your AI agent{RESET}
""")


def print_verdict(verdict, risk_score):
    """Format and print a verdict with color."""
    if verdict == "APPROVE":
        color = GREEN
        icon = "[PASS]"
    elif verdict == "REVIEW":
        color = YELLOW
        icon = "[REVIEW]"
    elif verdict == "BLOCK":
        color = RED
        icon = "[BLOCK]"
    else:
        color = CYAN
        icon = f"[{verdict}]"
    click.echo(f"  {color}{BOLD}{icon}{RESET} Risk: {color}{risk_score}{RESET}")


def print_box(title, content_lines, color=DIM):
    """Print a bordered box with content."""
    max_len = max(len(title), max((len(l) for l in content_lines), default=0))
    width = min(max_len + 4, 72)
    click.echo(f"  {color}{'─' * width}{RESET}")
    click.echo(f"  {BOLD}{title}{RESET}")
    click.echo(f"  {color}{'─' * width}{RESET}")
    for line in content_lines:
        click.echo(f"  {line}")
    click.echo(f"  {color}{'─' * width}{RESET}")


# ─── CLI Group ────────────────────────────────────────────────────────────────

@click.group()
@click.version_option(version="1.0.0", prog_name="vigil")
def cli():
    """Vigil CLI — Behavioral intelligence for autonomous agent wallets."""
    pass


# ─── Config ───────────────────────────────────────────────────────────────────

@cli.command()
@click.option("--server", "-s", help="Vigil server URL (e.g. https://svc-mn0q6itc9qru4k2q.buildwithlocus.com)")
@click.option("--key", "-k", help="API key to store")
@click.option("--show", is_flag=True, help="Show current config")
def config(server, key, show):
    """Configure the Vigil CLI."""
    cfg = load_config()

    if show:
        print_header()
        click.echo(f"  {DIM}Server:{RESET}  {cfg.get('server', 'http://localhost:8080')}")
        click.echo(f"  {DIM}API Key:{RESET} {cfg.get('api_key', 'not set')[:12]}{'...' if cfg.get('api_key') else ''}")
        click.echo(f"  {DIM}Name:{RESET}    {cfg.get('name', 'not set')}")
        click.echo(f"  {DIM}Config:{RESET}  {CONFIG_FILE}")
        click.echo()
        return

    if server:
        cfg["server"] = server.rstrip("/")
        click.echo(f"  {GREEN}Server set to {server}{RESET}")
    if key:
        cfg["api_key"] = key
        click.echo(f"  {GREEN}API key stored{RESET}")

    if server or key:
        save_config(cfg)
    else:
        click.echo(f"  {DIM}Use --server, --key, or --show{RESET}")


# ─── Register ─────────────────────────────────────────────────────────────────

@cli.command()
@click.option("--name", "-n", required=True, help="Agent or operator name")
@click.option("--email", "-e", default="", help="Contact email (optional)")
def register(name, email):
    """Register with Vigil and get an API key."""
    print_header()
    click.echo(f"  Registering as {BOLD}{name}{RESET}...")

    resp = api_request("POST", "/api/register", {"name": name, "email": email}, auth=False)

    if resp.status_code == 200:
        data = resp.json()
        api_key = data.get("api_key", "")
        operator_id = data.get("operator_id", "")

        # Save to config
        cfg = load_config()
        cfg["api_key"] = api_key
        cfg["name"] = name
        cfg["operator_id"] = operator_id
        save_config(cfg)

        click.echo(f"  {GREEN}Registered successfully{RESET}")
        click.echo()
        print_box("Credentials", [
            f"{DIM}API Key:{RESET}      {CYAN}{api_key}{RESET}",
            f"{DIM}Operator ID:{RESET}  {operator_id}",
            f"",
            f"{YELLOW}Save your API key — it cannot be recovered.{RESET}",
            f"{DIM}Use vigil regenerate-key if you lose it.{RESET}",
        ])
        click.echo()
        click.echo(f"  {DIM}Config saved to {CONFIG_FILE}{RESET}")
    else:
        click.echo(f"  {RED}Registration failed: {resp.text}{RESET}")


# ─── Regenerate Key ───────────────────────────────────────────────────────────

@cli.command("regenerate-key")
@click.option("--operator-id", "-o", help="Your operator ID (from registration)")
def regenerate_key(operator_id):
    """Regenerate your API key."""
    print_header()
    if not operator_id:
        cfg = load_config()
        operator_id = cfg.get("operator_id")
        if not operator_id:
            click.echo(f"  {RED}Provide --operator-id or register first{RESET}")
            return

    click.echo(f"  Regenerating API key for {BOLD}{operator_id}{RESET}...")

    resp = api_request("POST", "/api/regenerate-key", {"operator_id": operator_id}, auth=False)

    if resp.status_code == 200:
        data = resp.json()
        new_key = data.get("api_key", "")

        cfg = load_config()
        cfg["api_key"] = new_key
        save_config(cfg)

        click.echo(f"  {GREEN}New API key generated{RESET}")
        click.echo()
        print_box("New Key", [
            f"{CYAN}{new_key}{RESET}",
            f"",
            f"{YELLOW}Save this key — the old one is now invalid.{RESET}",
        ])
    else:
        click.echo(f"  {RED}Failed: {resp.text}{RESET}")


# ─── Audit ────────────────────────────────────────────────────────────────────

@cli.command()
@click.option("--from", "from_addr", required=True, help="Sender wallet address")
@click.option("--to", "to_addr", required=True, help="Recipient wallet address")
@click.option("--amount", required=True, type=float, help="Transaction amount in USDC")
@click.option("--memo", default="", help="Transaction memo/description")
@click.option("--agent-name", default="CLI Agent", help="Name of the agent")
@click.option("--agent-task", default="", help="Agent's authorized task description")
@click.option("--deep", is_flag=True, help="Run deep audit with trajectory analysis ($0.05)")
@click.option("--json-output", "json_out", is_flag=True, help="Output raw JSON")
def audit(from_addr, to_addr, amount, memo, agent_name, agent_task, deep, json_out):
    """Audit a transaction through Vigil's 4-layer pipeline."""
    if not json_out:
        print_header()
        click.echo(f"  {DIM}Auditing transaction...{RESET}")
        click.echo(f"  {DIM}From:{RESET} {from_addr[:10]}...{from_addr[-6:]}")
        click.echo(f"  {DIM}To:{RESET}   {to_addr[:10]}...{to_addr[-6:]}")
        click.echo(f"  {DIM}Amount:{RESET} ${amount:.2f} USDC")
        if memo:
            click.echo(f"  {DIM}Memo:{RESET} {memo}")
        click.echo()

    endpoint = "/api/audit/deep" if deep else "/api/audit"
    payload = {
        "transaction": {
            "from": from_addr,
            "to": to_addr,
            "amount": amount,
            "memo": memo,
        },
        "agent_context": {
            "name": agent_name,
            "task": agent_task,
        },
    }

    resp = api_request("POST", endpoint, payload)

    if resp.status_code == 200:
        data = resp.json()
        if json_out:
            click.echo(json.dumps(data, indent=2))
            return

        print_verdict(data["verdict"], data["risk_score"])
        click.echo()
        print_box("Audit Result", [
            f"{DIM}Verdict:{RESET}      {data['verdict']}",
            f"{DIM}Risk Score:{RESET}   {data['risk_score']}",
            f"{DIM}Reasoning:{RESET}    {data.get('reasoning', 'N/A')}",
            f"{DIM}Action:{RESET}       {data.get('recommended_action', 'N/A')}",
            f"{DIM}Attestation:{RESET}  {data.get('attestation_tx', 'pending')}",
            f"{DIM}Cost:{RESET}         {data.get('cost', data.get('cost_usdc', '0.01'))} USDC",
        ])

        if deep and "counterparty_profile" in data:
            cp = data["counterparty_profile"]
            click.echo()
            print_box("Counterparty Profile", [
                f"{DIM}Address:{RESET}      {cp.get('address', to_addr)}",
                f"{DIM}Trust:{RESET}        {cp.get('trust_score', 'unknown')}",
                f"{DIM}Category:{RESET}     {cp.get('category', 'unknown')}",
                f"{DIM}Interactions:{RESET} {cp.get('total_interactions', 0)}",
                f"{DIM}Flags:{RESET}        {cp.get('flagged_interactions', 0)}",
            ])
    else:
        click.echo(f"  {RED}Audit failed: {resp.text}{RESET}")


# ─── Reputation ───────────────────────────────────────────────────────────────

@cli.command()
@click.argument("address")
@click.option("--json-output", "json_out", is_flag=True, help="Output raw JSON")
def reputation(address, json_out):
    """Look up the trust profile for any address."""
    resp = api_request("GET", f"/api/reputation/{address}")

    if resp.status_code == 200:
        data = resp.json()
        if json_out:
            click.echo(json.dumps(data, indent=2))
            return

        print_header()
        trust = data.get("trust_score", "unknown")
        label = data.get("known_label", data.get("label", "Unknown"))
        category = data.get("category", "unknown")

        # Color code trust
        if isinstance(trust, (int, float)):
            if trust >= 0.8:
                trust_color = GREEN
            elif trust >= 0.5:
                trust_color = YELLOW
            else:
                trust_color = RED
            trust_str = f"{trust_color}{trust}{RESET}"
        else:
            trust_str = str(trust)

        print_box(f"Reputation: {label}", [
            f"{DIM}Address:{RESET}      {address}",
            f"{DIM}Trust:{RESET}        {trust_str}",
            f"{DIM}Category:{RESET}     {category}",
            f"{DIM}Interactions:{RESET} {data.get('total_interactions', 0)}",
            f"{DIM}Flagged:{RESET}      {data.get('flagged_interactions', 0)}",
            f"{DIM}First Seen:{RESET}   {data.get('first_seen', 'N/A')}",
        ])
    else:
        click.echo(f"  {RED}Lookup failed: {resp.text}{RESET}")


# ─── Graph ────────────────────────────────────────────────────────────────────

@cli.command()
@click.option("--json-output", "json_out", is_flag=True, help="Output raw JSON")
def graph(json_out):
    """Display the reputation graph summary."""
    resp = api_request("GET", "/api/reputation/graph")

    if resp.status_code == 200:
        data = resp.json()
        if json_out:
            click.echo(json.dumps(data, indent=2))
            return

        print_header()
        click.echo(f"  {BOLD}Reputation Graph{RESET}")
        click.echo(f"  {DIM}{'─' * 60}{RESET}")
        click.echo(f"  {DIM}Total Audits:{RESET}   {data.get('total_audits', 0)}")
        click.echo(f"  {GREEN}Approved:{RESET}      {data.get('total_approved', 0)}")
        click.echo(f"  {YELLOW}Flagged:{RESET}       {data.get('total_flagged', 0)}")
        click.echo(f"  {RED}Blocked:{RESET}       {data.get('total_blocked', 0)}")
        click.echo()

        nodes = data.get("nodes", [])
        if nodes:
            click.echo(f"  {BOLD}{'Address':<16} {'Label':<20} {'Trust':>6} {'Category':<14} {'Txns':>5}{RESET}")
            click.echo(f"  {DIM}{'─' * 65}{RESET}")
            for n in sorted(nodes, key=lambda x: x.get("trust_score", 0), reverse=True):
                trust = n.get("trust_score", 0)
                if trust >= 0.8:
                    tc = GREEN
                elif trust >= 0.5:
                    tc = YELLOW
                else:
                    tc = RED
                addr = n.get("address", "")[:14] + ".."
                label = n.get("label", "")[:18]
                cat = n.get("category", "")[:12]
                txns = n.get("total_interactions", 0)
                click.echo(f"  {DIM}{addr:<16}{RESET} {label:<20} {tc}{trust:>5.2f}{RESET}  {cat:<14} {txns:>5}")
        click.echo()
    else:
        click.echo(f"  {RED}Graph query failed: {resp.text}{RESET}")


# ─── Status ───────────────────────────────────────────────────────────────────

@cli.command()
@click.option("--json-output", "json_out", is_flag=True, help="Output raw JSON")
def status(json_out):
    """Show Vigil server status and wallet info."""
    resp = api_request("GET", "/api/status")

    if resp.status_code == 200:
        data = resp.json()
        if json_out:
            click.echo(json.dumps(data, indent=2))
            return

        print_header()
        wallet = data.get("wallet", {})
        audits = data.get("audits", {})
        print_box("Server Status", [
            f"{DIM}Status:{RESET}     {GREEN}running{RESET}",
            f"{DIM}Wallet:{RESET}     {wallet.get('address', 'N/A')}",
            f"{DIM}Balance:{RESET}    {wallet.get('balance', 0)} {wallet.get('currency', 'USDC')}",
            f"",
            f"{DIM}Total Audits:{RESET}  {audits.get('total_audits', 0)}",
            f"{DIM}Approved:{RESET}      {audits.get('approved', 0)}",
            f"{DIM}Flagged:{RESET}       {audits.get('flagged', 0)}",
            f"{DIM}Blocked:{RESET}       {audits.get('blocked', 0)}",
        ])
    else:
        click.echo(f"  {RED}Status check failed: {resp.text}{RESET}")


# ─── Health ───────────────────────────────────────────────────────────────────

@cli.command()
def health():
    """Quick health check on the Vigil server."""
    resp = api_request("GET", "/health", auth=False)
    if resp.status_code == 200:
        data = resp.json()
        click.echo(f"  {GREEN}OK{RESET} — {data.get('service', 'vigil')} v{data.get('version', '?')}")
    else:
        click.echo(f"  {RED}DOWN{RESET} — {resp.status_code}")


# ─── Audits List ──────────────────────────────────────────────────────────────

@cli.command("audits")
@click.option("--limit", "-l", default=20, help="Number of recent audits to show")
@click.option("--json-output", "json_out", is_flag=True, help="Output raw JSON")
def list_audits(limit, json_out):
    """List recent audit results."""
    resp = api_request("GET", "/api/audits", params={"limit": limit})

    if resp.status_code == 200:
        data = resp.json()
        if json_out:
            click.echo(json.dumps(data, indent=2))
            return

        print_header()
        audits = data.get("audits", [])
        click.echo(f"  {BOLD}Recent Audits{RESET} ({data.get('total', 0)} shown)")
        click.echo(f"  {DIM}{'─' * 72}{RESET}")

        if not audits:
            click.echo(f"  {DIM}No audits yet. Submit one with: vigil audit --from 0x... --to 0x... --amount 100{RESET}")
        else:
            click.echo(f"  {BOLD}{'Tx Hash':<14} {'Verdict':<10} {'Risk':>6} {'L2':>3} {'Time':<20}{RESET}")
            click.echo(f"  {DIM}{'─' * 72}{RESET}")
            for a in audits:
                verdict = a.get("verdict", "?")
                risk = a.get("risk_score", 0)
                tx = a.get("tx_hash", "")[:12] + ".." if a.get("tx_hash") else "N/A"
                l2 = "Y" if a.get("layer2_invoked") else "N"
                ts = a.get("timestamp", "")[:19]

                if verdict == "APPROVE":
                    vc = GREEN
                elif verdict == "REVIEW":
                    vc = YELLOW
                else:
                    vc = RED

                click.echo(f"  {DIM}{tx:<14}{RESET} {vc}{verdict:<10}{RESET} {risk:>5.3f}  {l2:>2}  {DIM}{ts}{RESET}")
        click.echo()
    else:
        click.echo(f"  {RED}Failed: {resp.text}{RESET}")


# ─── Policies ─────────────────────────────────────────────────────────────────

@cli.group()
def policies():
    """Manage natural language policies."""
    pass


@policies.command("list")
def policies_list():
    """List all active policies."""
    # Policies are managed server-side via the dashboard
    # CLI can fetch via a status or dedicated endpoint
    print_header()
    click.echo(f"  {BOLD}Policies{RESET}")
    click.echo(f"  {DIM}Policies are managed through the dashboard at /dashboard{RESET}")
    click.echo(f"  {DIM}Use 'vigil policies add' to create new policies via CLI{RESET}")
    click.echo()


@policies.command("add")
@click.option("--agent", "-a", default="global", help="Agent address (or 'global' for all)")
@click.option("--rule", "-r", required=True, help="Policy rule in natural language")
def policies_add(agent, rule):
    """Add a new natural language policy."""
    print_header()
    click.echo(f"  Adding policy for {BOLD}{agent}{RESET}...")

    resp = api_request("POST", "/api/policy", {
        "agent_address": agent,
        "policy_text": rule,
    })

    if resp.status_code == 200:
        data = resp.json()
        click.echo(f"  {GREEN}Policy created{RESET}")
        print_box("Policy", [
            f"{DIM}Agent:{RESET}  {agent}",
            f"{DIM}Rule:{RESET}   {rule}",
            f"{DIM}ID:{RESET}     {data.get('policy_id', 'N/A')}",
        ])
    else:
        click.echo(f"  {RED}Failed: {resp.text}{RESET}")


# ─── Monitor ──────────────────────────────────────────────────────────────────

@cli.command()
@click.option("--wallet", "-w", required=True, help="Agent wallet address to monitor")
@click.option("--name", "-n", required=True, help="Agent name")
@click.option("--task", "-t", default="", help="Agent's authorized task description")
def monitor(wallet, name, task):
    """Register an agent wallet for continuous monitoring."""
    print_header()
    click.echo(f"  Registering {BOLD}{name}{RESET} for monitoring...")

    resp = api_request("POST", "/api/monitor", {
        "wallet_address": wallet,
        "agent_name": name,
        "agent_task": task,
    })

    if resp.status_code == 200:
        data = resp.json()
        click.echo(f"  {GREEN}Agent registered for monitoring{RESET}")
        print_box("Monitored Agent", [
            f"{DIM}Name:{RESET}    {name}",
            f"{DIM}Wallet:{RESET}  {wallet}",
            f"{DIM}Task:{RESET}    {task or 'not specified'}",
        ])
    else:
        click.echo(f"  {RED}Failed: {resp.text}{RESET}")


@cli.command("agents")
def list_agents():
    """List all monitored agents."""
    resp = api_request("GET", "/api/monitor/agents")

    if resp.status_code == 200:
        data = resp.json()
        print_header()
        agents = data.get("agents", [])
        click.echo(f"  {BOLD}Monitored Agents{RESET} ({data.get('total', 0)})")
        click.echo(f"  {DIM}{'─' * 60}{RESET}")

        if not agents:
            click.echo(f"  {DIM}No agents monitored. Use: vigil monitor --wallet 0x... --name Bot{RESET}")
        else:
            for a in agents:
                click.echo(f"  {CYAN}{a.get('name', '?')}{RESET}")
                click.echo(f"    {DIM}Wallet:{RESET} {a.get('wallet_address', '?')}")
                click.echo(f"    {DIM}Task:{RESET}   {a.get('task', 'N/A')}")
                click.echo()
    else:
        click.echo(f"  {RED}Failed: {resp.text}{RESET}")


# ─── Attestations ─────────────────────────────────────────────────────────────

@cli.command()
@click.option("--limit", "-l", default=20, help="Number of attestations to show")
@click.option("--json-output", "json_out", is_flag=True, help="Output raw JSON")
def attestations(limit, json_out):
    """List onchain ERC-8004 attestations."""
    resp = api_request("GET", "/api/attestations", params={"limit": limit})

    if resp.status_code == 200:
        data = resp.json()
        if json_out:
            click.echo(json.dumps(data, indent=2))
            return

        print_header()
        atts = data.get("attestations", [])
        click.echo(f"  {BOLD}ERC-8004 Attestations{RESET} ({data.get('total', 0)} total)")
        click.echo(f"  {DIM}{'─' * 72}{RESET}")

        if not atts:
            click.echo(f"  {DIM}No attestations yet.{RESET}")
        else:
            for a in atts:
                verdict = a.get("verdict", "?")
                vc = GREEN if verdict == "APPROVE" else (YELLOW if verdict == "REVIEW" else RED)
                click.echo(f"  {vc}{verdict:<10}{RESET} {DIM}risk:{RESET}{a.get('risk_score', '?'):>6}  {DIM}domain:{RESET} {a.get('domain', '?')}")
                click.echo(f"    {DIM}subject:{RESET} {a.get('subject', '?')}")
                click.echo(f"    {DIM}hash:{RESET}    {a.get('attestation_hash', 'pending')}")
                click.echo()
    else:
        click.echo(f"  {RED}Failed: {resp.text}{RESET}")


# ─── Watch (live tail) ────────────────────────────────────────────────────────

@cli.command()
@click.option("--interval", "-i", default=5, help="Poll interval in seconds")
def watch(interval):
    """Live-tail audit results as they come in."""
    import time

    print_header()
    click.echo(f"  {BOLD}Watching for new audits...{RESET} {DIM}(Ctrl+C to stop){RESET}")
    click.echo(f"  {DIM}{'─' * 60}{RESET}")

    seen = set()

    try:
        while True:
            resp = api_request("GET", "/api/audits", params={"limit": 10})
            if resp.status_code == 200:
                audits = resp.json().get("audits", [])
                for a in reversed(audits):
                    tx = a.get("tx_hash", "")
                    key = f"{tx}_{a.get('timestamp', '')}"
                    if key not in seen:
                        seen.add(key)
                        verdict = a.get("verdict", "?")
                        risk = a.get("risk_score", 0)
                        ts = a.get("timestamp", "")[:19]

                        if verdict == "APPROVE":
                            vc = GREEN
                        elif verdict == "REVIEW":
                            vc = YELLOW
                        else:
                            vc = RED

                        tx_short = (tx[:12] + "..") if tx else "N/A"
                        click.echo(f"  {DIM}{ts}{RESET}  {vc}{verdict:<8}{RESET}  risk:{risk:.3f}  {DIM}{tx_short}{RESET}")

            time.sleep(interval)
    except KeyboardInterrupt:
        click.echo(f"\n  {DIM}Stopped watching.{RESET}")


# ─── x402 Discovery ──────────────────────────────────────────────────────────

@cli.command("pricing")
def pricing():
    """Show Vigil's x402 pricing for pay-per-call services."""
    resp = api_request("GET", "/.well-known/x402", auth=False)

    if resp.status_code == 200:
        data = resp.json()
        print_header()
        click.echo(f"  {BOLD}x402 Pay-Per-Call Pricing{RESET}")
        click.echo(f"  {DIM}{'─' * 60}{RESET}")

        x402 = data.get("x402", data)
        endpoints = x402.get("endpoints", {})
        payment_addr = x402.get("payment_address", "N/A")
        accepts = x402.get("accepts", [])

        for path, info in endpoints.items():
            price = info.get("price", "?")
            currency = info.get("currency", "USDC")
            desc = info.get("description", "")
            chain = info.get("chain", "base")
            price_color = GREEN if price == "0.00" else CYAN
            click.echo(f"  {BOLD}{path}{RESET}")
            click.echo(f"    {DIM}Price:{RESET}  {price_color}${price} {currency}{RESET} {DIM}({chain}){RESET}")
            if desc:
                click.echo(f"    {DIM}Info:{RESET}   {desc}")
            click.echo()

        click.echo(f"  {DIM}Payment Address:{RESET} {payment_addr}")
        click.echo(f"  {DIM}Accepts:{RESET}         {', '.join(accepts)}")
        click.echo()
    else:
        click.echo(f"  {RED}Failed: {resp.text}{RESET}")


# ─── Entrypoint ───────────────────────────────────────────────────────────────

def main():
    cli()


if __name__ == "__main__":
    main()
