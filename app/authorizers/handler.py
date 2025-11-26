"""AWS API Gateway Lambda Authorizer handler."""

import logging
from typing import Any

from app.authorizers.authorizer_service import AuthorizerService

LOG_TAG = "AUTHORIZER"
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


def _build_deny_policy(method_arn: str) -> dict[str, Any]:
    """Build deny policy for unauthorized access.

    Args:
        method_arn: API Gateway method ARN

    Returns:
        Deny policy document
    """
    resource = method_arn.split("/")[:2]
    resource_arn = f"{'/'.join(resource)}/*/*" if len(resource) >= 2 else method_arn
    return {
        "principalId": "unauthorized",
        "policyDocument": {
            "Version": "2012-10-17",
            "Statement": [{
                "Effect": "Deny",
                "Action": "execute-api:Invoke",
                "Resource": resource_arn
            }]
        }
    }


def lambda_authorizer_handler(event: dict[str, Any], _context: Any) -> dict[str, Any]:
    """Lambda Authorizer handler for AWS API Gateway.

    This function verifies Firebase ID tokens and generates IAM policies
    to allow/deny access to API Gateway resources.

    Args:
        event: API Gateway authorizer event
        context: Lambda context

    Returns:
        IAM policy document with user context
    """
    authorizer_service = AuthorizerService()
    method_arn = event.get("methodArn", "")
    try:
        result = authorizer_service.authorize(event)
    except Exception as exc:
        logger.error(f"{LOG_TAG} Authorization failed for method: {method_arn}, error: {exc}", exc_info=True)
        return _build_deny_policy(method_arn)

    principal_id = result.get("principalId", "unknown")
    logger.info(f"{LOG_TAG} Authorization successful for principal: {principal_id}, method: {method_arn}")
    return result
