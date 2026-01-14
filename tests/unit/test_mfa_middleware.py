"""Tests for MFA middleware."""

import os
import unittest
from unittest.mock import MagicMock, patch

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

    @patch("app.middleware.mfa.TOTPService.verify_totp")
    @patch("app.middleware.mfa.TOTPStorageService.get_secret")
    @patch.dict(os.environ, {"ENVIRONMENT": "local", "FIXED_OTP_CODE": "999999"})
    def test_require_mfa_verification_fixed_otp_code_local(self, mock_get_secret, mock_verify_totp):
        """Test MFA verification with fixed OTP code in local environment."""
        mock_get_secret.return_value = self.valid_secret
        mock_verify_totp.return_value = False  # TOTP fails, but fixed code should work

        result = require_mfa_verification(
            current_user=self.mock_user,
            totp_code="999999",
        )

        self.assertEqual(result, self.mock_user)
        mock_verify_totp.assert_called_once_with(self.valid_secret, "999999")

    @patch("app.middleware.mfa.TOTPService.verify_totp")
    @patch("app.middleware.mfa.TOTPStorageService.get_secret")
    @patch.dict(os.environ, {"ENVIRONMENT": "staging", "FIXED_OTP_CODE": "888888"})
    def test_require_mfa_verification_fixed_otp_code_staging(self, mock_get_secret, mock_verify_totp):
        """Test MFA verification with fixed OTP code in staging environment."""
        mock_get_secret.return_value = self.valid_secret
        mock_verify_totp.return_value = False

        result = require_mfa_verification(
            current_user=self.mock_user,
            totp_code="888888",
        )

        self.assertEqual(result, self.mock_user)

    @patch("app.middleware.mfa.TOTPService.verify_totp")
    @patch("app.middleware.mfa.TOTPStorageService.get_secret")
    @patch.dict(os.environ, {"ENVIRONMENT": "development", "FIXED_OTP_CODE": "777777"})
    def test_require_mfa_verification_fixed_otp_code_development(self, mock_get_secret, mock_verify_totp):
        """Test MFA verification with fixed OTP code in development environment."""
        mock_get_secret.return_value = self.valid_secret
        mock_verify_totp.return_value = False

        result = require_mfa_verification(
            current_user=self.mock_user,
            totp_code="777777",
        )

        self.assertEqual(result, self.mock_user)

    @patch("app.middleware.mfa.TOTPService.verify_totp")
    @patch("app.middleware.mfa.TOTPStorageService.get_secret")
    @patch.dict(os.environ, {"ENVIRONMENT": "dev", "FIXED_OTP_CODE": "666666"})
    def test_require_mfa_verification_fixed_otp_code_dev(self, mock_get_secret, mock_verify_totp):
        """Test MFA verification with fixed OTP code in dev environment."""
        mock_get_secret.return_value = self.valid_secret
        mock_verify_totp.return_value = False

        result = require_mfa_verification(
            current_user=self.mock_user,
            totp_code="666666",
        )

        self.assertEqual(result, self.mock_user)

    @patch("app.middleware.mfa.TOTPService.verify_totp")
    @patch("app.middleware.mfa.TOTPStorageService.get_secret")
    @patch.dict(os.environ, {"ENVIRONMENT": "stage", "FIXED_OTP_CODE": "555555"})
    def test_require_mfa_verification_fixed_otp_code_stage(self, mock_get_secret, mock_verify_totp):
        """Test MFA verification with fixed OTP code in stage environment."""
        mock_get_secret.return_value = self.valid_secret
        mock_verify_totp.return_value = False

        result = require_mfa_verification(
            current_user=self.mock_user,
            totp_code="555555",
        )

        self.assertEqual(result, self.mock_user)

    @patch("app.middleware.mfa.TOTPService.verify_totp")
    @patch("app.middleware.mfa.TOTPStorageService.get_secret")
    @patch.dict(os.environ, {"ENVIRONMENT": "production", "FIXED_OTP_CODE": "999999"})
    def test_require_mfa_verification_fixed_otp_code_not_allowed_in_production(self, mock_get_secret, mock_verify_totp):
        """Test that fixed OTP code is not allowed in production."""
        mock_get_secret.return_value = self.valid_secret
        mock_verify_totp.return_value = False

        with self.assertRaises(HTTPException) as context:
            require_mfa_verification(
                current_user=self.mock_user,
                totp_code="999999",
            )

        self.assertEqual(context.exception.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("Código TOTP inválido", context.exception.detail)

    @patch("app.middleware.mfa.TOTPService.verify_totp")
    @patch("app.middleware.mfa.TOTPStorageService.get_secret")
    @patch.dict(os.environ, {"ENVIRONMENT": "local"}, clear=False)
    def test_require_mfa_verification_fixed_otp_code_wrong_code(self, mock_get_secret, mock_verify_totp):
        """Test MFA verification with wrong fixed OTP code in local environment."""
        mock_get_secret.return_value = self.valid_secret
        mock_verify_totp.return_value = False

        with patch.dict(os.environ, {"FIXED_OTP_CODE": "999999"}, clear=False):
            with self.assertRaises(HTTPException) as context:
                require_mfa_verification(
                    current_user=self.mock_user,
                    totp_code="000000",  # Wrong code
                )

        self.assertEqual(context.exception.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("Código TOTP inválido", context.exception.detail)

    @patch("app.middleware.mfa.TOTPService.verify_totp")
    @patch("app.middleware.mfa.TOTPStorageService.get_secret")
    @patch.dict(os.environ, {"ENVIRONMENT": "local"}, clear=False)
    def test_require_mfa_verification_fixed_otp_code_not_set(self, mock_get_secret, mock_verify_totp):
        """Test MFA verification when fixed OTP code is not set in local environment."""
        mock_get_secret.return_value = self.valid_secret
        mock_verify_totp.return_value = False

        # Remove FIXED_OTP_CODE if it exists
        if "FIXED_OTP_CODE" in os.environ:
            del os.environ["FIXED_OTP_CODE"]

        with self.assertRaises(HTTPException) as context:
            require_mfa_verification(
                current_user=self.mock_user,
                totp_code="000000",
            )

        self.assertEqual(context.exception.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("Código TOTP inválido", context.exception.detail)

    @patch("app.middleware.mfa.TOTPService.verify_totp")
    @patch("app.middleware.mfa.TOTPStorageService.get_secret")
    @patch.dict(os.environ, {"ENVIRONMENT": "LOCAL"}, clear=False)
    def test_require_mfa_verification_case_insensitive_environment(self, mock_get_secret, mock_verify_totp):
        """Test that environment check is case insensitive."""
        mock_get_secret.return_value = self.valid_secret
        mock_verify_totp.return_value = False

        with patch.dict(os.environ, {"FIXED_OTP_CODE": "999999"}, clear=False):
            result = require_mfa_verification(
                current_user=self.mock_user,
                totp_code="999999",
            )

        self.assertEqual(result, self.mock_user)

    @patch("app.middleware.mfa.TOTPService.verify_totp")
    @patch("app.middleware.mfa.TOTPStorageService.get_secret")
    def test_require_mfa_verification_empty_totp_code(self, mock_get_secret, mock_verify_totp):
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

