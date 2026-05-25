from __future__ import annotations

import asyncio
from typing import AsyncIterator

from app.agents.graph import build_graph
from app.agents.parsing import HANDOFF_MARKER, MarkdownStreamFilter, MarkerFilter
from app.agents.state import AgentState
from app.llm.base import ChainFilter, LLMClient, StreamingTap
from app.services.memory import AssetLog
from app.services.rag import FrameworkRetriever
from app.db.factory import CreditStore


class Orchestrator:
    """Runs a single conversational turn through the two-agent graph.

    Holds the compiled graph plus the service dependencies. Exposes a buffered
    ``run`` and a token-streaming ``stream``; both share the exact same routing
    logic (the stream wraps each LLM in a StreamingTap rather than reimplementing
    the graph).
    """

    def __init__(
        self,
        cro_llm: LLMClient,
        shepherd_llm: LLMClient | None = None,
        *,
        memory: AssetLog | None = None,
        rag: FrameworkRetriever | None = None,
        recall=None,
        credits: CreditStore | None = None,
    ) -> None:
        self._cro_llm = cro_llm
        self._shepherd_llm = shepherd_llm or cro_llm
        self._memory = memory
        self._rag = rag
        self._recall = recall
        self._credits = credits
        self._graph = build_graph(
            self._cro_llm, self._shepherd_llm, memory=memory, rag=rag, recall=recall
        )

    def _check_credits(self, state: AgentState) -> None:
        if self._credits is None:
            return
        user_id = state.get("user_id")
        if not user_id:
            return
        
        # We need to get the email from the state or context if possible
        # For now, we'll check the state metadata
        email = state.get("user_email")
        
        row = self._credits.get(user_id, email=email)
        if row.credits_balance <= 0:
            raise ValueError("Insufficient credits to run campaign engine.")

    def run(self, state: AgentState) -> AgentState:
        self._check_credits(state)
        return self._graph.invoke(state)

    async def stream(
        self, state: AgentState
    ) -> AsyncIterator[tuple[str, object]]:
        """Yield ("token", text) events as the turn is generated, then a single
        ("final", state) event with the completed state (or ("error", msg))."""
        try:
            self._check_credits(state)
        except Exception as e:
            yield "error", str(e)
            return

        queue: asyncio.Queue[tuple[str, object]] = asyncio.Queue()
        loop = asyncio.get_running_loop()

        def sink(text: str) -> None:
            if text:
                loop.call_soon_threadsafe(queue.put_nowait, ("token", text))

        def filter_factory() -> ChainFilter:
            # Hide the handoff marker, then strip Markdown tells from the stream.
            return ChainFilter(MarkerFilter(HANDOFF_MARKER), MarkdownStreamFilter())

        cro_tap = StreamingTap(self._cro_llm, sink, filter_factory)
        shepherd_tap = StreamingTap(self._shepherd_llm, sink, filter_factory)
        graph = build_graph(
            cro_tap, shepherd_tap, memory=self._memory, rag=self._rag, recall=self._recall
        )

        def run_graph() -> None:
            try:
                final = graph.invoke(state)
                loop.call_soon_threadsafe(queue.put_nowait, ("final", final))
            except Exception as exc:  # surface to the client, then end
                loop.call_soon_threadsafe(queue.put_nowait, ("error", str(exc)))
            finally:
                loop.call_soon_threadsafe(queue.put_nowait, ("__end__", None))

        task = asyncio.create_task(asyncio.to_thread(run_graph))
        try:
            while True:
                kind, payload = await queue.get()
                if kind == "__end__":
                    break
                yield kind, payload
        finally:
            await task
