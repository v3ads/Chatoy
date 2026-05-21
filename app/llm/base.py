from __future__ import annotations

from typing import Callable, Iterator, Protocol, runtime_checkable

Message = dict[str, str]  # {"role": "user"|"assistant"|"system", "content": str}


@runtime_checkable
class LLMClient(Protocol):
    """Minimal chat interface the agents depend on.

    Keeping this narrow lets the LangGraph nodes stay agnostic about whether
    they are talking to Anthropic, a streaming tap, or the offline fake.
    """

    def invoke(self, system: str, messages: list[Message]) -> str: ...

    def stream(self, system: str, messages: list[Message]) -> Iterator[str]: ...


class StreamingTap:
    """Wraps an LLMClient so that ``invoke`` streams under the hood.

    Every token produced by the inner client is forwarded to ``sink`` as it is
    generated, while ``invoke`` still returns the full assembled string so node
    logic (e.g. handoff parsing) is unchanged. A fresh ``filter_factory`` is
    created per call so per-message suppression (hiding the handoff marker) does
    not bleed across LLM calls within one graph run.
    """

    def __init__(
        self,
        inner: LLMClient,
        sink: Callable[[str], None],
        filter_factory: Callable[[], "TokenFilter"] | None = None,
    ) -> None:
        self._inner = inner
        self._sink = sink
        self._filter_factory = filter_factory or (lambda: _PassThroughFilter())

    def invoke(self, system: str, messages: list[Message]) -> str:
        token_filter = self._filter_factory()
        parts: list[str] = []
        for token in self._inner.stream(system, messages):
            parts.append(token)
            visible = token_filter.feed(token)
            if visible:
                self._sink(visible)
        tail = token_filter.flush()
        if tail:
            self._sink(tail)
        return "".join(parts)

    def stream(self, system: str, messages: list[Message]) -> Iterator[str]:
        return self._inner.stream(system, messages)


class TokenFilter(Protocol):
    """Transforms a stream of raw tokens into the tokens shown to the user."""

    def feed(self, token: str) -> str: ...

    def flush(self) -> str: ...


class _PassThroughFilter:
    def feed(self, token: str) -> str:
        return token

    def flush(self) -> str:
        return ""
