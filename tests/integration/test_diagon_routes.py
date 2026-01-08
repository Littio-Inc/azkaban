"""Integration tests for Diagon routes."""

import unittest
from unittest.mock import patch

from fastapi import FastAPI
from fastapi.testclient import TestClient
from faker import Faker

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
from app.middleware.auth import get_current_user
from app.routes.diagon_routes import router

fake = Faker()


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
    def test_get_vault_accounts_with_null_block_height(self, mock_diagon_service):
        """Test getting accounts when blockHeight is None in asset."""
        self.app.dependency_overrides[get_current_user] = lambda: self.mock_current_user

        mock_accounts_data = [
            {
                "id": "5",
                "name": "Test Account",
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
                        "blockHeight": None,
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
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]["id"], "5")
        self.assertEqual(len(data[0]["assets"]), 1)
        self.assertIsNone(data[0]["assets"][0]["blockHeight"])
        self.assertEqual(data[0]["assets"][0]["blockHash"], "0xbd4b5221dbded68a6c76f809b31f87732b29e2972bf0d9075d2e09e3e2a46fcd")
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

    @patch("app.routes.diagon_routes.DiagonClient")
    def test_create_transaction_success(self, mock_diagon_service):
        """Test creating transaction successfully."""
        self.app.dependency_overrides[get_current_user] = lambda: self.mock_current_user

        transaction_id = fake.uuid4()
        status = fake.random_element(elements=("SUBMITTED", "PENDING", "COMPLETED"))
        network = fake.random_element(elements=("polygon", "ethereum", "bitcoin"))
        service = fake.random_element(elements=("BLOCKCHAIN_WITHDRAWAL", "BLOCKCHAIN_DEPOSIT"))
        token = fake.random_element(elements=("usdc", "usdt", "eth", "btc"))
        source_vault_id = str(fake.random_int(min=1, max=100))
        destination_wallet_id = fake.hexify(text="0x^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^")
        fee_level = fake.random_element(elements=("HIGH", "MEDIUM", "LOW"))
        amount = str(fake.pydecimal(left_digits=2, right_digits=2, positive=True))

        mock_response_data = {
            "id": transaction_id,
            "status": status
        }

        mock_client = mock_diagon_service.return_value
        mock_client.vault_to_vault.return_value = VaultToVaultResponse(**mock_response_data)

        request_data = {
            "network": network,
            "service": service,
            "token": token,
            "sourceVaultId": source_vault_id,
            "destinationWalletId": destination_wallet_id,
            "feeLevel": fee_level,
            "amount": amount
        }

        response = self.client.post("/v1/vault/transactions/create-transaction", json=request_data)

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["id"], transaction_id)
        self.assertEqual(data["status"], status)
        mock_client.vault_to_vault.assert_called_once()
        call_args = mock_client.vault_to_vault.call_args
        request_obj = call_args[0][0]
        self.assertIsInstance(request_obj, VaultToVaultRequest)
        self.assertEqual(request_obj.network, network)
        self.assertEqual(request_obj.service, service)
        self.assertEqual(request_obj.token, token)
        self.assertEqual(request_obj.sourceVaultId, source_vault_id)
        self.assertEqual(request_obj.destinationWalletId, destination_wallet_id)
        self.assertEqual(request_obj.feeLevel, fee_level)
        self.assertEqual(request_obj.amount, amount)
        # Verify idempotency_key is not passed when not provided
        self.assertEqual(call_args.kwargs.get("idempotency_key"), None)

    @patch("app.routes.diagon_routes.DiagonClient")
    def test_create_transaction_with_idempotency_key(self, mock_diagon_service):
        """Test creating transaction with idempotency-key header."""
        self.app.dependency_overrides[get_current_user] = lambda: self.mock_current_user

        transaction_id = fake.uuid4()
        status = fake.random_element(elements=("SUBMITTED", "PENDING", "COMPLETED"))
        network = fake.random_element(elements=("polygon", "ethereum", "bitcoin"))
        service = fake.random_element(elements=("BLOCKCHAIN_WITHDRAWAL", "BLOCKCHAIN_DEPOSIT"))
        token = fake.random_element(elements=("usdc", "usdt", "eth", "btc"))
        source_vault_id = str(fake.random_int(min=1, max=100))
        destination_wallet_id = fake.hexify(text="0x^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^")
        fee_level = fake.random_element(elements=("HIGH", "MEDIUM", "LOW"))
        amount = str(fake.pydecimal(left_digits=2, right_digits=2, positive=True))
        idempotency_key = fake.uuid4()

        mock_response_data = {
            "id": transaction_id,
            "status": status
        }

        mock_client = mock_diagon_service.return_value
        mock_client.vault_to_vault.return_value = VaultToVaultResponse(**mock_response_data)

        request_data = {
            "network": network,
            "service": service,
            "token": token,
            "sourceVaultId": source_vault_id,
            "destinationWalletId": destination_wallet_id,
            "feeLevel": fee_level,
            "amount": amount
        }

        response = self.client.post(
            "/v1/vault/transactions/create-transaction",
            json=request_data,
            headers={"idempotency-key": idempotency_key}
        )

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["id"], transaction_id)
        self.assertEqual(data["status"], status)
        mock_client.vault_to_vault.assert_called_once()
        call_args = mock_client.vault_to_vault.call_args
        request_obj = call_args[0][0]
        self.assertIsInstance(request_obj, VaultToVaultRequest)
        # Verify idempotency_key is passed from header
        self.assertEqual(call_args.kwargs.get("idempotency_key"), idempotency_key)

    @patch("app.routes.diagon_routes.DiagonClient")
    def test_create_transaction_configuration_error(self, mock_diagon_service):
        """Test creating transaction when configuration error occurs."""
        self.app.dependency_overrides[get_current_user] = lambda: self.mock_current_user

        from app.common.apis.diagon.errors import DiagonAPIClientError
        mock_client = mock_diagon_service.return_value
        mock_client.vault_to_vault.side_effect = DiagonAPIClientError("DIAGON_API_KEY not found in secrets")

        request_data = {
            "network": fake.random_element(elements=("polygon", "ethereum", "bitcoin")),
            "service": fake.random_element(elements=("BLOCKCHAIN_WITHDRAWAL", "BLOCKCHAIN_DEPOSIT")),
            "token": fake.random_element(elements=("usdc", "usdt", "eth", "btc")),
            "sourceVaultId": str(fake.random_int(min=1, max=100)),
            "destinationWalletId": fake.hexify(text="0x^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^"),
            "feeLevel": fake.random_element(elements=("HIGH", "MEDIUM", "LOW")),
            "amount": str(fake.pydecimal(left_digits=2, right_digits=2, positive=True))
        }

        response = self.client.post("/v1/vault/transactions/create-transaction", json=request_data)

        assert response.status_code == 502
        data = response.json()
        assert "error creating transaction" in data["detail"].lower()

    @patch("app.routes.diagon_routes.DiagonClient")
    def test_create_transaction_generic_error(self, mock_diagon_service):
        """Test creating transaction when generic error occurs."""
        self.app.dependency_overrides[get_current_user] = lambda: self.mock_current_user

        mock_client = mock_diagon_service.return_value
        mock_client.vault_to_vault.side_effect = Exception("Network error")

        request_data = {
            "network": fake.random_element(elements=("polygon", "ethereum", "bitcoin")),
            "service": fake.random_element(elements=("BLOCKCHAIN_WITHDRAWAL", "BLOCKCHAIN_DEPOSIT")),
            "token": fake.random_element(elements=("usdc", "usdt", "eth", "btc")),
            "sourceVaultId": str(fake.random_int(min=1, max=100)),
            "destinationWalletId": fake.hexify(text="0x^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^"),
            "feeLevel": fake.random_element(elements=("HIGH", "MEDIUM", "LOW")),
            "amount": str(fake.pydecimal(left_digits=2, right_digits=2, positive=True))
        }

        response = self.client.post("/v1/vault/transactions/create-transaction", json=request_data)

        assert response.status_code == 502
        data = response.json()
        assert "error creating transaction" in data["detail"].lower()


if __name__ == "__main__":
    unittest.main()

