from __future__ import annotations

import json
import re
from typing import Callable, Iterator

from app.llm.base import Message

_DEFAULT_PROFILE = {
    "sentence_structure": "short, punchy, varied",
    "avg_paragraph_length": "2-3 sentences",
    "humor_idioms": "occasional dry humor",
    "capitalization_habits": "standard",
    "jargon_level": "low",
    "tone": "direct and warm",
    "signature_phrases": ["here's the thing", "let's get into it"],
}


class FakeLLM:
    """Deterministic, offline stand-in for a real model.

    Used for tests, CI, and local demos without an API key. Behaviour is
    inferred from the system prompt so the same fake can play every role:

    - Asset Engine -> returns sample copy.
    - Voice analysis    -> returns a JSON stylistic fingerprint.
    - Growth Architect (default)     -> asks one question, then hands off once it has
      collected at least ``handoff_after`` user turns.

    Tests can fully override behaviour by passing ``scripted`` (popped in
    order) or a ``responder`` callable.
    """

    def __init__(
        self,
        scripted: list[str] | None = None,
        responder: Callable[[str, list[Message]], str] | None = None,
        handoff_after: int = 2,
    ) -> None:
        self._scripted = list(scripted or [])
        self._responder = responder
        self._handoff_after = handoff_after

    def invoke(self, system: str, messages: list[Message]) -> str:
        if self._scripted:
            return self._scripted.pop(0)
        if self._responder:
            return self._responder(system, messages)
        return self._default(system, messages)

    def stream(self, system: str, messages: list[Message]) -> Iterator[str]:
        text = self.invoke(system, messages)
        # Emit word-by-word (keeping whitespace) to exercise streaming paths.
        for token in re.findall(r"\S+\s*|\s+", text):
            yield token

    def _default(self, system: str, messages: list[Message]) -> str:
        if "Asset Engine" in system:
            return (
                "Subject: The 3pm slump killer your team will thank you for\n\n"
                "Most afternoons fall apart at the exact same moment. Here's how "
                "to take that hour back — without another meeting.\n\n"
                "[Fake offline copy. Set MYTHOSTACK_ANTHROPIC_API_KEY for real output.]"
            )
        if "stylistic fingerprint" in system:
            return json.dumps(_DEFAULT_PROFILE)
        # Growth Architect behaviour.
        user_turns = [m for m in messages if m.get("role") == "user"]
        if len(user_turns) >= self._handoff_after:
            return (
                "Great — I've got a clear picture now. Let's build this.\n"
                'PROMPT_HANDOFF: {"asset_type": "email_promo", '
                '"marketing_angle": "reclaim the afternoon productivity dip"}'
            )
        return "Got it. What's the single most important outcome you want this asset to drive?"
