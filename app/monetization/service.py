"""Monetization service for managing payout operations."""

import logging

from app.common.apis.cassandra.client import CassandraClient
from app.common.apis.cassandra.dtos import (
    BalanceResponse,
    BlockchainWalletCreateRequest,
    BlockchainWalletResponse,
    BlockchainWalletUpdateRequest,
    ExternalWalletCreateRequest,
    ExternalWalletResponse,
    ExternalWalletUpdateRequest,
    PayoutCreateRequest,
    PayoutHistoryResponse,
    PayoutResponse,
    QuoteResponse,
    RecipientCreateRequest,
    RecipientListResponse,
    RecipientResponse,
    RecipientUpdateRequest,
    VaultAccountResponse,
    VaultOverviewResponse,
    VaultsListResponse,
)
from app.common.apis.cassandra.errors import CassandraAPIClientError

logger = logging.getLogger(__name__)


def _get_client() -> CassandraClient:
    """Get a Cassandra client instance.

    Returns:
        CassandraClient instance

    Raises:
        MissingCredentialsError: If Cassandra API credentials are missing (raised by CassandraClient)
    """
    return CassandraClient()


def _call_get_quote(
    account: str,
    amount: float,
    base_currency: str,
    quote_currency: str,
    provider: str,
) -> QuoteResponse:
    """Call get_quote on client.

    Args:
        account: Account type
        amount: Amount to convert
        base_currency: Source currency code
        quote_currency: Target currency code
        provider: Provider name (kira, cobre, supra)

    Returns:
        QuoteResponse object
    """
    client = _get_client()
    return client.get_quote(account, amount, base_currency, quote_currency, provider)


def _call_get_recipients(account: str, user_id: str, provider: str) -> list[RecipientResponse]:
    """Call get_recipients on client.

    Args:
        account: Account type
        user_id: User ID to filter recipients
        provider: Provider name (kira, cobre, supra)

    Returns:
        List of RecipientResponse objects
    """
    client = _get_client()
    return client.get_recipients(account, user_id, provider)


def _call_get_balance(account: str, wallet_id: str, provider: str = "kira") -> BalanceResponse:
    """Call get_balance on client.

    Args:
        account: Account type
        wallet_id: Wallet ID
        provider: Provider name (kira, cobre, supra). Defaults to "kira"

    Returns:
        BalanceResponse object
    """
    client = _get_client()
    return client.get_balance(account, wallet_id, provider)


def _call_create_payout(account: str, payout_data: PayoutCreateRequest) -> PayoutResponse:
    """Call create_payout on client.

    Args:
        account: Account type
        payout_data: Payout request data

    Returns:
        PayoutResponse object
    """
    client = _get_client()
    return client.create_payout(account, payout_data)


def _call_get_payout_history(account: str) -> PayoutHistoryResponse:
    """Call get_payout_history on client.

    Args:
        account: Account type

    Returns:
        PayoutHistoryResponse containing payout history information
    """
    client = _get_client()
    return client.get_payout_history(account)


def _call_get_vault_account(vault_address: str, account_address: str) -> VaultAccountResponse:
    """Call get_vault_account on client.

    Args:
        vault_address: Vault address
        account_address: Account address

    Returns:
        VaultAccountResponse containing vault account information
    """
    client = _get_client()
    return client.get_vault_account(vault_address, account_address)


def _call_get_vaults_list() -> VaultsListResponse:
    """Call get_vaults_list on client.

    Returns:
        VaultsListResponse containing list of vaults
    """
    client = _get_client()
    return client.get_vaults_list()


def _call_get_vault_overview(vault_address: str) -> VaultOverviewResponse:
    """Call get_vault_overview on client.

    Args:
        vault_address: Vault address

    Returns:
        VaultOverviewResponse containing vault overview information
    """
    client = _get_client()
    return client.get_vault_overview(vault_address)


