from __future__ import annotations

from langgraph.graph import END, StateGraph

from app.agents.architect import make_architect_node
from app.agents.writer import make_writer_node
from app.agents.state import AgentState
from app.llm.base import LLMClient
from app.services.memory import AssetLog
from app.services.rag import FrameworkRetriever

ARCHITECT = "growth_architect"
WRITER = "asset_writer"


def build_graph(
    architect_llm: LLMClient,
    writer_llm: LLMClient | None = None,
    *,
    memory: AssetLog | None = None,
    rag: FrameworkRetriever | None = None,
):
    """Compile the two-agent state machine.

    Flow per user turn:
      - entry routes by phase: ``write``/``refine`` skip straight to the writer,
        otherwise the Architect runs.
      - Architect either ends the turn with a question (``diagnose``) or, on handoff,
        flows into the writer in the same run.
      - The writer always ends the turn.
    """
    writer_llm = writer_llm or architect_llm

    workflow = StateGraph(AgentState)
    workflow.add_node(ARCHITECT, make_architect_node(architect_llm, memory=memory))
    workflow.add_node(WRITER, make_writer_node(writer_llm, rag=rag))

    def entry_router(state: AgentState) -> str:
        return WRITER if state.get("next_step") in ("write", "refine") else ARCHITECT

    workflow.set_conditional_entry_point(
        entry_router, {ARCHITECT: ARCHITECT, WRITER: WRITER}
    )

    def after_architect(state: AgentState) -> str:
        return "write" if state.get("next_step") == "write" else "end"

    workflow.add_conditional_edges(ARCHITECT, after_architect, {"write": WRITER, "end": END})
    workflow.add_edge(WRITER, END)

    return workflow.compile()
