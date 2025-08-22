"""
Cloud LLM Integration
Provides cloud-based LLM fallback when local models are unavailable.
"""

import json
import logging
import os
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


@dataclass
class CloudLLMConfig:
    """Configuration for cloud LLM providers."""

    enabled: bool = False
    primary_provider: str = "openai"  # openai, anthropic, google
    fallback_providers: List[str] = field(
        default_factory=lambda: ["openai", "anthropic"]
    )

    # API Configuration
    openai_api_key: Optional[str] = None
    openai_model: str = "gpt-3.5-turbo"
    openai_base_url: str = "https://api.openai.com/v1"

    anthropic_api_key: Optional[str] = None
    anthropic_model: str = "claude-3-haiku-20240307"
    anthropic_base_url: str = "https://api.anthropic.com/v1"

    google_api_key: Optional[str] = None
    google_model: str = "gemini-pro"
    google_base_url: str = "https://generativelanguage.googleapis.com/v1beta"

    # Request settings
    max_tokens: int = 512
    temperature: float = 0.1
    timeout: int = 30
    max_retries: int = 2
    retry_delay: float = 1.0

    def __post_init__(self):
        # Load from environment variables
        self.openai_api_key = self.openai_api_key or os.environ.get("OPENAI_API_KEY")
        self.anthropic_api_key = self.anthropic_api_key or os.environ.get(
            "ANTHROPIC_API_KEY"
        )
        self.google_api_key = self.google_api_key or os.environ.get("GOOGLE_API_KEY")

        # Enable if at least one API key is available
        if not self.enabled and (
            self.openai_api_key or self.anthropic_api_key or self.google_api_key
        ):
            self.enabled = True


@dataclass
class CloudLLMResponse:
    """Response from cloud LLM provider."""

    text: str
    provider: str
    model: str
    tokens_used: int = 0
    confidence: float = 0.0
    success: bool = True
    error: Optional[str] = None
    response_time: float = 0.0


