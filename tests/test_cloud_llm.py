"""
Test Cloud LLM Integration
Tests for cloud LLM providers and fallback functionality.
"""

import json
import unittest
from unittest.mock import MagicMock, Mock, patch
from urllib.error import HTTPError, URLError
from urllib.request import Request

from nlcli.cloud_llm import (
    CloudLLMConfig,
    CloudLLMProvider,
    CloudLLMResponse,
    CloudLLMService,
    create_cloud_llm_service,
    get_cloud_llm_service,
)


class TestCloudLLMConfig(unittest.TestCase):
    """Test cloud LLM configuration."""

    def test_default_config(self):
        """Test default configuration."""
        config = CloudLLMConfig()
        self.assertFalse(config.enabled)
        self.assertEqual(config.primary_provider, "openai")
        self.assertIn("openai", config.fallback_providers)
        self.assertIn("anthropic", config.fallback_providers)

    @patch.dict("os.environ", {"OPENAI_API_KEY": "test-key"})
    def test_config_from_env(self):
        """Test configuration from environment variables."""
        config = CloudLLMConfig()
        self.assertEqual(config.openai_api_key, "test-key")
        self.assertTrue(config.enabled)  # Should be enabled when API key is present

    def test_custom_config(self):
        """Test custom configuration."""
        config = CloudLLMConfig(
            enabled=True,
            primary_provider="anthropic",
            openai_api_key="test-openai-key",
            anthropic_api_key="test-anthropic-key",
        )

        self.assertTrue(config.enabled)
        self.assertEqual(config.primary_provider, "anthropic")
        self.assertEqual(config.openai_api_key, "test-openai-key")
        self.assertEqual(config.anthropic_api_key, "test-anthropic-key")


class TestCloudLLMProvider(unittest.TestCase):
    """Test cloud LLM provider."""

    def setUp(self):
        self.config = CloudLLMConfig(
            enabled=True,
            openai_api_key="test-openai-key",
            anthropic_api_key="test-anthropic-key",
            google_api_key="test-google-key",
        )
        self.provider = CloudLLMProvider(self.config)
        self.messages = [{"role": "user", "content": "test message"}]

    def test_unsupported_provider(self):
        """Test request to unsupported provider."""
        response = self.provider.make_request(self.messages, "unsupported")

        self.assertFalse(response.success)
        self.assertIn("Unsupported provider", response.error)
        self.assertEqual(response.provider, "unsupported")

    @patch("nlcli.cloud_llm.urlopen")
    def test_openai_request_success(self, mock_urlopen):
        """Test successful OpenAI API request."""
        # Mock response
        mock_response = Mock()
        mock_response.read.return_value = json.dumps(
            {
                "choices": [{"message": {"content": "Test response"}}],
                "usage": {"total_tokens": 10},
            }
        ).encode("utf-8")
        mock_urlopen.return_value.__enter__.return_value = mock_response

        response = self.provider.make_request(self.messages, "openai")

        self.assertTrue(response.success)
        self.assertEqual(response.text, "Test response")
        self.assertEqual(response.provider, "openai")
        self.assertEqual(response.tokens_used, 10)

    @patch("nlcli.cloud_llm.urlopen")
    def test_anthropic_request_success(self, mock_urlopen):
        """Test successful Anthropic API request."""
        mock_response = Mock()
        mock_response.read.return_value = json.dumps(
            {
                "content": [{"text": "Anthropic response"}],
                "usage": {"input_tokens": 5, "output_tokens": 8},
            }
        ).encode("utf-8")
        mock_urlopen.return_value.__enter__.return_value = mock_response

        response = self.provider.make_request(self.messages, "anthropic")

        self.assertTrue(response.success)
        self.assertEqual(response.text, "Anthropic response")
        self.assertEqual(response.provider, "anthropic")
        self.assertEqual(response.tokens_used, 13)  # input + output tokens

    @patch("nlcli.cloud_llm.urlopen")
    def test_google_request_success(self, mock_urlopen):
        """Test successful Google API request."""
        mock_response = Mock()
        mock_response.read.return_value = json.dumps(
            {"candidates": [{"content": {"parts": [{"text": "Google response"}]}}]}
        ).encode("utf-8")
        mock_urlopen.return_value.__enter__.return_value = mock_response

        response = self.provider.make_request(self.messages, "google")

        self.assertTrue(response.success)
        self.assertEqual(response.text, "Google response")
        self.assertEqual(response.provider, "google")

    @patch("nlcli.cloud_llm.urlopen")
    def test_http_error(self, mock_urlopen):
        """Test HTTP error handling."""
        mock_error = HTTPError(
            url="http://test.com", code=401, msg="Unauthorized", hdrs={}, fp=None
        )
        mock_error.read = Mock(
            return_value=json.dumps({"error": {"message": "Invalid API key"}}).encode(
                "utf-8"
            )
        )
        mock_urlopen.side_effect = mock_error

        response = self.provider.make_request(self.messages, "openai")

        self.assertFalse(response.success)
        self.assertIn("Invalid API key", response.error)

    @patch("nlcli.cloud_llm.urlopen")
    def test_network_error(self, mock_urlopen):
        """Test network error handling."""
        mock_urlopen.side_effect = URLError("Network error")

        response = self.provider.make_request(self.messages, "openai")

        self.assertFalse(response.success)
        self.assertIn("Network error", response.error)

    def test_no_api_key(self):
        """Test request without API key."""
        config = CloudLLMConfig(enabled=True)  # No API keys
        provider = CloudLLMProvider(config)

        response = provider.make_request(self.messages, "openai")

        self.assertFalse(response.success)
        self.assertIn("API key not configured", response.error)


