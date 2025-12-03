"""Integration tests for Basilisco routes."""

import unittest
from unittest.mock import patch

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.middleware.admin import get_admin_user
from app.routes.basilisco_routes import router


class TestBasiliscoRoutes(unittest.TestCase):
    """Test cases for Basilisco routes."""

    def setUp(self):
        """Set up test fixtures."""
        self.app = FastAPI()
        self.app.include_router(router, prefix="/v1")
        self.client = TestClient(self.app)
        self.mock_admin_user = {
            "id": "admin-1",
            "firebase_uid": "admin-uid-123",
            "email": "admin@littio.co",
            "name": "Admin User",
            "role": "admin",
            "is_active": True,
        }

    def tearDown(self):
        """Clean up after each test."""
        # Clear dependency overrides after each test
        self.app.dependency_overrides.clear()

    @patch("app.routes.basilisco_routes.BasiliscoService")
    def test_get_backoffice_transactions_success(self, mock_basilisco_service):
        """Test getting backoffice transactions successfully."""
        self.app.dependency_overrides[get_admin_user] = lambda: self.mock_admin_user

        mock_transactions_data = {
            "transactions": [
                {
                    "id": "f5f99656-6b5c-40d9-8d4d-8ab1f7feca98",
                    "transaction_id": "0891c79b-20a6-4daf-a885-331f08b9f8cd",
                    "created_at": "2025-11-28T16:58:16.773000",
                    "type": "transfer",
                    "provider": "fireblocks",
                    "amount": "0.3000",
                    "currency": "USD",
                }
            ],
            "count": 1,
            "total_count": 1,
            "page": 1,
            "limit": 10,
        }

        mock_basilisco_service.get_transactions.return_value = mock_transactions_data

        response = self.client.get("/v1/backoffice/transactions?provider=fireblocks&page=1&limit=10")

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["count"], 1)
        self.assertEqual(len(data["transactions"]), 1)
        mock_basilisco_service.get_transactions.assert_called_once_with(
            provider="fireblocks",
            page=1,
            limit=10
        )

    @patch("app.routes.basilisco_routes.BasiliscoService")
    def test_get_backoffice_transactions_without_provider(self, mock_basilisco_service):
        """Test getting transactions without provider filter."""
        self.app.dependency_overrides[get_admin_user] = lambda: self.mock_admin_user

        mock_transactions_data = {
            "transactions": [],
            "count": 0,
            "total_count": 0,
            "page": 1,
            "limit": 10,
        }

        mock_basilisco_service.get_transactions.return_value = mock_transactions_data

        response = self.client.get("/v1/backoffice/transactions?page=2&limit=20")

        self.assertEqual(response.status_code, 200)
        mock_basilisco_service.get_transactions.assert_called_once_with(
            provider=None,
            page=2,
            limit=20
        )

    @patch("app.routes.basilisco_routes.BasiliscoService")
    def test_get_backoffice_transactions_configuration_error(self, mock_basilisco_service):
        """Test getting transactions when configuration error occurs."""
        self.app.dependency_overrides[get_admin_user] = lambda: self.mock_admin_user

        mock_basilisco_service.get_transactions.side_effect = ValueError("BASILISCO_API_KEY not found in secrets")

        response = self.client.get("/v1/backoffice/transactions")

        self.assertEqual(response.status_code, 500)
        data = response.json()
        self.assertIn("configuration error", data["detail"].lower())

    @patch("app.routes.basilisco_routes.BasiliscoService")
    def test_get_backoffice_transactions_generic_error(self, mock_basilisco_service):
        """Test getting transactions when generic error occurs."""
        self.app.dependency_overrides[get_admin_user] = lambda: self.mock_admin_user

        mock_basilisco_service.get_transactions.side_effect = Exception("Network error")

        response = self.client.get("/v1/backoffice/transactions")

        self.assertEqual(response.status_code, 502)
        data = response.json()
        self.assertIn("error retrieving transactions", data["detail"].lower())

    @patch("app.routes.basilisco_routes.BasiliscoService")
    def test_get_backoffice_transactions_default_params(self, mock_basilisco_service):
        """Test getting transactions with default parameters."""
        self.app.dependency_overrides[get_admin_user] = lambda: self.mock_admin_user

        mock_transactions_data = {
            "transactions": [],
            "count": 0,
            "page": 1,
            "limit": 10,
        }

        mock_basilisco_service.get_transactions.return_value = mock_transactions_data

        response = self.client.get("/v1/backoffice/transactions")

        self.assertEqual(response.status_code, 200)
        mock_basilisco_service.get_transactions.assert_called_once_with(
            provider=None,
            page=1,
            limit=10
        )


if __name__ == "__main__":
    unittest.main()
