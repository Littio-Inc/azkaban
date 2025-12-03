"""Basilisco routes for backoffice transactions."""

import logging

from fastapi import APIRouter, Depends, HTTPException, Query, status

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


@router.get("/backoffice/transactions")
async def get_backoffice_transactions(
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
