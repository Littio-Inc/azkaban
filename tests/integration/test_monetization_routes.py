"""Integration tests for monetization routes."""

import unittest
from datetime import datetime, timezone
from unittest.mock import patch

from fastapi import FastAPI
from fastapi.testclient import TestClient
from faker import Faker

from app.common.apis.cassandra.dtos import (
    BalanceResponse,
    BlockchainWalletCreateRequest,
    BlockchainWalletResponse,
    BlockchainWalletUpdateRequest,
    PayoutCreateRequest,
    PayoutHistoryResponse,
    PayoutResponse,
    QuoteResponse,
    RecipientCreateRequest,
    RecipientListResponse,
    RecipientUpdateRequest,
    TokenBalance,
    VaultAccountResponse,
    VaultOverviewResponse,
    VaultsListResponse,
)
from app.common.apis.cassandra.errors import CassandraAPIClientError
from app.common.errors import MissingCredentialsError
from app.middleware.auth import get_current_user
from app.middleware.mfa import require_mfa_verification
from app.routes.monetization_routes import router
from tests.fixtures import create_test_quote_response

fake = Faker()

# Test constants for payout tests
ACCOUNT_TRANSFER = "transfer"
ACCOUNT_PAY = "pay"
CURRENCY_USD = "USD"
CURRENCY_COP = "COP"
TOKEN_USDC = "USDC"
PROVIDER_KIRA = "kira"


