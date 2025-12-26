"""DTOs for Basilisco API operations."""

from datetime import datetime
from typing import List

from pydantic import BaseModel, Field


class TransactionResponse(BaseModel):
    """Response model for a single transaction."""

    id: str = Field(..., description="Transaction ID")
    transaction_id: str | None = Field(None, description="External transaction ID")
    created_at: str | None = Field(None, description="Creation timestamp")
    type: str | None = Field(None, description="Transaction type")
    provider: str | None = Field(None, description="Transaction provider")
    fees: str | None = Field(None, description="Transaction fees")
    amount: str | None = Field(None, description="Transaction amount")
    currency: str | None = Field(None, description="Currency code")
    rate: str | None = Field(None, description="Exchange rate")
    st_id: str | None = Field(None, description="Stable transaction ID")
    st_hash: str | None = Field(None, description="Stable transaction hash")
    user_id: str | None = Field(None, description="User ID")
    category: str | None = Field(None, description="Transaction category")
    transfer_id: str | None = Field(None, description="Transfer ID")
    actor_id: str | None = Field(None, description="Actor ID")
    source_id: str | None = Field(None, description="Source ID")
    reason: str | None = Field(None, description="Transaction reason")
    occurred_at: str | None = Field(None, description="Occurrence timestamp")
    idempotency_key: str | None = Field(None, description="Idempotency key")
    method: str | None = Field(None, description="Transaction method (e.g., 'BLOCKCHAIN')")
    status: str | None = Field(None, description="Transaction status (e.g., 'COMPLETED')")
    origin_provider: str | None = Field(None, description="Origin provider (e.g., 'bridge')")
    movement_type: str | None = Field(None, description="Movement type", alias="movementType")

    class Config:
        populate_by_name = True


class TransactionsResponse(BaseModel):
    """Response model for transactions list with pagination."""

    transactions: list[TransactionResponse] = Field(..., description="List of transactions")
    count: int = Field(..., description="Number of transactions in current page")
    total_count: int | None = Field(None, description="Total number of transactions")
    page: int = Field(..., description="Current page number")
    limit: int = Field(..., description="Number of results per page")


class CreateTransactionResponse(BaseModel):
    """Response model for creating a transaction."""

    id: str = Field(..., description="Created transaction ID")


class TransactionFilters(BaseModel):
    """Filters for querying transactions."""

    provider: str | None = Field(None, description="Filter by provider (e.g., 'fireblocks')")
    exclude_provider: List[str] | None = Field(None, description="List of providers to exclude")
    date_from: datetime | None = Field(None, description="Start date for filtering transactions (ISO format)")
    date_to: datetime | None = Field(None, description="End date for filtering transactions (ISO format)")
