"""DTOs for Cassandra API operations."""

from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


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
    # Supra-specific fields
    supra_quote_id: str | None = Field(None, description="Supra quote ID (Supra provider only)")
    exchange_confirmation_token: str | None = Field(None, description="Exchange confirmation token for Supra")

    model_config = ConfigDict(
        extra="allow",  # Allow extra fields that are not defined in the model
        json_encoders={
            Decimal: str,
        },
    )


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


class RecipientListResponse(BaseModel):
    """Response model for recipient list operations (v1/recipients endpoint)."""

    id: str = Field(..., description="Recipient's unique identifier")
    user_id: str = Field(..., description="User ID associated with the recipient")
    type: str = Field(..., description="Recipient type (e.g., 'transfer')")
    first_name: str | None = Field(None, description="Recipient's first name")
    last_name: str | None = Field(None, description="Recipient's last name")
    company_name: str | None = Field(None, description="Recipient's company name")
    document_type: str | None = Field(None, description="Document type (e.g., 'NIT')")
    document_number: str | None = Field(None, description="Document number")
    bank_code: str | None = Field(None, description="Bank code")
    account_number: str | None = Field(None, description="Account number")
    account_type: str | None = Field(None, description="Account type (e.g., 'savings')")
    cobre_counterparty_id: str | None = Field(None, description="Cobre counterparty ID")
    provider: str = Field(..., description="Provider name (e.g., 'BBVA', 'ZULU', 'COBRE')")
    enabled: bool | None = Field(None, description="Whether the recipient is enabled")
    created_at: str = Field(..., description="Recipient creation timestamp")
    updated_at: str = Field(..., description="Recipient last update timestamp")

    class Config:
        """Pydantic RecipientListResponse configuration."""

        json_encoders = {
            Decimal: str,
        }


class RecipientCreateRequest(BaseModel):
    """Request model for creating a recipient."""

    user_id: str = Field(..., description="User ID associated with the recipient")
    type: str = Field(..., description="Recipient type (e.g., 'transfer')")
    first_name: str | None = Field(None, description="Recipient's first name")
    last_name: str | None = Field(None, description="Recipient's last name")
    company_name: str | None = Field(None, description="Recipient's company name")
    document_type: str = Field(..., description="Document type (e.g., 'CC')")
    document_number: str = Field(..., description="Document number")
    bank_code: str = Field(..., description="Bank code")
    account_number: str = Field(..., description="Account number")
    account_type: str = Field(..., description="Account type (e.g., 'checking')")
    provider: str = Field(..., description="Provider name (e.g., 'cobre')")
    enabled: bool = Field(..., description="Whether the recipient is enabled")


class RecipientUpdateRequest(BaseModel):
    """Request model for updating a recipient."""

    first_name: str | None = Field(None, description="Recipient's first name")
    last_name: str | None = Field(None, description="Recipient's last name")
    company_name: str | None = Field(None, description="Recipient's company name")
    document_type: str | None = Field(None, description="Document type (e.g., 'CC')")
    document_number: str | None = Field(None, description="Document number")
    bank_code: str | None = Field(None, description="Bank code")
    account_number: str | None = Field(None, description="Account number")
    account_type: str | None = Field(None, description="Account type (e.g., 'checking')")
    enabled: bool | None = Field(None, description="Whether the recipient is enabled")


class BlockchainWalletCreateRequest(BaseModel):
    """Request model for creating a blockchain wallet."""

    name: str = Field(..., description="Wallet name")
    provider: str = Field(..., description="Provider name (e.g., 'cobre')")
    wallet_id: str = Field(..., description="Wallet ID")
    provider_id: str | None = Field(None, description="Provider ID")
    network: str = Field(..., description="Blockchain network (e.g., 'ethereum')")
    enabled: bool = Field(..., description="Whether the wallet is enabled")
    category: str | None = Field(None, description="Wallet category")
    owner: str | None = Field(None, description="Wallet owner")


class BlockchainWalletUpdateRequest(BaseModel):
    """Request model for updating a blockchain wallet."""

    name: str | None = Field(None, description="Wallet name")
    enabled: bool | None = Field(None, description="Whether the wallet is enabled")
    category: str | None = Field(None, description="Wallet category")


