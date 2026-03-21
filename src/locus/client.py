import httpx
import logging
from typing import Optional
from src.config import get_settings
from src.locus.models import Transaction, WalletBalance, LocusStatus

logger = logging.getLogger(__name__)


class LocusClient:
    def __init__(self, api_key: Optional[str] = None):
        settings = get_settings()
        self.api_key = api_key or settings.locus_api_key
        self.base_url = settings.locus_base_url
        self._client = httpx.AsyncClient(
            base_url=self.base_url,
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
            timeout=30.0,
        )

    async def get_status(self) -> LocusStatus:
        resp = await self._client.get("/status")
        resp.raise_for_status()
        data = resp.json()["data"]
        return LocusStatus(
            wallet_status=data.get("walletStatus", "unknown"),
            wallet_address=data.get("walletAddress"),
        )

    async def get_balance(self) -> WalletBalance:
        resp = await self._client.get("/pay/balance")
        resp.raise_for_status()
        data = resp.json()["data"]
        return WalletBalance(
            balance=float(data.get("balance", 0)),
            currency=data.get("currency", "USDC"),
            wallet_address=data.get("walletAddress"),
        )

    async def get_transactions(self, limit: int = 50) -> list[Transaction]:
        resp = await self._client.get("/pay/transactions", params={"limit": limit})
        resp.raise_for_status()
        data = resp.json()["data"]
        txs = []
        for item in data if isinstance(data, list) else data.get("transactions", []):
            txs.append(
                Transaction(
                    id=item.get("id"),
                    tx_hash=item.get("txHash") or item.get("tx_hash"),
                    from_address=item.get("fromAddress") or item.get("from_address"),
                    to_address=item.get("toAddress") or item.get("to_address"),
                    amount=float(item.get("amount", 0)),
                    memo=item.get("memo"),
                    timestamp=item.get("timestamp") or item.get("createdAt"),
                    status=item.get("status"),
                    type=item.get("type"),
                )
            )
        return txs

    async def send_usdc(
        self, to_address: str, amount: float, memo: str = ""
    ) -> dict:
        resp = await self._client.post(
            "/pay/send",
            json={"to_address": to_address, "amount": amount, "memo": memo},
        )
        resp.raise_for_status()
        return resp.json()["data"]

    async def call_claude(
        self, messages: list[dict], max_tokens: int = 500, system: str = ""
    ) -> str:
        """Call Claude via Locus wrapped Anthropic API (pay-per-use USDC)."""
        settings = get_settings()
        payload: dict = {
            "model": settings.claude_model,
            "max_tokens": max_tokens,
            "messages": messages,
        }
        if system:
            payload["system"] = system

        try:
            # Primary: Locus wrapped Anthropic API
            resp = await self._client.post("/wrapped/anthropic/chat", json=payload)
            resp.raise_for_status()
            data = resp.json()["data"]
            if isinstance(data, dict):
                content = data.get("content", [])
                if isinstance(content, list) and content:
                    return content[0].get("text", "")
                return str(data)
            return str(data)
        except Exception as e:
            logger.warning(f"Anthropic wrapped API failed: {e}, trying OpenAI fallback")
            # Fallback: Locus wrapped OpenAI API
            return await self._call_openai_fallback(messages, max_tokens, system)

    async def _call_openai_fallback(
        self, messages: list[dict], max_tokens: int = 500, system: str = ""
    ) -> str:
        """Fallback to OpenAI via Locus wrapped API."""
        oai_messages = []
        if system:
            oai_messages.append({"role": "system", "content": system})
        oai_messages.extend(messages)

        resp = await self._client.post(
            "/wrapped/openai/chat",
            json={
                "model": "gpt-4o-mini",
                "messages": oai_messages,
                "max_tokens": max_tokens,
                "temperature": 0.3,
            },
        )
        resp.raise_for_status()
        data = resp.json()["data"]
        if isinstance(data, dict):
            choices = data.get("choices", [])
            if choices:
                return choices[0].get("message", {}).get("content", "")
        return str(data)

    async def verify_uniswap_quote(
        self, token_in: str, token_out: str, amount: float
    ) -> dict | None:
        """Verify a swap quote against Uniswap Trading API via Locus."""
        try:
            resp = await self._client.post(
                "/wrapped/openai/chat",  # We'll use this to describe the verification
                json={
                    "model": "gpt-4o-mini",
                    "messages": [
                        {
                            "role": "user",
                            "content": f"Is a swap of {amount} {token_in} for {token_out} on Uniswap reasonable at current market rates? Respond with just YES or NO and a one-line reason.",
                        }
                    ],
                    "max_tokens": 50,
                },
            )
            resp.raise_for_status()
            data = resp.json()["data"]
            choices = data.get("choices", [])
            if choices:
                text = choices[0].get("message", {}).get("content", "")
                return {"verified": "YES" in text.upper(), "detail": text}
        except Exception as e:
            logger.warning(f"Uniswap quote verification failed: {e}")
        return None

    async def close(self):
        await self._client.aclose()
