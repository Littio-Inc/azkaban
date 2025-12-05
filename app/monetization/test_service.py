"""Tests for monetization service."""

import unittest
from unittest.mock import MagicMock, patch

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
from app.monetization.service import MonetizationService

# Test constants
ACCOUNT_TRANSFER = "transfer"
CURRENCY_USD = "USD"
CURRENCY_COP = "COP"
TOKEN_USDC = "USDC"
USER_ID_TEST = "user123"
WALLET_ID_TEST = "wallet123"
RECIPIENT_ID_TEST = "rec123"
QUOTE_ID_TEST = "quote123"
API_ERROR_MSG = "API error"
UNEXPECTED_ERROR_MSG = "Unexpected error"
PATCH_PATH = "app.monetization.service.CassandraClient"


class TestMonetizationService(unittest.TestCase):
    """Test cases for MonetizationService."""

    @patch(PATCH_PATH)
    def test_get_quote_success(self, mock_client_class):
        """Test successful quote retrieval."""
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client
        expected_quote = QuoteResponse(
            quote_id=QUOTE_ID_TEST,
            base_currency=CURRENCY_USD,
            quote_currency=CURRENCY_COP,
            base_amount=100.0,
            quote_amount=1000.0,
            rate=10.0,
            balam_rate=1.5,
            fixed_fee=0,
            pct_fee=0,
            status="active",
            expiration_ts="2024-01-01T00:00:00",
            expiration_ts_utc="2024-01-01T00:00:00Z",
        )
        mock_client.get_quote.return_value = expected_quote

        result = MonetizationService.get_quote(ACCOUNT_TRANSFER, 100.0, CURRENCY_USD, CURRENCY_COP)

        self.assertEqual(result.quote_id, expected_quote.quote_id)
        self.assertEqual(result.quote_amount, expected_quote.quote_amount)
        mock_client.get_quote.assert_called_once_with(ACCOUNT_TRANSFER, 100.0, CURRENCY_USD, CURRENCY_COP)

    @patch(PATCH_PATH)
    def test_get_quote_api_error(self, mock_client_class):
        """Test quote retrieval with API error."""
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client
        mock_client.get_quote.side_effect = CassandraAPIClientError(API_ERROR_MSG)

        with self.assertRaises(CassandraAPIClientError):
            MonetizationService.get_quote(ACCOUNT_TRANSFER, 100.0, CURRENCY_USD, CURRENCY_COP)

    @patch(PATCH_PATH)
    def test_get_recipients_success(self, mock_client_class):
        """Test successful recipients retrieval."""
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client
        expected_recipients = [
            RecipientResponse(
                recipient_id="1",
                first_name="Recipient",
                last_name="One",
                account_type="PSE",
            ),
            RecipientResponse(
                recipient_id="2",
                first_name="Recipient",
                last_name="Two",
                account_type="SPEI",
            ),
        ]
        mock_client.get_recipients.return_value = expected_recipients

        result = MonetizationService.get_recipients(ACCOUNT_TRANSFER, USER_ID_TEST)

        self.assertEqual(len(result), 2)
        self.assertEqual(result[0].recipient_id, "1")
        mock_client.get_recipients.assert_called_once_with(ACCOUNT_TRANSFER, USER_ID_TEST)

    @patch(PATCH_PATH)
    def test_get_recipients_api_error(self, mock_client_class):
        """Test recipients retrieval with API error."""
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client
        mock_client.get_recipients.side_effect = CassandraAPIClientError(API_ERROR_MSG)

        with self.assertRaises(CassandraAPIClientError):
            MonetizationService.get_recipients(ACCOUNT_TRANSFER, USER_ID_TEST)

    @patch(PATCH_PATH)
    def test_get_balance_success(self, mock_client_class):
        """Test successful balance retrieval."""
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client
        expected_balance = BalanceResponse(
            wallet_id=WALLET_ID_TEST,
            network="polygon",
            balances=[
                TokenBalance(token=TOKEN_USDC, amount="1000.0", decimals=6),
            ],
        )
        mock_client.get_balance.return_value = expected_balance

        result = MonetizationService.get_balance(ACCOUNT_TRANSFER, WALLET_ID_TEST)

        self.assertEqual(result.wallet_id, expected_balance.wallet_id)
        self.assertEqual(len(result.balances), 1)
        mock_client.get_balance.assert_called_once_with(ACCOUNT_TRANSFER, WALLET_ID_TEST)

    @patch(PATCH_PATH)
    def test_get_balance_api_error(self, mock_client_class):
        """Test balance retrieval with API error."""
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client
        mock_client.get_balance.side_effect = CassandraAPIClientError(API_ERROR_MSG)

        with self.assertRaises(CassandraAPIClientError):
            MonetizationService.get_balance(ACCOUNT_TRANSFER, WALLET_ID_TEST)

    @patch(PATCH_PATH)
    def test_create_payout_success(self, mock_client_class):
        """Test successful payout creation."""
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client
        payout_data = PayoutCreateRequest(
            recipient_id=RECIPIENT_ID_TEST,
            wallet_id=WALLET_ID_TEST,
            base_currency=CURRENCY_USD,
            quote_currency=CURRENCY_COP,
            amount=100.0,
            quote_id=QUOTE_ID_TEST,
            quote={"quote_id": QUOTE_ID_TEST},
            token=TOKEN_USDC,
        )
        expected_response = PayoutResponse(
            payout_id="payout123",
            user_id=USER_ID_TEST,
            recipient_id=RECIPIENT_ID_TEST,
            quote_id=QUOTE_ID_TEST,
            from_amount="100.0",
            from_currency=CURRENCY_USD,
            to_amount="1000.0",
            to_currency=CURRENCY_COP,
            status="pending",
            created_at="2024-01-01T00:00:00",
            updated_at="2024-01-01T00:00:00",
        )
        mock_client.create_payout.return_value = expected_response

        result = MonetizationService.create_payout(ACCOUNT_TRANSFER, payout_data)

        self.assertEqual(result.payout_id, expected_response.payout_id)
        self.assertEqual(result.status, expected_response.status)
        mock_client.create_payout.assert_called_once_with(ACCOUNT_TRANSFER, payout_data)

    @patch(PATCH_PATH)
    def test_create_payout_api_error(self, mock_client_class):
        """Test payout creation with API error."""
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client
        payout_data = PayoutCreateRequest(
            recipient_id=RECIPIENT_ID_TEST,
            wallet_id=WALLET_ID_TEST,
            base_currency=CURRENCY_USD,
            quote_currency=CURRENCY_COP,
            amount=100.0,
            quote_id=QUOTE_ID_TEST,
            quote={"quote_id": QUOTE_ID_TEST},
            token=TOKEN_USDC,
        )
        mock_client.create_payout.side_effect = CassandraAPIClientError(API_ERROR_MSG)

        with self.assertRaises(CassandraAPIClientError):
            MonetizationService.create_payout(ACCOUNT_TRANSFER, payout_data)

    @patch(PATCH_PATH)
    def test_get_quote_missing_credentials(self, mock_client_class):
        """Test quote retrieval with missing credentials."""
        mock_client_class.side_effect = MissingCredentialsError("Missing credentials")

        with self.assertRaises(MissingCredentialsError):
            MonetizationService.get_quote(ACCOUNT_TRANSFER, 100.0, CURRENCY_USD, CURRENCY_COP)

    @patch(PATCH_PATH)
    def test_get_quote_unexpected_error(self, mock_client_class):
        """Test quote retrieval with unexpected error."""
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client
        mock_client.get_quote.side_effect = ValueError(UNEXPECTED_ERROR_MSG)

        with self.assertRaises(ValueError):
            MonetizationService.get_quote(ACCOUNT_TRANSFER, 100.0, CURRENCY_USD, CURRENCY_COP)

    @patch(PATCH_PATH)
    def test_get_recipients_unexpected_error(self, mock_client_class):
        """Test recipients retrieval with unexpected error."""
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client
        mock_client.get_recipients.side_effect = ValueError(UNEXPECTED_ERROR_MSG)

        with self.assertRaises(ValueError):
            MonetizationService.get_recipients(ACCOUNT_TRANSFER, USER_ID_TEST)

    @patch(PATCH_PATH)
    def test_get_balance_unexpected_error(self, mock_client_class):
        """Test balance retrieval with unexpected error."""
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client
        mock_client.get_balance.side_effect = ValueError(UNEXPECTED_ERROR_MSG)

        with self.assertRaises(ValueError):
            MonetizationService.get_balance(ACCOUNT_TRANSFER, WALLET_ID_TEST)

    @patch(PATCH_PATH)
    def test_create_payout_unexpected_error(self, mock_client_class):
        """Test payout creation with unexpected error."""
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client
        payout_data = PayoutCreateRequest(
            recipient_id=RECIPIENT_ID_TEST,
            wallet_id=WALLET_ID_TEST,
            base_currency=CURRENCY_USD,
            quote_currency=CURRENCY_COP,
            amount=100.0,
            quote_id=QUOTE_ID_TEST,
            quote={"quote_id": QUOTE_ID_TEST},
            token=TOKEN_USDC,
        )
        mock_client.create_payout.side_effect = ValueError(UNEXPECTED_ERROR_MSG)

        with self.assertRaises(ValueError):
            MonetizationService.create_payout(ACCOUNT_TRANSFER, payout_data)
