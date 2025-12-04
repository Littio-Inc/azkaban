"""Tests for Diagon service."""

import unittest
from unittest.mock import MagicMock, patch

import httpx
from faker import Faker

from app.littio.diagon.service import DiagonService

fake = Faker()


class TestDiagonService(unittest.TestCase):
    """Test cases for Diagon service."""

    @patch("app.littio.diagon.service.get_secret")
    def test_get_base_url_success(self, mock_get_secret):
        """Test getting base URL when secret exists."""
        base_url_value = fake.url().rstrip("/")
        mock_get_secret.return_value = base_url_value
        base_url = DiagonService._get_base_url()
        self.assertEqual(base_url, base_url_value)
        mock_get_secret.assert_called_once_with("DIAGON_BASE_URL")

    @patch("app.littio.diagon.service.get_secret")
    def test_get_base_url_with_trailing_slash(self, mock_get_secret):
        """Test getting base URL removes trailing slash."""
        base_url_value = fake.url().rstrip("/")
        url_with_slash = f"{base_url_value}/"
        mock_get_secret.return_value = url_with_slash
        base_url = DiagonService._get_base_url()
        self.assertEqual(base_url, base_url_value)
        mock_get_secret.assert_called_once_with("DIAGON_BASE_URL")

    @patch("app.littio.diagon.service.get_secret")
    def test_get_base_url_not_found(self, mock_get_secret):
        """Test getting base URL when secret is not found."""
        mock_get_secret.return_value = None
        with self.assertRaises(ValueError) as context:
            DiagonService._get_base_url()
        self.assertIn("DIAGON_BASE_URL not found in secrets", str(context.exception))

    @patch("app.littio.diagon.service.get_secret")
    def test_get_api_key_success(self, mock_get_secret):
        """Test getting API key when secret exists."""
        api_key_value = fake.password(length=32, special_chars=False)
        mock_get_secret.return_value = api_key_value
        api_key = DiagonService._get_api_key()
        self.assertEqual(api_key, api_key_value)
        mock_get_secret.assert_called_once_with("DIAGON_API_KEY")

    @patch("app.littio.diagon.service.get_secret")
    def test_get_api_key_not_found(self, mock_get_secret):
        """Test getting API key when secret is not found."""
        mock_get_secret.return_value = None
        with self.assertRaises(ValueError) as context:
            DiagonService._get_api_key()
        self.assertIn("DIAGON_API_KEY not found in secrets", str(context.exception))

    @patch("app.littio.diagon.service.get_secret")
    @patch("app.littio.diagon.service.httpx.Client")
    def test_get_accounts_success(self, mock_client_class, mock_get_secret):
        """Test getting accounts successfully."""
        base_url = fake.url().rstrip("/")
        api_key = fake.password(length=32, special_chars=False)

        mock_get_secret.side_effect = lambda key: {
            "DIAGON_BASE_URL": base_url,
            "DIAGON_API_KEY": api_key
        }.get(key)

        account_id_1 = fake.uuid4()
        account_name_1 = fake.company()
        account_id_2 = fake.uuid4()
        account_name_2 = fake.company()
        asset_id = fake.bothify(text="????_####", letters="ABCDEFGHIJKLMNOPQRSTUVWXYZ")
        asset_amount = fake.pydecimal(left_digits=1, right_digits=2, positive=True)
        block_height = fake.random_int(min=10000000, max=99999999)
        block_hash = fake.sha256()

        mock_response_data = [
            {
                "id": account_id_1,
                "name": account_name_1,
                "hiddenOnUI": False,
                "autoFuel": False,
                "assets": []
            },
            {
                "id": account_id_2,
                "name": account_name_2,
                "hiddenOnUI": False,
                "autoFuel": False,
                "assets": [
                    {
                        "id": asset_id,
                        "total": str(asset_amount),
                        "balance": str(asset_amount),
                        "lockedAmount": "0",
                        "available": str(asset_amount),
                        "pending": "0",
                        "frozen": "0",
                        "staked": "0",
                        "blockHeight": str(block_height),
                        "blockHash": block_hash
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
        self.assertEqual(result[0]["id"], account_id_1)
        self.assertEqual(result[0]["name"], account_name_1)
        self.assertEqual(result[1]["id"], account_id_2)
        self.assertEqual(result[1]["name"], account_name_2)
        self.assertEqual(len(result[1]["assets"]), 1)
        mock_client.get.assert_called_once()
        call_args = mock_client.get.call_args
        self.assertEqual(call_args[1]["headers"]["X-API-KEY"], api_key)
        self.assertIn("/vault/accounts", call_args[0][0])

    @patch("app.littio.diagon.service.get_secret")
    def test_get_accounts_missing_base_url(self, mock_get_secret):
        """Test getting accounts when base URL is missing."""
        api_key = fake.password(length=32, special_chars=False)

        mock_get_secret.side_effect = lambda key: {
            "DIAGON_BASE_URL": None,
            "DIAGON_API_KEY": api_key
        }.get(key)

        with self.assertRaises(ValueError) as context:
            DiagonService.get_accounts()
        self.assertIn("DIAGON_BASE_URL not found in secrets", str(context.exception))

    @patch("app.littio.diagon.service.get_secret")
    def test_get_accounts_missing_api_key(self, mock_get_secret):
        """Test getting accounts when API key is missing."""
        base_url = fake.url().rstrip("/")

        mock_get_secret.side_effect = lambda key: {
            "DIAGON_BASE_URL": base_url,
            "DIAGON_API_KEY": None
        }.get(key)

        with self.assertRaises(ValueError) as context:
            DiagonService.get_accounts()
        self.assertIn("DIAGON_API_KEY not found in secrets", str(context.exception))

    @patch("app.littio.diagon.service.get_secret")
    @patch("app.littio.diagon.service.httpx.Client")
    def test_get_accounts_http_error(self, mock_client_class, mock_get_secret):
        """Test getting accounts when API returns HTTP error."""
        base_url = fake.url().rstrip("/")
        api_key = fake.password(length=32, special_chars=False)

        mock_get_secret.side_effect = lambda key: {
            "DIAGON_BASE_URL": base_url,
            "DIAGON_API_KEY": api_key
        }.get(key)

        status_code = fake.random_int(min=400, max=599)
        error_message = fake.text(max_nb_chars=100)

        mock_response = MagicMock()
        mock_response.status_code = status_code
        mock_response.text = error_message

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
        base_url = fake.url().rstrip("/")
        api_key = fake.password(length=32, special_chars=False)

        mock_get_secret.side_effect = lambda key: {
            "DIAGON_BASE_URL": base_url,
            "DIAGON_API_KEY": api_key
        }.get(key)

        error_message = fake.text(max_nb_chars=50)
        mock_request_error = httpx.RequestError(error_message, request=MagicMock())

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
        base_url = fake.url().rstrip("/")
        api_key = fake.password(length=32, special_chars=False)

        mock_get_secret.side_effect = lambda key: {
            "DIAGON_BASE_URL": base_url,
            "DIAGON_API_KEY": api_key
        }.get(key)

        error_message = fake.text(max_nb_chars=50)
        mock_client = MagicMock()
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=None)
        mock_client.get.side_effect = Exception(error_message)
        mock_client_class.return_value = mock_client

        with self.assertRaises(Exception) as context:
            DiagonService.get_accounts()
        self.assertEqual(str(context.exception), error_message)

    @patch("app.littio.diagon.service.get_secret")
    def test_build_url(self, mock_get_secret):
        """Test building the complete API URL."""
        base_url = fake.url().rstrip("/")
        mock_get_secret.return_value = base_url
        url = DiagonService._build_url()
        expected_url = f"{base_url}/vault/accounts"
        self.assertEqual(url, expected_url)

    @patch("app.littio.diagon.service.get_secret")
    def test_build_headers(self, mock_get_secret):
        """Test building request headers."""
        api_key = fake.password(length=32, special_chars=False)
        mock_get_secret.return_value = api_key
        headers = DiagonService._build_headers()
        self.assertEqual(headers["X-API-KEY"], api_key)


if __name__ == "__main__":
    unittest.main()
