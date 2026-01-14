"""Monetization routes for payout operations."""

import logging

from fastapi import APIRouter, Body, Depends, HTTPException, Query, status

from app.common.apis.cassandra.dtos import (
    BalanceResponse,
    BlockchainWalletCreateRequest,
    BlockchainWalletUpdateRequest,
    ExternalWalletCreateRequest,
    ExternalWalletUpdateRequest,
    PayoutCreateRequest,
    PayoutResponse,
    QuoteResponse,
    RecipientCreateRequest,
    RecipientResponse,
    RecipientUpdateRequest,
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


def _extract_cassandra_error_message(cass_err: CassandraAPIClientError) -> str:
    """Extract error message from Cassandra API error.

    Args:
        cass_err: Cassandra API client error

    Returns:
        str: Extracted error message
    """
    error_detail_dict = cass_err.error_detail or {}
    error_obj = error_detail_dict.get(ERROR_KEY)

    # Try different error message formats from Cassandra
    if error_detail_dict.get(DETAIL_KEY):
        return error_detail_dict[DETAIL_KEY]

    if isinstance(error_obj, dict) and error_obj.get(MESSAGE_KEY):
        return error_obj[MESSAGE_KEY]

    if error_detail_dict.get(MESSAGE_KEY):
        return error_detail_dict[MESSAGE_KEY]

    return str(cass_err)


def _validate_payout_payload(payout_data: PayoutCreateRequest) -> None:
    """Validate payout payload.

    Args:
        payout_data: Payout request data

    Raises:
        HTTPException: If validation fails
    """
    if not payout_data.provider:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Provider is required",
        )

    _validate_provider(payout_data.provider)

    if not payout_data.exchange_only and not payout_data.recipient_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="recipient_id is required unless exchange_only is True",
        )


def _configure_payout_user_id(
    payout_data: PayoutCreateRequest,
    db_user_id: str,
) -> None:
    """Configure user_id in payout data.

    Args:
        payout_data: Payout request data (modified in place)
        db_user_id: User ID from database
    """
    if not payout_data.user_id:
        payout_data.user_id = db_user_id
    payout_data.provider = payout_data.provider.lower()


def _handle_cassandra_payout_error(cass_err: CassandraAPIClientError) -> HTTPException:
    """Handle Cassandra API error for payout creation.

    Args:
        cass_err: Cassandra API client error

    Returns:
        HTTPException: Appropriate HTTP exception
    """
    error_message = _extract_cassandra_error_message(cass_err)
    error_status_code = cass_err.status_code or status.HTTP_502_BAD_GATEWAY

    if error_message != str(cass_err):
        logger.error(f"Cassandra API error: {error_message}")
        return HTTPException(
            status_code=error_status_code,
            detail=error_message,
        )

    logger.exception("Error creating payout in monetization service: %s", cass_err)
    return HTTPException(
        status_code=error_status_code,
        detail="Error creating payout in monetization service",
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
    _validate_payout_payload(payout_data)
    _configure_payout_user_id(payout_data, db_user_id)

    logger.info(
        f"Creating payout - account: {account}, user_id: {payout_data.user_id}, "
        f"{PROVIDER_KEY}: {payout_data.provider}, exchange_only: {payout_data.exchange_only}",
    )

    try:
        payout_response = _create_payout_data(account, payout_data)
    except MissingCredentialsError as config_error:
        logger.exception(CONFIG_ERROR_MSG, config_error)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=CONFIG_ERROR_DETAIL,
        ) from config_error
    except CassandraAPIClientError as cass_err:
        raise _handle_cassandra_payout_error(cass_err) from cass_err
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


