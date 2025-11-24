"""Secrets management for Azkaban service."""

import json
import os

from app.common.enums import Environment

# boto3 is optional - only needed for AWS Secrets Manager
try:
    import boto3
except ImportError:
    boto3 = None  # type: ignore


secrets = {}


def get_secret(name: str) -> str | None:
    """Retrieves a secret value based on the current environment.

    For LOCAL and TESTING environments, it reads the secret from environment variables.
    For other environments, it fetches secrets from AWS Secrets Manager,
    caching them globally for subsequent calls.

    Args:
        name: The name of the secret to retrieve.

    Returns:
        The secret value as a string, or None if not found.
    """
    environment = os.environ.get("ENVIRONMENT", Environment.LOCAL.value)
    if environment in {Environment.LOCAL.value, Environment.TESTING.value}:
        return os.environ.get(name)

    global secrets  # noqa: WPS420
    if not secrets:
        secret_arn = os.environ.get("SECRET_MANAGER_AZKABAN_ARN")
        if not secret_arn:
            # Fallback to environment variables if ARN not set
            return os.environ.get(name)

        if boto3 is None:
            # boto3 not available, fallback to environment variables
            return os.environ.get(name)

        client = boto3.client("secretsmanager")
        secrets_value = client.get_secret_value(
            SecretId=secret_arn,
        )
        secrets = json.loads(secrets_value.get("SecretString"))  # noqa: WPS442

    return secrets.get(name)
