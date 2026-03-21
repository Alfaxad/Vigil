from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class Transaction(BaseModel):
    id: Optional[str] = None
    tx_hash: Optional[str] = None
    from_address: Optional[str] = None
    to_address: Optional[str] = None
    amount: float = 0.0
    memo: Optional[str] = None
    timestamp: Optional[datetime] = None
    status: Optional[str] = None
    type: Optional[str] = None


class WalletBalance(BaseModel):
    balance: float = 0.0
    currency: str = "USDC"
    wallet_address: Optional[str] = None


class LocusStatus(BaseModel):
    wallet_status: str = "unknown"
    wallet_address: Optional[str] = None