@router.get("/opentrade/vaultsAccount/{vault_address}/{account_address}")
def get_vault_account(
    vault_address: str,
    account_address: str,
    current_user: dict = Depends(get_current_user),
):
    """Get vault account information.

    This endpoint requires authentication and proxies requests to Cassandra API.

    Args:
        vault_address: Vault address
        account_address: Account address
        current_user: Current authenticated user

    Returns:
        dict: Vault account information from Cassandra (as dict for JSON response)

    Raises:
        HTTPException: If API call fails or user is not authenticated
    """
    logger.info(f"Getting vault account - vault_address: {vault_address}, account_address: {account_address}")

    try:
        vault_account_data = MonetizationService.get_vault_account(vault_address, account_address)
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
            f"Error getting vault account from Cassandra API (status: {error_status_code}): {cassandra_error}",
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
        logger.exception(f"Error getting vault account from monetization service: {exc}")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Error retrieving vault account from monetization service",
        ) from exc
    return vault_account_data.model_dump()


@router.get("/opentrade/vaults")
def get_vaults_list(
    current_user: dict = Depends(get_current_user),
):
    """Get list of vaults.

    This endpoint requires authentication and proxies requests to Cassandra API.

    Args:
        current_user: Current authenticated user

    Returns:
        dict: List of vaults from Cassandra (as dict for JSON response)

    Raises:
        HTTPException: If API call fails or user is not authenticated
    """
    logger.info("Getting vaults list")

    try:
        vaults_list_data = MonetizationService.get_vaults_list()
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
            f"Error getting vaults list from Cassandra API (status: {error_status_code}): {cassandra_error}",
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
        logger.exception(f"Error getting vaults list from monetization service: {exc}")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Error retrieving vaults list from monetization service",
        ) from exc
    return vaults_list_data.model_dump()


@router.get("/opentrade/vaults/{vault_address}")
def get_vault_overview(
    vault_address: str,
    current_user: dict = Depends(get_current_user),
):
    """Get vault overview information.

    This endpoint requires authentication and proxies requests to Cassandra API.

    Args:
        vault_address: Vault address
        current_user: Current authenticated user

    Returns:
        dict: Vault overview information from Cassandra (as dict for JSON response)

    Raises:
        HTTPException: If API call fails or user is not authenticated
    """
    logger.info(f"Getting vault overview - vault_address: {vault_address}")

    try:
        vault_overview_data = MonetizationService.get_vault_overview(vault_address)
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
            f"Error getting vault overview from Cassandra API (status: {error_status_code}): {cassandra_error}",
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
        logger.exception(f"Error getting vault overview from monetization service: {exc}")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Error retrieving vault overview from monetization service",
        ) from exc
    return vault_overview_data.model_dump()


def _handle_recipients_list_error(cassandra_error: CassandraAPIClientError) -> HTTPException:
    """Handle Cassandra API error for recipients list endpoint.

    Args:
        cassandra_error: Cassandra API client error

    Returns:
        HTTPException: Formatted HTTP exception
    """
    error_status_code = cassandra_error.status_code or status.HTTP_502_BAD_GATEWAY
    error_detail = cassandra_error.error_detail or {}
    logger.exception(
        f"Error getting recipients list from Cassandra API (status: {error_status_code}): {cassandra_error}",
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


@router.get("/recipients")
def get_recipients_list(
    provider: str | None = Query(None, description="Provider name to filter by"),
    exclude_provider: str | None = Query(None, description="Provider name to exclude"),
    current_user: dict = Depends(get_current_user),
):
    """Get recipients list from v1/recipients endpoint.

    This endpoint requires authentication and proxies requests to Cassandra API.

    Args:
        provider: Optional provider name to filter by
        exclude_provider: Optional provider name to exclude
        current_user: Current authenticated user

    Returns:
        dict: Recipients list from Cassandra with format {"recipients": [...]}

    Raises:
        HTTPException: If API call fails or user is not authenticated
    """
    logger.info(f"Getting recipients list - provider: {provider}, exclude_provider: {exclude_provider}")

    try:
        recipients_data = MonetizationService.get_recipients_list(
            provider=provider,
            exclude_provider=exclude_provider,
        )
    except MissingCredentialsError as config_error:
        logger.exception(CONFIG_ERROR_MSG, config_error)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=CONFIG_ERROR_DETAIL,
        ) from config_error
    except CassandraAPIClientError as cassandra_error:
        raise _handle_recipients_list_error(cassandra_error) from cassandra_error
    except Exception as exc:
        logger.exception(f"Error getting recipients list from monetization service: {exc}")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail={
                ERROR_KEY: {
                    MESSAGE_KEY: "Error retrieving recipients list from monetization service",
                    CODE_KEY: "INTERNAL_ERROR",
                },
            },
        ) from exc
    return {"recipients": [recipient.model_dump() for recipient in recipients_data]}


