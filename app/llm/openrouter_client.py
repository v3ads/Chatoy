from __future__ import annotations

import json
from typing import Iterator

import httpx

from app.llm.base import Message


class OpenRouterError(RuntimeError):
    pass


class OpenRouterLLM:
    """LLM client for OpenRouter's OpenAI-compatible chat completions API.

    Raises on transport/HTTP errors (before any token is yielded) so callers
    like FallbackLLM can fall back to a default model.
    """

    def __init__(
        self,
        model: str,
        api_key: str,
        base_url: str = "https://openrouter.ai/api/v1",
        temperature: float = 0.7,
        max_tokens: int = 2048,
        timeout: float = 60.0,
    ) -> None:
        self._model = model
        self._temperature = temperature
        self._max_tokens = max_tokens
        self._client = httpx.Client(
            base_url=base_url.rstrip("/"),
            timeout=httpx.Timeout(timeout, connect=10.0),
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
                # Recommended by OpenRouter for attribution; harmless if ignored.
                "HTTP-Referer": "https://mythostack.com",
                "X-Title": "MythoStack",
            },
        )

    def _payload(self, system: str, messages: list[Message], stream: bool) -> dict:
        oa_messages = [{"role": "system", "content": system}]
        for m in messages:
            oa_messages.append({"role": m.get("role", "user"), "content": m.get("content", "")})
        return {
            "model": self._model,
            "messages": oa_messages,
            "max_tokens": self._max_tokens,
            "temperature": self._temperature,
            "stream": stream,
        }

    def invoke(self, system: str, messages: list[Message]) -> str:
        resp = self._client.post(
            "/chat/completions", json=self._payload(system, messages, stream=False)
        )
        if resp.status_code >= 400:
            raise OpenRouterError(f"OpenRouter {resp.status_code}: {resp.text[:300]}")
        data = resp.json()
        try:
            return data["choices"][0]["message"]["content"] or ""
        except (KeyError, IndexError, TypeError) as exc:
            raise OpenRouterError(f"Unexpected OpenRouter response: {exc}") from exc

    def stream(self, system: str, messages: list[Message]) -> Iterator[str]:
        with self._client.stream(
            "POST", "/chat/completions", json=self._payload(system, messages, stream=True)
        ) as resp:
            if resp.status_code >= 400:
                body = resp.read().decode("utf-8", "replace")
                raise OpenRouterError(f"OpenRouter {resp.status_code}: {body[:300]}")
            for line in resp.iter_lines():
                if not line or not line.startswith("data:"):
                    continue
                data = line[len("data:") :].strip()
                if data == "[DONE]":
                    break
                try:
                    chunk = json.loads(data)
                    delta = chunk["choices"][0]["delta"].get("content")
                except (json.JSONDecodeError, KeyError, IndexError, TypeError):
                    continue
                if delta:
                    yield delta
