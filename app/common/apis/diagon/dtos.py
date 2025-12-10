"""DTOs for Diagon API operations."""

from typing import Optional

from pydantic import BaseModel, Field


class AssetResponse(BaseModel):
    """Response model for an asset."""

    id: str = Field(..., description="Asset identifier")
    total: str = Field(..., description="Total amount")
    balance: str = Field(..., description="Balance amount")
    lockedAmount: str = Field(..., description="Locked amount", alias="lockedAmount")
    available: str = Field(..., description="Available amount")
    pending: str = Field(..., description="Pending amount")
    frozen: str = Field(..., description="Frozen amount")
    staked: str = Field(..., description="Staked amount")
    blockHeight: str = Field(..., description="Block height", alias="blockHeight")
    blockHash: Optional[str] = Field(None, description="Block hash", alias="blockHash")

    class Config:
        """Pydantic configuration."""

        populate_by_name = True


class AccountResponse(BaseModel):
    """Response model for an account."""

    id: str = Field(..., description="Account ID")
    name: str = Field(..., description="Account name")
    hiddenOnUI: bool = Field(..., description="Hidden on UI flag", alias="hiddenOnUI")
    autoFuel: bool = Field(..., description="Auto fuel flag", alias="autoFuel")
    assets: list[AssetResponse] = Field(..., description="List of assets")

    class Config:
        """Pydantic configuration."""

        populate_by_name = True


class RefreshBalanceResponse(BaseModel):
    """Response model for refresh balance operation."""

    message: str = Field(..., description="Response message")
    idempotencyKey: str = Field(..., description="Idempotency key", alias="idempotencyKey")

    class Config:
        """Pydantic configuration."""

        populate_by_name = True
