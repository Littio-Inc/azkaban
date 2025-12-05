"""Monetization routes for payout operations."""

import logging

from fastapi import APIRouter, Body, Depends, HTTPException, Query, status

from app.common.apis.cassandra.dtos import PayoutCreateRequest
from app.middleware.auth import get_current_user
from app.monetization.service import MonetizationService

logger = logging.getLogger(__name__)

router = APIRouter()

# Constants
CONFIG_ERROR_MSG = "Configuration error: %s"
CONFIG_ERROR_DETAIL = "Monetization service configuration error"


def _get_quote_data(
    account: str,
    amount: float,
    base_currency: str,
    quote_currency: str,
):
    """Get quote data from monetization service.

    Args:
        account: Account type
        amount: Amount to convert
        base_currency: Source currency code
        quote_currency: Target currency code

    Returns:
        QuoteResponse object

    Raises:
        ValueError: If configuration error occurs
        Exception: If other error occurs
    """
    return MonetizationService.get_quote(account, amount, base_currency, quote_currency)


@router.get("/payouts/account/{account}/quote")
def get_quote(
    account: str,
    amount: float = Query(..., description="Amount to convert"),  # noqa: WPS404
    base_currency: str = Query(..., description="Source currency code"),  # noqa: WPS404
    quote_currency: str = Query(..., description="Target currency code"),  # noqa: WPS404
    current_user: dict = Depends(get_current_user),  # noqa: WPS404
):
    """Get a quote for currency conversion.

    This endpoint requires authentication and proxies requests to Cassandra API.

    Args:
        account: Account type (e.g., 'transfer', 'pay')
        amount: Amount to convert
        base_currency: Source currency code
        quote_currency: Target currency code
        current_user: Current authenticated user

    Returns:
        dict: Quote information from Cassandra (as dict for JSON response)

    Raises:
        HTTPException: If API call fails or user is not authenticated
    """
    logger.info(
        "Getting quote - account: %s, amount: %s, base_currency: %s, quote_currency: %s",
        account,
        amount,
        base_currency,
        quote_currency,
    )

    try:
        quote_data = _get_quote_data(account, amount, base_currency, quote_currency)
    except ValueError as config_error:
        logger.error(CONFIG_ERROR_MSG, config_error)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=CONFIG_ERROR_DETAIL,
        )
    except Exception as exc:
        logger.error("Error getting quote from monetization service: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Error retrieving quote from monetization service",
        )
    return quote_data.model_dump()


@router.get("/payouts/account/{account}/recipient")
def get_recipients(
    account: str,
    user_id: str = Query(..., description="User ID to filter recipients"),  # noqa: WPS404
    current_user: dict = Depends(get_current_user),  # noqa: WPS404
):
    """Get recipients for an account.

    This endpoint requires authentication and proxies requests to Cassandra API.

    Args:
        account: Account type (e.g., 'transfer', 'pay')
        user_id: User ID to filter recipients
        current_user: Current authenticated user

    Returns:
        list: List of recipients from Cassandra (as list of dicts for JSON response)

    Raises:
        HTTPException: If API call fails or user is not authenticated
    """
    logger.info("Getting recipients - account: %s, user_id: %s", account, user_id)

    try:
        recipients_data = MonetizationService.get_recipients(account, user_id)
    except ValueError as config_error:
        logger.error(CONFIG_ERROR_MSG, config_error)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=CONFIG_ERROR_DETAIL,
        )
    except Exception as exc:
        logger.error("Error getting recipients from monetization service: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Error retrieving recipients from monetization service",
        )
    recipients_list = [recipient.model_dump() for recipient in recipients_data]
    return {"recipients": recipients_list, "total": len(recipients_list)}


@router.get("/payouts/account/{account}/wallets/{wallet_id}/balances")
def get_balance(
    account: str,
    wallet_id: str,
    current_user: dict = Depends(get_current_user),  # noqa: WPS404
):
    """Get balance for a wallet.

    This endpoint requires authentication and proxies requests to Cassandra API.

    Args:
        account: Account type (e.g., 'transfer', 'pay')
        wallet_id: Wallet ID
        current_user: Current authenticated user

    Returns:
        dict: Balance information from Cassandra (as dict for JSON response)

    Raises:
        HTTPException: If API call fails or user is not authenticated
    """
    logger.info("Getting balance - account: %s, wallet_id: %s", account, wallet_id)

    try:
        balance_data = MonetizationService.get_balance(account, wallet_id)
    except ValueError as config_error:
        logger.error(CONFIG_ERROR_MSG, config_error)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=CONFIG_ERROR_DETAIL,
        )
    except Exception as exc:
        logger.error("Error getting balance from monetization service: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Error retrieving balance from monetization service",
        )
    return balance_data.model_dump()


@router.post("/payouts/account/{account}/payout")
def create_payout(
    account: str,
    payout_data: PayoutCreateRequest = Body(...),  # noqa: WPS404
    current_user: dict = Depends(get_current_user),  # noqa: WPS404
):
    """Create a payout.

    This endpoint requires authentication and proxies requests to Cassandra API.

    Args:
        account: Account type (e.g., 'transfer', 'pay')
        payout_data: Payout request data
        current_user: Current authenticated user

    Returns:
        dict: Payout response from Cassandra (as dict for JSON response)

    Raises:
        HTTPException: If API call fails or user is not authenticated
    """
    logger.info("Creating payout - account: %s", account)

    try:
        payout_response = MonetizationService.create_payout(account, payout_data)
    except ValueError as config_error:
        logger.error(CONFIG_ERROR_MSG, config_error)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=CONFIG_ERROR_DETAIL,
        )
    except Exception as exc:
        logger.error("Error creating payout in monetization service: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Error creating payout in monetization service",
        )
    return payout_response.model_dump()
