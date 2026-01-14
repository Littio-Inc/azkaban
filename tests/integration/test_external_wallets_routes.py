"""Integration tests for external wallets routes."""

import unittest
from unittest.mock import patch

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.common.apis.cassandra.dtos import ExternalWalletResponse
from app.middleware.auth import get_current_user
from app.routes.monetization_routes import router


class TestExternalWalletsRoutes(unittest.TestCase):
    """Test cases for external wallets routes."""

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

    @patch("app.routes.monetization_routes.MonetizationService")
    def test_get_external_wallets_success(self, mock_service_class):
        """Test getting external wallets successfully."""
        self.app.dependency_overrides[get_current_user] = lambda: self.mock_current_user

        mock_wallets_data = [
            ExternalWalletResponse(
                id="2f4d0fad-185a-49b5-88d9-bf8c1c45c626",
                external_wallet_id="123e4567-e89b-12d3-a456-426614174000",
                asset_id=None,
                asset_address=None,
                asset_tag=None,
                name="Vault Wallet Principal 2",
                category="VAULT",
                provider="FIREBLOCKS",
                supplier_prefunding=True,
                b2c_funding=True,
                enabled=True,
                created_at="2026-01-14T16:53:32.251713+00:00",
                updated_at="2026-01-14T16:54:21.397067+00:00",
            ),
            ExternalWalletResponse(
                id="11a3c035-c462-43bb-b4e0-4ede8ff80d76",
                external_wallet_id="123e4567-e89b-12d3-a456-426614174001",
                asset_id="USDC_AMOY_POLYGON_TEST_7WWV",
                asset_address="0xDC8B0E600d38496F4ed07995ECa37a834FbdC73A",
                asset_tag="",
                name="Vault Wallet Principal",
                category="OTC",
                provider="FIREBLOCKS",
                supplier_prefunding=True,
                b2c_funding=False,
                enabled=False,
                created_at="2026-01-14T17:10:01.841814+00:00",
                updated_at="2026-01-14T17:10:19.113699+00:00",
            ),
        ]

        mock_service_class.get_external_wallets.return_value = mock_wallets_data

        response = self.client.get("/v1/external-wallets")

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("wallets", data)
        self.assertEqual(len(data["wallets"]), 2)
        self.assertEqual(data["wallets"][0]["id"], "2f4d0fad-185a-49b5-88d9-bf8c1c45c626")
        self.assertEqual(data["wallets"][0]["category"], "VAULT")
        # Verify new fields are included in response
        self.assertIn("asset_id", data["wallets"][0])
        self.assertIn("asset_address", data["wallets"][0])
        self.assertIn("asset_tag", data["wallets"][0])
        self.assertIsNone(data["wallets"][0]["asset_id"])
        # Verify second wallet has asset fields populated
        self.assertEqual(data["wallets"][1]["asset_id"], "USDC_AMOY_POLYGON_TEST_7WWV")
        self.assertEqual(data["wallets"][1]["asset_address"], "0xDC8B0E600d38496F4ed07995ECa37a834FbdC73A")
        self.assertEqual(data["wallets"][1]["asset_tag"], "")
        mock_service_class.get_external_wallets.assert_called_once()

    @patch("app.routes.monetization_routes.MonetizationService")
    def test_get_external_wallets_configuration_error(self, mock_service_class):
        """Test getting external wallets when configuration error occurs."""
        self.app.dependency_overrides[get_current_user] = lambda: self.mock_current_user

        from app.common.errors import MissingCredentialsError
        mock_service_class.get_external_wallets.side_effect = MissingCredentialsError(
            "CASSANDRA_API_KEY not found in secrets"
        )

        response = self.client.get("/v1/external-wallets")

        self.assertEqual(response.status_code, 500)
        data = response.json()
        self.assertIn("configuration error", data["detail"].lower())

    @patch("app.routes.monetization_routes.MonetizationService")
    def test_get_external_wallets_api_error(self, mock_service_class):
        """Test getting external wallets when API error occurs."""
        self.app.dependency_overrides[get_current_user] = lambda: self.mock_current_user

        from app.common.apis.cassandra.errors import CassandraAPIClientError
        mock_service_class.get_external_wallets.side_effect = CassandraAPIClientError(
            "Error calling Cassandra API",
            status_code=502,
            error_detail={"error": {"message": "Service unavailable", "code": "SERVICE_ERROR"}},
        )

        response = self.client.get("/v1/external-wallets")

        self.assertEqual(response.status_code, 502)
        data = response.json()
        self.assertIn("error", data["detail"])

    @patch("app.routes.monetization_routes.MonetizationService")
    def test_create_external_wallet_success(self, mock_service_class):
        """Test creating external wallet successfully."""
        self.app.dependency_overrides[get_current_user] = lambda: self.mock_current_user

        wallet_id = "2f4d0fad-185a-49b5-88d9-bf8c1c45c626"
        mock_wallet_response = ExternalWalletResponse(
            id=wallet_id,
            external_wallet_id="123e4567-e89b-12d3-a456-426614174001",
            asset_id="USDC_AMOY_POLYGON_TEST_7WWV",
            asset_address="0xDC8B0E600d38496F4ed07995ECa37a834FbdC73A",
            asset_tag="",
            name="Vault Wallet Principal",
            category="OTC",
            provider="FIREBLOCKS",
            supplier_prefunding=True,
            b2c_funding=False,
            enabled=True,
            created_at="2026-01-14T17:10:01.841814+00:00",
            updated_at="2026-01-14T17:10:01.841814+00:00",
        )

        mock_service_class.create_external_wallet.return_value = mock_wallet_response

        wallet_data = {
            "external_wallet_id": "123e4567-e89b-12d3-a456-426614174001",
            "asset_id": "USDC_AMOY_POLYGON_TEST_7WWV",
            "asset_address": "0xDC8B0E600d38496F4ed07995ECa37a834FbdC73A",
            "asset_tag": "",
            "name": "Vault Wallet Principal",
            "category": "OTC",
            "provider": "FIREBLOCKS",
            "supplier_prefunding": True,
            "b2c_funding": False,
            "enabled": True,
        }

        response = self.client.post("/v1/external-wallets", json=wallet_data)

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["id"], wallet_id)
        self.assertEqual(data["category"], "OTC")
        # Verify new fields are included in response
        self.assertEqual(data["asset_id"], "USDC_AMOY_POLYGON_TEST_7WWV")
        self.assertEqual(data["asset_address"], "0xDC8B0E600d38496F4ed07995ECa37a834FbdC73A")
        self.assertEqual(data["asset_tag"], "")
        mock_service_class.create_external_wallet.assert_called_once()

    @patch("app.routes.monetization_routes.MonetizationService")
    def test_create_external_wallet_api_error(self, mock_service_class):
        """Test creating external wallet when API error occurs."""
        self.app.dependency_overrides[get_current_user] = lambda: self.mock_current_user

        from app.common.apis.cassandra.errors import CassandraAPIClientError
        mock_service_class.create_external_wallet.side_effect = CassandraAPIClientError(
            "Error calling Cassandra API",
            status_code=400,
            error_detail={"error": {"message": "Invalid data", "code": "VALIDATION_ERROR"}},
        )

        wallet_data = {
            "external_wallet_id": "123e4567-e89b-12d3-a456-426614174001",
            "name": "Vault Wallet Principal",
            "category": "OTC",
            "supplier_prefunding": True,
            "b2c_funding": False,
            "enabled": True,
        }

        response = self.client.post("/v1/external-wallets", json=wallet_data)

        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertIn("error", data["detail"])

    @patch("app.routes.monetization_routes.MonetizationService")
    def test_update_external_wallet_success(self, mock_service_class):
        """Test updating external wallet successfully."""
        self.app.dependency_overrides[get_current_user] = lambda: self.mock_current_user

        wallet_id = "2f4d0fad-185a-49b5-88d9-bf8c1c45c626"
        mock_wallet_response = ExternalWalletResponse(
            id=wallet_id,
            external_wallet_id="123e4567-e89b-12d3-a456-426614174000",
            asset_id="USDC_AMOY_POLYGON_TEST_7WWV",
            asset_address="0xDC8B0E600d38496F4ed07995ECa37a834FbdC73A",
            asset_tag="",
            name="Vault Wallet Principal 2",
            category="VAULT",
            provider="FIREBLOCKS",
            supplier_prefunding=True,
            b2c_funding=True,
            enabled=True,
            created_at="2026-01-14T16:53:32.251713+00:00",
            updated_at="2026-01-14T16:54:21.397067+00:00",
        )

        mock_service_class.update_external_wallet.return_value = mock_wallet_response

        wallet_data = {
            "asset_id": "USDC_AMOY_POLYGON_TEST_7WWV",
            "asset_address": "0xDC8B0E600d38496F4ed07995ECa37a834FbdC73A",
            "asset_tag": "",
            "name": "Vault Wallet Principal 2",
            "category": "VAULT",
            "provider": "FIREBLOCKS",
            "supplier_prefunding": True,
            "b2c_funding": True,
            "enabled": True,
        }

        response = self.client.put(f"/v1/external-wallets/{wallet_id}", json=wallet_data)

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["id"], wallet_id)
        self.assertEqual(data["name"], "Vault Wallet Principal 2")
        self.assertEqual(data["category"], "VAULT")
        # Verify new fields are included in response
        self.assertEqual(data["asset_id"], "USDC_AMOY_POLYGON_TEST_7WWV")
        self.assertEqual(data["asset_address"], "0xDC8B0E600d38496F4ed07995ECa37a834FbdC73A")
        self.assertEqual(data["asset_tag"], "")
        mock_service_class.update_external_wallet.assert_called_once()

    @patch("app.routes.monetization_routes.MonetizationService")
    def test_update_external_wallet_api_error(self, mock_service_class):
        """Test updating external wallet when API error occurs."""
        self.app.dependency_overrides[get_current_user] = lambda: self.mock_current_user

        from app.common.apis.cassandra.errors import CassandraAPIClientError
        mock_service_class.update_external_wallet.side_effect = CassandraAPIClientError(
            "Error calling Cassandra API",
            status_code=404,
            error_detail={"error": {"message": "Wallet not found", "code": "NOT_FOUND"}},
        )

        wallet_id = "2f4d0fad-185a-49b5-88d9-bf8c1c45c626"
        wallet_data = {
            "name": "Updated Wallet",
            "enabled": False,
        }

        response = self.client.put(f"/v1/external-wallets/{wallet_id}", json=wallet_data)

        self.assertEqual(response.status_code, 404)
        data = response.json()
        self.assertIn("error", data["detail"])

    @patch("app.routes.monetization_routes.MonetizationService")
    def test_delete_external_wallet_success(self, mock_service_class):
        """Test deleting external wallet successfully."""
        self.app.dependency_overrides[get_current_user] = lambda: self.mock_current_user

        wallet_id = "11a3c035-c462-43bb-b4e0-4ede8ff80d76"
        mock_service_class.delete_external_wallet.return_value = None

        response = self.client.delete(f"/v1/external-wallets/{wallet_id}")

        self.assertEqual(response.status_code, 204)
        mock_service_class.delete_external_wallet.assert_called_once_with(wallet_id=wallet_id)

    @patch("app.routes.monetization_routes.MonetizationService")
    def test_delete_external_wallet_api_error(self, mock_service_class):
        """Test deleting external wallet when API error occurs."""
        self.app.dependency_overrides[get_current_user] = lambda: self.mock_current_user

        from app.common.apis.cassandra.errors import CassandraAPIClientError
        mock_service_class.delete_external_wallet.side_effect = CassandraAPIClientError(
            "Error calling Cassandra API",
            status_code=404,
            error_detail={"error": {"message": "Wallet not found", "code": "NOT_FOUND"}},
        )

        wallet_id = "11a3c035-c462-43bb-b4e0-4ede8ff80d76"

        response = self.client.delete(f"/v1/external-wallets/{wallet_id}")

        self.assertEqual(response.status_code, 404)
        data = response.json()
        self.assertIn("error", data["detail"])

    @patch("app.routes.monetization_routes.MonetizationService")
    def test_get_external_wallets_empty_list(self, mock_service_class):
        """Test getting external wallets when list is empty."""
        self.app.dependency_overrides[get_current_user] = lambda: self.mock_current_user

        mock_service_class.get_external_wallets.return_value = []

        response = self.client.get("/v1/external-wallets")

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("wallets", data)
        self.assertEqual(len(data["wallets"]), 0)

    @patch("app.routes.monetization_routes.MonetizationService")
    def test_get_external_wallets_generic_error(self, mock_service_class):
        """Test getting external wallets when generic error occurs."""
        self.app.dependency_overrides[get_current_user] = lambda: self.mock_current_user

        mock_service_class.get_external_wallets.side_effect = Exception("Network error")

        response = self.client.get("/v1/external-wallets")

        self.assertEqual(response.status_code, 502)
        data = response.json()
        self.assertIn("error", data["detail"])

    @patch("app.routes.monetization_routes.MonetizationService")
    def test_create_external_wallet_generic_error(self, mock_service_class):
        """Test creating external wallet when generic error occurs."""
        self.app.dependency_overrides[get_current_user] = lambda: self.mock_current_user

        mock_service_class.create_external_wallet.side_effect = Exception("Network error")

        wallet_data = {
            "external_wallet_id": "123e4567-e89b-12d3-a456-426614174001",
            "name": "Vault Wallet Principal",
            "category": "OTC",
            "supplier_prefunding": True,
            "b2c_funding": False,
            "enabled": True,
        }

        response = self.client.post("/v1/external-wallets", json=wallet_data)

        self.assertEqual(response.status_code, 502)
        data = response.json()
        self.assertIn("error", data["detail"])

    @patch("app.routes.monetization_routes.MonetizationService")
    def test_update_external_wallet_generic_error(self, mock_service_class):
        """Test updating external wallet when generic error occurs."""
        self.app.dependency_overrides[get_current_user] = lambda: self.mock_current_user

        mock_service_class.update_external_wallet.side_effect = Exception("Network error")

        wallet_id = "2f4d0fad-185a-49b5-88d9-bf8c1c45c626"
        wallet_data = {
            "name": "Updated Wallet",
            "enabled": False,
        }

        response = self.client.put(f"/v1/external-wallets/{wallet_id}", json=wallet_data)

        self.assertEqual(response.status_code, 502)
        data = response.json()
        self.assertIn("error", data["detail"])

    @patch("app.routes.monetization_routes.MonetizationService")
    def test_delete_external_wallet_generic_error(self, mock_service_class):
        """Test deleting external wallet when generic error occurs."""
        self.app.dependency_overrides[get_current_user] = lambda: self.mock_current_user

        mock_service_class.delete_external_wallet.side_effect = Exception("Network error")

        wallet_id = "11a3c035-c462-43bb-b4e0-4ede8ff80d76"

        response = self.client.delete(f"/v1/external-wallets/{wallet_id}")

        self.assertEqual(response.status_code, 502)
        data = response.json()
        self.assertIn("error", data["detail"])


if __name__ == "__main__":
    unittest.main()
