"""Integration tests for authentication routes."""

import unittest
from unittest.mock import patch

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.middleware.auth import get_current_user
from app.routes.auth_routes import router


class TestAuthRoutes(unittest.TestCase):
    """Test cases for authentication routes."""

    def setUp(self):
        """Set up test fixtures."""
        self.app = FastAPI()
        self.app.include_router(router)
        self.client = TestClient(self.app)
        self.mock_current_user = {
            "firebase_uid": "test-uid-123",
            "email": "test@littio.co",
            "name": "Test User",
        }

    def tearDown(self):
        """Clean up after each test."""
        # Clear dependency overrides after each test
        self.app.dependency_overrides.clear()

    def _mock_get_current_user(self):
        """Helper to mock get_current_user dependency."""
        self.app.dependency_overrides[get_current_user] = lambda: self.mock_current_user

    def test_login_endpoint(self):
        """Test login endpoint."""
        response = self.client.post("/login")
        self.assertEqual(response.status_code, 200)
        self.assertIn("message", response.json())

    def test_verify_endpoint(self):
        """Test verify endpoint."""
        response = self.client.post("/verify")
        self.assertEqual(response.status_code, 200)
        self.assertIn("message", response.json())

    @patch("app.routes.auth_routes.TOTPStorageService")
    @patch("app.routes.auth_routes.TOTPService")
    def test_setup_totp_success(
        self, mock_totp_service, mock_totp_storage
    ):
        """Test successful TOTP setup."""
        self._mock_get_current_user()
        mock_totp_storage.get_secret.return_value = None
        mock_totp_service.generate_secret.return_value = "TEST_SECRET_123"
        mock_totp_service.get_totp_uri.return_value = "otpauth://totp/test@littio.co?secret=TEST_SECRET_123"
        mock_totp_service.generate_qr_code.return_value = "data:image/png;base64,test"

        with patch("app.routes.auth_routes.os.getenv", return_value="local"):
            response = self.client.post(
                "/setup-totp",
                headers={"Authorization": "Bearer test-token"}
            )
            self.assertEqual(response.status_code, 200)
            data = response.json()
            self.assertIn("qr_code", data)
            self.assertIn("secret", data)
            self.assertIn("manual_entry_key", data)

    @patch("app.routes.auth_routes.TOTPStorageService")
    def test_setup_totp_already_configured(
        self, mock_totp_storage
    ):
        """Test TOTP setup when already configured."""
        self._mock_get_current_user()
        mock_totp_storage.get_secret.return_value = "EXISTING_SECRET"
        mock_totp_storage.is_verified.return_value = True

        response = self.client.post(
            "/setup-totp",
            headers={"Authorization": "Bearer test-token"}
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("TOTP ya está configurado", response.json()["detail"])

    @patch("app.routes.auth_routes.TOTPStorageService")
    @patch("app.routes.auth_routes.TOTPService")
    def test_verify_totp_success(
        self, mock_totp_service, mock_totp_storage
    ):
        """Test successful TOTP verification."""
        self._mock_get_current_user()
        mock_totp_storage.get_secret.return_value = "TEST_SECRET_123"
        mock_totp_service.verify_totp.return_value = True
        mock_totp_storage.is_verified.return_value = False

        response = self.client.post(
            "/verify-totp",
            json={"totp_code": "123456"},
            headers={"Authorization": "Bearer test-token"}
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data["verified"])
        mock_totp_storage.mark_verified.assert_called_once()

    @patch("app.routes.auth_routes.TOTPStorageService")
    def test_verify_totp_not_configured(
        self, mock_totp_storage
    ):
        """Test TOTP verification when not configured."""
        self._mock_get_current_user()
        mock_totp_storage.get_secret.return_value = None

        response = self.client.post(
            "/verify-totp",
            json={"totp_code": "123456"},
            headers={"Authorization": "Bearer test-token"}
        )
        self.assertEqual(response.status_code, 404)
        self.assertIn("TOTP no está configurado", response.json()["detail"])

    @patch("app.routes.auth_routes.TOTPStorageService")
    @patch("app.routes.auth_routes.TOTPService")
    def test_verify_totp_invalid_code(
        self, mock_totp_service, mock_totp_storage
    ):
        """Test TOTP verification with invalid code."""
        self._mock_get_current_user()
        mock_totp_storage.get_secret.return_value = "TEST_SECRET_123"
        mock_totp_service.verify_totp.return_value = False

        response = self.client.post(
            "/verify-totp",
            json={"totp_code": "000000"},
            headers={"Authorization": "Bearer test-token"}
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("Código TOTP inválido", response.json()["detail"])

    @patch("app.routes.auth_routes.TOTPStorageService")
    @patch("app.routes.auth_routes.TOTPService")
    def test_verify_totp_fixed_code_dev(
        self, mock_totp_service, mock_totp_storage
    ):
        """Test TOTP verification with fixed code in development."""
        self._mock_get_current_user()
        mock_totp_storage.get_secret.return_value = "TEST_SECRET_123"
        mock_totp_service.verify_totp.return_value = False
        mock_totp_storage.is_verified.return_value = False

        with patch("app.routes.auth_routes.os.getenv") as mock_getenv:
            mock_getenv.side_effect = lambda key, default="": "local" if key == "ENVIRONMENT" else "123456" if key == "FIXED_OTP_CODE" else default
            response = self.client.post(
                "/verify-totp",
                json={"totp_code": "123456"},
                headers={"Authorization": "Bearer test-token"}
            )
            self.assertEqual(response.status_code, 200)
            data = response.json()
            self.assertTrue(data["verified"])
            mock_totp_storage.mark_verified.assert_called_once()

    @patch("app.routes.auth_routes.TOTPStorageService")
    def test_get_totp_status_configured(
        self, mock_totp_storage
    ):
        """Test getting TOTP status when configured."""
        self._mock_get_current_user()
        mock_totp_storage.get_secret.return_value = "TEST_SECRET_123"
        mock_totp_storage.is_verified.return_value = True

        response = self.client.get(
            "/totp-status",
            headers={"Authorization": "Bearer test-token"}
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data["is_configured"])
        self.assertTrue(data["is_verified"])

    @patch("app.routes.auth_routes.TOTPStorageService")
    def test_get_totp_status_not_configured(
        self, mock_totp_storage
    ):
        """Test getting TOTP status when not configured."""
        self._mock_get_current_user()
        mock_totp_storage.get_secret.return_value = None

        response = self.client.get(
            "/totp-status",
            headers={"Authorization": "Bearer test-token"}
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertFalse(data["is_configured"])
        self.assertFalse(data["is_verified"])

    @patch("app.routes.auth_routes.TOTPStorageService")
    @patch("app.routes.auth_routes.TOTPService")
    def test_get_current_totp_dev_only(
        self, mock_totp_service, mock_totp_storage
    ):
        """Test getting current TOTP code (dev only)."""
        self._mock_get_current_user()
        mock_totp_storage.get_secret.return_value = "TEST_SECRET_123"
        mock_totp_service.get_current_totp.return_value = "123456"

        with patch("app.routes.auth_routes.os.getenv", return_value="local"):
            response = self.client.post(
                "/get-current-totp",
                json={"secret": "TEST_SECRET_123"},
                headers={"Authorization": "Bearer test-token"}
            )
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.json()["totp_code"], "123456")

    @patch("app.routes.auth_routes.TOTPStorageService")
    def test_get_current_totp_secret_mismatch(
        self, mock_totp_storage
    ):
        """Test getting current TOTP code with mismatched secret."""
        self._mock_get_current_user()
        mock_totp_storage.get_secret.return_value = "STORED_SECRET_123"

        with patch("app.routes.auth_routes.os.getenv", return_value="local"):
            response = self.client.post(
                "/get-current-totp",
                json={"secret": "DIFFERENT_SECRET_456"},
                headers={"Authorization": "Bearer test-token"}
            )
            self.assertEqual(response.status_code, 403)
            self.assertIn("Secret does not match", response.json()["detail"])

    def test_get_current_totp_production_forbidden(self):
        """Test getting current TOTP code in production."""
        self._mock_get_current_user()

        with patch("app.routes.auth_routes.os.getenv", return_value="production"):
            response = self.client.post(
                "/get-current-totp",
                json={"secret": "TEST_SECRET_123"},
                headers={"Authorization": "Bearer test-token"}
            )
            self.assertEqual(response.status_code, 403)
            self.assertIn("only available in development", response.json()["detail"])


if __name__ == "__main__":
    unittest.main()
