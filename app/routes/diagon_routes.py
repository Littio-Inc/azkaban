"""Diagon routes for vault accounts."""

import logging
import os

from fastapi import APIRouter, Depends, Header, HTTPException, status

from app.common.apis.diagon.client import DiagonClient
from app.common.apis.diagon.dtos import EstimateFeeRequest, VaultToVaultRequest
from app.common.apis.diagon.errors import DiagonAPIClientError
from app.common.enums import Environment
from app.middleware.auth import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter()

# Constants
DIAGON_API_ERROR_MSG = "Diagon API error: %s"


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
        logger.error(DIAGON_API_ERROR_MSG, api_error)
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
        logger.error(DIAGON_API_ERROR_MSG, api_error)
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


def _estimate_fee_data(request: EstimateFeeRequest) -> dict:
    """Estimate fee data from Diagon client.

    Args:
        request: EstimateFeeRequest with operation, source, destination, assetId, and amount

    Returns:
        Dictionary with fee estimate response

    Raises:
        DiagonAPIClientError: If API call fails
    """
    client = DiagonClient()
    response = client.estimate_fee(request)
    return response.model_dump()


@router.post("/vault/transactions/estimate-fee")
def estimate_fee(
    request: EstimateFeeRequest,
    current_user: dict = Depends(get_current_user)  # noqa: WPS404
):
    """Estimate transaction fee from Diagon.

    This endpoint requires authentication and proxies requests to Diagon API.

    Args:
        request: EstimateFeeRequest with operation, source, destination, assetId, and amount
        current_user: Current authenticated user

    Returns:
        dict: Response with fee estimates for low, medium, and high priority

    Raises:
        HTTPException: If API call fails or user is not authenticated
    """
    logger.info(
        "Estimating fee for operation %s, asset %s, amount %s from Diagon",
        request.operation,
        request.assetId,
        request.amount
    )

    try:
        fee_data = _estimate_fee_data(request)
    except DiagonAPIClientError as api_error:
        logger.error(DIAGON_API_ERROR_MSG, api_error)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Error estimating fee from Diagon service"
        )
    except Exception as exc:
        logger.error("Error estimating fee from Diagon: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Error estimating fee from Diagon service"
        )
    return fee_data


def _get_production_mock_external_wallets() -> dict:
    """Get mocked external wallets data for production.

    Returns:
        Dictionary with mocked external wallets response
    """
    return {
        "message": "External wallets retrieved successfully",
        "code": 0,
        "data": [
            {
                "id": "edbd06be-e9b0-4739-ad91-41b7dc83c594",
                "name": "BOTH_COBRE_B2C",
                "assets": [
                    {
                        "id": "USDT_POLYGON",
                        "status": "APPROVED",
                        "address": "0x4A99D2Bc4bf591a0a6FC39B1D24cD6959c609391",
                        "tag": ""
                    },
                    {
                        "id": "USDC_POLYGON_NXTB",
                        "status": "APPROVED",
                        "address": "0x4A99D2Bc4bf591a0a6FC39B1D24cD6959c609391",
                        "tag": ""
                    }
                ]
            },
            {
                "id": "8bf82d61-7574-41b1-8af5-0c5f1d543f35",
                "name": "PROVIDER_KIRA_B2B",
                "assets": [
                    {
                        "id": "USDT_POLYGON",
                        "status": "APPROVED",
                        "address": "0xB9fE096DA4b371FC0c8eCEB5DACb6931E0748C43",
                        "tag": ""
                    },
                    {
                        "id": "USDC_POLYGON_NXTB",
                        "status": "APPROVED",
                        "address": "0xB9fE096DA4b371FC0c8eCEB5DACb6931E0748C43",
                        "tag": ""
                    }
                ]
            },
            {
                "id": "8bf82d61-7574-41b1-8af5-0c5f1d543f36",
                "name": "PROVIDER_KIRA_POMELO",
                "assets": [
                    {
                        "id": "USDT_POLYGON",
                        "status": "APPROVED",
                        "address": "0x2E95787CB5Fe967257aF440a4134080018dffE54",
                        "tag": ""
                    },
                    {
                        "id": "USDC_POLYGON_NXTB",
                        "status": "APPROVED",
                        "address": "0x2E95787CB5Fe967257aF440a4134080018dffE54",
                        "tag": ""
                    }
                ]
            },
            {
                "id": "de129840-bcea-40b4-993c-04dc342d78bb",
                "name": "PROVIDER_SUPRA",
                "assets": [
                    {
                        "id": "USDC",
                        "status": "APPROVED",
                        "address": "0x821d8547515dcD513e2f5eBb0EA684A003B85a58",
                        "tag": ""
                    },
                    {
                        "id": "USDT_ERC20",
                        "status": "APPROVED",
                        "address": "0x821d8547515dcD513e2f5eBb0EA684A003B85a58",
                        "tag": ""
                    },
                    {
                        "id": "USDT_POLYGON",
                        "status": "APPROVED",
                        "address": "0x821d8547515dcD513e2f5eBb0EA684A003B85a58",
                        "tag": ""
                    }
                ]
            },
            {
                "id": "dbee134f-b6f0-428b-8992-2813ca3f4bd0",
                "name": "B2C_BRIDGE",
                "assets": [
                    {
                        "id": "USDC_POLYGON",
                        "status": "APPROVED",
                        "address": "0x56dD4D9A4236Acbe5C6F6E0970A41b26A27d62e6",
                        "tag": ""
                    }
                ]
            },
            {
                "id": "dbee134f-b6f0-428b-8992-2813ca3f4bd1",
                "name": "B2C_KOYWE",
                "assets": [
                    {
                        "id": "USDC_POLYGON",
                        "status": "APPROVED",
                        "address": "0x97F3539EbEA7844C1BfBdbC00b82F285D2f5D32f",
                        "tag": ""
                    }
                ]
            },
            {
                "id": "dbee134f-b6f0-428b-8992-2813ca3f4bd2",
                "name": "B2C_BLOCKCHAIN",
                "assets": [
                    {
                        "id": "USDC_POLYGON",
                        "status": "APPROVED",
                        "address": "0xE95DFf9E426F8135F018534C4bA2dE9f9E42783F",
                        "tag": ""
                    }
                ]
            }
        ]
    }


