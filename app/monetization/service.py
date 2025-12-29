"""Monetization service for managing payout operations."""

import logging

from app.common.apis.cassandra.client import CassandraClient
from app.common.apis.cassandra.dtos import (
    BalanceResponse,
    PayoutCreateRequest,
    PayoutHistoryResponse,
    PayoutResponse,
    QuoteResponse,
    RecipientResponse,
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
