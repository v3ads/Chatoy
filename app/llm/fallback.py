from __future__ import annotations

import logging
from typing import Iterator

from app.llm.base import LLMClient, Message

logger = logging.getLogger(__name__)


class FallbackLLM:
    """Tries ``primary``; if it errors before producing output, uses ``fallback``.

    For streaming, the fallback only kicks in if the primary fails before the
    first token (the typical "model didn't respond" case — connection/timeout/
    HTTP error). A mid-stream failure is logged and ends the stream, since
    already-emitted tokens can't be retracted.
    """

    def __init__(self, primary: LLMClient, fallback: LLMClient) -> None:
        self._primary = primary
        self._fallback = fallback

    def invoke(self, system: str, messages: list[Message]) -> str:
        try:
            return self._primary.invoke(system, messages)
        except Exception as exc:  # noqa: BLE001 — any primary failure -> fallback
            logger.warning("Primary model failed (%s); falling back.", exc)
            return self._fallback.invoke(system, messages)

    def stream(self, system: str, messages: list[Message]) -> Iterator[str]:
        gen = self._primary.stream(system, messages)
        try:
            first = next(gen)
        except StopIteration:
            return
        except Exception as exc:  # noqa: BLE001 — failed before first token
            logger.warning("Primary model failed pre-stream (%s); falling back.", exc)
            yield from self._fallback.stream(system, messages)
            return

        yield first
        try:
            yield from gen
        except Exception as exc:  # noqa: BLE001 — mid-stream; can't retract tokens
            logger.warning("Primary model failed mid-stream (%s); ending stream.", exc)
