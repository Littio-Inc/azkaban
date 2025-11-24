"""User management routes."""

import logging

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from app.middleware.admin import get_admin_user
from app.middleware.auth import get_current_user
from app.user.service import UserService

logger = logging.getLogger(__name__)

router = APIRouter()


class UpdateUserStatusRequest(BaseModel):
    """Request model for updating user status."""

    is_active: bool


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
    firebase_uid = current_user.get("firebase_uid")
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
    firebase_uid = current_user.get("firebase_uid")
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
