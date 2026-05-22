"use client";

import { useEffect, useRef, useState } from "react";
import Link from "next/link";
import {
  ChatMessage,
  FinalPayload,
  getConfig,
  setConfig,
  streamChat,
} from "@/lib/api";

const PHASE_LABEL: Record<string, string> = {
  diagnose: "Analyzing Business",
  write: "Architecting Assets",
  refine: "Compounding Intelligence",
};

export default function Chat({
  userEmail,
  onLogout,
}: {
  userEmail?: string | null;
  onLogout?: () => void;
}) {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [phase, setPhase] = useState<string>("diagnose");
  const [strategy, setStrategy] = useState<Record<string, unknown> | null>(null);
  const [frameworks, setFrameworks] = useState<string[]>([]);
  const [sessionId, setSessionId] = useState("");

  const [showSettings, setShowSettings] = useState(false);
  const [apiUrl, setApiUrl] = useState("");
  const [token, setToken] = useState("");
  const [profileText, setProfileText] = useState("");

  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    setSessionId(crypto.randomUUID());
    const cfg = getConfig();
    setApiUrl(cfg.apiUrl);
    setToken(cfg.token);
  }, []);

  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight });
  }, [messages]);

  function newChat() {
    setSessionId(crypto.randomUUID());
    setMessages([]);
    setPhase("diagnose");
    setStrategy(null);
    setFrameworks([]);
    setError("");
  }

  function saveSettings() {
    setConfig({ apiUrl, token });
    setShowSettings(false);
    setError("");
  }

  async function send() {
    const text = input.trim();
    if (!text || busy || !sessionId) return;
    setInput("");
    setError("");

    let businessProfile: Record<string, unknown> | undefined;
    if (messages.length === 0 && profileText.trim()) {
      try {
        businessProfile = JSON.parse(profileText);
      } catch {
        /* ignore invalid JSON; just skip the profile */
      }
    }

    setMessages((m) => [...m, { role: "user", content: text }, { role: "assistant", content: "" }]);
    setBusy(true);

    const appendToLast = (chunk: string) =>
      setMessages((m) => {
        const copy = [...m];
        const last = copy[copy.length - 1];
        copy[copy.length - 1] = { ...last, content: last.content + chunk };
        return copy;
      });

    await streamChat(
      { sessionId, message: text, businessProfile },
      {
        onToken: appendToLast,
        onFinal: (payload: FinalPayload) => {
          setPhase(payload.next_step);
          setStrategy(payload.current_strategy);
          setFrameworks(payload.retrieved_frameworks ?? []);
          if (payload.reply) {
            setMessages((m) => {
              const copy = [...m];
              copy[copy.length - 1] = { role: "assistant", content: payload.reply };
              return copy;
            });
          }
        },
        onError: (message: string) => {
          let userMessage = message;
          if (message.includes("503")) {
            userMessage = "The architect is offline. Please check engine configuration.";
          } else if (message.includes("401")) {
            userMessage = "Session expired. Please log in again.";
          } else if (message.includes("Failed to fetch")) {
            userMessage = `Could not connect to the growth engine at ${apiUrl}.`;
          }
          setError(userMessage);
          setMessages((m) => (m[m.length - 1]?.content === "" ? m.slice(0, -1) : m));
        },
      },
    );
    setBusy(false);
  }

  function onKeyDown(e: React.KeyboardEvent<HTMLTextAreaElement>) {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      void send();
    }
  }

  return (
    <main className="mx-auto flex h-screen max-w-4xl flex-col bg-surface px-6">
      <header className="flex items-center justify-between border-b border-surface-border py-6">
        <div className="flex items-center gap-4">
          <Link href="/" className="text-2xl font-bold tracking-tight text-text-primary">
            Mytho<span className="text-accent">Stack</span>
          </Link>
          <div className="flex items-center gap-2 rounded-full border border-accent/20 bg-accent/5 px-3 py-1">
            <div className="h-1.5 w-1.5 animate-pulse rounded-full bg-accent" />
            <span className="text-[10px] font-bold uppercase tracking-widest text-accent">
              {PHASE_LABEL[phase] ?? phase}
            </span>
          </div>
        </div>
        <div className="flex items-center gap-3">
          <button
            onClick={newChat}
            className="rounded-lg border border-surface-border bg-surface-card px-4 py-2 text-xs font-bold uppercase tracking-wider text-text-primary transition-colors hover:bg-surface-border"
          >
            New Session
          </button>
          <button
            onClick={() => setShowSettings((s) => !s)}
            className="rounded-lg border border-surface-border bg-surface-card px-4 py-2 text-xs font-bold uppercase tracking-wider text-text-primary transition-colors hover:bg-surface-border"
          >
            Config
          </button>
          {onLogout && (
            <button
              onClick={onLogout}
              className="rounded-lg border border-red-900/30 bg-red-950/10 px-4 py-2 text-xs font-bold uppercase tracking-wider text-red-400 transition-colors hover:bg-red-900/20"
            >
              Exit
            </button>
          )}
        </div>
      </header>

      {showSettings && (
        <section className="mt-4 space-y-4 rounded-xl border border-surface-border bg-surface-card p-6 shadow-xl">
          <div className="grid gap-4 md:grid-cols-2">
            <Field label="Growth Engine API">
              <input
                value={apiUrl}
                onChange={(e) => setApiUrl(e.target.value)}
                placeholder="https://api.mythostack.com"
                className="w-full rounded-lg border border-surface-border bg-surface px-3 py-2 text-sm text-text-primary outline-none focus:border-accent"
              />
            </Field>
            <Field label="Access Token (JWT)">
              <input
                value={token}
                onChange={(e) => setToken(e.target.value)}
                placeholder="eyJ..."
                className="w-full rounded-lg border border-surface-border bg-surface px-3 py-2 text-sm text-text-primary outline-none focus:border-accent"
              />
            </Field>
          </div>
          <Field label="Strategic Context (JSON)">
            <textarea
              value={profileText}
              onChange={(e) => setProfileText(e.target.value)}
              rows={3}
              placeholder='{"core_product": "...", "target_audience": "..."}'
              className="w-full rounded-lg border border-surface-border bg-surface px-3 py-2 font-mono text-xs text-text-primary outline-none focus:border-accent"
            />
          </Field>
          <div className="flex justify-end">
            <button
              onClick={saveSettings}
              className="rounded-lg bg-accent px-6 py-2 text-sm font-bold text-surface transition-colors hover:bg-accent-dim"
            >
              Apply Configuration
            </button>
          </div>
        </section>
      )}

      <div ref={scrollRef} className="scroll-thin flex-1 space-y-6 overflow-y-auto py-8">
        {messages.length === 0 && (
          <div className="mx-auto max-w-lg pt-20 text-center">
            <h2 className="text-3xl font-bold text-text-primary">Ready to architect.</h2>
            <p className="mt-4 text-text-secondary leading-relaxed">
              Brief the architect on your business or the campaign you want to build. 
              The more context you provide, the more the intelligence compounds.
            </p>
          </div>
        )}
        {messages.map((m, i) => (
          <Bubble key={i} role={m.role} content={m.content} busy={busy && i === messages.length - 1} />
        ))}

        {strategy && (
          <div className="mx-auto max-w-2xl rounded-xl border border-accent/20 bg-accent/5 p-6 shadow-sm">
            <div className="mb-4 flex items-center gap-2 border-b border-accent/10 pb-3">
              <span className="text-[10px] font-bold uppercase tracking-[0.2em] text-accent">Active Growth Strategy</span>
            </div>
            <dl className="grid gap-4 sm:grid-cols-2">
              {Object.entries(strategy).map(([k, v]) => (
                <div key={k} className="flex flex-col">
                  <dt className="text-[10px] font-bold uppercase tracking-wider text-text-muted">{k.replace(/_/g, ' ')}</dt>
                  <dd className="mt-1 text-sm font-medium text-text-primary">{String(v)}</dd>
                </div>
              ))}
            </dl>
          </div>
        )}
      </div>

      {error && (
        <div className="mb-6 rounded-xl border border-red-900/40 bg-red-950/20 p-4 text-sm text-red-300">
          <div className="flex items-center gap-2 font-bold uppercase tracking-wider">
            <span className="text-lg">⚠️</span> System Alert
          </div>
          <p className="mt-1 opacity-90">{error}</p>
          <button 
            onClick={() => setShowSettings(true)}
            className="mt-2 text-xs font-bold uppercase tracking-widest text-accent underline hover:no-underline"
          >
            Reconfigure Engine
          </button>
        </div>
      )}

      <div className="mb-8 flex items-end gap-3 rounded-2xl border border-surface-border bg-surface-card p-3 shadow-lg focus-within:border-accent transition-colors">
        <textarea
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={onKeyDown}
          rows={1}
          placeholder="Brief the architect..."
          className="max-h-48 flex-1 resize-none bg-transparent px-3 py-2 text-base text-text-primary outline-none placeholder:text-text-muted"
        />
        <button
          onClick={() => void send()}
          disabled={busy || !input.trim()}
          className="flex h-12 w-12 items-center justify-center rounded-xl bg-accent text-surface transition-all hover:bg-accent-dim disabled:opacity-20"
        >
          {busy ? (
            <div className="h-5 w-5 animate-spin rounded-full border-2 border-surface border-t-transparent" />
          ) : (
            <span className="text-xl">↑</span>
          )}
        </button>
      </div>
    </main>
  );
}

function Field({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <label className="block">
      <span className="mb-1.5 block text-[10px] font-bold uppercase tracking-wider text-text-muted">{label}</span>
      {children}
    </label>
  );
}

function Bubble({
  role,
  content,
  busy,
}: {
  role: string;
  content: string;
  busy: boolean;
}) {
  const isUser = role === "user";
  return (
    <div className={isUser ? "flex justify-end" : "flex justify-start"}>
      <div
        className={
          isUser
            ? "max-w-[80%] whitespace-pre-wrap rounded-2xl bg-surface-card border border-surface-border px-5 py-3.5 text-sm text-text-primary shadow-sm"
            : "max-w-[90%] whitespace-pre-wrap rounded-2xl bg-surface px-2 py-1 text-base leading-relaxed text-text-secondary"
        }
      >
        {content || (busy ? <span className="animate-pulse text-accent">▋</span> : null)}
      </div>
    </div>
  );
}
