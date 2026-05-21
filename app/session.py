from __future__ import annotations

from typing import Protocol

from app.agents.state import AgentState


class SessionStore(Protocol):
    """Conversation state keyed by session id.

    Keeps chat stateless from the client's perspective: it sends a session_id
    and a message; the store threads ``AgentState`` across turns.
    """

    def get(self, session_id: str) -> AgentState: ...

    def set(self, session_id: str, state: AgentState) -> None: ...

    def reset(self, session_id: str) -> None: ...


class InMemorySessionStore:
    """Default store. Swap for the SQL-backed store via the database config."""

    def __init__(self) -> None:
        self._sessions: dict[str, AgentState] = {}

    def get(self, session_id: str) -> AgentState:
        return dict(self._sessions.get(session_id, {}))

    def set(self, session_id: str, state: AgentState) -> None:
        self._sessions[session_id] = dict(state)

    def reset(self, session_id: str) -> None:
        self._sessions.pop(session_id, None)