class BlockchainWalletResponse(BaseModel):
    """Response model for blockchain wallet operations."""

    id: str = Field(..., description="Wallet's unique identifier")
    name: str = Field(..., description="Wallet name")
    provider: str = Field(..., description="Provider name (e.g., 'FIREBLOCKS', 'OPEN_TRADE')")
    wallet_id: str = Field(..., description="Wallet ID")
    provider_id: str | None = Field(None, description="Provider ID")
    network: str = Field(..., description="Blockchain network (e.g., 'POLYGON')")
    enabled: bool = Field(..., description="Whether the wallet is enabled")
    category: str | None = Field(None, description="Wallet category")
    owner: str | None = Field(None, description="Wallet owner")
    created_at: str = Field(..., description="Wallet creation timestamp")
    updated_at: str = Field(..., description="Wallet last update timestamp")

    class Config:
        """Pydantic BlockchainWalletResponse configuration."""

        json_encoders = {
            Decimal: str,
        }


class ExternalWalletCreateRequest(BaseModel):
    """Request model for creating an external wallet."""

    external_wallet_id: str = Field(..., description="External wallet ID")
    asset_id: str | None = Field(None, description="Asset ID associated with the wallet")
    asset_address: str | None = Field(None, description="Asset address associated with the wallet")
    asset_tag: str | None = Field(None, description="Asset tag associated with the wallet")
    name: str = Field(..., description="Wallet name")
    category: str = Field(..., description="Wallet category (e.g., 'VAULT', 'OTC')")
    supplier_prefunding: bool = Field(..., description="Whether supplier prefunding is enabled")
    b2c_funding: bool = Field(..., description="Whether B2C funding is enabled")
    enabled: bool = Field(..., description="Whether the wallet is enabled")


class ExternalWalletUpdateRequest(BaseModel):
    """Request model for updating an external wallet."""

    asset_id: str | None = Field(None, description="Asset ID associated with the wallet")
    asset_address: str | None = Field(None, description="Asset address associated with the wallet")
    asset_tag: str | None = Field(None, description="Asset tag associated with the wallet")
    name: str | None = Field(None, description="Wallet name")
    category: str | None = Field(None, description="Wallet category (e.g., 'VAULT', 'OTC')")
    supplier_prefunding: bool | None = Field(None, description="Whether supplier prefunding is enabled")
    b2c_funding: bool | None = Field(None, description="Whether B2C funding is enabled")
    enabled: bool | None = Field(None, description="Whether the wallet is enabled")


class ExternalWalletResponse(BaseModel):
    """Response model for external wallet operations."""

    id: str = Field(..., description="Wallet's unique identifier")
    external_wallet_id: str = Field(..., description="External wallet ID")
    asset_id: str | None = Field(None, description="Asset ID associated with the wallet")
    asset_address: str | None = Field(None, description="Asset address associated with the wallet")
    asset_tag: str | None = Field(None, description="Asset tag associated with the wallet")
    name: str = Field(..., description="Wallet name")
    category: str = Field(..., description="Wallet category (e.g., 'VAULT', 'OTC')")
    supplier_prefunding: bool = Field(..., description="Whether supplier prefunding is enabled")
    b2c_funding: bool = Field(..., description="Whether B2C funding is enabled")
    enabled: bool = Field(..., description="Whether the wallet is enabled")
    created_at: str = Field(..., description="Wallet creation timestamp")
    updated_at: str = Field(..., description="Wallet last update timestamp")


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

    recipient_id: str | None = Field(None, description="UUID of the recipient for the payout")
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
    exchange_only: bool = Field(False, description="If true, only perform exchange without recipient (for B2C)")

    class Config:
        """Pydantic PayoutCreateRequest configuration."""

        json_encoders = {
            Decimal: str,
        }


class PayoutResponse(BaseModel):
    """Response model for payout operations."""

    payout_id: str = Field(..., description="Payout's unique identifier")
    user_id: str = Field(..., description="ID of the user")
    recipient_id: str | None = Field(None, description="ID of the recipient (optional for exchange-only payouts)")
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
    final_amount: str | None = Field(None, description="Final amount (can be None for incomplete payouts)")
    rate: str | None = Field(None, description="Exchange rate (can be None for incomplete payouts)")
    status: str = Field(..., description="Payout status")
    user_id: str | None = Field(None, description="ID of the user")
    provider: int = Field(..., description="Provider identifier")
    provider_external_id: str | None = Field(None, description="External ID from provider")
    provider_response: dict | None = Field(None, description="Provider response data")
    provider_webhook: dict | None = Field(None, description="Provider webhook data")
    additional_data: dict | None = Field(None, description="Additional data")

    model_config = ConfigDict(
        json_encoders={
            Decimal: str,
        },
    )


class PayoutHistoryResponse(BaseModel):
    """Response model for payout history operations."""

    status: str = Field(..., description="Response status")
    message: str = Field(..., description="Response message")
    data: list[PayoutHistoryItem] = Field(..., description="List of payout history items")
    count: int | None = Field(None, description="Total count of payouts")

    model_config = ConfigDict(
        json_encoders={
            Decimal: str,
        },
    )


