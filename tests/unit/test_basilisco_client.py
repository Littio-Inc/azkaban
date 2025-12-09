"""Tests for Basilisco API client."""

import unittest
from unittest.mock import MagicMock, patch

from app.common.apis.basilisco.client import BasiliscoClient
from app.common.apis.basilisco.dtos import CreateTransactionResponse, TransactionsResponse

PATCH_AGENT = "app.common.apis.basilisco.client.BasiliscoAgent"


class TestBasiliscoClient(unittest.TestCase):
    """Test cases for BasiliscoClient."""

    @patch(PATCH_AGENT)
    def test_get_transactions_success(self, mock_agent_class):
        """Test getting transactions successfully."""
        mock_agent = MagicMock()
        mock_agent_class.return_value = mock_agent

        mock_response_data = {
            "transactions": [{"id": "1", "amount": "100"}],
            "count": 1,
            "page": 1,
            "limit": 10,
        }
        mock_agent.get.return_value = mock_response_data

        client = BasiliscoClient()
        result = client.get_transactions(filters={"provider": "fireblocks"}, page=1, limit=10)

        self.assertIsInstance(result, TransactionsResponse)
        self.assertEqual(result.count, 1)
        self.assertEqual(len(result.transactions), 1)
        mock_agent.get.assert_called_once_with(
            req_path="/v1/backoffice/transactions",
            query_params={"page": 1, "limit": 10, "provider": "fireblocks"}
        )

    @patch(PATCH_AGENT)
    def test_get_transactions_without_provider(self, mock_agent_class):
        """Test getting transactions without provider filter."""
        mock_agent = MagicMock()
        mock_agent_class.return_value = mock_agent

        mock_response_data = {
            "transactions": [],
            "count": 0,
            "page": 1,
            "limit": 10,
        }
        mock_agent.get.return_value = mock_response_data

        client = BasiliscoClient()
        result = client.get_transactions()

        self.assertIsInstance(result, TransactionsResponse)
        self.assertEqual(result.count, 0)
        mock_agent.get.assert_called_once_with(
            req_path="/v1/backoffice/transactions",
            query_params={"page": 1, "limit": 10}
        )

    @patch(PATCH_AGENT)
    def test_create_transaction_success(self, mock_agent_class):
        """Test creating transaction successfully."""
        mock_agent = MagicMock()
        mock_agent_class.return_value = mock_agent

        transaction_id = "test-transaction-id"
        mock_response_data = {"id": transaction_id}
        mock_agent.post.return_value = mock_response_data

        transaction_data = {
            "type": "withdrawal",
            "amount": "1.30",
            "currency": "USD",
        }

        client = BasiliscoClient()
        result = client.create_transaction(transaction_data)

        self.assertIsInstance(result, CreateTransactionResponse)
        self.assertEqual(result.id, transaction_id)
        mock_agent.post.assert_called_once_with(
            req_path="/v1/backoffice/transactions",
            json=transaction_data,
            idempotency_key=None
        )


if __name__ == "__main__":
    unittest.main()

