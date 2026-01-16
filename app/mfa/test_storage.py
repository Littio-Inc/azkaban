"""Tests for TOTP storage."""

import unittest
from unittest.mock import MagicMock, patch

from faker import Faker
from sqlalchemy.exc import SQLAlchemyError

from app.mfa.storage import TOTPStorage
from app.models.totp_secret import TOTPSecret

fake = Faker()

# Constants for TOTP secret generation
SECRET_PATTERN = "????####"
SECRET_LETTERS = "ABCDEFGHIJKLMNOPQRSTUVWXYZ234567"


class TestTOTPStorage(unittest.TestCase):
    """Test cases for TOTPStorage."""

    def setUp(self):
        """Set up test fixtures."""
        self.mock_db = MagicMock()
        self.mock_session = MagicMock()
        self.mock_none_return = MagicMock(return_value=None)
        self.mock_session.__enter__ = MagicMock(return_value=self.mock_db)
        self.mock_session.__exit__ = self.mock_none_return

    @patch("app.mfa.storage.SessionLocal")
    def test_store_secret(self, mock_session_local):
        """Test storing a TOTP secret."""
        mock_session_local.return_value = self.mock_session
        firebase_uid = fake.uuid4()
        secret = fake.bothify(text=SECRET_PATTERN, letters=SECRET_LETTERS)

        # Mock no existing secret
        mock_query = MagicMock()
        mock_filter = MagicMock()
        mock_first = self.mock_none_return
        mock_filter.first = mock_first
        mock_query.filter.return_value = mock_filter
        self.mock_db.query.return_value = mock_query

        TOTPStorage.store_secret(firebase_uid, secret)

        # Verify that add was called with a TOTPSecret object
        self.mock_db.add.assert_called_once()
        call_args = self.mock_db.add.call_args
        added_secret = call_args[0][0]
        self.assertIsInstance(added_secret, TOTPSecret)
        self.assertEqual(added_secret.firebase_uid, firebase_uid)
        self.assertEqual(added_secret.secret, secret)
        self.assertTrue(added_secret.is_active)
        self.mock_db.commit.assert_called_once()

    @patch("app.mfa.storage.SessionLocal")
    @patch("app.mfa.storage.datetime")
    def test_store_secret_update_existing(self, mock_datetime, mock_session_local):
        """Test updating an existing TOTP secret."""
        mock_session_local.return_value = self.mock_session
        mock_now = MagicMock()
        mock_datetime.utcnow.return_value = mock_now
        firebase_uid = fake.uuid4()
        new_secret = fake.bothify(text=SECRET_PATTERN, letters=SECRET_LETTERS)

        # Mock existing secret
        mock_existing = MagicMock()
        mock_existing.secret = "OLDSECRET"
        mock_existing.is_active = False
        mock_existing.verified_at = "2024-01-01T00:00:00"
        mock_query = MagicMock()
        mock_filter = MagicMock()
        mock_first = MagicMock(return_value=mock_existing)
        mock_filter.first = mock_first
        mock_query.filter.return_value = mock_filter
        self.mock_db.query.return_value = mock_query

        TOTPStorage.store_secret(firebase_uid, new_secret)

        # Verify that existing secret was updated
        self.assertEqual(mock_existing.secret, new_secret)
        self.assertTrue(mock_existing.is_active)
        self.assertIsNone(mock_existing.verified_at)
        self.assertEqual(mock_existing.updated_at, mock_now)
        self.mock_db.add.assert_not_called()
        self.mock_db.commit.assert_called_once()

    @patch("app.mfa.storage.SessionLocal")
    def test_store_secret_database_error(self, mock_session_local):
        """Test storing secret when database error occurs."""
        mock_session_local.return_value = self.mock_session
        firebase_uid = fake.uuid4()
        secret = fake.bothify(text=SECRET_PATTERN, letters=SECRET_LETTERS)

        # Mock database error
        mock_query = MagicMock()
        mock_filter = MagicMock()
        mock_first = self.mock_none_return
        mock_filter.first = mock_first
        mock_query.filter.return_value = mock_filter
        self.mock_db.query.return_value = mock_query
        self.mock_db.commit.side_effect = SQLAlchemyError("Database error")

        with self.assertRaises(SQLAlchemyError):
            TOTPStorage.store_secret(firebase_uid, secret)

        self.mock_db.rollback.assert_called_once()

    @patch("app.mfa.storage.SessionLocal")
    def test_get_secret_found(self, mock_session_local):
        """Test getting a stored secret."""
        mock_session_local.return_value = self.mock_session
        firebase_uid = fake.uuid4()
        secret = fake.bothify(text=SECRET_PATTERN, letters=SECRET_LETTERS)

        # Mock existing secret
        mock_totp_secret = MagicMock()
        mock_totp_secret.secret = secret
        mock_query = MagicMock()
        mock_filter = MagicMock()
        mock_first = MagicMock(return_value=mock_totp_secret)
        mock_filter.first = mock_first
        mock_query.filter.return_value = mock_filter
        self.mock_db.query.return_value = mock_query

        retrieved_secret = TOTPStorage.get_secret(firebase_uid)
        self.assertEqual(retrieved_secret, secret)

    @patch("app.mfa.storage.SessionLocal")
    def test_get_secret_not_found(self, mock_session_local):
        """Test getting a secret that doesn't exist."""
        mock_session_local.return_value = self.mock_session
        mock_query = MagicMock()
        mock_filter = MagicMock()
        mock_first = self.mock_none_return
        mock_filter.first = mock_first
        mock_query.filter.return_value = mock_filter
        self.mock_db.query.return_value = mock_query

        retrieved_secret = TOTPStorage.get_secret(fake.uuid4())
        self.assertIsNone(retrieved_secret)

    @patch("app.mfa.storage.SessionLocal")
    def test_get_secret_inactive(self, mock_session_local):
        """Test getting an inactive secret."""
        mock_session_local.return_value = self.mock_session
        # Inactive secrets should return None
        mock_query = MagicMock()
        mock_filter = MagicMock()
        mock_first = self.mock_none_return
        mock_filter.first = mock_first
        mock_query.filter.return_value = mock_filter
        self.mock_db.query.return_value = mock_query

        firebase_uid = fake.uuid4()
        retrieved_secret = TOTPStorage.get_secret(firebase_uid)
        self.assertIsNone(retrieved_secret)

        # Verify that filter was called with both firebase_uid and is_active conditions
        mock_query.filter.assert_called_once()
        filter_call_args = mock_query.filter.call_args
        call_args_list = filter_call_args[0]
        self.assertEqual(len(call_args_list), 2, "Filter should be called with 2 conditions")
        # First condition: TOTPSecret.firebase_uid == firebase_uid
        # Second condition: TOTPSecret.is_active.is_(True)
        # Verify both conditions were passed to filter
        first_condition = call_args_list[0]
        second_condition = call_args_list[1]
        self.assertIsNotNone(first_condition, "First filter condition (firebase_uid) should not be None")
        self.assertIsNotNone(second_condition, "Second filter condition (is_active) should not be None")
        # Verify the filter includes is_active check by checking that the second condition
        # references TOTPSecret.is_active - inspect the call args to verify is_active is included
        # The second argument should be a SQLAlchemy expression for is_active.is_(True)
        # Check the string representation contains is_active
        second_condition_str = str(second_condition)
        self.assertIn(
            "is_active",
            second_condition_str,
            "Second filter condition should include is_active check to exclude inactive secrets"
        )

    @patch("app.mfa.storage.SessionLocal")
    def test_get_secret_database_error(self, mock_session_local):
        """Test getting secret when database error occurs."""
        mock_session_local.return_value = self.mock_session
        firebase_uid = fake.uuid4()

        # Mock database error
        self.mock_db.query.side_effect = SQLAlchemyError("Database error")

        retrieved_secret = TOTPStorage.get_secret(firebase_uid)
        self.assertIsNone(retrieved_secret)

    @patch("app.mfa.storage.SessionLocal")
    def test_is_verified_false(self, mock_session_local):
        """Test checking verification status when not verified."""
        mock_session_local.return_value = self.mock_session
        firebase_uid = fake.uuid4()

        # Mock secret with verified_at = None
        mock_totp_secret = MagicMock()
        mock_totp_secret.verified_at = None
        mock_query = MagicMock()
        mock_filter = MagicMock()
        mock_first = MagicMock(return_value=mock_totp_secret)
        mock_filter.first = mock_first
        mock_query.filter.return_value = mock_filter
        self.mock_db.query.return_value = mock_query

        is_verified = TOTPStorage.is_verified(firebase_uid)
        self.assertFalse(is_verified)

    @patch("app.mfa.storage.SessionLocal")
    def test_is_verified_true(self, mock_session_local):
        """Test checking verification status when verified."""
        mock_session_local.return_value = self.mock_session
        firebase_uid = fake.uuid4()

        # Mock secret with verified_at set
        mock_totp_secret = MagicMock()
        mock_totp_secret.verified_at = "2024-01-01T00:00:00"
        mock_query = MagicMock()
        mock_filter = MagicMock()
        mock_first = MagicMock(return_value=mock_totp_secret)
        mock_filter.first = mock_first
        mock_query.filter.return_value = mock_filter
        self.mock_db.query.return_value = mock_query

        is_verified = TOTPStorage.is_verified(firebase_uid)
        self.assertTrue(is_verified)

    @patch("app.mfa.storage.SessionLocal")
    def test_is_verified_not_found(self, mock_session_local):
        """Test checking verification status when user not found."""
        mock_session_local.return_value = self.mock_session
        mock_query = MagicMock()
        mock_filter = MagicMock()
        mock_first = self.mock_none_return
        mock_filter.first = mock_first
        mock_query.filter.return_value = mock_filter
        self.mock_db.query.return_value = mock_query

        is_verified = TOTPStorage.is_verified(fake.uuid4())
        self.assertFalse(is_verified)

    @patch("app.mfa.storage.SessionLocal")
    def test_is_verified_database_error(self, mock_session_local):
        """Test checking verification status when database error occurs."""
        mock_session_local.return_value = self.mock_session
        firebase_uid = fake.uuid4()

        # Mock database error
        self.mock_db.query.side_effect = SQLAlchemyError("Database error")

        is_verified = TOTPStorage.is_verified(firebase_uid)
        self.assertFalse(is_verified)

    @patch("app.mfa.storage.SessionLocal")
    @patch("app.mfa.storage.datetime")
    def test_mark_verified(self, mock_datetime, mock_session_local):
        """Test marking TOTP as verified."""
        mock_session_local.return_value = self.mock_session
        mock_now = MagicMock()
        mock_datetime.utcnow.return_value = mock_now

        firebase_uid = fake.uuid4()
        mock_totp_secret = MagicMock()
        mock_query = MagicMock()
        mock_filter = MagicMock()
        mock_first = MagicMock(return_value=mock_totp_secret)
        mock_filter.first = mock_first
        mock_query.filter.return_value = mock_filter
        self.mock_db.query.return_value = mock_query

        TOTPStorage.mark_verified(firebase_uid)

        self.assertEqual(mock_totp_secret.verified_at, mock_now)
        self.assertEqual(mock_totp_secret.updated_at, mock_now)
        self.mock_db.commit.assert_called_once()

    @patch("app.mfa.storage.SessionLocal")
    def test_mark_verified_not_found(self, mock_session_local):
        """Test marking TOTP as verified when secret not found."""
        mock_session_local.return_value = self.mock_session
        firebase_uid = fake.uuid4()

        # Mock no existing secret
        mock_query = MagicMock()
        mock_filter = MagicMock()
        mock_first = self.mock_none_return
        mock_filter.first = mock_first
        mock_query.filter.return_value = mock_filter
        self.mock_db.query.return_value = mock_query

        # Should not raise error, just do nothing
        TOTPStorage.mark_verified(firebase_uid)
        self.mock_db.commit.assert_not_called()

    @patch("app.mfa.storage.SessionLocal")
    def test_mark_verified_database_error(self, mock_session_local):
        """Test marking TOTP as verified when database error occurs."""
        mock_session_local.return_value = self.mock_session
        firebase_uid = fake.uuid4()

        # Mock database error
        mock_totp_secret = MagicMock()
        mock_query = MagicMock()
        mock_filter = MagicMock()
        mock_first = MagicMock(return_value=mock_totp_secret)
        mock_filter.first = mock_first
        mock_query.filter.return_value = mock_filter
        self.mock_db.query.return_value = mock_query
        self.mock_db.commit.side_effect = SQLAlchemyError("Database error")

        with self.assertRaises(SQLAlchemyError):
            TOTPStorage.mark_verified(firebase_uid)

        self.mock_db.rollback.assert_called_once()

    @patch("app.mfa.storage.SessionLocal")
    @patch("app.mfa.storage.datetime")
    def test_deactivate(self, mock_datetime, mock_session_local):
        """Test deactivating TOTP."""
        mock_session_local.return_value = self.mock_session
        mock_now = MagicMock()
        mock_datetime.utcnow.return_value = mock_now

        firebase_uid = fake.uuid4()
        mock_totp_secret = MagicMock()
        mock_query = MagicMock()
        mock_filter = MagicMock()
        mock_first = MagicMock(return_value=mock_totp_secret)
        mock_filter.first = mock_first
        mock_query.filter.return_value = mock_filter
        self.mock_db.query.return_value = mock_query

        TOTPStorage.deactivate(firebase_uid)

        self.assertFalse(mock_totp_secret.is_active)
        self.assertEqual(mock_totp_secret.updated_at, mock_now)
        self.mock_db.commit.assert_called_once()

    @patch("app.mfa.storage.SessionLocal")
    def test_deactivate_not_found(self, mock_session_local):
        """Test deactivating TOTP when secret not found."""
        mock_session_local.return_value = self.mock_session
        firebase_uid = fake.uuid4()

        # Mock no existing secret
        mock_query = MagicMock()
        mock_filter = MagicMock()
        mock_first = self.mock_none_return
        mock_filter.first = mock_first
        mock_query.filter.return_value = mock_filter
        self.mock_db.query.return_value = mock_query

        # Should not raise error, just do nothing
        TOTPStorage.deactivate(firebase_uid)
        self.mock_db.commit.assert_not_called()

    @patch("app.mfa.storage.SessionLocal")
    def test_deactivate_database_error(self, mock_session_local):
        """Test deactivating TOTP when database error occurs."""
        mock_session_local.return_value = self.mock_session
        firebase_uid = fake.uuid4()

        # Mock database error
        mock_totp_secret = MagicMock()
        mock_query = MagicMock()
        mock_filter = MagicMock()
        mock_first = MagicMock(return_value=mock_totp_secret)
        mock_filter.first = mock_first
        mock_query.filter.return_value = mock_filter
        self.mock_db.query.return_value = mock_query
        self.mock_db.commit.side_effect = SQLAlchemyError("Database error")

        with self.assertRaises(SQLAlchemyError):
            TOTPStorage.deactivate(firebase_uid)

        self.mock_db.rollback.assert_called_once()