class CloudLLMProvider:
    """Base class for cloud LLM providers."""

    def __init__(self, config: CloudLLMConfig):
        self.config = config
        self.logger = logging.getLogger(__name__)

    def make_request(
        self, messages: List[Dict[str, str]], provider: str
    ) -> CloudLLMResponse:
        """Make a request to the specified provider."""
        start_time = time.time()

        try:
            if provider == "openai":
                return self._request_openai(messages, start_time)
            elif provider == "anthropic":
                return self._request_anthropic(messages, start_time)
            elif provider == "google":
                return self._request_google(messages, start_time)
            else:
                return CloudLLMResponse(
                    text="",
                    provider=provider,
                    model="unknown",
                    success=False,
                    error=f"Unsupported provider: {provider}",
                    response_time=time.time() - start_time,
                )
        except Exception as e:
            return CloudLLMResponse(
                text="",
                provider=provider,
                model="unknown",
                success=False,
                error=str(e),
                response_time=time.time() - start_time,
            )

    def _request_openai(
        self, messages: List[Dict[str, str]], start_time: float
    ) -> CloudLLMResponse:
        """Make request to OpenAI API."""
        if not self.config.openai_api_key:
            return CloudLLMResponse(
                text="",
                provider="openai",
                model=self.config.openai_model,
                success=False,
                error="OpenAI API key not configured",
                response_time=time.time() - start_time,
            )

        url = f"{self.config.openai_base_url}/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.config.openai_api_key}",
            "Content-Type": "application/json",
        }

        data = {
            "model": self.config.openai_model,
            "messages": messages,
            "max_tokens": self.config.max_tokens,
            "temperature": self.config.temperature,
        }

        return self._make_http_request(
            url, headers, data, "openai", self.config.openai_model, start_time
        )

    def _request_anthropic(
        self, messages: List[Dict[str, str]], start_time: float
    ) -> CloudLLMResponse:
        """Make request to Anthropic API."""
        if not self.config.anthropic_api_key:
            return CloudLLMResponse(
                text="",
                provider="anthropic",
                model=self.config.anthropic_model,
                success=False,
                error="Anthropic API key not configured",
                response_time=time.time() - start_time,
            )

        url = f"{self.config.anthropic_base_url}/messages"
        headers = {
            "x-api-key": self.config.anthropic_api_key,
            "Content-Type": "application/json",
            "anthropic-version": "2023-06-01",
        }

        # Convert messages format for Anthropic
        system_message = ""
        user_messages = []

        for msg in messages:
            if msg["role"] == "system":
                system_message = msg["content"]
            else:
                user_messages.append(msg)

        data = {
            "model": self.config.anthropic_model,
            "max_tokens": self.config.max_tokens,
            "temperature": self.config.temperature,
            "messages": user_messages,
        }

        if system_message:
            data["system"] = system_message

        return self._make_http_request(
            url, headers, data, "anthropic", self.config.anthropic_model, start_time
        )

    def _request_google(
        self, messages: List[Dict[str, str]], start_time: float
    ) -> CloudLLMResponse:
        """Make request to Google Gemini API."""
        if not self.config.google_api_key:
            return CloudLLMResponse(
                text="",
                provider="google",
                model=self.config.google_model,
                success=False,
                error="Google API key not configured",
                response_time=time.time() - start_time,
            )

        url = f"{self.config.google_base_url}/models/{self.config.google_model}:generateContent?key={self.config.google_api_key}"
        headers = {"Content-Type": "application/json"}

        # Convert messages to Gemini format
        contents = []
        for msg in messages:
            if (
                msg["role"] != "system"
            ):  # Gemini doesn't use system messages in the same way
                contents.append({"parts": [{"text": msg["content"]}]})

        data = {
            "contents": contents,
            "generationConfig": {
                "maxOutputTokens": self.config.max_tokens,
                "temperature": self.config.temperature,
            },
        }

        return self._make_http_request(
            url, headers, data, "google", self.config.google_model, start_time
        )

    def _make_http_request(
        self,
        url: str,
        headers: Dict[str, str],
        data: Dict[str, Any],
        provider: str,
        model: str,
        start_time: float,
    ) -> CloudLLMResponse:
        """Make HTTP request to cloud provider."""
        try:
            request = Request(
                url, data=json.dumps(data).encode("utf-8"), headers=headers
            )

            with urlopen(request, timeout=self.config.timeout) as response:
                response_data = json.loads(response.read().decode("utf-8"))

                # Extract response text based on provider
                text = self._extract_response_text(response_data, provider)
                tokens_used = self._extract_tokens_used(response_data, provider)

                return CloudLLMResponse(
                    text=text,
                    provider=provider,
                    model=model,
                    tokens_used=tokens_used,
                    confidence=0.8,  # Cloud providers generally have good confidence
                    success=True,
                    response_time=time.time() - start_time,
                )

        except HTTPError as e:
            error_msg = f"HTTP {e.code}: {e.reason}"
            try:
                error_data = json.loads(e.read().decode("utf-8"))
                if "error" in error_data:
                    if isinstance(error_data["error"], dict):
                        error_msg = error_data["error"].get("message", error_msg)
                    else:
                        error_msg = str(error_data["error"])
            except Exception:
                pass

            return CloudLLMResponse(
                text="",
                provider=provider,
                model=model,
                success=False,
                error=error_msg,
                response_time=time.time() - start_time,
            )

        except (URLError, TimeoutError) as e:
            return CloudLLMResponse(
                text="",
                provider=provider,
                model=model,
                success=False,
                error=f"Network error: {str(e)}",
                response_time=time.time() - start_time,
            )

    def _extract_response_text(
        self, response_data: Dict[str, Any], provider: str
    ) -> str:
        """Extract response text from provider-specific response format."""
        try:
            if provider == "openai":
                return response_data["choices"][0]["message"]["content"]
            elif provider == "anthropic":
                return response_data["content"][0]["text"]
            elif provider == "google":
                return response_data["candidates"][0]["content"]["parts"][0]["text"]
        except (KeyError, IndexError, TypeError):
            pass

        return ""

    def _extract_tokens_used(self, response_data: Dict[str, Any], provider: str) -> int:
        """Extract tokens used from provider response."""
        try:
            if provider == "openai":
                return response_data.get("usage", {}).get("total_tokens", 0)
            elif provider == "anthropic":
                return response_data.get("usage", {}).get(
                    "input_tokens", 0
                ) + response_data.get("usage", {}).get("output_tokens", 0)
            elif provider == "google":
                # Google may not always return token usage
                return 0
        except (KeyError, TypeError):
            pass

        return 0


