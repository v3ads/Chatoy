from __future__ import annotations

from app.config import Settings
from app.services.memory import AssetLog, InMemoryAssetLog
from app.services.voice_profile import (
    InMemoryVoiceProfileStore,
    VoiceProfileStore,
)
from app.session import InMemorySessionStore, SessionStore
from typing import Protocol, runtime_checkable

@runtime_checkable
class CreditStore(Protocol):
    def get(self, user_id: str, email: str | None = None): ...
    def deduct(self, user_id: str, amount: float) -> float: ...
    def add(self, user_id: str, amount: float) -> float: ...
    def set_auto_recharge(self, user_id: str, enabled: bool) -> None: ...
    def set_customer(self, user_id: str, customer_id: str) -> None: ...
    def user_for_customer(self, customer_id: str) -> str | None: ...

class InMemoryCreditStore:
    def __init__(self) -> None:
        self._credits = {}
        self._auto = {}
        self._customer_to_user = {}

    def get(self, user_id: str, email: str | None = None):
        from app.db.models import CreditProfileRow
        # God Mode for Admin
        if email == "vipaymanshalaby@gmail.com":
            return CreditProfileRow(
                user_id=user_id,
                credits_balance=999999.0,
                auto_recharge_enabled=False
            )

        return CreditProfileRow(
            user_id=user_id, 
            credits_balance=self._credits.get(user_id, 10.0),
            auto_recharge_enabled=self._auto.get(user_id, False)
        )

    def deduct(self, user_id: str, amount: float) -> float:
        curr = self._credits.get(user_id, 10.0)
        new = curr - amount
        self._credits[user_id] = new
        return new

    def add(self, user_id: str, amount: float) -> float:
        curr = self._credits.get(user_id, 10.0)
        new = curr + amount
        self._credits[user_id] = new
        return new

    def set_auto_recharge(self, user_id: str, enabled: bool) -> None:
        self._auto[user_id] = enabled

    def set_customer(self, user_id: str, customer_id: str) -> None:
        self._customer_to_user[customer_id] = user_id

    def user_for_customer(self, customer_id: str) -> str | None:
        return self._customer_to_user.get(customer_id)


def build_stores(
    settings: Settings,
) -> tuple[VoiceProfileStore, AssetLog, SessionStore, CreditStore]:
    """Return (voice_store, asset_log, session_store) for the configured backend.

    Uses Postgres (or any SQLAlchemy URL) when ``database_url`` is set, else the
    in-memory stores. The three stores share one engine / connection pool.
    """
    if not settings.use_database:
        return (
            InMemoryVoiceProfileStore(),
            InMemoryAssetLog(),
            InMemorySessionStore(),
            InMemoryCreditStore(),
        )

    from app.db.base import make_engine, make_session_factory
    from app.db.stores import (
        SqlAssetLog,
        SqlCreditStore,
        SqlSessionStore,
        SqlVoiceProfileStore,
    )

    engine = make_engine(settings.database_url)  # type: ignore[arg-type]
    sf = make_session_factory(engine)
    return (
        SqlVoiceProfileStore(sf),
        SqlAssetLog(sf),
        SqlSessionStore(sf),
        SqlCreditStore(sf),
    )
