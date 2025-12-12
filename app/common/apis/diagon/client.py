"""Diagon API client for vault accounts."""

from app.common.apis.diagon.agent import (
    BASE_ACCOUNTS_PATH,
    BASE_TRANSACTIONS_PATH,
    BASE_VAULT_TRANSACTIONS_PATH,
    DiagonAgent,
)
from app.common.apis.diagon.dtos import (
    AccountResponse,
    EstimateFeeRequest,
    EstimateFeeResponse,
    ExternalWallet,
    ExternalWalletsEmptyResponse,
    RefreshBalanceResponse,
    VaultToVaultRequest,
    VaultToVaultResponse,
)

# Constants
PATH_SEPARATOR = "/"


class DiagonClient:
    """Client for interacting with Diagon API.

    This client provides high-level methods to interact with the Diagon API,
    handling request/response parsing and error handling.
    """

    _agent: DiagonAgent

    def __init__(self) -> None:
        """Initialize Diagon client with API agent."""
        self._agent = DiagonAgent()

    def get_accounts(self) -> list[AccountResponse]:
        """Get accounts from Diagon API.

        Returns:
            List of AccountResponse objects containing account information and assets

        Raises:
            DiagonAPIClientError: If API call fails
        """
        response_data = self._agent.get(req_path=BASE_ACCOUNTS_PATH)
        # Handle both list and single object responses
        if isinstance(response_data, list):
            return [AccountResponse(**account) for account in response_data]
        # If single object, wrap in list
        return [AccountResponse(**response_data)]

    def refresh_balance(self, account_id: str, asset: str) -> RefreshBalanceResponse:
        """Refresh balance for a specific account and asset.

        Args:
            account_id: Account ID
            asset: Asset identifier

        Returns:
            RefreshBalanceResponse containing message and idempotency key

        Raises:
            DiagonAPIClientError: If API call fails
        """
        req_path = f"{BASE_ACCOUNTS_PATH}{PATH_SEPARATOR}{account_id}{PATH_SEPARATOR}{asset}/balance"
        response_data = self._agent.post(req_path=req_path)
        return RefreshBalanceResponse(**response_data)

    def estimate_fee(self, request: EstimateFeeRequest) -> EstimateFeeResponse:
        """Estimate transaction fee.

        Args:
            request: EstimateFeeRequest containing operation, source, destination, assetId, and amount

        Returns:
            EstimateFeeResponse containing fee estimates for low, medium, and high priority

        Raises:
            DiagonAPIClientError: If API call fails
        """
        req_path = f"{BASE_VAULT_TRANSACTIONS_PATH}/estimate-fee"
        request_dict = request.model_dump(by_alias=True)
        response_data = self._agent.post(req_path=req_path, json=request_dict)
        return EstimateFeeResponse(**response_data)

    def get_external_wallets(self) -> list[ExternalWallet] | ExternalWalletsEmptyResponse:
        """Get external wallets from Diagon API.

        Returns:
            List of ExternalWallet objects when wallets exist, or
            ExternalWalletsEmptyResponse when no wallets found.

        Raises:
            DiagonAPIClientError: If API call fails
        """
        response_data = self._agent.get_external_wallets()
        # Handle response when no wallets found (dict with message, code, data)
        if isinstance(response_data, dict) and "data" in response_data:
            return ExternalWalletsEmptyResponse(**response_data)
        # Handle response when wallets exist (list of wallets)
        if isinstance(response_data, list):
            return [ExternalWallet(**wallet) for wallet in response_data]
        # If single object, wrap in list
        return [ExternalWallet(**response_data)]

    def vault_to_vault(self, request: VaultToVaultRequest) -> VaultToVaultResponse:
        """Create a vault-to-vault transaction.

        Args:
            request: VaultToVaultRequest containing network, service, token,
                sourceVaultId, destinationWalletId, feeLevel, and amount

        Returns:
            VaultToVaultResponse containing transaction id and status

        Raises:
            DiagonAPIClientError: If API call fails
        """
        req_path = f"{BASE_TRANSACTIONS_PATH}/vault-to-vault"
        request_dict = request.model_dump(by_alias=True)
        response_data = self._agent.post(req_path=req_path, json=request_dict)
        return VaultToVaultResponse(**response_data)
