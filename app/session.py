from __future__ import annotations

from app.agents.state import AgentState


class SessionStore:
    """In-memory conversation state keyed by session id.

    Keeps the chat stateless from the client's perspective: it sends a
    session_id and a message; the server threads ``AgentState`` across turns.
    Swap for Redis/Postgres in production.
    """

    def __init__(self) -> None:
        self._sessions: dict[str, AgentState] = {}

    def get(self, session_id: str) -> AgentState:
        return self._sessions.get(session_id, {})

    def set(self, session_id: str, state: AgentState) -> None:
        self._sessions[session_id] = state

    def reset(self, session_id: str) -> None:
        self._sessions.pop(session_id, None)
