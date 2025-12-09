"""Diagon API client for vault accounts."""

from app.common.apis.diagon.agent import BASE_ACCOUNTS_PATH, DiagonAgent
from app.common.apis.diagon.dtos import AccountResponse, RefreshBalanceResponse

# Constants
PATH_SEPARATOR = "/"


class DiagonClient:
    """Client for interacting with Diagon API.

    This client provides high-level methods to interact with the Diagon API,
    handling request/response parsing and error handling.
    """

    _agent: DiagonAgent

    def __init__(self) -> None:
        """Initialize Diagon client with API agent."""
        self._agent = DiagonAgent()

    def get_accounts(self) -> list[AccountResponse]:
        """Get accounts from Diagon API.

        Returns:
            List of AccountResponse objects containing account information and assets

        Raises:
            DiagonAPIClientError: If API call fails
        """
        response_data = self._agent.get(req_path=BASE_ACCOUNTS_PATH)
        # Handle both list and single object responses
        if isinstance(response_data, list):
            return [AccountResponse(**account) for account in response_data]
        # If single object, wrap in list
        return [AccountResponse(**response_data)]

    def refresh_balance(self, account_id: str, asset: str) -> RefreshBalanceResponse:
        """Refresh balance for a specific account and asset.

        Args:
            account_id: Account ID
            asset: Asset identifier

        Returns:
            RefreshBalanceResponse containing message and idempotency key

        Raises:
            DiagonAPIClientError: If API call fails
        """
        req_path = f"{BASE_ACCOUNTS_PATH}{PATH_SEPARATOR}{account_id}{PATH_SEPARATOR}{asset}/balance"
        response_data = self._agent.post(req_path=req_path)
        return RefreshBalanceResponse(**response_data)
