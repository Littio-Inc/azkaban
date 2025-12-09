"""Tests for Diagon API agent."""

import unittest
from unittest.mock import MagicMock, patch

from requests.exceptions import HTTPError
from requests.models import Response

from app.common.apis.diagon.agent import DiagonAgent
from app.common.apis.diagon.errors import DiagonAPIClientError
from app.common.errors import MissingCredentialsError

# Test constants
API_URL = "https://api.example.com"
API_KEY = "test-api-key-12345"
SHORT_API_KEY = "short"
PATCH_SECRETS = "app.common.apis.diagon.agent.get_secret"
PATCH_REST_AGENT = "app.common.apis.rest_api_agent.RESTfulAPIAgent"


class TestDiagonAgent(unittest.TestCase):
    """Test cases for DiagonAgent."""

    @patch(PATCH_REST_AGENT)
    @patch(PATCH_SECRETS)
    def test_init_success(self, mock_get_secret, mock_rest_agent_class):
        """Test successful agent initialization."""
        mock_get_secret.side_effect = lambda key: API_URL if key == "DIAGON_BASE_URL" else API_KEY
        mock_rest_agent = MagicMock()
        mock_rest_agent_class.return_value = mock_rest_agent

        agent = DiagonAgent()

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
        mock_get_secret.side_effect = lambda key: None if key == "DIAGON_BASE_URL" else API_KEY

        with self.assertRaises(MissingCredentialsError):
            DiagonAgent()

    @patch(PATCH_SECRETS)
    def test_init_missing_api_key(self, mock_get_secret):
        """Test initialization with missing API key."""
        mock_get_secret.side_effect = lambda key: API_URL if key == "DIAGON_BASE_URL" else None

        with self.assertRaises(MissingCredentialsError):
            DiagonAgent()

    @patch(PATCH_REST_AGENT)
    @patch(PATCH_SECRETS)
    def test_get_success(self, mock_get_secret, mock_rest_agent_class):
        """Test successful GET request."""
        mock_get_secret.side_effect = lambda key: API_URL if key == "DIAGON_BASE_URL" else API_KEY
        mock_rest_agent = MagicMock()
        mock_rest_agent_class.return_value = mock_rest_agent

        mock_response = MagicMock(spec=Response)
        mock_response.json.return_value = [{"id": "1", "name": "Test"}]
        mock_rest_agent.make_request.return_value = mock_response

        agent = DiagonAgent()
        # Replace the make_request method on the agent's parent class instance
        agent.make_request = mock_rest_agent.make_request
        # Also mock update_headers on the actual agent instance
        agent.update_headers = mock_rest_agent.update_headers
        result = agent.get("/vault/accounts")

        self.assertEqual(result, [{"id": "1", "name": "Test"}])
        mock_rest_agent.update_headers.assert_called_once_with({"X-API-KEY": API_KEY})
        mock_rest_agent.make_request.assert_called_once()
        self.assertTrue(agent._api_key_is_valid)

    @patch(PATCH_REST_AGENT)
    @patch(PATCH_SECRETS)
    def test_post_success(self, mock_get_secret, mock_rest_agent_class):
        """Test successful POST request."""
        mock_get_secret.side_effect = lambda key: API_URL if key == "DIAGON_BASE_URL" else API_KEY
        mock_rest_agent = MagicMock()
        mock_rest_agent_class.return_value = mock_rest_agent

        mock_response = MagicMock(spec=Response)
        mock_response.json.return_value = {"message": "Success", "idempotencyKey": "key-123"}
        mock_rest_agent.make_request.return_value = mock_response

        agent = DiagonAgent()
        # Replace the make_request method on the agent's parent class instance
        agent.make_request = mock_rest_agent.make_request
        # Also mock update_headers on the actual agent instance
        agent.update_headers = mock_rest_agent.update_headers
        result = agent.post("/vault/accounts/1/USDC/balance")

        self.assertEqual(result, {"message": "Success", "idempotencyKey": "key-123"})
        mock_rest_agent.update_headers.assert_called_once_with({"X-API-KEY": API_KEY})
        mock_rest_agent.make_request.assert_called_once()
        self.assertTrue(agent._api_key_is_valid)

    @patch(PATCH_REST_AGENT)
    @patch(PATCH_SECRETS)
    def test_authenticate_sets_headers(self, mock_get_secret, mock_rest_agent_class):
        """Test that authenticate sets headers correctly."""
        mock_get_secret.side_effect = lambda key: API_URL if key == "DIAGON_BASE_URL" else API_KEY
        mock_rest_agent = MagicMock()
        mock_rest_agent_class.return_value = mock_rest_agent

        agent = DiagonAgent()
        # Mock update_headers on the actual agent instance
        agent.update_headers = mock_rest_agent.update_headers
        agent._authenticate()

        mock_rest_agent.update_headers.assert_called_once_with({"X-API-KEY": API_KEY})
        self.assertTrue(agent._api_key_is_valid)

    @patch(PATCH_REST_AGENT)
    @patch(PATCH_SECRETS)
    def test_authenticate_idempotent(self, mock_get_secret, mock_rest_agent_class):
        """Test that authenticate is idempotent."""
        mock_get_secret.side_effect = lambda key: API_URL if key == "DIAGON_BASE_URL" else API_KEY
        mock_rest_agent = MagicMock()
        mock_rest_agent_class.return_value = mock_rest_agent

        agent = DiagonAgent()
        # Mock update_headers on the actual agent instance
        agent.update_headers = mock_rest_agent.update_headers
        agent._authenticate()
        agent._authenticate()

        # Should only be called once
        self.assertEqual(mock_rest_agent.update_headers.call_count, 1)

    @patch(PATCH_REST_AGENT)
    @patch(PATCH_SECRETS)
    def test_get_http_error(self, mock_get_secret, mock_rest_agent_class):
        """Test GET request with HTTP error."""
        mock_get_secret.side_effect = lambda key: API_URL if key == "DIAGON_BASE_URL" else API_KEY
        mock_rest_agent = MagicMock()
        mock_rest_agent_class.return_value = mock_rest_agent

        mock_http_error = HTTPError("Server error")
        mock_rest_agent.make_request.side_effect = mock_http_error

        agent = DiagonAgent()
        with self.assertRaises(DiagonAPIClientError):
            agent.get("/vault/accounts")

    @patch(PATCH_REST_AGENT)
    @patch(PATCH_SECRETS)
    def test_post_http_error(self, mock_get_secret, mock_rest_agent_class):
        """Test POST request with HTTP error."""
        mock_get_secret.side_effect = lambda key: API_URL if key == "DIAGON_BASE_URL" else API_KEY
        mock_rest_agent = MagicMock()
        mock_rest_agent_class.return_value = mock_rest_agent

        mock_http_error = HTTPError("Server error")
        mock_rest_agent.make_request.side_effect = mock_http_error

        agent = DiagonAgent()
        with self.assertRaises(DiagonAPIClientError):
            agent.post("/vault/accounts/1/USDC/balance")

    @patch(PATCH_REST_AGENT)
    @patch(PATCH_SECRETS)
    def test_get_generic_error(self, mock_get_secret, mock_rest_agent_class):
        """Test GET request with generic error."""
        mock_get_secret.side_effect = lambda key: API_URL if key == "DIAGON_BASE_URL" else API_KEY
        mock_rest_agent = MagicMock()
        mock_rest_agent_class.return_value = mock_rest_agent

        mock_rest_agent.make_request.side_effect = Exception("Unexpected error")

        agent = DiagonAgent()
        with self.assertRaises(DiagonAPIClientError):
            agent.get("/vault/accounts")


if __name__ == "__main__":
    unittest.main()

