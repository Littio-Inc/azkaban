"""Tests for Diagon API client."""

import unittest
from unittest.mock import MagicMock, patch

from app.common.apis.diagon.client import DiagonClient
from app.common.apis.diagon.dtos import AccountResponse, RefreshBalanceResponse

PATCH_AGENT = "app.common.apis.diagon.client.DiagonAgent"


class TestDiagonClient(unittest.TestCase):
    """Test cases for DiagonClient."""

    @patch(PATCH_AGENT)
    def test_get_accounts_success(self, mock_agent_class):
        """Test getting accounts successfully."""
        mock_agent = MagicMock()
        mock_agent_class.return_value = mock_agent

        mock_response_data = [
            {
                "id": "1",
                "name": "Test Account",
                "hiddenOnUI": False,
                "autoFuel": False,
                "assets": []
            }
        ]
        mock_agent.get.return_value = mock_response_data

        client = DiagonClient()
        result = client.get_accounts()

        self.assertIsInstance(result, list)
        self.assertEqual(len(result), 1)
        self.assertIsInstance(result[0], AccountResponse)
        self.assertEqual(result[0].id, "1")
        self.assertEqual(result[0].name, "Test Account")
        mock_agent.get.assert_called_once_with(req_path="/vault/accounts")

    @patch(PATCH_AGENT)
    def test_get_accounts_empty_list(self, mock_agent_class):
        """Test getting accounts with empty list."""
        mock_agent = MagicMock()
        mock_agent_class.return_value = mock_agent

        mock_agent.get.return_value = []

        client = DiagonClient()
        result = client.get_accounts()

        self.assertIsInstance(result, list)
        self.assertEqual(len(result), 0)

    @patch(PATCH_AGENT)
    def test_refresh_balance_success(self, mock_agent_class):
        """Test refreshing balance successfully."""
        mock_agent = MagicMock()
        mock_agent_class.return_value = mock_agent

        account_id = "account-123"
        asset = "USDC_POLYGON"
        mock_response_data = {
            "message": "Balance refresh initiated successfully",
            "idempotencyKey": "key-123"
        }
        mock_agent.post.return_value = mock_response_data

        client = DiagonClient()
        result = client.refresh_balance(account_id, asset)

        self.assertIsInstance(result, RefreshBalanceResponse)
        self.assertEqual(result.message, "Balance refresh initiated successfully")
        self.assertEqual(result.idempotencyKey, "key-123")
        mock_agent.post.assert_called_once_with(
            req_path=f"/vault/accounts/{account_id}/{asset}/balance"
        )


if __name__ == "__main__":
    unittest.main()