def _get_external_wallets_data() -> list[dict] | dict:
    """Get external wallets data from Diagon client.

    Returns:
        List of external wallets data dictionaries when wallets exist, or
        Dictionary with message, code, and data when no wallets found.

    Raises:
        DiagonAPIClientError: If API call fails
    """
    client = DiagonClient()
    wallets = client.get_external_wallets()
    # If it's a list, convert to list of dicts
    if isinstance(wallets, list):
        return [wallet.model_dump() for wallet in wallets]
    # If it's the empty response, return as dict
    return wallets.model_dump()


@router.get("/vault/external-wallets")
def get_external_wallets(
    current_user: dict = Depends(get_current_user)  # noqa: WPS404
):
    """Get external wallets from Diagon.

    This endpoint requires authentication and proxies requests to Diagon API.
    If the environment is production, returns mocked data instead of calling Diagon.

    Args:
        current_user: Current authenticated user

    Returns:
        list | dict: List of external wallets with their assets from Diagon,
            or dict with message, code, and data when no wallets found

    Raises:
        HTTPException: If API call fails or user is not authenticated
    """
    # Check if environment is production
    environment = os.getenv("ENVIRONMENT", Environment.LOCAL.value)
    logger.info("Environment: %s", environment)

    if environment == Environment.PRODUCTION.value:
        logger.info(
            "Production environment detected (ENVIRONMENT=%s). Returning mocked external wallets data",
            environment
        )
        return _get_production_mock_external_wallets()

    logger.info("Getting external wallets from Diagon (environment: %s)", environment)

    try:
        wallets_data = _get_external_wallets_data()
    except DiagonAPIClientError as api_error:
        logger.error(DIAGON_API_ERROR_MSG, api_error)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Error retrieving external wallets from Diagon service"
        )
    except Exception as exc:
        logger.error("Error getting external wallets from Diagon: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Error retrieving external wallets from Diagon service"
        )
    return wallets_data


def _create_transaction_data(request: VaultToVaultRequest, idempotency_key: str | None = None) -> dict:
    """Create transaction data from Diagon client.

    Args:
        request: VaultToVaultRequest with network, service, token,
            sourceVaultId, destinationWalletId, feeLevel, and amount
        idempotency_key: Optional idempotency key to send as header

    Returns:
        Dictionary with transaction response

    Raises:
        DiagonAPIClientError: If API call fails
    """
    client = DiagonClient()
    response = client.vault_to_vault(request, idempotency_key=idempotency_key)
    return response.model_dump()


@router.post("/vault/transactions/create-transaction")
def create_transaction(
    request: VaultToVaultRequest,
    idempotency_key: str | None = Header(  # noqa: WPS404
        None,
        alias="idempotency-key",
        description="Idempotency key for the request"
    ),
    current_user: dict = Depends(get_current_user)  # noqa: WPS404
):
    """Create a transaction from Diagon (vault-to-vault, vault-to-external, etc.).

    This endpoint requires authentication and proxies requests to Diagon API.

    Args:
        request: VaultToVaultRequest with network, service, token,
            sourceVaultId, destinationWalletId, feeLevel, and amount
        idempotency_key: Optional idempotency key header (idempotency-key)
        current_user: Current authenticated user

    Returns:
        dict: Response with transaction id and status

    Raises:
        HTTPException: If API call fails or user is not authenticated
    """
    logger.info(
        "Creating transaction: network %s, service %s, token %s, amount %s from Diagon",
        request.network,
        request.service,
        request.token,
        request.amount
    )

    try:
        transaction_data = _create_transaction_data(request, idempotency_key=idempotency_key)
    except DiagonAPIClientError as api_error:
        logger.error(DIAGON_API_ERROR_MSG, api_error)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Error creating transaction from Diagon service"
        )
    except Exception as exc:
        logger.error("Error creating transaction from Diagon: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Error creating transaction from Diagon service"
        )
    return transaction_data
