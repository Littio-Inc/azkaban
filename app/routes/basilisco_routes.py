"""Basilisco routes for backoffice transactions."""

import logging

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel

from app.littio.basilisco.service import BasiliscoService
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
    category: str | None = None
    transfer_id: str | None = None
    actor_id: str | None = None
    source_id: str | None = None
    reason: str | None = None
    occurred_at: str | None = None
    idempotency_key: str | None = None


def _get_transactions_data(provider: str | None, page: int, limit: int) -> dict:
    """Get transactions data from Basilisco service.

    Args:
        provider: Optional provider filter
        page: Page number
        limit: Number of results per page

    Returns:
        Transactions data dictionary

    Raises:
        ValueError: If configuration error occurs
        Exception: If other error occurs
    """
    return BasiliscoService.get_transactions(
        provider=provider,
        page=page,
        limit=limit
    )


def _create_transaction_data(transaction_data: dict) -> dict:
    """Create transaction data using Basilisco service.

    Args:
        transaction_data: Transaction data dictionary

    Returns:
        Created transaction data dictionary

    Raises:
        ValueError: If configuration error occurs
        Exception: If other error occurs
    """
    return BasiliscoService.create_transaction(transaction_data)


@router.get("/backoffice/transactions")
def get_backoffice_transactions(
    provider: str | None = Query(None, description="Filter by provider (e.g., 'fireblocks')"),  # noqa: WPS404
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
        page: Page number (default: 1, minimum: 1)
        limit: Number of results per page (default: 10, minimum: 1, maximum: 100)
        current_user: Current authenticated user

    Returns:
        dict: Transactions and pagination information from Basilisco

    Raises:
        HTTPException: If API call fails or user is not authenticated
    """
    logger.info(
        "Getting backoffice transactions - provider: %s, page: %s, limit: %s",
        provider,
        page,
        limit
    )

    try:
        transactions_data = _get_transactions_data(provider, page, limit)
    except ValueError as config_error:
        logger.error("Configuration error: %s", config_error)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Basilisco service configuration error"
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
    current_user: dict = Depends(get_current_user)  # noqa: WPS404
):
    """Create a backoffice transaction in Basilisco.

    This endpoint requires authentication and proxies requests to Basilisco API.

    Args:
        request: Transaction data to create
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
    request_dict = request.model_dump()
    transaction_data = {
        field_name: field_value
        for field_name, field_value in request_dict.items()
        if field_value is not None
    }

    try:
        transaction_response = _create_transaction_data(transaction_data)
    except ValueError as config_error:
        logger.error("Configuration error: %s", config_error)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Basilisco service configuration error"
        )
    except Exception as exc:
        logger.error("Error creating transaction in Basilisco: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Error creating transaction in Basilisco service"
        )
    return transaction_response
