"""Admin middleware for checking admin permissions."""

import logging

from fastapi import Depends, HTTPException, status

from app.common.enums import UserRole
from app.middleware.auth import get_current_user
from app.user.service import UserService

logger = logging.getLogger(__name__)


def _check_special_admin_email(email: str) -> dict | None:
    """Check if email is special admin email.

    Args:
        email: User email

    Returns:
        User dict if admin, None otherwise
    """
    special_email = "mauricio.quinche@littio.co"
    if email != special_email:
        return None

    logger.debug("Special case: %s, checking by email", special_email)
    db_user = UserService.get_user_by_email(email)
    role = db_user.get("role") if db_user else "None"
    logger.debug("db_user found: %s, role: %s", db_user is not None, role)
    if db_user and db_user.get("role") == UserRole.ADMIN.value:
        logger.debug("User is admin by email, allowing access")
        return db_user
    logger.warning("User not found or not admin in database")
    return None


def get_admin_user(
    current_user: dict = Depends(get_current_user)  # noqa: WPS404
) -> dict:
    """Get current user and verify admin permissions.

    Args:
        current_user: Current authenticated user from get_current_user

    Returns:
        dict: User information with admin verification

    Raises:
        HTTPException: If user is not admin
    """
    logger.debug("get_admin_user called, current_user keys: %s", list(current_user.keys()))
    firebase_uid = current_user.get("firebase_uid")
    email = current_user.get("email", "")
    logger.debug("firebase_uid: %s, email: %s", firebase_uid, email)

    if not firebase_uid:
        logger.warning("No firebase_uid found, raising 401")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuario no autenticado"
        )

    # Check if user is admin
    logger.debug("Calling UserService.is_admin(%s)", firebase_uid)
    is_admin = UserService.is_admin(firebase_uid)
    logger.debug("is_admin result: %s", is_admin)

    if not is_admin:
        special_admin = _check_special_admin_email(email)
        if special_admin:
            return special_admin
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes permisos de administrador"
        )

    # Get full user info from database
    user_info = UserService.get_user_by_firebase_uid(firebase_uid)
    if not user_info:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuario no encontrado en la base de datos"
        )

    return user_info
