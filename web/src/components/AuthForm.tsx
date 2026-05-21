"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState } from "react";
import { isSupabaseConfigured, supabase } from "@/lib/supabase";

type Mode = "signin" | "signup";

export default function AuthForm() {
  const router = useRouter();
  const [mode, setMode] = useState<Mode>("signin");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setError("");
    setNotice("");
    if (!supabase) {
      setError("Login isn't configured yet. Set NEXT_PUBLIC_SUPABASE_URL and NEXT_PUBLIC_SUPABASE_ANON_KEY.");
      return;
    }
    setBusy(true);
    try {
      if (mode === "signup") {
        const { data, error } = await supabase.auth.signUp({ email, password });
        if (error) throw error;
        if (data.session) {
          router.replace("/chat");
        } else {
          setNotice("Check your email to confirm your account, then log in.");
          setMode("signin");
        }
      } else {
        const { error } = await supabase.auth.signInWithPassword({ email, password });
        if (error) throw error;
        router.replace("/chat");
      }
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="w-full max-w-sm">
      <h1 className="text-2xl font-semibold tracking-tight">
        {mode === "signin" ? "Log in" : "Create your account"}
      </h1>
      <p className="mt-1 text-sm text-text-muted">
        to <span className="text-text-secondary">Mytho<span className="text-accent">Stack</span></span>
      </p>

      {!isSupabaseConfigured && (
        <p className="mt-4 rounded-md border border-yellow-900/60 bg-yellow-950/30 px-3 py-2 text-sm text-yellow-300">
          Login isn&apos;t configured in this environment yet. You can still use the
          app via a dev token in the chat Settings.
        </p>
      )}

      <form onSubmit={submit} className="mt-6 space-y-3">
        <div>
          <label className="mb-1 block text-xs text-text-muted">Email</label>
          <input
            type="email"
            required
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            className="input"
            placeholder="you@company.com"
          />
        </div>
        <div>
          <label className="mb-1 block text-xs text-text-muted">Password</label>
          <input
            type="password"
            required
            minLength={6}
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            className="input"
            placeholder="••••••••"
          />
        </div>

        {error && <p className="text-sm text-red-400">{error}</p>}
        {notice && <p className="text-sm text-accent">{notice}</p>}

        <button
          type="submit"
          disabled={busy}
          className="w-full rounded-lg bg-accent px-4 py-2.5 font-medium text-surface disabled:opacity-40"
        >
          {busy ? "…" : mode === "signin" ? "Log in" : "Sign up"}
        </button>
      </form>

      <p className="mt-4 text-sm text-text-muted">
        {mode === "signin" ? (
          <>
            New here?{" "}
            <button onClick={() => setMode("signup")} className="text-accent hover:underline">
              Create an account
            </button>
          </>
        ) : (
          <>
            Already have an account?{" "}
            <button onClick={() => setMode("signin")} className="text-accent hover:underline">
              Log in
            </button>
          </>
        )}
      </p>

      <p className="mt-6 text-xs text-text-muted">
        <Link href="/" className="hover:text-text-secondary">
          ← Back to home
        </Link>
      </p>
    </div>
  );
}
