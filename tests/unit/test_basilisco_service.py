"""Tests for Basilisco service."""

import unittest
from unittest.mock import MagicMock, patch

import httpx

from app.littio.basilisco.service import BasiliscoService


class TestBasiliscoService(unittest.TestCase):
    """Test cases for Basilisco service."""

    @patch("app.littio.basilisco.service.get_secret")
    def test_get_base_url_success(self, mock_get_secret):
        """Test getting base URL when secret exists."""
        mock_get_secret.return_value = "https://api.example.com"
        base_url = BasiliscoService._get_base_url()
        self.assertEqual(base_url, "https://api.example.com")
        mock_get_secret.assert_called_once_with("BASILISCO_BASE_URL")

    @patch("app.littio.basilisco.service.get_secret")
    def test_get_base_url_with_trailing_slash(self, mock_get_secret):
        """Test getting base URL removes trailing slash."""
        mock_get_secret.return_value = "https://api.example.com/"
        base_url = BasiliscoService._get_base_url()
        self.assertEqual(base_url, "https://api.example.com")
        mock_get_secret.assert_called_once_with("BASILISCO_BASE_URL")

    @patch("app.littio.basilisco.service.get_secret")
    def test_get_base_url_not_found(self, mock_get_secret):
        """Test getting base URL when secret is not found."""
        mock_get_secret.return_value = None
        with self.assertRaises(ValueError) as context:
            BasiliscoService._get_base_url()
        self.assertIn("BASILISCO_BASE_URL not found", str(context.exception))

    @patch("app.littio.basilisco.service.get_secret")
    def test_get_api_key_success(self, mock_get_secret):
        """Test getting API key when secret exists."""
        mock_get_secret.return_value = "test-api-key-123"
        api_key = BasiliscoService._get_api_key()
        self.assertEqual(api_key, "test-api-key-123")
        mock_get_secret.assert_called_once_with("BASILISCO_API_KEY")

    @patch("app.littio.basilisco.service.get_secret")
    def test_get_api_key_not_found(self, mock_get_secret):
        """Test getting API key when secret is not found."""
        mock_get_secret.return_value = None
        with self.assertRaises(ValueError) as context:
            BasiliscoService._get_api_key()
        self.assertIn("BASILISCO_API_KEY not found", str(context.exception))

    @patch("app.littio.basilisco.service.get_secret")
    @patch("app.littio.basilisco.service.httpx.Client")
    def test_get_transactions_success(self, mock_client_class, mock_get_secret):
        """Test getting transactions successfully."""
        mock_get_secret.side_effect = lambda key: {
            "BASILISCO_BASE_URL": "https://api.example.com",
            "BASILISCO_API_KEY": "test-api-key"
        }.get(key)

        mock_response = MagicMock()
        mock_response.json.return_value = {
            "transactions": [{"id": "1", "amount": "100"}],
            "count": 1,
            "page": 1,
            "limit": 10
        }
        mock_response.raise_for_status.return_value = None

        mock_client = MagicMock()
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=None)
        mock_client.get.return_value = mock_response
        mock_client_class.return_value = mock_client

        result = BasiliscoService.get_transactions()

        self.assertEqual(result["count"], 1)
        mock_client.get.assert_called_once()
        call_args = mock_client.get.call_args
        self.assertEqual(call_args[1]["headers"]["x-api-key"], "test-api-key")
        self.assertIn("page", call_args[1]["params"])
        self.assertIn("limit", call_args[1]["params"])

    @patch("app.littio.basilisco.service.get_secret")
    @patch("app.littio.basilisco.service.httpx.Client")
    def test_get_transactions_with_provider(self, mock_client_class, mock_get_secret):
        """Test getting transactions with provider filter."""
        mock_get_secret.side_effect = lambda key: {
            "BASILISCO_BASE_URL": "https://api.example.com",
            "BASILISCO_API_KEY": "test-api-key"
        }.get(key)

        mock_response = MagicMock()
        mock_response.json.return_value = {"transactions": []}
        mock_response.raise_for_status.return_value = None

        mock_client = MagicMock()
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=None)
        mock_client.get.return_value = mock_response
        mock_client_class.return_value = mock_client

        BasiliscoService.get_transactions(provider="fireblocks", page=2, limit=20)

        call_args = mock_client.get.call_args
        self.assertEqual(call_args[1]["params"]["provider"], "fireblocks")
        self.assertEqual(call_args[1]["params"]["page"], 2)
        self.assertEqual(call_args[1]["params"]["limit"], 20)

    @patch("app.littio.basilisco.service.get_secret")
    def test_get_transactions_missing_base_url(self, mock_get_secret):
        """Test getting transactions when base URL is missing."""
        mock_get_secret.side_effect = lambda key: {
            "BASILISCO_BASE_URL": None,
            "BASILISCO_API_KEY": "test-api-key"
        }.get(key)

        with self.assertRaises(ValueError) as context:
            BasiliscoService.get_transactions()
        self.assertIn("BASILISCO_BASE_URL not found", str(context.exception))

    @patch("app.littio.basilisco.service.get_secret")
    def test_get_transactions_missing_api_key(self, mock_get_secret):
        """Test getting transactions when API key is missing."""
        mock_get_secret.side_effect = lambda key: {
            "BASILISCO_BASE_URL": "https://api.example.com",
            "BASILISCO_API_KEY": None
        }.get(key)

        with self.assertRaises(ValueError) as context:
            BasiliscoService.get_transactions()
        self.assertIn("BASILISCO_API_KEY not found", str(context.exception))

    @patch("app.littio.basilisco.service.get_secret")
    @patch("app.littio.basilisco.service.httpx.Client")
    def test_get_transactions_http_error(self, mock_client_class, mock_get_secret):
        """Test getting transactions when API returns HTTP error."""
        mock_get_secret.side_effect = lambda key: {
            "BASILISCO_BASE_URL": "https://api.example.com",
            "BASILISCO_API_KEY": "test-api-key"
        }.get(key)

        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.text = "Internal Server Error"

        mock_http_error = httpx.HTTPStatusError(
            "Server error",
            request=MagicMock(),
            response=mock_response
        )

        mock_client = MagicMock()
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=None)
        mock_client.get.return_value = mock_response
        mock_response.raise_for_status.side_effect = mock_http_error
        mock_client_class.return_value = mock_client

        with self.assertRaises(httpx.HTTPStatusError):
            BasiliscoService.get_transactions()

    @patch("app.littio.basilisco.service.get_secret")
    @patch("app.littio.basilisco.service.httpx.Client")
    def test_get_transactions_request_error(self, mock_client_class, mock_get_secret):
        """Test getting transactions when request fails."""
        mock_get_secret.side_effect = lambda key: {
            "BASILISCO_BASE_URL": "https://api.example.com",
            "BASILISCO_API_KEY": "test-api-key"
        }.get(key)

        mock_request_error = httpx.RequestError("Connection error", request=MagicMock())

        mock_client = MagicMock()
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=None)
        mock_client.get.side_effect = mock_request_error
        mock_client_class.return_value = mock_client

        with self.assertRaises(httpx.RequestError):
            BasiliscoService.get_transactions()

    @patch("app.littio.basilisco.service.get_secret")
    @patch("app.littio.basilisco.service.httpx.Client")
    def test_get_transactions_generic_error(self, mock_client_class, mock_get_secret):
        """Test getting transactions when generic error occurs."""
        mock_get_secret.side_effect = lambda key: {
            "BASILISCO_BASE_URL": "https://api.example.com",
            "BASILISCO_API_KEY": "test-api-key"
        }.get(key)

        mock_client = MagicMock()
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=None)
        mock_client.get.side_effect = Exception("Unexpected error")
        mock_client_class.return_value = mock_client

        with self.assertRaises(Exception) as context:
            BasiliscoService.get_transactions()
        self.assertEqual(str(context.exception), "Unexpected error")


if __name__ == "__main__":
    unittest.main()
