"""LLM Router supporting multiple providers with phase-based model selection."""
from __future__ import annotations

import json
from typing import Any, Dict, List, Optional, Type

import structlog
from openai import OpenAI
from pydantic import BaseModel

log = structlog.get_logger(__name__)


class LLMClient:
    """Wrapper around OpenAI-compatible API client."""

    def __init__(
        self,
        api_key: str,
        base_url: Optional[str] = None,
        model: str = "gpt-4o",
        response_model: Optional[Type[BaseModel]] = None,
    ):
        self.model = model
        self.response_model = response_model
        self.client = OpenAI(api_key=api_key, base_url=base_url)
        log.debug("LLMClient init", model=model, base_url=base_url)

    def generate(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 4096,
    ) -> str:
        """Generate a text response."""
        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
        )
        return response.choices[0].message.content or ""

    def generate_structured(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 4096,
    ) -> BaseModel:
        """Generate a structured response matching self.response_model."""
        if not self.response_model:
            raise ValueError("response_model must be set for structured generation")

        # Use JSON mode
        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            response_format={"type": "json_object"},
        )

        content = response.choices[0].message.content or "{}"
        data = json.loads(content)
        return self.response_model.model_validate(data)


class LLMRouter:
    """Route LLM requests to different providers based on phase."""

    # Provider configurations (base_url for OpenAI-compatible APIs)
    PROVIDERS = {
        "openai": {"base_url": None},
        "anthropic": {"base_url": None},  # Uses native Anthropic client
        "groq": {"base_url": "https://api.groq.com/openai/v1"},
        "sambanova": {"base_url": "https://api.sambanova.ai/v1"},
        "codestral": {"base_url": "https://codestral.mistral.ai/v1"},  # Mistral's Codestral
    }

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.llm_config = config.get("llm", {})
        self._clients: Dict[str, LLMClient] = {}
        log.debug("LLMRouter init", default_provider=self.llm_config.get("default_provider"))

    def _get_client(self, provider: str) -> LLMClient:
        """Get or create a client for the specified provider."""
        if provider in self._clients:
            return self._clients[provider]

        provider_config = self.llm_config.get(provider, {})
        api_key = provider_config.get("api_key", "")
        model = provider_config.get("model", "gpt-4o")
        base_url = self.PROVIDERS.get(provider, {}).get("base_url")

        if not api_key:
            log.warning(f"No API key for provider {provider}, using default")
            # Fall back to OpenAI
            provider = "openai"
            provider_config = self.llm_config.get("openai", {})
            api_key = provider_config.get("api_key", "")
            model = provider_config.get("model", "gpt-4o")
            base_url = None

        client = LLMClient(api_key=api_key, base_url=base_url, model=model)
        self._clients[provider] = client
        return client

    def for_phase(self, phase: str) -> LLMClient:
        """Get the appropriate LLM client for a specific phase.

        Phases:
            - 'plan': Model for planning/reasoning
            - 'execute': Model for execution/code generation
            - 'fallback': Cheaper/faster model for reflection
        """
        phases = self.llm_config.get("phases", {})
        provider = phases.get(phase, self.llm_config.get("default_provider", "openai"))
        log.debug("LLMRouter.for_phase", phase=phase, provider=provider)
        return self._get_client(provider)
