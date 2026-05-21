from __future__ import annotations

import asyncio
from typing import AsyncIterator

from app.agents.graph import build_graph
from app.agents.parsing import HANDOFF_MARKER, MarkerFilter
from app.agents.state import AgentState
from app.llm.base import LLMClient, StreamingTap
from app.services.memory import AssetLog
from app.services.rag import FrameworkRetriever


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
    ) -> None:
        self._cro_llm = cro_llm
        self._shepherd_llm = shepherd_llm or cro_llm
        self._memory = memory
        self._rag = rag
        self._graph = build_graph(
            self._cro_llm, self._shepherd_llm, memory=memory, rag=rag
        )

    def run(self, state: AgentState) -> AgentState:
        return self._graph.invoke(state)

    async def stream(
        self, state: AgentState
    ) -> AsyncIterator[tuple[str, object]]:
        """Yield ("token", text) events as the turn is generated, then a single
        ("final", state) event with the completed state (or ("error", msg))."""
        queue: asyncio.Queue[tuple[str, object]] = asyncio.Queue()
        loop = asyncio.get_running_loop()

        def sink(text: str) -> None:
            if text:
                loop.call_soon_threadsafe(queue.put_nowait, ("token", text))

        def filter_factory() -> MarkerFilter:
            return MarkerFilter(HANDOFF_MARKER)

        cro_tap = StreamingTap(self._cro_llm, sink, filter_factory)
        shepherd_tap = StreamingTap(self._shepherd_llm, sink, filter_factory)
        graph = build_graph(
            cro_tap, shepherd_tap, memory=self._memory, rag=self._rag
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
