"""Tests for authentication middleware."""

import unittest
from unittest.mock import patch, MagicMock
from fastapi import HTTPException
from fastapi.security import HTTPAuthorizationCredentials
from app.middleware.auth import get_current_user


# Mock exception classes that inherit from Exception
class MockInvalidIdTokenError(Exception):
    """Mock InvalidIdTokenError exception."""


class MockExpiredIdTokenError(Exception):
    """Mock ExpiredIdTokenError exception."""


class TestAuthMiddleware(unittest.TestCase):
    """Test cases for authentication middleware."""

    @patch("app.middleware.auth.firebase_auth")
    def test_get_current_user_success(self, mock_firebase_auth):
        """Test successful user authentication."""
        mock_credentials = MagicMock(spec=HTTPAuthorizationCredentials)
        mock_credentials.credentials = "valid-token"

        mock_decoded_token = {
            "uid": "firebase-uid-123",
            "email": "test@littio.co",
            "name": "Test User",
            "picture": "https://example.com/pic.jpg",
        }
        mock_firebase_auth.verify_id_token.return_value = mock_decoded_token

        user = get_current_user(mock_credentials)
        self.assertIsNotNone(user)
        self.assertEqual(user["firebase_uid"], "firebase-uid-123")
        self.assertEqual(user["email"], "test@littio.co")
        self.assertEqual(user["name"], "Test User")
        mock_firebase_auth.verify_id_token.assert_called_once_with("valid-token")

    def test_get_current_user_no_credentials(self):
        """Test authentication without credentials."""
        with self.assertRaises(HTTPException) as context:
            get_current_user(None)
        self.assertEqual(context.exception.status_code, 401)
        self.assertIn("Token de autenticación requerido", context.exception.detail)

    @patch("app.middleware.auth.firebase_auth")
    def test_get_current_user_invalid_domain(self, mock_firebase_auth):
        """Test authentication with invalid email domain."""
        mock_credentials = MagicMock(spec=HTTPAuthorizationCredentials)
        mock_credentials.credentials = "valid-token"

        mock_decoded_token = {
            "uid": "firebase-uid-123",
            "email": "test@example.com",  # Not @littio.co
            "name": "Test User",
        }
        mock_firebase_auth.verify_id_token.return_value = mock_decoded_token

        with self.assertRaises(HTTPException) as context:
            get_current_user(mock_credentials)
        self.assertEqual(context.exception.status_code, 403)
        self.assertIn("Solo se permiten emails @littio.co", context.exception.detail)

    @patch("app.middleware.auth.firebase_auth")
    def test_get_current_user_invalid_token(self, mock_firebase_auth):
        """Test authentication with invalid token."""
        # Set the exception class as an attribute of the mock using type()
        type(mock_firebase_auth).InvalidIdTokenError = MockInvalidIdTokenError
        mock_credentials = MagicMock(spec=HTTPAuthorizationCredentials)
        mock_credentials.credentials = "invalid-token"
        mock_firebase_auth.verify_id_token.side_effect = MockInvalidIdTokenError("Invalid token")

        with self.assertRaises(HTTPException) as context:
            get_current_user(mock_credentials)
        self.assertEqual(context.exception.status_code, 401)
        self.assertIn("Token inválido", context.exception.detail)

    @patch("app.middleware.auth.firebase_auth")
    def test_get_current_user_expired_token(self, mock_firebase_auth):
        """Test authentication with expired token."""
        # Create a mock that has both exception classes as attributes
        mock_firebase_auth.ExpiredIdTokenError = MockExpiredIdTokenError
        mock_firebase_auth.InvalidIdTokenError = MockInvalidIdTokenError
        mock_credentials = MagicMock(spec=HTTPAuthorizationCredentials)
        mock_credentials.credentials = "expired-token"
        expired_exception = MockExpiredIdTokenError("Token expired")
        mock_firebase_auth.verify_id_token.side_effect = expired_exception

        with self.assertRaises(HTTPException) as context:
            get_current_user(mock_credentials)
        self.assertEqual(context.exception.status_code, 401)
        self.assertIn("Token expirado", context.exception.detail)

    @patch("app.middleware.auth.firebase_auth")
    def test_get_current_user_generic_exception(self, mock_firebase_auth):
        """Test authentication with generic exception."""
        # Set exception classes so the except blocks can find them
        mock_firebase_auth.ExpiredIdTokenError = MockExpiredIdTokenError
        mock_firebase_auth.InvalidIdTokenError = MockInvalidIdTokenError
        mock_credentials = MagicMock(spec=HTTPAuthorizationCredentials)
        mock_credentials.credentials = "token"
        mock_firebase_auth.verify_id_token.side_effect = Exception("Unexpected error")

        with self.assertRaises(HTTPException) as context:
            get_current_user(mock_credentials)
        self.assertEqual(context.exception.status_code, 401)
        self.assertIn("Error de autenticación", context.exception.detail)


if __name__ == "__main__":
    unittest.main()
