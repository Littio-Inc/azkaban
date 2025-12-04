"""Integration tests for Diagon routes."""

import unittest
from unittest.mock import patch

from fastapi import FastAPI
from fastapi.testclient import TestClient

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

    @patch("app.routes.diagon_routes.DiagonService")
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

        mock_diagon_service.get_accounts.return_value = mock_accounts_data

        response = self.client.get("/v1/vault/accounts")

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(len(data), 2)
        self.assertEqual(data[0]["id"], "6")
        self.assertEqual(data[0]["name"], "Test2")
        self.assertEqual(data[1]["id"], "5")
        self.assertEqual(data[1]["name"], "Littio-Test")
        self.assertEqual(len(data[1]["assets"]), 1)
        mock_diagon_service.get_accounts.assert_called_once()

    @patch("app.routes.diagon_routes.DiagonService")
    def test_get_vault_accounts_configuration_error(self, mock_diagon_service):
        """Test getting accounts when configuration error occurs."""
        self.app.dependency_overrides[get_current_user] = lambda: self.mock_current_user

        mock_diagon_service.get_accounts.side_effect = ValueError("DIAGON_API_KEY not found in secrets")

        response = self.client.get("/v1/vault/accounts")

        self.assertEqual(response.status_code, 500)
        data = response.json()
        self.assertIn("configuration error", data["detail"].lower())

    @patch("app.routes.diagon_routes.DiagonService")
    def test_get_vault_accounts_generic_error(self, mock_diagon_service):
        """Test getting accounts when generic error occurs."""
        self.app.dependency_overrides[get_current_user] = lambda: self.mock_current_user

        mock_diagon_service.get_accounts.side_effect = Exception("Network error")

        response = self.client.get("/v1/vault/accounts")

        self.assertEqual(response.status_code, 502)
        data = response.json()
        self.assertIn("error retrieving accounts", data["detail"].lower())

    @patch("app.routes.diagon_routes.DiagonService")
    def test_get_vault_accounts_empty_list(self, mock_diagon_service):
        """Test getting accounts when empty list is returned."""
        self.app.dependency_overrides[get_current_user] = lambda: self.mock_current_user

        mock_diagon_service.get_accounts.return_value = []

        response = self.client.get("/v1/vault/accounts")

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data, [])
        mock_diagon_service.get_accounts.assert_called_once()

    @patch("app.routes.diagon_routes.DiagonService")
    def test_refresh_balance_success(self, mock_diagon_service):
        """Test refreshing balance successfully."""
        self.app.dependency_overrides[get_current_user] = lambda: self.mock_current_user

        account_id = "5"
        asset = "USDC_AMOY_POLYGON_TEST_7WWV"
        mock_response_data = {
            "message": "Balance refresh initiated successfully",
            "idempotencyKey": "1a70d158-f499-427d-9337-745be60113b1"
        }

        mock_diagon_service.refresh_balance.return_value = mock_response_data

        response = self.client.post(f"/v1/vault/accounts/{account_id}/{asset}/balance")

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["message"], "Balance refresh initiated successfully")
        self.assertEqual(data["idempotencyKey"], "1a70d158-f499-427d-9337-745be60113b1")
        mock_diagon_service.refresh_balance.assert_called_once_with(account_id, asset)

    @patch("app.routes.diagon_routes.DiagonService")
    def test_refresh_balance_configuration_error(self, mock_diagon_service):
        """Test refreshing balance when configuration error occurs."""
        self.app.dependency_overrides[get_current_user] = lambda: self.mock_current_user

        account_id = "5"
        asset = "USDC_AMOY_POLYGON_TEST_7WWV"
        mock_diagon_service.refresh_balance.side_effect = ValueError("DIAGON_API_KEY not found in secrets")

        response = self.client.post(f"/v1/vault/accounts/{account_id}/{asset}/balance")

        self.assertEqual(response.status_code, 500)
        data = response.json()
        self.assertIn("configuration error", data["detail"].lower())

    @patch("app.routes.diagon_routes.DiagonService")
    def test_refresh_balance_generic_error(self, mock_diagon_service):
        """Test refreshing balance when generic error occurs."""
        self.app.dependency_overrides[get_current_user] = lambda: self.mock_current_user

        account_id = "5"
        asset = "USDC_AMOY_POLYGON_TEST_7WWV"
        mock_diagon_service.refresh_balance.side_effect = Exception("Network error")

        response = self.client.post(f"/v1/vault/accounts/{account_id}/{asset}/balance")

        self.assertEqual(response.status_code, 502)
        data = response.json()
        self.assertIn("error refreshing balance", data["detail"].lower())


if __name__ == "__main__":
    unittest.main()

