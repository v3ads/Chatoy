"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState } from "react";
import { isSupabaseConfigured, supabase } from "@/lib/supabase";
import { getConfig } from "@/lib/api";

type Mode = "signin" | "signup" | "reset";

export default function AuthForm() {
  const router = useRouter();
  const [mode, setMode] = useState<Mode>("signin");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  const [resetEmail, setResetEmail] = useState("");

  async function handleReset(e: React.FormEvent) {
    e.preventDefault();
    setError("");
    setNotice("");
    if (!supabase) {
      setError("Password reset isn't configured yet.");
      return;
    }
    setBusy(true);
    try {
      const { error } = await supabase.auth.resetPasswordForEmail(resetEmail, {
        redirectTo: `${window.location.origin}/auth/reset-password`,
      });
      if (error) throw error;
      setNotice("Check your email for a password reset link.");
      setResetEmail("");
      setTimeout(() => setMode("signin"), 3000);
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setBusy(false);
    }
  }

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setError("");
    setNotice("");
    if (!supabase) {
      setError("Login isn't configured yet.");
      return;
    }
    setBusy(true);
    try {
      if (mode === "signup") {
        const { data, error } = await supabase.auth.signUp({ email, password });
        if (error) throw error;
        
        if (data.user) {
          const { apiUrl } = getConfig();
          const token = data.session?.access_token;
          if (token) {
            await fetch(`${apiUrl}/auth/notify-signup`, {
              method: "POST",
              headers: { 
                "Authorization": `Bearer ${token}`,
                "Content-Type": "application/json"
              }
            }).catch(console.error);
          }
        }

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
    <div className="w-full max-w-sm rounded-2xl border border-surface-border bg-surface-card p-10 shadow-2xl">
      <Link href="/" className="mb-8 block font-serif text-2xl font-bold tracking-tight text-text-primary text-center">
        Mytho<span className="text-accent">Stack</span>
      </Link>
      
      <h1 className="font-serif text-3xl font-bold tracking-tight text-text-primary">
        {mode === "signin" ? "Log in" : mode === "signup" ? "Create your account" : "Reset Password"}
      </h1>
      <p className="mt-2 text-sm text-text-secondary">
        {mode === "signin" ? "Enter your credentials to access the architect." : mode === "signup" ? "Sign up to join MythoStack." : "Enter your email to receive a password reset link."}
      </p>

      <form onSubmit={mode === "reset" ? handleReset : submit} className="mt-8 space-y-4">
        {mode === "reset" ? (
          <div>
            <label className="mb-1.5 block text-xs font-bold uppercase tracking-wider text-text-muted">Email Address</label>
            <input
              type="email"
              required
              value={resetEmail}
              onChange={(e) => setResetEmail(e.target.value)}
              className="w-full rounded-lg border border-surface-border bg-surface px-4 py-3 text-text-primary outline-none focus:border-accent transition-colors"
              placeholder="name@company.com"
            />
          </div>
        ) : (
          <>
            <div>
              <label className="mb-1.5 block text-xs font-bold uppercase tracking-wider text-text-muted">Email Address</label>
              <input
                type="email"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="w-full rounded-lg border border-surface-border bg-surface px-4 py-3 text-text-primary outline-none focus:border-accent transition-colors"
                placeholder="name@company.com"
              />
            </div>
            <div>
              <div className="flex justify-between items-center mb-1.5">
                <label className="block text-xs font-bold uppercase tracking-wider text-text-muted">Password</label>
                {mode === "signin" && (
                  <button 
                    type="button"
                    onClick={() => setMode("reset")} 
                    className="text-xs font-bold text-accent hover:underline"
                  >
                    Forgot?
                  </button>
                )}
              </div>
              <input
                type="password"
                required
                minLength={6}
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="w-full rounded-lg border border-surface-border bg-surface px-4 py-3 text-text-primary outline-none focus:border-accent transition-colors"
                placeholder="••••••••"
              />
            </div>
          </>
        )}

        {error && <p className="text-sm text-red-400 font-medium">{error}</p>}
        {notice && <p className="text-sm text-accent font-medium">{notice}</p>}

        <button
          type="submit"
          disabled={busy}
          className="w-full rounded-lg bg-accent px-4 py-3.5 font-bold text-surface transition-colors hover:bg-accent-dim disabled:opacity-40"
        >
          {busy ? "Processing..." : mode === "signin" ? "Enter Dashboard" : mode === "signup" ? "Create Account" : "Send Reset Link"}
        </button>
      </form>

      <div className="mt-8 border-t border-surface-border pt-6">
        <p className="text-sm text-text-secondary text-center">
          {mode === "signin" ? (
            <>
              New to MythoStack?{" "}
              <button onClick={() => setMode("signup")} className="font-bold text-accent hover:underline">
                Join the Waitlist
              </button>
            </>
          ) : (
            <>
              Remember your password?{" "}
              <button onClick={() => setMode("signin")} className="font-bold text-accent hover:underline">
                Log in
              </button>
            </>
          )}
        </p>
      </div>

      <p className="mt-6 text-center text-xs text-text-muted">
        <Link href="/" className="hover:text-text-primary transition-colors">
          ← Return to Landing Page
        </Link>
      </p>
    </div>
  );
}
