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
from app.common.apis.cassandra.errors import CassandraAPIClientError
from app.common.enums import Provider
from app.common.errors import MissingCredentialsError
from app.middleware.auth import get_current_user
from app.monetization.service import MonetizationService
from app.user.service import UserService

logger = logging.getLogger(__name__)

router = APIRouter()

# Constants
CONFIG_ERROR_MSG = "Configuration error: %s"
CONFIG_ERROR_DETAIL = "Monetization service configuration error"
PROVIDER_KEY = "provider"  # noqa: WPS226
DETAIL_KEY = "detail"  # noqa: WPS226
ERROR_KEY = "error"  # noqa: WPS226
MESSAGE_KEY = "message"  # noqa: WPS226
CODE_KEY = "code"  # noqa: WPS226
ID_KEY = "id"  # noqa: WPS226


def _get_quote_data(
    account: str,
    amount: float,
    base_currency: str,
    quote_currency: str,
    provider: str,
) -> QuoteResponse:
    """Get quote data from monetization service.

    Args:
        account: Account type
        amount: Amount to convert
        base_currency: Source currency code
        quote_currency: Target currency code
        provider: Provider name (kira, cobre, supra)

    Returns:
        QuoteResponse object

    Raises:
        MissingCredentialsError: If Cassandra API credentials are missing
        CassandraAPIClientError: If API call fails
    """
    return MonetizationService.get_quote(account, amount, base_currency, quote_currency, provider)


def _get_recipients_data(
    account: str,
    user_id: str,
    provider: str,
) -> list[RecipientResponse]:
    """Get recipients data from monetization service.

    Args:
        account: Account type
        user_id: User ID to filter recipients
        provider: Provider name (kira, cobre, supra)

    Returns:
        List of RecipientResponse objects

    Raises:
        MissingCredentialsError: If Cassandra API credentials are missing
        CassandraAPIClientError: If API call fails
    """
    return MonetizationService.get_recipients(account, user_id, provider)


def _get_balance_data(
    account: str,
    wallet_id: str,
    provider: str = "kira",
) -> BalanceResponse:
    """Get balance data from monetization service.

    Args:
        account: Account type
        wallet_id: Wallet ID
        provider: Provider name (kira, cobre, supra). Defaults to "kira"

    Returns:
        BalanceResponse object

    Raises:
        MissingCredentialsError: If Cassandra API credentials are missing
        CassandraAPIClientError: If API call fails
    """
    return MonetizationService.get_balance(account, wallet_id, provider)


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


def _validate_provider(provider: str) -> None:
    """Validate provider name.

    Args:
        provider: Provider name to validate

    Raises:
        HTTPException: If provider is invalid
    """
    try:
        Provider(provider.lower())
    except ValueError:
        provider_list = ", ".join([prov.value for prov in Provider])
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid provider: {provider}. Must be one of: {provider_list}",
        )


def _extract_from_dict(data: dict, default_message: str, default_code: str) -> tuple[str, str]:
    """Extract message and code from a dictionary.

    Args:
        data: Dictionary to extract from
        default_message: Default message if not found
        default_code: Default code if not found

    Returns:
        tuple[str, str]: Message and code
    """
    error_dict = data.get(ERROR_KEY)
    if isinstance(error_dict, dict):
        return (
            error_dict.get(MESSAGE_KEY, default_message),
            error_dict.get(CODE_KEY, default_code),
        )
    if MESSAGE_KEY in data:
        return (
            data.get(MESSAGE_KEY, default_message),
            data.get(CODE_KEY, default_code),
        )
    return default_message, default_code


def _extract_error_from_detail(error_detail: dict) -> tuple[str, str]:
    """Extract error message and code from error detail.

    Args:
        error_detail: Error detail dictionary

    Returns:
        tuple[str, str]: Error message and code
    """
    default_message = "Error al obtener la cotización"
    default_code = "CASSANDRA_API_ERROR"

    if not isinstance(error_detail, dict):
        return default_message, default_code

    # Check nested format: {"detail": {"error": {...}}}
    if DETAIL_KEY in error_detail and isinstance(error_detail[DETAIL_KEY], dict):
        return _extract_from_dict(error_detail[DETAIL_KEY], default_message, default_code)

    # Check direct format: {"error": {...}} or {"message": ...}
    return _extract_from_dict(error_detail, default_message, default_code)


def _get_kira_user_id(account: str, user_id: str | None) -> str:
    """Get Kira user ID from query parameter or environment variables.

    Args:
        account: Account type
        user_id: Optional user ID from query parameter

    Returns:
        str: User ID

    Raises:
        HTTPException: If user_id is not configured
    """
    if user_id:
        return user_id

    from app.common.secrets import get_secret

    if account == "transfer":
        user_id = get_secret("KIRA_USER_ID_TRANSFER")
    elif account == "pay":
        user_id = get_secret("KIRA_USER_ID_PAY")
    else:
        user_id = None

    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Kira user_id not configured for account type: {account}",
        )
    return user_id


