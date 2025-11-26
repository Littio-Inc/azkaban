"""User management routes."""

import logging

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from app.middleware.admin import get_admin_user
from app.middleware.auth import get_current_user
from app.user.service import UserService

logger = logging.getLogger(__name__)

router = APIRouter()

# Constants
FIREBASE_UID_KEY = "firebase_uid"


class UpdateUserStatusRequest(BaseModel):
    """Request model for updating user status."""

    is_active: bool


class UpdateUserRoleRequest(BaseModel):
    """Request model for updating user role."""

    role: str


@router.post("/sync")
async def sync_user(
    current_user: dict = Depends(get_current_user)  # noqa: WPS404
):
    """Sync user from Firebase to database.

    Args:
        current_user: Current authenticated user from Firebase token

    Returns:
        dict: Synced user information
    """
    firebase_uid = current_user.get(FIREBASE_UID_KEY)
    email = current_user.get("email", "")
    name = current_user.get("name")
    picture = current_user.get("picture")

    # Create or update user in database
    user = UserService.create_or_update_user(
        firebase_uid=firebase_uid,
        email=email,
        name=name,
        picture=picture
    )

    return user


@router.get("/me")
async def get_current_user_info(
    current_user: dict = Depends(get_current_user)  # noqa: WPS404
):
    """Get current user information from database.

    Args:
        current_user: Current authenticated user

    Returns:
        dict: User information from database
    """
    firebase_uid = current_user.get(FIREBASE_UID_KEY)
    if not firebase_uid:
        return current_user

    # Get user from database to include role and is_active
    user_info = UserService.get_user_by_firebase_uid(firebase_uid)
    if user_info:
        return user_info

    # If user not in database, return Firebase info
    return current_user


@router.get("/me/permissions")
async def get_my_permissions(
    current_user: dict = Depends(get_current_user)  # noqa: WPS404
):
    """Get permissions for current user.

    Args:
        current_user: Current authenticated user

    Returns:
        dict: User permissions
    """
    # TODO: Implement permission retrieval from database
    return {"permissions": []}


@router.get("/")
async def list_users(
    skip: int = 0,
    limit: int = 100,
    admin_user: dict = Depends(get_admin_user)  # noqa: WPS404
):
    """List all users. Only admins can access this endpoint.

    Args:
        skip: Number of records to skip
        limit: Maximum number of records to return
        admin_user: Current authenticated admin user

    Returns:
        dict: List of users
    """
    logger.debug("list_users called, admin_user: %s", admin_user.get("email") if admin_user else "None")
    users = UserService.get_all_users(skip=skip, limit=limit)
    return {
        "users": users,
        "total": len(users),
        "skip": skip,
        "limit": limit,
    }


@router.patch("/{user_id}/status")
async def update_user_status(
    user_id: str,
    request: UpdateUserStatusRequest,
    admin_user: dict = Depends(get_admin_user)  # noqa: WPS404
):
    """Update user active status. Only admins can update user status.

    Args:
        user_id: User ID
        request: Request with new status
        admin_user: Current authenticated admin user

    Returns:
        dict: Updated user information

    Raises:
        HTTPException: If user not found
    """
    updated_user = UserService.update_user_status(user_id, request.is_active)
    if not updated_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuario no encontrado"
        )
    return updated_user


def _validate_role_update_permission(
    db_user: dict,
    target_user: dict,
    user_role: type
) -> None:
    """Validate if user has permission to update role.

    Args:
        db_user: Current user from database
        target_user: Target user to update
        user_role: UserRole enum class

    Raises:
        HTTPException: If user doesn't have permission
    """
    is_admin = db_user.get("role") == user_role.ADMIN.value
    is_self = (
        db_user.get("id") == target_user.get("id")
        or db_user.get(FIREBASE_UID_KEY) == target_user.get(FIREBASE_UID_KEY)
    )

    if not is_admin and not is_self:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes permisos para actualizar el rol de este usuario"
        )


@router.patch("/{user_id}/role")
async def update_user_role(
    user_id: str,
    request: UpdateUserRoleRequest,
    current_user: dict = Depends(get_current_user)  # noqa: WPS404
):
    """Update user role. Admins can update any user's role, users can only update their own role.

    Args:
        user_id: User ID
        request: Request with new role
        current_user: Current authenticated user

    Returns:
        dict: Updated user information

    Raises:
        HTTPException: If user not found, invalid role, or insufficient permissions
    """
    from app.common.enums import UserRole

    # Validate role
    if request.role not in [UserRole.ADMIN.value, UserRole.USER.value]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Rol inválido. Debe ser 'admin' o 'user'"
        )

    # Check permissions: user can only update their own role, admin can update any role
    firebase_uid = current_user.get(FIREBASE_UID_KEY)
    if not firebase_uid:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuario no autenticado"
        )

    # Get user from database to check if they're updating themselves
    db_user = UserService.get_user_by_firebase_uid(firebase_uid)
    if not db_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuario no encontrado en la base de datos"
        )

    # Get target user by ID
    target_user = UserService.get_user_by_id(user_id)
    if not target_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuario objetivo no encontrado"
        )

    # Check permissions
    _validate_role_update_permission(db_user, target_user, UserRole)

    # Use target_user's id for update
    target_user_id = target_user.get("id")
    if not target_user_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="ID de usuario no encontrado"
        )

    updated_user = UserService.update_user_role(target_user_id, request.role)
    if not updated_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuario no encontrado"
        )
    return updated_user
