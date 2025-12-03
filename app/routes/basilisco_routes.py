"""Basilisco routes for backoffice transactions."""

import logging

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.littio.basilisco.service import BasiliscoService
from app.middleware.admin import get_admin_user

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/backoffice/transactions")
async def get_backoffice_transactions(
    provider: str | None = Query(None, description="Filter by provider (e.g., 'fireblocks')"),
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(10, ge=1, le=100, description="Number of results per page"),
    admin_user: dict = Depends(get_admin_user)  # noqa: WPS404
):
    """Get backoffice transactions from Basilisco.

    This endpoint requires admin authentication and proxies requests to Basilisco API.

    Args:
        provider: Optional provider filter (e.g., 'fireblocks')
        page: Page number (default: 1, minimum: 1)
        limit: Number of results per page (default: 10, minimum: 1, maximum: 100)
        admin_user: Current authenticated admin user

    Returns:
        dict: Transactions and pagination information from Basilisco

    Raises:
        HTTPException: If API call fails or user is not admin
    """
    logger.info(
        "Getting backoffice transactions - provider: %s, page: %s, limit: %s",
        provider,
        page,
        limit
    )

    try:
        transactions_data = BasiliscoService.get_transactions(
            provider=provider,
            page=page,
            limit=limit
        )
        return transactions_data
    except ValueError as e:
        logger.error("Configuration error: %s", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Basilisco service configuration error"
        )
    except Exception as e:
        logger.error("Error getting transactions from Basilisco: %s", e)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Error retrieving transactions from Basilisco service"
        )
