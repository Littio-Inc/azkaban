"""Tests for Cassandra API client."""

import unittest
from unittest.mock import MagicMock, patch

from app.common.apis.cassandra.client import CassandraClient
from app.common.apis.cassandra.dtos import (
    BalanceResponse,
    BlockchainWalletCreateRequest,
    BlockchainWalletResponse,
    BlockchainWalletUpdateRequest,
    CollateralSetCTO,
    ExternalWalletCreateRequest,
    ExternalWalletResponse,
    ExternalWalletUpdateRequest,
    PayoutCreateRequest,
    PayoutResponse,
    QuoteResponse,
    RecipientCreateRequest,
    RecipientListResponse,
    RecipientResponse,
    RecipientUpdateRequest,
    VaultAccountCTO,
    VaultAccountResponse,
    VaultListItem,
    VaultOverviewCTO,
    VaultOverviewResponse,
    VaultsListResponse,
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

    @patch(PATCH_AGENT)
    @patch(PATCH_SECRETS)
    def test_get_vault_account_success(self, mock_get_secret, mock_agent_class):
        """Test successful vault account retrieval."""
        mock_get_secret.side_effect = lambda key: API_URL if key == "CASSANDRA_API_URL" else API_KEY
        mock_agent = MagicMock()
        mock_agent_class.return_value = mock_agent
        vault_address = "0xc03B8490636055D453878a7bD74bd116d0051e4B"
        account_address = "0xfd4f11A2aaE86165050688c85eC9ED6210C427A9"
        mock_agent.get.return_value = {
            "vaultAccountCTO": {
                "yieldType": "DeFi",
                "rolloverCollateral": " ",
                "automaticRollover": False,
                "earlyWithdrawalProcessingPeriod": 0,
                "maximumTransferAmount": 0,
                "minimumTransferAmount": 0,
                "contractualCurrency": " ",
                "liquidityFeeRate": 0,
                "platformFeeRate": 0,
                "advisoryFeeRate": 0,
                "transferOutDays": 0,
                "transferInDays": 0,
                "benchmarkRate": " ",
                "collateral": [],
                "collateralSetCTO": {
                    "exchangeRateAutomation": "Manual",
                    "timestamp": 1767044575,
                    "collateral": [],
                    "poolAddr": "0x0000000000000000000000000000000000000000",
                },
                "timestampOffchain": 1767044568,
                "poolAddrOffchain": vault_address,
                "version": "5.0.0",
                "poolType": 2,
                "id": f"{vault_address}-{account_address}",
                "timestamp": 1767044568,
                "timestampDateString": "29-12-2025 UTC",
                "timestampString": "21:42:48 UTC",
                "dayNumber": 20451,
                "timeOfDay": 78168,
                "blockNumber": 9941016,
                "vaultName": "Dynamic Vault 001",
                "currencyLabel": "ERC20",
                "liquidityTokenSymbol": "MUSDC",
                "poolAddr": vault_address,
                "accountAddr": account_address,
                "liquidityAssetAddr": account_address,
                "tokenBalance": "0",
                "assetBalance": "0",
                "principalEarningInterest": "0",
                "maxWithdrawRequest": "0",
                "maxRedeemRequest": "0",
                "requestedSharesOf": "0",
                "requestedAssetsOf": "0",
                "acceptedShares": "0",
                "acceptedAssets": "0",
                "assetsDeposited": "0",
                "assetsWithdrawn": "0",
                "currentAssetValue": "0",
                "gainLoss": "0",
                "gainLossInDay": "0",
                "credits": "0",
                "creditsInDay": "0",
                "debits": "0",
                "debitsInDay": "0",
                "fees": "0",
                "feesInDay": "0",
                "interestRate": "1200",
                "exchangeRate": "1060438524345691461",
                "indicativeInterestRate": "0",
                "collateralRate": "0",
            },
            "vaultAddress": vault_address,
            "accountAddress": account_address,
        }

        client = CassandraClient()
        result = client.get_vault_account(vault_address, account_address)

        self.assertIsInstance(result, VaultAccountResponse)
        self.assertEqual(result.vault_address, vault_address)
        self.assertEqual(result.account_address, account_address)
        mock_agent.get.assert_called_once_with(
            req_path=f"/v1/opentrade/vaultsAccount/{vault_address}/{account_address}"
        )

    @patch(PATCH_AGENT)
    @patch(PATCH_SECRETS)
    def test_get_vaults_list_success(self, mock_get_secret, mock_agent_class):
        """Test successful vaults list retrieval."""
        mock_get_secret.side_effect = lambda key: API_URL if key == "CASSANDRA_API_URL" else API_KEY
        mock_agent = MagicMock()
        mock_agent_class.return_value = mock_agent
        mock_agent.get.return_value = {
            "vaultList": [
                {
                    "displayName": "Dynamic Test Vault 001",
                    "chainId": 11155111,
                    "contractName": "PoolDynamic",
                    "poolType": 2,
                    "chainConfigName": "SandboxSepolia",
                    "creationBlock": 8818602,
                    "creationTimestamp": 1753197612,
                    "symbol": "xFIGSOL",
                    "name": "Dynamic Test Vault 001",
                    "liquidityAssetAddr": "0xfd4f11A2aaE86165050688c85eC9ED6210C427A9",
                    "liquidityTokenSymbol": "MUSDC",
                    "currencyLabel": "ERC20",
                    "poolAddr": "0xD1f0774ccff0CE4F36DeA57b6a28aB7FeB0a01B0",
                },
            ],
        }

        client = CassandraClient()
        result = client.get_vaults_list()

        self.assertIsInstance(result, VaultsListResponse)
        self.assertEqual(len(result.vault_list), 1)
        self.assertEqual(result.vault_list[0].display_name, "Dynamic Test Vault 001")
        mock_agent.get.assert_called_once_with(req_path="/v1/opentrade/vaults")

    @patch(PATCH_AGENT)
    @patch(PATCH_SECRETS)
    def test_get_vault_overview_success(self, mock_get_secret, mock_agent_class):
        """Test successful vault overview retrieval."""
        mock_get_secret.side_effect = lambda key: API_URL if key == "CASSANDRA_API_URL" else API_KEY
        mock_agent = MagicMock()
        mock_agent_class.return_value = mock_agent
        vault_address = "0xD1f0774ccff0CE4F36DeA57b6a28aB7FeB0a01B0"
        mock_agent.get.return_value = {
            "vaultOverviewCTO": {
                "yieldType": "DeFi",
                "rolloverCollateral": " ",
                "automaticRollover": False,
                "earlyWithdrawalProcessingPeriod": 0,
                "maximumTransferAmount": 1000000000,
                "minimumTransferAmount": 100,
                "contractualCurrency": " USD",
                "liquidityFeeRate": 20,
                "platformFeeRate": 25,
                "advisoryFeeRate": 5,
                "transferOutDays": 3,
                "transferInDays": 0,
                "benchmarkRate": " NA",
                "collateral": [],
                "collateralSetCTO": {
                    "exchangeRateAutomation": "Manual",
                    "timestamp": 1767041714,
                    "collateral": [],
                    "poolAddr": "0x0000000000000000000000000000000000000000",
                },
                "timestampOffchain": 1753198329,
                "poolAddrOffchain": vault_address,
                "version": "5.0.0",
                "poolType": 2,
                "poolAddr": vault_address,
                "id": vault_address,
                "chainConfigurationName": "SandboxSepolia",
                "creationBlock": 8818602,
                "creationTimestamp": 1753197612,
                "liquidityTokenSymbol": "MUSDC",
                "currencyLabel": "ERC20",
                "poolAdminAddr": "0x517B2eBBd4fB0Bd0EEc0E9b540ae29E6984314f0",
                "poolControllerAddr": "0xe3aFa8b1cd6334D0DC15303446A2FEcdeb4f0Dd4",
                "exchangeRateType": 3,
                "name": "Dynamic Test Vault 001",
                "symbol": "xFIGSOL",
                "borrowerManagerAddr": "0x27E6A4Bc57f86B0ba15561dc5D822Fb539C2295e",
                "borrowerWalletAddr": "0x27E6A4Bc57f86B0ba15561dc5D822Fb539C2295e",
                "closeOfDepositTime": 64800,
                "closeOfWithdrawTime": 64800,
                "feeCollectorAddress": "0x27E6A4Bc57f86B0ba15561dc5D822Fb539C2295e",
                "liquidityAssetAddr": "0xfd4f11A2aaE86165050688c85eC9ED6210C427A9",
                "blockNumber": 9940865,
                "timestamp": 1767042576,
                "timestampDateString": "29-12-2025 UTC",
                "timestampString": "21:09:36 UTC",
                "timeOfDay": 76176,
                "dayNumber": 20451,
                "chainId": 0,
                "state": 1,
                "totalAssetsDeposited": "11122887621000",
                "totalAssetsWithdrawn": "1201239102",
                "interestRate": "1500",
                "exchangeRate": "1063588340855450534",
                "exchangeRateAtSetDay": "1063588340855450534",
                "exchangeRateSetDay": 20451,
                "exchangeRateChangeRate": "0",
                "exchangeRateCompoundingRate": "1000382982750000000",
                "exchangeRateAtMaturity": "1000000000000000000",
                "exchangeRateMaturityDay": 20291,
                "indicativeInterestRate": "0",
                "collateralRate": "0",
                "totalInterestAccrued": "657609398727",
                "totalShares": "11075051623029",
                "totalAssets": "11779295780625",
                "totalOutstandingLoanPrincipal": "11779295780625",
            },
            "vaultAddress": vault_address,
        }

        client = CassandraClient()
        result = client.get_vault_overview(vault_address)

        self.assertIsInstance(result, VaultOverviewResponse)
        self.assertEqual(result.vault_address, vault_address)
        self.assertEqual(result.vault_overview_cto.name, "Dynamic Test Vault 001")
        mock_agent.get.assert_called_once_with(req_path=f"/v1/opentrade/vaults/{vault_address}")

    @patch(PATCH_AGENT)
    @patch(PATCH_SECRETS)
    def test_get_recipients_list_success(self, mock_get_secret, mock_agent_class):
        """Test successful recipients list retrieval."""
        mock_get_secret.side_effect = lambda key: API_URL if key == "CASSANDRA_API_URL" else API_KEY
        mock_agent = MagicMock()
        mock_agent_class.return_value = mock_agent
        mock_agent.get.return_value = {
            "recipients": [
                {
                    "id": "b7d30b7a-0c66-411d-a0e6-1b3ae385132e",
                    "user_id": "dd329366-a9ff-4f5b-a606-6ce0e15b5a83",
                    "type": "transfer",
                    "first_name": None,
                    "last_name": None,
                    "company_name": "Banco BBVA Colombia S.A",
                    "document_type": "NIT",
                    "document_number": "90156317234",
                    "bank_code": "1013",
                    "account_number": "31231231233",
                    "account_type": "savings",
                    "cobre_counterparty_id": None,
                    "provider": "BBVA",
                    "created_at": "2025-12-31T21:05:11.794956+00:00",
                    "updated_at": "2025-12-31T21:05:11.794956+00:00",
                }
            ]
        }

        client = CassandraClient()
        result = client.get_recipients_list(provider="BBVA")

        self.assertIsInstance(result, list)
        self.assertEqual(len(result), 1)
        self.assertIsInstance(result[0], RecipientListResponse)
        self.assertEqual(result[0].id, "b7d30b7a-0c66-411d-a0e6-1b3ae385132e")
        self.assertEqual(result[0].provider, "BBVA")
        mock_agent.get.assert_called_once_with(
            req_path="/v1/recipients",
            query_params={"provider": "BBVA"},
        )

    @patch(PATCH_AGENT)
    @patch(PATCH_SECRETS)
    def test_get_recipients_list_with_exclude_provider(self, mock_get_secret, mock_agent_class):
        """Test recipients list retrieval with exclude_provider filter."""
        mock_get_secret.side_effect = lambda key: API_URL if key == "CASSANDRA_API_URL" else API_KEY
        mock_agent = MagicMock()
        mock_agent_class.return_value = mock_agent
        mock_agent.get.return_value = {"recipients": []}

        client = CassandraClient()
        result = client.get_recipients_list(exclude_provider="COBRE")

        self.assertIsInstance(result, list)
        self.assertEqual(len(result), 0)
        mock_agent.get.assert_called_once_with(
            req_path="/v1/recipients",
            query_params={"exclude_provider": "COBRE"},
        )

    @patch(PATCH_AGENT)
    @patch(PATCH_SECRETS)
    def test_get_recipients_list_no_filters(self, mock_get_secret, mock_agent_class):
        """Test recipients list retrieval without filters."""
        mock_get_secret.side_effect = lambda key: API_URL if key == "CASSANDRA_API_URL" else API_KEY
        mock_agent = MagicMock()
        mock_agent_class.return_value = mock_agent
        mock_agent.get.return_value = {"recipients": []}

        client = CassandraClient()
        result = client.get_recipients_list()

        self.assertIsInstance(result, list)
        mock_agent.get.assert_called_once_with(
            req_path="/v1/recipients",
            query_params=None,
        )

    @patch(PATCH_AGENT)
    @patch(PATCH_SECRETS)
    def test_get_blockchain_wallets_success(self, mock_get_secret, mock_agent_class):
        """Test successful blockchain wallets retrieval."""
        mock_get_secret.side_effect = lambda key: API_URL if key == "CASSANDRA_API_URL" else API_KEY
        mock_agent = MagicMock()
        mock_agent_class.return_value = mock_agent
        mock_agent.get.return_value = {
            "wallets": [
                {
                    "id": "80cb0fb1-ddce-499a-a84d-927a9c30944a",
                    "name": "Littio-Test",
                    "provider": "OPEN_TRADE",
                    "wallet_id": "0x3390885691531951317BB47afE6F304B19bb6140",
                    "provider_id": "5",
                    "network": "POLYGON",
                    "enabled": True,
                    "category": "Manual retiros",
                    "owner": "LITTIO",
                    "created_at": "2025-12-31T15:22:32.738242+00:00",
                    "updated_at": "2025-12-31T15:22:32.738242+00:00",
                }
            ]
        }

        client = CassandraClient()
        result = client.get_blockchain_wallets(provider="FIREBLOCKS")

        self.assertIsInstance(result, list)
        self.assertEqual(len(result), 1)
        self.assertIsInstance(result[0], BlockchainWalletResponse)
        self.assertEqual(result[0].id, "80cb0fb1-ddce-499a-a84d-927a9c30944a")
        self.assertEqual(result[0].provider, "OPEN_TRADE")
        mock_agent.get.assert_called_once_with(
            req_path="/v1/blockchain-wallets",
            query_params={"provider": "FIREBLOCKS"},
        )

    @patch(PATCH_AGENT)
    @patch(PATCH_SECRETS)
    def test_get_blockchain_wallets_with_exclude_provider(self, mock_get_secret, mock_agent_class):
        """Test blockchain wallets retrieval with exclude_provider filter."""
        mock_get_secret.side_effect = lambda key: API_URL if key == "CASSANDRA_API_URL" else API_KEY
        mock_agent = MagicMock()
        mock_agent_class.return_value = mock_agent
        mock_agent.get.return_value = {"wallets": []}

        client = CassandraClient()
        result = client.get_blockchain_wallets(exclude_provider="COBRE")

        self.assertIsInstance(result, list)
        self.assertEqual(len(result), 0)
        mock_agent.get.assert_called_once_with(
            req_path="/v1/blockchain-wallets",
            query_params={"exclude_provider": "COBRE"},
        )

    @patch(PATCH_AGENT)
    @patch(PATCH_SECRETS)
    def test_get_blockchain_wallets_no_filters(self, mock_get_secret, mock_agent_class):
        """Test blockchain wallets retrieval without filters."""
        mock_get_secret.side_effect = lambda key: API_URL if key == "CASSANDRA_API_URL" else API_KEY
        mock_agent = MagicMock()
        mock_agent_class.return_value = mock_agent
        mock_agent.get.return_value = {"wallets": []}

        client = CassandraClient()
        result = client.get_blockchain_wallets()

        self.assertIsInstance(result, list)
        mock_agent.get.assert_called_once_with(
            req_path="/v1/blockchain-wallets",
            query_params=None,
        )

    @patch(PATCH_AGENT)
    @patch(PATCH_SECRETS)
    def test_create_recipient_success(self, mock_get_secret, mock_agent_class):
        """Test successful recipient creation."""
        mock_get_secret.side_effect = lambda key: API_URL if key == "CASSANDRA_API_URL" else API_KEY
        mock_agent = MagicMock()
        mock_agent_class.return_value = mock_agent
        mock_agent.post.return_value = {
            "id": "recipient-id-123",
            "user_id": USER_ID_TEST,
            "type": "transfer",
            "first_name": "John",
            "last_name": "Doe",
            "provider": "cobre",
            "enabled": True,
            "created_at": TEST_TIMESTAMP,
            "updated_at": TEST_TIMESTAMP,
        }

        client = CassandraClient()
        recipient_data = RecipientCreateRequest(
            user_id=USER_ID_TEST,
            type="transfer",
            first_name="John",
            last_name="Doe",
            document_type="CC",
            document_number="1234567890",
            bank_code="001",
            account_number="123456789",
            account_type="checking",
            provider="cobre",
            enabled=True,
        )
        result = client.create_recipient(recipient_data)

        self.assertIsInstance(result, RecipientListResponse)
        self.assertEqual(result.id, "recipient-id-123")
        mock_agent.post.assert_called_once()

    @patch(PATCH_AGENT)
    @patch(PATCH_SECRETS)
    def test_update_recipient_success(self, mock_get_secret, mock_agent_class):
        """Test successful recipient update."""
        mock_get_secret.side_effect = lambda key: API_URL if key == "CASSANDRA_API_URL" else API_KEY
        mock_agent = MagicMock()
        mock_agent_class.return_value = mock_agent
        mock_agent.put.return_value = {
            "id": "recipient-id-123",
            "user_id": USER_ID_TEST,
            "type": "transfer",
            "first_name": "Jane",
            "last_name": "Smith",
            "provider": "cobre",
            "enabled": True,
            "created_at": TEST_TIMESTAMP,
            "updated_at": TEST_TIMESTAMP,
        }

        client = CassandraClient()
        recipient_data = RecipientUpdateRequest(first_name="Jane", last_name="Smith")
        result = client.update_recipient("recipient-id-123", recipient_data)

        self.assertIsInstance(result, RecipientListResponse)
        self.assertEqual(result.first_name, "Jane")
        mock_agent.put.assert_called_once()

    @patch(PATCH_AGENT)
    @patch(PATCH_SECRETS)
    def test_delete_recipient_success(self, mock_get_secret, mock_agent_class):
        """Test successful recipient deletion."""
        mock_get_secret.side_effect = lambda key: API_URL if key == "CASSANDRA_API_URL" else API_KEY
        mock_agent = MagicMock()
        mock_agent_class.return_value = mock_agent
        mock_response = MagicMock()
        mock_response.status_code = 204
        mock_agent.delete.return_value = None

        client = CassandraClient()
        client.delete_recipient("recipient-id-123")

        mock_agent.delete.assert_called_once_with(req_path="/v1/recipients/recipient-id-123")

    @patch(PATCH_AGENT)
    @patch(PATCH_SECRETS)
    def test_create_blockchain_wallet_success(self, mock_get_secret, mock_agent_class):
        """Test successful blockchain wallet creation."""
        mock_get_secret.side_effect = lambda key: API_URL if key == "CASSANDRA_API_URL" else API_KEY
        mock_agent = MagicMock()
        mock_agent_class.return_value = mock_agent
        mock_agent.post.return_value = {
            "id": "wallet-id-123",
            "name": "Test Wallet",
            "provider": "cobre",
            "wallet_id": "wallet_12345",
            "provider_id": "provider_67890",
            "network": "ethereum",
            "enabled": True,
            "category": "exchange",
            "owner": "team-backend",
            "created_at": TEST_TIMESTAMP,
            "updated_at": TEST_TIMESTAMP,
        }

        client = CassandraClient()
        wallet_data = BlockchainWalletCreateRequest(
            name="Test Wallet",
            provider="cobre",
            wallet_id="wallet_12345",
            provider_id="provider_67890",
            network="ethereum",
            enabled=True,
            category="exchange",
            owner="team-backend",
        )
        result = client.create_blockchain_wallet(wallet_data)

        self.assertIsInstance(result, BlockchainWalletResponse)
        self.assertEqual(result.id, "wallet-id-123")
        mock_agent.post.assert_called_once()

    @patch(PATCH_AGENT)
    @patch(PATCH_SECRETS)
    def test_update_blockchain_wallet_success(self, mock_get_secret, mock_agent_class):
        """Test successful blockchain wallet update."""
        mock_get_secret.side_effect = lambda key: API_URL if key == "CASSANDRA_API_URL" else API_KEY
        mock_agent = MagicMock()
        mock_agent_class.return_value = mock_agent
        mock_agent.put.return_value = {
            "id": "wallet-id-123",
            "name": "Updated Wallet",
            "provider": "cobre",
            "wallet_id": "wallet_12345",
            "provider_id": "provider_67890",
            "network": "ethereum",
            "enabled": False,
            "category": "trading",
            "owner": "team-backend",
            "created_at": TEST_TIMESTAMP,
            "updated_at": TEST_TIMESTAMP,
        }

        client = CassandraClient()
        wallet_data = BlockchainWalletUpdateRequest(name="Updated Wallet", enabled=False, category="trading")
        result = client.update_blockchain_wallet("wallet-id-123", wallet_data)

        self.assertIsInstance(result, BlockchainWalletResponse)
        self.assertEqual(result.name, "Updated Wallet")
        mock_agent.put.assert_called_once()

    @patch(PATCH_AGENT)
    @patch(PATCH_SECRETS)
    def test_delete_blockchain_wallet_success(self, mock_get_secret, mock_agent_class):
        """Test successful blockchain wallet deletion."""
        mock_get_secret.side_effect = lambda key: API_URL if key == "CASSANDRA_API_URL" else API_KEY
        mock_agent = MagicMock()
        mock_agent_class.return_value = mock_agent
        mock_agent.delete.return_value = None

        client = CassandraClient()
        client.delete_blockchain_wallet("wallet-id-123")

        mock_agent.delete.assert_called_once_with(req_path="/v1/blockchain-wallets/wallet-id-123")

    @patch(PATCH_AGENT)
    @patch(PATCH_SECRETS)
    def test_get_external_wallets_success(self, mock_get_secret, mock_agent_class):
        """Test successful external wallets retrieval."""
        mock_get_secret.side_effect = lambda key: API_URL if key == "CASSANDRA_API_URL" else API_KEY
        mock_agent = MagicMock()
        mock_agent_class.return_value = mock_agent
        mock_agent.get.return_value = {
            "wallets": [
                {
                    "id": "2f4d0fad-185a-49b5-88d9-bf8c1c45c626",
                    "external_wallet_id": "123e4567-e89b-12d3-a456-426614174000",
                    "name": "Vault Wallet Principal 2",
                    "category": "VAULT",
                    "supplier_prefunding": True,
                    "b2c_funding": True,
                    "enabled": True,
                    "created_at": "2026-01-14T16:53:32.251713+00:00",
                    "updated_at": "2026-01-14T16:54:21.397067+00:00",
                }
            ]
        }

        client = CassandraClient()
        result = client.get_external_wallets()

        self.assertIsInstance(result, list)
        self.assertEqual(len(result), 1)
        self.assertIsInstance(result[0], ExternalWalletResponse)
        self.assertEqual(result[0].id, "2f4d0fad-185a-49b5-88d9-bf8c1c45c626")
        self.assertEqual(result[0].category, "VAULT")
        mock_agent.get.assert_called_once_with(req_path="/v1/external-wallets")

    @patch(PATCH_AGENT)
    @patch(PATCH_SECRETS)
    def test_get_external_wallets_list_format(self, mock_get_secret, mock_agent_class):
        """Test external wallets retrieval with direct list format."""
        mock_get_secret.side_effect = lambda key: API_URL if key == "CASSANDRA_API_URL" else API_KEY
        mock_agent = MagicMock()
        mock_agent_class.return_value = mock_agent
        mock_agent.get.return_value = [
            {
                "id": "2f4d0fad-185a-49b5-88d9-bf8c1c45c626",
                "external_wallet_id": "123e4567-e89b-12d3-a456-426614174000",
                "name": "Vault Wallet Principal 2",
                "category": "VAULT",
                "supplier_prefunding": True,
                "b2c_funding": True,
                "enabled": True,
                "created_at": "2026-01-14T16:53:32.251713+00:00",
                "updated_at": "2026-01-14T16:54:21.397067+00:00",
            }
        ]

        client = CassandraClient()
        result = client.get_external_wallets()

        self.assertIsInstance(result, list)
        self.assertEqual(len(result), 1)
        self.assertIsInstance(result[0], ExternalWalletResponse)

    @patch(PATCH_AGENT)
    @patch(PATCH_SECRETS)
    def test_create_external_wallet_success(self, mock_get_secret, mock_agent_class):
        """Test successful external wallet creation."""
        mock_get_secret.side_effect = lambda key: API_URL if key == "CASSANDRA_API_URL" else API_KEY
        mock_agent = MagicMock()
        mock_agent_class.return_value = mock_agent
        mock_agent.post.return_value = {
            "id": "2f4d0fad-185a-49b5-88d9-bf8c1c45c626",
            "external_wallet_id": "123e4567-e89b-12d3-a456-426614174001",
            "name": "Vault Wallet Principal",
            "category": "OTC",
            "supplier_prefunding": True,
            "b2c_funding": False,
            "enabled": True,
            "created_at": "2026-01-14T17:10:01.841814+00:00",
            "updated_at": "2026-01-14T17:10:01.841814+00:00",
        }

        client = CassandraClient()
        wallet_data = ExternalWalletCreateRequest(
            external_wallet_id="123e4567-e89b-12d3-a456-426614174001",
            name="Vault Wallet Principal",
            category="OTC",
            supplier_prefunding=True,
            b2c_funding=False,
            enabled=True,
        )
        result = client.create_external_wallet(wallet_data)

        self.assertIsInstance(result, ExternalWalletResponse)
        self.assertEqual(result.id, "2f4d0fad-185a-49b5-88d9-bf8c1c45c626")
        self.assertEqual(result.category, "OTC")
        mock_agent.post.assert_called_once()

    @patch(PATCH_AGENT)
    @patch(PATCH_SECRETS)
    def test_update_external_wallet_success(self, mock_get_secret, mock_agent_class):
        """Test successful external wallet update."""
        mock_get_secret.side_effect = lambda key: API_URL if key == "CASSANDRA_API_URL" else API_KEY
        mock_agent = MagicMock()
        mock_agent_class.return_value = mock_agent
        mock_agent.put.return_value = {
            "id": "2f4d0fad-185a-49b5-88d9-bf8c1c45c626",
            "external_wallet_id": "123e4567-e89b-12d3-a456-426614174000",
            "name": "Vault Wallet Principal 2",
            "category": "VAULT",
            "supplier_prefunding": True,
            "b2c_funding": True,
            "enabled": True,
            "created_at": "2026-01-14T16:53:32.251713+00:00",
            "updated_at": "2026-01-14T16:54:21.397067+00:00",
        }

        client = CassandraClient()
        wallet_data = ExternalWalletUpdateRequest(
            name="Vault Wallet Principal 2",
            category="VAULT",
            supplier_prefunding=True,
            b2c_funding=True,
            enabled=True,
        )
        result = client.update_external_wallet("2f4d0fad-185a-49b5-88d9-bf8c1c45c626", wallet_data)

        self.assertIsInstance(result, ExternalWalletResponse)
        self.assertEqual(result.name, "Vault Wallet Principal 2")
        self.assertEqual(result.category, "VAULT")
        mock_agent.put.assert_called_once()

    @patch(PATCH_AGENT)
    @patch(PATCH_SECRETS)
    def test_delete_external_wallet_success(self, mock_get_secret, mock_agent_class):
        """Test successful external wallet deletion."""
        mock_get_secret.side_effect = lambda key: API_URL if key == "CASSANDRA_API_URL" else API_KEY
        mock_agent = MagicMock()
        mock_agent_class.return_value = mock_agent
        mock_agent.delete.return_value = None

        client = CassandraClient()
        client.delete_external_wallet("2f4d0fad-185a-49b5-88d9-bf8c1c45c626")

        mock_agent.delete.assert_called_once_with(req_path="/v1/external-wallets/2f4d0fad-185a-49b5-88d9-bf8c1c45c626")

    @patch(PATCH_AGENT)
    @patch(PATCH_SECRETS)
    def test_get_external_wallets_single_object(self, mock_get_secret, mock_agent_class):
        """Test external wallets retrieval with single object format."""
        mock_get_secret.side_effect = lambda key: API_URL if key == "CASSANDRA_API_URL" else API_KEY
        mock_agent = MagicMock()
        mock_agent_class.return_value = mock_agent
        mock_agent.get.return_value = {
            "id": "2f4d0fad-185a-49b5-88d9-bf8c1c45c626",
            "external_wallet_id": "123e4567-e89b-12d3-a456-426614174000",
            "name": "Vault Wallet Principal 2",
            "category": "VAULT",
            "supplier_prefunding": True,
            "b2c_funding": True,
            "enabled": True,
            "created_at": "2026-01-14T16:53:32.251713+00:00",
            "updated_at": "2026-01-14T16:54:21.397067+00:00",
        }

        client = CassandraClient()
        result = client.get_external_wallets()

        self.assertIsInstance(result, list)
        self.assertEqual(len(result), 1)
        self.assertIsInstance(result[0], ExternalWalletResponse)
