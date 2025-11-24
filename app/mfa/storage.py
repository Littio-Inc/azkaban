"""Storage for TOTP secrets (in-memory for development, database for production)."""

import logging

logger = logging.getLogger(__name__)


class TOTPStorage:
    """Storage for TOTP secrets."""

    # In-memory storage for development
    _secrets: dict[str, dict] = {}

    @classmethod
    def store_secret(
        cls,
        firebase_uid: str,
        secret: str,
    ) -> None:
        """Store TOTP secret for user.

        Args:
            firebase_uid: Firebase user ID
            secret: TOTP secret (base32)
        """
        cls._secrets[firebase_uid] = {
            "secret": secret,
            "is_active": True,
            "verified": False,
        }
        logger.debug("Stored secret for user %s", firebase_uid)

    @classmethod
    def get_secret(cls, firebase_uid: str) -> str | None:
        """Get TOTP secret for user.

        Args:
            firebase_uid: Firebase user ID

        Returns:
            str: TOTP secret or None if not found
        """
        secret_data = cls._secrets.get(firebase_uid)
        if secret_data and secret_data.get("is_active"):
            return secret_data.get("secret")
        return None

    @classmethod
    def is_verified(cls, firebase_uid: str) -> bool:
        """Check if TOTP is verified for user.

        Args:
            firebase_uid: Firebase user ID

        Returns:
            bool: True if verified, False otherwise
        """
        secret_data = cls._secrets.get(firebase_uid)
        return secret_data.get("verified", False) if secret_data else False

    @classmethod
    def mark_verified(cls, firebase_uid: str) -> None:
        """Mark TOTP as verified for user.

        Args:
            firebase_uid: Firebase user ID
        """
        if firebase_uid in cls._secrets:
            cls._secrets[firebase_uid]["verified"] = True
            logger.debug("Marked as verified for user %s", firebase_uid)

    @classmethod
    def deactivate(cls, firebase_uid: str) -> None:
        """Deactivate TOTP for user.

        Args:
            firebase_uid: Firebase user ID
        """
        if firebase_uid in cls._secrets:
            cls._secrets[firebase_uid]["is_active"] = False
            logger.debug("Deactivated for user %s", firebase_uid)
