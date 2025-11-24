"""Permission management routes."""

from fastapi import APIRouter, Depends

from app.middleware.auth import get_current_user

router = APIRouter()


@router.get("/")
async def list_permissions(
    current_user: dict = Depends(get_current_user)  # noqa: WPS404
):
    """List all available permissions.

    Args:
        current_user: Current authenticated user

    Returns:
        dict: List of permissions
    """
    # TODO: Implement permission listing from database
    return {"permissions": []}
