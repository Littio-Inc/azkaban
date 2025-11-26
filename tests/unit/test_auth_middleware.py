"""Tests for authentication middleware."""

import unittest
from unittest.mock import MagicMock, patch

from fastapi import HTTPException
from fastapi.security import HTTPAuthorizationCredentials

from app.middleware.auth import get_current_user


class TestAuthMiddleware(unittest.TestCase):
    """Test cases for authentication middleware."""

    @patch("app.middleware.auth._get_firebase_client")
    def test_get_current_user_success(self, mock_get_client):
        """Test successful user authentication."""
        mock_credentials = MagicMock(spec=HTTPAuthorizationCredentials)
        mock_credentials.credentials = "valid-token"

        mock_decoded_token = {
            "uid": "firebase-uid-123",
            "email": "test@littio.co",
            "name": "Test User",
            "picture": "https://example.com/pic.jpg",
        }
        mock_client = MagicMock()
        mock_client.verify_id_token.return_value = mock_decoded_token
        mock_get_client.return_value = mock_client

        user = get_current_user(mock_credentials)
        self.assertIsNotNone(user)
        self.assertEqual(user["firebase_uid"], "firebase-uid-123")
        self.assertEqual(user["email"], "test@littio.co")
        self.assertEqual(user["name"], "Test User")
        mock_client.verify_id_token.assert_called_once_with("valid-token")

    def test_get_current_user_no_credentials(self):
        """Test authentication without credentials."""
        with self.assertRaises(HTTPException) as context:
            get_current_user(None)
        self.assertEqual(context.exception.status_code, 401)
        self.assertIn("Token de autenticación requerido", context.exception.detail)

    @patch("app.middleware.auth._get_firebase_client")
    def test_get_current_user_invalid_domain(self, mock_get_client):
        """Test authentication with invalid email domain."""
        mock_credentials = MagicMock(spec=HTTPAuthorizationCredentials)
        mock_credentials.credentials = "valid-token"

        mock_decoded_token = {
            "uid": "firebase-uid-123",
            "email": "test@example.com",  # Not @littio.co
            "name": "Test User",
        }
        mock_client = MagicMock()
        mock_client.verify_id_token.return_value = mock_decoded_token
        mock_get_client.return_value = mock_client

        with self.assertRaises(HTTPException) as context:
            get_current_user(mock_credentials)
        self.assertEqual(context.exception.status_code, 403)
        self.assertIn("Solo se permiten emails @littio.co", context.exception.detail)

    @patch("app.middleware.auth._get_firebase_client")
    def test_get_current_user_invalid_token(self, mock_get_client):
        """Test authentication with invalid token."""
        mock_credentials = MagicMock(spec=HTTPAuthorizationCredentials)
        mock_credentials.credentials = "invalid-token"
        mock_client = MagicMock()
        mock_client.verify_id_token.side_effect = ValueError("Invalid token format")
        mock_get_client.return_value = mock_client

        with self.assertRaises(HTTPException) as context:
            get_current_user(mock_credentials)
        self.assertEqual(context.exception.status_code, 401)
        self.assertIn("Token inválido", context.exception.detail)

    @patch("app.middleware.auth._get_firebase_client")
    def test_get_current_user_expired_token(self, mock_get_client):
        """Test authentication with expired token."""
        mock_credentials = MagicMock(spec=HTTPAuthorizationCredentials)
        mock_credentials.credentials = "expired-token"
        mock_client = MagicMock()
        mock_client.verify_id_token.side_effect = ValueError("Token expired")
        mock_get_client.return_value = mock_client

        with self.assertRaises(HTTPException) as context:
            get_current_user(mock_credentials)
        self.assertEqual(context.exception.status_code, 401)
        self.assertIn("Token expirado", context.exception.detail)

    @patch("app.middleware.auth._get_firebase_client")
    def test_get_current_user_generic_exception(self, mock_get_client):
        """Test authentication with generic exception."""
        mock_credentials = MagicMock(spec=HTTPAuthorizationCredentials)
        mock_credentials.credentials = "token"
        mock_client = MagicMock()
        mock_client.verify_id_token.side_effect = Exception("Unexpected error")
        mock_get_client.return_value = mock_client

        with self.assertRaises(HTTPException) as context:
            get_current_user(mock_credentials)
        self.assertEqual(context.exception.status_code, 401)
        self.assertIn("Error de autenticación", context.exception.detail)

    @patch("app.middleware.auth._get_firebase_client")
    def test_get_current_user_generic_exception_non_http(self, mock_get_client):
        """Test authentication with generic exception that's not HTTPException."""
        from app.middleware.auth import _verify_firebase_token
        mock_credentials = MagicMock(spec=HTTPAuthorizationCredentials)
        mock_credentials.credentials = "token"
        mock_client = MagicMock()
        mock_client.verify_id_token.side_effect = KeyError("Unexpected key error")
        mock_get_client.return_value = mock_client

        with self.assertRaises(HTTPException) as context:
            get_current_user(mock_credentials)
        self.assertEqual(context.exception.status_code, 401)
        self.assertIn("Error de autenticación", context.exception.detail)

    @patch("app.middleware.auth.FirebaseClient")
    def test_get_firebase_client_creates_new(self, mock_firebase_client_class):
        """Test _get_firebase_client creates new instance when None."""
        from app.middleware.auth import _get_firebase_client
        import app.middleware.auth as auth_module

        # Reset the global variable
        auth_module.firebase_client = None
        mock_client_instance = MagicMock()
        mock_firebase_client_class.return_value = mock_client_instance

        result = _get_firebase_client()
        self.assertEqual(result, mock_client_instance)
        mock_firebase_client_class.assert_called_once()

    @patch("app.middleware.auth._get_firebase_client")
    def test_handle_generic_error(self, mock_get_client):
        """Test _handle_generic_error function."""
        from app.middleware.auth import _handle_generic_error
        mock_client = MagicMock()
        mock_client.verify_id_token.side_effect = RuntimeError("Runtime error")
        mock_get_client.return_value = mock_client

        with self.assertRaises(HTTPException) as context:
            _handle_generic_error(RuntimeError("Runtime error"))
        self.assertEqual(context.exception.status_code, 401)
        self.assertIn("Error de autenticación", context.exception.detail)

    @patch("app.middleware.auth.FirebaseClient")
    def test_get_firebase_client_returns_existing(self, mock_firebase_client_class):
        """Test _get_firebase_client returns existing instance."""
        from app.middleware.auth import _get_firebase_client
        import app.middleware.auth as auth_module

        # Set existing client
        mock_existing_client = MagicMock()
        auth_module.firebase_client = mock_existing_client

        result = _get_firebase_client()
        self.assertEqual(result, mock_existing_client)
        mock_firebase_client_class.assert_not_called()

        # Reset for other tests
        auth_module.firebase_client = None

    @patch("app.middleware.auth._get_firebase_client")
    def test_handle_value_error_other_error(self, mock_get_client):
        """Test _handle_value_error with other ValueError message."""
        from app.middleware.auth import _handle_value_error

        with self.assertRaises(HTTPException) as context:
            _handle_value_error(ValueError("Some other error"))
        self.assertEqual(context.exception.status_code, 401)
        self.assertIn("Error de autenticación", context.exception.detail)

    @patch("app.middleware.auth._get_firebase_client")
    def test_get_current_user_generic_exception_in_get_current_user(self, mock_get_client):
        """Test get_current_user with generic exception in try block."""
        mock_credentials = MagicMock(spec=HTTPAuthorizationCredentials)
        mock_credentials.credentials = "token"
        mock_client = MagicMock()
        # Make verify_id_token raise a non-HTTPException exception
        mock_client.verify_id_token.side_effect = KeyError("Unexpected key error")
        mock_get_client.return_value = mock_client

        with self.assertRaises(HTTPException) as context:
            get_current_user(mock_credentials)
        self.assertEqual(context.exception.status_code, 401)
        self.assertIn("Error de autenticación", context.exception.detail)


if __name__ == "__main__":
    unittest.main()
