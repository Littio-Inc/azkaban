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
    blockHeight: Optional[str] = Field(None, description="Block height", alias="blockHeight")
    blockHash: Optional[str] = Field(None, description="Block hash", alias="blockHash")

    class Config:
        populate_by_name = True


class AccountResponse(BaseModel):
    """Response model for an account."""

    id: str = Field(..., description="Account ID")
    name: str = Field(..., description="Account name")
    hiddenOnUI: bool = Field(..., description="Hidden on UI flag", alias="hiddenOnUI")
    autoFuel: bool = Field(..., description="Auto fuel flag", alias="autoFuel")
    assets: list[AssetResponse] = Field(..., description="List of assets")

    class Config:
        populate_by_name = True


class RefreshBalanceResponse(BaseModel):
    """Response model for refresh balance operation."""

    message: str = Field(..., description="Response message")
    idempotencyKey: str = Field(..., description="Idempotency key", alias="idempotencyKey")

    class Config:
        populate_by_name = True


class SourceDestination(BaseModel):
    """Source or destination model for transaction estimate."""

    type: str = Field(..., description="Type (e.g., 'VAULT_ACCOUNT')")
    id: str = Field(..., description="Account ID")


class EstimateFeeRequest(BaseModel):
    """Request model for estimating transaction fee."""

    operation: str = Field(..., description="Operation type (e.g., 'TRANSFER')")
    source: SourceDestination = Field(..., description="Source account")
    destination: SourceDestination = Field(..., description="Destination account")
    assetId: str = Field(..., description="Asset identifier", alias="assetId")
    amount: str = Field(..., description="Transaction amount")

    class Config:
        populate_by_name = True


class FeeEstimate(BaseModel):
    """Fee estimate model for a specific priority level."""

    networkFee: str = Field(..., description="Network fee", alias="networkFee")
    gasPrice: str = Field(..., description="Gas price", alias="gasPrice")
    gasLimit: str = Field(..., description="Gas limit", alias="gasLimit")
    baseFee: str = Field(..., description="Base fee", alias="baseFee")
    priorityFee: str = Field(..., description="Priority fee", alias="priorityFee")
    l1Fee: str = Field(..., description="L1 fee", alias="l1Fee")
    maxFeePerGasDelta: str = Field(..., description="Max fee per gas delta", alias="maxFeePerGasDelta")

    class Config:
        populate_by_name = True


class EstimateFeeResponse(BaseModel):
    """Response model for transaction fee estimate."""

    low: FeeEstimate = Field(..., description="Low priority fee estimate")
    medium: FeeEstimate = Field(..., description="Medium priority fee estimate")
    high: FeeEstimate = Field(..., description="High priority fee estimate")


class ExternalWalletAsset(BaseModel):
    """Response model for an external wallet asset."""

    id: str = Field(..., description="Asset identifier")
    balance: str = Field(..., description="Balance amount")
    lockedAmount: str = Field(..., description="Locked amount", alias="lockedAmount")
    status: str = Field(..., description="Asset status")
    address: str = Field(..., description="Wallet address")
    tag: str = Field(..., description="Tag or memo")
    activationTime: str = Field(..., description="Activation time", alias="activationTime")

    class Config:
        populate_by_name = True


class ExternalWallet(BaseModel):
    """Response model for an external wallet."""

    id: str = Field(..., description="Wallet ID")
    name: str = Field(..., description="Wallet name")
    customerRefId: str = Field(..., description="Customer reference ID", alias="customerRefId")
    assets: list[ExternalWalletAsset] = Field(..., description="List of assets")

    class Config:
        populate_by_name = True


class ExternalWalletsEmptyResponse(BaseModel):
    """Response model when no external wallets are found."""

    message: str = Field(..., description="Response message")
    code: int = Field(..., description="Response code")
    data: list = Field(..., description="Empty data list")

    class Config:
        populate_by_name = True


class VaultToVaultRequest(BaseModel):
    """Request model for vault-to-vault transaction."""

    network: str = Field(..., description="Network (e.g., 'polygon')")
    service: str = Field(..., description="Service type (e.g., 'BLOCKCHAIN_WITHDRAWAL')")
    token: str = Field(..., description="Token identifier (e.g., 'usdc')")
    sourceVaultId: str = Field(..., description="Source vault ID", alias="sourceVaultId")
    destinationWalletId: Optional[str] = Field(None, description="Destination wallet ID", alias="destinationWalletId")
    destinationVaultId: Optional[str] = Field(None, description="Destination vault ID", alias="destinationVaultId")
    feeLevel: str = Field(..., description="Fee level (e.g., 'HIGH', 'MEDIUM', 'LOW')", alias="feeLevel")
    amount: str = Field(..., description="Transaction amount")

    class Config:
        populate_by_name = True


class VaultToVaultResponse(BaseModel):
    """Response model for vault-to-vault transaction."""

    id: str = Field(..., description="Transaction ID")
    status: str = Field(..., description="Transaction status (e.g., 'SUBMITTED')")
