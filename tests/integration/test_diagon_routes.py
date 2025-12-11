"""Integration tests for Diagon routes."""

import unittest
from unittest.mock import patch

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.common.apis.diagon.dtos import (
    AccountResponse,
    EstimateFeeRequest,
    EstimateFeeResponse,
    ExternalWallet,
    ExternalWalletsEmptyResponse,
    RefreshBalanceResponse,
)
from app.middleware.auth import get_current_user
from app.routes.diagon_routes import router


class TestDiagonRoutes(unittest.TestCase):
    """Test cases for Diagon routes."""

    def setUp(self):
        """Set up test fixtures."""
        self.app = FastAPI()
        self.app.include_router(router, prefix="/v1")
        self.client = TestClient(self.app)
        self.mock_current_user = {
            "firebase_uid": "user-uid-123",
            "email": "user@littio.co",
            "name": "Test User",
            "picture": None,
        }

    def tearDown(self):
        """Clean up after each test."""
        # Clear dependency overrides after each test
        self.app.dependency_overrides.clear()

    @patch("app.routes.diagon_routes.DiagonClient")
    def test_get_vault_accounts_success(self, mock_diagon_service):
        """Test getting vault accounts successfully."""
        self.app.dependency_overrides[get_current_user] = lambda: self.mock_current_user

        mock_accounts_data = [
            {
                "id": "6",
                "name": "Test2",
                "hiddenOnUI": False,
                "autoFuel": False,
                "assets": []
            },
            {
                "id": "5",
                "name": "Littio-Test",
                "hiddenOnUI": False,
                "autoFuel": False,
                "assets": [
                    {
                        "id": "AMOY_POLYGON_TEST",
                        "total": "0.2",
                        "balance": "0.2",
                        "lockedAmount": "0",
                        "available": "0.2",
                        "pending": "0",
                        "frozen": "0",
                        "staked": "0",
                        "blockHeight": "17182897",
                        "blockHash": "0xbd4b5221dbded68a6c76f809b31f87732b29e2972bf0d9075d2e09e3e2a46fcd"
                    }
                ]
            }
        ]

        mock_client = mock_diagon_service.return_value
        mock_client.get_accounts.return_value = [AccountResponse(**account) for account in mock_accounts_data]

        response = self.client.get("/v1/vault/accounts")

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(len(data), 2)
        self.assertEqual(data[0]["id"], "6")
        self.assertEqual(data[0]["name"], "Test2")
        self.assertEqual(data[1]["id"], "5")
        self.assertEqual(data[1]["name"], "Littio-Test")
        self.assertEqual(len(data[1]["assets"]), 1)
        mock_client.get_accounts.assert_called_once()

    @patch("app.routes.diagon_routes.DiagonClient")
    def test_get_vault_accounts_configuration_error(self, mock_diagon_service):
        """Test getting accounts when configuration error occurs."""
        self.app.dependency_overrides[get_current_user] = lambda: self.mock_current_user

        from app.common.apis.diagon.errors import DiagonAPIClientError
        mock_client = mock_diagon_service.return_value
        mock_client.get_accounts.side_effect = DiagonAPIClientError("DIAGON_API_KEY not found in secrets")

        response = self.client.get("/v1/vault/accounts")

        self.assertEqual(response.status_code, 502)
        data = response.json()
        self.assertIn("error retrieving accounts", data["detail"].lower())

    @patch("app.routes.diagon_routes.DiagonClient")
    def test_get_vault_accounts_generic_error(self, mock_diagon_service):
        """Test getting accounts when generic error occurs."""
        self.app.dependency_overrides[get_current_user] = lambda: self.mock_current_user

        mock_client = mock_diagon_service.return_value
        mock_client.get_accounts.side_effect = Exception("Network error")

        response = self.client.get("/v1/vault/accounts")

        self.assertEqual(response.status_code, 502)
        data = response.json()
        self.assertIn("error retrieving accounts", data["detail"].lower())

    @patch("app.routes.diagon_routes.DiagonClient")
    def test_get_vault_accounts_empty_list(self, mock_diagon_service):
        """Test getting accounts when empty list is returned."""
        self.app.dependency_overrides[get_current_user] = lambda: self.mock_current_user

        mock_client = mock_diagon_service.return_value
        mock_client.get_accounts.return_value = []

        response = self.client.get("/v1/vault/accounts")

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data, [])
        mock_client.get_accounts.assert_called_once()

    @patch("app.routes.diagon_routes.DiagonClient")
    def test_refresh_balance_success(self, mock_diagon_service):
        """Test refreshing balance successfully."""
        self.app.dependency_overrides[get_current_user] = lambda: self.mock_current_user

        account_id = "5"
        asset = "USDC_AMOY_POLYGON_TEST_7WWV"
        mock_response_data = {
            "message": "Balance refresh initiated successfully",
            "idempotencyKey": "1a70d158-f499-427d-9337-745be60113b1"
        }

        mock_client = mock_diagon_service.return_value
        mock_client.refresh_balance.return_value = RefreshBalanceResponse(**mock_response_data)

        response = self.client.post(f"/v1/vault/accounts/{account_id}/{asset}/balance")

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["message"], "Balance refresh initiated successfully")
        self.assertEqual(data["idempotencyKey"], "1a70d158-f499-427d-9337-745be60113b1")
        mock_client.refresh_balance.assert_called_once_with(account_id, asset)

    @patch("app.routes.diagon_routes.DiagonClient")
    def test_refresh_balance_configuration_error(self, mock_diagon_service):
        """Test refreshing balance when configuration error occurs."""
        self.app.dependency_overrides[get_current_user] = lambda: self.mock_current_user

        account_id = "5"
        asset = "USDC_AMOY_POLYGON_TEST_7WWV"
        from app.common.apis.diagon.errors import DiagonAPIClientError
        mock_client = mock_diagon_service.return_value
        mock_client.refresh_balance.side_effect = DiagonAPIClientError("DIAGON_API_KEY not found in secrets")

        response = self.client.post(f"/v1/vault/accounts/{account_id}/{asset}/balance")

        self.assertEqual(response.status_code, 502)
        data = response.json()
        self.assertIn("error refreshing balance", data["detail"].lower())

    @patch("app.routes.diagon_routes.DiagonClient")
    def test_refresh_balance_generic_error(self, mock_diagon_service):
        """Test refreshing balance when generic error occurs."""
        self.app.dependency_overrides[get_current_user] = lambda: self.mock_current_user

        account_id = "5"
        asset = "USDC_AMOY_POLYGON_TEST_7WWV"
        mock_client = mock_diagon_service.return_value
        mock_client.refresh_balance.side_effect = Exception("Network error")

        response = self.client.post(f"/v1/vault/accounts/{account_id}/{asset}/balance")

        self.assertEqual(response.status_code, 502)
        data = response.json()
        self.assertIn("error refreshing balance", data["detail"].lower())

    @patch("app.routes.diagon_routes.DiagonClient")
    def test_estimate_fee_success(self, mock_diagon_service):
        """Test estimating fee successfully."""
        self.app.dependency_overrides[get_current_user] = lambda: self.mock_current_user

        mock_response_data = {
            "low": {
                "networkFee": "0.001432725180253028",
                "gasPrice": "26.276",
                "gasLimit": "54526",
                "baseFee": "0.000000063",
                "priorityFee": "26.276",
                "l1Fee": "0",
                "maxFeePerGasDelta": "0.000000015"
            },
            "medium": {
                "networkFee": "0.001589651008253028",
                "gasPrice": "29.154",
                "gasLimit": "54526",
                "baseFee": "0.000000063",
                "priorityFee": "29.154",
                "l1Fee": "0",
                "maxFeePerGasDelta": "0.000000015"
            },
            "high": {
                "networkFee": "0.001746522310253028",
                "gasPrice": "32.032",
                "gasLimit": "54526",
                "baseFee": "0.000000063",
                "priorityFee": "32.031",
                "l1Fee": "0",
                "maxFeePerGasDelta": "0.000000015"
            }
        }

        mock_client = mock_diagon_service.return_value
        mock_client.estimate_fee.return_value = EstimateFeeResponse(**mock_response_data)

        request_data = {
            "operation": "TRANSFER",
            "source": {
                "type": "VAULT_ACCOUNT",
                "id": "5"
            },
            "destination": {
                "type": "VAULT_ACCOUNT",
                "id": "3"
            },
            "assetId": "USDC_AMOY_POLYGON_TEST_7WWV",
            "amount": "1"
        }

        response = self.client.post("/v1/vault/transactions/estimate-fee", json=request_data)

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["low"]["networkFee"], "0.001432725180253028")
        self.assertEqual(data["medium"]["gasPrice"], "29.154")
        self.assertEqual(data["high"]["priorityFee"], "32.031")
        mock_client.estimate_fee.assert_called_once()
        call_args = mock_client.estimate_fee.call_args
        request_obj = call_args[0][0]
        self.assertIsInstance(request_obj, EstimateFeeRequest)
        self.assertEqual(request_obj.operation, "TRANSFER")
        self.assertEqual(request_obj.assetId, "USDC_AMOY_POLYGON_TEST_7WWV")
        self.assertEqual(request_obj.amount, "1")

    @patch("app.routes.diagon_routes.DiagonClient")
    def test_estimate_fee_configuration_error(self, mock_diagon_service):
        """Test estimating fee when configuration error occurs."""
        self.app.dependency_overrides[get_current_user] = lambda: self.mock_current_user

        from app.common.apis.diagon.errors import DiagonAPIClientError
        mock_client = mock_diagon_service.return_value
        mock_client.estimate_fee.side_effect = DiagonAPIClientError("DIAGON_API_KEY not found in secrets")

        request_data = {
            "operation": "TRANSFER",
            "source": {
                "type": "VAULT_ACCOUNT",
                "id": "5"
            },
            "destination": {
                "type": "VAULT_ACCOUNT",
                "id": "3"
            },
            "assetId": "USDC_AMOY_POLYGON_TEST_7WWV",
            "amount": "1"
        }

        response = self.client.post("/v1/vault/transactions/estimate-fee", json=request_data)

        self.assertEqual(response.status_code, 502)
        data = response.json()
        self.assertIn("error estimating fee", data["detail"].lower())

    @patch("app.routes.diagon_routes.DiagonClient")
    def test_estimate_fee_generic_error(self, mock_diagon_service):
        """Test estimating fee when generic error occurs."""
        self.app.dependency_overrides[get_current_user] = lambda: self.mock_current_user

        mock_client = mock_diagon_service.return_value
        mock_client.estimate_fee.side_effect = Exception("Network error")

        request_data = {
            "operation": "TRANSFER",
            "source": {
                "type": "VAULT_ACCOUNT",
                "id": "5"
            },
            "destination": {
                "type": "VAULT_ACCOUNT",
                "id": "3"
            },
            "assetId": "USDC_AMOY_POLYGON_TEST_7WWV",
            "amount": "1"
        }

        response = self.client.post("/v1/vault/transactions/estimate-fee", json=request_data)

        self.assertEqual(response.status_code, 502)
        data = response.json()
        self.assertIn("error estimating fee", data["detail"].lower())

    @patch("app.routes.diagon_routes.DiagonClient")
    def test_get_external_wallets_success(self, mock_diagon_service):
        """Test getting external wallets successfully."""
        self.app.dependency_overrides[get_current_user] = lambda: self.mock_current_user

        mock_wallets_data = [
            {
                "id": "wallet-1",
                "name": "Test Wallet",
                "customerRefId": "customer-123",
                "assets": [
                    {
                        "id": "USDC_POLYGON",
                        "balance": "100.0",
                        "lockedAmount": "0",
                        "status": "WAITING_FOR_APPROVAL",
                        "address": "0x1234567890abcdef",
                        "tag": "",
                        "activationTime": "2024-01-01T00:00:00Z"
                    }
                ]
            }
        ]

        mock_client = mock_diagon_service.return_value
        mock_client.get_external_wallets.return_value = [ExternalWallet(**wallet) for wallet in mock_wallets_data]

        response = self.client.get("/v1/vault/external-wallets")

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]["id"], "wallet-1")
        self.assertEqual(data[0]["name"], "Test Wallet")
        self.assertEqual(data[0]["customerRefId"], "customer-123")
        self.assertEqual(len(data[0]["assets"]), 1)
        self.assertEqual(data[0]["assets"][0]["id"], "USDC_POLYGON")
        self.assertEqual(data[0]["assets"][0]["balance"], "100.0")
        self.assertEqual(data[0]["assets"][0]["status"], "WAITING_FOR_APPROVAL")
        mock_client.get_external_wallets.assert_called_once()

    @patch("app.routes.diagon_routes.DiagonClient")
    def test_get_external_wallets_empty(self, mock_diagon_service):
        """Test getting external wallets when no wallets found."""
        self.app.dependency_overrides[get_current_user] = lambda: self.mock_current_user

        mock_client = mock_diagon_service.return_value
        empty_response = ExternalWalletsEmptyResponse(
            message="No external wallets found",
            code=0,
            data=[]
        )
        mock_client.get_external_wallets.return_value = empty_response

        response = self.client.get("/v1/vault/external-wallets")

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["message"], "No external wallets found")
        self.assertEqual(data["code"], 0)
        self.assertEqual(data["data"], [])
        mock_client.get_external_wallets.assert_called_once()

    @patch("app.routes.diagon_routes.DiagonClient")
    def test_get_external_wallets_configuration_error(self, mock_diagon_service):
        """Test getting external wallets when configuration error occurs."""
        self.app.dependency_overrides[get_current_user] = lambda: self.mock_current_user

        from app.common.apis.diagon.errors import DiagonAPIClientError
        mock_client = mock_diagon_service.return_value
        mock_client.get_external_wallets.side_effect = DiagonAPIClientError("DIAGON_API_KEY not found in secrets")

        response = self.client.get("/v1/vault/external-wallets")

        self.assertEqual(response.status_code, 502)
        data = response.json()
        self.assertIn("error retrieving external wallets", data["detail"].lower())

    @patch("app.routes.diagon_routes.DiagonClient")
    def test_get_external_wallets_generic_error(self, mock_diagon_service):
        """Test getting external wallets when generic error occurs."""
        self.app.dependency_overrides[get_current_user] = lambda: self.mock_current_user

        mock_client = mock_diagon_service.return_value
        mock_client.get_external_wallets.side_effect = Exception("Network error")

        response = self.client.get("/v1/vault/external-wallets")

        self.assertEqual(response.status_code, 502)
        data = response.json()
        self.assertIn("error retrieving external wallets", data["detail"].lower())


if __name__ == "__main__":
    unittest.main()

