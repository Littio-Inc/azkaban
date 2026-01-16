"""MFA (Multi-Factor Authentication) middleware for sensitive operations."""

import logging
import os
from typing import Optional

from fastapi import Depends, Header, HTTPException, status

from app.common.enums import Environment
from app.mfa.service import TOTPService
from app.mfa.storage import TOTPStorage as TOTPStorageService
from app.middleware.auth import get_current_user

logger = logging.getLogger(__name__)

# Header name for TOTP code
TOTP_CODE_HEADER = "X-TOTP-Code"

# Development/staging environment names (frozenset to make it immutable)
DEV_STAGING_ENVS = frozenset((
    Environment.LOCAL.value,
    Environment.STAGING.value,
))

# Default values for function parameters (to avoid B008/WPS404)
_DEFAULT_CURRENT_USER = Depends(get_current_user)
_DEFAULT_TOTP_CODE_HEADER = Header(
    None,
    alias=TOTP_CODE_HEADER,
    description="TOTP code from Google Authenticator",
)


def _check_fixed_otp_code(totp_code: str, firebase_uid: str) -> bool:
    """Check if fixed OTP code is valid for development/staging.

    Args:
        totp_code: TOTP code to validate
        firebase_uid: Firebase user ID

    Returns:
        bool: True if fixed OTP code is valid, False otherwise
    """
    environment = os.getenv("ENVIRONMENT", "local")
    is_dev_or_staging = environment in DEV_STAGING_ENVS or environment.lower() in DEV_STAGING_ENVS

    if not is_dev_or_staging:
        return False

    fixed_otp_code = os.getenv("FIXED_OTP_CODE", "")
    if fixed_otp_code and totp_code == fixed_otp_code:
        logger.info(f"Using fixed OTP code for firebase_uid={firebase_uid} in development/staging")
        return True

    return False


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

    # Allow fixed OTP code in development/staging
    if not is_valid:
        is_valid = _check_fixed_otp_code(totp_code, firebase_uid)

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
