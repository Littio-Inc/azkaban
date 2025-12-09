"""Tests for RESTful API agent."""

import unittest
from unittest.mock import MagicMock, patch

from requests.exceptions import HTTPError, RequestException
from requests.models import Response

from app.common.apis.rest_api_agent import MakeRequestParams, RESTfulAPIAgent

# Test constants
CLIENT_NAME = "TestClient"
HOST_URL = "https://api.example.com"
MAX_RETRIES = 3


class TestRESTfulAPIAgent(unittest.TestCase):
    """Test cases for RESTfulAPIAgent."""

    def test_init_with_retries(self):
        """Test initialization with retries enabled."""
        agent = RESTfulAPIAgent(CLIENT_NAME, HOST_URL, MAX_RETRIES)

        self.assertEqual(agent._client_class_name, CLIENT_NAME)
        self.assertEqual(agent._host_url, HOST_URL)
        self.assertIsNotNone(agent._session)

    def test_init_without_retries(self):
        """Test initialization with retries disabled."""
        agent = RESTfulAPIAgent(CLIENT_NAME, HOST_URL, 0)

        self.assertEqual(agent._client_class_name, CLIENT_NAME)
        self.assertEqual(agent._host_url, HOST_URL)

    @patch("app.common.apis.rest_api_agent.logger")
    def test_make_request_success(self, _mock_logger):
        """Test successful request."""
        agent = RESTfulAPIAgent(CLIENT_NAME, HOST_URL, MAX_RETRIES)
        mock_response = MagicMock(spec=Response)
        mock_response.status_code = 200
        mock_response.text = '{"result": "success"}'
        mock_response.headers = {}
        mock_response.raise_for_status = MagicMock()

        with patch.object(agent._session, "request", return_value=mock_response):
            params = MakeRequestParams(
                method="GET",
                path="/test",
                query_params={"key": "value"},
            )
            result = agent.make_request(params)

            self.assertEqual(result, mock_response)
            mock_response.raise_for_status.assert_called_once()

    @patch("app.common.apis.rest_api_agent.logger")
    def test_make_request_with_body(self, _mock_logger):
        """Test request with JSON body."""
        agent = RESTfulAPIAgent(CLIENT_NAME, HOST_URL, MAX_RETRIES)
        mock_response = MagicMock(spec=Response)
        mock_response.status_code = 200
        mock_response.text = '{"result": "success"}'
        mock_response.headers = {}
        mock_response.raise_for_status = MagicMock()

        with patch.object(agent._session, "request", return_value=mock_response):
            params = MakeRequestParams(
                method="POST",
                path="/test",
                body={"key": "value"},
            )
            result = agent.make_request(params)

            self.assertEqual(result, mock_response)

    @patch("app.common.apis.rest_api_agent.logger")
    def test_make_request_with_headers(self, _mock_logger):
        """Test request with custom headers."""
        agent = RESTfulAPIAgent(CLIENT_NAME, HOST_URL, MAX_RETRIES)
        mock_response = MagicMock(spec=Response)
        mock_response.status_code = 200
        mock_response.text = '{"result": "success"}'
        mock_response.headers = {}
        mock_response.raise_for_status = MagicMock()

        with patch.object(agent._session, "request", return_value=mock_response):
            params = MakeRequestParams(
                method="GET",
                path="/test",
                headers={"Authorization": "Bearer token"},
            )
            result = agent.make_request(params)

            self.assertEqual(result, mock_response)

    @patch("app.common.apis.rest_api_agent.logger")
    def test_make_request_request_exception(self, mock_logger):
        """Test request with RequestException."""
        agent = RESTfulAPIAgent(CLIENT_NAME, HOST_URL, MAX_RETRIES)
        request_exception = RequestException("Connection error")

        with patch.object(agent._session, "request", side_effect=request_exception):
            params = MakeRequestParams(
                method="GET",
                path="/test",
            )

            with self.assertRaises(RequestException):
                agent.make_request(params)

            mock_logger.info.assert_called()

    @patch("app.common.apis.rest_api_agent.logger")
    def test_make_request_http_error(self, mock_logger):
        """Test request with HTTPError."""
        agent = RESTfulAPIAgent(CLIENT_NAME, HOST_URL, MAX_RETRIES)
        mock_response = MagicMock(spec=Response)
        mock_response.status_code = 404
        mock_response.text = "Not Found"
        mock_response.headers = {}
        http_error = HTTPError("404 Not Found")
        mock_response.raise_for_status = MagicMock(side_effect=http_error)

        with patch.object(agent._session, "request", return_value=mock_response):
            params = MakeRequestParams(
                method="GET",
                path="/test",
            )

            with self.assertRaises(HTTPError):
                agent.make_request(params)

            mock_logger.info.assert_called()

    def test_update_headers(self):
        """Test updating session headers."""
        agent = RESTfulAPIAgent(CLIENT_NAME, HOST_URL, MAX_RETRIES)
        headers = {"Authorization": "Bearer token"}

        agent.update_headers(headers)

        self.assertIn("Authorization", agent._session.headers)

    def test_update_query_params(self):
        """Test updating session query parameters."""
        agent = RESTfulAPIAgent(CLIENT_NAME, HOST_URL, MAX_RETRIES)
        query_params = {"key": "value"}

        agent.update_query_params(query_params)

        self.assertIn("key", agent._session.params)

    @patch("app.common.apis.rest_api_agent.logger")
    @patch("app.common.apis.rest_api_agent.json_dumps")
    def test_log_request(self, mock_json_dumps, mock_logger):
        """Test request logging."""
        agent = RESTfulAPIAgent(CLIENT_NAME, HOST_URL, MAX_RETRIES)
        mock_json_dumps.return_value = '{"test": "data"}'
        mock_response = MagicMock(spec=Response)
        mock_response.status_code = 200
        mock_response.text = '{"result": "success"}'
        mock_response.headers = {}
        mock_response.raise_for_status = MagicMock()

        with patch.object(agent._session, "request", return_value=mock_response):
            params = MakeRequestParams(
                method="GET",
                path="/test",
                body={"key": "value"},
            )
            agent.make_request(params)

            mock_logger.info.assert_called()

    @patch("app.common.apis.rest_api_agent.logger")
    @patch("app.common.apis.rest_api_agent.json_dumps")
    def test_log_response(self, mock_json_dumps, mock_logger):
        """Test response logging."""
        agent = RESTfulAPIAgent(CLIENT_NAME, HOST_URL, MAX_RETRIES)
        mock_json_dumps.return_value = '{"test": "data"}'
        mock_response = MagicMock(spec=Response)
        mock_response.status_code = 200
        mock_response.text = '{"result": "success"}'
        mock_response.headers = {"Content-Type": "application/json"}
        mock_response.raise_for_status = MagicMock()

        with patch.object(agent._session, "request", return_value=mock_response):
            params = MakeRequestParams(
                method="GET",
                path="/test",
            )
            agent.make_request(params)

            mock_logger.info.assert_called()

