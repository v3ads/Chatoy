from __future__ import annotations

from typing import Callable

from app.agents.prompts import shepherd_system_prompt
from app.agents.state import AgentState, Message
from app.llm.base import LLMClient
from app.services.rag import FrameworkRetriever

_WRITE_INSTRUCTION = "Write the asset now, following the strategy and voice profile."


def _ensure_user_turn(messages: list[Message]) -> list[Message]:
    """Anthropic requires the final turn to be a user message; append one if
    the conversation currently ends on an assistant turn (e.g. right after the
    Architect handoff)."""
    if messages and messages[-1].get("role") == "user":
        return messages
    return messages + [{"role": "user", "content": _WRITE_INSTRUCTION}]


def make_writer_node(
    llm: LLMClient, rag: FrameworkRetriever | None = None
) -> Callable[[AgentState], dict]:
    """Build the Asset Engine (copywriter) node."""

    def writer_node(state: AgentState) -> dict:
        strategy = state.get("current_strategy", {})
        voice = state.get("voice_profile", "")
        messages = state.get("messages", [])

        frameworks: list[str] = []
        asset_type = strategy.get("asset_type") if isinstance(strategy, dict) else None
        if rag is not None and asset_type:
            query = " ".join(
                str(strategy.get(key, ""))
                for key in ("asset_type", "marketing_angle", "audience", "primary_goal")
            ).strip()
            search = getattr(rag, "search", None)
            frameworks = (
                search(query, k=3, asset_type=asset_type)
                if search
                else rag.retrieve(asset_type, k=3)
            )

        system = shepherd_system_prompt(strategy, voice, frameworks)
        copy = llm.invoke(system, _ensure_user_turn(messages))

        new_messages = messages + [{"role": "assistant", "content": copy}]
        return {
            "messages": new_messages,
            "retrieved_frameworks": frameworks,
            "next_step": "refine",
        }

    return writer_node
