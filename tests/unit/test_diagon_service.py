"""Tests for Diagon service."""

import unittest
from unittest.mock import MagicMock, patch

import httpx

from app.littio.diagon.service import DiagonService


class TestDiagonService(unittest.TestCase):
    """Test cases for Diagon service."""

    @patch("app.littio.diagon.service.get_secret")
    def test_get_base_url_success(self, mock_get_secret):
        """Test getting base URL when secret exists."""
        mock_get_secret.return_value = "https://api.example.com"
        base_url = DiagonService._get_base_url()
        self.assertEqual(base_url, "https://api.example.com")
        mock_get_secret.assert_called_once_with("DIAGON_BASE_URL")

    @patch("app.littio.diagon.service.get_secret")
    def test_get_base_url_with_trailing_slash(self, mock_get_secret):
        """Test getting base URL removes trailing slash."""
        mock_get_secret.return_value = "https://api.example.com/"
        base_url = DiagonService._get_base_url()
        self.assertEqual(base_url, "https://api.example.com")
        mock_get_secret.assert_called_once_with("DIAGON_BASE_URL")

    @patch("app.littio.diagon.service.get_secret")
    def test_get_base_url_not_found(self, mock_get_secret):
        """Test getting base URL when secret is not found."""
        mock_get_secret.return_value = None
        with self.assertRaises(ValueError) as context:
            DiagonService._get_base_url()
        self.assertIn("DIAGON_BASE_URL not found", str(context.exception))

    @patch("app.littio.diagon.service.get_secret")
    def test_get_api_key_success(self, mock_get_secret):
        """Test getting API key when secret exists."""
        mock_get_secret.return_value = "test-api-key-123"
        api_key = DiagonService._get_api_key()
        self.assertEqual(api_key, "test-api-key-123")
        mock_get_secret.assert_called_once_with("DIAGON_API_KEY")

    @patch("app.littio.diagon.service.get_secret")
    def test_get_api_key_not_found(self, mock_get_secret):
        """Test getting API key when secret is not found."""
        mock_get_secret.return_value = None
        with self.assertRaises(ValueError) as context:
            DiagonService._get_api_key()
        self.assertIn("DIAGON_API_KEY not found", str(context.exception))

    @patch("app.littio.diagon.service.get_secret")
    @patch("app.littio.diagon.service.httpx.Client")
    def test_get_accounts_success(self, mock_client_class, mock_get_secret):
        """Test getting accounts successfully."""
        mock_get_secret.side_effect = lambda key: {
            "DIAGON_BASE_URL": "https://a3a9mlmbsk.execute-api.us-east-1.amazonaws.com/staging",
            "DIAGON_API_KEY": "wP9xrNemYuKynUJ4bjsL3cpZFQqThVAk"
        }.get(key)

        mock_response_data = [
            {
                "id": "6",
                "name": "Test2",
                "hiddenOnUI": False,
                "autoFuel": False,
                "assets": []
            },
            {
                "id": "5",
                "name": "Littio-Test",
                "hiddenOnUI": False,
                "autoFuel": False,
                "assets": [
                    {
                        "id": "AMOY_POLYGON_TEST",
                        "total": "0.2",
                        "balance": "0.2",
                        "lockedAmount": "0",
                        "available": "0.2",
                        "pending": "0",
                        "frozen": "0",
                        "staked": "0",
                        "blockHeight": "17182897",
                        "blockHash": "0xbd4b5221dbded68a6c76f809b31f87732b29e2972bf0d9075d2e09e3e2a46fcd"
                    }
                ]
            }
        ]

        mock_response = MagicMock()
        mock_response.json.return_value = mock_response_data
        mock_response.raise_for_status.return_value = None

        mock_client = MagicMock()
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=None)
        mock_client.get.return_value = mock_response
        mock_client_class.return_value = mock_client

        result = DiagonService.get_accounts()

        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]["id"], "6")
        self.assertEqual(result[0]["name"], "Test2")
        self.assertEqual(result[1]["id"], "5")
        self.assertEqual(result[1]["name"], "Littio-Test")
        self.assertEqual(len(result[1]["assets"]), 1)
        mock_client.get.assert_called_once()
        call_args = mock_client.get.call_args
        self.assertEqual(
            call_args[1]["headers"]["X-API-KEY"],
            "wP9xrNemYuKynUJ4bjsL3cpZFQqThVAk"
        )
        self.assertIn(
            "/vault/accounts",
            call_args[0][0]
        )

    @patch("app.littio.diagon.service.get_secret")
    def test_get_accounts_missing_base_url(self, mock_get_secret):
        """Test getting accounts when base URL is missing."""
        mock_get_secret.side_effect = lambda key: {
            "DIAGON_BASE_URL": None,
            "DIAGON_API_KEY": "test-api-key"
        }.get(key)

        with self.assertRaises(ValueError) as context:
            DiagonService.get_accounts()
        self.assertIn("DIAGON_BASE_URL not found", str(context.exception))

    @patch("app.littio.diagon.service.get_secret")
    def test_get_accounts_missing_api_key(self, mock_get_secret):
        """Test getting accounts when API key is missing."""
        mock_get_secret.side_effect = lambda key: {
            "DIAGON_BASE_URL": "https://api.example.com",
            "DIAGON_API_KEY": None
        }.get(key)

        with self.assertRaises(ValueError) as context:
            DiagonService.get_accounts()
        self.assertIn("DIAGON_API_KEY not found", str(context.exception))

    @patch("app.littio.diagon.service.get_secret")
    @patch("app.littio.diagon.service.httpx.Client")
    def test_get_accounts_http_error(self, mock_client_class, mock_get_secret):
        """Test getting accounts when API returns HTTP error."""
        mock_get_secret.side_effect = lambda key: {
            "DIAGON_BASE_URL": "https://api.example.com",
            "DIAGON_API_KEY": "test-api-key"
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
            DiagonService.get_accounts()

    @patch("app.littio.diagon.service.get_secret")
    @patch("app.littio.diagon.service.httpx.Client")
    def test_get_accounts_request_error(self, mock_client_class, mock_get_secret):
        """Test getting accounts when request fails."""
        mock_get_secret.side_effect = lambda key: {
            "DIAGON_BASE_URL": "https://api.example.com",
            "DIAGON_API_KEY": "test-api-key"
        }.get(key)

        mock_request_error = httpx.RequestError("Connection error", request=MagicMock())

        mock_client = MagicMock()
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=None)
        mock_client.get.side_effect = mock_request_error
        mock_client_class.return_value = mock_client

        with self.assertRaises(httpx.RequestError):
            DiagonService.get_accounts()

    @patch("app.littio.diagon.service.get_secret")
    @patch("app.littio.diagon.service.httpx.Client")
    def test_get_accounts_generic_error(self, mock_client_class, mock_get_secret):
        """Test getting accounts when generic error occurs."""
        mock_get_secret.side_effect = lambda key: {
            "DIAGON_BASE_URL": "https://api.example.com",
            "DIAGON_API_KEY": "test-api-key"
        }.get(key)

        mock_client = MagicMock()
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=None)
        mock_client.get.side_effect = Exception("Unexpected error")
        mock_client_class.return_value = mock_client

        with self.assertRaises(Exception) as context:
            DiagonService.get_accounts()
        self.assertEqual(str(context.exception), "Unexpected error")

    @patch("app.littio.diagon.service.get_secret")
    def test_build_url(self, mock_get_secret):
        """Test building the complete API URL."""
        mock_get_secret.return_value = "https://a3a9mlmbsk.execute-api.us-east-1.amazonaws.com/staging"
        url = DiagonService._build_url()
        expected_url = "https://a3a9mlmbsk.execute-api.us-east-1.amazonaws.com/staging/vault/accounts"
        self.assertEqual(url, expected_url)

    @patch("app.littio.diagon.service.get_secret")
    def test_build_headers(self, mock_get_secret):
        """Test building request headers."""
        mock_get_secret.return_value = "wP9xrNemYuKynUJ4bjsL3cpZFQqThVAk"
        headers = DiagonService._build_headers()
        self.assertEqual(headers["X-API-KEY"], "wP9xrNemYuKynUJ4bjsL3cpZFQqThVAk")


if __name__ == "__main__":
    unittest.main()

