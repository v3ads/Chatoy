from __future__ import annotations

from langgraph.graph import END, StateGraph

from app.agents.cro import make_cro_node
from app.agents.shepherd import make_shepherd_node
from app.agents.state import AgentState
from app.llm.base import LLMClient
from app.services.memory import AssetLog
from app.services.rag import FrameworkRetriever

CRO = "chief_revenue_officer"
SHEPHERD = "project_shepherd"


def build_graph(
    cro_llm: LLMClient,
    shepherd_llm: LLMClient | None = None,
    *,
    memory: AssetLog | None = None,
    rag: FrameworkRetriever | None = None,
):
    """Compile the two-agent state machine.

    Flow per user turn:
      - entry routes by phase: ``write``/``refine`` skip straight to the writer,
        otherwise the CRO runs.
      - CRO either ends the turn with a question (``diagnose``) or, on handoff,
        flows into the writer in the same run.
      - The writer always ends the turn.
    """
    shepherd_llm = shepherd_llm or cro_llm

    workflow = StateGraph(AgentState)
    workflow.add_node(CRO, make_cro_node(cro_llm, memory=memory))
    workflow.add_node(SHEPHERD, make_shepherd_node(shepherd_llm, rag=rag))

    def entry_router(state: AgentState) -> str:
        return SHEPHERD if state.get("next_step") in ("write", "refine") else CRO

    workflow.set_conditional_entry_point(
        entry_router, {CRO: CRO, SHEPHERD: SHEPHERD}
    )

    def after_cro(state: AgentState) -> str:
        return "write" if state.get("next_step") == "write" else "end"

    workflow.add_conditional_edges(CRO, after_cro, {"write": SHEPHERD, "end": END})
    workflow.add_edge(SHEPHERD, END)

    return workflow.compile()
