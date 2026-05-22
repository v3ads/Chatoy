from __future__ import annotations

from typing import Callable

from app.agents.parsing import parse_handoff
from app.agents.prompts import cro_system_prompt
from app.agents.state import AgentState
from app.llm.base import LLMClient
from app.services.memory import AssetLog


def make_architect_node(
    llm: LLMClient, memory: AssetLog | None = None
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

        digest = ""
        user_id = state.get("user_id")
        if memory is not None and user_id:
            digest = memory.summarize(user_id)

        system = cro_system_prompt(profile, past_assets_digest=digest)
        raw = llm.invoke(system, messages)

        strategy, visible = parse_handoff(raw)
        new_messages = messages + [{"role": "assistant", "content": visible}]

        if strategy is not None:
            return {
                "messages": new_messages,
                "current_strategy": strategy,
                "next_step": "write",
            }
        return {"messages": new_messages, "next_step": "diagnose"}

    return architect_node
