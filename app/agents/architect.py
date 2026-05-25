from __future__ import annotations

import json
from typing import Callable

from app.agents.parsing import parse_handoff, strip_inline_markdown
from app.agents.prompts import cro_system_prompt
from app.agents.state import AgentState
from app.llm.base import LLMClient
from app.services.memory import AssetLog
from app.services.rag import FrameworkRetriever


def make_architect_node(
    llm: LLMClient,
    memory: AssetLog | None = None,
    rag: FrameworkRetriever | None = None,
    recall=None,
) -> Callable[[AgentState], dict]:
    """Build the Growth Architect node.

    Interviews the user. If it locks a strategy it strips the handoff marker
    from the visible reply, stores the parsed strategy, and routes to the
    writer; otherwise it stays in ``diagnose`` and the turn ends with a
    question.
    """

    def architect_node(state: AgentState) -> dict:
        messages = state.get("messages", [])
        profile = state.get("business_profile", {})
        project_id = state.get("project_id") or ""

        digest = ""
        if memory is not None and project_id:
            digest = memory.summarize(project_id)

        last_user = next(
            (m["content"] for m in reversed(messages) if m.get("role") == "user"),
            "",
        )
        query = f"{json.dumps(profile)} {last_user}".strip()

        knowledge: list[str] = []
        search = getattr(rag, "search", None)
        if search is not None:
            knowledge = search(query, k=3)

        recalled: list[str] = []
        if recall is not None and project_id:
            recalled = recall.recall(project_id, query, k=2)

        system = cro_system_prompt(
            profile,
            past_assets_digest=digest,
            knowledge=knowledge,
            recalled=recalled,
            website_content=state.get("website_content", ""),
        )
        raw = llm.invoke(system, messages)

        strategy, visible = parse_handoff(raw)
        visible = strip_inline_markdown(visible)
        new_messages = messages + [{"role": "assistant", "content": visible}]

        if strategy is not None:
            return {
                "messages": new_messages,
                "current_strategy": strategy,
                "next_step": "write",
            }
        return {"messages": new_messages, "next_step": "diagnose"}

    return architect_node