@router.post("/recipients")
def create_recipient(
    recipient_data: RecipientCreateRequest = Body(...),
    current_user: dict = Depends(get_current_user),
):
    """Create a recipient.

    This endpoint requires authentication and proxies requests to Cassandra API.

    Args:
        recipient_data: Recipient data to create
        current_user: Current authenticated user

    Returns:
        dict: Created recipient from Cassandra

    Raises:
        HTTPException: If API call fails or user is not authenticated
    """
    logger.info(f"Creating recipient - user_id: {recipient_data.user_id}, provider: {recipient_data.provider}")

    try:
        recipient_response = MonetizationService.create_recipient(recipient_data=recipient_data)
    except MissingCredentialsError as config_error:
        logger.exception(CONFIG_ERROR_MSG, config_error)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=CONFIG_ERROR_DETAIL,
        ) from config_error
    except CassandraAPIClientError as cassandra_error:
        raise _handle_recipients_list_error(cassandra_error) from cassandra_error
    except Exception as exc:
        logger.exception(f"Error creating recipient from monetization service: {exc}")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail={
                ERROR_KEY: {
                    MESSAGE_KEY: "Error creating recipient from monetization service",
                    CODE_KEY: "INTERNAL_ERROR",
                },
            },
        ) from exc
    return recipient_response.model_dump()


@router.put("/recipients/{recipient_id}")
def update_recipient(
    recipient_id: str,
    recipient_data: RecipientUpdateRequest = Body(...),
    current_user: dict = Depends(get_current_user),
):
    """Update a recipient.

    This endpoint requires authentication and proxies requests to Cassandra API.

    Args:
        recipient_id: Recipient ID to update
        recipient_data: Recipient data to update
        current_user: Current authenticated user

    Returns:
        dict: Updated recipient from Cassandra

    Raises:
        HTTPException: If API call fails or user is not authenticated
    """
    logger.info(f"Updating recipient {recipient_id}")

    try:
        recipient_response = MonetizationService.update_recipient(
            recipient_id=recipient_id,
            recipient_data=recipient_data,
        )
    except MissingCredentialsError as config_error:
        logger.exception(CONFIG_ERROR_MSG, config_error)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=CONFIG_ERROR_DETAIL,
        ) from config_error
    except CassandraAPIClientError as cassandra_error:
        raise _handle_recipients_list_error(cassandra_error) from cassandra_error
    except Exception as exc:
        logger.exception(f"Error updating recipient from monetization service: {exc}")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail={
                ERROR_KEY: {
                    MESSAGE_KEY: "Error updating recipient from monetization service",
                    CODE_KEY: "INTERNAL_ERROR",
                },
            },
        ) from exc
    return recipient_response.model_dump()


@router.delete("/recipients/{recipient_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_recipient(
    recipient_id: str,
    current_user: dict = Depends(get_current_user),
):
    """Delete a recipient.

    This endpoint requires authentication and proxies requests to Cassandra API.

    Args:
        recipient_id: Recipient ID to delete
        current_user: Current authenticated user

    Raises:
        HTTPException: If API call fails or user is not authenticated
    """
    logger.info(f"Deleting recipient {recipient_id}")

    try:
        MonetizationService.delete_recipient(recipient_id=recipient_id)
    except MissingCredentialsError as config_error:
        logger.exception(CONFIG_ERROR_MSG, config_error)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=CONFIG_ERROR_DETAIL,
        ) from config_error
    except CassandraAPIClientError as cassandra_error:
        raise _handle_recipients_list_error(cassandra_error) from cassandra_error
    except Exception as exc:
        logger.exception(f"Error deleting recipient from monetization service: {exc}")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail={
                ERROR_KEY: {
                    MESSAGE_KEY: "Error deleting recipient from monetization service",
                    CODE_KEY: "INTERNAL_ERROR",
                },
            },
        ) from exc


