"""AWS Lambda handler for Azkaban authentication service."""

import logging
import os
from typing import Any

try:
    import unzip_requirements  # noqa: F401
except ImportError:
    # Lambda unzip_requirements is optional
    unzip_requirements = None

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from mangum import Mangum

# Initialize Firebase Admin SDK (only in production/Lambda)
# In local development, this will use environment variables
try:
    from app.common.config import firebase_admin  # noqa: F401
except ImportError:
    # Firebase config is optional for local dev
    firebase_admin = None

from app.routes.auth_routes import router as auth_router
from app.routes.basilisco_routes import router as basilisco_router
from app.routes.diagon_routes import router as diagon_router
from app.routes.permissions_routes import router as permissions_router
from app.routes.roles_routes import router as roles_router
from app.routes.users_routes import router as users_router

app = FastAPI(title="Azkaban - Authentication Service")

# Configure CORS - Must be added before routes
# Get allowed origins from environment or use defaults
environment = os.getenv("ENVIRONMENT", "local").lower()
cors_env = os.getenv("CORS_ALLOWED_ORIGINS", "")
allowed_origins = cors_env.split(",") if cors_env else []

# Add localhost origins for local and staging environments
localhost_origins = [
    "http://localhost:4321",
    "http://localhost:3000",
    "http://127.0.0.1:4321",
    "http://127.0.0.1:3000",
]

# Combine origins: add localhost for local/staging, keep only production origins for production
if environment in ["local", "staging"]:
    all_origins = [origin.strip() for origin in allowed_origins + localhost_origins if origin.strip()]
else:
    # Production: only use allowed_origins from environment (no localhost)
    all_origins = [origin.strip() for origin in allowed_origins if origin.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=all_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
    allow_headers=["*"],
    expose_headers=["*"],
)


@app.get("/health")
@app.head("/health")
def health():
    """Health check endpoint."""
    return {"message": "OK"}


# Include all routers - FastAPI will handle routing
app.include_router(auth_router, prefix="/v1/auth", tags=["Authentication"])
app.include_router(users_router, prefix="/v1/users", tags=["Users"])
app.include_router(roles_router, prefix="/v1/roles", tags=["Roles"])
app.include_router(permissions_router, prefix="/v1/permissions", tags=["Permissions"])
app.include_router(basilisco_router, prefix="/v1", tags=["Basilisco"])
app.include_router(diagon_router, prefix="/v1", tags=["Diagon"])

# Lambda handler
http_handler = Mangum(app)


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Log unhandled errors and return a generic response."""
    logging.getLogger(__name__).exception(
        "Unhandled exception while processing %s %s", request.method, request.url
    )
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "Internal server error"},
    )


def lambda_authorizer_handler(event: dict[str, Any], _context: Any) -> dict[str, Any]:  # noqa: WPS210
    """Lambda Authorizer handler for AWS API Gateway.

    This function verifies Firebase ID tokens and generates IAM policies
    to allow/deny access to API Gateway resources.

    Args:
        event: API Gateway authorizer event
        context: Lambda context

    Returns:
        IAM policy document with user context
    """
    from app.authorizers.handler import lambda_authorizer_handler as authorizer_handler  # noqa: WPS433

    return authorizer_handler(event, _context)
