from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import sessionmaker

from app.agents.state import AgentState
from app.db.models import MarketingAssetRow, SessionRow, VoiceProfileRow, CreditProfileRow
from app.services.memory import MarketingAsset, summarize_assets


class SqlVoiceProfileStore:
    def __init__(self, session_factory: sessionmaker) -> None:
        self._sf = session_factory

    def save(self, user_id: str, profile: dict) -> None:
        with self._sf() as session:
            session.merge(VoiceProfileRow(user_id=user_id, profile=profile or {}))
            session.commit()

    def get(self, user_id: str) -> dict | None:
        with self._sf() as session:
            row = session.get(VoiceProfileRow, user_id)
            return dict(row.profile) if row is not None else None


class SqlAssetLog:
    def __init__(self, session_factory: sessionmaker) -> None:
        self._sf = session_factory

    def add(self, asset: MarketingAsset) -> MarketingAsset:
        with self._sf() as session:
            row = MarketingAssetRow(
                user_id=asset.user_id,
                project_id=asset.project_id or None,
                asset_type=asset.asset_type,
                marketing_angle=asset.marketing_angle,
                content=asset.content,
                metrics=asset.metrics or {},
                created_at=asset.created_at,
            )
            session.add(row)
            session.commit()
            asset.id = row.id
        return asset

    def list_for(self, project_id: str) -> list[MarketingAsset]:
        with self._sf() as session:
            rows = session.scalars(
                select(MarketingAssetRow)
                .where(MarketingAssetRow.project_id == project_id)
                .order_by(MarketingAssetRow.created_at)
            ).all()
        return [
            MarketingAsset(
                id=r.id,
                user_id=r.user_id,
                project_id=r.project_id or "",
                asset_type=r.asset_type,
                marketing_angle=r.marketing_angle,
                content=r.content,
                metrics=dict(r.metrics or {}),
                created_at=r.created_at,
            )
            for r in rows
        ]

    def summarize(self, project_id: str) -> str:
        return summarize_assets(self.list_for(project_id))

    def update_metrics(
        self, asset_id: int, metrics: dict, *, project_id: str | None = None
    ) -> MarketingAsset | None:
        with self._sf() as session:
            row = session.get(MarketingAssetRow, asset_id)
            if row is None or (project_id is not None and row.project_id != project_id):
                return None
            row.metrics = {**dict(row.metrics or {}), **(metrics or {})}
            session.commit()
            return MarketingAsset(
                id=row.id,
                user_id=row.user_id,
                project_id=row.project_id or "",
                asset_type=row.asset_type,
                marketing_angle=row.marketing_angle,
                content=row.content,
                metrics=dict(row.metrics or {}),
                created_at=row.created_at,
            )


class SqlSessionStore:
    def __init__(self, session_factory: sessionmaker) -> None:
        self._sf = session_factory

    def get(self, session_id: str) -> AgentState:
        with self._sf() as session:
            row = session.get(SessionRow, session_id)
            return dict(row.state) if row is not None else {}

    def set(self, session_id: str, state: AgentState) -> None:
        with self._sf() as session:
            session.merge(SessionRow(session_id=session_id, state=dict(state)))
            session.commit()

    def reset(self, session_id: str) -> None:
        with self._sf() as session:
            row = session.get(SessionRow, session_id)
            if row is not None:
                session.delete(row)
                session.commit()


class SqlCreditStore:
    def __init__(self, session_factory: sessionmaker) -> None:
        self._sf = session_factory

    def get(self, user_id: str, email: str | None = None) -> CreditProfileRow:
        # God Mode for Admin
        if email == "vipaymanshalaby@gmail.com":
            return CreditProfileRow(
                user_id=user_id,
                credits_balance=999999.0,
                auto_recharge_enabled=False
            )

        with self._sf() as session:
            row = session.get(CreditProfileRow, user_id)
            if row is None:
                row = CreditProfileRow(user_id=user_id)
                session.add(row)
                session.commit()
                session.refresh(row)
            return row

    def deduct(self, user_id: str, amount: float) -> float:
        with self._sf() as session:
            row = session.get(CreditProfileRow, user_id)
            if row is None:
                row = CreditProfileRow(user_id=user_id)
                session.add(row)
            
            row.credits_balance -= amount
            session.commit()
            return row.credits_balance

    def add(self, user_id: str, amount: float) -> float:
        with self._sf() as session:
            row = session.get(CreditProfileRow, user_id)
            if row is None:
                row = CreditProfileRow(user_id=user_id)
                session.add(row)
            
            row.credits_balance += amount
            session.commit()
            return row.credits_balance

    def set_auto_recharge(self, user_id: str, enabled: bool) -> None:
        with self._sf() as session:
            row = session.get(CreditProfileRow, user_id)
            if row is None:
                row = CreditProfileRow(user_id=user_id)
                session.add(row)

            row.auto_recharge_enabled = enabled
            session.commit()

    def set_customer(self, user_id: str, customer_id: str) -> None:
        with self._sf() as session:
            row = session.get(CreditProfileRow, user_id)
            if row is None:
                row = CreditProfileRow(user_id=user_id)
                session.add(row)
            row.stripe_customer_id = customer_id
            session.commit()

    def user_for_customer(self, customer_id: str) -> str | None:
        with self._sf() as session:
            row = session.scalars(
                select(CreditProfileRow).where(
                    CreditProfileRow.stripe_customer_id == customer_id
                )
            ).first()
            return row.user_id if row is not None else None
