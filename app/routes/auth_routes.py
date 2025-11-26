"""Authentication routes."""

import logging
import os

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from app.common.enums import Environment
from app.mfa.service import TOTPService
from app.mfa.storage import TOTPStorage as TOTPStorageService
from app.middleware.auth import get_current_user

router = APIRouter()


class SetupTOTPRequest(BaseModel):
    """Setup TOTP request model."""

    # No additional data needed, uses authenticated user


class VerifyTOTPRequest(BaseModel):
    """Verify TOTP request model."""

    totp_code: str


logger = logging.getLogger(__name__)


# Constants for response keys
RESPONSE_MESSAGE_KEY = "message"
FIREBASE_UID_KEY = "firebase_uid"


@router.post("/login")
async def login():
    """Login endpoint (handled by frontend with Firebase)."""
    login_message = "Login handled by frontend with Firebase"
    return {RESPONSE_MESSAGE_KEY: login_message}


@router.post("/verify")
async def verify_token():
    """Verify token endpoint."""
    verify_message = "Token verification"
    return {RESPONSE_MESSAGE_KEY: verify_message}


def _check_totp_already_setup(firebase_uid: str) -> None:
    """Check if TOTP is already set up for user.

    Args:
        firebase_uid: Firebase user ID

    Raises:
        HTTPException: If TOTP is already configured
    """
    existing_secret = TOTPStorageService.get_secret(firebase_uid)
    if existing_secret and TOTPStorageService.is_verified(firebase_uid):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="TOTP ya está configurado para este usuario"
        )


def _is_dev_or_staging() -> bool:
    """Check if environment is development or staging.

    Returns:
        True if dev or staging, False otherwise
    """
    environment = os.getenv("ENVIRONMENT", Environment.LOCAL.value)
    return environment in [Environment.LOCAL.value, "dev", Environment.STAGING.value]


def _generate_totp_setup_response(secret: str, qr_code: str, is_dev_or_staging: bool) -> dict:
    """Generate TOTP setup response.

    Args:
        secret: TOTP secret
        qr_code: QR code string
        is_dev_or_staging: Whether environment is dev or staging

    Returns:
        Response dictionary
    """
    return {
        "qr_code": qr_code,
        "secret": secret if is_dev_or_staging else None,
        "manual_entry_key": secret,
        RESPONSE_MESSAGE_KEY: "Escanea el código QR con Google Authenticator o ingresa la clave manualmente",
    }


@router.post("/setup-totp")
async def setup_totp(  # noqa: WPS210
    current_user: dict = Depends(get_current_user)  # noqa: WPS404
):
    """Setup TOTP (Google Authenticator) for user.

    Args:
        current_user: Current authenticated user from Firebase token

    Returns:
        dict: QR code and setup information
    """
    firebase_uid = current_user.get(FIREBASE_UID_KEY)
    email = current_user.get("email", "")

    log_start = f"Starting TOTP setup for firebase_uid={firebase_uid} email={email}"
    logger.info(log_start)
    try:
        response = _build_totp_setup_response(firebase_uid, email)
    except Exception:
        log_error = f"Error during TOTP setup for firebase_uid={firebase_uid}"
        logger.exception(log_error)
        raise
    else:
        log_success = f"TOTP setup response generated for firebase_uid={firebase_uid}"
        logger.info(log_success)
        return response


def _build_totp_setup_response(firebase_uid: str, email: str) -> dict:
    """Build the TOTP response dictionary."""
    _check_totp_already_setup(firebase_uid)
    secret = TOTPService.generate_secret()
    TOTPStorageService.store_secret(firebase_uid, secret)
    totp_uri = TOTPService.get_totp_uri(secret, email)
    qr_code = TOTPService.generate_qr_code(totp_uri)
    is_dev_or_staging = _is_dev_or_staging()
    return _generate_totp_setup_response(secret, qr_code, is_dev_or_staging)


@router.post("/verify-totp")
async def verify_totp(
    request: VerifyTOTPRequest,
    current_user: dict = Depends(get_current_user)  # noqa: WPS404
):
    """Verify TOTP code from Google Authenticator.

    Args:
        request: Request containing TOTP code
        current_user: Current authenticated user from Firebase token

    Returns:
        dict: Verification result
    """
    firebase_uid = current_user.get(FIREBASE_UID_KEY)
    logger.info(f"Verifying TOTP code for firebase_uid={firebase_uid}")

    # Get user's TOTP secret
    secret = TOTPStorageService.get_secret(firebase_uid)
    if not secret:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="TOTP no está configurado. Por favor, configura TOTP primero."
        )

    # Verify TOTP code
    is_valid = TOTPService.verify_totp(secret, request.totp_code)
    if not is_valid and _is_dev_or_staging():
        fixed_otp_code = os.getenv("FIXED_OTP_CODE", "")
        if fixed_otp_code and request.totp_code == fixed_otp_code:
            logger.info(f"Using fixed OTP code for firebase_uid={firebase_uid} in development")
            is_valid = True

    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Código TOTP inválido. Asegúrate de usar el código más reciente de Google Authenticator."
        )

    logger.info(f"TOTP code valid for firebase_uid={firebase_uid}, marking verified")
    if not TOTPStorageService.is_verified(firebase_uid):
        TOTPStorageService.mark_verified(firebase_uid)

    return {
        "verified": True,
        "message": "TOTP verificado correctamente",
        "access_token": "totp-verified-token",  # In production, generate proper session token
    }


@router.get("/totp-status")
async def get_totp_status(
    current_user: dict = Depends(get_current_user)  # noqa: WPS404
):
    """Get TOTP setup status for user.

    Args:
        current_user: Current authenticated user from Firebase token

    Returns:
        dict: TOTP status information
    """
    firebase_uid = current_user.get(FIREBASE_UID_KEY)
    secret = TOTPStorageService.get_secret(firebase_uid)
    is_verified = TOTPStorageService.is_verified(firebase_uid) if secret else False

    return {
        "is_configured": secret is not None,
        "is_verified": is_verified,
    }


class GetCurrentTOTPRequest(BaseModel):
    """Get current TOTP code request (development only)."""

    secret: str


@router.post("/get-current-totp")
async def get_current_totp(
    request: GetCurrentTOTPRequest,
    current_user: dict = Depends(get_current_user)  # noqa: WPS404
):
    """Get current TOTP code (development only).

    Args:
        request: Request containing secret
        current_user: Current authenticated user from Firebase token

    Returns:
        dict: Current TOTP code
    """
    # Only allow in development/staging
    environment = os.getenv("ENVIRONMENT", Environment.LOCAL.value)
    if environment not in [Environment.LOCAL.value, "dev", Environment.STAGING.value]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This endpoint is only available in development"
        )

    firebase_uid = current_user.get(FIREBASE_UID_KEY)
    stored_secret = TOTPStorageService.get_secret(firebase_uid)

    # Verify secret matches
    if stored_secret != request.secret:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Secret does not match"
        )

    current_code = TOTPService.get_current_totp(request.secret)

    return {
        "totp_code": current_code,
    }
