"""Service for API Gateway authorizer token verification."""

import logging
from typing import Any

from app.common.firebase_client import FirebaseClient

logger = logging.getLogger(__name__)

LOG_TAG = "AUTHORIZER"

# Constants for token keys
TOKEN_EMAIL_KEY = "email"
TOKEN_UID_KEY = "uid"
TOKEN_NAME_KEY = "name"
TOKEN_PICTURE_KEY = "picture"
CONTEXT_USER_ID_KEY = "user_id"
CONTEXT_EMAIL_KEY = "email"
CONTEXT_NAME_KEY = "name"
CONTEXT_PICTURE_KEY = "picture"


def _extract_user_info(decoded_token: dict[str, Any]) -> dict[str, str]:
    """Extract user information from decoded token.

    Args:
        decoded_token: Decoded Firebase token

    Returns:
        Dictionary with user information
    """
    return {
        TOKEN_EMAIL_KEY: decoded_token.get(TOKEN_EMAIL_KEY, ""),
        "firebase_uid": decoded_token.get(TOKEN_UID_KEY, ""),
        TOKEN_NAME_KEY: decoded_token.get(TOKEN_NAME_KEY, ""),
        TOKEN_PICTURE_KEY: decoded_token.get(TOKEN_PICTURE_KEY, ""),
    }


def _build_authorizer_context(user_info: dict[str, str]) -> dict[str, str]:
    """Build authorizer context from user info.

    Args:
        user_info: User information dictionary

    Returns:
        Authorizer context dictionary
    """
    firebase_uid = user_info["firebase_uid"]
    email = user_info[TOKEN_EMAIL_KEY]
    return {
        CONTEXT_USER_ID_KEY: firebase_uid,
        CONTEXT_EMAIL_KEY: email,
        CONTEXT_NAME_KEY: user_info[TOKEN_NAME_KEY] or "",
        CONTEXT_PICTURE_KEY: user_info[TOKEN_PICTURE_KEY] or "",
    }


class AuthorizerService:
    """Service for handling Firebase ID token verification and policy generation."""

    def __init__(self):
        """Initialize the service."""
        self.firebase_client = FirebaseClient()

    def extract_token(self, event: dict[str, Any]) -> str:
        """Extract token from event.

        Args:
            event: API Gateway authorizer event

        Returns:
            Token string

        Raises:
            ValueError: If no token provided
        """
        token = event.get("authorizationToken", "")
        if not token:
            headers = event.get("headers") or {}
            token = headers.get("authorization") or headers.get("Authorization", "")
            if not token:
                logger.warning(f"{LOG_TAG} Authorization header missing")
                raise ValueError("Unauthorized: No token provided")

        if token.startswith("Bearer "):
            token = token.replace("Bearer ", "")

        return token

    def verify_token(self, token: str) -> dict[str, Any]:
        """Verify Firebase ID token.

        Args:
            token: Firebase ID token

        Returns:
            Decoded token dictionary

        Raises:
            ValueError: If token is invalid or expired
        """
        try:
            return self.firebase_client.verify_id_token(token)
        except ValueError:
            raise
        except Exception as exc:
            logger.error(f"{LOG_TAG} Unexpected error verifying token: {exc}")
            raise ValueError("Token verification failed") from exc

    def generate_policy(
        self,
        is_authorized: bool,
        principal_id: str | None = None,
        context: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        """Generate API Gateway authorization policy.

        Args:
            is_authorized: Whether the request is authorized
            principal_id: User identifier (optional, defaults to "user" or "unauthorized")
            context: Additional context to pass to API Gateway

        Returns:
            Dict containing the authorization policy
        """
        if principal_id is None:
            principal_id = "user" if is_authorized else "unauthorized"
        policy = {
            "isAuthorized": is_authorized,
            "principalId": principal_id,
        }

        if context:
            policy["context"] = context

        return policy

    def generate_deny_policy(self) -> dict[str, Any]:
        """Generate deny policy for unauthorized access.

        Returns:
            Deny policy document
        """
        return self.generate_policy(
            is_authorized=False,
            principal_id="unauthorized"
        )

    def authorize(self, event: dict[str, Any]) -> dict[str, Any]:
        """Authorize request and generate IAM policy.

        Args:
            event: API Gateway authorizer event

        Returns:
            IAM policy document with user context
        """
        try:
            token = self.extract_token(event)
        except ValueError as extract_error:
            logger.error(f"{LOG_TAG} Error extracting token: {extract_error}")
            return self.generate_deny_policy()

        try:
            decoded_token = self.verify_token(token)
        except ValueError as verify_error:
            logger.error(f"{LOG_TAG} Error verifying token: {verify_error}")
            return self.generate_deny_policy()

        return _build_authorized_policy(self, decoded_token)


def _build_authorized_policy(service: AuthorizerService, decoded_token: dict[str, Any]) -> dict[str, Any]:
    """Build authorized policy from decoded token.

    Args:
        service: AuthorizerService instance
        decoded_token: Decoded Firebase token

    Returns:
        Authorization policy
    """
    user_info = _extract_user_info(decoded_token)
    email = user_info[TOKEN_EMAIL_KEY]

    if not email.endswith("@littio.co"):
        logger.warning(f"{LOG_TAG} User {email} is not from @littio.co domain")

    authorizer_context = _build_authorizer_context(user_info)
    firebase_uid = user_info["firebase_uid"]

    return service.generate_policy(
        is_authorized=True,
        principal_id=firebase_uid,
        context=authorizer_context
    )
