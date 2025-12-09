"""Basilisco API client for backoffice transactions."""

from typing import Any

from app.common.apis.basilisco.agent import BASE_TRANSACTIONS_PATH, BasiliscoAgent
from app.common.apis.basilisco.dtos import CreateTransactionResponse, TransactionsResponse

# Constants
PATH_SEPARATOR = "/"


class BasiliscoClient:
    """Client for interacting with Basilisco API.

    This client provides high-level methods to interact with the Basilisco API,
    handling request/response parsing and error handling.
    """

    _agent: BasiliscoAgent

    def __init__(self) -> None:
        """Initialize Basilisco client with API agent."""
        self._agent = BasiliscoAgent()

    def get_transactions(
        self,
        provider: str | None = None,
        page: int = 1,
        limit: int = 10,
    ) -> TransactionsResponse:
        """Get transactions from Basilisco API.

        Args:
            provider: Transaction provider filter (e.g., 'fireblocks')
            page: Page number (default: 1)
            limit: Number of results per page (default: 10)

        Returns:
            TransactionsResponse containing transactions and pagination info

        Raises:
            BasiliscoAPIClientError: If API call fails
        """
        query_params: dict[str, Any] = {
            "page": page,
            "limit": limit,
        }
        if provider:
            query_params["provider"] = provider

        response_data = self._agent.get(
            req_path=BASE_TRANSACTIONS_PATH,
            query_params=query_params,
        )
        return TransactionsResponse(**response_data)

    def create_transaction(self, transaction_data: dict[str, Any]) -> CreateTransactionResponse:
        """Create a transaction in Basilisco API.

        Args:
            transaction_data: Dictionary containing transaction data

        Returns:
            CreateTransactionResponse containing the created transaction ID

        Raises:
            BasiliscoAPIClientError: If API call fails
        """
        response_data = self._agent.post(
            req_path=BASE_TRANSACTIONS_PATH,
            json=transaction_data,
        )
        return CreateTransactionResponse(**response_data)
