"""Cassandra API client for monetization services."""

from app.common.apis.cassandra.agent import BASE_PAYOUTS_PATH, CassandraAgent
from app.common.apis.cassandra.dtos import (
    BalanceResponse,
    PayoutCreateRequest,
    PayoutHistoryResponse,
    PayoutResponse,
    QuoteResponse,
    RecipientResponse,
)

# Constants
PATH_SEPARATOR = "/"


class CassandraClient:
    """Client for interacting with Cassandra monetization API.

    This client provides high-level methods to interact with the Cassandra API,
    handling request/response parsing and error handling.
    """

    _agent: CassandraAgent

    def __init__(self) -> None:
        """Initialize Cassandra client with API agent."""
        self._agent = CassandraAgent()

    def get_quote(
        self,
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
            CassandraAPIClientError: If API call fails
        """
        req_path = f"{BASE_PAYOUTS_PATH}{PATH_SEPARATOR}{account}/quote"
        response_data = self._agent.get(
            req_path=req_path,
            query_params={
                "amount": amount,
                "base_currency": base_currency,
                "quote_currency": quote_currency,
                "provider": provider,
            },
        )
        return QuoteResponse(**response_data)

    def get_recipients(self, account: str, user_id: str, provider: str) -> list[RecipientResponse]:
        """Get recipients for an account.

        Args:
            account: Account type (e.g., 'transfer', 'pay')
            user_id: User ID to filter recipients
            provider: Provider name (kira, cobre, supra)

        Returns:
            List of RecipientResponse objects

        Raises:
            CassandraAPIClientError: If API call fails
        """
        req_path = f"{BASE_PAYOUTS_PATH}{PATH_SEPARATOR}{account}/recipient"
        response_data = self._agent.get(
            req_path=req_path,
            query_params={"user_id": user_id, "provider": provider},
        )
        return self._parse_recipients_response(response_data)

    def get_balance(self, account: str, wallet_id: str, provider: str = "kira") -> BalanceResponse:
        """Get balance for a wallet.

        Args:
            account: Account type (e.g., 'transfer', 'pay')
            wallet_id: Wallet ID
            provider: Provider name (kira, cobre, supra). Defaults to "kira"

        Returns:
            BalanceResponse containing balance information

        Raises:
            CassandraAPIClientError: If API call fails
        """
        req_path = f"{BASE_PAYOUTS_PATH}{PATH_SEPARATOR}{account}/wallets{PATH_SEPARATOR}{wallet_id}/balances"
        response_data = self._agent.get(
            req_path=req_path,
            query_params={"provider": provider},
        )
        return BalanceResponse(**response_data)

    def create_payout(self, account: str, payout_data: PayoutCreateRequest) -> PayoutResponse:
        """Create a payout.

        Args:
            account: Account type (e.g., 'transfer', 'pay')
            payout_data: Payout request data

        Returns:
            PayoutResponse containing payout information

        Raises:
            CassandraAPIClientError: If API call fails
        """
        req_path = f"{BASE_PAYOUTS_PATH}{PATH_SEPARATOR}{account}/payout"
        # Use model_dump(mode="json") to get a JSON-ready dict directly
        # This ensures Decimal is serialized correctly via json_encoders
        # Since quote is now QuoteResponse (Pydantic model), all Decimals are handled automatically
        payload = payout_data.model_dump(mode="json")
        response_data = self._agent.post(
            req_path=req_path,
            json=payload,
        )
        return PayoutResponse(**response_data)

    def get_payout_history(self, account: str) -> PayoutHistoryResponse:
        """Get payout history for an account.

        Args:
            account: Account type (e.g., 'transfer', 'pay')

        Returns:
            PayoutHistoryResponse containing payout history information

        Raises:
            CassandraAPIClientError: If API call fails
        """
        req_path = f"{BASE_PAYOUTS_PATH}{PATH_SEPARATOR}{account}/payout"
        response_data = self._agent.get(req_path=req_path)
        return PayoutHistoryResponse(**response_data)

    def _parse_recipients_response(self, response_data: dict | list) -> list[RecipientResponse]:
        """Parse recipients response from API.

        Args:
            response_data: Response data as dict or list

        Returns:
            List of RecipientResponse objects

        Raises:
            CassandraAPIClientError: If parsing fails
        """
        # Handle response format: {'recipients': [...], 'total': N}
        if isinstance(response_data, dict) and "recipients" in response_data:
            recipients_list = response_data["recipients"]
            return [RecipientResponse(**recipient) for recipient in recipients_list]
        # Handle direct list format
        if isinstance(response_data, list):
            return [RecipientResponse(**recipient) for recipient in response_data]
        # Handle single recipient object
        return [RecipientResponse(**response_data)]
