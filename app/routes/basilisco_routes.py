"""Basilisco routes for backoffice transactions."""

from datetime import datetime
import logging
from typing import List

from fastapi import APIRouter, Depends, Header, HTTPException, Query, status
from pydantic import BaseModel

from app.common.apis.basilisco.client import BasiliscoClient
from app.common.apis.basilisco.dtos import TransactionFilters
from app.common.apis.basilisco.errors import BasiliscoAPIClientError
from app.middleware.auth import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter()

# Query parameter defaults
DEFAULT_PAGE = 1
DEFAULT_LIMIT = 10
MIN_PAGE = 1
MIN_LIMIT = 1
MAX_LIMIT = 100


class CreateTransactionRequest(BaseModel):
    """Request model for creating a transaction."""

    created_at: str | None = None
    type: str | None = None
    provider: str | None = None
    fees: str | None = None
    amount: str | None = None
    currency: str | None = None
    rate: str | None = None
    st_id: str | None = None
    st_hash: str | None = None
    user_id: str | None = None
    user_id_to: str | None = None
    user_id_from: str | None = None
    category: str | None = None
    transfer_id: str | None = None
    actor_id: str | None = None
    source_id: str | None = None
    reason: str | None = None
    occurred_at: str | None = None
    method: str | None = None
    status: str | None = None
    origin_provider: str | None = None
    movement_type: str | None = None
    idempotency_key: str | None = None


def _get_transactions_data(
    filters: TransactionFilters,
    page: int,
    limit: int,
) -> dict:
    """Get transactions data from Basilisco client.

    Args:
        filters: Transaction filters (provider, exclude_provider, date_from, date_to)
        page: Page number
        limit: Number of results per page

    Returns:
        Transactions data dictionary

    Raises:
        BasiliscoAPIClientError: If API call fails
    """
    client = BasiliscoClient()
    filters_dict = filters.model_dump(exclude_none=True)
    response = client.get_transactions(filters=filters_dict, page=page, limit=limit)
    return response.model_dump()


def _create_transaction_data(
    transaction_data: dict,
    idempotency_key: str | None = None,
) -> dict:
    """Create transaction data using Basilisco client.

    Args:
        transaction_data: Transaction data dictionary
        idempotency_key: Optional idempotency key for the request

    Returns:
        Created transaction data dictionary

    Raises:
        BasiliscoAPIClientError: If API call fails
    """
    client = BasiliscoClient()
    response = client.create_transaction(
        transaction_data,
        idempotency_key=idempotency_key,
    )
    return response.model_dump()


@router.get("/backoffice/transactions")
def get_backoffice_transactions(  # noqa: WPS211
    provider: str | None = Query(  # noqa: WPS404
        None, description="Filter by provider (e.g., 'fireblocks')"
    ),
    exclude_provider: List[str] | None = Query(  # noqa: WPS404
        None, description="List of providers to exclude"
    ),
    date_from: datetime | None = Query(  # noqa: WPS404
        None, description="Start date for filtering transactions (ISO format)"
    ),
    date_to: datetime | None = Query(  # noqa: WPS404
        None, description="End date for filtering transactions (ISO format)"
    ),
    movement_type: str | None = Query(  # noqa: WPS404
        None, description="Filter by movement type (e.g., 'monetization', 'internal')"
    ),
    page: int = Query(DEFAULT_PAGE, ge=MIN_PAGE, description="Page number"),  # noqa: WPS404
    limit: int = Query(  # noqa: WPS404
        DEFAULT_LIMIT, ge=MIN_LIMIT, le=MAX_LIMIT, description="Number of results per page"
    ),
    current_user: dict = Depends(get_current_user)  # noqa: WPS404
):
    """Get backoffice transactions from Basilisco.

    This endpoint requires authentication and proxies requests to Basilisco API.

    Args:
        provider: Optional provider filter (e.g., 'fireblocks')
        exclude_provider: Optional list of providers to exclude
        date_from: Optional start date for filtering transactions (ISO format)
        date_to: Optional end date for filtering transactions (ISO format)
        movement_type: Optional movement type filter (e.g., 'monetization', 'internal')
        page: Page number (default: 1, minimum: 1)
        limit: Number of results per page (default: 10, minimum: 1, maximum: 100)
        current_user: Current authenticated user

    Returns:
        dict: Transactions and pagination information from Basilisco

    Raises:
        HTTPException: If API call fails or user is not authenticated
    """
    filters = TransactionFilters(
        provider=provider,
        exclude_provider=exclude_provider,
        date_from=date_from,
        date_to=date_to,
        movement_type=movement_type,
    )
    logger.info(
        (
            "Getting backoffice transactions - provider: %s, exclude_provider: %s, "
            "date_from: %s, date_to: %s, movement_type: %s, page: %s, limit: %s"
        ),
        provider,
        exclude_provider,
        date_from,
        date_to,
        movement_type,
        page,
        limit
    )
    try:
        transactions_data = _get_transactions_data(filters=filters, page=page, limit=limit)
    except BasiliscoAPIClientError as api_error:
        logger.error("Basilisco API error: %s", api_error)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Error retrieving transactions from Basilisco service"
        )
    except Exception as exc:
        logger.error("Error getting transactions from Basilisco: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Error retrieving transactions from Basilisco service"
        )
    return transactions_data


@router.post("/backoffice/transactions")
def create_backoffice_transaction(
    request: CreateTransactionRequest,
    idempotency_key: str | None = Header(  # noqa: WPS404
        None,
        alias="idempotency-key",
        description="Idempotency key for the request"
    ),
    current_user: dict = Depends(get_current_user)  # noqa: WPS404
):
    """Create a backoffice transaction in Basilisco.

    This endpoint requires authentication and proxies requests to Basilisco API.

    Args:
        request: Transaction data to create
        idempotency_key: Optional idempotency key header (idempotency-key)
        current_user: Current authenticated user

    Returns:
        dict: Created transaction information from Basilisco

    Raises:
        HTTPException: If API call fails or user is not authenticated
    """
    logger.info(
        "Creating backoffice transaction - type: %s, provider: %s, amount: %s",
        request.type,
        request.provider,
        request.amount
    )

    # Filter out None values to only send fields that were provided
    transaction_data = {
        field_name: field_value
        for field_name, field_value in request.model_dump().items()
        if field_value is not None and field_name != "idempotency_key"
    }

    # Use idempotency_key from header if provided, otherwise from body
    final_idempotency_key = idempotency_key or request.idempotency_key

    try:
        transaction_response = _create_transaction_data(
            transaction_data,
            idempotency_key=final_idempotency_key,
        )
    except BasiliscoAPIClientError as api_error:
        logger.error("Basilisco API error: %s", api_error, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Error creating transaction in Basilisco service: {str(api_error)}"
        )
    except Exception as exc:
        logger.error("Error creating transaction in Basilisco: %s", exc, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Error creating transaction in Basilisco service: {str(exc)}"
        )
    return transaction_response
