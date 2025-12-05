"""Cassandra API client for monetization services."""

from requests.exceptions import JSONDecodeError

from app.common.apis.cassandra.dtos import (
    BalanceResponse,
    PayoutCreateRequest,
    PayoutResponse,
    QuoteResponse,
    RecipientResponse,
)
from app.common.apis.cassandra.errors import CassandraAPIClientError
from app.common.apis.rest_api_agent import MakeRequestParams, RESTfulAPIAgent
from app.common.errors import MissingCredentialsError
from app.common.secrets import get_secret

# Constants
BASE_PAYOUTS_PATH = "/v2/payouts/account"
PATH_SEPARATOR = "/"
ERROR_DECODING_JSON = "Error decoding JSON response"


class CassandraClient:
    """Client for interacting with Cassandra monetization API."""

    _api_key: str
    _api_key_is_valid: bool
    _agent: RESTfulAPIAgent

    def __init__(self) -> None:
        """Initialize Cassandra client with API credentials."""
        host_url = get_secret("CASSANDRA_API_URL")
        if not host_url:
            raise MissingCredentialsError("Missing credentials for Cassandra API.")
        self._agent = RESTfulAPIAgent(
            client_class_name=self.__class__.__name__,
            host_url=host_url,
            max_retries=3,
        )
        self._api_key = get_secret("CASSANDRA_API_KEY")
        if not self._api_key:
            raise MissingCredentialsError("Missing credentials for Cassandra API.")
        self._api_key_is_valid = False

    def get_quote(
        self,
        account: str,
        amount: float,
        base_currency: str,
        quote_currency: str,
    ) -> QuoteResponse:
        """Get a quote for currency conversion.

        Args:
            account: Account type (e.g., 'transfer', 'pay')
            amount: Amount to convert
            base_currency: Source currency code
            quote_currency: Target currency code

        Returns:
            QuoteResponse containing quote information

        Raises:
            CassandraAPIClientError: If API call fails
        """
        self._authenticate()
        params = MakeRequestParams(
            method="GET",
            path=f"{BASE_PAYOUTS_PATH}{PATH_SEPARATOR}{account}/quote",
            query_params={
                "amount": amount,
                "base_currency": base_currency,
                "quote_currency": quote_currency,
            },
        )
        response = self._agent.make_request(params)
        return self._parse_quote_response(response)

    def get_recipients(self, account: str, user_id: str) -> list[RecipientResponse]:
        """Get recipients for an account.

        Args:
            account: Account type (e.g., 'transfer', 'pay')
            user_id: User ID to filter recipients

        Returns:
            List of RecipientResponse objects

        Raises:
            CassandraAPIClientError: If API call fails
        """
        self._authenticate()
        params = MakeRequestParams(
            method="GET",
            path=f"{BASE_PAYOUTS_PATH}{PATH_SEPARATOR}{account}/recipient",
            query_params={"user_id": user_id},
        )
        response = self._agent.make_request(params)
        return self._parse_recipients_response(response)

    def get_balance(self, account: str, wallet_id: str) -> BalanceResponse:
        """Get balance for a wallet.

        Args:
            account: Account type (e.g., 'transfer', 'pay')
            wallet_id: Wallet ID

        Returns:
            BalanceResponse containing balance information

        Raises:
            CassandraAPIClientError: If API call fails
        """
        self._authenticate()
        params = MakeRequestParams(
            method="GET",
            path=f"{BASE_PAYOUTS_PATH}{PATH_SEPARATOR}{account}/wallets/{wallet_id}/balances",
        )
        response = self._agent.make_request(params)
        return self._parse_balance_response(response)

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
        self._authenticate()
        params = MakeRequestParams(
            method="POST",
            path=f"{BASE_PAYOUTS_PATH}{PATH_SEPARATOR}{account}/payout",
            body=payout_data.model_dump(),
        )
        response = self._agent.make_request(params)
        return self._parse_payout_response(response)

    def _parse_quote_response(self, response) -> QuoteResponse:
        """Parse quote response from API.

        Args:
            response: HTTP response object

        Returns:
            QuoteResponse object

        Raises:
            CassandraAPIClientError: If parsing fails
        """
        response_data = self._get_json_from_response(response)
        return QuoteResponse(**response_data)

    def _parse_recipients_response(self, response) -> list[RecipientResponse]:
        """Parse recipients response from API.

        Args:
            response: HTTP response object

        Returns:
            List of RecipientResponse objects

        Raises:
            CassandraAPIClientError: If parsing fails
        """
        response_data = self._get_json_from_response(response)
        # Handle response format: {'recipients': [...], 'total': N}
        if isinstance(response_data, dict) and "recipients" in response_data:
            recipients_list = response_data["recipients"]
            return [RecipientResponse(**recipient) for recipient in recipients_list]
        # Handle direct list format
        if isinstance(response_data, list):
            return [RecipientResponse(**recipient) for recipient in response_data]
        # Handle single recipient object
        return [RecipientResponse(**response_data)]

    def _parse_balance_response(self, response) -> BalanceResponse:
        """Parse balance response from API.

        Args:
            response: HTTP response object

        Returns:
            BalanceResponse object

        Raises:
            CassandraAPIClientError: If parsing fails
        """
        response_data = self._get_json_from_response(response)
        return BalanceResponse(**response_data)

    def _parse_payout_response(self, response) -> PayoutResponse:
        """Parse payout response from API.

        Args:
            response: HTTP response object

        Returns:
            PayoutResponse object

        Raises:
            CassandraAPIClientError: If parsing fails
        """
        response_data = self._get_json_from_response(response)
        return PayoutResponse(**response_data)

    def _get_json_from_response(self, response) -> dict:
        """Extract JSON data from HTTP response.

        Args:
            response: HTTP response object

        Returns:
            Dictionary with response data

        Raises:
            CassandraAPIClientError: If parsing fails
        """
        try:
            return response.json()
        except (JSONDecodeError, ValueError, TypeError) as json_error:
            raise CassandraAPIClientError(ERROR_DECODING_JSON) from json_error

    def _authenticate(self) -> None:
        """Authenticate with Cassandra API using API key."""
        if self._api_key_is_valid:
            return
        # Use lowercase header name as expected by API Gateway authorizer
        self._agent.update_headers({"x-api-key": self._api_key})
        self._api_key_is_valid = True
