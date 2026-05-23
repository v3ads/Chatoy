from __future__ import annotations

from app.config import Settings
from app.db.factory import CreditStore

class StripeService:
    def __init__(self, settings: Settings, credit_store: CreditStore):
        self.settings = settings
        self.credit_store = credit_store

    def handle_webhook(self, payload: str, sig_header: str):
        return {"status": "error", "message": "Stripe integration disabled"}

    def _process_session(self, session):
        pass

    def trigger_auto_recharge(self, user_id: str, customer_id: str):
        return False
