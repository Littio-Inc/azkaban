"""Firebase Admin SDK configuration.

This module initializes Firebase Admin SDK on import.
The actual Firebase client is now in app.common.firebase_client.FirebaseClient.
"""


def _init_firebase_client() -> None:
    """Initialize Firebase client if available."""
    try:
        FirebaseClient()  # noqa: WPS122
    except Exception:
        pass  # noqa: WPS420


# Import and instantiate FirebaseClient to ensure Firebase is initialized
# This maintains backward compatibility for imports like:
# from app.common.config import firebase_client
try:
    from app.common.firebase_client import FirebaseClient
except ImportError:
    FirebaseClient = None  # type: ignore
else:
    # Firebase config is optional for local dev
    # If Firebase initialization fails, continue without it
    # The authorizer will handle its own initialization
    _init_firebase_client()

# For backward compatibility, expose firebase_admin
try:
    import firebase_admin as firebase_admin  # noqa: F401
except ImportError:
    firebase_admin = None
