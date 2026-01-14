"""Tests for monetization service."""

import unittest
from unittest.mock import MagicMock, patch

from app.common.apis.cassandra.dtos import (
    ExternalWalletCreateRequest,
    ExternalWalletResponse,
    ExternalWalletUpdateRequest,
)
from app.common.apis.cassandra.errors import CassandraAPIClientError
from app.common.errors import MissingCredentialsError
from app.monetization.service import MonetizationService

PATCH_CLIENT = "app.monetization.service.CassandraClient"


class TestMonetizationService(unittest.TestCase):
    """Test cases for MonetizationService."""

    @patch(PATCH_CLIENT)
    def test_get_external_wallets_exception(self, mock_client_class):
        """Test get_external_wallets when generic exception occurs."""
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client
        mock_client.get_external_wallets.side_effect = Exception("Unexpected error")

        with self.assertRaises(Exception) as context:
            MonetizationService.get_external_wallets()

        self.assertIn("Unexpected error", str(context.exception))

    @patch(PATCH_CLIENT)
    def test_create_external_wallet_exception(self, mock_client_class):
        """Test create_external_wallet when generic exception occurs."""
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client
        wallet_data = ExternalWalletCreateRequest(
            external_wallet_id="123e4567-e89b-12d3-a456-426614174001",
            name="Test Wallet",
            category="VAULT",
            supplier_prefunding=True,
            b2c_funding=False,
            enabled=True,
        )
        mock_client.create_external_wallet.side_effect = Exception("Unexpected error")

        with self.assertRaises(Exception) as context:
            MonetizationService.create_external_wallet(wallet_data=wallet_data)

        self.assertIn("Unexpected error", str(context.exception))

    @patch(PATCH_CLIENT)
    def test_update_external_wallet_exception(self, mock_client_class):
        """Test update_external_wallet when generic exception occurs."""
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client
        wallet_data = ExternalWalletUpdateRequest(
            name="Updated Wallet",
            enabled=False,
        )
        mock_client.update_external_wallet.side_effect = Exception("Unexpected error")

        with self.assertRaises(Exception) as context:
            MonetizationService.update_external_wallet(
                wallet_id="test-id", wallet_data=wallet_data
            )

        self.assertIn("Unexpected error", str(context.exception))

    @patch(PATCH_CLIENT)
    def test_delete_external_wallet_exception(self, mock_client_class):
        """Test delete_external_wallet when generic exception occurs."""
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client
        mock_client.delete_external_wallet.side_effect = Exception("Unexpected error")

        with self.assertRaises(Exception) as context:
            MonetizationService.delete_external_wallet(wallet_id="test-id")

        self.assertIn("Unexpected error", str(context.exception))

    @patch(PATCH_CLIENT)
    def test_get_external_wallets_cassandra_error(self, mock_client_class):
        """Test get_external_wallets when CassandraAPIClientError occurs."""
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client
        mock_client.get_external_wallets.side_effect = CassandraAPIClientError(
            "Cassandra API error"
        )

        with self.assertRaises(CassandraAPIClientError):
            MonetizationService.get_external_wallets()

    @patch(PATCH_CLIENT)
    def test_create_external_wallet_cassandra_error(self, mock_client_class):
        """Test create_external_wallet when CassandraAPIClientError occurs."""
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client
        wallet_data = ExternalWalletCreateRequest(
            external_wallet_id="123e4567-e89b-12d3-a456-426614174001",
            name="Test Wallet",
            category="VAULT",
            supplier_prefunding=True,
            b2c_funding=False,
            enabled=True,
        )
        mock_client.create_external_wallet.side_effect = CassandraAPIClientError(
            "Cassandra API error"
        )

        with self.assertRaises(CassandraAPIClientError):
            MonetizationService.create_external_wallet(wallet_data=wallet_data)

    @patch(PATCH_CLIENT)
    def test_update_external_wallet_cassandra_error(self, mock_client_class):
        """Test update_external_wallet when CassandraAPIClientError occurs."""
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client
        wallet_data = ExternalWalletUpdateRequest(
            name="Updated Wallet",
            enabled=False,
        )
        mock_client.update_external_wallet.side_effect = CassandraAPIClientError(
            "Cassandra API error"
        )

        with self.assertRaises(CassandraAPIClientError):
            MonetizationService.update_external_wallet(
                wallet_id="test-id", wallet_data=wallet_data
            )

    @patch(PATCH_CLIENT)
    def test_delete_external_wallet_cassandra_error(self, mock_client_class):
        """Test delete_external_wallet when CassandraAPIClientError occurs."""
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client
        mock_client.delete_external_wallet.side_effect = CassandraAPIClientError(
            "Cassandra API error"
        )

        with self.assertRaises(CassandraAPIClientError):
            MonetizationService.delete_external_wallet(wallet_id="test-id")

    @patch(PATCH_CLIENT)
    def test_get_external_wallets_success(self, mock_client_class):
        """Test get_external_wallets successfully."""
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client
        mock_wallet = ExternalWalletResponse(
            id="test-id",
            external_wallet_id="external-id",
            name="Test Wallet",
            category="VAULT",
            supplier_prefunding=True,
            b2c_funding=True,
            enabled=True,
            created_at="2026-01-14T16:53:32.251713+00:00",
            updated_at="2026-01-14T16:54:21.397067+00:00",
        )
        mock_client.get_external_wallets.return_value = [mock_wallet]

        result = MonetizationService.get_external_wallets()

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].id, "test-id")
        mock_client.get_external_wallets.assert_called_once()

    @patch(PATCH_CLIENT)
    def test_create_external_wallet_success(self, mock_client_class):
        """Test create_external_wallet successfully."""
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client
        wallet_data = ExternalWalletCreateRequest(
            external_wallet_id="123e4567-e89b-12d3-a456-426614174001",
            name="Test Wallet",
            category="VAULT",
            supplier_prefunding=True,
            b2c_funding=False,
            enabled=True,
        )
        mock_wallet = ExternalWalletResponse(
            id="test-id",
            external_wallet_id="123e4567-e89b-12d3-a456-426614174001",
            name="Test Wallet",
            category="VAULT",
            supplier_prefunding=True,
            b2c_funding=False,
            enabled=True,
            created_at="2026-01-14T16:53:32.251713+00:00",
            updated_at="2026-01-14T16:54:21.397067+00:00",
        )
        mock_client.create_external_wallet.return_value = mock_wallet

        result = MonetizationService.create_external_wallet(wallet_data=wallet_data)

        self.assertEqual(result.id, "test-id")
        mock_client.create_external_wallet.assert_called_once_with(wallet_data=wallet_data)

    @patch(PATCH_CLIENT)
    def test_update_external_wallet_success(self, mock_client_class):
        """Test update_external_wallet successfully."""
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client
        wallet_data = ExternalWalletUpdateRequest(
            name="Updated Wallet",
            enabled=False,
        )
        mock_wallet = ExternalWalletResponse(
            id="test-id",
            external_wallet_id="external-id",
            name="Updated Wallet",
            category="VAULT",
            supplier_prefunding=True,
            b2c_funding=True,
            enabled=False,
            created_at="2026-01-14T16:53:32.251713+00:00",
            updated_at="2026-01-14T16:54:21.397067+00:00",
        )
        mock_client.update_external_wallet.return_value = mock_wallet

        result = MonetizationService.update_external_wallet(
            wallet_id="test-id", wallet_data=wallet_data
        )

        self.assertEqual(result.name, "Updated Wallet")
        mock_client.update_external_wallet.assert_called_once_with(
            wallet_id="test-id", wallet_data=wallet_data
        )

    @patch(PATCH_CLIENT)
    def test_delete_external_wallet_success(self, mock_client_class):
        """Test delete_external_wallet successfully."""
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client
        mock_client.delete_external_wallet.return_value = None

        result = MonetizationService.delete_external_wallet(wallet_id="test-id")

        self.assertIsNone(result)
        mock_client.delete_external_wallet.assert_called_once_with(wallet_id="test-id")


if __name__ == "__main__":
    unittest.main()
