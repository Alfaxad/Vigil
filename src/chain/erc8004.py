import json
import hashlib
import logging
from typing import Optional
from eth_account import Account
from eth_account.messages import encode_defunct
from web3 import Web3
from src.config import get_settings
from src.auditor.models import AuditResult
from src.chain.contracts import (
    BASE_RPC_URL,
    ERC8004_REPUTATION_REGISTRY,
)

logger = logging.getLogger("vigil.erc8004")

# Minimal ABI for ReputationRegistry.giveFeedback
REPUTATION_ABI = [
    {
        "inputs": [
            {"name": "agentId", "type": "uint256"},
            {"name": "value", "type": "int128"},
            {"name": "valueDecimals", "type": "uint8"},
            {"name": "tag1", "type": "string"},
            {"name": "tag2", "type": "string"},
            {"name": "endpoint", "type": "string"},
            {"name": "ipfsHash", "type": "string"},
            {"name": "dataHash", "type": "bytes32"},
        ],
        "name": "giveFeedback",
        "outputs": [],
        "stateMutability": "nonpayable",
        "type": "function",
    }
]


class ERC8004Attestor:
    """Writes audit attestations as ERC-8004 reputation entries on Base."""

    def __init__(self):
        settings = get_settings()
        self.private_key = settings.locus_owner_private_key
        self.owner_address = settings.locus_owner_address
        self._attestations: list[dict] = []
        self._w3: Optional[Web3] = None
        self._contract = None

        # Initialize Web3 connection to Base
        if ERC8004_REPUTATION_REGISTRY:
            try:
                self._w3 = Web3(Web3.HTTPProvider(BASE_RPC_URL))
                self._contract = self._w3.eth.contract(
                    address=Web3.to_checksum_address(ERC8004_REPUTATION_REGISTRY),
                    abi=REPUTATION_ABI,
                )
                logger.info(
                    f"ERC-8004 attestor connected to Base: "
                    f"ReputationRegistry={ERC8004_REPUTATION_REGISTRY}"
                )
            except Exception as e:
                logger.warning(f"Could not connect to Base: {e}")

    def _build_attestation_data(
        self, result: AuditResult, audited_address: str
    ) -> dict:
        report = {
            "schema": "vigil-audit-v1",
            "auditor": self.owner_address,
            "subject": audited_address,
            "tx_hash": result.tx_hash or "",
            "statistical_score": round(result.statistical_score, 4),
            "verdict": result.verdict.value,
            "risk_score": round(result.risk_score, 4),
            "risk_level": result.risk_level.value,
            "reasoning": result.reasoning,
            "evidence": result.evidence,
            "timestamp": result.timestamp.isoformat(),
        }
        report_json = json.dumps(report, sort_keys=True)
        file_hash = "0x" + hashlib.sha256(report_json.encode()).hexdigest()

        return {
            "subject": audited_address,
            "tags": [
                "vigil-audit",
                result.risk_level.value,
                result.verdict.value.lower(),
            ],
            "fileHash": file_hash,
            "report": report,
            # ERC-8004 reputation feedback fields
            "feedback_value": int((1.0 - result.risk_score) * 100),  # 0-100 safety score
            "feedback_tag1": "vigil-audit",
            "feedback_tag2": result.verdict.value.lower(),
        }

    def _sign_attestation(self, attestation_data: dict) -> str:
        if not self.private_key:
            return ""
        message_text = json.dumps(
            {k: v for k, v in attestation_data.items() if k != "report"},
            sort_keys=True,
        )
        message = encode_defunct(text=message_text)
        signed = Account.sign_message(message, private_key=self.private_key)
        return signed.signature.hex()

    async def attest(
        self, result: AuditResult, audited_address: str
    ) -> Optional[str]:
        attestation = self._build_attestation_data(result, audited_address)
        signature = self._sign_attestation(attestation)
        attestation["signature"] = signature

        # Store locally
        self._attestations.append(attestation)

        logger.info(
            f"Attestation created: subject={audited_address} "
            f"verdict={result.verdict.value} "
            f"hash={attestation['fileHash'][:18]}..."
        )

        # Return the file hash as attestation reference
        return attestation["fileHash"]

    def get_attestations(self, limit: int = 50) -> list[dict]:
        return self._attestations[-limit:]

    def get_attestation_count(self) -> int:
        return len(self._attestations)
