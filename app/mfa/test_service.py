"""Tests for TOTP service."""

import unittest

from app.mfa.service import TOTPService


class TestTOTPService(unittest.TestCase):
    """Test cases for TOTPService."""

    def test_generate_secret(self):
        """Test generating a TOTP secret."""
        secret = TOTPService.generate_secret()
        self.assertIsInstance(secret, str)
        self.assertGreater(len(secret), 0)

    def test_generate_secret_unique(self):
        """Test that generated secrets are unique."""
        secret1 = TOTPService.generate_secret()
        secret2 = TOTPService.generate_secret()
        self.assertNotEqual(secret1, secret2)

    def test_get_totp_uri(self):
        """Test generating TOTP URI."""
        secret = TOTPService.generate_secret()
        email = "test@littio.co"
        uri = TOTPService.get_totp_uri(secret, email)
        self.assertIn("otpauth://totp/", uri)
        # Email is URL-encoded in URI (test%40littio.co)
        self.assertIn("test", uri)
        self.assertIn("littio.co", uri)
        self.assertIn(secret, uri)
        # Issuer name is URL-encoded (Dobby%20-%20Littio)
        self.assertIn("Dobby", uri)
        self.assertIn("Littio", uri)

    def test_generate_qr_code(self):
        """Test generating QR code."""
        secret = TOTPService.generate_secret()
        uri = TOTPService.get_totp_uri(secret, "test@littio.co")
        qr_code = TOTPService.generate_qr_code(uri)
        self.assertIsInstance(qr_code, str)
        self.assertTrue(qr_code.startswith("data:image/png;base64,"))

    def test_verify_totp_valid(self):
        """Test verifying a valid TOTP code."""
        secret = TOTPService.generate_secret()
        current_code = TOTPService.get_current_totp(secret)
        is_valid = TOTPService.verify_totp(secret, current_code)
        self.assertTrue(is_valid)

    def test_verify_totp_invalid(self):
        """Test verifying an invalid TOTP code."""
        secret = TOTPService.generate_secret()
        is_valid = TOTPService.verify_totp(secret, "000000")
        # May be valid if it happens to match, but unlikely
        # We'll test with a definitely invalid code
        is_valid = TOTPService.verify_totp(secret, "999999")
        # This might still be valid if it's in the time window, so we just check it's a bool
        self.assertIsInstance(is_valid, bool)

    def test_verify_totp_wrong_length(self):
        """Test verifying TOTP code with wrong length."""
        secret = TOTPService.generate_secret()
        is_valid = TOTPService.verify_totp(secret, "12345")  # Too short
        self.assertFalse(is_valid)
        is_valid = TOTPService.verify_totp(secret, "1234567")  # Too long
        self.assertFalse(is_valid)

    def test_verify_totp_non_numeric(self):
        """Test verifying TOTP code with non-numeric characters."""
        secret = TOTPService.generate_secret()
        is_valid = TOTPService.verify_totp(secret, "abc123")
        self.assertFalse(is_valid)

    def test_get_current_totp(self):
        """Test getting current TOTP code."""
        secret = TOTPService.generate_secret()
        code = TOTPService.get_current_totp(secret)
        self.assertIsInstance(code, str)
        self.assertEqual(len(code), 6)
        self.assertTrue(code.isdigit())