def _handle_recipients_error(cassandra_error: CassandraAPIClientError) -> HTTPException:
    """Handle Cassandra API error for recipients endpoint.

    Args:
        cassandra_error: Cassandra API client error

    Returns:
        HTTPException: Formatted HTTP exception
    """
    error_status_code = cassandra_error.status_code or status.HTTP_502_BAD_GATEWAY
    error_detail = cassandra_error.error_detail or {}
    logger.exception(
        f"Error getting recipients from Cassandra API (status: {error_status_code}): {cassandra_error}",
    )
    error_message, error_code = _extract_error_from_detail(error_detail)
    return HTTPException(
        status_code=error_status_code,
        detail={
            ERROR_KEY: {
                MESSAGE_KEY: error_message,
                CODE_KEY: error_code,
            },
        },
    )


def _get_database_user_id(current_user: dict) -> str:
    """Get user ID from database using Firebase UID.

    Args:
        current_user: Current authenticated user

    Returns:
        str: User ID from database

    Raises:
        HTTPException: If user is not authenticated or not found
    """
    firebase_uid = current_user.get("firebase_uid")
    if not firebase_uid:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not authenticated",
        )

    db_user = UserService.get_user_by_firebase_uid(firebase_uid)
    if not db_user or not db_user.get(ID_KEY):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found in database",
        )

    return db_user.get(ID_KEY)


@router.get("/payouts/account/{account}/quote")
def get_quote(  # noqa: WPS211
    account: str,
    amount: float = Query(..., description="Amount to convert"),
    base_currency: str = Query(..., description="Source currency code"),
    quote_currency: str = Query(..., description="Target currency code"),
    provider: str = Query(..., description="Provider name (kira, cobre, supra)"),
    current_user: dict = Depends(get_current_user),
):
    """Get a quote for currency conversion.

    This endpoint requires authentication and proxies requests to Cassandra API.

    Args:
        account: Account type (e.g., 'transfer', 'pay')
        amount: Amount to convert
        base_currency: Source currency code
        quote_currency: Target currency code
        provider: Provider name (kira, cobre, supra)
        current_user: Current authenticated user

    Returns:
        dict: Quote information from Cassandra (as dict for JSON response)

    Raises:
        HTTPException: If API call fails or user is not authenticated
    """
    logger.info(
        f"Getting quote - account: {account}, amount: {amount}, "
        f"base_currency: {base_currency}, quote_currency: {quote_currency}, "
        f"{PROVIDER_KEY}: {provider}",
    )

    _validate_provider(provider)

    try:
        quote_data = _get_quote_data(account, amount, base_currency, quote_currency, provider.lower())
    except MissingCredentialsError as config_error:
        logger.exception(CONFIG_ERROR_MSG, config_error)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=CONFIG_ERROR_DETAIL,
        ) from config_error
    except CassandraAPIClientError as cassandra_error:
        error_status_code = cassandra_error.status_code or status.HTTP_502_BAD_GATEWAY
        error_detail = cassandra_error.error_detail or {}
        logger.exception(
            f"Error getting quote from Cassandra API (status: {error_status_code}): {cassandra_error}",
        )
        error_message, error_code = _extract_error_from_detail(error_detail)
        raise HTTPException(
            status_code=error_status_code,
            detail={
                ERROR_KEY: {
                    MESSAGE_KEY: error_message,
                    CODE_KEY: error_code,
                },
            },
        ) from cassandra_error
    except Exception as exc:
        logger.exception(f"Error getting quote from monetization service: {exc}")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Error retrieving quote from monetization service",
        ) from exc
    return quote_data.model_dump()


@router.get("/payouts/account/{account}/recipient")
def get_recipients(
    account: str,
    provider: str = Query(..., description="Provider name (kira, cobre, supra)"),
    user_id: str | None = Query(None, description="User ID (optional, for Kira provider)"),
    current_user: dict = Depends(get_current_user),
):
    """Get recipients for an account.

    This endpoint requires authentication and proxies requests to Cassandra API.
    For Kira provider, user_id can be passed as query parameter (from Dobby env vars).
    For other providers, user_id is obtained from the authenticated user's database record.

    Args:
        account: Account type (e.g., 'transfer', 'pay')
        provider: Provider name (kira, cobre, supra)
        user_id: Optional user ID (for Kira provider, comes from Dobby env vars)
        current_user: Current authenticated user

    Returns:
        list: List of recipients from Cassandra (as list of dicts for JSON response)

    Raises:
        HTTPException: If API call fails or user is not authenticated
    """
    _validate_provider(provider)

    provider_lower = provider.lower()
    if provider_lower == "kira":
        resolved_user_id = _get_kira_user_id(account, user_id)
    else:
        resolved_user_id = _get_database_user_id(current_user)

    logger.info(f"Getting recipients - account: {account}, user_id: {resolved_user_id}, provider: {provider}")

    try:
        recipients_data = _get_recipients_data(account, resolved_user_id, provider_lower)
    except MissingCredentialsError as config_error:
        logger.exception(CONFIG_ERROR_MSG, config_error)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=CONFIG_ERROR_DETAIL,
        ) from config_error
    except CassandraAPIClientError as cassandra_error:
        raise _handle_recipients_error(cassandra_error) from cassandra_error
    except Exception as exc:
        logger.exception(f"Error getting recipients from monetization service: {exc}")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail={
                ERROR_KEY: {
                    MESSAGE_KEY: "Error retrieving recipients from monetization service",
                    CODE_KEY: "INTERNAL_ERROR",
                },
            },
        ) from exc
    recipients_list = [recipient.model_dump() for recipient in recipients_data]
    return {"recipients": recipients_list, "total": len(recipients_list)}


