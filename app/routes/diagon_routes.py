"""Diagon routes for vault accounts."""

import logging

from fastapi import APIRouter, Depends, HTTPException, status

from app.littio.diagon.service import DiagonService
from app.middleware.auth import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter()


def _get_accounts_data() -> list[dict]:
    """Get accounts data from Diagon service.

    Returns:
        List of accounts data dictionaries

    Raises:
        ValueError: If configuration error occurs
        Exception: If other error occurs
    """
    return DiagonService.get_accounts()


@router.get("/vault/accounts")
def get_vault_accounts(
    current_user: dict = Depends(get_current_user)  # noqa: WPS404
):
    """Get vault accounts from Diagon.

    This endpoint requires authentication and proxies requests to Diagon API.

    Args:
        current_user: Current authenticated user

    Returns:
        list: List of accounts with their assets from Diagon

    Raises:
        HTTPException: If API call fails or user is not authenticated
    """
    logger.info("Getting vault accounts from Diagon")

    try:
        accounts_data = _get_accounts_data()
    except ValueError as config_error:
        logger.error("Configuration error: %s", config_error)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Diagon service configuration error"
        )
    except Exception as exc:
        logger.error("Error getting accounts from Diagon: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Error retrieving accounts from Diagon service"
        )
    return accounts_data