def _call_get_recipients_list(
    provider: str | None = None,
    exclude_provider: str | None = None,
) -> list[RecipientListResponse]:
    """Call get_recipients_list on client.

    Args:
        provider: Optional provider name to filter by
        exclude_provider: Optional provider name to exclude

    Returns:
        List of RecipientListResponse objects
    """
    client = _get_client()
    return client.get_recipients_list(provider=provider, exclude_provider=exclude_provider)


def _call_create_recipient(
    recipient_data: RecipientCreateRequest,
) -> RecipientListResponse:
    """Call create_recipient on client.

    Args:
        recipient_data: Recipient data to create

    Returns:
        RecipientListResponse object

    Raises:
        CassandraAPIClientError: If API call fails
    """
    client = _get_client()
    return client.create_recipient(recipient_data=recipient_data)


def _call_update_recipient(
    recipient_id: str,
    recipient_data: RecipientUpdateRequest,
) -> RecipientListResponse:
    """Call update_recipient on client.

    Args:
        recipient_id: Recipient ID to update
        recipient_data: Recipient data to update

    Returns:
        RecipientListResponse object

    Raises:
        CassandraAPIClientError: If API call fails
    """
    client = _get_client()
    return client.update_recipient(recipient_id=recipient_id, recipient_data=recipient_data)


def _call_delete_recipient(
    recipient_id: str,
) -> None:
    """Call delete_recipient on client.

    Args:
        recipient_id: Recipient ID to delete

    Raises:
        CassandraAPIClientError: If API call fails
    """
    client = _get_client()
    return client.delete_recipient(recipient_id=recipient_id)


def _call_get_blockchain_wallets(
    provider: str | None = None,
    exclude_provider: str | None = None,
) -> list[BlockchainWalletResponse]:
    """Call get_blockchain_wallets on client.

    Args:
        provider: Optional provider name to filter by
        exclude_provider: Optional provider name to exclude

    Returns:
        List of BlockchainWalletResponse objects
    """
    client = _get_client()
    return client.get_blockchain_wallets(provider=provider, exclude_provider=exclude_provider)


def _call_create_blockchain_wallet(
    wallet_data: BlockchainWalletCreateRequest,
) -> BlockchainWalletResponse:
    """Call create_blockchain_wallet on client.

    Args:
        wallet_data: Wallet data to create

    Returns:
        BlockchainWalletResponse object

    Raises:
        CassandraAPIClientError: If API call fails
    """
    client = _get_client()
    return client.create_blockchain_wallet(wallet_data=wallet_data)


def _call_update_blockchain_wallet(
    wallet_id: str,
    wallet_data: BlockchainWalletUpdateRequest,
) -> BlockchainWalletResponse:
    """Call update_blockchain_wallet on client.

    Args:
        wallet_id: Wallet ID to update
        wallet_data: Wallet data to update

    Returns:
        BlockchainWalletResponse object

    Raises:
        CassandraAPIClientError: If API call fails
    """
    client = _get_client()
    return client.update_blockchain_wallet(wallet_id=wallet_id, wallet_data=wallet_data)


def _call_delete_blockchain_wallet(
    wallet_id: str,
) -> None:
    """Call delete_blockchain_wallet on client.

    Args:
        wallet_id: Wallet ID to delete

    Raises:
        CassandraAPIClientError: If API call fails
    """
    client = _get_client()
    return client.delete_blockchain_wallet(wallet_id=wallet_id)


def _call_get_external_wallets() -> list[ExternalWalletResponse]:
    """Call get_external_wallets on client.

    Returns:
        List of ExternalWalletResponse objects
    """
    client = _get_client()
    return client.get_external_wallets()


def _call_create_external_wallet(
    wallet_data: ExternalWalletCreateRequest,
) -> ExternalWalletResponse:
    """Call create_external_wallet on client.

    Args:
        wallet_data: Wallet data to create

    Returns:
        ExternalWalletResponse object

    Raises:
        CassandraAPIClientError: If API call fails
    """
    client = _get_client()
    return client.create_external_wallet(wallet_data=wallet_data)


