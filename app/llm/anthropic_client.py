from __future__ import annotations

from typing import Iterator

from app.llm.base import Message


def _coerce_content(content: object) -> str:
    """langchain message content may be a string or a list of content blocks."""
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts: list[str] = []
        for block in content:
            if isinstance(block, str):
                parts.append(block)
            elif isinstance(block, dict) and block.get("type") == "text":
                parts.append(str(block.get("text", "")))
        return "".join(parts)
    return str(content)


class AnthropicLLM:
    """Real LLM client backed by langchain-anthropic's ChatAnthropic.

    Imports are lazy so the package (and the test suite, which uses FakeLLM)
    does not require langchain-anthropic to be installed.
    """

    def __init__(
        self,
        model: str,
        api_key: str,
        temperature: float = 0.7,
        max_tokens: int = 2048,
        timeout: float = 60.0,
        max_retries: int = 2,
    ) -> None:
        from langchain_anthropic import ChatAnthropic

        self._chat = ChatAnthropic(
            model=model,
            anthropic_api_key=api_key,
            temperature=temperature,
            max_tokens=max_tokens,
            default_request_timeout=timeout,
            max_retries=max_retries,
        )

    def _to_lc(self, system: str, messages: list[Message]):
        from langchain_core.messages import (
            AIMessage,
            HumanMessage,
            SystemMessage,
        )

        lc: list = [SystemMessage(content=system)]
        for m in messages:
            role, content = m.get("role"), m.get("content", "")
            if role == "assistant":
                lc.append(AIMessage(content=content))
            elif role == "system":
                lc.append(SystemMessage(content=content))
            else:
                lc.append(HumanMessage(content=content))
        return lc

    def invoke(self, system: str, messages: list[Message]) -> str:
        resp = self._chat.invoke(self._to_lc(system, messages))
        return _coerce_content(resp.content)

    def stream(self, system: str, messages: list[Message]) -> Iterator[str]:
        for chunk in self._chat.stream(self._to_lc(system, messages)):
            text = _coerce_content(chunk.content)
            if text:
                yield text
