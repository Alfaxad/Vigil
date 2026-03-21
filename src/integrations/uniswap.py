"""Uniswap Trading API integration for swap verification."""

import httpx
import logging
from typing import Optional

logger = logging.getLogger(__name__)

# Known token addresses on Base
BASE_TOKENS = {
    "USDC": "0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913",
    "WETH": "0x4200000000000000000000000000000000000006",
    "DAI": "0x50c5725949A6F0c72E6C4a641F24049A917DB0Cb",
    "USDbC": "0xd9aAEc86B65D86f6A7B5B1b0c42FFA531710b6CA",
    "cbETH": "0x2Ae3F1Ec7F1F5012CFEab0185bfc7aa3cf0DEc22",
}

UNISWAP_API_BASE = "https://trade-api.gateway.uniswap.org/v1"
BASE_CHAIN_ID = 8453


class UniswapVerifier:
    """Verifies swap parameters against Uniswap Trading API."""

    def __init__(self, api_key: Optional[str] = None):
        self._client = httpx.AsyncClient(
            base_url=UNISWAP_API_BASE,
            headers={
                "Content-Type": "application/json",
                **({"x-api-key": api_key} if api_key else {}),
            },
            timeout=10,
        )

    async def get_quote(
        self,
        token_in: str,
        token_out: str,
        amount: str,
        swapper: str = "0x0000000000000000000000000000000000000000",
    ) -> Optional[dict]:
        """Get a swap quote from Uniswap to verify pricing."""
        try:
            resp = await self._client.post(
                "/quote",
                json={
                    "type": "EXACT_INPUT",
                    "tokenInChainId": BASE_CHAIN_ID,
                    "tokenOutChainId": BASE_CHAIN_ID,
                    "tokenIn": token_in,
                    "tokenOut": token_out,
                    "amount": amount,
                    "swapper": swapper,
                    "slippageTolerance": 0.5,
                },
            )
            if resp.status_code == 200:
                data = resp.json()
                return {
                    "quote_amount_out": data.get("quote", {}).get("amountOut"),
                    "gas_estimate": data.get("quote", {}).get("gasUseEstimate"),
                    "route": data.get("quote", {}).get("route"),
                    "price_impact": data.get("quote", {}).get("priceImpact"),
                }
            logger.warning(f"Uniswap quote failed: {resp.status_code}")
        except Exception as e:
            logger.warning(f"Uniswap API error: {e}")
        return None

    async def verify_swap_transaction(
        self,
        to_address: str,
        amount: float,
        memo: str = "",
    ) -> dict:
        """Verify if a swap transaction looks legitimate by checking against Uniswap."""
        # Check if the target is the known Uniswap router
        uniswap_routers = {
            "0x2626664c2603336e57b271c5c0b26f421741e481",  # Universal Router
            "0x3fc91a3afd70395cd496c647d5a6cc9d4b2b7fad",  # Universal Router v2
        }

        is_uniswap = to_address.lower() in uniswap_routers

        result = {
            "is_known_router": is_uniswap,
            "router_verified": is_uniswap,
            "amount_reasonable": amount < 10000,  # Basic sanity check
            "risk_modifier": 0.0,
        }

        if is_uniswap:
            result["risk_modifier"] = -0.15  # Lower risk for verified router
        elif "swap" in memo.lower() and not is_uniswap:
            result["risk_modifier"] = 0.2  # Higher risk for unverified swap router
            result["warning"] = "Swap claims Uniswap but uses unknown router"

        return result

    async def close(self):
        await self._client.aclose()
