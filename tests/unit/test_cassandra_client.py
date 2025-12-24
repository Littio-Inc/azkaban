"""Tests for Cassandra API client."""

import unittest
from unittest.mock import MagicMock, patch

from app.common.apis.cassandra.client import CassandraClient
from app.common.apis.cassandra.dtos import (
    BalanceResponse,
    PayoutCreateRequest,
    PayoutResponse,
    QuoteResponse,
    RecipientResponse,
)
from app.common.apis.cassandra.errors import CassandraAPIClientError
from app.common.errors import MissingCredentialsError

from tests.fixtures import (
    QUOTE_ID_TEST,
    TEST_TIMESTAMP,
    TEST_TIMESTAMP_UTC,
    create_test_quote_response,
)

# Test constants
ACCOUNT_TRANSFER = "transfer"
CURRENCY_USD = "USD"
CURRENCY_COP = "COP"
USER_ID_TEST = "user123"
WALLET_ID_TEST = "wallet123"
API_URL = "https://api.example.com"
API_KEY = "test-api-key"
PATCH_SECRETS = "app.common.apis.cassandra.agent.get_secret"
PATCH_AGENT = "app.common.apis.cassandra.client.CassandraAgent"


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

        self.assertIsNotNone(client._agent)
        mock_agent_class.assert_called_once()

    @patch(PATCH_AGENT)
    @patch(PATCH_SECRETS)
    def test_init_missing_url(self, mock_get_secret, mock_agent_class):
        """Test initialization with missing API URL."""
        mock_get_secret.return_value = None
        mock_agent_class.side_effect = MissingCredentialsError("Missing credentials for Cassandra API.")

        with self.assertRaises(MissingCredentialsError):
            CassandraClient()

    @patch(PATCH_AGENT)
    @patch(PATCH_SECRETS)
    def test_init_missing_api_key(self, mock_get_secret, mock_agent_class):
        """Test initialization with missing API key."""
        mock_get_secret.side_effect = lambda key: API_URL if key == "CASSANDRA_API_URL" else None
        mock_agent_class.side_effect = MissingCredentialsError("Missing credentials for Cassandra API.")

        with self.assertRaises(MissingCredentialsError):
            CassandraClient()

    @patch(PATCH_AGENT)
    @patch(PATCH_SECRETS)
    def test_get_quote_success(self, mock_get_secret, mock_agent_class):
        """Test successful quote retrieval."""
        mock_get_secret.side_effect = lambda key: API_URL if key == "CASSANDRA_API_URL" else API_KEY
        mock_agent = MagicMock()
        mock_agent_class.return_value = mock_agent
        mock_agent.get.return_value = {
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
            "expiration_ts": TEST_TIMESTAMP,
            "expiration_ts_utc": TEST_TIMESTAMP_UTC,
        }

        client = CassandraClient()
        result = client.get_quote(ACCOUNT_TRANSFER, 100.0, CURRENCY_USD, CURRENCY_COP, "kira")

        self.assertIsInstance(result, QuoteResponse)
        self.assertEqual(result.quote_id, QUOTE_ID_TEST)
        mock_agent.get.assert_called_once()

    @patch(PATCH_AGENT)
    @patch(PATCH_SECRETS)
    def test_get_quote_json_error(self, mock_get_secret, mock_agent_class):
        """Test quote retrieval with JSON decode error."""
        mock_get_secret.side_effect = lambda key: API_URL if key == "CASSANDRA_API_URL" else API_KEY
        mock_agent = MagicMock()
        mock_agent_class.return_value = mock_agent
        mock_agent.get.side_effect = CassandraAPIClientError("Error decoding JSON response")

        client = CassandraClient()
        with self.assertRaises(CassandraAPIClientError):
            client.get_quote(ACCOUNT_TRANSFER, 100.0, CURRENCY_USD, CURRENCY_COP, "kira")

    @patch(PATCH_AGENT)
    @patch(PATCH_SECRETS)
    def test_get_recipients_success_list(self, mock_get_secret, mock_agent_class):
        """Test successful recipients retrieval with list response."""
        mock_get_secret.side_effect = lambda key: API_URL if key == "CASSANDRA_API_URL" else API_KEY
        mock_agent = MagicMock()
        mock_agent_class.return_value = mock_agent
        mock_agent.get.return_value = [
            {
                "recipient_id": "1",
                "first_name": "John",
                "last_name": "Doe",
                "account_type": "PSE",
            },
        ]

        client = CassandraClient()
        result = client.get_recipients(ACCOUNT_TRANSFER, USER_ID_TEST, "kira")

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
        mock_agent.get.return_value = {
            "recipient_id": "1",
            "first_name": "John",
            "last_name": "Doe",
            "account_type": "PSE",
        }

        client = CassandraClient()
        result = client.get_recipients(ACCOUNT_TRANSFER, USER_ID_TEST, "kira")

        self.assertIsInstance(result, list)
        self.assertEqual(len(result), 1)

    @patch(PATCH_AGENT)
    @patch(PATCH_SECRETS)
    def test_get_balance_success(self, mock_get_secret, mock_agent_class):
        """Test successful balance retrieval."""
        mock_get_secret.side_effect = lambda key: API_URL if key == "CASSANDRA_API_URL" else API_KEY
        mock_agent = MagicMock()
        mock_agent_class.return_value = mock_agent
        mock_agent.get.return_value = {
            "walletId": WALLET_ID_TEST,
            "network": "polygon",
            "balances": [
                {"token": "USDC", "amount": "1000.0", "decimals": 6},
            ],
        }

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
        mock_agent.post.return_value = {
            "payout_id": "payout123",
            "user_id": USER_ID_TEST,
            "recipient_id": "rec123",
            "quote_id": QUOTE_ID_TEST,
            "from_amount": "100.0",
            "from_currency": CURRENCY_USD,
            "to_amount": "1000.0",
            "to_currency": CURRENCY_COP,
            "status": "pending",
            "created_at": TEST_TIMESTAMP,
            "updated_at": TEST_TIMESTAMP,
        }

        payout_data = PayoutCreateRequest(
            recipient_id="rec123",
            wallet_id=WALLET_ID_TEST,
            base_currency=CURRENCY_USD,
            quote_currency=CURRENCY_COP,
            amount=100.0,
            quote_id=QUOTE_ID_TEST,
            quote=create_test_quote_response(),
            token="USDC",
            provider="kira",
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
        mock_agent._api_key_is_valid = False
        
        # Make get() call update_headers to simulate authentication
        def get_side_effect(*args, **kwargs):
            if not mock_agent._api_key_is_valid:
                mock_agent.update_headers({"x-api-key": API_KEY})
                mock_agent._api_key_is_valid = True
            return {
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
        
        mock_agent.get.side_effect = get_side_effect

        client = CassandraClient()
        client.get_quote(ACCOUNT_TRANSFER, 100.0, CURRENCY_USD, CURRENCY_COP, "kira")

        # Verify that get was called (which internally calls _authenticate)
        mock_agent.get.assert_called_once()
        # Verify that update_headers was called with API key during authentication
        mock_agent.update_headers.assert_called_with({"x-api-key": API_KEY})
        # Verify that api_key_is_valid was set to True
        self.assertTrue(mock_agent._api_key_is_valid)

    @patch(PATCH_AGENT)
    @patch(PATCH_SECRETS)
    def test_authenticate_skip_if_valid(self, mock_get_secret, mock_agent_class):
        """Test authentication is skipped if already valid."""
        mock_get_secret.side_effect = lambda key: API_URL if key == "CASSANDRA_API_URL" else API_KEY
        mock_agent = MagicMock()
        mock_agent_class.return_value = mock_agent
        mock_agent.get.return_value = {
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
            "expiration_ts": TEST_TIMESTAMP,
            "expiration_ts_utc": TEST_TIMESTAMP_UTC,
        }
        # Set _api_key_is_valid to True in the agent
        mock_agent._api_key_is_valid = True

        client = CassandraClient()
        client.get_quote(ACCOUNT_TRANSFER, 100.0, CURRENCY_USD, CURRENCY_COP, "kira")

        # update_headers should not be called if already authenticated
        # But get should still be called
        mock_agent.get.assert_called_once()

    @patch(PATCH_AGENT)
    @patch(PATCH_SECRETS)
    def test_get_json_from_response_value_error(self, mock_get_secret, mock_agent_class):
        """Test JSON parsing with ValueError."""
        mock_get_secret.side_effect = lambda key: API_URL if key == "CASSANDRA_API_URL" else API_KEY
        mock_agent = MagicMock()
        mock_agent_class.return_value = mock_agent
        mock_agent.get.side_effect = ValueError("Invalid value")

        client = CassandraClient()
        with self.assertRaises(ValueError):
            client.get_quote(ACCOUNT_TRANSFER, 100.0, CURRENCY_USD, CURRENCY_COP, "kira")

    @patch(PATCH_AGENT)
    @patch(PATCH_SECRETS)
    def test_get_json_from_response_type_error(self, mock_get_secret, mock_agent_class):
        """Test JSON parsing with TypeError."""
        mock_get_secret.side_effect = lambda key: API_URL if key == "CASSANDRA_API_URL" else API_KEY
        mock_agent = MagicMock()
        mock_agent_class.return_value = mock_agent
        mock_agent.get.side_effect = TypeError("Invalid type")

        client = CassandraClient()
        with self.assertRaises(TypeError):
            client.get_quote(ACCOUNT_TRANSFER, 100.0, CURRENCY_USD, CURRENCY_COP, "kira")