class CloudLLMService:
    """Service for managing cloud LLM interactions with fallback."""

    def __init__(self, config: Optional[CloudLLMConfig] = None):
        self.config = config or CloudLLMConfig()
        self.provider = CloudLLMProvider(self.config)
        self.logger = logging.getLogger(__name__)

    def is_available(self) -> bool:
        """Check if cloud LLM service is available."""
        return self.config.enabled and (
            self.config.openai_api_key
            or self.config.anthropic_api_key
            or self.config.google_api_key
        )

    def generate_response(
        self, prompt: str, system_prompt: Optional[str] = None
    ) -> CloudLLMResponse:
        """Generate response using cloud LLM with fallback."""
        if not self.is_available():
            return CloudLLMResponse(
                text="",
                provider="none",
                model="none",
                success=False,
                error="Cloud LLM service not available",
            )

        # Build messages
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        # Try providers in order
        providers_to_try = [self.config.primary_provider] + [
            p
            for p in self.config.fallback_providers
            if p != self.config.primary_provider
        ]

        last_response = None

        for provider in providers_to_try:
            # Check if provider is configured
            if not self._is_provider_configured(provider):
                continue

            self.logger.info(f"Trying cloud LLM provider: {provider}")

            for attempt in range(self.config.max_retries + 1):
                response = self.provider.make_request(messages, provider)

                if response.success:
                    self.logger.info(
                        f"Cloud LLM request successful with {provider} (attempt {attempt + 1})"
                    )
                    return response

                last_response = response
                self.logger.warning(
                    f"Cloud LLM request failed with {provider} (attempt {attempt + 1}): {response.error}"
                )

                # Wait before retry
                if attempt < self.config.max_retries:
                    time.sleep(self.config.retry_delay * (attempt + 1))

        # All providers failed
        return last_response or CloudLLMResponse(
            text="",
            provider="none",
            model="none",
            success=False,
            error="All cloud LLM providers failed",
        )

    def _is_provider_configured(self, provider: str) -> bool:
        """Check if a provider is properly configured."""
        if provider == "openai":
            return bool(self.config.openai_api_key)
        elif provider == "anthropic":
            return bool(self.config.anthropic_api_key)
        elif provider == "google":
            return bool(self.config.google_api_key)
        return False

    def get_provider_status(self) -> Dict[str, Dict[str, Any]]:
        """Get status of all providers."""
        status = {}

        for provider in ["openai", "anthropic", "google"]:
            status[provider] = {
                "configured": self._is_provider_configured(provider),
                "model": getattr(self.config, f"{provider}_model", "unknown"),
            }

        return status


def create_cloud_llm_service() -> CloudLLMService:
    """Create cloud LLM service from environment configuration."""
    config = CloudLLMConfig()

    # Override from environment variables
    if os.environ.get("NLCLI_CLOUD_LLM_ENABLED", "").lower() == "true":
        config.enabled = True

    if "NLCLI_CLOUD_LLM_PROVIDER" in os.environ:
        config.primary_provider = os.environ["NLCLI_CLOUD_LLM_PROVIDER"]

    return CloudLLMService(config)


# Global service instance
_cloud_llm_service: Optional[CloudLLMService] = None


def get_cloud_llm_service() -> CloudLLMService:
    """Get the global cloud LLM service instance."""
    global _cloud_llm_service
    if _cloud_llm_service is None:
        _cloud_llm_service = create_cloud_llm_service()
    return _cloud_llm_service
