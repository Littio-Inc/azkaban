"""Authentication middleware for Firebase JWT validation."""

import logging
import traceback

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from firebase_admin import auth as firebase_auth

logger = logging.getLogger(__name__)


security = HTTPBearer(auto_error=False)


def _verify_firebase_token(token: str) -> dict:
    """Verify Firebase ID token.

    Args:
        token: Firebase ID token

    Returns:
        Decoded token dictionary

    Raises:
        HTTPException: If token is invalid or expired
    """
    try:
        decoded_token = firebase_auth.verify_id_token(token)
    except firebase_auth.InvalidIdTokenError as invalid_error:
        logger.warning("InvalidIdTokenError: %s", invalid_error)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido"
        )
    except firebase_auth.ExpiredIdTokenError as expired_error:
        logger.warning("ExpiredIdTokenError: %s", expired_error)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token expirado"
        )
    except Exception as verify_error:
        logger.error("Unexpected error verifying token: %s: %s", type(verify_error).__name__, verify_error)
        logger.error("Traceback: %s", traceback.format_exc())
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Error de autenticación: {str(verify_error)}"
        )
    return decoded_token


def _extract_user_from_token(decoded_token: dict) -> dict:
    """Extract user information from decoded token.

    Args:
        decoded_token: Decoded Firebase token

    Returns:
        User information dictionary
    """
    firebase_uid = decoded_token.get("uid")
    email = decoded_token.get("email", "")
    logger.debug("Token verified - firebase_uid: %s, email: %s", firebase_uid, email)

    # Verify that email is from authorized domain
    if not email.endswith("@littio.co"):
        logger.warning("Email %s not from @littio.co domain - RAISING 403", email)
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Solo se permiten emails @littio.co"
        )

    return {
        "firebase_uid": firebase_uid,
        "email": email,
        "name": decoded_token.get("name"),
        "picture": decoded_token.get("picture"),
    }


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(security)  # noqa: WPS404
) -> dict:
    """Get current user from Firebase ID Token.

    Args:
        credentials: HTTP Bearer token credentials

    Returns:
        dict: User information extracted from token

    Raises:
        HTTPException: If token is invalid or email is not authorized
    """
    logger.debug("get_current_user called")

    if not credentials:
        logger.warning("No credentials provided")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token de autenticación requerido",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = credentials.credentials
    token_length = len(token) if token else 0
    logger.debug("Token received, length: %s", token_length)

    try:
        decoded_token = _verify_firebase_token(token)
    except HTTPException:
        raise
    except Exception as auth_error:
        logger.error("Unexpected error: %s: %s", type(auth_error).__name__, auth_error)
        logger.error("Traceback: %s", traceback.format_exc())
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Error de autenticación: {str(auth_error)}"
        )

    user_info = _extract_user_from_token(decoded_token)
    logger.debug("Returning user info: %s", user_info)
    return user_info