class TestCloudLLMService(unittest.TestCase):
    """Test cloud LLM service."""

    def setUp(self):
        self.config = CloudLLMConfig(
            enabled=True,
            openai_api_key="test-key",
            primary_provider="openai",
            fallback_providers=["anthropic"],
        )
        self.service = CloudLLMService(self.config)

    def test_service_availability(self):
        """Test service availability check."""
        self.assertTrue(self.service.is_available())

        # Test with no API keys
        config_no_keys = CloudLLMConfig(enabled=True)
        service_no_keys = CloudLLMService(config_no_keys)
        self.assertFalse(service_no_keys.is_available())

    @patch.object(CloudLLMProvider, "make_request")
    def test_successful_generation(self, mock_make_request):
        """Test successful response generation."""
        mock_make_request.return_value = CloudLLMResponse(
            text="Generated response",
            provider="openai",
            model="gpt-3.5-turbo",
            success=True,
            confidence=0.8,
        )

        response = self.service.generate_response("test prompt")

        self.assertTrue(response.success)
        self.assertEqual(response.text, "Generated response")
        self.assertEqual(response.provider, "openai")

    @patch.object(CloudLLMProvider, "make_request")
    def test_fallback_on_failure(self, mock_make_request):
        """Test fallback to secondary provider on failure."""
        # First call fails, second succeeds
        mock_make_request.side_effect = [
            CloudLLMResponse(
                text="",
                provider="openai",
                model="gpt-3.5-turbo",
                success=False,
                error="API error",
            ),
            CloudLLMResponse(
                text="Fallback response",
                provider="anthropic",
                model="claude-3",
                success=True,
            ),
        ]

        # Configure with Anthropic key for fallback
        self.config.anthropic_api_key = "anthropic-key"

        response = self.service.generate_response("test prompt")

        self.assertTrue(response.success)
        self.assertEqual(response.text, "Fallback response")
        self.assertEqual(response.provider, "anthropic")

    @patch.object(CloudLLMProvider, "make_request")
    def test_all_providers_fail(self, mock_make_request):
        """Test when all providers fail."""
        mock_make_request.return_value = CloudLLMResponse(
            text="",
            provider="openai",
            model="gpt-3.5-turbo",
            success=False,
            error="All failed",
        )

        response = self.service.generate_response("test prompt")

        self.assertFalse(response.success)
        self.assertIn("All failed", response.error or "")

    def test_service_disabled(self):
        """Test service when disabled."""
        config = CloudLLMConfig(enabled=False)
        service = CloudLLMService(config)

        response = service.generate_response("test prompt")

        self.assertFalse(response.success)
        self.assertIn("not available", response.error)

    def test_provider_status(self):
        """Test getting provider status."""
        status = self.service.get_provider_status()

        self.assertIn("openai", status)
        self.assertIn("anthropic", status)
        self.assertIn("google", status)

        self.assertTrue(status["openai"]["configured"])
        self.assertFalse(status["anthropic"]["configured"])
        self.assertFalse(status["google"]["configured"])

    def test_generate_with_system_prompt(self):
        """Test generation with system prompt."""
        with patch.object(self.service.provider, "make_request") as mock_request:
            mock_request.return_value = CloudLLMResponse(
                text="Response with system",
                provider="openai",
                model="gpt-3.5-turbo",
                success=True,
            )

            response = self.service.generate_response("user prompt", "system prompt")

            self.assertTrue(response.success)
            # Verify system prompt was included in request
            call_args = mock_request.call_args[0]
            messages = call_args[0]
            self.assertEqual(len(messages), 2)
            self.assertEqual(messages[0]["role"], "system")
            self.assertEqual(messages[0]["content"], "system prompt")


class TestGlobalFunctions(unittest.TestCase):
    """Test global functions and singletons."""

    def test_create_service(self):
        """Test service creation function."""
        service = create_cloud_llm_service()
        self.assertIsInstance(service, CloudLLMService)

    @patch.dict(
        "os.environ",
        {"NLCLI_CLOUD_LLM_ENABLED": "true", "NLCLI_CLOUD_LLM_PROVIDER": "anthropic"},
    )
    def test_create_service_from_env(self):
        """Test service creation from environment."""
        service = create_cloud_llm_service()
        self.assertTrue(service.config.enabled)
        self.assertEqual(service.config.primary_provider, "anthropic")

    def test_global_service_singleton(self):
        """Test global service singleton."""
        service1 = get_cloud_llm_service()
        service2 = get_cloud_llm_service()

        self.assertIs(service1, service2)


if __name__ == "__main__":
    unittest.main()
