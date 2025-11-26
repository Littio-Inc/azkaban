"""Tests for authorizer service."""

import unittest
from unittest.mock import MagicMock, patch

from app.authorizers.authorizer_service import AuthorizerService


class TestAuthorizerService(unittest.TestCase):
    """Test cases for authorizer service."""

    def setUp(self):
        """Set up test fixtures."""
        with patch("app.authorizers.authorizer_service.FirebaseClient"):
            self.service = AuthorizerService()

    def test_extract_token_from_authorization_token(self):
        """Test extracting token from authorizationToken field."""
        event = {"authorizationToken": "test-token-123"}
        token = self.service.extract_token(event)
        self.assertEqual(token, "test-token-123")

    def test_extract_token_from_headers_lowercase(self):
        """Test extracting token from lowercase authorization header."""
        event = {
            "headers": {"authorization": "test-token-456"}
        }
        token = self.service.extract_token(event)
        self.assertEqual(token, "test-token-456")

    def test_extract_token_from_headers_uppercase(self):
        """Test extracting token from uppercase Authorization header."""
        event = {
            "headers": {"Authorization": "test-token-789"}
        }
        token = self.service.extract_token(event)
        self.assertEqual(token, "test-token-789")

    def test_extract_token_with_bearer_prefix(self):
        """Test extracting token with Bearer prefix."""
        event = {"authorizationToken": "Bearer test-token-bearer"}
        token = self.service.extract_token(event)
        self.assertEqual(token, "test-token-bearer")

    def test_extract_token_missing(self):
        """Test extracting token when no token is provided."""
        event = {"headers": {}}
        with self.assertRaises(ValueError) as context:
            self.service.extract_token(event)
        self.assertIn("No token provided", str(context.exception))

    def test_extract_token_no_headers(self):
        """Test extracting token when event has no headers."""
        event = {}
        with self.assertRaises(ValueError) as context:
            self.service.extract_token(event)
        self.assertIn("No token provided", str(context.exception))

    def test_verify_token_success(self):
        """Test successful token verification."""
        mock_decoded_token = {
            "uid": "firebase-uid-123",
            "email": "test@littio.co",
            "name": "Test User",
        }
        self.service.firebase_client.verify_id_token = MagicMock(return_value=mock_decoded_token)

        result = self.service.verify_token("valid-token")
        self.assertEqual(result, mock_decoded_token)
        self.service.firebase_client.verify_id_token.assert_called_once_with("valid-token")

    def test_verify_token_value_error(self):
        """Test token verification with ValueError."""
        self.service.firebase_client.verify_id_token = MagicMock(side_effect=ValueError("Invalid token"))

        with self.assertRaises(ValueError):
            self.service.verify_token("invalid-token")

    def test_verify_token_generic_exception(self):
        """Test token verification with generic exception."""
        self.service.firebase_client.verify_id_token = MagicMock(side_effect=Exception("Unexpected error"))

        with self.assertRaises(ValueError) as context:
            self.service.verify_token("token")
        self.assertIn("Token verification failed", str(context.exception))

    def test_extract_user_info_complete(self):
        """Test extracting user info with all fields."""
        from app.authorizers.authorizer_service import _extract_user_info
        decoded_token = {
            "uid": "firebase-uid-123",
            "email": "test@littio.co",
            "name": "Test User",
            "picture": "https://example.com/pic.jpg",
        }
        user_info = _extract_user_info(decoded_token)
        self.assertEqual(user_info["firebase_uid"], "firebase-uid-123")
        self.assertEqual(user_info["email"], "test@littio.co")
        self.assertEqual(user_info["name"], "Test User")
        self.assertEqual(user_info["picture"], "https://example.com/pic.jpg")

    def test_extract_user_info_missing_fields(self):
        """Test extracting user info with missing fields."""
        from app.authorizers.authorizer_service import _extract_user_info
        decoded_token = {"uid": "firebase-uid-123"}
        user_info = _extract_user_info(decoded_token)
        self.assertEqual(user_info["firebase_uid"], "firebase-uid-123")
        self.assertEqual(user_info["email"], "")
        self.assertEqual(user_info["name"], "")
        self.assertEqual(user_info["picture"], "")

    def test_build_authorizer_context_complete(self):
        """Test building authorizer context with all fields."""
        from app.authorizers.authorizer_service import _build_authorizer_context
        user_info = {
            "firebase_uid": "firebase-uid-123",
            "email": "test@littio.co",
            "name": "Test User",
            "picture": "https://example.com/pic.jpg",
        }
        context = _build_authorizer_context(user_info)
        self.assertEqual(context["user_id"], "firebase-uid-123")
        self.assertEqual(context["email"], "test@littio.co")
        self.assertEqual(context["name"], "Test User")
        self.assertEqual(context["picture"], "https://example.com/pic.jpg")

    def test_build_authorizer_context_empty_fields(self):
        """Test building authorizer context with empty fields."""
        from app.authorizers.authorizer_service import _build_authorizer_context
        user_info = {
            "firebase_uid": "firebase-uid-123",
            "email": "test@littio.co",
            "name": "",
            "picture": "",
        }
        context = _build_authorizer_context(user_info)
        self.assertEqual(context["user_id"], "firebase-uid-123")
        self.assertEqual(context["email"], "test@littio.co")
        self.assertEqual(context["name"], "")
        self.assertEqual(context["picture"], "")

    def test_generate_policy_authorized_with_principal(self):
        """Test generating policy for authorized request with principal."""
        context = {"user_id": "firebase-uid-123", "email": "test@littio.co"}
        policy = self.service.generate_policy(
            is_authorized=True,
            principal_id="firebase-uid-123",
            context=context
        )
        self.assertTrue(policy["isAuthorized"])
        self.assertEqual(policy["principalId"], "firebase-uid-123")
        self.assertEqual(policy["context"], context)

    def test_generate_policy_authorized_without_principal(self):
        """Test generating policy for authorized request without principal."""
        policy = self.service.generate_policy(is_authorized=True)
        self.assertTrue(policy["isAuthorized"])
        self.assertEqual(policy["principalId"], "user")
        self.assertNotIn("context", policy)

    def test_generate_policy_denied_without_principal(self):
        """Test generating policy for denied request without principal."""
        policy = self.service.generate_policy(is_authorized=False)
        self.assertFalse(policy["isAuthorized"])
        self.assertEqual(policy["principalId"], "unauthorized")
        self.assertNotIn("context", policy)

    def test_generate_policy_denied_with_principal(self):
        """Test generating policy for denied request with principal."""
        policy = self.service.generate_policy(
            is_authorized=False,
            principal_id="unauthorized-user"
        )
        self.assertFalse(policy["isAuthorized"])
        self.assertEqual(policy["principalId"], "unauthorized-user")

    def test_generate_deny_policy(self):
        """Test generating deny policy."""
        policy = self.service.generate_deny_policy()
        self.assertFalse(policy["isAuthorized"])
        self.assertEqual(policy["principalId"], "unauthorized")
        self.assertNotIn("context", policy)

    @patch.object(AuthorizerService, "extract_token")
    @patch.object(AuthorizerService, "verify_token")
    def test_authorize_success(self, mock_verify_token, mock_extract_token):
        """Test successful authorization."""
        mock_extract_token.return_value = "valid-token"
        mock_decoded_token = {
            "uid": "firebase-uid-123",
            "email": "test@littio.co",
            "name": "Test User",
            "picture": "https://example.com/pic.jpg",
        }
        mock_verify_token.return_value = mock_decoded_token

        event = {"methodArn": "arn:aws:execute-api:us-east-1:123456789:api/test"}
        policy = self.service.authorize(event)

        self.assertTrue(policy["isAuthorized"])
        self.assertEqual(policy["principalId"], "firebase-uid-123")
        self.assertIn("context", policy)
        self.assertEqual(policy["context"]["user_id"], "firebase-uid-123")
        self.assertEqual(policy["context"]["email"], "test@littio.co")

    @patch.object(AuthorizerService, "extract_token")
    def test_authorize_no_token(self, mock_extract_token):
        """Test authorization when no token is provided."""
        mock_extract_token.side_effect = ValueError("No token provided")

        event = {"methodArn": "arn:aws:execute-api:us-east-1:123456789:api/test"}
        policy = self.service.authorize(event)

        self.assertFalse(policy["isAuthorized"])
        self.assertEqual(policy["principalId"], "unauthorized")

    @patch.object(AuthorizerService, "extract_token")
    @patch.object(AuthorizerService, "verify_token")
    def test_authorize_invalid_token(self, mock_verify_token, mock_extract_token):
        """Test authorization with invalid token."""
        mock_extract_token.return_value = "invalid-token"
        mock_verify_token.side_effect = ValueError("Invalid token")

        event = {"methodArn": "arn:aws:execute-api:us-east-1:123456789:api/test"}
        policy = self.service.authorize(event)

        self.assertFalse(policy["isAuthorized"])
        self.assertEqual(policy["principalId"], "unauthorized")

    @patch.object(AuthorizerService, "extract_token")
    @patch.object(AuthorizerService, "verify_token")
    def test_authorize_non_littio_email(self, mock_verify_token, mock_extract_token):
        """Test authorization with non-@littio.co email."""
        mock_extract_token.return_value = "valid-token"
        mock_decoded_token = {
            "uid": "firebase-uid-123",
            "email": "test@example.com",
            "name": "Test User",
        }
        mock_verify_token.return_value = mock_decoded_token

        event = {"methodArn": "arn:aws:execute-api:us-east-1:123456789:api/test"}
        policy = self.service.authorize(event)

        # Should still authorize but log warning
        self.assertTrue(policy["isAuthorized"])
        self.assertEqual(policy["principalId"], "firebase-uid-123")


if __name__ == "__main__":
    unittest.main()

