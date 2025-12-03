"""Basilisco service for managing external API calls."""

import logging
from typing import Any

import httpx

from app.common.secrets import get_secret

logger = logging.getLogger(__name__)

# Constants
BASILISCO_API_KEY = "BASILISCO_API_KEY"
BASILISCO_BASE_URL = "BASILISCO_BASE_URL"
DEFAULT_TIMEOUT = 30.0


class BasiliscoService:
    """Service for interacting with Basilisco API."""

    @staticmethod
    def get_transactions(
        provider: str | None = None,
        page: int = 1,
        limit: int = 10
    ) -> dict[str, Any]:
        """Get transactions from Basilisco API.

        Args:
            provider: Transaction provider filter (e.g., 'fireblocks')
            page: Page number (default: 1)
            limit: Number of results per page (default: 10)

        Returns:
            Dictionary containing transactions and pagination info

        Raises:
            httpx.HTTPStatusError: If API request fails
            ValueError: If API key or base URL is not found
        """
        url = BasiliscoService._build_url()
        headers = BasiliscoService._build_headers()
        params = BasiliscoService._build_request_params(provider, page, limit)

        logger.info(
            "Calling Basilisco API: %s with params: %s",
            url,
            params
        )

        try:
            with httpx.Client(timeout=DEFAULT_TIMEOUT) as client:
                response = client.get(url, headers=headers, params=params)
                response.raise_for_status()
                return response.json()
        except httpx.HTTPStatusError as http_error:
            logger.error(
                "Basilisco API error: %s - %s",
                http_error.response.status_code,
                http_error.response.text
            )
            raise
        except httpx.RequestError as request_error:
            logger.error("Basilisco API request error: %s", request_error)
            raise
        except Exception as exc:
            logger.error("Unexpected error calling Basilisco API: %s", exc)
            raise

    @staticmethod
    def _get_base_url() -> str:
        """Get Basilisco base URL from secrets.

        Returns:
            Basilisco base URL

        Raises:
            ValueError: If base URL is not found
        """
        base_url = get_secret(BASILISCO_BASE_URL)
        if not base_url:
            raise ValueError("BASILISCO_BASE_URL not found in secrets")
        return base_url.rstrip("/")

    @staticmethod
    def _get_api_key() -> str:
        """Get Basilisco API key from secrets.

        Returns:
            Basilisco API key

        Raises:
            ValueError: If API key is not found
        """
        api_key = get_secret(BASILISCO_API_KEY)
        if not api_key:
            raise ValueError("BASILISCO_API_KEY not found in secrets")
        return api_key

    @staticmethod
    def _build_url() -> str:
        """Build the full API URL.

        Returns:
            Complete API URL

        Raises:
            ValueError: If base URL is not found
        """
        base_url = BasiliscoService._get_base_url()
        return f"{base_url}/v1/backoffice/transactions"

    @staticmethod
    def _build_headers() -> dict[str, str]:
        """Build request headers.

        Returns:
            Dictionary with request headers

        Raises:
            ValueError: If API key is not found
        """
        api_key = BasiliscoService._get_api_key()
        return {"x-api-key": api_key}

    @staticmethod
    def _build_request_params(provider: str | None, page: int, limit: int) -> dict[str, Any]:
        """Build query parameters for API request.

        Args:
            provider: Transaction provider filter
            page: Page number
            limit: Number of results per page

        Returns:
            Dictionary with query parameters
        """
        params: dict[str, Any] = {
            "page": page,
            "limit": limit,
        }
        if provider:
            params["provider"] = provider
        return params
