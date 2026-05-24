from __future__ import annotations

from typing import Iterator

from app.config import Settings
from app.llm.base import LLMClient, Message
from app.llm.fake import FakeLLM
from app.services.model_config import ModelConfigStore


class ModelResolver:
    """Builds the LLM client for a role, honoring the admin's live OpenRouter
    overrides with an Anthropic (Claude) fallback.

    Resolution per role:
      - offline (no keys / fake forced) -> FakeLLM
      - an OpenRouter override is set + key present -> OpenRouter(model) with the
        Anthropic default as fallback
      - otherwise -> the Anthropic default for that role

    Constructed clients are cached (so the OpenRouter httpx pool and Anthropic
    client are reused); the override lookup is read fresh per call so admin
    changes take effect without a restart.
    """

    def __init__(self, settings: Settings, store: ModelConfigStore) -> None:
        self._settings = settings
        self._store = store
        self._cache: dict[tuple[str, str], LLMClient] = {}

    def _anthropic(self, model: str) -> LLMClient:
        key = ("anthropic", model)
        if key not in self._cache:
            if self._settings.offline:
                self._cache[key] = FakeLLM()
            else:
                from app.llm.anthropic_client import AnthropicLLM

                self._cache[key] = AnthropicLLM(
                    model=model,
                    api_key=self._settings.anthropic_api_key,  # type: ignore[arg-type]
                    temperature=self._settings.temperature,
                    max_tokens=self._settings.max_tokens,
                )
        return self._cache[key]

    def _openrouter(self, model: str) -> LLMClient:
        key = ("openrouter", model)
        if key not in self._cache:
            from app.llm.openrouter_client import OpenRouterLLM

            self._cache[key] = OpenRouterLLM(
                model=model,
                api_key=self._settings.openrouter_api_key,  # type: ignore[arg-type]
                base_url=self._settings.openrouter_base_url,
                temperature=self._settings.temperature,
                max_tokens=self._settings.max_tokens,
            )
        return self._cache[key]

    def client_for(self, role: str) -> LLMClient:
        if self._settings.offline:
            return FakeLLM()

        default = self._anthropic(self._settings.model_for(role))
        override = self._store.get_overrides().get(role)
        if override and self._settings.openrouter_api_key:
            from app.llm.fallback import FallbackLLM

            return FallbackLLM(self._openrouter(override), default)
        return default


class ResolvingLLM:
    """An LLMClient that resolves its concrete client per call via ModelResolver,
    so global model changes apply live to every request."""

    def __init__(self, role: str, resolver: ModelResolver) -> None:
        self._role = role
        self._resolver = resolver

    def invoke(self, system: str, messages: list[Message]) -> str:
        return self._resolver.client_for(self._role).invoke(system, messages)

    def stream(self, system: str, messages: list[Message]) -> Iterator[str]:
        return self._resolver.client_for(self._role).stream(system, messages)