# OpenTrade DTOs
class CollateralSetCTO(BaseModel):
    """Model for collateral set CTO."""

    exchange_rate_automation: str = Field(
        ..., alias="exchangeRateAutomation", description="Exchange rate automation type"
    )
    timestamp: int = Field(..., description="Timestamp")
    collateral: list = Field(default_factory=list, description="List of collateral")
    pool_addr: str = Field(..., alias="poolAddr", description="Pool address")

    class Config:
        """Pydantic configuration."""

        populate_by_name = True


class VaultAccountCTO(BaseModel):
    """Model for vault account CTO."""

    yield_type: str = Field(..., alias="yieldType", description="Yield type")
    rollover_collateral: str = Field(..., alias="rolloverCollateral", description="Rollover collateral")
    automatic_rollover: bool = Field(..., alias="automaticRollover", description="Automatic rollover flag")
    early_withdrawal_processing_period: int = Field(
        ..., alias="earlyWithdrawalProcessingPeriod", description="Early withdrawal processing period"
    )
    maximum_transfer_amount: int = Field(..., alias="maximumTransferAmount", description="Maximum transfer amount")
    minimum_transfer_amount: int = Field(..., alias="minimumTransferAmount", description="Minimum transfer amount")
    contractual_currency: str = Field(..., alias="contractualCurrency", description="Contractual currency")
    liquidity_fee_rate: int = Field(..., alias="liquidityFeeRate", description="Liquidity fee rate")
    platform_fee_rate: int = Field(..., alias="platformFeeRate", description="Platform fee rate")
    advisory_fee_rate: int = Field(..., alias="advisoryFeeRate", description="Advisory fee rate")
    transfer_out_days: int = Field(..., alias="transferOutDays", description="Transfer out days")
    transfer_in_days: int = Field(..., alias="transferInDays", description="Transfer in days")
    benchmark_rate: str = Field(..., alias="benchmarkRate", description="Benchmark rate")
    collateral: list = Field(default_factory=list, description="List of collateral")
    collateral_set_cto: CollateralSetCTO = Field(..., alias="collateralSetCTO", description="Collateral set CTO")
    timestamp_offchain: int = Field(..., alias="timestampOffchain", description="Timestamp offchain")
    pool_addr_offchain: str = Field(..., alias="poolAddrOffchain", description="Pool address offchain")
    version: str = Field(..., description="Version")
    pool_type: int = Field(..., alias="poolType", description="Pool type")
    id: str = Field(..., description="ID")
    timestamp: int = Field(..., description="Timestamp")
    timestamp_date_string: str = Field(..., alias="timestampDateString", description="Timestamp date string")
    timestamp_string: str = Field(..., alias="timestampString", description="Timestamp string")
    day_number: int = Field(..., alias="dayNumber", description="Day number")
    time_of_day: int = Field(..., alias="timeOfDay", description="Time of day")
    block_number: int = Field(..., alias="blockNumber", description="Block number")
    vault_name: str = Field(..., alias="vaultName", description="Vault name")
    currency_label: str = Field(..., alias="currencyLabel", description="Currency label")
    liquidity_token_symbol: str = Field(..., alias="liquidityTokenSymbol", description="Liquidity token symbol")
    pool_addr: str = Field(..., alias="poolAddr", description="Pool address")
    account_addr: str = Field(..., alias="accountAddr", description="Account address")
    liquidity_asset_addr: str = Field(..., alias="liquidityAssetAddr", description="Liquidity asset address")
    token_balance: str = Field(..., alias="tokenBalance", description="Token balance")
    asset_balance: str = Field(..., alias="assetBalance", description="Asset balance")
    principal_earning_interest: str = Field(
        ..., alias="principalEarningInterest", description="Principal earning interest"
    )
    max_withdraw_request: str = Field(..., alias="maxWithdrawRequest", description="Max withdraw request")
    max_redeem_request: str = Field(..., alias="maxRedeemRequest", description="Max redeem request")
    requested_shares_of: str = Field(..., alias="requestedSharesOf", description="Requested shares of")
    requested_assets_of: str = Field(..., alias="requestedAssetsOf", description="Requested assets of")
    accepted_shares: str = Field(..., alias="acceptedShares", description="Accepted shares")
    accepted_assets: str = Field(..., alias="acceptedAssets", description="Accepted assets")
    assets_deposited: str = Field(..., alias="assetsDeposited", description="Assets deposited")
    assets_withdrawn: str = Field(..., alias="assetsWithdrawn", description="Assets withdrawn")
    current_asset_value: str = Field(..., alias="currentAssetValue", description="Current asset value")
    gain_loss: str = Field(..., alias="gainLoss", description="Gain loss")
    gain_loss_in_day: str = Field(..., alias="gainLossInDay", description="Gain loss in day")
    credits: str = Field(..., description="Credits")
    credits_in_day: str = Field(..., alias="creditsInDay", description="Credits in day")
    debits: str = Field(..., description="Debits")
    debits_in_day: str = Field(..., alias="debitsInDay", description="Debits in day")
    fees: str = Field(..., description="Fees")
    fees_in_day: str = Field(..., alias="feesInDay", description="Fees in day")
    interest_rate: str = Field(..., alias="interestRate", description="Interest rate")
    exchange_rate: str = Field(..., alias="exchangeRate", description="Exchange rate")
    indicative_interest_rate: str = Field(..., alias="indicativeInterestRate", description="Indicative interest rate")
    collateral_rate: str = Field(..., alias="collateralRate", description="Collateral rate")

    class Config:
        """Pydantic configuration."""

        populate_by_name = True


