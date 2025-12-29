"""DTOs for Cassandra API operations."""

from decimal import Decimal

from pydantic import BaseModel, Field


class QuoteResponse(BaseModel):
    """Response model for quote operations."""

    quote_id: str = Field(..., description="Unique identifier for the quote")
    base_currency: str = Field(..., description="Base currency code")
    quote_currency: str = Field(..., description="Quote currency code")
    base_amount: Decimal = Field(..., description="Base amount")
    quote_amount: Decimal = Field(..., description="Quote amount")
    rate: Decimal = Field(..., description="Exchange rate")
    balam_rate: Decimal = Field(..., description="Balam exchange rate")
    fixed_fee: Decimal = Field(..., description="Fixed fee amount")
    pct_fee: Decimal = Field(..., description="Percentage fee")
    status: str = Field(..., description="Quote status")
    expiration_ts: str = Field(..., description="Expiration timestamp")
    expiration_ts_utc: str = Field(..., description="Expiration timestamp UTC")
    network: str | None = Field(None, description="Blockchain network")
    network_fee: Decimal | None = Field(None, description="Network fee for blockchain transactions")
    spread: Decimal | None = Field(None, description="Spread in basis points")

    class Config:
        """Pydantic configuration."""

        json_encoders = {
            Decimal: str,
        }


class RecipientResponse(BaseModel):
    """Response model for recipient operations."""

    recipient_id: str = Field(..., description="Recipient's unique identifier")
    first_name: str | None = Field(None, description="Recipient's first name")
    middle_name: str | None = Field(None, description="Recipient's middle name")
    last_name: str | None = Field(None, description="Recipient's last name")
    company_name: str | None = Field(None, description="Recipient's company name")
    account_type: str = Field(..., description="Recipient's account type")
    created_ts: str | None = Field(None, description="Recipient's creation timestamp")
    phone: str | None = Field(None, description="Recipient's phone number")
    email: str | None = Field(None, description="Recipient's email address")
    address: str | None = Field(None, description="Recipient's address")

    class Config:
        """Pydantic RecipientResponse configuration."""

        json_encoders = {
            Decimal: str,
        }


class TokenBalance(BaseModel):
    """Model for individual token balance."""

    token: str = Field(..., description="Token symbol (USDC, USDT)")
    amount: str = Field(..., description="Balance amount as string with 6 decimal places")
    decimals: int = Field(..., description="Number of decimal places for the token")


class BalanceResponse(BaseModel):
    """Response model for wallet balances."""

    wallet_id: str = Field(..., alias="walletId", description="Wallet's unique identifier")
    network: str = Field(..., description="Blockchain network (solana, polygon, tron)")
    balances: list[TokenBalance] = Field(..., description="List of token balances")

    class Config:
        """Pydantic configuration."""

        populate_by_name = True


class PayoutCreateRequest(BaseModel):
    """Request model for creating a payout."""

    recipient_id: str = Field(..., description="UUID of the recipient for the payout")
    wallet_id: str = Field(..., description="UUID of the wallet for the payout")
    reference: str | None = Field(None, description="Custom reference for the payout")
    base_currency: str = Field(..., description="Base currency code according to ISO-4217")
    quote_currency: str = Field(..., description="Currency code to be quoted according to ISO-4217")
    amount: Decimal = Field(..., description="Amount to be quoted")
    quote_id: str = Field(..., description="UUID of the quote to use for the payout")
    quote: QuoteResponse = Field(..., description="Full quote object")
    token: str = Field(..., description="Token type to use for the payout (USDC or USDT)")
    provider: str = Field(..., description="Provider name (kira, cobre, supra)")
    user_id: str | None = Field(None, description="User ID from database (optional, will be set by Azkaban)")

    class Config:
        """Pydantic PayoutCreateRequest configuration."""

        json_encoders = {
            Decimal: str,
        }


class PayoutResponse(BaseModel):
    """Response model for payout operations."""

    payout_id: str = Field(..., description="Payout's unique identifier")
    user_id: str = Field(..., description="ID of the user")
    recipient_id: str = Field(..., description="ID of the recipient")
    quote_id: str = Field(..., description="ID of the quote used")
    reference: str | None = Field(None, description="External reference for the payout")
    from_amount: str = Field(..., description="Amount in from currency")
    from_currency: str = Field(..., description="From currency code")
    to_amount: str = Field(..., description="Amount in to currency")
    to_currency: str = Field(..., description="To currency code")
    txn_hash: str | None = Field(None, description="Transaction hash")
    status: str = Field(..., description="Payout status")
    extra_info: dict | None = Field(None, description="Additional information")
    created_at: str = Field(..., description="Payout creation timestamp")
    updated_at: str = Field(..., description="Payout last update timestamp")
    failure_reason: str | None = Field(None, description="Reason for payout failure")

    class Config:
        """Pydantic PayoutResponse configuration."""

        json_encoders = {
            Decimal: str,
        }


class PayoutHistoryItem(BaseModel):
    """Model for individual payout history item."""

    id: str = Field(..., description="Payout's unique identifier")
    created_at: str = Field(..., description="Payout creation timestamp")
    updated_at: str = Field(..., description="Payout last update timestamp")
    initial_currency: str = Field(..., description="Initial currency code")
    final_currency: str = Field(..., description="Final currency code")
    initial_amount: str = Field(..., description="Initial amount")
    final_amount: str = Field(..., description="Final amount")
    rate: str = Field(..., description="Exchange rate")
    status: str = Field(..., description="Payout status")
    user_id: str | None = Field(None, description="ID of the user")
    provider: int = Field(..., description="Provider identifier")
    provider_external_id: str | None = Field(None, description="External ID from provider")
    provider_response: dict | None = Field(None, description="Provider response data")
    provider_webhook: dict | None = Field(None, description="Provider webhook data")
    additional_data: dict | None = Field(None, description="Additional data")

    class Config:
        """Pydantic PayoutHistoryItem configuration."""

        json_encoders = {
            Decimal: str,
        }


class PayoutHistoryResponse(BaseModel):
    """Response model for payout history operations."""

    status: str = Field(..., description="Response status")
    message: str = Field(..., description="Response message")
    data: list[PayoutHistoryItem] = Field(..., description="List of payout history items")
    count: int | None = Field(None, description="Total count of payouts")

    class Config:
        """Pydantic PayoutHistoryResponse configuration."""

        json_encoders = {
            Decimal: str,
        }
