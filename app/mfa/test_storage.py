"""Tests for TOTP storage."""

import unittest

from faker import Faker

from app.mfa.storage import TOTPStorage

fake = Faker()

# Constants for TOTP secret generation
SECRET_PATTERN = "????####"
SECRET_LETTERS = "ABCDEFGHIJKLMNOPQRSTUVWXYZ234567"


class TestTOTPStorage(unittest.TestCase):
    """Test cases for TOTPStorage."""

    def setUp(self):
        """Set up test fixtures."""
        # Clear storage before each test
        TOTPStorage._secrets.clear()

    def test_store_secret(self):
        """Test storing a TOTP secret."""
        firebase_uid = fake.uuid4()
        secret = fake.bothify(text=SECRET_PATTERN, letters=SECRET_LETTERS)
        TOTPStorage.store_secret(firebase_uid, secret)
        self.assertIn(firebase_uid, TOTPStorage._secrets)
        self.assertEqual(TOTPStorage._secrets[firebase_uid]["secret"], secret)
        self.assertTrue(TOTPStorage._secrets[firebase_uid]["is_active"])
        self.assertFalse(TOTPStorage._secrets[firebase_uid]["verified"])

    def test_get_secret_found(self):
        """Test getting a stored secret."""
        firebase_uid = fake.uuid4()
        secret = fake.bothify(text=SECRET_PATTERN, letters=SECRET_LETTERS)
        TOTPStorage.store_secret(firebase_uid, secret)
        retrieved_secret = TOTPStorage.get_secret(firebase_uid)
        self.assertEqual(retrieved_secret, secret)

    def test_get_secret_not_found(self):
        """Test getting a secret that doesn't exist."""
        retrieved_secret = TOTPStorage.get_secret(fake.uuid4())
        self.assertIsNone(retrieved_secret)

    def test_get_secret_inactive(self):
        """Test getting an inactive secret."""
        firebase_uid = fake.uuid4()
        secret = fake.bothify(text=SECRET_PATTERN, letters=SECRET_LETTERS)
        TOTPStorage.store_secret(firebase_uid, secret)
        TOTPStorage.deactivate(firebase_uid)
        retrieved_secret = TOTPStorage.get_secret(firebase_uid)
        self.assertIsNone(retrieved_secret)

    def test_is_verified_false(self):
        """Test checking verification status when not verified."""
        firebase_uid = fake.uuid4()
        secret = fake.bothify(text=SECRET_PATTERN, letters=SECRET_LETTERS)
        TOTPStorage.store_secret(firebase_uid, secret)
        is_verified = TOTPStorage.is_verified(firebase_uid)
        self.assertFalse(is_verified)

    def test_is_verified_true(self):
        """Test checking verification status when verified."""
        firebase_uid = fake.uuid4()
        secret = fake.bothify(text=SECRET_PATTERN, letters=SECRET_LETTERS)
        TOTPStorage.store_secret(firebase_uid, secret)
        TOTPStorage.mark_verified(firebase_uid)
        is_verified = TOTPStorage.is_verified(firebase_uid)
        self.assertTrue(is_verified)

    def test_is_verified_not_found(self):
        """Test checking verification status when user not found."""
        is_verified = TOTPStorage.is_verified(fake.uuid4())
        self.assertFalse(is_verified)

    def test_mark_verified(self):
        """Test marking TOTP as verified."""
        firebase_uid = fake.uuid4()
        secret = fake.bothify(text=SECRET_PATTERN, letters=SECRET_LETTERS)
        TOTPStorage.store_secret(firebase_uid, secret)
        TOTPStorage.mark_verified(firebase_uid)
        self.assertTrue(TOTPStorage._secrets[firebase_uid]["verified"])

    def test_deactivate(self):
        """Test deactivating TOTP."""
        firebase_uid = fake.uuid4()
        secret = fake.bothify(text=SECRET_PATTERN, letters=SECRET_LETTERS)
        TOTPStorage.store_secret(firebase_uid, secret)
        TOTPStorage.deactivate(firebase_uid)
        self.assertFalse(TOTPStorage._secrets[firebase_uid]["is_active"])
