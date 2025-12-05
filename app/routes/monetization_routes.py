"""Monetization routes for payout operations."""

import logging

from fastapi import APIRouter, Body, Depends, HTTPException, Query, status

from app.common.apis.cassandra.dtos import (
    BalanceResponse,
    PayoutCreateRequest,
    PayoutResponse,
    QuoteResponse,
    RecipientResponse,
)
from app.common.errors import MissingCredentialsError
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
) -> QuoteResponse:
    """Get quote data from monetization service.

    Args:
        account: Account type
        amount: Amount to convert
        base_currency: Source currency code
        quote_currency: Target currency code

    Returns:
        QuoteResponse object

    Raises:
        MissingCredentialsError: If Cassandra API credentials are missing
        CassandraAPIClientError: If API call fails
    """
    return MonetizationService.get_quote(account, amount, base_currency, quote_currency)


def _get_recipients_data(
    account: str,
    user_id: str,
) -> list[RecipientResponse]:
    """Get recipients data from monetization service.

    Args:
        account: Account type
        user_id: User ID to filter recipients

    Returns:
        List of RecipientResponse objects

    Raises:
        MissingCredentialsError: If Cassandra API credentials are missing
        CassandraAPIClientError: If API call fails
    """
    return MonetizationService.get_recipients(account, user_id)


def _get_balance_data(
    account: str,
    wallet_id: str,
) -> BalanceResponse:
    """Get balance data from monetization service.

    Args:
        account: Account type
        wallet_id: Wallet ID

    Returns:
        BalanceResponse object

    Raises:
        MissingCredentialsError: If Cassandra API credentials are missing
        CassandraAPIClientError: If API call fails
    """
    return MonetizationService.get_balance(account, wallet_id)


def _create_payout_data(
    account: str,
    payout_data: PayoutCreateRequest,
) -> PayoutResponse:
    """Create payout data from monetization service.

    Args:
        account: Account type
        payout_data: Payout request data

    Returns:
        PayoutResponse object

    Raises:
        MissingCredentialsError: If Cassandra API credentials are missing
        CassandraAPIClientError: If API call fails
    """
    return MonetizationService.create_payout(account, payout_data)


@router.get("/payouts/account/{account}/quote")
def get_quote(
    account: str,
    amount: float = Query(..., description="Amount to convert"),
    base_currency: str = Query(..., description="Source currency code"),
    quote_currency: str = Query(..., description="Target currency code"),
    current_user: dict = Depends(get_current_user),
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
    except MissingCredentialsError as config_error:
        logger.exception(CONFIG_ERROR_MSG, config_error)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=CONFIG_ERROR_DETAIL,
        ) from config_error
    except Exception as exc:
        logger.exception("Error getting quote from monetization service: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Error retrieving quote from monetization service",
        ) from exc
    return quote_data.model_dump()


@router.get("/payouts/account/{account}/recipient")
def get_recipients(
    account: str,
    user_id: str = Query(..., description="User ID to filter recipients"),
    current_user: dict = Depends(get_current_user),
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
        recipients_data = _get_recipients_data(account, user_id)
    except MissingCredentialsError as config_error:
        logger.exception(CONFIG_ERROR_MSG, config_error)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=CONFIG_ERROR_DETAIL,
        ) from config_error
    except Exception as exc:
        logger.exception("Error getting recipients from monetization service: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Error retrieving recipients from monetization service",
        ) from exc
    recipients_list = [recipient.model_dump() for recipient in recipients_data]
    return {"recipients": recipients_list, "total": len(recipients_list)}


@router.get("/payouts/account/{account}/wallets/{wallet_id}/balances")
def get_balance(
    account: str,
    wallet_id: str,
    current_user: dict = Depends(get_current_user),
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
        balance_data = _get_balance_data(account, wallet_id)
    except MissingCredentialsError as config_error:
        logger.exception(CONFIG_ERROR_MSG, config_error)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=CONFIG_ERROR_DETAIL,
        ) from config_error
    except Exception as exc:
        logger.exception("Error getting balance from monetization service: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Error retrieving balance from monetization service",
        ) from exc
    return balance_data.model_dump()


@router.post("/payouts/account/{account}/payout")
def create_payout(
    account: str,
    payout_data: PayoutCreateRequest = Body(...),
    current_user: dict = Depends(get_current_user),
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
        payout_response = _create_payout_data(account, payout_data)
    except MissingCredentialsError as config_error:
        logger.exception(CONFIG_ERROR_MSG, config_error)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=CONFIG_ERROR_DETAIL,
        ) from config_error
    except Exception as exc:
        logger.exception("Error creating payout in monetization service: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Error creating payout in monetization service",
        ) from exc
    return payout_response.model_dump()
