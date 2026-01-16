"""MFA (Multi-Factor Authentication) middleware for sensitive operations."""

import logging
from typing import Optional

from fastapi import Depends, Header, HTTPException, status

from app.mfa.service import TOTPService
from app.mfa.storage import TOTPStorage as TOTPStorageService
from app.middleware.auth import get_current_user

logger = logging.getLogger(__name__)

# Header name for TOTP code
TOTP_CODE_HEADER = "X-TOTP-Code"

# Default values for function parameters (to avoid B008/WPS404)
_DEFAULT_CURRENT_USER = Depends(get_current_user)
_DEFAULT_TOTP_CODE_HEADER = Header(
    None,
    alias=TOTP_CODE_HEADER,
    description="TOTP code from Google Authenticator",
)


def require_mfa_verification(
    current_user: dict = _DEFAULT_CURRENT_USER,
    totp_code: Optional[str] = _DEFAULT_TOTP_CODE_HEADER,
) -> dict:
    """Require MFA verification for sensitive operations.

    This dependency validates that:
    1. User has MFA (TOTP) configured
    2. A valid TOTP code is provided in the request header

    Args:
        current_user: Current authenticated user from Firebase token
        totp_code: TOTP code from Google Authenticator (6 digits)

    Returns:
        dict: User information with MFA verification confirmed

    Raises:
        HTTPException: If MFA is not configured or code is invalid
    """
    firebase_uid = current_user.get("firebase_uid")
    logger.info(f"Validating MFA for firebase_uid={firebase_uid}")

    # Check if MFA is configured
    secret = TOTPStorageService.get_secret(firebase_uid)
    if not secret:
        logger.warning(f"MFA not configured for firebase_uid={firebase_uid}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=(
                "MFA (Multi-Factor Authentication) no está configurado. "
                "Por favor, configura MFA primero."
            ),
        )

    # Require TOTP code in header
    if not totp_code:
        logger.warning(f"TOTP code missing for firebase_uid={firebase_uid}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                "Código TOTP requerido. Por favor, proporciona el código de "
                "Google Authenticator en el header X-TOTP-Code."
            ),
        )

    # Validate TOTP code
    is_valid = TOTPService.verify_totp(secret, totp_code)

    if not is_valid:
        logger.warning(f"Invalid TOTP code for firebase_uid={firebase_uid}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                "Código TOTP inválido. Asegúrate de usar el código más reciente "
                "de Google Authenticator."
            ),
        )

    logger.info(f"MFA verified successfully for firebase_uid={firebase_uid}")
    return current_user
