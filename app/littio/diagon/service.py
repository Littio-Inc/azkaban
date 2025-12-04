"""Diagon service for managing external API calls."""

import logging
from typing import Any

import httpx

from app.common.secrets import get_secret

logger = logging.getLogger(__name__)

# Constants
DIAGON_API_KEY = "DIAGON_API_KEY"
DIAGON_BASE_URL = "DIAGON_BASE_URL"
DEFAULT_TIMEOUT = 30.0


class DiagonService:
    """Service for interacting with Diagon API."""

    @staticmethod
    def get_accounts() -> list[dict[str, Any]]:
        """Get accounts from Diagon API.

        Returns:
            List of account dictionaries containing account information and assets

        Raises:
            httpx.HTTPStatusError: If API request fails
            ValueError: If API key or base URL is not found
        """
        url = DiagonService._build_url()
        headers = DiagonService._build_headers()

        logger.info("Calling Diagon API: %s", url)

        try:
            with httpx.Client(timeout=DEFAULT_TIMEOUT) as client:
                response = client.get(url, headers=headers)
                response.raise_for_status()
                return response.json()
        except httpx.HTTPStatusError as http_error:
            logger.error(
                "Diagon API error: %s - %s",
                http_error.response.status_code,
                http_error.response.text
            )
            raise
        except httpx.RequestError as request_error:
            logger.error("Diagon API request error: %s", request_error)
            raise
        except Exception as exc:
            logger.error("Unexpected error calling Diagon API: %s", exc)
            raise

    @staticmethod
    def _get_base_url() -> str:
        """Get Diagon base URL from secrets.

        Returns:
            Diagon base URL

        Raises:
            ValueError: If base URL is not found
        """
        base_url = get_secret(DIAGON_BASE_URL)
        if not base_url:
            raise ValueError("DIAGON_BASE_URL not found in secrets")
        return base_url.rstrip("/")

    @staticmethod
    def _get_api_key() -> str:
        """Get Diagon API key from secrets.

        Returns:
            Diagon API key

        Raises:
            ValueError: If API key is not found
        """
        api_key = get_secret(DIAGON_API_KEY)
        if not api_key:
            raise ValueError("DIAGON_API_KEY not found in secrets")
        return api_key

    @staticmethod
    def _build_url() -> str:
        """Build the full API URL.

        Returns:
            Complete API URL

        Raises:
            ValueError: If base URL is not found
        """
        base_url = DiagonService._get_base_url()
        return f"{base_url}/vault/accounts"

    @staticmethod
    def _build_headers() -> dict[str, str]:
        """Build request headers.

        Returns:
            Dictionary with request headers

        Raises:
            ValueError: If API key is not found
        """
        api_key = DiagonService._get_api_key()
        return {"X-API-KEY": api_key}
