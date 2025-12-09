"""Basilisco API client for backoffice transactions."""

from datetime import datetime
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
        exclude_provider: list[str] | None = None,
        date_from: datetime | None = None,
        date_to: datetime | None = None,
        page: int = 1,
        limit: int = 10,
    ) -> TransactionsResponse:
        """Get transactions from Basilisco API.

        Args:
            provider: Transaction provider filter (e.g., 'fireblocks')
            exclude_provider: List of providers to exclude
            date_from: Start date for filtering transactions
            date_to: End date for filtering transactions
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
        if exclude_provider:
            query_params["exclude_provider"] = exclude_provider
        if date_from:
            # Convert datetime to ISO format string
            query_params["date_from"] = date_from.isoformat()
        if date_to:
            # Convert datetime to ISO format string
            query_params["date_to"] = date_to.isoformat()

        response_data = self._agent.get(
            req_path=BASE_TRANSACTIONS_PATH,
            query_params=query_params,
        )
        return TransactionsResponse(**response_data)

    def create_transaction(
        self,
        transaction_data: dict[str, Any],
        idempotency_key: str | None = None,
    ) -> CreateTransactionResponse:
        """Create a transaction in Basilisco API.

        Args:
            transaction_data: Dictionary containing transaction data
            idempotency_key: Optional idempotency key for the request.
                           If not provided, will try to extract from transaction_data

        Returns:
            CreateTransactionResponse containing the created transaction ID

        Raises:
            BasiliscoAPIClientError: If API call fails
        """
        # Extract idempotency_key from transaction_data if not provided
        if not idempotency_key and "idempotency_key" in transaction_data:
            idempotency_key = transaction_data.pop("idempotency_key")
        
        response_data = self._agent.post(
            req_path=BASE_TRANSACTIONS_PATH,
            json=transaction_data,
            idempotency_key=idempotency_key,
        )
        return CreateTransactionResponse(**response_data)
