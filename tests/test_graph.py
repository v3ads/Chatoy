from app.agents.graph import build_graph
from app.llm.fake import FakeLLM
from app.services.memory import InMemoryAssetLog
from app.services.rag import InMemoryFrameworkRetriever


def _graph():
    return build_graph(
        FakeLLM(handoff_after=2),
        memory=InMemoryAssetLog(),
        rag=InMemoryFrameworkRetriever(),
    )


def test_first_turn_diagnoses_with_a_question():
    graph = _graph()
    state = {"messages": [{"role": "user", "content": "I need help with marketing"}]}
    out = graph.invoke(state)
    assert out["next_step"] == "diagnose"
    assert out["messages"][-1]["role"] == "assistant"
    assert "current_strategy" not in out
    assert "?" in out["messages"][-1]["content"]


def test_handoff_turn_routes_into_writer_and_writes_copy():
    graph = _graph()
    # Two user turns triggers the FakeLLM Architect handoff.
    state = {
        "messages": [
            {"role": "user", "content": "I run a SaaS"},
            {"role": "assistant", "content": "What outcome matters most?"},
            {"role": "user", "content": "More trial signups from email"},
        ]
    }
    out = graph.invoke(state)
    assert out["next_step"] == "refine"
    assert out["current_strategy"]["asset_type"] == "email_promo"
    # Two assistant messages were appended: Architect preface + Writer copy.
    assert out["messages"][-2]["role"] == "assistant"  # CRO preface
    assert out["messages"][-1]["role"] == "assistant"  # written asset
    # Handoff marker must never leak into the visible Architect message.
    assert "PROMPT_HANDOFF" not in out["messages"][-2]["content"]
    assert "Subject:" in out["messages"][-1]["content"]
    # RAG frameworks were attached for the asset type.
    assert out["retrieved_frameworks"]


def test_refine_phase_skips_architect_and_goes_straight_to_writer():
    graph = _graph()
    state = {
        "messages": [
            {"role": "user", "content": "Make the subject line punchier"},
        ],
        "current_strategy": {"asset_type": "email_promo"},
        "next_step": "refine",
    }
    out = graph.invoke(state)
    # Exactly one assistant message appended (the writer), Architect was skipped.
    assert out["messages"][-1]["role"] == "assistant"
    assert len(out["messages"]) == 2
    assert out["next_step"] == "refine"