class TestMonetizationRoutes(unittest.TestCase):
    """Test cases for monetization routes."""

    def setUp(self):
        """Set up test fixtures."""
        self.app = FastAPI()
        self.app.include_router(router, prefix="/v1")
        self.client = TestClient(self.app)
        self.mock_current_user = {
            "firebase_uid": "user-uid-123",
            "email": "user@littio.co",
            "name": "Test User",
            "picture": None,
        }

    def tearDown(self):
        """Clean up after each test."""
        self.app.dependency_overrides.clear()

    def _mock_require_mfa_verification(self):
        """Helper to mock require_mfa_verification dependency."""
        self.app.dependency_overrides[require_mfa_verification] = lambda: self.mock_current_user

    def _create_test_payout_request(self, **kwargs):
        """Helper to create test payout request."""
        quote_id = fake.uuid4()
        defaults = {
            "recipient_id": fake.uuid4(),
            "wallet_id": fake.uuid4(),
            "base_currency": CURRENCY_USD,
            "quote_currency": CURRENCY_COP,
            "amount": float(fake.pydecimal(left_digits=3, right_digits=2, positive=True)),
            "quote_id": quote_id,
            "quote": create_test_quote_response(quote_id=quote_id).model_dump(mode="json"),
            "token": TOKEN_USDC,
            "provider": PROVIDER_KIRA,
            "exchange_only": False,
        }
        defaults.update(kwargs)
        return defaults

    @patch("app.routes.monetization_routes.MonetizationService")
    def test_get_quote_success(self, mock_service_class):
        """Test getting quote successfully."""
        self.app.dependency_overrides[get_current_user] = lambda: self.mock_current_user

        mock_quote = QuoteResponse(
            quote_id="quote-123",
            base_currency="USD",
            quote_currency="COP",
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
        mock_service_class.get_quote.return_value = mock_quote

        response = self.client.get(
            "/v1/payouts/account/transfer/quote?amount=100&base_currency=USD&quote_currency=COP&provider=kira"
        )

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["quote_id"], "quote-123")
        mock_service_class.get_quote.assert_called_once()

    @patch("app.routes.monetization_routes.MonetizationService")
    def test_get_quote_invalid_provider(self, mock_service_class):
        """Test getting quote with invalid provider."""
        self.app.dependency_overrides[get_current_user] = lambda: self.mock_current_user

        response = self.client.get(
            "/v1/payouts/account/transfer/quote?amount=100&base_currency=USD&quote_currency=COP&provider=invalid"
        )

        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertIn("Invalid provider", data["detail"])

    @patch("app.routes.monetization_routes.MonetizationService")
    def test_get_recipients_success(self, mock_service_class):
        """Test getting recipients successfully."""
        self.app.dependency_overrides[get_current_user] = lambda: self.mock_current_user

        from app.common.apis.cassandra.dtos import RecipientResponse
        mock_recipients = [
            RecipientResponse(
                recipient_id="rec-1",
                first_name="John",
                last_name="Doe",
                account_type="PSE",
            )
        ]
        mock_service_class.get_recipients.return_value = mock_recipients

        response = self.client.get(
            "/v1/payouts/account/transfer/recipient?provider=kira&user_id=user-123"
        )

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("recipients", data)
        self.assertEqual(len(data["recipients"]), 1)

    @patch("app.routes.monetization_routes.MonetizationService")
    def test_get_balance_success(self, mock_service_class):
        """Test getting balance successfully."""
        self.app.dependency_overrides[get_current_user] = lambda: self.mock_current_user

        mock_balance = BalanceResponse(
            wallet_id="wallet-123",
            network="polygon",
            balances=[
                TokenBalance(token="USDC", amount="1000.0", decimals=6),
            ],
        )
        mock_service_class.get_balance.return_value = mock_balance

        response = self.client.get(
            "/v1/payouts/account/transfer/wallets/wallet-123/balances?provider=kira"
        )

        self.assertEqual(response.status_code, 200)
        data = response.json()
        # BalanceResponse uses alias walletId, model_dump() should preserve it with populate_by_name=True
        self.assertEqual(data.get("walletId") or data.get("wallet_id"), "wallet-123")

    @patch("app.routes.monetization_routes.MonetizationService")
    def test_get_payout_history_success(self, mock_service_class):
        """Test getting payout history successfully."""
        self.app.dependency_overrides[get_current_user] = lambda: self.mock_current_user

        from app.common.apis.cassandra.dtos import PayoutHistoryItem
        mock_history = PayoutHistoryResponse(
            status="success",
            message="OK",
            data=[
                PayoutHistoryItem(
                    id="payout-1",
                    created_at="2024-01-01T00:00:00",
                    updated_at="2024-01-01T00:00:00",
                    initial_currency="USD",
                    final_currency="COP",
                    initial_amount="100.0",
                    final_amount="1000.0",
                    rate="10.0",
                    status="completed",
                    user_id="user-123",
                    provider=1,
                )
            ],
            count=1,
        )
        mock_service_class.get_payout_history.return_value = mock_history

        response = self.client.get("/v1/payouts/account/transfer/payout")

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "success")

    @patch("app.routes.monetization_routes.MonetizationService")
    def test_get_vault_account_success(self, mock_service_class):
        """Test getting vault account successfully."""
        self.app.dependency_overrides[get_current_user] = lambda: self.mock_current_user

        from app.common.apis.cassandra.dtos import VaultAccountCTO, CollateralSetCTO
        mock_vault = VaultAccountResponse(
            vault_account_cto=VaultAccountCTO(
                yield_type="DeFi",
                rollover_collateral=" ",
                automatic_rollover=False,
                early_withdrawal_processing_period=0,
                maximum_transfer_amount=0,
                minimum_transfer_amount=0,
                contractual_currency=" ",
                liquidity_fee_rate=0,
                platform_fee_rate=0,
                advisory_fee_rate=0,
                transfer_out_days=0,
                transfer_in_days=0,
                benchmark_rate=" ",
                collateral=[],
                collateral_set_cto=CollateralSetCTO(
                    exchange_rate_automation="Manual",
                    timestamp=1767044575,
                    collateral=[],
                    pool_addr="0x0000000000000000000000000000000000000000",
                ),
                timestamp_offchain=1767044568,
                pool_addr_offchain="0x123",
                version="5.0.0",
                pool_type=2,
                id="vault-account-id",
                timestamp=1767044568,
                timestamp_date_string="29-12-2025 UTC",
                timestamp_string="21:42:48 UTC",
                day_number=20451,
                time_of_day=78168,
                block_number=9941016,
                vault_name="Dynamic Vault 001",
                currency_label="ERC20",
                liquidity_token_symbol="MUSDC",
                pool_addr="0x123",
                account_addr="0x456",
                liquidity_asset_addr="0x456",
                token_balance="0",
                asset_balance="0",
                principal_earning_interest="0",
                max_withdraw_request="0",
                max_redeem_request="0",
                requested_shares_of="0",
                requested_assets_of="0",
                accepted_shares="0",
                accepted_assets="0",
                assets_deposited="0",
                assets_withdrawn="0",
                current_asset_value="0",
                gain_loss="0",
                gain_loss_in_day="0",
                credits="0",
                credits_in_day="0",
                debits="0",
                debits_in_day="0",
                fees="0",
                fees_in_day="0",
                interest_rate="1200",
                exchange_rate="1060438524345691461",
                indicative_interest_rate="0",
                collateral_rate="0",
            ),
            vault_address="0x123",
            account_address="0x456",
        )
        mock_service_class.get_vault_account.return_value = mock_vault

        response = self.client.get("/v1/opentrade/vaultsAccount/0x123/0x456")

        self.assertEqual(response.status_code, 200)
        data = response.json()
        # VaultAccountResponse uses vault_address in Python, vaultAddress as alias
        self.assertEqual(data.get("vaultAddress") or data.get("vault_address"), "0x123")

    @patch("app.routes.monetization_routes.MonetizationService")
    def test_get_vaults_list_success(self, mock_service_class):
        """Test getting vaults list successfully."""
        self.app.dependency_overrides[get_current_user] = lambda: self.mock_current_user

        from app.common.apis.cassandra.dtos import VaultListItem
        mock_vaults = VaultsListResponse(
            vault_list=[
                VaultListItem(
                    display_name="Test Vault",
                    chain_id=11155111,
                    contract_name="PoolDynamic",
                    pool_type=2,
                    chain_config_name="SandboxSepolia",
                    creation_block=8818602,
                    creation_timestamp=1753197612,
                    symbol="xFIGSOL",
                    name="Test Vault",
                    liquidity_asset_addr="0x123",
                    liquidity_token_symbol="MUSDC",
                    currency_label="ERC20",
                    pool_addr="0x456",
                )
            ],
        )
        mock_service_class.get_vaults_list.return_value = mock_vaults

        response = self.client.get("/v1/opentrade/vaults")

        self.assertEqual(response.status_code, 200)
        data = response.json()
        # VaultsListResponse uses vault_list in Python, vaultList as alias
        self.assertIn("vault_list", data)

    @patch("app.routes.monetization_routes.MonetizationService")
    def test_get_recipients_list_success(self, mock_service_class):
        """Test getting recipients list successfully."""
        self.app.dependency_overrides[get_current_user] = lambda: self.mock_current_user

        mock_recipients = [
            RecipientListResponse(
                id="rec-1",
                user_id="user-123",
                type="transfer",
                provider="BBVA",
                created_at="2025-12-31T21:05:11.794956+00:00",
                updated_at="2025-12-31T21:05:11.794956+00:00",
            )
        ]
        mock_service_class.get_recipients_list.return_value = mock_recipients

        response = self.client.get("/v1/recipients?provider=BBVA")

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("recipients", data)
        self.assertEqual(len(data["recipients"]), 1)

    @patch("app.routes.monetization_routes.MonetizationService")
    def test_create_recipient_success(self, mock_service_class):
        """Test creating recipient successfully."""
        self.app.dependency_overrides[get_current_user] = lambda: self.mock_current_user

        mock_recipient = RecipientListResponse(
            id="rec-new",
            user_id="user-123",
            type="transfer",
            provider="cobre",
            created_at="2025-12-31T21:05:11.794956+00:00",
            updated_at="2025-12-31T21:05:11.794956+00:00",
        )
        mock_service_class.create_recipient.return_value = mock_recipient

        recipient_data = {
            "user_id": "user-123",
            "type": "transfer",
            "first_name": "John",
            "last_name": "Doe",
            "document_type": "CC",
            "document_number": "1234567890",
            "bank_code": "001",
            "account_number": "123456789",
            "account_type": "checking",
            "provider": "cobre",
            "enabled": True,
        }

        response = self.client.post("/v1/recipients", json=recipient_data)

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["id"], "rec-new")

    @patch("app.routes.monetization_routes.MonetizationService")
    def test_update_recipient_success(self, mock_service_class):
        """Test updating recipient successfully."""
        self.app.dependency_overrides[get_current_user] = lambda: self.mock_current_user

        mock_recipient = RecipientListResponse(
            id="rec-1",
            user_id="user-123",
            type="transfer",
            first_name="Jane",
            last_name="Smith",
            provider="cobre",
            enabled=True,
            created_at="2025-12-31T21:05:11.794956+00:00",
            updated_at="2025-12-31T21:05:11.794956+00:00",
        )
        mock_service_class.update_recipient.return_value = mock_recipient

        recipient_data = {
            "first_name": "Jane",
            "last_name": "Smith",
        }

        response = self.client.put("/v1/recipients/rec-1", json=recipient_data)

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["first_name"], "Jane")

    @patch("app.routes.monetization_routes.MonetizationService")
    def test_delete_recipient_success(self, mock_service_class):
        """Test deleting recipient successfully."""
        self.app.dependency_overrides[get_current_user] = lambda: self.mock_current_user

        mock_service_class.delete_recipient.return_value = None

        response = self.client.delete("/v1/recipients/rec-1")

        self.assertEqual(response.status_code, 204)
        mock_service_class.delete_recipient.assert_called_once_with(recipient_id="rec-1")

    @patch("app.routes.monetization_routes.MonetizationService")
    def test_get_blockchain_wallets_success(self, mock_service_class):
        """Test getting blockchain wallets successfully."""
        self.app.dependency_overrides[get_current_user] = lambda: self.mock_current_user

        mock_wallets = [
            BlockchainWalletResponse(
                id="wallet-1",
                name="Test Wallet",
                provider="FIREBLOCKS",
                wallet_id="0x123",
                network="POLYGON",
                enabled=True,
                created_at="2025-12-31T15:22:32.738242+00:00",
                updated_at="2025-12-31T15:22:32.738242+00:00",
            )
        ]
        mock_service_class.get_blockchain_wallets.return_value = mock_wallets

        response = self.client.get("/v1/blockchain-wallets?provider=FIREBLOCKS")

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("wallets", data)
        self.assertEqual(len(data["wallets"]), 1)

    @patch("app.routes.monetization_routes.MonetizationService")
    def test_create_blockchain_wallet_success(self, mock_service_class):
        """Test creating blockchain wallet successfully."""
        self.app.dependency_overrides[get_current_user] = lambda: self.mock_current_user

        mock_wallet = BlockchainWalletResponse(
            id="wallet-new",
            name="New Wallet",
            provider="cobre",
            wallet_id="wallet_12345",
            network="ethereum",
            enabled=True,
            created_at="2025-12-31T15:22:32.738242+00:00",
            updated_at="2025-12-31T15:22:32.738242+00:00",
        )
        mock_service_class.create_blockchain_wallet.return_value = mock_wallet

        wallet_data = {
            "name": "New Wallet",
            "provider": "cobre",
            "wallet_id": "wallet_12345",
            "network": "ethereum",
            "enabled": True,
        }

        response = self.client.post("/v1/blockchain-wallets", json=wallet_data)

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["id"], "wallet-new")

    @patch("app.routes.monetization_routes.MonetizationService")
    def test_update_blockchain_wallet_success(self, mock_service_class):
        """Test updating blockchain wallet successfully."""
        self.app.dependency_overrides[get_current_user] = lambda: self.mock_current_user

        mock_wallet = BlockchainWalletResponse(
            id="wallet-1",
            name="Updated Wallet",
            provider="cobre",
            wallet_id="wallet_12345",
            network="ethereum",
            enabled=False,
            created_at="2025-12-31T15:22:32.738242+00:00",
            updated_at="2025-12-31T15:22:32.738242+00:00",
        )
        mock_service_class.update_blockchain_wallet.return_value = mock_wallet

        wallet_data = {
            "name": "Updated Wallet",
            "enabled": False,
        }

        response = self.client.put("/v1/blockchain-wallets/wallet-1", json=wallet_data)

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["name"], "Updated Wallet")

    @patch("app.routes.monetization_routes.MonetizationService")
    def test_delete_blockchain_wallet_success(self, mock_service_class):
        """Test deleting blockchain wallet successfully."""
        self.app.dependency_overrides[get_current_user] = lambda: self.mock_current_user

        mock_service_class.delete_blockchain_wallet.return_value = None

        response = self.client.delete("/v1/blockchain-wallets/wallet-1")

        self.assertEqual(response.status_code, 204)
        mock_service_class.delete_blockchain_wallet.assert_called_once_with(wallet_id="wallet-1")

    @patch("app.routes.monetization_routes.MonetizationService")
    def test_get_quote_generic_error(self, mock_service_class):
        """Test getting quote when generic error occurs."""
        self.app.dependency_overrides[get_current_user] = lambda: self.mock_current_user

        mock_service_class.get_quote.side_effect = Exception("Network error")

        response = self.client.get(
            "/v1/payouts/account/transfer/quote?amount=100&base_currency=USD&quote_currency=COP&provider=kira"
        )

        self.assertEqual(response.status_code, 502)
        data = response.json()
        self.assertIn("Error retrieving quote", data["detail"])

    @patch("app.routes.monetization_routes.MonetizationService")
    def test_get_balance_generic_error(self, mock_service_class):
        """Test getting balance when generic error occurs."""
        self.app.dependency_overrides[get_current_user] = lambda: self.mock_current_user

        mock_service_class.get_balance.side_effect = Exception("Network error")

        response = self.client.get(
            "/v1/payouts/account/transfer/wallets/wallet-123/balances?provider=kira"
        )

        self.assertEqual(response.status_code, 502)
        data = response.json()
        self.assertIn("Error retrieving balance", data["detail"])

    @patch("app.routes.monetization_routes.MonetizationService")
    @patch("app.routes.monetization_routes.UserService")
    def test_get_recipients_with_user_service(self, mock_user_service, mock_service_class):
        """Test getting recipients when user service is needed."""
        self.app.dependency_overrides[get_current_user] = lambda: self.mock_current_user

        from app.common.apis.cassandra.dtos import RecipientResponse
        mock_recipients = [
            RecipientResponse(
                recipient_id="rec-1",
                first_name="John",
                last_name="Doe",
                account_type="PSE",
            )
        ]
        mock_service_class.get_recipients.return_value = mock_recipients
        mock_user_service.get_user_by_firebase_uid.return_value = {"id": "user-123"}

        response = self.client.get(
            "/v1/payouts/account/transfer/recipient?provider=cobre"
        )

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("recipients", data)

    @patch("app.routes.monetization_routes.MonetizationService")
    def test_get_vault_overview_success(self, mock_service_class):
        """Test getting vault overview successfully."""
        self.app.dependency_overrides[get_current_user] = lambda: self.mock_current_user

        from app.common.apis.cassandra.dtos import VaultOverviewCTO, CollateralSetCTO
        mock_overview = VaultOverviewResponse(
            vault_overview_cto=VaultOverviewCTO(
                yield_type="DeFi",
                rollover_collateral=" ",
                automatic_rollover=False,
                early_withdrawal_processing_period=0,
                maximum_transfer_amount=1000000000,
                minimum_transfer_amount=100,
                contractual_currency=" USD",
                liquidity_fee_rate=20,
                platform_fee_rate=25,
                advisory_fee_rate=5,
                transfer_out_days=3,
                transfer_in_days=0,
                benchmark_rate=" NA",
                collateral=[],
                collateral_set_cto=CollateralSetCTO(
                    exchange_rate_automation="Manual",
                    timestamp=1767041714,
                    collateral=[],
                    pool_addr="0x0000000000000000000000000000000000000000",
                ),
                timestamp_offchain=1753198329,
                pool_addr_offchain="0x123",
                version="5.0.0",
                pool_type=2,
                pool_addr="0x123",
                id="0x123",
                chain_configuration_name="SandboxSepolia",
                creation_block=8818602,
                creation_timestamp=1753197612,
                liquidity_token_symbol="MUSDC",
                currency_label="ERC20",
                pool_admin_addr="0x517B2eBBd4fB0Bd0EEc0E9b540ae29E6984314f0",
                pool_controller_addr="0xe3aFa8b1cd6334D0DC15303446A2FEcdeb4f0Dd4",
                exchange_rate_type=3,
                name="Dynamic Test Vault 001",
                symbol="xFIGSOL",
                borrower_manager_addr="0x27E6A4Bc57f86B0ba15561dc5D822Fb539C2295e",
                borrower_wallet_addr="0x27E6A4Bc57f86B0ba15561dc5D822Fb539C2295e",
                close_of_deposit_time=64800,
                close_of_withdraw_time=64800,
                fee_collector_address="0x27E6A4Bc57f86B0ba15561dc5D822Fb539C2295e",
                liquidity_asset_addr="0xfd4f11A2aaE86165050688c85eC9ED6210C427A9",
                block_number=9940865,
                timestamp=1767042576,
                timestamp_date_string="29-12-2025 UTC",
                timestamp_string="21:09:36 UTC",
                time_of_day=76176,
                day_number=20451,
                chain_id=0,
                state=1,
                total_assets_deposited="11122887621000",
                total_assets_withdrawn="1201239102",
                interest_rate="1500",
                exchange_rate="1063588340855450534",
                exchange_rate_at_set_day="1063588340855450534",
                exchange_rate_set_day=20451,
                exchange_rate_change_rate="0",
                exchange_rate_compounding_rate="1000382982750000000",
                exchange_rate_at_maturity="1000000000000000000",
                exchange_rate_maturity_day=20291,
                indicative_interest_rate="0",
                collateral_rate="0",
                total_interest_accrued="657609398727",
                total_shares="11075051623029",
                total_assets="11779295780625",
                total_outstanding_loan_principal="11779295780625",
            ),
            vault_address="0x123",
        )
        mock_service_class.get_vault_overview.return_value = mock_overview

        response = self.client.get("/v1/opentrade/vaults/0x123")

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data.get("vaultAddress") or data.get("vault_address"), "0x123")

    @patch("app.routes.monetization_routes.MonetizationService")
    @patch("app.routes.monetization_routes.UserService")
    def test_create_payout_success(self, mock_user_service, mock_monetization_service):
        """Test creating payout successfully."""
        self._mock_require_mfa_verification()

        user_id = fake.uuid4()
        payout_id = fake.uuid4()
        recipient_id = fake.uuid4()
        quote_id = fake.uuid4()
        from_amount = str(fake.pydecimal(left_digits=3, right_digits=2, positive=True))
        to_amount = str(fake.pydecimal(left_digits=4, right_digits=2, positive=True))
        timestamp = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

        # Mock UserService.get_user_by_firebase_uid
        mock_user_service.get_user_by_firebase_uid.return_value = {"id": user_id}

        # Mock payout response
        mock_payout_response = PayoutResponse(
            payout_id=payout_id,
            user_id=user_id,
            recipient_id=recipient_id,
            quote_id=quote_id,
            from_amount=from_amount,
            from_currency=CURRENCY_USD,
            to_amount=to_amount,
            to_currency=CURRENCY_COP,
            status="pending",
            created_at=timestamp,
            updated_at=timestamp,
        )
        mock_monetization_service.create_payout.return_value = mock_payout_response

        payout_data = self._create_test_payout_request()

        response = self.client.post(
            f"/v1/payouts/account/{ACCOUNT_TRANSFER}/payout",
            json=payout_data,
            headers={"X-TOTP-Code": fake.numerify("######")},
        )

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["payout_id"], payout_id)
        self.assertEqual(data["status"], "pending")

    @patch("app.routes.monetization_routes.UserService")
    def test_create_payout_missing_provider(self, mock_user_service):
        """Test creating payout without provider."""
        self._mock_require_mfa_verification()

        user_id = fake.uuid4()

        # Mock UserService.get_user_by_firebase_uid
        mock_user_service.get_user_by_firebase_uid.return_value = {"id": user_id}

        # Remove provider from request data
        payout_data = self._create_test_payout_request()
        payout_data.pop("provider", None)

        response = self.client.post(
            f"/v1/payouts/account/{ACCOUNT_TRANSFER}/payout",
            json=payout_data,
            headers={"X-TOTP-Code": fake.numerify("######")},
        )

        # Pydantic validation returns 422 when required field is missing
        self.assertEqual(response.status_code, 422)
        data = response.json()
        # Pydantic error format
        self.assertIn("detail", data)

    @patch("app.routes.monetization_routes.UserService")
    def test_create_payout_missing_recipient_id(self, mock_user_service):
        """Test creating payout without recipient_id when exchange_only is False."""
        self._mock_require_mfa_verification()

        user_id = fake.uuid4()

        # Mock UserService.get_user_by_firebase_uid
        mock_user_service.get_user_by_firebase_uid.return_value = {"id": user_id}

        payout_data = self._create_test_payout_request(recipient_id=None, exchange_only=False)

        response = self.client.post(
            f"/v1/payouts/account/{ACCOUNT_TRANSFER}/payout",
            json=payout_data,
            headers={"X-TOTP-Code": fake.numerify("######")},
        )

        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertIn("recipient_id is required", data["detail"])

    @patch("app.routes.monetization_routes.MonetizationService")
    @patch("app.routes.monetization_routes.UserService")
    def test_create_payout_generic_error(self, mock_user_service, mock_monetization_service):
        """Test creating payout when generic error occurs."""
        self._mock_require_mfa_verification()

        user_id = fake.uuid4()
        error_message = fake.sentence()

        # Mock UserService.get_user_by_firebase_uid
        mock_user_service.get_user_by_firebase_uid.return_value = {"id": user_id}

        # Mock generic exception
        mock_monetization_service.create_payout.side_effect = Exception(error_message)

        payout_data = self._create_test_payout_request()

        response = self.client.post(
            f"/v1/payouts/account/{ACCOUNT_TRANSFER}/payout",
            json=payout_data,
            headers={"X-TOTP-Code": fake.numerify("######")},
        )

        self.assertEqual(response.status_code, 502)
        data = response.json()
        self.assertIn("Error creating payout", data["detail"])

    @patch("app.routes.monetization_routes.MonetizationService")
    @patch("app.routes.monetization_routes.UserService")
    def test_create_payout_cassandra_error(self, mock_user_service, mock_monetization_service):
        """Test creating payout when Cassandra API error occurs."""
        self._mock_require_mfa_verification()

        user_id = fake.uuid4()
        error_message = fake.sentence()

        # Mock UserService.get_user_by_firebase_uid
        mock_user_service.get_user_by_firebase_uid.return_value = {"id": user_id}

        # Mock Cassandra API error
        mock_monetization_service.create_payout.side_effect = CassandraAPIClientError(error_message)

        payout_data = self._create_test_payout_request()

        response = self.client.post(
            f"/v1/payouts/account/{ACCOUNT_TRANSFER}/payout",
            json=payout_data,
            headers={"X-TOTP-Code": fake.numerify("######")},
        )

        # Should return appropriate error status (usually 400 or 502)
        self.assertIn(response.status_code, [400, 502])
        data = response.json()
        self.assertIn("detail", data)

    @patch("app.routes.monetization_routes.MonetizationService")
    @patch("app.routes.monetization_routes.UserService")
    def test_create_payout_missing_credentials_error(self, mock_user_service, mock_monetization_service):
        """Test creating payout when missing credentials error occurs."""
        self._mock_require_mfa_verification()

        user_id = fake.uuid4()
        error_message = fake.sentence()

        # Mock UserService.get_user_by_firebase_uid
        mock_user_service.get_user_by_firebase_uid.return_value = {"id": user_id}

        # Mock MissingCredentialsError
        mock_monetization_service.create_payout.side_effect = MissingCredentialsError(error_message)

        payout_data = self._create_test_payout_request()

        response = self.client.post(
            f"/v1/payouts/account/{ACCOUNT_TRANSFER}/payout",
            json=payout_data,
            headers={"X-TOTP-Code": fake.numerify("######")},
        )

        self.assertEqual(response.status_code, 500)
        data = response.json()
        self.assertIn("Monetization service configuration error", data["detail"])

    @patch("app.routes.monetization_routes.MonetizationService")
    @patch("app.routes.monetization_routes.UserService")
    def test_create_payout_exchange_only_success(self, mock_user_service, mock_monetization_service):
        """Test creating payout with exchange_only=True (no recipient_id required)."""
        self._mock_require_mfa_verification()

        user_id = fake.uuid4()
        payout_id = fake.uuid4()
        quote_id = fake.uuid4()
        from_amount = str(fake.pydecimal(left_digits=3, right_digits=2, positive=True))
        to_amount = str(fake.pydecimal(left_digits=4, right_digits=2, positive=True))
        timestamp = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

        # Mock UserService.get_user_by_firebase_uid
        mock_user_service.get_user_by_firebase_uid.return_value = {"id": user_id}

        # Mock payout response
        mock_payout_response = PayoutResponse(
            payout_id=payout_id,
            user_id=user_id,
            recipient_id=None,
            quote_id=quote_id,
            from_amount=from_amount,
            from_currency=CURRENCY_USD,
            to_amount=to_amount,
            to_currency=CURRENCY_COP,
            status="pending",
            created_at=timestamp,
            updated_at=timestamp,
        )
        mock_monetization_service.create_payout.return_value = mock_payout_response

        payout_data = self._create_test_payout_request(recipient_id=None, exchange_only=True)

        response = self.client.post(
            f"/v1/payouts/account/{ACCOUNT_TRANSFER}/payout",
            json=payout_data,
            headers={"X-TOTP-Code": fake.numerify("######")},
        )

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["payout_id"], payout_id)

    @patch("app.routes.monetization_routes.MonetizationService")
    def test_get_payout_history_generic_error(self, mock_service_class):
        """Test getting payout history when generic error occurs."""
        self.app.dependency_overrides[get_current_user] = lambda: self.mock_current_user

        mock_service_class.get_payout_history.side_effect = Exception("Network error")

        response = self.client.get("/v1/payouts/account/transfer/payout")

        self.assertEqual(response.status_code, 502)
        data = response.json()
        self.assertIn("Error retrieving payout history", data["detail"])

    @patch("app.routes.monetization_routes.MonetizationService")
    def test_get_vault_account_generic_error(self, mock_service_class):
        """Test getting vault account when generic error occurs."""
        self.app.dependency_overrides[get_current_user] = lambda: self.mock_current_user

        mock_service_class.get_vault_account.side_effect = Exception("Network error")

        response = self.client.get("/v1/opentrade/vaultsAccount/0x123/0x456")

        self.assertEqual(response.status_code, 502)
        data = response.json()
        self.assertIn("Error retrieving vault account", data["detail"])

    @patch("app.routes.monetization_routes.MonetizationService")
    def test_get_vaults_list_generic_error(self, mock_service_class):
        """Test getting vaults list when generic error occurs."""
        self.app.dependency_overrides[get_current_user] = lambda: self.mock_current_user

        mock_service_class.get_vaults_list.side_effect = Exception("Network error")

        response = self.client.get("/v1/opentrade/vaults")

        self.assertEqual(response.status_code, 502)
        data = response.json()
        self.assertIn("Error retrieving vaults list", data["detail"])

    @patch("app.routes.monetization_routes.MonetizationService")
    def test_get_vault_overview_generic_error(self, mock_service_class):
        """Test getting vault overview when generic error occurs."""
        self.app.dependency_overrides[get_current_user] = lambda: self.mock_current_user

        mock_service_class.get_vault_overview.side_effect = Exception("Network error")

        response = self.client.get("/v1/opentrade/vaults/0x123")

        self.assertEqual(response.status_code, 502)
        data = response.json()
        self.assertIn("Error retrieving vault overview", data["detail"])

    @patch("app.routes.monetization_routes.MonetizationService")
    def test_get_recipients_list_generic_error(self, mock_service_class):
        """Test getting recipients list when generic error occurs."""
        self.app.dependency_overrides[get_current_user] = lambda: self.mock_current_user

        mock_service_class.get_recipients_list.side_effect = Exception("Network error")

        response = self.client.get("/v1/recipients")

        self.assertEqual(response.status_code, 502)
        data = response.json()
        self.assertIn("error", data["detail"])

    @patch("app.routes.monetization_routes.MonetizationService")
    def test_create_recipient_generic_error(self, mock_service_class):
        """Test creating recipient when generic error occurs."""
        self.app.dependency_overrides[get_current_user] = lambda: self.mock_current_user

        mock_service_class.create_recipient.side_effect = Exception("Network error")

        recipient_data = {
            "user_id": "user-123",
            "type": "transfer",
            "document_type": "CC",
            "document_number": "1234567890",
            "bank_code": "001",
            "account_number": "123456789",
            "account_type": "checking",
            "provider": "cobre",
            "enabled": True,
        }

        response = self.client.post("/v1/recipients", json=recipient_data)

        self.assertEqual(response.status_code, 502)
        data = response.json()
        self.assertIn("error", data["detail"])

    @patch("app.routes.monetization_routes.MonetizationService")
    def test_update_recipient_generic_error(self, mock_service_class):
        """Test updating recipient when generic error occurs."""
        self.app.dependency_overrides[get_current_user] = lambda: self.mock_current_user

        mock_service_class.update_recipient.side_effect = Exception("Network error")

        recipient_data = {
            "first_name": "Jane",
        }

        response = self.client.put("/v1/recipients/rec-1", json=recipient_data)

        self.assertEqual(response.status_code, 502)
        data = response.json()
        self.assertIn("error", data["detail"])

    @patch("app.routes.monetization_routes.MonetizationService")
    def test_delete_recipient_generic_error(self, mock_service_class):
        """Test deleting recipient when generic error occurs."""
        self.app.dependency_overrides[get_current_user] = lambda: self.mock_current_user

        mock_service_class.delete_recipient.side_effect = Exception("Network error")

        response = self.client.delete("/v1/recipients/rec-1")

        self.assertEqual(response.status_code, 502)
        data = response.json()
        self.assertIn("error", data["detail"])

    @patch("app.routes.monetization_routes.MonetizationService")
    def test_create_blockchain_wallet_generic_error(self, mock_service_class):
        """Test creating blockchain wallet when generic error occurs."""
        self.app.dependency_overrides[get_current_user] = lambda: self.mock_current_user

        mock_service_class.create_blockchain_wallet.side_effect = Exception("Network error")

        wallet_data = {
            "name": "New Wallet",
            "provider": "cobre",
            "wallet_id": "wallet_12345",
            "network": "ethereum",
            "enabled": True,
        }

        response = self.client.post("/v1/blockchain-wallets", json=wallet_data)

        self.assertEqual(response.status_code, 502)
        data = response.json()
        self.assertIn("error", data["detail"])

    @patch("app.routes.monetization_routes.MonetizationService")
    def test_update_blockchain_wallet_generic_error(self, mock_service_class):
        """Test updating blockchain wallet when generic error occurs."""
        self.app.dependency_overrides[get_current_user] = lambda: self.mock_current_user

        mock_service_class.update_blockchain_wallet.side_effect = Exception("Network error")

        wallet_data = {
            "name": "Updated Wallet",
        }

        response = self.client.put("/v1/blockchain-wallets/wallet-1", json=wallet_data)

        self.assertEqual(response.status_code, 502)
        data = response.json()
        self.assertIn("error", data["detail"])

    @patch("app.routes.monetization_routes.MonetizationService")
    def test_delete_blockchain_wallet_generic_error(self, mock_service_class):
        """Test deleting blockchain wallet when generic error occurs."""
        self.app.dependency_overrides[get_current_user] = lambda: self.mock_current_user

        mock_service_class.delete_blockchain_wallet.side_effect = Exception("Network error")

        response = self.client.delete("/v1/blockchain-wallets/wallet-1")

        self.assertEqual(response.status_code, 502)
        data = response.json()
        self.assertIn("error", data["detail"])

    @patch("app.routes.monetization_routes.MonetizationService")
    def test_get_payout_history_with_error_detail(self, mock_service_class):
        """Test getting payout history with error detail."""
        self.app.dependency_overrides[get_current_user] = lambda: self.mock_current_user

        from app.common.apis.cassandra.errors import CassandraAPIClientError
        mock_service_class.get_payout_history.side_effect = CassandraAPIClientError(
            "Error calling Cassandra API",
            status_code=502,
            error_detail={
                "error": {
                    "message": "Payout history error",
                    "code": "PAYOUT_ERROR",
                }
            },
        )

        response = self.client.get("/v1/payouts/account/transfer/payout")

        self.assertEqual(response.status_code, 502)
        data = response.json()
        self.assertIn("error", data["detail"])

    @patch("app.routes.monetization_routes.MonetizationService")
    def test_get_payout_history_without_error_detail(self, mock_service_class):
        """Test getting payout history without error detail."""
        self.app.dependency_overrides[get_current_user] = lambda: self.mock_current_user

        from app.common.apis.cassandra.errors import CassandraAPIClientError
        mock_service_class.get_payout_history.side_effect = CassandraAPIClientError(
            "Error calling Cassandra API",
            status_code=502,
            error_detail=None,
        )

        response = self.client.get("/v1/payouts/account/transfer/payout")

        self.assertEqual(response.status_code, 502)
        data = response.json()
        self.assertIn("error", data["detail"])

    @patch("app.routes.monetization_routes.MonetizationService")
    def test_get_recipients_generic_error(self, mock_service_class):
        """Test getting recipients when generic error occurs."""
        self.app.dependency_overrides[get_current_user] = lambda: self.mock_current_user

        mock_service_class.get_recipients.side_effect = Exception("Network error")

        response = self.client.get(
            "/v1/payouts/account/transfer/recipient?provider=kira&user_id=user-123"
        )

        self.assertEqual(response.status_code, 502)
        data = response.json()
        self.assertIn("error", data["detail"])

    @patch("app.routes.monetization_routes.MonetizationService")
    @patch("app.routes.monetization_routes.UserService")
    def test_get_recipients_with_cobre_provider(self, mock_user_service, mock_service_class):
        """Test getting recipients with cobre provider."""
        self.app.dependency_overrides[get_current_user] = lambda: self.mock_current_user

        mock_user_service.get_user_by_firebase_uid.return_value = {"id": "user-123"}
        from app.common.apis.cassandra.dtos import RecipientResponse
        mock_recipients = [
            RecipientResponse(
                recipient_id="rec-1",
                first_name="John",
                last_name="Doe",
                account_type="PSE",
            )
        ]
        mock_service_class.get_recipients.return_value = mock_recipients

        response = self.client.get(
            "/v1/payouts/account/transfer/recipient?provider=cobre"
        )

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("recipients", data)

    @patch("app.routes.monetization_routes.MonetizationService")
    def test_get_balance_invalid_provider(self, mock_service_class):
        """Test getting balance with invalid provider."""
        self.app.dependency_overrides[get_current_user] = lambda: self.mock_current_user

        response = self.client.get(
            "/v1/payouts/account/transfer/wallets/wallet-123/balances?provider=invalid"
        )

        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertIn("Invalid provider", data["detail"])

    @patch("app.routes.monetization_routes.MonetizationService")
    def test_get_quote_configuration_error(self, mock_service_class):
        """Test getting quote when configuration error occurs."""
        self.app.dependency_overrides[get_current_user] = lambda: self.mock_current_user

        from app.common.errors import MissingCredentialsError
        mock_service_class.get_quote.side_effect = MissingCredentialsError(
            "CASSANDRA_API_KEY not found"
        )

        response = self.client.get(
            "/v1/payouts/account/transfer/quote?amount=100&base_currency=USD&quote_currency=COP&provider=kira"
        )

        self.assertEqual(response.status_code, 500)
        data = response.json()
        self.assertIn("configuration error", data["detail"].lower())

    @patch("app.routes.monetization_routes.MonetizationService")
    def test_get_quote_cassandra_error(self, mock_service_class):
        """Test getting quote when Cassandra error occurs."""
        self.app.dependency_overrides[get_current_user] = lambda: self.mock_current_user

        from app.common.apis.cassandra.errors import CassandraAPIClientError
        mock_service_class.get_quote.side_effect = CassandraAPIClientError(
            "Error calling Cassandra API",
            status_code=502,
            error_detail={
                "error": {
                    "message": "Quote error",
                    "code": "QUOTE_ERROR",
                }
            },
        )

        response = self.client.get(
            "/v1/payouts/account/transfer/quote?amount=100&base_currency=USD&quote_currency=COP&provider=kira"
        )

        self.assertEqual(response.status_code, 502)
        data = response.json()
        self.assertIn("error", data["detail"])

    @patch("app.routes.monetization_routes.MonetizationService")
    def test_get_vault_account_configuration_error(self, mock_service_class):
        """Test getting vault account when configuration error occurs."""
        self.app.dependency_overrides[get_current_user] = lambda: self.mock_current_user

        from app.common.errors import MissingCredentialsError
        mock_service_class.get_vault_account.side_effect = MissingCredentialsError(
            "CASSANDRA_API_KEY not found"
        )

        response = self.client.get("/v1/opentrade/vaultsAccount/0x123/0x456")

        self.assertEqual(response.status_code, 500)
        data = response.json()
        self.assertIn("configuration error", data["detail"].lower())

    @patch("app.routes.monetization_routes.MonetizationService")
    def test_get_vault_account_cassandra_error(self, mock_service_class):
        """Test getting vault account when Cassandra error occurs."""
        self.app.dependency_overrides[get_current_user] = lambda: self.mock_current_user

        from app.common.apis.cassandra.errors import CassandraAPIClientError
        mock_service_class.get_vault_account.side_effect = CassandraAPIClientError(
            "Error calling Cassandra API",
            status_code=404,
            error_detail={
                "error": {
                    "message": "Vault not found",
                    "code": "NOT_FOUND",
                }
            },
        )

        response = self.client.get("/v1/opentrade/vaultsAccount/0x123/0x456")

        self.assertEqual(response.status_code, 404)
        data = response.json()
        self.assertIn("error", data["detail"])

    @patch("app.routes.monetization_routes.MonetizationService")
    def test_get_vaults_list_configuration_error(self, mock_service_class):
        """Test getting vaults list when configuration error occurs."""
        self.app.dependency_overrides[get_current_user] = lambda: self.mock_current_user

        from app.common.errors import MissingCredentialsError
        mock_service_class.get_vaults_list.side_effect = MissingCredentialsError(
            "CASSANDRA_API_KEY not found"
        )

        response = self.client.get("/v1/opentrade/vaults")

        self.assertEqual(response.status_code, 500)
        data = response.json()
        self.assertIn("configuration error", data["detail"].lower())

    @patch("app.routes.monetization_routes.MonetizationService")
    def test_get_vaults_list_cassandra_error(self, mock_service_class):
        """Test getting vaults list when Cassandra error occurs."""
        self.app.dependency_overrides[get_current_user] = lambda: self.mock_current_user

        from app.common.apis.cassandra.errors import CassandraAPIClientError
        mock_service_class.get_vaults_list.side_effect = CassandraAPIClientError(
            "Error calling Cassandra API",
            status_code=502,
            error_detail={
                "error": {
                    "message": "Vaults error",
                    "code": "VAULTS_ERROR",
                }
            },
        )

        response = self.client.get("/v1/opentrade/vaults")

        self.assertEqual(response.status_code, 502)
        data = response.json()
        self.assertIn("error", data["detail"])

    @patch("app.routes.monetization_routes.MonetizationService")
    def test_get_vault_overview_configuration_error(self, mock_service_class):
        """Test getting vault overview when configuration error occurs."""
        self.app.dependency_overrides[get_current_user] = lambda: self.mock_current_user

        from app.common.errors import MissingCredentialsError
        mock_service_class.get_vault_overview.side_effect = MissingCredentialsError(
            "CASSANDRA_API_KEY not found"
        )

        response = self.client.get("/v1/opentrade/vaults/0x123")

        self.assertEqual(response.status_code, 500)
        data = response.json()
        self.assertIn("configuration error", data["detail"].lower())

    @patch("app.routes.monetization_routes.MonetizationService")
    def test_get_vault_overview_cassandra_error(self, mock_service_class):
        """Test getting vault overview when Cassandra error occurs."""
        self.app.dependency_overrides[get_current_user] = lambda: self.mock_current_user

        from app.common.apis.cassandra.errors import CassandraAPIClientError
        mock_service_class.get_vault_overview.side_effect = CassandraAPIClientError(
            "Error calling Cassandra API",
            status_code=404,
            error_detail={
                "error": {
                    "message": "Vault not found",
                    "code": "NOT_FOUND",
                }
            },
        )

        response = self.client.get("/v1/opentrade/vaults/0x123")

        self.assertEqual(response.status_code, 404)
        data = response.json()
        self.assertIn("error", data["detail"])

    @patch("app.routes.monetization_routes.MonetizationService")
    def test_get_recipients_list_configuration_error(self, mock_service_class):
        """Test getting recipients list when configuration error occurs."""
        self.app.dependency_overrides[get_current_user] = lambda: self.mock_current_user

        from app.common.errors import MissingCredentialsError
        mock_service_class.get_recipients_list.side_effect = MissingCredentialsError(
            "CASSANDRA_API_KEY not found"
        )

        response = self.client.get("/v1/recipients")

        self.assertEqual(response.status_code, 500)
        data = response.json()
        self.assertIn("configuration error", data["detail"].lower())

    @patch("app.routes.monetization_routes.MonetizationService")
    def test_create_recipient_configuration_error(self, mock_service_class):
        """Test creating recipient when configuration error occurs."""
        self.app.dependency_overrides[get_current_user] = lambda: self.mock_current_user

        from app.common.errors import MissingCredentialsError
        mock_service_class.create_recipient.side_effect = MissingCredentialsError(
            "CASSANDRA_API_KEY not found"
        )

        recipient_data = {
            "user_id": "user-123",
            "type": "transfer",
            "document_type": "CC",
            "document_number": "1234567890",
            "bank_code": "001",
            "account_number": "123456789",
            "account_type": "checking",
            "provider": "cobre",
            "enabled": True,
        }

        response = self.client.post("/v1/recipients", json=recipient_data)

        self.assertEqual(response.status_code, 500)
        data = response.json()
        self.assertIn("configuration error", data["detail"].lower())

    @patch("app.routes.monetization_routes.MonetizationService")
    def test_update_recipient_configuration_error(self, mock_service_class):
        """Test updating recipient when configuration error occurs."""
        self.app.dependency_overrides[get_current_user] = lambda: self.mock_current_user

        from app.common.errors import MissingCredentialsError
        mock_service_class.update_recipient.side_effect = MissingCredentialsError(
            "CASSANDRA_API_KEY not found"
        )

        recipient_data = {
            "first_name": "Jane",
        }

        response = self.client.put("/v1/recipients/rec-1", json=recipient_data)

        self.assertEqual(response.status_code, 500)
        data = response.json()
        self.assertIn("configuration error", data["detail"].lower())

    @patch("app.routes.monetization_routes.MonetizationService")
    def test_delete_recipient_configuration_error(self, mock_service_class):
        """Test deleting recipient when configuration error occurs."""
        self.app.dependency_overrides[get_current_user] = lambda: self.mock_current_user

        from app.common.errors import MissingCredentialsError
        mock_service_class.delete_recipient.side_effect = MissingCredentialsError(
            "CASSANDRA_API_KEY not found"
        )

        response = self.client.delete("/v1/recipients/rec-1")

        self.assertEqual(response.status_code, 500)
        data = response.json()
        self.assertIn("configuration error", data["detail"].lower())

    @patch("app.routes.monetization_routes.MonetizationService")
    def test_get_blockchain_wallets_configuration_error(self, mock_service_class):
        """Test getting blockchain wallets when configuration error occurs."""
        self.app.dependency_overrides[get_current_user] = lambda: self.mock_current_user

        from app.common.errors import MissingCredentialsError
        mock_service_class.get_blockchain_wallets.side_effect = MissingCredentialsError(
            "CASSANDRA_API_KEY not found"
        )

        response = self.client.get("/v1/blockchain-wallets")

        self.assertEqual(response.status_code, 500)
        data = response.json()
        self.assertIn("configuration error", data["detail"].lower())

    @patch("app.routes.monetization_routes.MonetizationService")
    def test_create_blockchain_wallet_configuration_error(self, mock_service_class):
        """Test creating blockchain wallet when configuration error occurs."""
        self.app.dependency_overrides[get_current_user] = lambda: self.mock_current_user

        from app.common.errors import MissingCredentialsError
        mock_service_class.create_blockchain_wallet.side_effect = MissingCredentialsError(
            "CASSANDRA_API_KEY not found"
        )

        wallet_data = {
            "name": "New Wallet",
            "provider": "cobre",
            "wallet_id": "wallet_12345",
            "network": "ethereum",
            "enabled": True,
        }

        response = self.client.post("/v1/blockchain-wallets", json=wallet_data)

        self.assertEqual(response.status_code, 500)
        data = response.json()
        self.assertIn("configuration error", data["detail"].lower())

    @patch("app.routes.monetization_routes.MonetizationService")
    def test_update_blockchain_wallet_configuration_error(self, mock_service_class):
        """Test updating blockchain wallet when configuration error occurs."""
        self.app.dependency_overrides[get_current_user] = lambda: self.mock_current_user

        from app.common.errors import MissingCredentialsError
        mock_service_class.update_blockchain_wallet.side_effect = MissingCredentialsError(
            "CASSANDRA_API_KEY not found"
        )

        wallet_data = {
            "name": "Updated Wallet",
        }

        response = self.client.put("/v1/blockchain-wallets/wallet-1", json=wallet_data)

        self.assertEqual(response.status_code, 500)
        data = response.json()
        self.assertIn("configuration error", data["detail"].lower())

    @patch("app.routes.monetization_routes.MonetizationService")
    def test_delete_blockchain_wallet_configuration_error(self, mock_service_class):
        """Test deleting blockchain wallet when configuration error occurs."""
        self.app.dependency_overrides[get_current_user] = lambda: self.mock_current_user

        from app.common.errors import MissingCredentialsError
        mock_service_class.delete_blockchain_wallet.side_effect = MissingCredentialsError(
            "CASSANDRA_API_KEY not found"
        )

        response = self.client.delete("/v1/blockchain-wallets/wallet-1")

        self.assertEqual(response.status_code, 500)
        data = response.json()
        self.assertIn("configuration error", data["detail"].lower())


if __name__ == "__main__":
    unittest.main()