class VaultAccountResponse(BaseModel):
    """Response model for vault account operations."""

    vault_account_cto: VaultAccountCTO = Field(..., alias="vaultAccountCTO", description="Vault account CTO")
    vault_address: str = Field(..., alias="vaultAddress", description="Vault address")
    account_address: str = Field(..., alias="accountAddress", description="Account address")

    class Config:
        """Pydantic configuration."""

        populate_by_name = True


class VaultListItem(BaseModel):
    """Model for individual vault list item."""

    display_name: str = Field(..., alias="displayName", description="Display name")
    chain_id: int = Field(..., alias="chainId", description="Chain ID")
    contract_name: str = Field(..., alias="contractName", description="Contract name")
    pool_type: int = Field(..., alias="poolType", description="Pool type")
    chain_config_name: str = Field(..., alias="chainConfigName", description="Chain config name")
    creation_block: int = Field(..., alias="creationBlock", description="Creation block")
    creation_timestamp: int = Field(..., alias="creationTimestamp", description="Creation timestamp")
    symbol: str = Field(..., description="Symbol")
    name: str = Field(..., description="Name")
    liquidity_asset_addr: str = Field(..., alias="liquidityAssetAddr", description="Liquidity asset address")
    liquidity_token_symbol: str = Field(..., alias="liquidityTokenSymbol", description="Liquidity token symbol")
    currency_label: str = Field(..., alias="currencyLabel", description="Currency label")
    pool_addr: str = Field(..., alias="poolAddr", description="Pool address")

    class Config:
        """Pydantic configuration."""

        populate_by_name = True


class VaultsListResponse(BaseModel):
    """Response model for vaults list operations."""

    vault_list: list[VaultListItem] = Field(..., alias="vaultList", description="List of vaults")

    class Config:
        """Pydantic configuration."""

        populate_by_name = True


