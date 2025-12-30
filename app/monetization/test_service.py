"""Tests for monetization service."""

import unittest
from unittest.mock import MagicMock, patch

from tests.fixtures import (
    create_test_quote_response,
    QUOTE_ID_TEST,
    TEST_TIMESTAMP,
    TEST_TIMESTAMP_UTC,
)

from app.common.apis.cassandra.dtos import (
    BalanceResponse,
    CollateralSetCTO,
    PayoutCreateRequest,
    PayoutResponse,
    QuoteResponse,
    RecipientResponse,
    TokenBalance,
    VaultAccountCTO,
    VaultAccountResponse,
    VaultListItem,
    VaultOverviewCTO,
    VaultOverviewResponse,
    VaultsListResponse,
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
PROVIDER_KIRA = "kira"
API_ERROR_MSG = "API error"
UNEXPECTED_ERROR_MSG = "Unexpected error"
PATCH_PATH = "app.monetization.service.CassandraClient"
VAULT_ADDRESS_TEST = "0xc03B8490636055D453878a7bD74bd116d0051e4B"
ACCOUNT_ADDRESS_TEST = "0xfd4f11A2aaE86165050688c85eC9ED6210C427A9"
VAULT_ADDRESS_TEST_SECOND = "0xD1f0774ccff0CE4F36DeA57b6a28aB7FeB0a01B0"
VAULT_NAME_TEST = "Dynamic Test Vault 001"
ZERO_ADDRESS = "0x0000000000000000000000000000000000000000"
ZERO_VALUE = 0


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
            expiration_ts=TEST_TIMESTAMP,
            expiration_ts_utc=TEST_TIMESTAMP_UTC,
        )
        mock_client.get_quote.return_value = expected_quote

        result = MonetizationService.get_quote(ACCOUNT_TRANSFER, 100.0, CURRENCY_USD, CURRENCY_COP, PROVIDER_KIRA)

        self.assertEqual(result.quote_id, expected_quote.quote_id)
        self.assertEqual(result.quote_amount, expected_quote.quote_amount)
        mock_client.get_quote.assert_called_once_with(
            ACCOUNT_TRANSFER, 100.0, CURRENCY_USD, CURRENCY_COP, PROVIDER_KIRA
        )

    @patch(PATCH_PATH)
    def test_get_quote_api_error(self, mock_client_class):
        """Test quote retrieval with API error."""
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client
        mock_client.get_quote.side_effect = CassandraAPIClientError(API_ERROR_MSG)

        with self.assertRaises(CassandraAPIClientError):
            MonetizationService.get_quote(ACCOUNT_TRANSFER, 100.0, CURRENCY_USD, CURRENCY_COP, PROVIDER_KIRA)

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

        result = MonetizationService.get_recipients(ACCOUNT_TRANSFER, USER_ID_TEST, PROVIDER_KIRA)

        self.assertEqual(len(result), 2)
        self.assertEqual(result[0].recipient_id, "1")
        mock_client.get_recipients.assert_called_once_with(ACCOUNT_TRANSFER, USER_ID_TEST, PROVIDER_KIRA)

    @patch(PATCH_PATH)
    def test_get_recipients_api_error(self, mock_client_class):
        """Test recipients retrieval with API error."""
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client
        mock_client.get_recipients.side_effect = CassandraAPIClientError(API_ERROR_MSG)

        with self.assertRaises(CassandraAPIClientError):
            MonetizationService.get_recipients(ACCOUNT_TRANSFER, USER_ID_TEST, PROVIDER_KIRA)

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
        mock_client.get_balance.assert_called_once_with(ACCOUNT_TRANSFER, WALLET_ID_TEST, PROVIDER_KIRA)

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
            quote=create_test_quote_response(),
            token=TOKEN_USDC,
            provider=PROVIDER_KIRA,
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
            created_at=TEST_TIMESTAMP,
            updated_at=TEST_TIMESTAMP,
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
            quote=create_test_quote_response(),
            token=TOKEN_USDC,
            provider=PROVIDER_KIRA,
        )
        mock_client.create_payout.side_effect = CassandraAPIClientError(API_ERROR_MSG)

        with self.assertRaises(CassandraAPIClientError):
            MonetizationService.create_payout(ACCOUNT_TRANSFER, payout_data)

    @patch(PATCH_PATH)
    def test_get_quote_missing_credentials(self, mock_client_class):
        """Test quote retrieval with missing credentials."""
        mock_client_class.side_effect = MissingCredentialsError("Missing credentials")

        with self.assertRaises(MissingCredentialsError):
            MonetizationService.get_quote(ACCOUNT_TRANSFER, 100.0, CURRENCY_USD, CURRENCY_COP, PROVIDER_KIRA)

    @patch(PATCH_PATH)
    def test_get_quote_unexpected_error(self, mock_client_class):
        """Test quote retrieval with unexpected error."""
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client
        mock_client.get_quote.side_effect = ValueError(UNEXPECTED_ERROR_MSG)

        with self.assertRaises(ValueError):
            MonetizationService.get_quote(ACCOUNT_TRANSFER, 100.0, CURRENCY_USD, CURRENCY_COP, PROVIDER_KIRA)

    @patch(PATCH_PATH)
    def test_get_recipients_unexpected_error(self, mock_client_class):
        """Test recipients retrieval with unexpected error."""
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client
        mock_client.get_recipients.side_effect = ValueError(UNEXPECTED_ERROR_MSG)

        with self.assertRaises(ValueError):
            MonetizationService.get_recipients(ACCOUNT_TRANSFER, USER_ID_TEST, PROVIDER_KIRA)

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
            quote=create_test_quote_response(),
            token=TOKEN_USDC,
            provider=PROVIDER_KIRA,
        )
        mock_client.create_payout.side_effect = ValueError(UNEXPECTED_ERROR_MSG)

        with self.assertRaises(ValueError):
            MonetizationService.create_payout(ACCOUNT_TRANSFER, payout_data)

    @patch(PATCH_PATH)
    def test_get_vault_account_success(self, mock_client_class):
        """Test successful vault account retrieval."""
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client
        vault_address = VAULT_ADDRESS_TEST
        account_address = ACCOUNT_ADDRESS_TEST
        expected_response = VaultAccountResponse(
            vaultAccountCTO=VaultAccountCTO(
                yieldType="DeFi",
                rolloverCollateral=" ",
                automaticRollover=False,
                earlyWithdrawalProcessingPeriod=0,
                maximumTransferAmount=0,
                minimumTransferAmount=0,
                contractualCurrency=" ",
                liquidityFeeRate=0,
                platformFeeRate=0,
                advisoryFeeRate=0,
                transferOutDays=0,
                transferInDays=0,
                benchmarkRate=" ",
                collateral=[],
                collateralSetCTO=CollateralSetCTO(
                    exchangeRateAutomation="Manual",
                    timestamp=1767044575,
                    collateral=[],
                    poolAddr=ZERO_ADDRESS,
                ),
                timestampOffchain=1767044568,
                poolAddrOffchain=vault_address,
                version="5.0.0",
                poolType=2,
                id=f"{vault_address}-{account_address}",
                timestamp=1767044568,
                timestampDateString="29-12-2025 UTC",
                timestampString="21:42:48 UTC",
                dayNumber=20451,
                timeOfDay=78168,
                blockNumber=9941016,
                vaultName="Dynamic Vault 001",
                currencyLabel="ERC20",
                liquidityTokenSymbol="MUSDC",
                poolAddr=vault_address,
                accountAddr=account_address,
                liquidityAssetAddr=account_address,
                tokenBalance="0",
                assetBalance="0",
                principalEarningInterest="0",
                maxWithdrawRequest="0",
                maxRedeemRequest="0",
                requestedSharesOf="0",
                requestedAssetsOf="0",
                acceptedShares="0",
                acceptedAssets="0",
                assetsDeposited="0",
                assetsWithdrawn="0",
                currentAssetValue="0",
                gainLoss="0",
                gainLossInDay="0",
                credits="0",
                creditsInDay="0",
                debits="0",
                debitsInDay="0",
                fees="0",
                feesInDay="0",
                interestRate="1200",
                exchangeRate="1060438524345691461",
                indicativeInterestRate="0",
                collateralRate="0",
            ),
            vaultAddress=vault_address,
            accountAddress=account_address,
        )
        mock_client.get_vault_account.return_value = expected_response

        result = MonetizationService.get_vault_account(vault_address, account_address)

        self.assertEqual(result.vault_address, vault_address)
        self.assertEqual(result.account_address, account_address)
        mock_client.get_vault_account.assert_called_once_with(vault_address, account_address)

    @patch(PATCH_PATH)
    def test_get_vault_account_api_error(self, mock_client_class):
        """Test vault account retrieval with API error."""
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client
        vault_address = "0xc03B8490636055D453878a7bD74bd116d0051e4B"
        account_address = ACCOUNT_ADDRESS_TEST
        mock_client.get_vault_account.side_effect = CassandraAPIClientError(API_ERROR_MSG)

        with self.assertRaises(CassandraAPIClientError):
            MonetizationService.get_vault_account(vault_address, account_address)

    @patch(PATCH_PATH)
    def test_get_vault_account_unexpected_error(self, mock_client_class):
        """Test vault account retrieval with unexpected error."""
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client
        vault_address = "0xc03B8490636055D453878a7bD74bd116d0051e4B"
        account_address = ACCOUNT_ADDRESS_TEST
        mock_client.get_vault_account.side_effect = ValueError(UNEXPECTED_ERROR_MSG)

        with self.assertRaises(ValueError):
            MonetizationService.get_vault_account(vault_address, account_address)

    @patch(PATCH_PATH)
    def test_get_vaults_list_success(self, mock_client_class):
        """Test successful vaults list retrieval."""
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client
        expected_response = VaultsListResponse(
            vaultList=[
                VaultListItem(
                    displayName=VAULT_NAME_TEST,
                    chainId=11155111,
                    contractName="PoolDynamic",
                    poolType=2,
                    chainConfigName="SandboxSepolia",
                    creationBlock=8818602,
                    creationTimestamp=1753197612,
                    symbol="xFIGSOL",
                    name=VAULT_NAME_TEST,
                    liquidityAssetAddr=ACCOUNT_ADDRESS_TEST,
                    liquidityTokenSymbol="MUSDC",
                    currencyLabel="ERC20",
                    poolAddr=VAULT_ADDRESS_TEST_SECOND,
                ),
            ],
        )
        mock_client.get_vaults_list.return_value = expected_response

        result = MonetizationService.get_vaults_list()

        self.assertEqual(len(result.vault_list), 1)
        self.assertEqual(result.vault_list[0].display_name, VAULT_NAME_TEST)
        mock_client.get_vaults_list.assert_called_once()

    @patch(PATCH_PATH)
    def test_get_vaults_list_api_error(self, mock_client_class):
        """Test vaults list retrieval with API error."""
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client
        mock_client.get_vaults_list.side_effect = CassandraAPIClientError(API_ERROR_MSG)

        with self.assertRaises(CassandraAPIClientError):
            MonetizationService.get_vaults_list()

    @patch(PATCH_PATH)
    def test_get_vaults_list_unexpected_error(self, mock_client_class):
        """Test vaults list retrieval with unexpected error."""
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client
        mock_client.get_vaults_list.side_effect = ValueError(UNEXPECTED_ERROR_MSG)

        with self.assertRaises(ValueError):
            MonetizationService.get_vaults_list()

    @patch(PATCH_PATH)
    def test_get_vault_overview_success(self, mock_client_class):
        """Test successful vault overview retrieval."""
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client
        vault_address = VAULT_ADDRESS_TEST_SECOND
        expected_response = VaultOverviewResponse(
            vaultOverviewCTO=VaultOverviewCTO(
                yieldType="DeFi",
                rolloverCollateral=" ",
                automaticRollover=False,
                earlyWithdrawalProcessingPeriod=0,
                maximumTransferAmount=1000000000,
                minimumTransferAmount=100,
                contractualCurrency=" USD",
                liquidityFeeRate=20,
                platformFeeRate=25,
                advisoryFeeRate=5,
                transferOutDays=3,
                transferInDays=0,
                benchmarkRate=" NA",
                collateral=[],
                collateralSetCTO=CollateralSetCTO(
                    exchangeRateAutomation="Manual",
                    timestamp=1767041714,
                    collateral=[],
                    poolAddr=ZERO_ADDRESS,
                ),
                timestampOffchain=1753198329,
                poolAddrOffchain=vault_address,
                version="5.0.0",
                poolType=2,
                poolAddr=vault_address,
                id=vault_address,
                chainConfigurationName="SandboxSepolia",
                creationBlock=8818602,
                creationTimestamp=1753197612,
                liquidityTokenSymbol="MUSDC",
                currencyLabel="ERC20",
                poolAdminAddr="0x517B2eBBd4fB0Bd0EEc0E9b540ae29E6984314f0",
                poolControllerAddr="0xe3aFa8b1cd6334D0DC15303446A2FEcdeb4f0Dd4",
                exchangeRateType=3,
                name=VAULT_NAME_TEST,
                symbol="xFIGSOL",
                borrowerManagerAddr="0x27E6A4Bc57f86B0ba15561dc5D822Fb539C2295e",
                borrowerWalletAddr="0x27E6A4Bc57f86B0ba15561dc5D822Fb539C2295e",
                closeOfDepositTime=64800,
                closeOfWithdrawTime=64800,
                feeCollectorAddress="0x27E6A4Bc57f86B0ba15561dc5D822Fb539C2295e",
                liquidityAssetAddr="0xfd4f11A2aaE86165050688c85eC9ED6210C427A9",
                blockNumber=9940865,
                timestamp=1767042576,
                timestampDateString="29-12-2025 UTC",
                timestampString="21:09:36 UTC",
                timeOfDay=76176,
                dayNumber=20451,
                chainId=0,
                state=1,
                totalAssetsDeposited="11122887621000",
                totalAssetsWithdrawn="1201239102",
                interestRate="1500",
                exchangeRate="1063588340855450534",
                exchangeRateAtSetDay="1063588340855450534",
                exchangeRateSetDay=20451,
                exchangeRateChangeRate="0",
                exchangeRateCompoundingRate="1000382982750000000",
                exchangeRateAtMaturity="1000000000000000000",
                exchangeRateMaturityDay=20291,
                indicativeInterestRate="0",
                collateralRate="0",
                totalInterestAccrued="657609398727",
                totalShares="11075051623029",
                totalAssets="11779295780625",
                totalOutstandingLoanPrincipal="11779295780625",
            ),
            vaultAddress=vault_address,
        )
        mock_client.get_vault_overview.return_value = expected_response

        result = MonetizationService.get_vault_overview(vault_address)

        self.assertEqual(result.vault_address, vault_address)
        self.assertEqual(result.vault_overview_cto.name, VAULT_NAME_TEST)
        mock_client.get_vault_overview.assert_called_once_with(vault_address)

    @patch(PATCH_PATH)
    def test_get_vault_overview_api_error(self, mock_client_class):
        """Test vault overview retrieval with API error."""
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client
        vault_address = VAULT_ADDRESS_TEST_SECOND
        mock_client.get_vault_overview.side_effect = CassandraAPIClientError(API_ERROR_MSG)

        with self.assertRaises(CassandraAPIClientError):
            MonetizationService.get_vault_overview(vault_address)

    @patch(PATCH_PATH)
    def test_get_vault_overview_unexpected_error(self, mock_client_class):
        """Test vault overview retrieval with unexpected error."""
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client
        vault_address = VAULT_ADDRESS_TEST_SECOND
        mock_client.get_vault_overview.side_effect = ValueError(UNEXPECTED_ERROR_MSG)

        with self.assertRaises(ValueError):
            MonetizationService.get_vault_overview(vault_address)
