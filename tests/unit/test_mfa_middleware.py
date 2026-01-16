"""Tests for MFA middleware."""

import os
import unittest
from unittest.mock import patch

from fastapi import HTTPException, status

from app.middleware.mfa import require_mfa_verification


class TestMFAMiddleware(unittest.TestCase):
    """Test cases for MFA middleware."""

    def setUp(self):
        """Set up test fixtures."""
        self.mock_user = {
            "firebase_uid": "test-uid-123",
            "email": "test@littio.co",
            "name": "Test User",
        }
        self.valid_totp_code = "123456"
        self.valid_secret = "JBSWY3DPEHPK3PXP"

    @patch("app.middleware.mfa.TOTPStorageService.get_secret")
    def test_require_mfa_verification_no_mfa_configured(self, mock_get_secret):
        """Test MFA verification when MFA is not configured."""
        mock_get_secret.return_value = None

        with self.assertRaises(HTTPException) as context:
            require_mfa_verification(
                current_user=self.mock_user,
                totp_code=self.valid_totp_code,
            )

        self.assertEqual(context.exception.status_code, status.HTTP_403_FORBIDDEN)
        self.assertIn("MFA (Multi-Factor Authentication) no está configurado", context.exception.detail)
        mock_get_secret.assert_called_once_with("test-uid-123")

    @patch("app.middleware.mfa.TOTPStorageService.get_secret")
    def test_require_mfa_verification_no_totp_code(self, mock_get_secret):
        """Test MFA verification when TOTP code is missing."""
        mock_get_secret.return_value = self.valid_secret

        with self.assertRaises(HTTPException) as context:
            require_mfa_verification(
                current_user=self.mock_user,
                totp_code=None,
            )

        self.assertEqual(context.exception.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("Código TOTP requerido", context.exception.detail)
        self.assertIn("X-TOTP-Code", context.exception.detail)

    @patch("app.middleware.mfa.TOTPService.verify_totp")
    @patch("app.middleware.mfa.TOTPStorageService.get_secret")
    def test_require_mfa_verification_invalid_totp_code(self, mock_get_secret, mock_verify_totp):
        """Test MFA verification with invalid TOTP code."""
        mock_get_secret.return_value = self.valid_secret
        mock_verify_totp.return_value = False

        with patch.dict(os.environ, {"ENVIRONMENT": "production"}, clear=False):
            with self.assertRaises(HTTPException) as context:
                require_mfa_verification(
                    current_user=self.mock_user,
                    totp_code="000000",
                )

        self.assertEqual(context.exception.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("Código TOTP inválido", context.exception.detail)
        mock_verify_totp.assert_called_once_with(self.valid_secret, "000000")

    @patch("app.middleware.mfa.TOTPService.verify_totp")
    @patch("app.middleware.mfa.TOTPStorageService.get_secret")
    def test_require_mfa_verification_success(self, mock_get_secret, mock_verify_totp):
        """Test successful MFA verification."""
        mock_get_secret.return_value = self.valid_secret
        mock_verify_totp.return_value = True

        result = require_mfa_verification(
            current_user=self.mock_user,
            totp_code=self.valid_totp_code,
        )

        self.assertEqual(result, self.mock_user)
        mock_verify_totp.assert_called_once_with(self.valid_secret, self.valid_totp_code)

    @patch("app.middleware.mfa.TOTPStorageService.get_secret")
    def test_require_mfa_verification_empty_totp_code(self, mock_get_secret):
        """Test MFA verification with empty TOTP code."""
        mock_get_secret.return_value = self.valid_secret

        with self.assertRaises(HTTPException) as context:
            require_mfa_verification(
                current_user=self.mock_user,
                totp_code="",
            )

        self.assertEqual(context.exception.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("Código TOTP requerido", context.exception.detail)

    @patch("app.middleware.mfa.TOTPService.verify_totp")
    @patch("app.middleware.mfa.TOTPStorageService.get_secret")
    def test_require_mfa_verification_user_without_firebase_uid(self, mock_get_secret, mock_verify_totp):
        """Test MFA verification with user missing firebase_uid."""
        user_without_uid = {
            "email": "test@littio.co",
            "name": "Test User",
        }
        mock_get_secret.return_value = self.valid_secret
        mock_verify_totp.return_value = True

        result = require_mfa_verification(
            current_user=user_without_uid,
            totp_code=self.valid_totp_code,
        )

        self.assertEqual(result, user_without_uid)
        mock_get_secret.assert_called_once_with(None)


if __name__ == "__main__":
    unittest.main()

