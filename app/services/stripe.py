from __future__ import annotations

import logging

import stripe
from app.config import Settings
from app.db.factory import CreditStore

logger = logging.getLogger(__name__)


class StripeService:
    def __init__(self, settings: Settings, credit_store: CreditStore):
        self.settings = settings
        self.credit_store = credit_store
        if settings.stripe_api_key:
            stripe.api_key = settings.stripe_api_key

    @property
    def configured(self) -> bool:
        return bool(self.settings.stripe_api_key)

    def create_checkout_session(
        self,
        user_id: str,
        email: str | None,
        kind: str,
        success_url: str,
        cancel_url: str,
    ) -> str | None:
        """Return a Stripe Checkout URL for a credit pack ('credits') or the Pro
        subscription ('pro'), or None if billing isn't configured."""
        if not self.settings.stripe_api_key:
            return None
        if kind == "pro":
            price, mode = self.settings.stripe_pro_price_id, "subscription"
        else:
            price, mode = self.settings.stripe_credit_pack_price_id, "payment"
        if not price:
            return None
        try:
            session = stripe.checkout.Session.create(
                mode=mode,
                line_items=[{"price": price, "quantity": 1}],
                client_reference_id=user_id,
                customer_email=email or None,
                success_url=success_url,
                cancel_url=cancel_url,
            )
            return session.url
        except Exception as exc:  # noqa: BLE001
            logger.warning("Stripe checkout session failed: %s", exc)
            return None

    def create_portal_session(self, email: str | None, return_url: str) -> str | None:
        """Return a Stripe billing-portal URL for the customer with this email,
        or None if there's no such customer / billing isn't configured."""
        if not self.settings.stripe_api_key or not email:
            return None
        try:
            customers = stripe.Customer.list(email=email, limit=1)
            if not customers.data:
                return None
            session = stripe.billing_portal.Session.create(
                customer=customers.data[0].id, return_url=return_url
            )
            return session.url
        except Exception as exc:  # noqa: BLE001
            logger.warning("Stripe portal session failed: %s", exc)
            return None

    def handle_webhook(self, payload: str, sig_header: str):
        if not self.settings.stripe_webhook_secret:
            return {"status": "error", "message": "Webhook secret not configured"}

        try:
            event = stripe.Webhook.construct_event(
                payload, sig_header, self.settings.stripe_webhook_secret
            )
        except ValueError:
            return {"status": "error", "message": "Invalid payload"}
        except stripe.error.SignatureVerificationError:
            return {"status": "error", "message": "Invalid signature"}

        if event["type"] == "checkout.session.completed":
            session = event["data"]["object"]
            self._process_session(session)

        return {"status": "success"}

    def _process_session(self, session):
        user_id = session.get("client_reference_id")
        if not user_id:
            return

        line_items = stripe.checkout.Session.list_line_items(session["id"])
        for item in line_items.data:
            price_id = item.price.id
            if price_id == self.settings.stripe_credit_pack_price_id:
                # Add 50 credits for $10 pack
                self.credit_store.add(user_id, 50.0)
            elif price_id == self.settings.stripe_pro_price_id:
                # Pro plan might come with a starting balance or just unlock unlimited
                # For now, let\'s give them a 100 credit boost
                self.credit_store.add(user_id, 100.0)

    def trigger_auto_recharge(self, user_id: str, customer_id: str):
        """Automatically charge the customer $10 and add 50 credits."""
        if not self.settings.stripe_credit_pack_price_id:
            return

        try:
            # Create an invoice item for the credit pack
            stripe.InvoiceItem.create(
                customer=customer_id,
                price=self.settings.stripe_credit_pack_price_id,
            )
            # Create and pay the invoice immediately
            invoice = stripe.Invoice.create(
                customer=customer_id,
                auto_advance=True,
            )
            stripe.Invoice.pay(invoice.id)
            
            # Add credits to the store
            self.credit_store.add(user_id, 50.0)
            return True
        except Exception as e:
            print(f"Auto-recharge failed for {user_id}: {e}")
            return False
