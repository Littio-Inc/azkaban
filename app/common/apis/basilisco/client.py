"""Basilisco API client for backoffice transactions."""

from typing import Any

from app.common.apis.basilisco.agent import BASE_TRANSACTIONS_PATH, BasiliscoAgent
from app.common.apis.basilisco.dtos import CreateTransactionResponse, TransactionsResponse

# Constants
PATH_SEPARATOR = "/"
FILTER_KEY_PROVIDER = "provider"
FILTER_KEY_EXCLUDE_PROVIDER = "exclude_provider"
FILTER_KEY_DATE_FROM = "date_from"
FILTER_KEY_DATE_TO = "date_to"


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
        filters: dict[str, Any] | None = None,
        page: int = 1,
        limit: int = 10,
    ) -> TransactionsResponse:
        """Get transactions from Basilisco API.

        Args:
            filters: Dictionary with optional filters: provider, exclude_provider,
                    date_from (datetime), date_to (datetime)
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
        if not filters:
            response_data = self._agent.get(
                req_path=BASE_TRANSACTIONS_PATH,
                query_params=query_params,
            )
            return TransactionsResponse(**response_data)

        self._add_filter_to_params(filters, FILTER_KEY_PROVIDER, query_params)
        self._add_filter_to_params(filters, FILTER_KEY_EXCLUDE_PROVIDER, query_params)
        self._add_date_filter_to_params(filters, FILTER_KEY_DATE_FROM, query_params)
        self._add_date_filter_to_params(filters, FILTER_KEY_DATE_TO, query_params)

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
                           as a fallback (for backward compatibility)

        Returns:
            CreateTransactionResponse containing the created transaction ID

        Raises:
            BasiliscoAPIClientError: If API call fails
        """
        # Extract idempotency_key from transaction_data if not provided (fallback)
        if not idempotency_key and "idempotency_key" in transaction_data:
            idempotency_key = transaction_data.pop("idempotency_key")

        response_data = self._agent.post(
            req_path=BASE_TRANSACTIONS_PATH,
            json=transaction_data,
            idempotency_key=idempotency_key,
        )
        return CreateTransactionResponse(**response_data)

    def _add_filter_to_params(
        self,
        filters: dict[str, Any],
        filter_key: str,
        query_params: dict[str, Any],
    ) -> None:
        """Add filter value to query params if present and truthy.

        Args:
            filters: Dictionary containing filters
            filter_key: Key to check in filters
            query_params: Query parameters dict to update
        """
        if filter_key in filters and filters[filter_key]:
            query_params[filter_key] = filters[filter_key]

    def _add_date_filter_to_params(
        self,
        filters: dict[str, Any],
        filter_key: str,
        query_params: dict[str, Any],
    ) -> None:
        """Add date filter value to query params if present and truthy.

        Args:
            filters: Dictionary containing filters
            filter_key: Key to check in filters
            query_params: Query parameters dict to update
        """
        if filter_key in filters and filters[filter_key]:
            query_params[filter_key] = filters[filter_key].isoformat()
