"""Cassandra API agent for handling REST requests."""

import logging
from typing import Any, Optional

from requests.exceptions import HTTPError

from app.common.apis.cassandra.errors import CassandraAPIClientError
from app.common.apis.rest_api_agent import MakeRequestParams, RESTfulAPIAgent
from app.common.errors import MissingCredentialsError
from app.common.secrets import get_secret

logger = logging.getLogger(__name__)

# Constants
BASE_PAYOUTS_PATH = "/v2/payouts/account"


class CassandraAgent(RESTfulAPIAgent):
    """REST interface for the Cassandra API.

    This class handles REST requests to the Cassandra API, making sure to use a valid API key
    for every request.
    """

    _api_host: str
    _api_key: str
    _api_key_is_valid: bool

    def __init__(self) -> None:
        """Initialize Cassandra agent with API credentials."""
        # Fetch and validate credentials before calling super()
        api_host = get_secret("CASSANDRA_API_URL")
        api_key = get_secret("CASSANDRA_API_KEY")

        if not api_host:
            raise MissingCredentialsError("Missing credentials for Cassandra API.")
        if not api_key:
            raise MissingCredentialsError("Missing credentials for Cassandra API.")

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
        logger.info("Cassandra API initialized with host: %s, key: %s", self._api_host, api_key_preview)

    def get(
        self,
        req_path: str,
        query_params: Optional[dict[str, Any]] = None,
    ) -> dict[str, Any]:
        """Make a GET request to the Cassandra API.

        Args:
            req_path: Request path (e.g., "/v2/payouts/account/transfer/quote")
            query_params: Optional query parameters

        Returns:
            Response data as dictionary

        Raises:
            CassandraAPIClientError: If API call fails
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
        """Make a POST request to the Cassandra API.

        Args:
            req_path: Request path (e.g., "/v2/payouts/account/transfer/payout")
            json: Optional JSON body

        Returns:
            Response data as dictionary

        Raises:
            CassandraAPIClientError: If API call fails
        """
        self._authenticate()
        params = MakeRequestParams(
            method="POST",
            path=req_path,
            body=json,
        )
        response = self._make_request_with_error_handling(params)
        return response.json()

    def put(
        self,
        req_path: str,
        json: Optional[dict[str, Any]] = None,
    ) -> dict[str, Any]:
        """Make a PUT request to the Cassandra API.

        Args:
            req_path: Request path (e.g., "/v1/blockchain-wallets/{id}")
            json: Optional JSON body

        Returns:
            Response data as dictionary

        Raises:
            CassandraAPIClientError: If API call fails
        """
        self._authenticate()
        params = MakeRequestParams(
            method="PUT",
            path=req_path,
            body=json,
        )
        response = self._make_request_with_error_handling(params)
        return response.json()

    def delete(
        self,
        req_path: str,
    ) -> None:
        """Make a DELETE request to the Cassandra API.

        Args:
            req_path: Request path (e.g., "/v1/blockchain-wallets/{id}")

        Raises:
            CassandraAPIClientError: If API call fails
        """
        self._authenticate()
        params = MakeRequestParams(
            method="DELETE",
            path=req_path,
        )
        response = self._make_request_with_error_handling(params)
        # DELETE requests may return 204 No Content, so we don't try to parse JSON
        if response.status_code == 204:
            return
        # If there's content, we could parse it, but for now we just return None

    def _authenticate(self) -> None:
        """Set the API key in the headers for authentication.

        This implementation sets the API key header once and marks it as valid
        to avoid redundant header updates.
        """
        if self._api_key_is_valid:
            return

        logger.info("Setting up Cassandra API key in headers...")
        self.update_headers({"x-api-key": self._api_key})
        self._api_key_is_valid = True
        logger.info("Cassandra API headers set successfully")

    def _make_request_with_error_handling(self, params: MakeRequestParams):
        """Make request and handle errors.

        Args:
            params: Request parameters

        Returns:
            Response object

        Raises:
            CassandraAPIClientError: If API call fails
        """
        try:
            return self.make_request(params)
        except HTTPError as http_exception:
            status_code, error_detail = self._extract_error_details(http_exception)
            error_message = f"Error calling Cassandra API: {http_exception}"
            raise CassandraAPIClientError(
                error_message,
                status_code=status_code,
                error_detail=error_detail,
            ) from http_exception
        except Exception as error:  # noqa: BLE001
            error_message = f"Unexpected error calling Cassandra API: {error}"
            raise CassandraAPIClientError(error_message) from error

    def _extract_error_details(self, http_exception: HTTPError) -> tuple[int | None, dict | None]:
        """Extract status code and error detail from HTTP exception.

        Args:
            http_exception: HTTP exception from API call

        Returns:
            tuple[int | None, dict | None]: Status code and error detail
        """
        if not hasattr(http_exception, "response") or http_exception.response is None:
            return None, None

        status_code = http_exception.response.status_code
        try:
            error_detail = http_exception.response.json()
        except Exception:  # noqa: BLE001
            # If response is not JSON, use text
            error_detail = {"message": http_exception.response.text}

        return status_code, error_detail
