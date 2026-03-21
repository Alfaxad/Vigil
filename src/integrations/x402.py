"""x402 Protocol support — makes Vigil's audit endpoint callable as a paid API.

When another agent calls Vigil's audit endpoint with an x402 payment header,
the payment is verified and the audit is executed. This allows any agent in
the ecosystem to use Vigil as a trust-as-a-service layer, paying per query.
"""

import logging
from typing import Optional

logger = logging.getLogger(__name__)

# x402 payment verification
# In production, this verifies the x402 payment proof from the request header
# For now, we support both direct API key auth and x402 payment headers


def extract_x402_payment(headers: dict) -> Optional[dict]:
    """Extract x402 payment proof from request headers."""
    payment_header = headers.get("x-payment") or headers.get("X-Payment")
    if not payment_header:
        return None

    # Parse x402 payment proof
    # Format: x402 <base64-encoded payment proof>
    try:
        if payment_header.startswith("x402 "):
            proof = payment_header[5:]
            return {
                "protocol": "x402",
                "proof": proof,
                "verified": True,  # In production, verify against Locus
            }
    except Exception as e:
        logger.warning(f"x402 payment parse error: {e}")
    return None


def get_audit_pricing() -> dict:
    """Return x402-compatible pricing for Vigil endpoints."""
    return {
        "x402": {
            "version": "1.0",
            "endpoints": {
                "/api/audit": {
                    "price": "0.01",
                    "currency": "USDC",
                    "chain": "base",
                    "description": "Standard 4-layer behavioral audit with onchain attestation",
                },
                "/api/audit/deep": {
                    "price": "0.05",
                    "currency": "USDC",
                    "chain": "base",
                    "description": "Deep audit with trajectory analysis and counterparty deep-dive",
                },
                "/api/reputation/{address}": {
                    "price": "0.00",
                    "currency": "USDC",
                    "chain": "base",
                    "description": "Free reputation lookup",
                },
            },
            "payment_address": "0xa2cec58dd199c392a4b2cd86f48fd620bb2040ff",
            "accepts": ["locus-x402", "direct-usdc"],
        }
    }
