from __future__ import annotations

import json

HANDOFF_MARKER = "PROMPT_HANDOFF:"


def extract_first_json(text: str) -> dict | None:
    """Return the first balanced ``{...}`` object in ``text`` as a dict.

    Tolerates braces/quotes inside strings and trailing prose after the object.
    Returns None if nothing parseable is found.
    """
    start = text.find("{")
    if start == -1:
        return None

    depth = 0
    in_str = False
    escaped = False
    for i in range(start, len(text)):
        c = text[i]
        if in_str:
            if escaped:
                escaped = False
            elif c == "\\":
                escaped = True
            elif c == '"':
                in_str = False
            continue
        if c == '"':
            in_str = True
        elif c == "{":
            depth += 1
        elif c == "}":
            depth -= 1
            if depth == 0:
                blob = text[start : i + 1]
                try:
                    parsed = json.loads(blob)
                except json.JSONDecodeError:
                    return None
                return parsed if isinstance(parsed, dict) else None
    return None


def parse_handoff(text: str) -> tuple[dict | None, str]:
    """Split a CRO reply into (strategy, user_visible_text).

    If the handoff marker is present, the strategy is the JSON that follows it
    (an empty dict if the JSON is malformed) and the visible text is everything
    before the marker. If the marker is absent, strategy is None and the full
    (stripped) text is returned.
    """
    idx = text.find(HANDOFF_MARKER)
    if idx == -1:
        return None, text.strip()
    visible = text[:idx].strip()
    strategy = extract_first_json(text[idx + len(HANDOFF_MARKER) :]) or {}
    return strategy, visible


class MarkerFilter:
    """Streaming filter that suppresses everything from ``marker`` onward.

    Used so the user never sees the raw ``PROMPT_HANDOFF: {...}`` JSON while
    tokens stream. Holds back a short tail each step so a marker split across
    token boundaries is still caught.
    """

    def __init__(self, marker: str = HANDOFF_MARKER) -> None:
        self._marker = marker
        self._buffer = ""
        self._suppressed = False

    def feed(self, token: str) -> str:
        if self._suppressed:
            return ""
        self._buffer += token
        idx = self._buffer.find(self._marker)
        if idx != -1:
            emit = self._buffer[:idx]
            self._suppressed = True
            self._buffer = ""
            return emit
        # Keep the last (len(marker)-1) chars in case the marker spans tokens.
        keep = len(self._marker) - 1
        if keep and len(self._buffer) > keep:
            emit = self._buffer[:-keep]
            self._buffer = self._buffer[-keep:]
            return emit
        return ""

    def flush(self) -> str:
        if self._suppressed:
            return ""
        emit, self._buffer = self._buffer, ""
        return emit
