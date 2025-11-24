"""Local authorizer for development (simulates API Gateway authorizer)."""

from typing import Any

from fastapi import Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.middleware.auth import get_current_user


security = HTTPBearer()


async def verify_token_local(request: Request) -> dict[str, Any]:
    """Verify token locally (for development).

    This simulates what the API Gateway authorizer does,
    but runs as a FastAPI middleware instead.

    Args:
        request: FastAPI request

    Returns:
        User information dictionary
    """
    # Use existing auth middleware
    credentials: HTTPAuthorizationCredentials = await security(request)
    user = get_current_user(credentials)
    return user
