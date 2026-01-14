"""Tests for Cassandra API agent."""

import unittest
from unittest.mock import MagicMock, patch

from requests.exceptions import HTTPError
from requests.models import Response

from app.common.apis.cassandra.agent import CassandraAgent
from app.common.apis.cassandra.errors import CassandraAPIClientError
from app.common.errors import MissingCredentialsError

# Test constants
API_URL = "https://api.example.com"
API_KEY = "test-api-key-12345"
SHORT_API_KEY = "short"
PATCH_SECRETS = "app.common.apis.cassandra.agent.get_secret"
PATCH_REST_AGENT = "app.common.apis.rest_api_agent.RESTfulAPIAgent"


class TestCassandraAgent(unittest.TestCase):
    """Test cases for CassandraAgent."""

    @patch(PATCH_REST_AGENT)
    @patch(PATCH_SECRETS)
    def test_init_success(self, mock_get_secret, mock_rest_agent_class):
        """Test successful agent initialization."""
        mock_get_secret.side_effect = lambda key: API_URL if key == "CASSANDRA_API_URL" else API_KEY
        mock_rest_agent = MagicMock()
        mock_rest_agent_class.return_value = mock_rest_agent

        agent = CassandraAgent()

        # Verify attributes are set correctly
        self.assertEqual(agent._api_host, API_URL)
        self.assertEqual(agent._api_key, API_KEY)
        self.assertFalse(agent._api_key_is_valid)
        # Verify that the agent has the expected parent class methods
        self.assertTrue(hasattr(agent, 'make_request'))
        self.assertTrue(hasattr(agent, 'update_headers'))

    @patch(PATCH_SECRETS)
    def test_init_missing_url(self, mock_get_secret):
        """Test initialization with missing API URL."""
        mock_get_secret.side_effect = lambda key: None if key == "CASSANDRA_API_URL" else API_KEY

        with self.assertRaises(MissingCredentialsError):
            CassandraAgent()

    @patch(PATCH_SECRETS)
    def test_init_missing_api_key(self, mock_get_secret):
        """Test initialization with missing API key."""
        mock_get_secret.side_effect = lambda key: API_URL if key == "CASSANDRA_API_URL" else None

        with self.assertRaises(MissingCredentialsError):
            CassandraAgent()

    @patch(PATCH_REST_AGENT)
    @patch(PATCH_SECRETS)
    def test_init_with_short_api_key(self, mock_get_secret, mock_rest_agent_class):
        """Test initialization with short API key."""
        mock_get_secret.side_effect = lambda key: API_URL if key == "CASSANDRA_API_URL" else SHORT_API_KEY
        mock_rest_agent = MagicMock()
        mock_rest_agent_class.return_value = mock_rest_agent

        agent = CassandraAgent()

        self.assertEqual(agent._api_key, SHORT_API_KEY)

    @patch(PATCH_REST_AGENT)
    @patch(PATCH_SECRETS)
    def test_get_success(self, mock_get_secret, mock_rest_agent_class):
        """Test successful GET request."""
        mock_get_secret.side_effect = lambda key: API_URL if key == "CASSANDRA_API_URL" else API_KEY
        mock_rest_agent = MagicMock()
        mock_rest_agent_class.return_value = mock_rest_agent

        mock_response = MagicMock(spec=Response)
        mock_response.json.return_value = {"result": "success"}
        mock_rest_agent.make_request.return_value = mock_response

        agent = CassandraAgent()
        # Replace the make_request method on the agent's parent class instance
        agent.make_request = mock_rest_agent.make_request
        # Also mock update_headers on the actual agent instance
        agent.update_headers = mock_rest_agent.update_headers
        result = agent.get("/test/path", query_params={"key": "value"})

        self.assertEqual(result, {"result": "success"})
        mock_rest_agent.update_headers.assert_called_once_with({"x-api-key": API_KEY})
        mock_rest_agent.make_request.assert_called_once()
        self.assertTrue(agent._api_key_is_valid)

    @patch(PATCH_REST_AGENT)
    @patch(PATCH_SECRETS)
    def test_post_success(self, mock_get_secret, mock_rest_agent_class):
        """Test successful POST request."""
        mock_get_secret.side_effect = lambda key: API_URL if key == "CASSANDRA_API_URL" else API_KEY
        mock_rest_agent = MagicMock()
        mock_rest_agent_class.return_value = mock_rest_agent

        mock_response = MagicMock(spec=Response)
        mock_response.json.return_value = {"result": "created"}
        mock_rest_agent.make_request.return_value = mock_response

        agent = CassandraAgent()
        # Replace the make_request method on the agent's parent class instance
        agent.make_request = mock_rest_agent.make_request
        # Also mock update_headers on the actual agent instance
        agent.update_headers = mock_rest_agent.update_headers
        result = agent.post("/test/path", json={"data": "test"})

        self.assertEqual(result, {"result": "created"})
        mock_rest_agent.update_headers.assert_called_once_with({"x-api-key": API_KEY})
        mock_rest_agent.make_request.assert_called_once()
        self.assertTrue(agent._api_key_is_valid)

    @patch(PATCH_REST_AGENT)
    @patch(PATCH_SECRETS)
    def test_authenticate_first_time(self, mock_get_secret, mock_rest_agent_class):
        """Test authentication on first call."""
        mock_get_secret.side_effect = lambda key: API_URL if key == "CASSANDRA_API_URL" else API_KEY
        mock_rest_agent = MagicMock()
        mock_rest_agent_class.return_value = mock_rest_agent

        mock_response = MagicMock(spec=Response)
        mock_response.json.return_value = {"result": "success"}
        mock_rest_agent.make_request.return_value = mock_response

        agent = CassandraAgent()
        # Replace the make_request method on the agent's parent class instance
        agent.make_request = mock_rest_agent.make_request
        # Also mock update_headers on the actual agent instance
        agent.update_headers = mock_rest_agent.update_headers
        self.assertFalse(agent._api_key_is_valid)

        result = agent.get("/test/path")

        self.assertEqual(result, {"result": "success"})
        mock_rest_agent.update_headers.assert_called_once_with({"x-api-key": API_KEY})
        self.assertTrue(agent._api_key_is_valid)

    @patch(PATCH_REST_AGENT)
    @patch(PATCH_SECRETS)
    def test_authenticate_skip_if_valid(self, mock_get_secret, mock_rest_agent_class):
        """Test authentication is skipped if already valid."""
        mock_get_secret.side_effect = lambda key: API_URL if key == "CASSANDRA_API_URL" else API_KEY
        mock_rest_agent = MagicMock()
        mock_rest_agent_class.return_value = mock_rest_agent

        mock_response = MagicMock(spec=Response)
        mock_response.json.return_value = {"result": "success"}
        mock_rest_agent.make_request.return_value = mock_response

        agent = CassandraAgent()
        # Replace the make_request method on the agent's parent class instance
        agent.make_request = mock_rest_agent.make_request
        # Also mock update_headers on the actual agent instance
        agent.update_headers = mock_rest_agent.update_headers
        agent._api_key_is_valid = True

        result = agent.get("/test/path")

        self.assertEqual(result, {"result": "success"})
        mock_rest_agent.update_headers.assert_not_called()

    @patch(PATCH_REST_AGENT)
    @patch(PATCH_SECRETS)
    def test_get_http_error(self, mock_get_secret, mock_rest_agent_class):
        """Test GET request with HTTPError."""
        mock_get_secret.side_effect = lambda key: API_URL if key == "CASSANDRA_API_URL" else API_KEY
        mock_rest_agent = MagicMock()
        mock_rest_agent_class.return_value = mock_rest_agent

        http_error = HTTPError("404 Not Found")
        # Mock make_request to raise HTTPError directly
        mock_rest_agent.make_request.side_effect = http_error

        agent = CassandraAgent()
        # Replace the make_request method on the agent's parent class instance
        agent.make_request = mock_rest_agent.make_request

        with self.assertRaises(CassandraAPIClientError) as context:
            agent.get("/test/path")

        self.assertIn("Error calling Cassandra API", str(context.exception))

    @patch(PATCH_REST_AGENT)
    @patch(PATCH_SECRETS)
    def test_get_generic_error(self, mock_get_secret, mock_rest_agent_class):
        """Test GET request with generic exception."""
        mock_get_secret.side_effect = lambda key: API_URL if key == "CASSANDRA_API_URL" else API_KEY
        mock_rest_agent = MagicMock()
        mock_rest_agent_class.return_value = mock_rest_agent

        generic_error = ValueError("Unexpected error")
        mock_rest_agent.make_request.side_effect = generic_error

        agent = CassandraAgent()
        # Replace the make_request method on the agent's parent class instance
        agent.make_request = mock_rest_agent.make_request

        with self.assertRaises(CassandraAPIClientError) as context:
            agent.get("/test/path")

        self.assertIn("Unexpected error calling Cassandra API", str(context.exception))

    @patch(PATCH_REST_AGENT)
    @patch(PATCH_SECRETS)
    def test_post_http_error(self, mock_get_secret, mock_rest_agent_class):
        """Test POST request with HTTPError."""
        mock_get_secret.side_effect = lambda key: API_URL if key == "CASSANDRA_API_URL" else API_KEY
        mock_rest_agent = MagicMock()
        mock_rest_agent_class.return_value = mock_rest_agent

        http_error = HTTPError("500 Internal Server Error")
        # Mock make_request to raise HTTPError directly
        mock_rest_agent.make_request.side_effect = http_error

        agent = CassandraAgent()
        # Replace the make_request method on the agent's parent class instance
        agent.make_request = mock_rest_agent.make_request

        with self.assertRaises(CassandraAPIClientError) as context:
            agent.post("/test/path", json={"data": "test"})

        self.assertIn("Error calling Cassandra API", str(context.exception))

    @patch(PATCH_REST_AGENT)
    @patch(PATCH_SECRETS)
    def test_post_generic_error(self, mock_get_secret, mock_rest_agent_class):
        """Test POST request with generic exception."""
        mock_get_secret.side_effect = lambda key: API_URL if key == "CASSANDRA_API_URL" else API_KEY
        mock_rest_agent = MagicMock()
        mock_rest_agent_class.return_value = mock_rest_agent

        generic_error = TypeError("Unexpected type error")
        mock_rest_agent.make_request.side_effect = generic_error

        agent = CassandraAgent()
        # Replace the make_request method on the agent's parent class instance
        agent.make_request = mock_rest_agent.make_request

        with self.assertRaises(CassandraAPIClientError) as context:
            agent.post("/test/path", json={"data": "test"})

        self.assertIn("Unexpected error calling Cassandra API", str(context.exception))

    @patch(PATCH_REST_AGENT)
    @patch(PATCH_SECRETS)
    def test_put_success(self, mock_get_secret, mock_rest_agent_class):
        """Test successful PUT request."""
        mock_get_secret.side_effect = lambda key: API_URL if key == "CASSANDRA_API_URL" else API_KEY
        mock_rest_agent = MagicMock()
        mock_rest_agent_class.return_value = mock_rest_agent

        mock_response = MagicMock(spec=Response)
        mock_response.json.return_value = {"result": "updated"}
        mock_rest_agent.make_request.return_value = mock_response

        agent = CassandraAgent()
        # Replace the make_request method on the agent's parent class instance
        agent.make_request = mock_rest_agent.make_request
        # Also mock update_headers on the actual agent instance
        agent.update_headers = mock_rest_agent.update_headers
        result = agent.put("/test/path", json={"data": "test"})

        self.assertEqual(result, {"result": "updated"})
        mock_rest_agent.update_headers.assert_called_once_with({"x-api-key": API_KEY})
        mock_rest_agent.make_request.assert_called_once()
        self.assertTrue(agent._api_key_is_valid)

    @patch(PATCH_REST_AGENT)
    @patch(PATCH_SECRETS)
    def test_put_http_error(self, mock_get_secret, mock_rest_agent_class):
        """Test PUT request with HTTPError."""
        mock_get_secret.side_effect = lambda key: API_URL if key == "CASSANDRA_API_URL" else API_KEY
        mock_rest_agent = MagicMock()
        mock_rest_agent_class.return_value = mock_rest_agent

        http_error = HTTPError("400 Bad Request")
        # Mock make_request to raise HTTPError directly
        mock_rest_agent.make_request.side_effect = http_error

        agent = CassandraAgent()
        # Replace the make_request method on the agent's parent class instance
        agent.make_request = mock_rest_agent.make_request

        with self.assertRaises(CassandraAPIClientError) as context:
            agent.put("/test/path", json={"data": "test"})

        self.assertIn("Error calling Cassandra API", str(context.exception))

    @patch(PATCH_REST_AGENT)
    @patch(PATCH_SECRETS)
    def test_delete_success_204(self, mock_get_secret, mock_rest_agent_class):
        """Test successful DELETE request with 204 status."""
        mock_get_secret.side_effect = lambda key: API_URL if key == "CASSANDRA_API_URL" else API_KEY
        mock_rest_agent = MagicMock()
        mock_rest_agent_class.return_value = mock_rest_agent

        mock_response = MagicMock(spec=Response)
        mock_response.status_code = 204
        mock_rest_agent.make_request.return_value = mock_response

        agent = CassandraAgent()
        # Replace the make_request method on the agent's parent class instance
        agent.make_request = mock_rest_agent.make_request
        # Also mock update_headers on the actual agent instance
        agent.update_headers = mock_rest_agent.update_headers
        result = agent.delete("/test/path")

        self.assertIsNone(result)
        mock_rest_agent.update_headers.assert_called_once_with({"x-api-key": API_KEY})
        mock_rest_agent.make_request.assert_called_once()
        self.assertTrue(agent._api_key_is_valid)

    @patch(PATCH_REST_AGENT)
    @patch(PATCH_SECRETS)
    def test_delete_success_non_204(self, mock_get_secret, mock_rest_agent_class):
        """Test successful DELETE request with non-204 status."""
        mock_get_secret.side_effect = lambda key: API_URL if key == "CASSANDRA_API_URL" else API_KEY
        mock_rest_agent = MagicMock()
        mock_rest_agent_class.return_value = mock_rest_agent

        mock_response = MagicMock(spec=Response)
        mock_response.status_code = 200
        mock_rest_agent.make_request.return_value = mock_response

        agent = CassandraAgent()
        # Replace the make_request method on the agent's parent class instance
        agent.make_request = mock_rest_agent.make_request
        # Also mock update_headers on the actual agent instance
        agent.update_headers = mock_rest_agent.update_headers
        result = agent.delete("/test/path")

        self.assertIsNone(result)
        mock_rest_agent.update_headers.assert_called_once_with({"x-api-key": API_KEY})
        mock_rest_agent.make_request.assert_called_once()

    @patch(PATCH_REST_AGENT)
    @patch(PATCH_SECRETS)
    def test_delete_http_error(self, mock_get_secret, mock_rest_agent_class):
        """Test DELETE request with HTTPError."""
        mock_get_secret.side_effect = lambda key: API_URL if key == "CASSANDRA_API_URL" else API_KEY
        mock_rest_agent = MagicMock()
        mock_rest_agent_class.return_value = mock_rest_agent

        http_error = HTTPError("404 Not Found")
        # Mock make_request to raise HTTPError directly
        mock_rest_agent.make_request.side_effect = http_error

        agent = CassandraAgent()
        # Replace the make_request method on the agent's parent class instance
        agent.make_request = mock_rest_agent.make_request

        with self.assertRaises(CassandraAPIClientError) as context:
            agent.delete("/test/path")

        self.assertIn("Error calling Cassandra API", str(context.exception))

    @patch(PATCH_REST_AGENT)
    @patch(PATCH_SECRETS)
    def test_delete_generic_error(self, mock_get_secret, mock_rest_agent_class):
        """Test DELETE request with generic exception."""
        mock_get_secret.side_effect = lambda key: API_URL if key == "CASSANDRA_API_URL" else API_KEY
        mock_rest_agent = MagicMock()
        mock_rest_agent_class.return_value = mock_rest_agent

        generic_error = ValueError("Unexpected error")
        mock_rest_agent.make_request.side_effect = generic_error

        agent = CassandraAgent()
        # Replace the make_request method on the agent's parent class instance
        agent.make_request = mock_rest_agent.make_request

        with self.assertRaises(CassandraAPIClientError) as context:
            agent.delete("/test/path")

        self.assertIn("Unexpected error calling Cassandra API", str(context.exception))
