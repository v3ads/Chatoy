from __future__ import annotations

import logging

from app.config import Settings
from app.llm.base import LLMClient
from app.llm.fake import FakeLLM

logger = logging.getLogger(__name__)


def build_llm(settings: Settings, role: str = "architect") -> LLMClient:
    """Return the right client for a role, falling back to the offline fake.

    With no API key (or CHATOY_USE_FAKE_LLM=true) the app still boots and is
    fully demoable using deterministic offline responses.
    """
    if settings.offline:
        logger.warning(
            "No Anthropic API key (or fake forced) — using offline FakeLLM for role=%s",
            role,
        )
        return FakeLLM()

    from app.llm.anthropic_client import AnthropicLLM

    return AnthropicLLM(
        model=settings.model_for(role),
        api_key=settings.anthropic_api_key,  # type: ignore[arg-type]
        temperature=settings.temperature,
        max_tokens=settings.max_tokens,
    )