def _handle_blockchain_wallets_error(cassandra_error: CassandraAPIClientError) -> HTTPException:
    """Handle Cassandra API error for blockchain wallets endpoint.

    Args:
        cassandra_error: Cassandra API client error

    Returns:
        HTTPException: Formatted HTTP exception
    """
    error_status_code = cassandra_error.status_code or status.HTTP_502_BAD_GATEWAY
    error_detail = cassandra_error.error_detail or {}
    logger.exception(
        f"Error getting blockchain wallets from Cassandra API (status: {error_status_code}): {cassandra_error}",
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


@router.get("/blockchain-wallets")
def get_blockchain_wallets(
    provider: str | None = Query(None, description="Provider name to filter by"),
    exclude_provider: str | None = Query(None, description="Provider name to exclude"),
    current_user: dict = Depends(get_current_user),
):
    """Get blockchain wallets from v1/blockchain-wallets endpoint.

    This endpoint requires authentication and proxies requests to Cassandra API.

    Args:
        provider: Optional provider name to filter by
        exclude_provider: Optional provider name to exclude
        current_user: Current authenticated user

    Returns:
        dict: Blockchain wallets list from Cassandra with format {"wallets": [...]}

    Raises:
        HTTPException: If API call fails or user is not authenticated
    """
    logger.info(f"Getting blockchain wallets - provider: {provider}, exclude_provider: {exclude_provider}")

    try:
        wallets_data = MonetizationService.get_blockchain_wallets(
            provider=provider,
            exclude_provider=exclude_provider,
        )
    except MissingCredentialsError as config_error:
        logger.exception(CONFIG_ERROR_MSG, config_error)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=CONFIG_ERROR_DETAIL,
        ) from config_error
    except CassandraAPIClientError as cassandra_error:
        raise _handle_blockchain_wallets_error(cassandra_error) from cassandra_error
    except Exception as exc:
        logger.exception(f"Error getting blockchain wallets from monetization service: {exc}")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail={
                ERROR_KEY: {
                    MESSAGE_KEY: "Error retrieving blockchain wallets from monetization service",
                    CODE_KEY: "INTERNAL_ERROR",
                },
            },
        ) from exc
    return {"wallets": [wallet.model_dump() for wallet in wallets_data]}


@router.post("/blockchain-wallets")
def create_blockchain_wallet(
    wallet_data: BlockchainWalletCreateRequest = Body(...),
    current_user: dict = Depends(get_current_user),
):
    """Create a blockchain wallet.

    This endpoint requires authentication and proxies requests to Cassandra API.

    Args:
        wallet_data: Wallet data to create
        current_user: Current authenticated user

    Returns:
        dict: Created blockchain wallet from Cassandra

    Raises:
        HTTPException: If API call fails or user is not authenticated
    """
    logger.info(f"Creating blockchain wallet - name: {wallet_data.name}, provider: {wallet_data.provider}")

    try:
        wallet_response = MonetizationService.create_blockchain_wallet(wallet_data=wallet_data)
    except MissingCredentialsError as config_error:
        logger.exception(CONFIG_ERROR_MSG, config_error)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=CONFIG_ERROR_DETAIL,
        ) from config_error
    except CassandraAPIClientError as cassandra_error:
        raise _handle_blockchain_wallets_error(cassandra_error) from cassandra_error
    except Exception as exc:
        logger.exception(f"Error creating blockchain wallet from monetization service: {exc}")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail={
                ERROR_KEY: {
                    MESSAGE_KEY: "Error creating blockchain wallet from monetization service",
                    CODE_KEY: "INTERNAL_ERROR",
                },
            },
        ) from exc
    return wallet_response.model_dump()


