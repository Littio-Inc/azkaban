"""Role management routes."""

from fastapi import APIRouter, Depends

from app.middleware.auth import get_current_user

router = APIRouter()


@router.get("/")
async def list_roles(
    current_user: dict = Depends(get_current_user)  # noqa: WPS404
):
    """List all available roles.

    Args:
        current_user: Current authenticated user

    Returns:
        dict: List of roles
    """
    # TODO: Implement role listing from database
    return {"roles": []}
