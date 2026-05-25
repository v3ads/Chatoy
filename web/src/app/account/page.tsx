"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { isSupabaseConfigured, supabase } from "@/lib/supabase";
import {
  formatCredits,
  getCredits,
  openBillingPortal,
  setAutoRecharge,
  startCheckout,
} from "@/lib/api";
import { initialOf } from "@/lib/useAccount";
import MobileMenu from "@/components/MobileMenu";
import AppMenuLinks from "@/components/AppMenuLinks";

export default function AccountPage() {
  const router = useRouter();
  const [ready, setReady] = useState(!isSupabaseConfigured);
  const [email, setEmail] = useState<string | null>(null);
  const [credits, setCredits] = useState<number | null>(null);
  const [autoRecharge, setAuto] = useState(false);
  const [notice, setNotice] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState("");

  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    if (params.get("billing") === "success")
      setNotice("Payment received — your credits will update shortly.");
    if (params.get("billing") === "cancel") setNotice("Checkout canceled.");

    if (!isSupabaseConfigured || !supabase) {
      setReady(true);
      void load();
      return;
    }
    supabase.auth.getSession().then(({ data }) => {
      if (!data.session) {
        router.replace("/login");
        return;
      }
      setEmail(data.session.user.email ?? null);
      setReady(true);
      void load();
    });
  }, [router]);

  async function load() {
    try {
      const c = await getCredits();
      setCredits(c.credits_balance);
      setAuto(c.auto_recharge_enabled);
    } catch {
      /* leave defaults */
    }
  }

  async function toggleAuto() {
    const next = !autoRecharge;
    setAuto(next);
    try {
      await setAutoRecharge(next);
    } catch (e) {
      setAuto(!next);
      setError((e as Error).message);
    }
  }

  async function checkout(kind: "credits" | "pro") {
    setBusy(kind);
    setError("");
    try {
      const { url } = await startCheckout(kind);
      window.location.href = url;
    } catch (e) {
      setError((e as Error).message);
      setBusy("");
    }
  }

  async function manage() {
    setBusy("portal");
    setError("");
    try {
      const { url } = await openBillingPortal();
      window.location.href = url;
    } catch (e) {
      setError((e as Error).message);
      setBusy("");
    }
  }

  if (!ready) {
    return <div className="p-8 text-text-muted">Loading…</div>;
  }

  return (
    <main className="mx-auto min-h-screen max-w-2xl bg-surface px-4 py-10 sm:px-6 sm:py-12">
      <header className="mb-8 flex items-start justify-between gap-3">
        <div>
          <Link
            href="/chat"
            className="text-sm font-bold uppercase tracking-widest text-accent hover:text-accent-dim"
          >
            ← Back to Architect
          </Link>
          <h1 className="mt-4 text-3xl font-bold text-text-primary sm:text-4xl">
            Profile &amp; billing
          </h1>
        </div>
        <div className="lg:hidden">
          <MobileMenu>{(close) => <AppMenuLinks onNavigate={close} />}</MobileMenu>
        </div>
      </header>

      <section className="flex items-center gap-4 rounded-2xl border border-surface-border bg-surface-card p-6">
        <span className="flex h-12 w-12 items-center justify-center rounded-full bg-accent/15 text-lg font-bold text-accent">
          {initialOf(email)}
        </span>
        <div className="min-w-0">
          <div className="truncate text-base font-medium text-text-primary">
            {email ?? "Your account"}
          </div>
          <div className="text-sm text-text-muted">MythoStack member</div>
        </div>
      </section>

      {notice && <p className="mt-4 text-sm text-accent">{notice}</p>}
      {error && <p className="mt-4 text-sm text-red-400">{error}</p>}

      <section className="mt-6 rounded-2xl border border-surface-border bg-surface-card p-6">
        <div className="flex items-center justify-between gap-4">
          <div>
            <div className="text-[10px] font-bold uppercase tracking-[0.2em] text-text-muted">
              Credits
            </div>
            <div className="mt-1 text-3xl font-bold text-text-primary">
              {formatCredits(credits)}
            </div>
          </div>
          <button
            onClick={() => void checkout("credits")}
            disabled={busy === "credits"}
            className="rounded-lg bg-accent px-5 py-2.5 font-semibold text-surface transition-colors hover:bg-accent-dim disabled:opacity-40"
          >
            {busy === "credits" ? "Opening…" : "Add credits"}
          </button>
        </div>
        <div className="mt-5 flex items-center justify-between border-t border-surface-border pt-4">
          <span className="text-sm text-text-secondary">Auto-recharge when I run low</span>
          <button
            type="button"
            aria-pressed={autoRecharge}
            onClick={() => void toggleAuto()}
            className={`relative h-6 w-11 rounded-full transition-colors ${
              autoRecharge ? "bg-accent" : "bg-surface-border"
            }`}
          >
            <span
              className={`absolute top-0.5 h-5 w-5 rounded-full bg-white transition-transform ${
                autoRecharge ? "translate-x-5" : "translate-x-0.5"
              }`}
            />
          </button>
        </div>
      </section>

      <section className="mt-6 rounded-2xl border border-surface-border bg-surface-card p-6">
        <div className="text-[10px] font-bold uppercase tracking-[0.2em] text-text-muted">
          Subscription
        </div>
        <p className="mt-2 text-sm text-text-secondary">
          Upgrade to Pro for higher limits, or manage your existing plan and payment method.
        </p>
        <div className="mt-4 flex flex-wrap gap-3">
          <button
            onClick={() => void checkout("pro")}
            disabled={busy === "pro"}
            className="rounded-lg bg-accent px-5 py-2.5 font-semibold text-surface transition-colors hover:bg-accent-dim disabled:opacity-40"
          >
            {busy === "pro" ? "Opening…" : "Upgrade to Pro"}
          </button>
          <button
            onClick={() => void manage()}
            disabled={busy === "portal"}
            className="rounded-lg border border-surface-border px-5 py-2.5 font-semibold text-text-primary transition-colors hover:bg-surface-border disabled:opacity-40"
          >
            {busy === "portal" ? "Opening…" : "Manage subscription"}
          </button>
        </div>
      </section>
    </main>
  );
}
