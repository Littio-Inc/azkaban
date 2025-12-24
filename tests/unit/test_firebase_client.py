"""Tests for Firebase client."""

import unittest
from unittest.mock import MagicMock, patch

from firebase_admin.exceptions import FirebaseError

from app.common.firebase_client import FirebaseClient


class TestFirebaseClient(unittest.TestCase):
    """Test cases for Firebase client."""

    @patch("app.common.firebase_client.get_app")
    @patch("app.common.firebase_client.initialize_app")
    @patch("app.common.firebase_client.credentials.Certificate")
    def test_init_success(self, mock_certificate, mock_init_app, mock_get_app):
        """Test successful Firebase client initialization."""
        mock_get_app.side_effect = ValueError("App not initialized")
        mock_creds = MagicMock()
        mock_certificate.return_value = mock_creds

        client = FirebaseClient()
        self.assertIsNotNone(client)
        mock_certificate.assert_called_once_with("service-account.json")
        mock_init_app.assert_called_once_with(mock_creds)

    @patch("app.common.firebase_client.get_app")
    @patch("app.common.firebase_client.initialize_app")
    @patch("app.common.firebase_client.credentials.Certificate")
    def test_init_already_initialized(self, mock_certificate, mock_init_app, mock_get_app):
        """Test Firebase client when app is already initialized."""
        mock_get_app.return_value = MagicMock()

        client = FirebaseClient()
        self.assertIsNotNone(client)
        mock_certificate.assert_not_called()
        mock_init_app.assert_not_called()

    @patch("app.common.firebase_client.get_app")
    @patch("app.common.firebase_client.initialize_app")
    @patch("app.common.firebase_client.credentials.Certificate")
    def test_init_io_error(self, mock_certificate, mock_init_app, mock_get_app):
        """Test Firebase client initialization with IOError."""
        mock_get_app.side_effect = IOError("File not found")
        mock_certificate.side_effect = IOError("File not found")

        with self.assertRaises(RuntimeError) as context:
            FirebaseClient()
        self.assertIn("Error reading Firebase credentials", str(context.exception))

    @patch("app.common.firebase_client.get_app")
    @patch("app.common.firebase_client.initialize_app")
    @patch("app.common.firebase_client.credentials.Certificate")
    def test_init_firebase_error(self, mock_certificate, mock_init_app, mock_get_app):
        """Test Firebase client initialization with FirebaseError."""
        mock_get_app.side_effect = ValueError("App not initialized")
        mock_certificate.return_value = MagicMock()
        # Create a real exception that inherits from FirebaseError

        class MockFirebaseError(FirebaseError):
            def __init__(self):
                super().__init__(code="internal", message="Firebase error")

        mock_init_app.side_effect = MockFirebaseError()

        with self.assertRaises(RuntimeError) as context:
            FirebaseClient()
        self.assertIn("Firebase initialization failed", str(context.exception))

    @patch("app.common.firebase_client.get_app")
    @patch("app.common.firebase_client.initialize_app")
    @patch("app.common.firebase_client.credentials.Certificate")
    def test_init_exception(self, mock_certificate, mock_init_app, mock_get_app):
        """Test Firebase client initialization with generic exception."""
        mock_get_app.side_effect = Exception("Unexpected error")

        with self.assertRaises(Exception):
            FirebaseClient()

    @patch("app.common.firebase_client.auth.verify_id_token")
    def test_verify_id_token_success(self, mock_verify):
        """Test successful token verification."""
        with patch("app.common.firebase_client.get_app"):
            with patch("app.common.firebase_client.initialize_app"):
                with patch("app.common.firebase_client.credentials.Certificate"):
                    client = FirebaseClient()
                    mock_decoded = {"uid": "test-uid", "email": "test@littio.co"}
                    mock_verify.return_value = mock_decoded

                    result = client.verify_id_token("valid-token")
                    self.assertEqual(result, mock_decoded)
                    mock_verify.assert_called_once_with("valid-token", clock_skew_seconds=10)

    @patch("app.common.firebase_client.auth.verify_id_token")
    def test_verify_id_token_invalid(self, mock_verify):
        """Test token verification with InvalidIdTokenError."""
        from firebase_admin import auth
        with patch("app.common.firebase_client.get_app"):
            with patch("app.common.firebase_client.initialize_app"):
                with patch("app.common.firebase_client.credentials.Certificate"):
                    client = FirebaseClient()
                    # Create a real exception that inherits from InvalidIdTokenError

                    class MockInvalidIdTokenError(auth.InvalidIdTokenError):
                        def __init__(self):
                            super().__init__(message="Invalid token")

                    mock_verify.side_effect = MockInvalidIdTokenError()

                    with self.assertRaises(ValueError) as context:
                        client.verify_id_token("invalid-token")
                    self.assertIn("Invalid token format", str(context.exception))

    @patch("app.common.firebase_client.auth.verify_id_token")
    def test_verify_id_token_expired(self, mock_verify):
        """Test token verification with ExpiredIdTokenError."""
        from firebase_admin import auth
        with patch("app.common.firebase_client.get_app"):
            with patch("app.common.firebase_client.initialize_app"):
                with patch("app.common.firebase_client.credentials.Certificate"):
                    client = FirebaseClient()
                    # Create a real exception that inherits from ExpiredIdTokenError
                    # Note: ExpiredIdTokenError may inherit from InvalidIdTokenError,
                    # so we need to ensure it's caught in the right order

                    class MockExpiredIdTokenError(auth.ExpiredIdTokenError):
                        def __init__(self):
                            # Try to match the actual signature of ExpiredIdTokenError
                            try:
                                super().__init__(message="Token expired", cause=Exception("Token expired"))
                            except TypeError:
                                # Fallback if signature is different
                                super().__init__(cause=Exception("Token expired"))

                    mock_verify.side_effect = MockExpiredIdTokenError()

                    with self.assertRaises(ValueError) as context:
                        client.verify_id_token("expired-token")
                    # The exception should be "Token expired" not "Invalid token format"
                    self.assertIn("Token expired", str(context.exception))

    @patch("app.common.firebase_client.auth.verify_id_token")
    def test_verify_id_token_firebase_error(self, mock_verify):
        """Test token verification with FirebaseError."""
        with patch("app.common.firebase_client.get_app"):
            with patch("app.common.firebase_client.initialize_app"):
                with patch("app.common.firebase_client.credentials.Certificate"):
                    client = FirebaseClient()
                    # Create a real exception that inherits from FirebaseError

                    class MockFirebaseError(FirebaseError):
                        def __init__(self):
                            super().__init__(code="internal", message="Firebase error")

                    mock_verify.side_effect = MockFirebaseError()

                    with self.assertRaises(FirebaseError) as context:
                        client.verify_id_token("token")
                    self.assertIn("Token verification failed", str(context.exception))

    @patch("app.common.firebase_client.credentials.Certificate")
    def test_load_credentials_success(self, mock_certificate):
        """Test loading credentials successfully."""
        with patch("app.common.firebase_client.get_app"):
            with patch("app.common.firebase_client.initialize_app"):
                mock_creds = MagicMock()
                mock_certificate.return_value = mock_creds

                client = FirebaseClient()
                result = client._load_credentials()
                self.assertEqual(result, mock_creds)
                mock_certificate.assert_called_with("service-account.json")

    @patch("app.common.firebase_client.credentials.Certificate")
    def test_load_credentials_file_not_found(self, mock_certificate):
        """Test loading credentials when file not found."""
        with patch("app.common.firebase_client.get_app"):
            with patch("app.common.firebase_client.initialize_app"):
                mock_certificate.side_effect = FileNotFoundError("File not found")

                client = FirebaseClient()
                with self.assertRaises(FileNotFoundError) as context:
                    client._load_credentials()
                self.assertIn("service-account.json not found", str(context.exception))

    @patch("app.common.firebase_client.credentials.Certificate")
    def test_load_credentials_value_error(self, mock_certificate):
        """Test loading credentials with ValueError."""
        with patch("app.common.firebase_client.get_app"):
            with patch("app.common.firebase_client.initialize_app"):
                mock_certificate.side_effect = ValueError("Invalid format")

                client = FirebaseClient()
                with self.assertRaises(ValueError) as context:
                    client._load_credentials()
                self.assertIn("Invalid or malformed", str(context.exception))

    @patch("app.common.firebase_client.credentials.Certificate")
    def test_load_credentials_permission_error(self, mock_certificate):
        """Test loading credentials with PermissionError."""
        with patch("app.common.firebase_client.get_app"):
            with patch("app.common.firebase_client.initialize_app"):
                mock_certificate.side_effect = PermissionError("Permission denied")

                client = FirebaseClient()
                with self.assertRaises(RuntimeError) as context:
                    client._load_credentials()
                self.assertIn("Permission denied", str(context.exception))

    @patch("app.common.firebase_client.get_app")
    @patch("app.common.firebase_client.initialize_app")
    @patch("app.common.firebase_client.credentials.Certificate")
    def test_init_exception_in_initialize(self, mock_certificate, mock_init_app, mock_get_app):
        """Test Firebase client initialization with exception in _initialize_firebase."""
        mock_get_app.side_effect = ValueError("App not initialized")
        mock_certificate.return_value = MagicMock()
        mock_init_app.side_effect = Exception("Unexpected error")

        with self.assertRaises(Exception):
            FirebaseClient()

    @patch("app.common.firebase_client.get_app")
    @patch("app.common.firebase_client.initialize_app")
    @patch("app.common.firebase_client.credentials.Certificate")
    def test_init_io_error_in_load_credentials(self, mock_certificate, mock_init_app, mock_get_app):
        """Test Firebase client initialization with IOError in _load_credentials."""
        mock_get_app.side_effect = ValueError("App not initialized")
        # IOError should be raised during initialize_app, not in Certificate
        mock_certificate.return_value = MagicMock()
        mock_init_app.side_effect = IOError("File not found")

        with self.assertRaises(RuntimeError) as context:
            FirebaseClient()
        self.assertIn("Error reading Firebase credentials", str(context.exception))

    @patch("app.common.firebase_client.get_app")
    @patch("app.common.firebase_client.initialize_app")
    @patch("app.common.firebase_client.credentials.Certificate")
    def test_init_firebase_error_in_initialize(self, mock_certificate, mock_init_app, mock_get_app):
        """Test Firebase client initialization with FirebaseError in _initialize_firebase."""
        mock_get_app.side_effect = ValueError("App not initialized")
        mock_certificate.return_value = MagicMock()
        # Create a real exception that inherits from FirebaseError

        class MockFirebaseError(FirebaseError):
            def __init__(self):
                super().__init__(code="internal", message="Firebase config error")

        mock_init_app.side_effect = MockFirebaseError()

        with self.assertRaises(RuntimeError) as context:
            FirebaseClient()
        self.assertIn("Firebase initialization failed", str(context.exception))


if __name__ == "__main__":
    unittest.main()
