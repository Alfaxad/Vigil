# ERC-8004 contract references on Base
# Deployed January 29, 2026 — same addresses on 20+ chains

BASE_CHAIN_ID = 8453
BASE_RPC_URL = "https://mainnet.base.org"

# ERC-8004 Identity Registry (ERC-721 based)
ERC8004_IDENTITY_REGISTRY = "0x8004A169FB4a3325136EB29fA0ceB6D2e539a432"

# ERC-8004 Reputation Registry (feedback, ratings, tags)
ERC8004_REPUTATION_REGISTRY = "0x8004BAa17C55a88189AE136b182e5fdA19dE9b63"

# Vigil's registration tx on Base
VIGIL_REGISTRATION_TX = "https://basescan.org/tx/0xb130bd07984f9dc9885643378347d3bda4186a4750b3efef24820af1ab0dcd69"

# USDC on Base (6 decimals!)
USDC_BASE = "0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913"

# Reputation feedback struct for Vigil audits:
# value: risk_score * 100 (0-100), decimals: 0
# tag1: "vigil-audit"
# tag2: verdict ("clean", "flagged", "blocked")
# endpoint: vigil service URL
# ipfsHash: hash of full audit report
