"""Tests for monetization routes helper functions."""

import unittest
from unittest.mock import patch

from fastapi import HTTPException

from app.common.apis.cassandra.errors import CassandraAPIClientError
from app.common.enums import Provider
from app.routes.monetization_routes import (
    _extract_cassandra_error_message,
    _extract_error_from_detail,
    _extract_from_dict,
    _get_kira_user_id,
    _handle_cassandra_payout_error,
    _handle_recipients_error,
    _validate_provider,
)


class TestMonetizationRoutesHelpers(unittest.TestCase):
    """Test cases for monetization routes helper functions."""

    def test_validate_provider_valid(self):
        """Test validating a valid provider."""
        # Should not raise an exception
        _validate_provider("kira")
        _validate_provider("cobre")
        _validate_provider("supra")

    def test_validate_provider_invalid(self):
        """Test validating an invalid provider."""
        with self.assertRaises(HTTPException) as context:
            _validate_provider("invalid_provider")

        self.assertEqual(context.exception.status_code, 400)
        self.assertIn("Invalid provider", context.exception.detail)

    def test_extract_from_dict_with_error_key(self):
        """Test extracting from dict with error key."""
        data = {
            "error": {
                "message": "Test error",
                "code": "TEST_CODE",
            }
        }
        message, code = _extract_from_dict(data, "Default message", "DEFAULT_CODE")
        self.assertEqual(message, "Test error")
        self.assertEqual(code, "TEST_CODE")

    def test_extract_from_dict_with_message_key(self):
        """Test extracting from dict with message key."""
        data = {
            "message": "Test message",
            "code": "TEST_CODE",
        }
        message, code = _extract_from_dict(data, "Default message", "DEFAULT_CODE")
        self.assertEqual(message, "Test message")
        self.assertEqual(code, "TEST_CODE")

    def test_extract_from_dict_default(self):
        """Test extracting from dict with defaults."""
        data = {"other_key": "value"}
        message, code = _extract_from_dict(data, "Default message", "DEFAULT_CODE")
        self.assertEqual(message, "Default message")
        self.assertEqual(code, "DEFAULT_CODE")

    def test_extract_error_from_detail_nested(self):
        """Test extracting error from nested detail."""
        error_detail = {
            "detail": {
                "error": {
                    "message": "Nested error",
                    "code": "NESTED_CODE",
                }
            }
        }
        message, code = _extract_error_from_detail(error_detail)
        self.assertEqual(message, "Nested error")
        self.assertEqual(code, "NESTED_CODE")

    def test_extract_error_from_detail_direct(self):
        """Test extracting error from direct format."""
        error_detail = {
            "error": {
                "message": "Direct error",
                "code": "DIRECT_CODE",
            }
        }
        message, code = _extract_error_from_detail(error_detail)
        self.assertEqual(message, "Direct error")
        self.assertEqual(code, "DIRECT_CODE")

    def test_extract_error_from_detail_message_only(self):
        """Test extracting error from message only."""
        error_detail = {
            "message": "Simple message",
        }
        message, code = _extract_error_from_detail(error_detail)
        self.assertEqual(message, "Simple message")

    def test_extract_error_from_detail_invalid(self):
        """Test extracting error from invalid format."""
        error_detail = "not a dict"
        message, code = _extract_error_from_detail(error_detail)
        self.assertEqual(message, "Error al obtener la cotización")
        self.assertEqual(code, "CASSANDRA_API_ERROR")

    @patch("app.common.secrets.get_secret")
    def test_get_kira_user_id_from_param(self, mock_get_secret):
        """Test getting Kira user ID from parameter."""
        result = _get_kira_user_id("transfer", "user-123")
        self.assertEqual(result, "user-123")
        mock_get_secret.assert_not_called()

    @patch("app.common.secrets.get_secret")
    def test_get_kira_user_id_from_secret_transfer(self, mock_get_secret):
        """Test getting Kira user ID from secret for transfer account."""
        mock_get_secret.return_value = "secret-user-123"
        result = _get_kira_user_id("transfer", None)
        self.assertEqual(result, "secret-user-123")
        mock_get_secret.assert_called_once_with("KIRA_USER_ID_TRANSFER")

    @patch("app.common.secrets.get_secret")
    def test_get_kira_user_id_from_secret_pay(self, mock_get_secret):
        """Test getting Kira user ID from secret for pay account."""
        mock_get_secret.return_value = "secret-user-456"
        result = _get_kira_user_id("pay", None)
        self.assertEqual(result, "secret-user-456")
        mock_get_secret.assert_called_once_with("KIRA_USER_ID_PAY")

    @patch("app.common.secrets.get_secret")
    def test_get_kira_user_id_not_configured(self, mock_get_secret):
        """Test getting Kira user ID when not configured."""
        mock_get_secret.return_value = None
        with self.assertRaises(HTTPException) as context:
            _get_kira_user_id("transfer", None)

        self.assertEqual(context.exception.status_code, 500)
        self.assertIn("Kira user_id not configured", context.exception.detail)

    def test_handle_recipients_error(self):
        """Test handling recipients error."""
        cassandra_error = CassandraAPIClientError(
            "Test error",
            status_code=502,
            error_detail={
                "error": {
                    "message": "Recipients error",
                    "code": "RECIPIENTS_ERROR",
                }
            },
        )
        http_exception = _handle_recipients_error(cassandra_error)
        self.assertEqual(http_exception.status_code, 502)
        self.assertIn("error", http_exception.detail)

    def test_extract_cassandra_error_message_from_detail(self):
        """Test extracting error message from detail."""
        cass_err = CassandraAPIClientError(
            "Base error",
            error_detail={"detail": "Detail message"},
        )
        message = _extract_cassandra_error_message(cass_err)
        self.assertEqual(message, "Detail message")

    def test_extract_cassandra_error_message_from_error_obj(self):
        """Test extracting error message from error object."""
        cass_err = CassandraAPIClientError(
            "Base error",
            error_detail={
                "error": {
                    "message": "Error object message",
                }
            },
        )
        message = _extract_cassandra_error_message(cass_err)
        self.assertEqual(message, "Error object message")

    def test_extract_cassandra_error_message_from_message_key(self):
        """Test extracting error message from message key."""
        cass_err = CassandraAPIClientError(
            "Base error",
            error_detail={"message": "Message key"},
        )
        message = _extract_cassandra_error_message(cass_err)
        self.assertEqual(message, "Message key")

    def test_extract_cassandra_error_message_fallback(self):
        """Test extracting error message fallback to string."""
        cass_err = CassandraAPIClientError("Base error")
        message = _extract_cassandra_error_message(cass_err)
        self.assertEqual(message, "Base error")

    def test_handle_cassandra_payout_error_with_message(self):
        """Test handling payout error with extracted message."""
        cass_err = CassandraAPIClientError(
            "Base error",
            status_code=400,
            error_detail={"detail": "Extracted message"},
        )
        http_exception = _handle_cassandra_payout_error(cass_err)
        self.assertEqual(http_exception.status_code, 400)
        self.assertEqual(http_exception.detail, "Extracted message")

    def test_handle_cassandra_payout_error_without_message(self):
        """Test handling payout error without extracted message."""
        cass_err = CassandraAPIClientError("Base error", status_code=500)
        http_exception = _handle_cassandra_payout_error(cass_err)
        self.assertEqual(http_exception.status_code, 500)
        self.assertEqual(http_exception.detail, "Error creating payout in monetization service")


if __name__ == "__main__":
    unittest.main()