class VaultOverviewCTO(BaseModel):
    """Model for vault overview CTO."""

    yield_type: str = Field(..., alias="yieldType", description="Yield type")
    rollover_collateral: str = Field(..., alias="rolloverCollateral", description="Rollover collateral")
    automatic_rollover: bool = Field(..., alias="automaticRollover", description="Automatic rollover flag")
    early_withdrawal_processing_period: int = Field(
        ..., alias="earlyWithdrawalProcessingPeriod", description="Early withdrawal processing period"
    )
    maximum_transfer_amount: int = Field(..., alias="maximumTransferAmount", description="Maximum transfer amount")
    minimum_transfer_amount: int = Field(..., alias="minimumTransferAmount", description="Minimum transfer amount")
    contractual_currency: str = Field(..., alias="contractualCurrency", description="Contractual currency")
    liquidity_fee_rate: int = Field(..., alias="liquidityFeeRate", description="Liquidity fee rate")
    platform_fee_rate: int = Field(..., alias="platformFeeRate", description="Platform fee rate")
    advisory_fee_rate: int = Field(..., alias="advisoryFeeRate", description="Advisory fee rate")
    transfer_out_days: int = Field(..., alias="transferOutDays", description="Transfer out days")
    transfer_in_days: int = Field(..., alias="transferInDays", description="Transfer in days")
    benchmark_rate: str = Field(..., alias="benchmarkRate", description="Benchmark rate")
    collateral: list = Field(default_factory=list, description="List of collateral")
    collateral_set_cto: CollateralSetCTO = Field(..., alias="collateralSetCTO", description="Collateral set CTO")
    timestamp_offchain: int = Field(..., alias="timestampOffchain", description="Timestamp offchain")
    pool_addr_offchain: str = Field(..., alias="poolAddrOffchain", description="Pool address offchain")
    version: str = Field(..., description="Version")
    pool_type: int = Field(..., alias="poolType", description="Pool type")
    pool_addr: str = Field(..., alias="poolAddr", description="Pool address")
    id: str = Field(..., description="ID")
    chain_configuration_name: str = Field(..., alias="chainConfigurationName", description="Chain configuration name")
    creation_block: int = Field(..., alias="creationBlock", description="Creation block")
    creation_timestamp: int = Field(..., alias="creationTimestamp", description="Creation timestamp")
    liquidity_token_symbol: str = Field(..., alias="liquidityTokenSymbol", description="Liquidity token symbol")
    currency_label: str = Field(..., alias="currencyLabel", description="Currency label")
    pool_admin_addr: str = Field(..., alias="poolAdminAddr", description="Pool admin address")
    pool_controller_addr: str = Field(..., alias="poolControllerAddr", description="Pool controller address")
    exchange_rate_type: int = Field(..., alias="exchangeRateType", description="Exchange rate type")
    name: str = Field(..., description="Name")
    symbol: str = Field(..., description="Symbol")
    borrower_manager_addr: str = Field(..., alias="borrowerManagerAddr", description="Borrower manager address")
    borrower_wallet_addr: str = Field(..., alias="borrowerWalletAddr", description="Borrower wallet address")
    close_of_deposit_time: int = Field(..., alias="closeOfDepositTime", description="Close of deposit time")
    close_of_withdraw_time: int = Field(..., alias="closeOfWithdrawTime", description="Close of withdraw time")
    fee_collector_address: str = Field(..., alias="feeCollectorAddress", description="Fee collector address")
    liquidity_asset_addr: str = Field(..., alias="liquidityAssetAddr", description="Liquidity asset address")
    block_number: int = Field(..., alias="blockNumber", description="Block number")
    timestamp: int = Field(..., description="Timestamp")
    timestamp_date_string: str = Field(..., alias="timestampDateString", description="Timestamp date string")
    timestamp_string: str = Field(..., alias="timestampString", description="Timestamp string")
    time_of_day: int = Field(..., alias="timeOfDay", description="Time of day")
    day_number: int = Field(..., alias="dayNumber", description="Day number")
    chain_id: int = Field(..., alias="chainId", description="Chain ID")
    state: int = Field(..., description="State")
    total_assets_deposited: str = Field(..., alias="totalAssetsDeposited", description="Total assets deposited")
    total_assets_withdrawn: str = Field(..., alias="totalAssetsWithdrawn", description="Total assets withdrawn")
    interest_rate: str = Field(..., alias="interestRate", description="Interest rate")
    exchange_rate: str = Field(..., alias="exchangeRate", description="Exchange rate")
    exchange_rate_at_set_day: str = Field(..., alias="exchangeRateAtSetDay", description="Exchange rate at set day")
    exchange_rate_set_day: int = Field(..., alias="exchangeRateSetDay", description="Exchange rate set day")
    exchange_rate_change_rate: str = Field(..., alias="exchangeRateChangeRate", description="Exchange rate change rate")
    exchange_rate_compounding_rate: str = Field(
        ..., alias="exchangeRateCompoundingRate", description="Exchange rate compounding rate"
    )
    exchange_rate_at_maturity: str = Field(..., alias="exchangeRateAtMaturity", description="Exchange rate at maturity")
    exchange_rate_maturity_day: int = Field(
        ..., alias="exchangeRateMaturityDay", description="Exchange rate maturity day"
    )
    indicative_interest_rate: str = Field(..., alias="indicativeInterestRate", description="Indicative interest rate")
    collateral_rate: str = Field(..., alias="collateralRate", description="Collateral rate")
    total_interest_accrued: str = Field(..., alias="totalInterestAccrued", description="Total interest accrued")
    total_shares: str = Field(..., alias="totalShares", description="Total shares")
    total_assets: str = Field(..., alias="totalAssets", description="Total assets")
    total_outstanding_loan_principal: str = Field(
        ..., alias="totalOutstandingLoanPrincipal", description="Total outstanding loan principal"
    )

    class Config:
        """Pydantic configuration."""

        populate_by_name = True


class VaultOverviewResponse(BaseModel):
    """Response model for vault overview operations."""

    vault_overview_cto: VaultOverviewCTO = Field(..., alias="vaultOverviewCTO", description="Vault overview CTO")
    vault_address: str = Field(..., alias="vaultAddress", description="Vault address")

    class Config:
        """Pydantic configuration."""

        populate_by_name = True
