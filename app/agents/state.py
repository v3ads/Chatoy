from __future__ import annotations

from typing_extensions import TypedDict


class Message(TypedDict):
    role: str  # "user" | "assistant" | "system"
    content: str


# Phases that drive routing through the graph.
#   "diagnose" — the CRO is still interviewing the user.
#   "write"    — a strategy is locked; the Shepherd should produce the asset.
#   "refine"   — an asset exists; the Shepherd should revise it from feedback.
Phase = str


class AgentState(TypedDict, total=False):
    """Shared state threaded through the LangGraph run.

    LangGraph merges each node's returned dict into this state by key (last
    write wins), so nodes return the full updated ``messages`` list rather than
    a delta.
    """

    messages: list[Message]
    user_id: str
    business_profile: dict
    voice_profile: str
    current_strategy: dict
    retrieved_frameworks: list[str]
    next_step: Phase
