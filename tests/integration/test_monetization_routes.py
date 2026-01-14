"""Integration tests for monetization routes."""

import unittest
from datetime import datetime, timezone
from unittest.mock import patch

from fastapi import FastAPI
from fastapi.testclient import TestClient
from faker import Faker

from app.common.apis.cassandra.dtos import PayoutResponse
from app.common.apis.cassandra.errors import CassandraAPIClientError
from app.common.errors import MissingCredentialsError
from app.middleware.mfa import require_mfa_verification
from app.routes.monetization_routes import router
from tests.fixtures import create_test_quote_response

fake = Faker()

# Test constants
ACCOUNT_TRANSFER = "transfer"
ACCOUNT_PAY = "pay"
CURRENCY_USD = "USD"
CURRENCY_COP = "COP"
TOKEN_USDC = "USDC"
PROVIDER_KIRA = "kira"


class TestMonetizationRoutes(unittest.TestCase):
    """Test cases for monetization routes."""

    def setUp(self):
        """Set up test fixtures."""
        self.app = FastAPI()
        self.app.include_router(router, prefix="/v1")
        self.client = TestClient(self.app)
        self.mock_current_user = {
            "firebase_uid": fake.uuid4(),
            "email": fake.email(),
            "name": fake.name(),
            "picture": fake.image_url() if fake.boolean() else None,
        }

    def tearDown(self):
        """Clean up after each test."""
        # Clear dependency overrides after each test
        self.app.dependency_overrides.clear()

    def _mock_require_mfa_verification(self):
        """Helper to mock require_mfa_verification dependency."""
        self.app.dependency_overrides[require_mfa_verification] = lambda: self.mock_current_user

    def _create_test_payout_request(self, **kwargs):
        """Helper to create test payout request."""
        quote_id = fake.uuid4()
        defaults = {
            "recipient_id": fake.uuid4(),
            "wallet_id": fake.uuid4(),
            "base_currency": CURRENCY_USD,
            "quote_currency": CURRENCY_COP,
            "amount": float(fake.pydecimal(left_digits=3, right_digits=2, positive=True)),
            "quote_id": quote_id,
            "quote": create_test_quote_response(quote_id=quote_id).model_dump(mode="json"),
            "token": TOKEN_USDC,
            "provider": PROVIDER_KIRA,
            "exchange_only": False,
        }
        defaults.update(kwargs)
        return defaults

    @patch("app.routes.monetization_routes.MonetizationService")
    @patch("app.routes.monetization_routes.UserService")
    def test_create_payout_success(self, mock_user_service, mock_monetization_service):
        """Test creating payout successfully."""
        self._mock_require_mfa_verification()

        user_id = fake.uuid4()
        payout_id = fake.uuid4()
        recipient_id = fake.uuid4()
        quote_id = fake.uuid4()
        from_amount = str(fake.pydecimal(left_digits=3, right_digits=2, positive=True))
        to_amount = str(fake.pydecimal(left_digits=4, right_digits=2, positive=True))
        timestamp = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

        # Mock UserService.get_user_by_firebase_uid
        mock_user_service.get_user_by_firebase_uid.return_value = {"id": user_id}

        # Mock payout response
        mock_payout_response = PayoutResponse(
            payout_id=payout_id,
            user_id=user_id,
            recipient_id=recipient_id,
            quote_id=quote_id,
            from_amount=from_amount,
            from_currency=CURRENCY_USD,
            to_amount=to_amount,
            to_currency=CURRENCY_COP,
            status="pending",
            created_at=timestamp,
            updated_at=timestamp,
        )
        mock_monetization_service.create_payout.return_value = mock_payout_response

        payout_data = self._create_test_payout_request()

        response = self.client.post(
            f"/v1/payouts/account/{ACCOUNT_TRANSFER}/payout",
            json=payout_data,
            headers={"X-TOTP-Code": fake.numerify("######")},
        )

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["payout_id"], payout_id)
        self.assertEqual(data["status"], "pending")

    @patch("app.routes.monetization_routes.UserService")
    def test_create_payout_missing_recipient_id(self, mock_user_service):
        """Test creating payout without recipient_id when exchange_only is False."""
        self._mock_require_mfa_verification()

        user_id = fake.uuid4()

        # Mock UserService.get_user_by_firebase_uid
        mock_user_service.get_user_by_firebase_uid.return_value = {"id": user_id}

        payout_data = self._create_test_payout_request(recipient_id=None, exchange_only=False)

        response = self.client.post(
            f"/v1/payouts/account/{ACCOUNT_TRANSFER}/payout",
            json=payout_data,
            headers={"X-TOTP-Code": fake.numerify("######")},
        )

        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertIn("recipient_id is required", data["detail"])

    @patch("app.routes.monetization_routes.UserService")
    def test_create_payout_missing_provider(self, mock_user_service):
        """Test creating payout without provider."""
        self._mock_require_mfa_verification()

        user_id = fake.uuid4()

        # Mock UserService.get_user_by_firebase_uid
        mock_user_service.get_user_by_firebase_uid.return_value = {"id": user_id}

        # Remove provider from request data
        payout_data = self._create_test_payout_request()
        payout_data.pop("provider", None)

        response = self.client.post(
            f"/v1/payouts/account/{ACCOUNT_TRANSFER}/payout",
            json=payout_data,
            headers={"X-TOTP-Code": fake.numerify("######")},
        )

        # Pydantic validation returns 422 when required field is missing
        self.assertEqual(response.status_code, 422)
        data = response.json()
        # Pydantic error format
        self.assertIn("detail", data)

    @patch("app.routes.monetization_routes.MonetizationService")
    @patch("app.routes.monetization_routes.UserService")
    def test_create_payout_generic_error(self, mock_user_service, mock_monetization_service):
        """Test creating payout when generic error occurs."""
        self._mock_require_mfa_verification()

        user_id = fake.uuid4()
        error_message = fake.sentence()

        # Mock UserService.get_user_by_firebase_uid
        mock_user_service.get_user_by_firebase_uid.return_value = {"id": user_id}

        # Mock generic exception
        mock_monetization_service.create_payout.side_effect = Exception(error_message)

        payout_data = self._create_test_payout_request()

        response = self.client.post(
            f"/v1/payouts/account/{ACCOUNT_TRANSFER}/payout",
            json=payout_data,
            headers={"X-TOTP-Code": fake.numerify("######")},
        )

        self.assertEqual(response.status_code, 502)
        data = response.json()
        self.assertIn("Error creating payout", data["detail"])

    @patch("app.routes.monetization_routes.MonetizationService")
    @patch("app.routes.monetization_routes.UserService")
    def test_create_payout_cassandra_error(self, mock_user_service, mock_monetization_service):
        """Test creating payout when Cassandra API error occurs."""
        self._mock_require_mfa_verification()

        user_id = fake.uuid4()
        error_message = fake.sentence()

        # Mock UserService.get_user_by_firebase_uid
        mock_user_service.get_user_by_firebase_uid.return_value = {"id": user_id}

        # Mock Cassandra API error
        mock_monetization_service.create_payout.side_effect = CassandraAPIClientError(error_message)

        payout_data = self._create_test_payout_request()

        response = self.client.post(
            f"/v1/payouts/account/{ACCOUNT_TRANSFER}/payout",
            json=payout_data,
            headers={"X-TOTP-Code": fake.numerify("######")},
        )

        # Should return appropriate error status (usually 400 or 502)
        self.assertIn(response.status_code, [400, 502])
        data = response.json()
        self.assertIn("detail", data)

    @patch("app.routes.monetization_routes.MonetizationService")
    @patch("app.routes.monetization_routes.UserService")
    def test_create_payout_missing_credentials_error(self, mock_user_service, mock_monetization_service):
        """Test creating payout when missing credentials error occurs."""
        self._mock_require_mfa_verification()

        user_id = fake.uuid4()
        error_message = fake.sentence()

        # Mock UserService.get_user_by_firebase_uid
        mock_user_service.get_user_by_firebase_uid.return_value = {"id": user_id}

        # Mock MissingCredentialsError
        mock_monetization_service.create_payout.side_effect = MissingCredentialsError(error_message)

        payout_data = self._create_test_payout_request()

        response = self.client.post(
            f"/v1/payouts/account/{ACCOUNT_TRANSFER}/payout",
            json=payout_data,
            headers={"X-TOTP-Code": fake.numerify("######")},
        )

        self.assertEqual(response.status_code, 500)
        data = response.json()
        self.assertIn("Monetization service configuration error", data["detail"])

    @patch("app.routes.monetization_routes.MonetizationService")
    @patch("app.routes.monetization_routes.UserService")
    def test_create_payout_exchange_only_success(self, mock_user_service, mock_monetization_service):
        """Test creating payout with exchange_only=True (no recipient_id required)."""
        self._mock_require_mfa_verification()

        user_id = fake.uuid4()
        payout_id = fake.uuid4()
        quote_id = fake.uuid4()
        from_amount = str(fake.pydecimal(left_digits=3, right_digits=2, positive=True))
        to_amount = str(fake.pydecimal(left_digits=4, right_digits=2, positive=True))
        timestamp = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

        # Mock UserService.get_user_by_firebase_uid
        mock_user_service.get_user_by_firebase_uid.return_value = {"id": user_id}

        # Mock payout response
        mock_payout_response = PayoutResponse(
            payout_id=payout_id,
            user_id=user_id,
            recipient_id=None,
            quote_id=quote_id,
            from_amount=from_amount,
            from_currency=CURRENCY_USD,
            to_amount=to_amount,
            to_currency=CURRENCY_COP,
            status="pending",
            created_at=timestamp,
            updated_at=timestamp,
        )
        mock_monetization_service.create_payout.return_value = mock_payout_response

        payout_data = self._create_test_payout_request(recipient_id=None, exchange_only=True)

        response = self.client.post(
            f"/v1/payouts/account/{ACCOUNT_TRANSFER}/payout",
            json=payout_data,
            headers={"X-TOTP-Code": fake.numerify("######")},
        )

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["payout_id"], payout_id)


if __name__ == "__main__":
    unittest.main()