@router.get("/payouts/account/{account}/wallets/{wallet_id}/balances")
def get_balance(
    account: str,
    wallet_id: str,
    provider: str = Query("kira", description="Provider name (kira, cobre, supra)"),
    current_user: dict = Depends(get_current_user),
):
    """Get balance for a wallet.

    This endpoint requires authentication and proxies requests to Cassandra API.

    Args:
        account: Account type (e.g., 'transfer', 'pay')
        wallet_id: Wallet ID
        provider: Provider name (kira, cobre, supra). Defaults to "kira"
        current_user: Current authenticated user

    Returns:
        dict: Balance information from Cassandra (as dict for JSON response)

    Raises:
        HTTPException: If API call fails or user is not authenticated
    """
    # Validate provider
    try:
        Provider(provider.lower())
    except ValueError:
        _validate_provider(provider)

    logger.info(f"Getting balance - account: {account}, wallet_id: {wallet_id}, provider: {provider}")

    try:
        balance_data = _get_balance_data(account, wallet_id, provider.lower())
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
    The user_id is obtained from the authenticated user's database record and added to the payout data.

    Args:
        account: Account type (e.g., 'transfer', 'pay')
        payout_data: Payout request data (must include provider)
        current_user: Current authenticated user

    Returns:
        dict: Payout response from Cassandra (as dict for JSON response)

    Raises:
        HTTPException: If API call fails or user is not authenticated
    """
    db_user_id = _get_database_user_id(current_user)

    if not payout_data.provider:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Provider is required",
        )

    _validate_provider(payout_data.provider)

    # Set user_id in payout_data
    # If user_id is already provided (e.g., from Dobby for Kira), use it
    # Otherwise, use the user_id from database (for Cobre, Supra, etc.)
    if not payout_data.user_id:
        payout_data.user_id = db_user_id
    # If user_id is provided, keep it (for Kira compatibility)
    payout_data.provider = payout_data.provider.lower()

    logger.info(
        f"Creating payout - account: {account}, user_id: {payout_data.user_id}, "
        f"{PROVIDER_KEY}: {payout_data.provider}",
    )

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


@router.get("/payouts/account/{account}/payout")
def get_payout_history(
    account: str,
    current_user: dict = Depends(get_current_user),
) -> dict:
    """Get payout history for an account.

    This endpoint requires authentication and proxies requests to Cassandra API.

    Args:
        account: Account type (e.g., 'transfer', 'pay')
        current_user: Current authenticated user

    Returns:
        PayoutHistoryResponse: Payout history response from Cassandra

    Raises:
        HTTPException: If API call fails or user is not authenticated
    """
    logger.info(f"Getting payout history - account: {account}")

    try:
        payout_history = MonetizationService.get_payout_history(account)
    except MissingCredentialsError as config_error:
        logger.exception(CONFIG_ERROR_MSG, config_error)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=CONFIG_ERROR_DETAIL,
        ) from config_error
    except CassandraAPIClientError as cass_err:
        error_status_code = cass_err.status_code or status.HTTP_502_BAD_GATEWAY
        error_detail = cass_err.error_detail or {}
        logger.exception(
            "Error getting payout history from Cassandra API (status: %s): %s",
            error_status_code,
            cass_err,
        )
        if error_detail:
            error_message, error_code = _extract_error_from_detail(error_detail)
        else:
            error_message = str(cass_err) or "Error retrieving payout history from Cassandra API"
            error_code = "CASSANDRA_API_ERROR"
        raise HTTPException(
            status_code=error_status_code,
            detail={
                ERROR_KEY: {
                    MESSAGE_KEY: error_message,
                    CODE_KEY: error_code,
                },
            },
        ) from cass_err
    except Exception as exc:
        logger.exception("Error getting payout history from monetization service: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Error retrieving payout history from monetization service",
        ) from exc
    return payout_history.model_dump()
