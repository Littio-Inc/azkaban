"""Diagon routes for vault accounts."""

import logging

from fastapi import APIRouter, Depends, HTTPException, status

from app.common.apis.diagon.client import DiagonClient
from app.common.apis.diagon.errors import DiagonAPIClientError
from app.middleware.auth import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter()


def _get_accounts_data() -> list[dict]:
    """Get accounts data from Diagon client.

    Returns:
        List of accounts data dictionaries

    Raises:
        DiagonAPIClientError: If API call fails
    """
    client = DiagonClient()
    accounts = client.get_accounts()
    return [account.model_dump() for account in accounts]


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
    except DiagonAPIClientError as api_error:
        logger.error("Diagon API error: %s", api_error)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Error retrieving accounts from Diagon service"
        )
    except Exception as exc:
        logger.error("Error getting accounts from Diagon: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Error retrieving accounts from Diagon service"
        )
    return accounts_data


def _refresh_balance_data(account_id: str, asset: str) -> dict:
    """Refresh balance data from Diagon client.

    Args:
        account_id: Account ID
        asset: Asset identifier

    Returns:
        Dictionary with refresh balance response

    Raises:
        DiagonAPIClientError: If API call fails
    """
    client = DiagonClient()
    response = client.refresh_balance(account_id, asset)
    return response.model_dump()


@router.post("/vault/accounts/{account_id}/{asset}/balance")
def refresh_balance(
    account_id: str,
    asset: str,
    current_user: dict = Depends(get_current_user)  # noqa: WPS404
):
    """Refresh balance for a specific account and asset from Diagon.

    This endpoint requires authentication and proxies requests to Diagon API.

    Args:
        account_id: Account ID
        asset: Asset identifier
        current_user: Current authenticated user

    Returns:
        dict: Response with message and idempotency key

    Raises:
        HTTPException: If API call fails or user is not authenticated
    """
    logger.info("Refreshing balance for account %s, asset %s from Diagon", account_id, asset)

    try:
        refresh_data = _refresh_balance_data(account_id, asset)
    except DiagonAPIClientError as api_error:
        logger.error("Diagon API error: %s", api_error)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Error refreshing balance from Diagon service"
        )
    except Exception as exc:
        logger.error("Error refreshing balance from Diagon: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Error refreshing balance from Diagon service"
        )
    return refresh_data
