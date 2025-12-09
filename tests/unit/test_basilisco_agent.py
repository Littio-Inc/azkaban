"""Tests for Basilisco API agent."""

import unittest
from unittest.mock import MagicMock, patch

from requests.exceptions import HTTPError
from requests.models import Response

from app.common.apis.basilisco.agent import BasiliscoAgent
from app.common.apis.basilisco.errors import BasiliscoAPIClientError
from app.common.errors import MissingCredentialsError

# Test constants
API_URL = "https://api.example.com"
API_KEY = "test-api-key-12345"
SHORT_API_KEY = "short"
PATCH_SECRETS = "app.common.apis.basilisco.agent.get_secret"
PATCH_REST_AGENT = "app.common.apis.rest_api_agent.RESTfulAPIAgent"


class TestBasiliscoAgent(unittest.TestCase):
    """Test cases for BasiliscoAgent."""

    @patch(PATCH_REST_AGENT)
    @patch(PATCH_SECRETS)
    def test_init_success(self, mock_get_secret, mock_rest_agent_class):
        """Test successful agent initialization."""
        mock_get_secret.side_effect = lambda key: API_URL if key == "BASILISCO_BASE_URL" else API_KEY
        mock_rest_agent = MagicMock()
        mock_rest_agent_class.return_value = mock_rest_agent

        agent = BasiliscoAgent()

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
        mock_get_secret.side_effect = lambda key: None if key == "BASILISCO_BASE_URL" else API_KEY

        with self.assertRaises(MissingCredentialsError):
            BasiliscoAgent()

    @patch(PATCH_SECRETS)
    def test_init_missing_api_key(self, mock_get_secret):
        """Test initialization with missing API key."""
        mock_get_secret.side_effect = lambda key: API_URL if key == "BASILISCO_BASE_URL" else None

        with self.assertRaises(MissingCredentialsError):
            BasiliscoAgent()

    @patch(PATCH_REST_AGENT)
    @patch(PATCH_SECRETS)
    def test_get_success(self, mock_get_secret, mock_rest_agent_class):
        """Test successful GET request."""
        mock_get_secret.side_effect = lambda key: API_URL if key == "BASILISCO_BASE_URL" else API_KEY
        mock_rest_agent = MagicMock()
        mock_rest_agent_class.return_value = mock_rest_agent

        mock_response = MagicMock(spec=Response)
        mock_response.json.return_value = {"transactions": [], "count": 0}
        mock_rest_agent.make_request.return_value = mock_response

        agent = BasiliscoAgent()
        # Replace the make_request method on the agent's parent class instance
        agent.make_request = mock_rest_agent.make_request
        # Also mock update_headers on the actual agent instance
        agent.update_headers = mock_rest_agent.update_headers
        result = agent.get("/v1/backoffice/transactions", {"page": 1})

        self.assertEqual(result, {"transactions": [], "count": 0})
        mock_rest_agent.update_headers.assert_called_once_with({
            "x-api-key": API_KEY,
            "Content-Type": "application/json"
        })
        mock_rest_agent.make_request.assert_called_once()
        self.assertTrue(agent._api_key_is_valid)

    @patch(PATCH_REST_AGENT)
    @patch(PATCH_SECRETS)
    def test_post_success(self, mock_get_secret, mock_rest_agent_class):
        """Test successful POST request."""
        mock_get_secret.side_effect = lambda key: API_URL if key == "BASILISCO_BASE_URL" else API_KEY
        mock_rest_agent = MagicMock()
        mock_rest_agent_class.return_value = mock_rest_agent

        mock_response = MagicMock(spec=Response)
        mock_response.json.return_value = {"id": "test-id"}
        mock_rest_agent.make_request.return_value = mock_response

        agent = BasiliscoAgent()
        # Replace the make_request method on the agent's parent class instance
        agent.make_request = mock_rest_agent.make_request
        # Also mock update_headers on the actual agent instance
        agent.update_headers = mock_rest_agent.update_headers
        result = agent.post("/v1/backoffice/transactions", {"type": "withdrawal"})

        self.assertEqual(result, {"id": "test-id"})
        mock_rest_agent.update_headers.assert_called_once_with({
            "x-api-key": API_KEY,
            "Content-Type": "application/json"
        })
        mock_rest_agent.make_request.assert_called_once()
        self.assertTrue(agent._api_key_is_valid)

    @patch(PATCH_REST_AGENT)
    @patch(PATCH_SECRETS)
    def test_post_with_idempotency_key_in_body(self, mock_get_secret, mock_rest_agent_class):
        """Test POST request with idempotency_key sent in body."""
        mock_get_secret.side_effect = lambda key: API_URL if key == "BASILISCO_BASE_URL" else API_KEY
        mock_rest_agent = MagicMock()
        mock_rest_agent_class.return_value = mock_rest_agent

        mock_response = MagicMock(spec=Response)
        mock_response.json.return_value = {"id": "test-id"}
        mock_rest_agent.make_request.return_value = mock_response

        agent = BasiliscoAgent()
        # Replace the make_request method on the agent's parent class instance
        agent.make_request = mock_rest_agent.make_request
        # Also mock update_headers on the actual agent instance
        agent.update_headers = mock_rest_agent.update_headers

        transaction_data = {"type": "withdrawal", "amount": "100"}
        idempotency_key = "test-idempotency-key-123"
        result = agent.post(
            "/v1/backoffice/transactions",
            json=transaction_data,
            idempotency_key=idempotency_key
        )

        self.assertEqual(result, {"id": "test-id"})
        mock_rest_agent.make_request.assert_called_once()
        
        # Verify that idempotency_key is in the body, not in headers
        call_args = mock_rest_agent.make_request.call_args
        params = call_args[0][0]  # First positional argument is MakeRequestParams
        self.assertIn("idempotency_key", params.body)
        self.assertEqual(params.body["idempotency_key"], idempotency_key)
        self.assertEqual(params.body["type"], "withdrawal")
        self.assertEqual(params.body["amount"], "100")
        # Verify headers don't contain idempotency-key
        if params.headers:
            self.assertNotIn("idempotency-key", params.headers)
        self.assertTrue(agent._api_key_is_valid)

    @patch(PATCH_REST_AGENT)
    @patch(PATCH_SECRETS)
    def test_authenticate_sets_headers(self, mock_get_secret, mock_rest_agent_class):
        """Test that authenticate sets headers correctly."""
        mock_get_secret.side_effect = lambda key: API_URL if key == "BASILISCO_BASE_URL" else API_KEY
        mock_rest_agent = MagicMock()
        mock_rest_agent_class.return_value = mock_rest_agent

        agent = BasiliscoAgent()
        # Mock update_headers on the actual agent instance
        agent.update_headers = mock_rest_agent.update_headers
        agent._authenticate()

        mock_rest_agent.update_headers.assert_called_once_with({
            "x-api-key": API_KEY,
            "Content-Type": "application/json"
        })
        self.assertTrue(agent._api_key_is_valid)

    @patch(PATCH_REST_AGENT)
    @patch(PATCH_SECRETS)
    def test_authenticate_idempotent(self, mock_get_secret, mock_rest_agent_class):
        """Test that authenticate is idempotent."""
        mock_get_secret.side_effect = lambda key: API_URL if key == "BASILISCO_BASE_URL" else API_KEY
        mock_rest_agent = MagicMock()
        mock_rest_agent_class.return_value = mock_rest_agent

        agent = BasiliscoAgent()
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
        mock_get_secret.side_effect = lambda key: API_URL if key == "BASILISCO_BASE_URL" else API_KEY
        mock_rest_agent = MagicMock()
        mock_rest_agent_class.return_value = mock_rest_agent

        mock_http_error = HTTPError("Server error")
        mock_rest_agent.make_request.side_effect = mock_http_error

        agent = BasiliscoAgent()
        with self.assertRaises(BasiliscoAPIClientError):
            agent.get("/v1/backoffice/transactions")

    @patch(PATCH_REST_AGENT)
    @patch(PATCH_SECRETS)
    def test_post_http_error(self, mock_get_secret, mock_rest_agent_class):
        """Test POST request with HTTP error."""
        mock_get_secret.side_effect = lambda key: API_URL if key == "BASILISCO_BASE_URL" else API_KEY
        mock_rest_agent = MagicMock()
        mock_rest_agent_class.return_value = mock_rest_agent

        mock_http_error = HTTPError("Server error")
        mock_rest_agent.make_request.side_effect = mock_http_error

        agent = BasiliscoAgent()
        with self.assertRaises(BasiliscoAPIClientError):
            agent.post("/v1/backoffice/transactions", {})

    @patch(PATCH_REST_AGENT)
    @patch(PATCH_SECRETS)
    def test_get_generic_error(self, mock_get_secret, mock_rest_agent_class):
        """Test GET request with generic error."""
        mock_get_secret.side_effect = lambda key: API_URL if key == "BASILISCO_BASE_URL" else API_KEY
        mock_rest_agent = MagicMock()
        mock_rest_agent_class.return_value = mock_rest_agent

        mock_rest_agent.make_request.side_effect = Exception("Unexpected error")

        agent = BasiliscoAgent()
        with self.assertRaises(BasiliscoAPIClientError):
            agent.get("/v1/backoffice/transactions")


if __name__ == "__main__":
    unittest.main()