@router.put("/blockchain-wallets/{wallet_id}")
def update_blockchain_wallet(
    wallet_id: str,
    wallet_data: BlockchainWalletUpdateRequest = Body(...),
    current_user: dict = Depends(get_current_user),
):
    """Update a blockchain wallet.

    This endpoint requires authentication and proxies requests to Cassandra API.

    Args:
        wallet_id: Wallet ID to update
        wallet_data: Wallet data to update
        current_user: Current authenticated user

    Returns:
        dict: Updated blockchain wallet from Cassandra

    Raises:
        HTTPException: If API call fails or user is not authenticated
    """
    logger.info(f"Updating blockchain wallet {wallet_id}")

    try:
        wallet_response = MonetizationService.update_blockchain_wallet(
            wallet_id=wallet_id,
            wallet_data=wallet_data,
        )
    except MissingCredentialsError as config_error:
        logger.exception(CONFIG_ERROR_MSG, config_error)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=CONFIG_ERROR_DETAIL,
        ) from config_error
    except CassandraAPIClientError as cassandra_error:
        raise _handle_blockchain_wallets_error(cassandra_error) from cassandra_error
    except Exception as exc:
        logger.exception(f"Error updating blockchain wallet from monetization service: {exc}")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail={
                ERROR_KEY: {
                    MESSAGE_KEY: "Error updating blockchain wallet from monetization service",
                    CODE_KEY: "INTERNAL_ERROR",
                },
            },
        ) from exc
    return wallet_response.model_dump()


@router.delete("/blockchain-wallets/{wallet_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_blockchain_wallet(
    wallet_id: str,
    current_user: dict = Depends(get_current_user),
):
    """Delete a blockchain wallet.

    This endpoint requires authentication and proxies requests to Cassandra API.

    Args:
        wallet_id: Wallet ID to delete
        current_user: Current authenticated user

    Raises:
        HTTPException: If API call fails or user is not authenticated
    """
    logger.info(f"Deleting blockchain wallet {wallet_id}")

    try:
        MonetizationService.delete_blockchain_wallet(wallet_id=wallet_id)
    except MissingCredentialsError as config_error:
        logger.exception(CONFIG_ERROR_MSG, config_error)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=CONFIG_ERROR_DETAIL,
        ) from config_error
    except CassandraAPIClientError as cassandra_error:
        raise _handle_blockchain_wallets_error(cassandra_error) from cassandra_error
    except Exception as exc:
        logger.exception(f"Error deleting blockchain wallet from monetization service: {exc}")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail={
                ERROR_KEY: {
                    MESSAGE_KEY: "Error deleting blockchain wallet from monetization service",
                    CODE_KEY: "INTERNAL_ERROR",
                },
            },
        ) from exc


def _handle_external_wallets_error(cassandra_error: CassandraAPIClientError) -> HTTPException:
    """Handle Cassandra API error for external wallets endpoint.

    Args:
        cassandra_error: Cassandra API client error

    Returns:
        HTTPException: Formatted HTTP exception
    """
    error_status_code = cassandra_error.status_code or status.HTTP_502_BAD_GATEWAY
    error_detail = cassandra_error.error_detail or {}
    logger.exception(
        f"Error getting external wallets from Cassandra API (status: {error_status_code}): {cassandra_error}",
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


@router.get("/external-wallets")
def get_external_wallets(
    current_user: dict = Depends(get_current_user),
):
    """Get external wallets from v1/external-wallets endpoint.

    This endpoint requires authentication and proxies requests to Cassandra API.

    Args:
        current_user: Current authenticated user

    Returns:
        dict: External wallets list from Cassandra with format {"wallets": [...]}

    Raises:
        HTTPException: If API call fails or user is not authenticated
    """
    logger.info("Getting external wallets")

    try:
        wallets_data = MonetizationService.get_external_wallets()
    except MissingCredentialsError as config_error:
        logger.exception(CONFIG_ERROR_MSG, config_error)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=CONFIG_ERROR_DETAIL,
        ) from config_error
    except CassandraAPIClientError as cassandra_error:
        raise _handle_external_wallets_error(cassandra_error) from cassandra_error
    except Exception as exc:
        logger.exception(f"Error getting external wallets from monetization service: {exc}")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail={
                ERROR_KEY: {
                    MESSAGE_KEY: "Error retrieving external wallets from monetization service",
                    CODE_KEY: "INTERNAL_ERROR",
                },
            },
        ) from exc
    return {"wallets": [wallet.model_dump() for wallet in wallets_data]}


