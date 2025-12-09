"""Basilisco API agent for handling REST requests."""

import logging
from typing import Any, Optional

from requests.exceptions import HTTPError

from app.common.apis.basilisco.errors import BasiliscoAPIClientError
from app.common.apis.rest_api_agent import MakeRequestParams, RESTfulAPIAgent
from app.common.errors import MissingCredentialsError
from app.common.secrets import get_secret

logger = logging.getLogger(__name__)

# Constants
BASILISCO_API_KEY = "BASILISCO_API_KEY"
BASILISCO_BASE_URL = "BASILISCO_BASE_URL"
BASE_TRANSACTIONS_PATH = "/v1/backoffice/transactions"


class BasiliscoAgent(RESTfulAPIAgent):
    """REST interface for the Basilisco API.

    This class handles REST requests to the Basilisco API, making sure to use a valid API key
    for every request.
    """

    _api_host: str
    _api_key: str
    _api_key_is_valid: bool

    def __init__(self) -> None:
        """Initialize Basilisco agent with API credentials."""
        # Fetch and validate credentials before calling super()
        api_host = get_secret(BASILISCO_BASE_URL)
        api_key = get_secret(BASILISCO_API_KEY)

        if not api_host:
            raise MissingCredentialsError("Missing credentials for Basilisco API.")
        if not api_key:
            raise MissingCredentialsError("Missing credentials for Basilisco API.")

        # Remove trailing slash from base URL
        api_host = api_host.rstrip("/")

        # Call super() with the real host_url
        super().__init__(
            client_class_name=self.__class__.__name__,
            host_url=api_host,
            max_retries=3,
        )

        # Assign instance attributes after super() initialization
        self._api_host = api_host
        self._api_key = api_key
        self._api_key_is_valid = False

        if len(self._api_key) > 10:
            start = self._api_key[:5]
            end = self._api_key[-5:]
            api_key_preview = f"{start}...{end}"
        else:
            api_key_preview = "***"
        logger.info("Basilisco API initialized with host: %s, key: %s", self._api_host, api_key_preview)

    def get(
        self,
        req_path: str,
        query_params: Optional[dict[str, Any]] = None,
    ) -> dict[str, Any]:
        """Make a GET request to the Basilisco API.

        Args:
            req_path: Request path (e.g., "/v1/backoffice/transactions")
            query_params: Optional query parameters

        Returns:
            Response data as dictionary

        Raises:
            BasiliscoAPIClientError: If API call fails
        """
        self._authenticate()
        params = MakeRequestParams(
            method="GET",
            path=req_path,
            query_params=query_params,
        )
        response = self._make_request_with_error_handling(params)
        return response.json()

    def post(
        self,
        req_path: str,
        json: Optional[dict[str, Any]] = None,
    ) -> dict[str, Any]:
        """Make a POST request to the Basilisco API.

        Args:
            req_path: Request path (e.g., "/v1/backoffice/transactions")
            json: Optional JSON body

        Returns:
            Response data as dictionary

        Raises:
            BasiliscoAPIClientError: If API call fails
        """
        self._authenticate()
        params = MakeRequestParams(
            method="POST",
            path=req_path,
            body=json,
        )
        response = self._make_request_with_error_handling(params)
        return response.json()

    def _authenticate(self) -> None:
        """Set the API key in the headers for authentication.

        This implementation sets the API key header once and marks it as valid
        to avoid redundant header updates.
        """
        if self._api_key_is_valid:
            return

        logger.info("Setting up Basilisco API key in headers...")
        self.update_headers({"x-api-key": self._api_key, "Content-Type": "application/json"})
        self._api_key_is_valid = True
        logger.info("Basilisco API headers set successfully")

    def _make_request_with_error_handling(self, params: MakeRequestParams):
        """Make request and handle errors.

        Args:
            params: Request parameters

        Returns:
            Response object

        Raises:
            BasiliscoAPIClientError: If API call fails
        """
        try:
            return self.make_request(params)
        except HTTPError as http_exception:
            raise BasiliscoAPIClientError(f"Error calling Basilisco API: {http_exception}") from http_exception
        except Exception as error:  # noqa: BLE001
            raise BasiliscoAPIClientError(f"Unexpected error calling Basilisco API: {str(error)}") from error