def _call_update_external_wallet(
    wallet_id: str,
    wallet_data: ExternalWalletUpdateRequest,
) -> ExternalWalletResponse:
    """Call update_external_wallet on client.

    Args:
        wallet_id: Wallet ID to update
        wallet_data: Wallet data to update

    Returns:
        ExternalWalletResponse object

    Raises:
        CassandraAPIClientError: If API call fails
    """
    client = _get_client()
    return client.update_external_wallet(wallet_id=wallet_id, wallet_data=wallet_data)


def _call_delete_external_wallet(
    wallet_id: str,
) -> None:
    """Call delete_external_wallet on client.

    Args:
        wallet_id: Wallet ID to delete

    Raises:
        CassandraAPIClientError: If API call fails
    """
    client = _get_client()
    return client.delete_external_wallet(wallet_id=wallet_id)


class MonetizationService:
    """Service for interacting with monetization operations via Cassandra API."""

    @staticmethod
    def get_quote(
        account: str,
        amount: float,
        base_currency: str,
        quote_currency: str,
        provider: str,
    ) -> QuoteResponse:
        """Get a quote for currency conversion.

        Args:
            account: Account type (e.g., 'transfer', 'pay')
            amount: Amount to convert
            base_currency: Source currency code
            quote_currency: Target currency code
            provider: Provider name (kira, cobre, supra)

        Returns:
            QuoteResponse containing quote information

        Raises:
            MissingCredentialsError: If Cassandra API credentials are missing (raised by CassandraClient)
            CassandraAPIClientError: If API call fails
        """
        try:
            return _call_get_quote(account, amount, base_currency, quote_currency, provider)
        except CassandraAPIClientError as api_error:
            logger.error(f"Cassandra API error getting quote: {api_error}")
            raise
        except Exception as exc:
            logger.error(f"Unexpected error getting quote: {exc}")
            raise

    @staticmethod
    def get_recipients(account: str, user_id: str, provider: str) -> list[RecipientResponse]:
        """Get recipients for an account.

        Args:
            account: Account type (e.g., 'transfer', 'pay')
            user_id: User ID to filter recipients
            provider: Provider name (kira, cobre, supra)

        Returns:
            List of RecipientResponse objects

        Raises:
            MissingCredentialsError: If Cassandra API credentials are missing (raised by CassandraClient)
            CassandraAPIClientError: If API call fails
        """
        try:
            return _call_get_recipients(account, user_id, provider)
        except CassandraAPIClientError as api_error:
            logger.error(f"Cassandra API error getting recipients: {api_error}")
            raise
        except Exception as exc:
            logger.error(f"Unexpected error getting recipients: {exc}")
            raise

    @staticmethod
    def get_balance(account: str, wallet_id: str, provider: str = "kira") -> BalanceResponse:
        """Get balance for a wallet.

        Args:
            account: Account type (e.g., 'transfer', 'pay')
            wallet_id: Wallet ID
            provider: Provider name (kira, cobre, supra). Defaults to "kira"

        Returns:
            BalanceResponse containing balance information

        Raises:
            MissingCredentialsError: If Cassandra API credentials are missing (raised by CassandraClient)
            CassandraAPIClientError: If API call fails
        """
        try:
            return _call_get_balance(account, wallet_id, provider)
        except CassandraAPIClientError as api_error:
            logger.error(f"Cassandra API error getting balance: {api_error}")
            raise
        except Exception as exc:
            logger.error(f"Unexpected error getting balance: {exc}")
            raise

    @staticmethod
    def create_payout(account: str, payout_data: PayoutCreateRequest) -> PayoutResponse:
        """Create a payout.

        Args:
            account: Account type (e.g., 'transfer', 'pay')
            payout_data: Payout request data

        Returns:
            PayoutResponse containing payout information

        Raises:
            MissingCredentialsError: If Cassandra API credentials are missing (raised by CassandraClient)
            CassandraAPIClientError: If API call fails
        """
        try:
            return _call_create_payout(account, payout_data)
        except CassandraAPIClientError as api_error:
            logger.error(f"Cassandra API error creating payout: {api_error}")
            raise
        except Exception as exc:
            logger.error(f"Unexpected error creating payout: {exc}")
            raise

    @staticmethod
    def get_payout_history(account: str) -> PayoutHistoryResponse:
        """Get payout history for an account.

        Args:
            account: Account type (e.g., 'transfer', 'pay')

        Returns:
            PayoutHistoryResponse containing payout history information

        Raises:
            MissingCredentialsError: If Cassandra API credentials are missing (raised by CassandraClient)
            CassandraAPIClientError: If API call fails
        """
        try:
            return _call_get_payout_history(account)
        except CassandraAPIClientError as api_error:
            logger.exception("Cassandra API error getting payout history: %s", api_error)
            raise
        except Exception as exc:
            logger.exception("Unexpected error getting payout history: %s", exc)
            raise

    @staticmethod
    def get_vault_account(vault_address: str, account_address: str) -> VaultAccountResponse:
        """Get vault account information.

        Args:
            vault_address: Vault address
            account_address: Account address

        Returns:
            VaultAccountResponse containing vault account information

        Raises:
            MissingCredentialsError: If Cassandra API credentials are missing (raised by CassandraClient)
            CassandraAPIClientError: If API call fails
        """
        try:
            return _call_get_vault_account(vault_address, account_address)
        except CassandraAPIClientError as api_error:
            logger.error(f"Cassandra API error getting vault account: {api_error}")
            raise
        except Exception as exc:
            logger.error(f"Unexpected error getting vault account: {exc}")
            raise

    @staticmethod
    def get_vaults_list() -> VaultsListResponse:
        """Get list of vaults.

        Returns:
            VaultsListResponse containing list of vaults

        Raises:
            MissingCredentialsError: If Cassandra API credentials are missing (raised by CassandraClient)
            CassandraAPIClientError: If API call fails
        """
        try:
            return _call_get_vaults_list()
        except CassandraAPIClientError as api_error:
            logger.error(f"Cassandra API error getting vaults list: {api_error}")
            raise
        except Exception as exc:
            logger.error(f"Unexpected error getting vaults list: {exc}")
            raise

    @staticmethod
    def get_vault_overview(vault_address: str) -> VaultOverviewResponse:
        """Get vault overview information.

        Args:
            vault_address: Vault address

        Returns:
            VaultOverviewResponse containing vault overview information

        Raises:
            MissingCredentialsError: If Cassandra API credentials are missing (raised by CassandraClient)
            CassandraAPIClientError: If API call fails
        """
        try:
            return _call_get_vault_overview(vault_address)
        except CassandraAPIClientError as api_error:
            logger.error(f"Cassandra API error getting vault overview: {api_error}")
            raise
        except Exception as exc:
            logger.error(f"Unexpected error getting vault overview: {exc}")
            raise

    @staticmethod
    def get_recipients_list(
        provider: str | None = None,
        exclude_provider: str | None = None,
    ) -> list[RecipientListResponse]:
        """Get recipients list from v1/recipients endpoint.

        Args:
            provider: Optional provider name to filter by
            exclude_provider: Optional provider name to exclude

        Returns:
            List of RecipientListResponse objects

        Raises:
            MissingCredentialsError: If Cassandra API credentials are missing (raised by CassandraClient)
            CassandraAPIClientError: If API call fails
        """
        try:
            return _call_get_recipients_list(provider=provider, exclude_provider=exclude_provider)
        except CassandraAPIClientError as api_error:
            logger.error(f"Cassandra API error getting recipients list: {api_error}")
            raise
        except Exception as exc:
            logger.error(f"Unexpected error getting recipients list: {exc}")
            raise

    @staticmethod
    def create_recipient(
        recipient_data: RecipientCreateRequest,
    ) -> RecipientListResponse:
        """Create a recipient.

        Args:
            recipient_data: Recipient data to create

        Returns:
            RecipientListResponse object

        Raises:
            MissingCredentialsError: If Cassandra API credentials are missing (raised by CassandraClient)
            CassandraAPIClientError: If API call fails
        """
        try:
            return _call_create_recipient(recipient_data=recipient_data)
        except CassandraAPIClientError as api_error:
            logger.error(f"Cassandra API error creating recipient: {api_error}")
            raise
        except Exception as exc:
            logger.error(f"Unexpected error creating recipient: {exc}")
            raise

    @staticmethod
    def update_recipient(
        recipient_id: str,
        recipient_data: RecipientUpdateRequest,
    ) -> RecipientListResponse:
        """Update a recipient.

        Args:
            recipient_id: Recipient ID to update
            recipient_data: Recipient data to update

        Returns:
            RecipientListResponse object

        Raises:
            MissingCredentialsError: If Cassandra API credentials are missing (raised by CassandraClient)
            CassandraAPIClientError: If API call fails
        """
        try:
            return _call_update_recipient(recipient_id=recipient_id, recipient_data=recipient_data)
        except CassandraAPIClientError as api_error:
            logger.error(f"Cassandra API error updating recipient: {api_error}")
            raise
        except Exception as exc:
            logger.error(f"Unexpected error updating recipient: {exc}")
            raise

    @staticmethod
    def delete_recipient(
        recipient_id: str,
    ) -> None:
        """Delete a recipient.

        Args:
            recipient_id: Recipient ID to delete

        Raises:
            MissingCredentialsError: If Cassandra API credentials are missing (raised by CassandraClient)
            CassandraAPIClientError: If API call fails
        """
        try:
            return _call_delete_recipient(recipient_id=recipient_id)
        except CassandraAPIClientError as api_error:
            logger.error(f"Cassandra API error deleting recipient: {api_error}")
            raise
        except Exception as exc:
            logger.error(f"Unexpected error deleting recipient: {exc}")
            raise

    @staticmethod
    def get_blockchain_wallets(
        provider: str | None = None,
        exclude_provider: str | None = None,
    ) -> list[BlockchainWalletResponse]:
        """Get blockchain wallets from v1/blockchain-wallets endpoint.

        Args:
            provider: Optional provider name to filter by
            exclude_provider: Optional provider name to exclude

        Returns:
            List of BlockchainWalletResponse objects

        Raises:
            MissingCredentialsError: If Cassandra API credentials are missing (raised by CassandraClient)
            CassandraAPIClientError: If API call fails
        """
        try:
            return _call_get_blockchain_wallets(provider=provider, exclude_provider=exclude_provider)
        except CassandraAPIClientError as api_error:
            logger.error(f"Cassandra API error getting blockchain wallets: {api_error}")
            raise
        except Exception as exc:
            logger.error(f"Unexpected error getting blockchain wallets: {exc}")
            raise

    @staticmethod
    def create_blockchain_wallet(
        wallet_data: BlockchainWalletCreateRequest,
    ) -> BlockchainWalletResponse:
        """Create a blockchain wallet.

        Args:
            wallet_data: Wallet data to create

        Returns:
            BlockchainWalletResponse object

        Raises:
            MissingCredentialsError: If Cassandra API credentials are missing (raised by CassandraClient)
            CassandraAPIClientError: If API call fails
        """
        try:
            return _call_create_blockchain_wallet(wallet_data=wallet_data)
        except CassandraAPIClientError as api_error:
            logger.error(f"Cassandra API error creating blockchain wallet: {api_error}")
            raise
        except Exception as exc:
            logger.error(f"Unexpected error creating blockchain wallet: {exc}")
            raise

    @staticmethod
    def update_blockchain_wallet(
        wallet_id: str,
        wallet_data: BlockchainWalletUpdateRequest,
    ) -> BlockchainWalletResponse:
        """Update a blockchain wallet.

        Args:
            wallet_id: Wallet ID to update
            wallet_data: Wallet data to update

        Returns:
            BlockchainWalletResponse object

        Raises:
            MissingCredentialsError: If Cassandra API credentials are missing (raised by CassandraClient)
            CassandraAPIClientError: If API call fails
        """
        try:
            return _call_update_blockchain_wallet(wallet_id=wallet_id, wallet_data=wallet_data)
        except CassandraAPIClientError as api_error:
            logger.error(f"Cassandra API error updating blockchain wallet: {api_error}")
            raise
        except Exception as exc:
            logger.error(f"Unexpected error updating blockchain wallet: {exc}")
            raise

    @staticmethod
    def delete_blockchain_wallet(
        wallet_id: str,
    ) -> None:
        """Delete a blockchain wallet.

        Args:
            wallet_id: Wallet ID to delete

        Raises:
            MissingCredentialsError: If Cassandra API credentials are missing (raised by CassandraClient)
            CassandraAPIClientError: If API call fails
        """
        try:
            return _call_delete_blockchain_wallet(wallet_id=wallet_id)
        except CassandraAPIClientError as api_error:
            logger.error(f"Cassandra API error deleting blockchain wallet: {api_error}")
            raise
        except Exception as exc:
            logger.error(f"Unexpected error deleting blockchain wallet: {exc}")
            raise

    @staticmethod
    def get_external_wallets() -> list[ExternalWalletResponse]:
        """Get external wallets from v1/external-wallets endpoint.

        Returns:
            List of ExternalWalletResponse objects

        Raises:
            MissingCredentialsError: If Cassandra API credentials are missing (raised by CassandraClient)
            CassandraAPIClientError: If API call fails
        """
        try:
            return _call_get_external_wallets()
        except CassandraAPIClientError as api_error:
            logger.error(f"Cassandra API error getting external wallets: {api_error}")
            raise
        except Exception as exc:
            logger.error(f"Unexpected error getting external wallets: {exc}")
            raise

    @staticmethod
    def create_external_wallet(
        wallet_data: ExternalWalletCreateRequest,
    ) -> ExternalWalletResponse:
        """Create an external wallet.

        Args:
            wallet_data: Wallet data to create

        Returns:
            ExternalWalletResponse object

        Raises:
            MissingCredentialsError: If Cassandra API credentials are missing (raised by CassandraClient)
            CassandraAPIClientError: If API call fails
        """
        try:
            return _call_create_external_wallet(wallet_data=wallet_data)
        except CassandraAPIClientError as api_error:
            logger.error(f"Cassandra API error creating external wallet: {api_error}")
            raise
        except Exception as exc:
            logger.error(f"Unexpected error creating external wallet: {exc}")
            raise

    @staticmethod
    def update_external_wallet(
        wallet_id: str,
        wallet_data: ExternalWalletUpdateRequest,
    ) -> ExternalWalletResponse:
        """Update an external wallet.

        Args:
            wallet_id: Wallet ID to update
            wallet_data: Wallet data to update

        Returns:
            ExternalWalletResponse object

        Raises:
            MissingCredentialsError: If Cassandra API credentials are missing (raised by CassandraClient)
            CassandraAPIClientError: If API call fails
        """
        try:
            return _call_update_external_wallet(wallet_id=wallet_id, wallet_data=wallet_data)
        except CassandraAPIClientError as api_error:
            logger.error(f"Cassandra API error updating external wallet: {api_error}")
            raise
        except Exception as exc:
            logger.error(f"Unexpected error updating external wallet: {exc}")
            raise

    @staticmethod
    def delete_external_wallet(
        wallet_id: str,
    ) -> None:
        """Delete an external wallet.

        Args:
            wallet_id: Wallet ID to delete

        Raises:
            MissingCredentialsError: If Cassandra API credentials are missing (raised by CassandraClient)
            CassandraAPIClientError: If API call fails
        """
        try:
            return _call_delete_external_wallet(wallet_id=wallet_id)
        except CassandraAPIClientError as api_error:
            logger.error(f"Cassandra API error deleting external wallet: {api_error}")
            raise
        except Exception as exc:
            logger.error(f"Unexpected error deleting external wallet: {exc}")
            raise
