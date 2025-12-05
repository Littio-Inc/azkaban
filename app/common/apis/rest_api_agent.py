"""RESTful API agent for making HTTP requests with retry mechanism."""

from dataclasses import dataclass
from json import dumps as json_dumps
import logging
from typing import Any

from requests.adapters import HTTPAdapter
from requests.exceptions import HTTPError, RequestException
from requests.models import Response
from requests.sessions import Session
from urllib3.util.retry import Retry

logger = logging.getLogger(__name__)

ERROR_COMMON_MESSAGE = "provider (%s) in %s %s: %s"


@dataclass
class MakeRequestParams:
    """Parameters for making an API request."""

    method: str
    path: str
    body: dict[str, Any] | None = None
    headers: dict[str, Any] | None = None
    data: Any | None = None
    query_params: dict[str, Any] | None = None


class RESTfulAPIAgent:
    """Abstraction of a RESTful API in requests library with logging and retry mechanism."""

    _client_class_name: str
    _session: Session
    _host_url: str

    def __init__(self, client_class_name: str, host_url: str, max_retries: int) -> None:
        """Initialize RESTful API agent.

        Args:
            client_class_name: Name of the client class for logging
            host_url: Base URL for the API
            max_retries: Maximum number of retries for failed requests
        """
        self._client_class_name = client_class_name
        self._session = Session()
        self._host_url = host_url
        if max_retries > 0:
            retry = Retry(
                total=max_retries,
                read=max_retries,
                connect=max_retries,
                backoff_factor=0.3,
                status_forcelist=(500, 502, 504),
            )
            adapter = HTTPAdapter(max_retries=retry)
            self._session.mount("http://", adapter)
            self._session.mount("https://", adapter)

    def make_request(self, params: MakeRequestParams) -> Response:
        """Make an HTTP request to the external API.

        Args:
            params: Parameters for the request, including method, path, body, headers and data.

        Returns:
            The HTTP response from the external API.

        Raises:
            RequestException: If there is an error during the request.
            HTTPError: If the HTTP response status code is not in the 2xx or 3xx range.
        """
        try:
            response = self._session.request(
                method=params.method,
                url=self._host_url + params.path,
                json=params.body,
                headers=params.headers,
                data=params.data,
                params=params.query_params,
                timeout=30,
            )
        except RequestException as request_exception:
            logger.info(
                "Error request from " + ERROR_COMMON_MESSAGE,
                self._client_class_name,
                params.method,
                params.path,
                request_exception,
                exc_info=request_exception,
            )
            raise
        self._log_request(params)
        self._log_response(params.method, params.path, response)
        try:
            response.raise_for_status()
        except HTTPError as http_exception:
            logger.info(
                "Error response from " + ERROR_COMMON_MESSAGE,
                self._client_class_name,
                params.method,
                params.path,
                http_exception,
                exc_info=http_exception,
            )
            raise
        return response

    def update_headers(self, headers: dict[str, Any]) -> None:
        """Update the headers of the session.

        Args:
            headers: Headers to be added to the session.
        """
        self._session.headers.update(headers)

    def update_query_params(self, query_params: dict[str, Any]) -> None:
        """Update the query parameters of the session.

        Args:
            query_params: Query parameters to be added to the session.
        """
        self._session.params.update(query_params)

    def _log_request(
        self,
        params: MakeRequestParams,
    ) -> None:
        """Log request details.

        Args:
            params: Request parameters to log.
        """
        request_object = {
            "body": params.body or params.data,
            "query_params": params.query_params,
            "headers": params.headers,
        }
        request_log_data = json_dumps(request_object)
        logger.info(
            "Request to " + ERROR_COMMON_MESSAGE,
            self._client_class_name,
            params.method,
            params.path,
            request_log_data,
        )

    def _log_response(
        self,
        method: str,
        req_path: str,
        response: Response,
    ) -> None:
        """Log response details.

        Args:
            method: HTTP method used.
            req_path: Request path.
            response: Response object to log.
        """
        response_object = {
            "status_code": response.status_code,
            "body": response.text,
            "headers": dict(response.headers),
        }
        response_log_data = json_dumps(response_object)
        logger.info(
            "Response from " + ERROR_COMMON_MESSAGE,
            self._client_class_name,
            method,
            req_path,
            response_log_data,
        )
