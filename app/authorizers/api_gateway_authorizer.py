"""AWS API Gateway Lambda Authorizer for token verification."""

try:
    import unzip_requirements  # noqa: F401
except ImportError:
    unzip_requirements = None
else:
    _ = unzip_requirements

import logging
from typing import Any

from firebase_admin import auth as firebase_auth

logger = logging.getLogger(__name__)

# Constants for token keys
TOKEN_EMAIL_KEY = "email"
TOKEN_UID_KEY = "uid"
TOKEN_NAME_KEY = "name"
TOKEN_PICTURE_KEY = "picture"
CONTEXT_USER_ID_KEY = "user_id"
CONTEXT_EMAIL_KEY = "email"
CONTEXT_NAME_KEY = "name"
CONTEXT_PICTURE_KEY = "picture"


def generate_policy(
    principal_id: str,
    effect: str,
    resource: str,
    context: dict[str, Any] | None = None
) -> dict[str, Any]:
    """Generate IAM policy for API Gateway.

    Args:
        principal_id: User identifier
        effect: 'Allow' or 'Deny'
        resource: API Gateway resource ARN
        context: Additional context to pass to API Gateway

    Returns:
        IAM policy document
    """
    policy = {
        "principalId": principal_id,
        "policyDocument": {
            "Version": "2012-10-17",
            "Statement": [{
                "Effect": effect,
                "Action": "execute-api:Invoke",
                "Resource": resource
            }]
        }
    }

    if context:
        policy["context"] = context

    return policy


def _extract_token(event: dict[str, Any]) -> str:
    """Extract token from event.

    Args:
        event: API Gateway authorizer event

    Returns:
        Token string

    Raises:
        Exception: If no token provided
    """
    token = event.get("authorizationToken", "")
    if not token:
        raise Exception("Unauthorized: No token provided")
    if token.startswith("Bearer "):
        token = token.replace("Bearer ", "")
    return token


def _verify_token(token: str) -> dict[str, Any]:
    """Verify Firebase token.

    Args:
        token: Firebase ID token

    Returns:
        Decoded token dictionary

    Raises:
        Exception: If token is invalid or expired
    """
    try:
        decoded_token = firebase_auth.verify_id_token(token)
    except firebase_auth.InvalidIdTokenError:
        raise Exception("Unauthorized: Invalid token")
    except firebase_auth.ExpiredIdTokenError:
        raise Exception("Unauthorized: Token expired")
    return decoded_token


def _build_resource_arn(method_arn: str) -> str:
    """Build resource ARN pattern.

    Args:
        method_arn: Method ARN from event

    Returns:
        Resource ARN pattern
    """
    separator = "/"
    arn_parts = method_arn.split(separator)
    if len(arn_parts) >= 2:
        base_arn = separator.join(arn_parts[:2])
        resource = f"{base_arn}/*/*"
    else:
        resource = method_arn
    return resource


def _generate_deny_policy(event: dict[str, Any]) -> dict[str, Any]:
    """Generate deny policy for unauthorized access.

    Args:
        event: API Gateway authorizer event

    Returns:
        Deny policy document
    """
    method_arn = event.get("methodArn", "")
    resource = _build_resource_arn(method_arn)
    return generate_policy(
        principal_id="unauthorized",
        effect="Deny",
        resource=resource
    )


def _extract_user_info(decoded_token: dict[str, Any]) -> dict[str, str]:
    """Extract user information from decoded token.

    Args:
        decoded_token: Decoded Firebase token

    Returns:
        Dictionary with user information
    """
    return {
        TOKEN_EMAIL_KEY: decoded_token.get(TOKEN_EMAIL_KEY, ""),
        "firebase_uid": decoded_token.get(TOKEN_UID_KEY, ""),
        TOKEN_NAME_KEY: decoded_token.get(TOKEN_NAME_KEY, ""),
        TOKEN_PICTURE_KEY: decoded_token.get(TOKEN_PICTURE_KEY, ""),
    }


def _build_authorizer_context(user_info: dict[str, str]) -> dict[str, str]:
    """Build authorizer context from user info.

    Args:
        user_info: User information dictionary

    Returns:
        Authorizer context dictionary
    """
    firebase_uid = user_info["firebase_uid"]
    email = user_info[TOKEN_EMAIL_KEY]
    return {
        CONTEXT_USER_ID_KEY: firebase_uid,
        CONTEXT_EMAIL_KEY: email,
        CONTEXT_NAME_KEY: user_info[TOKEN_NAME_KEY] or "",
        CONTEXT_PICTURE_KEY: user_info[TOKEN_PICTURE_KEY] or "",
    }


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
    try:
        token = _extract_token(event)
    except Exception as extract_error:
        logger.error("Error extracting token: %s", extract_error)
        return _generate_deny_policy(event)

    try:
        decoded_token = _verify_token(token)
    except Exception as verify_error:
        logger.error("Error verifying token: %s", verify_error)
        return _generate_deny_policy(event)

    user_info = _extract_user_info(decoded_token)
    email = user_info[TOKEN_EMAIL_KEY]

    # Verify email domain (optional - can be done in Rules)
    if not email.endswith("@littio.co"):
        logger.warning("User %s is not from @littio.co domain", email)

    method_arn = event.get("methodArn", "")
    resource = _build_resource_arn(method_arn)
    authorizer_context = _build_authorizer_context(user_info)
    firebase_uid = user_info["firebase_uid"]

    policy = generate_policy(
        principal_id=firebase_uid,
        effect="Allow",
        resource=resource,
        context=authorizer_context
    )

    logger.info("Successfully authorized user %s (%s)", email, firebase_uid)
    return policy
