from __future__ import annotations

import json
from typing import Protocol

from app.agents.parsing import extract_first_json
from app.llm.base import LLMClient

# The phrase "stylistic fingerprint" is also how the offline FakeLLM recognises
# a voice-analysis request, so keep it in this prompt.
VOICE_ANALYSIS_PROMPT = """You are a linguistic profiler. Analyze the writing
sample(s) below and produce the author's stylistic fingerprint.

Assess: sentence structure and length variance, average paragraph length,
use of humor/idioms, capitalization habits, punctuation quirks, level of
professional jargon, overall tone, and any signature phrases.

Output ONLY a single JSON object (no prose, no code fences) with these keys:
  "sentence_structure", "avg_paragraph_length", "humor_idioms",
  "capitalization_habits", "punctuation", "jargon_level", "tone",
  "signature_phrases" (array of strings)."""


def analyze_voice(llm: LLMClient, samples: list[str]) -> dict:
    """Run the offline/online voice-cloning analysis over the user's samples.

    Returns the structured stylistic fingerprint as a dict (empty on failure).
    """
    cleaned = [s.strip() for s in samples if s and s.strip()]
    if not cleaned:
        return {}
    joined = "\n\n---\n\n".join(cleaned)
    raw = llm.invoke(VOICE_ANALYSIS_PROMPT, [{"role": "user", "content": joined}])
    return extract_first_json(raw) or {}


def render_voice_profile(profile: dict) -> str:
    """Render a fingerprint dict into the string injected into the writer."""
    if not profile:
        return ""
    lines = []
    for key, value in profile.items():
        label = key.replace("_", " ").title()
        if isinstance(value, (list, tuple)):
            value = ", ".join(str(v) for v in value)
        lines.append(f"- {label}: {value}")
    return "Write in this voice:\n" + "\n".join(lines)


class VoiceProfileStore(Protocol):
    def save(self, user_id: str, profile: dict) -> None: ...

    def get(self, user_id: str) -> dict | None: ...


class InMemoryVoiceProfileStore:
    """Default store. Swap for a Postgres-backed implementation in production."""

    def __init__(self) -> None:
        self._data: dict[str, dict] = {}

    def save(self, user_id: str, profile: dict) -> None:
        self._data[user_id] = dict(profile)

    def get(self, user_id: str) -> dict | None:
        profile = self._data.get(user_id)
        return dict(profile) if profile is not None else None
