from __future__ import annotations

import json

from app.agents.parsing import extract_first_json
from app.llm.base import LLMClient
from app.services.projects import merge_profile

# Mentions "business facts" so the offline FakeLLM can no-op cleanly (it won't
# emit JSON, the extractor returns the profile unchanged).
_EXTRACT_PROMPT = """You maintain a structured profile of a business by reading
its founder's chat messages. From the latest message, extract only NEW, durable
business facts worth remembering long-term — e.g. core_product, target_audience,
offer, price_point, primary_goal, channels, positioning, constraints, brand_voice.

Rules:
- Output ONLY a single JSON object (no prose, no code fences) of facts to store.
- Use concise snake_case keys and short string values.
- Include a key ONLY if the message clearly states it. If nothing durable is
  stated, output {}.

Currently known about this business:
{known}
"""


def evolve_business_profile(
    llm: LLMClient, current_profile: dict, latest_user_message: str
) -> dict:
    """Best-effort: pull durable business facts from the latest message and merge
    them into the stored profile. Returns the (possibly unchanged) merged dict;
    never raises."""
    text = (latest_user_message or "").strip()
    if not text:
        return dict(current_profile or {})
    try:
        known = json.dumps(current_profile or {}, indent=2)
        system = _EXTRACT_PROMPT.format(known=known)
        raw = llm.invoke(system, [{"role": "user", "content": text}])
        facts = extract_first_json(raw) or {}
    except Exception:  # noqa: BLE001 — profile evolution must never break a turn
        return dict(current_profile or {})
    if not isinstance(facts, dict) or not facts:
        return dict(current_profile or {})
    return merge_profile(current_profile, facts)
