"""Integration tests for Basilisco routes."""

import unittest
from unittest.mock import patch

from fastapi import FastAPI
from fastapi.testclient import TestClient
from faker import Faker

from app.common.apis.basilisco.dtos import CreateTransactionResponse, TransactionsResponse
from app.middleware.auth import get_current_user
from app.routes.basilisco_routes import router

fake = Faker()


class TestBasiliscoRoutes(unittest.TestCase):
    """Test cases for Basilisco routes."""

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

    @patch("app.routes.basilisco_routes.BasiliscoClient")
    def test_get_backoffice_transactions_success(self, mock_client_class):
        """Test getting backoffice transactions successfully."""
        self.app.dependency_overrides[get_current_user] = lambda: self.mock_current_user

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

        mock_client = mock_client_class.return_value
        mock_client.get_transactions.return_value = TransactionsResponse(**mock_transactions_data)

        response = self.client.get("/v1/backoffice/transactions?provider=fireblocks&page=1&limit=10")

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["count"], 1)
        self.assertEqual(len(data["transactions"]), 1)
        mock_client.get_transactions.assert_called_once_with(
            provider="fireblocks",
            page=1,
            limit=10
        )

    @patch("app.routes.basilisco_routes.BasiliscoClient")
    def test_get_backoffice_transactions_without_provider(self, mock_client_class):
        """Test getting transactions without provider filter."""
        self.app.dependency_overrides[get_current_user] = lambda: self.mock_current_user

        mock_transactions_data = {
            "transactions": [],
            "count": 0,
            "total_count": 0,
            "page": 1,
            "limit": 10,
        }

        mock_client = mock_client_class.return_value
        mock_client.get_transactions.return_value = TransactionsResponse(**mock_transactions_data)

        response = self.client.get("/v1/backoffice/transactions?page=2&limit=20")

        self.assertEqual(response.status_code, 200)
        mock_client.get_transactions.assert_called_once_with(
            provider=None,
            page=2,
            limit=20
        )

    @patch("app.routes.basilisco_routes.BasiliscoClient")
    def test_get_backoffice_transactions_configuration_error(self, mock_client_class):
        """Test getting transactions when configuration error occurs."""
        self.app.dependency_overrides[get_current_user] = lambda: self.mock_current_user

        from app.common.apis.basilisco.errors import BasiliscoAPIClientError
        mock_client = mock_client_class.return_value
        mock_client.get_transactions.side_effect = BasiliscoAPIClientError("BASILISCO_API_KEY not found in secrets")

        response = self.client.get("/v1/backoffice/transactions")

        self.assertEqual(response.status_code, 502)
        data = response.json()
        self.assertIn("error retrieving transactions", data["detail"].lower())

    @patch("app.routes.basilisco_routes.BasiliscoClient")
    def test_get_backoffice_transactions_generic_error(self, mock_client_class):
        """Test getting transactions when generic error occurs."""
        self.app.dependency_overrides[get_current_user] = lambda: self.mock_current_user

        mock_client = mock_client_class.return_value
        mock_client.get_transactions.side_effect = Exception("Network error")

        response = self.client.get("/v1/backoffice/transactions")

        self.assertEqual(response.status_code, 502)
        data = response.json()
        self.assertIn("error retrieving transactions", data["detail"].lower())

    @patch("app.routes.basilisco_routes.BasiliscoClient")
    def test_get_backoffice_transactions_default_params(self, mock_client_class):
        """Test getting transactions with default parameters."""
        self.app.dependency_overrides[get_current_user] = lambda: self.mock_current_user

        mock_transactions_data = {
            "transactions": [],
            "count": 0,
            "page": 1,
            "limit": 10,
        }

        mock_client = mock_client_class.return_value
        mock_client.get_transactions.return_value = TransactionsResponse(**mock_transactions_data)

        response = self.client.get("/v1/backoffice/transactions")

        self.assertEqual(response.status_code, 200)
        mock_client.get_transactions.assert_called_once_with(
            provider=None,
            page=1,
            limit=10
        )

    @patch("app.routes.basilisco_routes.BasiliscoClient")
    def test_create_backoffice_transaction_success(self, mock_client_class):
        """Test creating backoffice transaction successfully."""
        self.app.dependency_overrides[get_current_user] = lambda: self.mock_current_user

        transaction_id = fake.uuid4()
        mock_transaction_response = {
            "id": transaction_id
        }

        mock_client = mock_client_class.return_value
        mock_client.create_transaction.return_value = CreateTransactionResponse(**mock_transaction_response)

        transaction_data = {
            "created_at": fake.date_time().strftime("%Y-%m-%d %H:%M:%S.%f"),
            "type": fake.random_element(elements=("withdrawal", "deposit", "transfer")),
            "provider": fake.random_element(elements=("kira", "fireblocks", "circle")),
            "fees": str(fake.pydecimal(left_digits=1, right_digits=4, positive=True)),
            "amount": str(fake.pydecimal(left_digits=2, right_digits=2, positive=True)),
            "currency": fake.currency_code(),
            "rate": str(fake.pydecimal(left_digits=4, right_digits=4, positive=True)),
            "st_id": fake.uuid4(),
            "st_hash": fake.sha256(),
            "user_id": fake.uuid4(),
            "category": fake.random_element(elements=("withdrawal", "deposit", "transfer")),
            "transfer_id": fake.uuid4(),
            "actor_id": fake.uuid4(),
            "source_id": fake.uuid4(),
            "reason": fake.sentence(),
            "occurred_at": fake.date_time().strftime("%Y-%m-%d %H:%M:%S.%f"),
            "idempotency_key": fake.uuid4()
        }

        response = self.client.post(
            "/v1/backoffice/transactions",
            json=transaction_data
        )

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["id"], transaction_id)
        mock_client.create_transaction.assert_called_once()
        call_args = mock_client.create_transaction.call_args
        self.assertEqual(call_args[0][0], transaction_data)

    @patch("app.routes.basilisco_routes.BasiliscoClient")
    def test_create_backoffice_transaction_configuration_error(self, mock_client_class):
        """Test creating transaction when configuration error occurs."""
        self.app.dependency_overrides[get_current_user] = lambda: self.mock_current_user

        from app.common.apis.basilisco.errors import BasiliscoAPIClientError
        mock_client = mock_client_class.return_value
        mock_client.create_transaction.side_effect = BasiliscoAPIClientError(
            "BASILISCO_API_KEY not found in secrets"
        )

        transaction_data = {
            "type": fake.random_element(elements=("withdrawal", "deposit")),
            "provider": fake.random_element(elements=("kira", "fireblocks")),
            "amount": str(fake.pydecimal(left_digits=2, right_digits=2, positive=True)),
            "currency": fake.currency_code(),
            "user_id": fake.uuid4(),
        }

        response = self.client.post(
            "/v1/backoffice/transactions",
            json=transaction_data
        )

        self.assertEqual(response.status_code, 502)
        data = response.json()
        self.assertIn("error creating transaction", data["detail"].lower())

    @patch("app.routes.basilisco_routes.BasiliscoClient")
    def test_create_backoffice_transaction_generic_error(self, mock_client_class):
        """Test creating transaction when generic error occurs."""
        self.app.dependency_overrides[get_current_user] = lambda: self.mock_current_user

        mock_client = mock_client_class.return_value
        mock_client.create_transaction.side_effect = Exception("Network error")

        transaction_data = {
            "type": fake.random_element(elements=("withdrawal", "deposit")),
            "provider": fake.random_element(elements=("kira", "fireblocks")),
            "amount": str(fake.pydecimal(left_digits=2, right_digits=2, positive=True)),
            "currency": fake.currency_code(),
            "user_id": fake.uuid4(),
        }

        response = self.client.post(
            "/v1/backoffice/transactions",
            json=transaction_data
        )

        self.assertEqual(response.status_code, 502)
        data = response.json()
        self.assertIn("error creating transaction", data["detail"].lower())

    @patch("app.routes.basilisco_routes.BasiliscoClient")
    def test_create_backoffice_transaction_with_minimal_data(self, mock_client_class):
        """Test creating transaction with only required/minimal fields."""
        self.app.dependency_overrides[get_current_user] = lambda: self.mock_current_user

        transaction_id = fake.uuid4()
        mock_transaction_response = {
            "id": transaction_id
        }

        mock_client = mock_client_class.return_value
        mock_client.create_transaction.return_value = CreateTransactionResponse(**mock_transaction_response)

        # Only send a few fields to test optional fields
        transaction_data = {
            "type": fake.random_element(elements=("withdrawal", "deposit")),
            "amount": str(fake.pydecimal(left_digits=2, right_digits=2, positive=True)),
            "currency": fake.currency_code(),
        }

        response = self.client.post(
            "/v1/backoffice/transactions",
            json=transaction_data
        )

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["id"], transaction_id)
        mock_client.create_transaction.assert_called_once()
        call_args = mock_client.create_transaction.call_args
        # Verify only the sent fields are passed (None values filtered out)
        sent_data = call_args[0][0]
        self.assertEqual(sent_data, transaction_data)
        self.assertIn("type", sent_data)
        self.assertIn("amount", sent_data)
        self.assertIn("currency", sent_data)


if __name__ == "__main__":
    unittest.main()