@router.post("/external-wallets")
def create_external_wallet(
    wallet_data: ExternalWalletCreateRequest = Body(...),
    current_user: dict = Depends(get_current_user),
):
    """Create an external wallet.

    This endpoint requires authentication and proxies requests to Cassandra API.

    Args:
        wallet_data: Wallet data to create
        current_user: Current authenticated user

    Returns:
        dict: Created external wallet from Cassandra

    Raises:
        HTTPException: If API call fails or user is not authenticated
    """
    logger.info(f"Creating external wallet - name: {wallet_data.name}, category: {wallet_data.category}")

    try:
        wallet_response = MonetizationService.create_external_wallet(wallet_data=wallet_data)
    except MissingCredentialsError as config_error:
        logger.exception(CONFIG_ERROR_MSG, config_error)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=CONFIG_ERROR_DETAIL,
        ) from config_error
    except CassandraAPIClientError as cassandra_error:
        raise _handle_external_wallets_error(cassandra_error) from cassandra_error
    except Exception as exc:
        logger.exception(f"Error creating external wallet from monetization service: {exc}")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail={
                ERROR_KEY: {
                    MESSAGE_KEY: "Error creating external wallet from monetization service",
                    CODE_KEY: "INTERNAL_ERROR",
                },
            },
        ) from exc
    return wallet_response.model_dump()


@router.put("/external-wallets/{wallet_id}")
def update_external_wallet(
    wallet_id: str,
    wallet_data: ExternalWalletUpdateRequest = Body(...),
    current_user: dict = Depends(get_current_user),
):
    """Update an external wallet.

    This endpoint requires authentication and proxies requests to Cassandra API.

    Args:
        wallet_id: Wallet ID to update
        wallet_data: Wallet data to update
        current_user: Current authenticated user

    Returns:
        dict: Updated external wallet from Cassandra

    Raises:
        HTTPException: If API call fails or user is not authenticated
    """
    logger.info(f"Updating external wallet {wallet_id}")

    try:
        wallet_response = MonetizationService.update_external_wallet(
            wallet_id=wallet_id,
            wallet_data=wallet_data,
        )
    except MissingCredentialsError as config_error:
        logger.exception(CONFIG_ERROR_MSG, config_error)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=CONFIG_ERROR_DETAIL,
        ) from config_error
    except CassandraAPIClientError as cassandra_error:
        raise _handle_external_wallets_error(cassandra_error) from cassandra_error
    except Exception as exc:
        logger.exception(f"Error updating external wallet from monetization service: {exc}")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail={
                ERROR_KEY: {
                    MESSAGE_KEY: "Error updating external wallet from monetization service",
                    CODE_KEY: "INTERNAL_ERROR",
                },
            },
        ) from exc
    return wallet_response.model_dump()


@router.delete("/external-wallets/{wallet_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_external_wallet(
    wallet_id: str,
    current_user: dict = Depends(get_current_user),
):
    """Delete an external wallet.

    This endpoint requires authentication and proxies requests to Cassandra API.

    Args:
        wallet_id: Wallet ID to delete
        current_user: Current authenticated user

    Raises:
        HTTPException: If API call fails or user is not authenticated
    """
    logger.info(f"Deleting external wallet {wallet_id}")

    try:
        MonetizationService.delete_external_wallet(wallet_id=wallet_id)
    except MissingCredentialsError as config_error:
        logger.exception(CONFIG_ERROR_MSG, config_error)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=CONFIG_ERROR_DETAIL,
        ) from config_error
    except CassandraAPIClientError as cassandra_error:
        raise _handle_external_wallets_error(cassandra_error) from cassandra_error
    except Exception as exc:
        logger.exception(f"Error deleting external wallet from monetization service: {exc}")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail={
                ERROR_KEY: {
                    MESSAGE_KEY: "Error deleting external wallet from monetization service",
                    CODE_KEY: "INTERNAL_ERROR",
                },
            },
        ) from exc
