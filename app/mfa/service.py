"""TOTP service for Google Authenticator two-factor authentication."""

import base64
import io

import pyotp
import qrcode


class TOTPService:
    """Service for generating and verifying TOTP codes."""

    ISSUER_NAME = "Dobby - Littio"
    TOTP_INTERVAL = 30  # Standard TOTP interval (30 seconds)

    @staticmethod
    def generate_secret() -> str:
        """Generate a new TOTP secret.

        Returns:
            str: Base32 encoded secret
        """
        return pyotp.random_base32()

    @staticmethod
    def get_totp_uri(secret: str, email: str) -> str:
        """Generate TOTP URI for QR code.

        Args:
            secret: TOTP secret (base32)
            email: User email

        Returns:
            str: TOTP URI
        """
        totp = pyotp.TOTP(secret)
        return totp.provisioning_uri(
            name=email,
            issuer_name=TOTPService.ISSUER_NAME
        )

    @staticmethod
    def generate_qr_code(uri: str) -> str:
        """Generate QR code as base64 image.

        Args:
            uri: TOTP URI

        Returns:
            str: Base64 encoded PNG image
        """
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(uri)
        qr.make(fit=True)

        img = qr.make_image(fill_color="black", back_color="white")

        # Convert to base64
        buffer = io.BytesIO()
        img.save(buffer, format="PNG")
        img_str = base64.b64encode(buffer.getvalue()).decode()

        return f"data:image/png;base64,{img_str}"

    @staticmethod
    def verify_totp(secret: str, code: str, window: int = 1) -> bool:
        """Verify TOTP code.

        Args:
            secret: TOTP secret (base32)
            code: TOTP code to verify (6 digits)
            window: Time window for verification (default: 1 = current and previous interval)

        Returns:
            bool: True if code is valid, False otherwise
        """
        if not code or len(code) != 6 or not code.isdigit():
            return False

        totp = pyotp.TOTP(secret)
        return totp.verify(code, valid_window=window)

    @staticmethod
    def get_current_totp(secret: str) -> str:
        """Get current TOTP code (for testing).

        Args:
            secret: TOTP secret (base32)

        Returns:
            str: Current 6-digit TOTP code
        """
        totp = pyotp.TOTP(secret)
        return totp.now()
