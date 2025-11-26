"""Tests for secrets management."""

import os
import unittest
from unittest.mock import MagicMock, patch

from app.common.enums import Environment
from app.common.secrets import get_secret


class TestSecrets(unittest.TestCase):
    """Test cases for secrets management."""

    def setUp(self):
        """Set up test fixtures."""
        # Clear any cached secrets
        import app.common.secrets as secrets_module
        secrets_module.secrets = {}

    def tearDown(self):
        """Clean up after each test."""
        # Clear environment variables
        env_vars_to_clear = ["ENVIRONMENT", "TEST_SECRET", "SECRET_MANAGER_AZKABAN_ARN"]
        for var in env_vars_to_clear:
            if var in os.environ:
                del os.environ[var]
        # Clear cached secrets
        import app.common.secrets as secrets_module
        secrets_module.secrets = {}

    def test_get_secret_local_environment(self):
        """Test getting secret from environment variable in LOCAL."""
        os.environ["ENVIRONMENT"] = Environment.LOCAL.value
        os.environ["TEST_SECRET"] = "local_secret_value"

        secret = get_secret("TEST_SECRET")
        self.assertEqual(secret, "local_secret_value")

    def test_get_secret_testing_environment(self):
        """Test getting secret from environment variable in TESTING."""
        os.environ["ENVIRONMENT"] = Environment.TESTING.value
        os.environ["TEST_SECRET"] = "testing_secret_value"

        secret = get_secret("TEST_SECRET")
        self.assertEqual(secret, "testing_secret_value")

    def test_get_secret_not_found_local(self):
        """Test getting secret that doesn't exist in LOCAL."""
        os.environ["ENVIRONMENT"] = Environment.LOCAL.value
        if "TEST_SECRET" in os.environ:
            del os.environ["TEST_SECRET"]

        secret = get_secret("TEST_SECRET")
        self.assertIsNone(secret)

    @patch("app.common.secrets.boto3")
    def test_get_secret_aws_secrets_manager(self, mock_boto3):
        """Test getting secret from AWS Secrets Manager."""
        os.environ["ENVIRONMENT"] = "staging"
        os.environ["SECRET_MANAGER_AZKABAN_ARN"] = "arn:aws:secretsmanager:us-east-1:123456789:secret:azkaban-staging"

        mock_client = MagicMock()
        mock_boto3.client.return_value = mock_client
        mock_client.get_secret_value.return_value = {
            "SecretString": '{"TEST_SECRET": "aws_secret_value"}'
        }

        secret = get_secret("TEST_SECRET")
        self.assertEqual(secret, "aws_secret_value")
        mock_boto3.client.assert_called_once_with("secretsmanager")
        mock_client.get_secret_value.assert_called_once_with(
            SecretId="arn:aws:secretsmanager:us-east-1:123456789:secret:azkaban-staging"
        )

    @patch("app.common.secrets.boto3")
    def test_get_secret_aws_cached(self, mock_boto3):
        """Test getting secret from AWS Secrets Manager with caching."""
        os.environ["ENVIRONMENT"] = "staging"
        os.environ["SECRET_MANAGER_AZKABAN_ARN"] = "arn:aws:secretsmanager:us-east-1:123456789:secret:azkaban-staging"

        mock_client = MagicMock()
        mock_boto3.client.return_value = mock_client
        mock_client.get_secret_value.return_value = {
            "SecretString": '{"TEST_SECRET": "aws_secret_value", "OTHER_SECRET": "other_value"}'
        }

        # First call should fetch from AWS
        secret1 = get_secret("TEST_SECRET")
        self.assertEqual(secret1, "aws_secret_value")
        self.assertEqual(mock_client.get_secret_value.call_count, 1)

        # Second call should use cache
        secret2 = get_secret("OTHER_SECRET")
        self.assertEqual(secret2, "other_value")
        # Should still be called only once (cached)
        self.assertEqual(mock_client.get_secret_value.call_count, 1)

    def test_get_secret_no_arn_fallback(self):
        """Test getting secret when ARN is not set, falls back to env vars."""
        os.environ["ENVIRONMENT"] = "staging"
        if "SECRET_MANAGER_AZKABAN_ARN" in os.environ:
            del os.environ["SECRET_MANAGER_AZKABAN_ARN"]
        os.environ["TEST_SECRET"] = "fallback_secret_value"

        secret = get_secret("TEST_SECRET")
        self.assertEqual(secret, "fallback_secret_value")

    @patch("app.common.secrets.boto3", None)
    def test_get_secret_boto3_not_available(self):
        """Test getting secret when boto3 is not available."""
        os.environ["ENVIRONMENT"] = "staging"
        os.environ["SECRET_MANAGER_AZKABAN_ARN"] = "arn:aws:secretsmanager:us-east-1:123456789:secret:azkaban-staging"
        os.environ["TEST_SECRET"] = "fallback_secret_value"

        # Clear cached secrets
        import app.common.secrets as secrets_module
        secrets_module.secrets = {}

        # When boto3 is None, it should fallback to environment variables
        secret = get_secret("TEST_SECRET")
        self.assertEqual(secret, "fallback_secret_value")

    @patch.dict("sys.modules", {"boto3": None})
    def test_get_secret_boto3_import_error(self):
        """Test getting secret when boto3 import fails."""
        import sys
        import app.common.secrets as secrets_module

        # Simulate ImportError by removing boto3 from the module
        original_boto3 = getattr(secrets_module, "boto3", None)
        secrets_module.boto3 = None
        secrets_module.secrets = {}

        os.environ["ENVIRONMENT"] = "staging"
        os.environ["SECRET_MANAGER_AZKABAN_ARN"] = "arn:aws:secretsmanager:us-east-1:123456789:secret:azkaban-staging"
        os.environ["TEST_SECRET"] = "fallback_secret_value"

        secret = get_secret("TEST_SECRET")
        self.assertEqual(secret, "fallback_secret_value")

        # Restore original boto3
        if original_boto3 is not None:
            secrets_module.boto3 = original_boto3

    def test_get_secret_not_found_staging(self):
        """Test getting secret that doesn't exist in staging."""
        os.environ["ENVIRONMENT"] = "staging"
        if "SECRET_MANAGER_AZKABAN_ARN" in os.environ:
            del os.environ["SECRET_MANAGER_AZKABAN_ARN"]
        if "TEST_SECRET" in os.environ:
            del os.environ["TEST_SECRET"]

        secret = get_secret("TEST_SECRET")
        self.assertIsNone(secret)


if __name__ == "__main__":
    unittest.main()
