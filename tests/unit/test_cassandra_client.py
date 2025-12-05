"""Tests for Cassandra API client."""

import unittest
from unittest.mock import MagicMock, patch

from requests.exceptions import HTTPError, JSONDecodeError, RequestException
from requests.models import Response

from app.common.apis.cassandra.client import CassandraClient
from app.common.apis.cassandra.dtos import (
    BalanceResponse,
    PayoutCreateRequest,
    PayoutResponse,
    QuoteResponse,
    RecipientResponse,
    TokenBalance,
)
from app.common.apis.cassandra.errors import CassandraAPIClientError
from app.common.errors import MissingCredentialsError

# Test constants
ACCOUNT_TRANSFER = "transfer"
CURRENCY_USD = "USD"
CURRENCY_COP = "COP"
USER_ID_TEST = "user123"
WALLET_ID_TEST = "wallet123"
QUOTE_ID_TEST = "quote123"
API_URL = "https://api.example.com"
API_KEY = "test-api-key"
PATCH_SECRETS = "app.common.apis.cassandra.client.get_secret"
PATCH_AGENT = "app.common.apis.cassandra.client.RESTfulAPIAgent"


class TestCassandraClient(unittest.TestCase):
    """Test cases for CassandraClient."""

    @patch(PATCH_AGENT)
    @patch(PATCH_SECRETS)
    def test_init_success(self, mock_get_secret, mock_agent_class):
        """Test successful client initialization."""
        mock_get_secret.side_effect = lambda key: API_URL if key == "CASSANDRA_API_URL" else API_KEY
        mock_agent = MagicMock()
        mock_agent_class.return_value = mock_agent

        client = CassandraClient()

        self.assertEqual(client._api_key, API_KEY)
        self.assertFalse(client._api_key_is_valid)
        mock_agent_class.assert_called_once()

    @patch(PATCH_SECRETS)
    def test_init_missing_url(self, mock_get_secret):
        """Test initialization with missing API URL."""
        mock_get_secret.return_value = None

        with self.assertRaises(MissingCredentialsError):
            CassandraClient()

    @patch(PATCH_SECRETS)
    def test_init_missing_api_key(self, mock_get_secret):
        """Test initialization with missing API key."""
        mock_get_secret.side_effect = lambda key: API_URL if key == "CASSANDRA_API_URL" else None

        with self.assertRaises(MissingCredentialsError):
            CassandraClient()

    @patch(PATCH_AGENT)
    @patch(PATCH_SECRETS)
    def test_get_quote_success(self, mock_get_secret, mock_agent_class):
        """Test successful quote retrieval."""
        mock_get_secret.side_effect = lambda key: API_URL if key == "CASSANDRA_API_URL" else API_KEY
        mock_agent = MagicMock()
        mock_agent_class.return_value = mock_agent
        mock_response = MagicMock(spec=Response)
        mock_response.json.return_value = {
            "quote_id": QUOTE_ID_TEST,
            "base_currency": CURRENCY_USD,
            "quote_currency": CURRENCY_COP,
            "base_amount": 100.0,
            "quote_amount": 1000.0,
            "rate": 10.0,
            "balam_rate": 1.5,
            "fixed_fee": 0,
            "pct_fee": 0,
            "status": "active",
            "expiration_ts": "2024-01-01T00:00:00",
            "expiration_ts_utc": "2024-01-01T00:00:00Z",
        }
        mock_agent.make_request.return_value = mock_response

        client = CassandraClient()
        result = client.get_quote(ACCOUNT_TRANSFER, 100.0, CURRENCY_USD, CURRENCY_COP)

        self.assertIsInstance(result, QuoteResponse)
        self.assertEqual(result.quote_id, QUOTE_ID_TEST)
        mock_agent.update_headers.assert_called_once_with({"X-API-KEY": API_KEY})

    @patch(PATCH_AGENT)
    @patch(PATCH_SECRETS)
    def test_get_quote_json_error(self, mock_get_secret, mock_agent_class):
        """Test quote retrieval with JSON decode error."""
        mock_get_secret.side_effect = lambda key: API_URL if key == "CASSANDRA_API_URL" else API_KEY
        mock_agent = MagicMock()
        mock_agent_class.return_value = mock_agent
        mock_response = MagicMock(spec=Response)
        mock_response.json.side_effect = JSONDecodeError("Invalid JSON", "", 0)
        mock_agent.make_request.return_value = mock_response

        client = CassandraClient()
        with self.assertRaises(CassandraAPIClientError):
            client.get_quote(ACCOUNT_TRANSFER, 100.0, CURRENCY_USD, CURRENCY_COP)

    @patch(PATCH_AGENT)
    @patch(PATCH_SECRETS)
    def test_get_recipients_success_list(self, mock_get_secret, mock_agent_class):
        """Test successful recipients retrieval with list response."""
        mock_get_secret.side_effect = lambda key: API_URL if key == "CASSANDRA_API_URL" else API_KEY
        mock_agent = MagicMock()
        mock_agent_class.return_value = mock_agent
        mock_response = MagicMock(spec=Response)
        mock_response.json.return_value = [
            {
                "recipient_id": "1",
                "first_name": "John",
                "last_name": "Doe",
                "account_type": "PSE",
            },
        ]
        mock_agent.make_request.return_value = mock_response

        client = CassandraClient()
        result = client.get_recipients(ACCOUNT_TRANSFER, USER_ID_TEST)

        self.assertIsInstance(result, list)
        self.assertEqual(len(result), 1)
        self.assertIsInstance(result[0], RecipientResponse)

    @patch(PATCH_AGENT)
    @patch(PATCH_SECRETS)
    def test_get_recipients_success_dict(self, mock_get_secret, mock_agent_class):
        """Test successful recipients retrieval with dict response."""
        mock_get_secret.side_effect = lambda key: API_URL if key == "CASSANDRA_API_URL" else API_KEY
        mock_agent = MagicMock()
        mock_agent_class.return_value = mock_agent
        mock_response = MagicMock(spec=Response)
        mock_response.json.return_value = {
            "recipient_id": "1",
            "first_name": "John",
            "last_name": "Doe",
            "account_type": "PSE",
        }
        mock_agent.make_request.return_value = mock_response

        client = CassandraClient()
        result = client.get_recipients(ACCOUNT_TRANSFER, USER_ID_TEST)

        self.assertIsInstance(result, list)
        self.assertEqual(len(result), 1)

    @patch(PATCH_AGENT)
    @patch(PATCH_SECRETS)
    def test_get_balance_success(self, mock_get_secret, mock_agent_class):
        """Test successful balance retrieval."""
        mock_get_secret.side_effect = lambda key: API_URL if key == "CASSANDRA_API_URL" else API_KEY
        mock_agent = MagicMock()
        mock_agent_class.return_value = mock_agent
        mock_response = MagicMock(spec=Response)
        mock_response.json.return_value = {
            "wallet_id": WALLET_ID_TEST,
            "network": "polygon",
            "balances": [
                {"token": "USDC", "amount": "1000.0", "decimals": 6},
            ],
        }
        mock_agent.make_request.return_value = mock_response

        client = CassandraClient()
        result = client.get_balance(ACCOUNT_TRANSFER, WALLET_ID_TEST)

        self.assertIsInstance(result, BalanceResponse)
        self.assertEqual(result.wallet_id, WALLET_ID_TEST)

    @patch(PATCH_AGENT)
    @patch(PATCH_SECRETS)
    def test_create_payout_success(self, mock_get_secret, mock_agent_class):
        """Test successful payout creation."""
        mock_get_secret.side_effect = lambda key: API_URL if key == "CASSANDRA_API_URL" else API_KEY
        mock_agent = MagicMock()
        mock_agent_class.return_value = mock_agent
        mock_response = MagicMock(spec=Response)
        mock_response.json.return_value = {
            "payout_id": "payout123",
            "user_id": USER_ID_TEST,
            "recipient_id": "rec123",
            "quote_id": QUOTE_ID_TEST,
            "from_amount": "100.0",
            "from_currency": CURRENCY_USD,
            "to_amount": "1000.0",
            "to_currency": CURRENCY_COP,
            "status": "pending",
            "created_at": "2024-01-01T00:00:00",
            "updated_at": "2024-01-01T00:00:00",
        }
        mock_agent.make_request.return_value = mock_response

        payout_data = PayoutCreateRequest(
            recipient_id="rec123",
            wallet_id=WALLET_ID_TEST,
            base_currency=CURRENCY_USD,
            quote_currency=CURRENCY_COP,
            amount=100.0,
            quote_id=QUOTE_ID_TEST,
            quote={"quote_id": QUOTE_ID_TEST},
            token="USDC",
        )

        client = CassandraClient()
        result = client.create_payout(ACCOUNT_TRANSFER, payout_data)

        self.assertIsInstance(result, PayoutResponse)
        self.assertEqual(result.payout_id, "payout123")

    @patch(PATCH_AGENT)
    @patch(PATCH_SECRETS)
    def test_authenticate_first_time(self, mock_get_secret, mock_agent_class):
        """Test authentication on first call."""
        mock_get_secret.side_effect = lambda key: API_URL if key == "CASSANDRA_API_URL" else API_KEY
        mock_agent = MagicMock()
        mock_agent_class.return_value = mock_agent
        mock_response = MagicMock(spec=Response)
        mock_response.json.return_value = {
            "quote_id": QUOTE_ID_TEST,
            "base_currency": CURRENCY_USD,
            "quote_currency": CURRENCY_COP,
            "base_amount": 100.0,
            "quote_amount": 1000.0,
            "rate": 10.0,
            "balam_rate": 1.5,
            "fixed_fee": 0,
            "pct_fee": 0,
            "status": "active",
            "expiration_ts": "2024-01-01T00:00:00",
            "expiration_ts_utc": "2024-01-01T00:00:00Z",
        }
        mock_agent.make_request.return_value = mock_response

        client = CassandraClient()
        client.get_quote(ACCOUNT_TRANSFER, 100.0, CURRENCY_USD, CURRENCY_COP)

        mock_agent.update_headers.assert_called_once_with({"X-API-KEY": API_KEY})
        self.assertTrue(client._api_key_is_valid)

    @patch(PATCH_AGENT)
    @patch(PATCH_SECRETS)
    def test_authenticate_skip_if_valid(self, mock_get_secret, mock_agent_class):
        """Test authentication is skipped if already valid."""
        mock_get_secret.side_effect = lambda key: API_URL if key == "CASSANDRA_API_URL" else API_KEY
        mock_agent = MagicMock()
        mock_agent_class.return_value = mock_agent
        mock_response = MagicMock(spec=Response)
        mock_response.json.return_value = {
            "quote_id": QUOTE_ID_TEST,
            "base_currency": CURRENCY_USD,
            "quote_currency": CURRENCY_COP,
            "base_amount": 100.0,
            "quote_amount": 1000.0,
            "rate": 10.0,
            "balam_rate": 1.5,
            "fixed_fee": 0,
            "pct_fee": 0,
            "status": "active",
            "expiration_ts": "2024-01-01T00:00:00",
            "expiration_ts_utc": "2024-01-01T00:00:00Z",
        }
        mock_agent.make_request.return_value = mock_response

        client = CassandraClient()
        client._api_key_is_valid = True
        client.get_quote(ACCOUNT_TRANSFER, 100.0, CURRENCY_USD, CURRENCY_COP)

        mock_agent.update_headers.assert_not_called()

    @patch(PATCH_AGENT)
    @patch(PATCH_SECRETS)
    def test_get_json_from_response_value_error(self, mock_get_secret, mock_agent_class):
        """Test JSON parsing with ValueError."""
        mock_get_secret.side_effect = lambda key: API_URL if key == "CASSANDRA_API_URL" else API_KEY
        mock_agent = MagicMock()
        mock_agent_class.return_value = mock_agent
        mock_response = MagicMock(spec=Response)
        mock_response.json.side_effect = ValueError("Invalid value")
        mock_agent.make_request.return_value = mock_response

        client = CassandraClient()
        with self.assertRaises(CassandraAPIClientError):
            client.get_quote(ACCOUNT_TRANSFER, 100.0, CURRENCY_USD, CURRENCY_COP)

    @patch(PATCH_AGENT)
    @patch(PATCH_SECRETS)
    def test_get_json_from_response_type_error(self, mock_get_secret, mock_agent_class):
        """Test JSON parsing with TypeError."""
        mock_get_secret.side_effect = lambda key: API_URL if key == "CASSANDRA_API_URL" else API_KEY
        mock_agent = MagicMock()
        mock_agent_class.return_value = mock_agent
        mock_response = MagicMock(spec=Response)
        mock_response.json.side_effect = TypeError("Invalid type")
        mock_agent.make_request.return_value = mock_response

        client = CassandraClient()
        with self.assertRaises(CassandraAPIClientError):
            client.get_quote(ACCOUNT_TRANSFER, 100.0, CURRENCY_USD, CURRENCY_COP)

