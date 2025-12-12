"""Tests for Diagon API client."""

import unittest
from unittest.mock import MagicMock, patch

from app.common.apis.diagon.client import DiagonClient
from app.common.apis.diagon.dtos import (
    AccountResponse,
    EstimateFeeRequest,
    EstimateFeeResponse,
    ExternalWallet,
    ExternalWalletsEmptyResponse,
    RefreshBalanceResponse,
    VaultToVaultRequest,
    VaultToVaultResponse,
)

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
    def test_get_accounts_single_object(self, mock_agent_class):
        """Test getting accounts when single object is returned."""
        mock_agent = MagicMock()
        mock_agent_class.return_value = mock_agent

        mock_response_data = {
            "id": "1",
            "name": "Test Account",
            "hiddenOnUI": False,
            "autoFuel": False,
            "assets": []
        }
        mock_agent.get.return_value = mock_response_data

        client = DiagonClient()
        result = client.get_accounts()

        self.assertIsInstance(result, list)
        self.assertEqual(len(result), 1)
        self.assertIsInstance(result[0], AccountResponse)
        self.assertEqual(result[0].id, "1")
        self.assertEqual(result[0].name, "Test Account")

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

    @patch(PATCH_AGENT)
    def test_estimate_fee_success(self, mock_agent_class):
        """Test estimating fee successfully."""
        mock_agent = MagicMock()
        mock_agent_class.return_value = mock_agent

        mock_response_data = {
            "low": {
                "networkFee": "0.001432725180253028",
                "gasPrice": "26.276",
                "gasLimit": "54526",
                "baseFee": "0.000000063",
                "priorityFee": "26.276",
                "l1Fee": "0",
                "maxFeePerGasDelta": "0.000000015"
            },
            "medium": {
                "networkFee": "0.001589651008253028",
                "gasPrice": "29.154",
                "gasLimit": "54526",
                "baseFee": "0.000000063",
                "priorityFee": "29.154",
                "l1Fee": "0",
                "maxFeePerGasDelta": "0.000000015"
            },
            "high": {
                "networkFee": "0.001746522310253028",
                "gasPrice": "32.032",
                "gasLimit": "54526",
                "baseFee": "0.000000063",
                "priorityFee": "32.031",
                "l1Fee": "0",
                "maxFeePerGasDelta": "0.000000015"
            }
        }
        mock_agent.post.return_value = mock_response_data

        request = EstimateFeeRequest(
            operation="TRANSFER",
            source={"type": "VAULT_ACCOUNT", "id": "5"},
            destination={"type": "VAULT_ACCOUNT", "id": "3"},
            assetId="USDC_AMOY_POLYGON_TEST_7WWV",
            amount="1"
        )

        client = DiagonClient()
        result = client.estimate_fee(request)

        self.assertIsInstance(result, EstimateFeeResponse)
        self.assertEqual(result.low.networkFee, "0.001432725180253028")
        self.assertEqual(result.medium.gasPrice, "29.154")
        self.assertEqual(result.high.priorityFee, "32.031")
        mock_agent.post.assert_called_once()
        call_args = mock_agent.post.call_args
        self.assertEqual(call_args.kwargs["req_path"], "/vault/transactions/estimate-fee")
        self.assertIn("json", call_args.kwargs)
        json_data = call_args.kwargs["json"]
        self.assertEqual(json_data["operation"], "TRANSFER")
        self.assertEqual(json_data["assetId"], "USDC_AMOY_POLYGON_TEST_7WWV")
        self.assertEqual(json_data["amount"], "1")

    @patch(PATCH_AGENT)
    def test_get_external_wallets_success(self, mock_agent_class):
        """Test getting external wallets successfully."""
        mock_agent = MagicMock()
        mock_agent_class.return_value = mock_agent

        mock_response_data = [
            {
                "id": "wallet-1",
                "name": "Test Wallet",
                "customerRefId": "customer-123",
                "assets": [
                    {
                        "id": "USDC_POLYGON",
                        "balance": "100.0",
                        "lockedAmount": "0",
                        "status": "WAITING_FOR_APPROVAL",
                        "address": "0x1234567890abcdef",
                        "tag": "",
                        "activationTime": "2024-01-01T00:00:00Z"
                    }
                ]
            }
        ]
        mock_agent.get_external_wallets.return_value = mock_response_data

        client = DiagonClient()
        result = client.get_external_wallets()

        self.assertIsInstance(result, list)
        self.assertEqual(len(result), 1)
        self.assertIsInstance(result[0], ExternalWallet)
        self.assertEqual(result[0].id, "wallet-1")
        self.assertEqual(result[0].name, "Test Wallet")
        self.assertEqual(result[0].customerRefId, "customer-123")
        self.assertEqual(len(result[0].assets), 1)
        self.assertEqual(result[0].assets[0].id, "USDC_POLYGON")
        self.assertEqual(result[0].assets[0].balance, "100.0")
        self.assertEqual(result[0].assets[0].status, "WAITING_FOR_APPROVAL")
        mock_agent.get_external_wallets.assert_called_once()

    @patch(PATCH_AGENT)
    def test_get_external_wallets_empty(self, mock_agent_class):
        """Test getting external wallets when no wallets found."""
        mock_agent = MagicMock()
        mock_agent_class.return_value = mock_agent

        mock_response_data = {
            "message": "No external wallets found",
            "code": 0,
            "data": []
        }
        mock_agent.get_external_wallets.return_value = mock_response_data

        client = DiagonClient()
        result = client.get_external_wallets()

        self.assertIsInstance(result, ExternalWalletsEmptyResponse)
        self.assertEqual(result.message, "No external wallets found")
        self.assertEqual(result.code, 0)
        self.assertEqual(result.data, [])
        mock_agent.get_external_wallets.assert_called_once()

    @patch(PATCH_AGENT)
    def test_get_external_wallets_multiple(self, mock_agent_class):
        """Test getting multiple external wallets."""
        mock_agent = MagicMock()
        mock_agent_class.return_value = mock_agent

        mock_response_data = [
            {
                "id": "wallet-1",
                "name": "Wallet 1",
                "customerRefId": "customer-123",
                "assets": []
            },
            {
                "id": "wallet-2",
                "name": "Wallet 2",
                "customerRefId": "customer-456",
                "assets": [
                    {
                        "id": "BTC",
                        "balance": "0.5",
                        "lockedAmount": "0",
                        "status": "ACTIVE",
                        "address": "bc1qxy2kgdygjrsqtzq2n0yrf2493p83kkfjhx0wlh",
                        "tag": "",
                        "activationTime": "2024-01-01T00:00:00Z"
                    }
                ]
            }
        ]
        mock_agent.get_external_wallets.return_value = mock_response_data

        client = DiagonClient()
        result = client.get_external_wallets()

        self.assertIsInstance(result, list)
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0].id, "wallet-1")
        self.assertEqual(result[1].id, "wallet-2")
        self.assertEqual(len(result[0].assets), 0)
        self.assertEqual(len(result[1].assets), 1)

    @patch(PATCH_AGENT)
    def test_get_external_wallets_single_object(self, mock_agent_class):
        """Test getting external wallets when single object is returned."""
        mock_agent = MagicMock()
        mock_agent_class.return_value = mock_agent

        mock_response_data = {
            "id": "wallet-1",
            "name": "Test Wallet",
            "customerRefId": "customer-123",
            "assets": []
        }
        mock_agent.get_external_wallets.return_value = mock_response_data

        client = DiagonClient()
        result = client.get_external_wallets()

        self.assertIsInstance(result, list)
        self.assertEqual(len(result), 1)
        self.assertIsInstance(result[0], ExternalWallet)
        self.assertEqual(result[0].id, "wallet-1")
        self.assertEqual(result[0].name, "Test Wallet")
        mock_agent.get_external_wallets.assert_called_once()

    @patch(PATCH_AGENT)
    def test_vault_to_vault_success(self, mock_agent_class):
        """Test creating vault-to-vault transaction successfully."""
        mock_agent = MagicMock()
        mock_agent_class.return_value = mock_agent

        mock_response_data = {
            "id": "c5e4379f-b344-4124-89b4-e8e76ea943a4",
            "status": "SUBMITTED"
        }
        mock_agent.post.return_value = mock_response_data

        request = VaultToVaultRequest(
            network="polygon",
            service="BLOCKCHAIN_WITHDRAWAL",
            token="usdc",
            sourceVaultId="5",
            destinationWalletId="0x958be847d9E7E93B897CfCc6A9E7065C273490a9",
            feeLevel="HIGH",
            amount="9.98"
        )

        client = DiagonClient()
        result = client.vault_to_vault(request)

        self.assertIsInstance(result, VaultToVaultResponse)
        self.assertEqual(result.id, "c5e4379f-b344-4124-89b4-e8e76ea943a4")
        self.assertEqual(result.status, "SUBMITTED")
        mock_agent.post.assert_called_once()
        call_args = mock_agent.post.call_args
        self.assertEqual(call_args.kwargs["req_path"], "/vault/transactions/vault-to-vault")
        self.assertIn("json", call_args.kwargs)
        json_data = call_args.kwargs["json"]
        self.assertEqual(json_data["network"], "polygon")
        self.assertEqual(json_data["service"], "BLOCKCHAIN_WITHDRAWAL")
        self.assertEqual(json_data["token"], "usdc")
        self.assertEqual(json_data["sourceVaultId"], "5")
        self.assertEqual(json_data["destinationWalletId"], "0x958be847d9E7E93B897CfCc6A9E7065C273490a9")
        self.assertEqual(json_data["feeLevel"], "HIGH")
        self.assertEqual(json_data["amount"], "9.98")


if __name__ == "__main__":
    unittest.main()

