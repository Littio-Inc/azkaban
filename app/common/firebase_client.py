"""Firebase Admin SDK client for token verification."""

import logging

from firebase_admin import auth, credentials, get_app, initialize_app
from firebase_admin.exceptions import FirebaseError

logger = logging.getLogger(__name__)

SERVICE_ACCOUNT_PATH = "service-account.json"


class FirebaseClient:
    """Client for Firebase ID token verification."""

    def __init__(self):
        """Initialize Firebase Admin SDK."""
        logger.info("FirebaseClient: Initializing Firebase Admin SDK")
        try:
            self._initialize_firebase()
        except Exception as exc:
            logger.error(f"FirebaseClient: Failed to initialize Firebase: {exc}", exc_info=True)
            raise
        logger.info("FirebaseClient: Firebase Admin SDK initialized successfully")

    def verify_id_token(self, id_token: str) -> dict:
        """
        Verify Firebase ID token.

        Args:
            id_token: The Firebase ID token to verify

        Returns:
            dict: Decoded token claims

        Raises:
            ValueError: If token format is invalid
            FirebaseError: If token verification fails
        """
        try:
            # Allow up to 10 seconds of clock skew to handle time synchronization issues
            # between client and server (especially in Docker containers)
            return auth.verify_id_token(id_token, clock_skew_seconds=10)
        except auth.ExpiredIdTokenError as exc:
            logger.error("Firebase ID token expired", exc_info=exc)
            raise ValueError("Token expired") from exc
        except auth.InvalidIdTokenError as exc:
            logger.error("Invalid Firebase ID token format", exc_info=exc)
            raise ValueError("Invalid token format") from exc
        except FirebaseError as exc:
            logger.error("Firebase ID token verification error", exc_info=exc)
            error_code = getattr(exc, "code", "unknown")
            raise FirebaseError(code=error_code, message="Token verification failed") from exc

    def _initialize_firebase(self) -> None:
        """Initialize Firebase Admin SDK with credentials.

        Raises:
            RuntimeError: If Firebase initialization fails
        """
        try:
            get_app()
        except ValueError:
            self._initialize_with_credentials()
        except (IOError, FirebaseError) as exc:
            self._handle_initialization_error(exc)

    def _initialize_with_credentials(self) -> None:
        """Initialize Firebase with credentials.

        Raises:
            RuntimeError: If Firebase initialization fails
        """
        creds = self._load_credentials()
        try:
            initialize_app(creds)
        except (IOError, FirebaseError) as exc:
            self._handle_initialization_error(exc)

    def _handle_initialization_error(self, exc: Exception) -> None:
        """Handle Firebase initialization errors.

        Args:
            exc: The exception that occurred

        Raises:
            RuntimeError: With appropriate error message
        """
        if isinstance(exc, IOError):
            logger.error("Error reading Firebase credentials", exc_info=exc)
            raise RuntimeError(
                "Error reading Firebase credentials. Please check file permissions and format.",
            ) from exc
        if isinstance(exc, FirebaseError):
            logger.error("Firebase initialization error", exc_info=exc)
            raise RuntimeError(
                "Firebase initialization failed. Please check your Firebase project configuration.",
            ) from exc

    def _load_credentials(self) -> credentials.Certificate:
        """Load Firebase credentials from service-account.json file.

        Returns:
            credentials.Certificate: Firebase credentials

        Raises:
            FileNotFoundError: If credentials file is not found
            ValueError: If credentials file is invalid or malformed
            RuntimeError: If there are permission issues or other system errors
        """
        try:
            return credentials.Certificate(SERVICE_ACCOUNT_PATH)
        except FileNotFoundError as exc:
            logger.error("Firebase credentials file not found", exc_info=exc)
            raise FileNotFoundError(
                f"{SERVICE_ACCOUNT_PATH} not found at project root. "
                "Please ensure the file exists and has correct permissions.",
            ) from exc
        except ValueError as val_exc:
            logger.exception("Invalid or malformed Firebase credentials", exc_info=val_exc)
            raise ValueError(
                f"Invalid or malformed {SERVICE_ACCOUNT_PATH}. Please check the file contents and format.",
            ) from val_exc
        except PermissionError as perm_exc:
            logger.exception("Permission denied accessing Firebase credentials", exc_info=perm_exc)
            raise RuntimeError(
                f"Permission denied accessing {SERVICE_ACCOUNT_PATH}. Please check file permissions.",
            ) from perm_exc
