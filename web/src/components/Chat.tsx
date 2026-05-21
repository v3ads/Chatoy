"use client";

import { useEffect, useRef, useState } from "react";
import {
  ChatMessage,
  FinalPayload,
  getConfig,
  setConfig,
  streamChat,
} from "@/lib/api";

const PHASE_LABEL: Record<string, string> = {
  diagnose: "Diagnosing",
  write: "Writing",
  refine: "Refining",
};

export default function Chat() {
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
          // The canonical reply joins multi-agent messages cleanly (e.g. CRO
          // hand-off preface + written copy), so adopt it as the final text.
          if (payload.reply) {
            setMessages((m) => {
              const copy = [...m];
              copy[copy.length - 1] = { role: "assistant", content: payload.reply };
              return copy;
            });
          }
        },
        onError: (message: string) => {
          setError(message);
          // Drop the empty assistant placeholder.
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
    <main className="mx-auto flex h-screen max-w-3xl flex-col px-4">
      <header className="flex items-center justify-between border-b border-surface-border py-4">
        <div className="flex items-center gap-3">
          <h1 className="text-lg font-semibold tracking-tight">Chatoy</h1>
          <span className="rounded-full bg-accent-soft px-2.5 py-0.5 text-xs font-medium text-accent">
            {PHASE_LABEL[phase] ?? phase}
          </span>
        </div>
        <div className="flex items-center gap-2 text-sm">
          <button
            onClick={newChat}
            className="rounded-md border border-surface-border px-3 py-1.5 text-text-secondary hover:text-text-primary"
          >
            New chat
          </button>
          <button
            onClick={() => setShowSettings((s) => !s)}
            className="rounded-md border border-surface-border px-3 py-1.5 text-text-secondary hover:text-text-primary"
          >
            Settings
          </button>
        </div>
      </header>

      {showSettings && (
        <section className="space-y-3 border-b border-surface-border bg-surface-elevated/40 p-4 text-sm">
          <Field label="API URL">
            <input
              value={apiUrl}
              onChange={(e) => setApiUrl(e.target.value)}
              placeholder="http://127.0.0.1:8000"
              className="input"
            />
          </Field>
          <Field label="Bearer token (Supabase JWT; blank if auth disabled)">
            <input
              value={token}
              onChange={(e) => setToken(e.target.value)}
              placeholder="eyJ..."
              className="input"
            />
          </Field>
          <Field label="Business profile (JSON, sent on first message)">
            <textarea
              value={profileText}
              onChange={(e) => setProfileText(e.target.value)}
              rows={3}
              placeholder='{"product": "...", "audience": "..."}'
              className="input font-mono text-xs"
            />
          </Field>
          <button
            onClick={saveSettings}
            className="rounded-md bg-accent px-3 py-1.5 font-medium text-surface"
          >
            Save
          </button>
        </section>
      )}

      <div ref={scrollRef} className="scroll-thin flex-1 space-y-4 overflow-y-auto py-6">
        {messages.length === 0 && (
          <div className="mx-auto max-w-md pt-16 text-center text-text-muted">
            <p className="text-text-secondary">Tell the CRO what you&apos;re trying to grow.</p>
            <p className="mt-2 text-sm">
              It interviews you, locks a strategy, then Project Shepherd writes the asset in your voice.
            </p>
          </div>
        )}
        {messages.map((m, i) => (
          <Bubble key={i} role={m.role} content={m.content} busy={busy && i === messages.length - 1} />
        ))}

        {strategy && (
          <div className="rounded-lg border border-surface-border bg-surface-elevated p-4 text-sm">
            <div className="mb-2 text-xs font-semibold uppercase tracking-wide text-accent">
              Locked strategy
            </div>
            <dl className="space-y-1">
              {Object.entries(strategy).map(([k, v]) => (
                <div key={k} className="flex gap-2">
                  <dt className="shrink-0 text-text-muted">{k}:</dt>
                  <dd className="text-text-secondary">{String(v)}</dd>
                </div>
              ))}
            </dl>
            {frameworks.length > 0 && (
              <p className="mt-2 text-xs text-text-muted">
                {frameworks.length} framework(s) retrieved for this asset.
              </p>
            )}
          </div>
        )}
      </div>

      {error && (
        <div className="mb-2 rounded-md border border-red-900/60 bg-red-950/40 px-3 py-2 text-sm text-red-300">
          {error}
        </div>
      )}

      <div className="mb-4 flex items-end gap-2 rounded-xl border border-surface-border bg-surface-elevated p-2">
        <textarea
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={onKeyDown}
          rows={1}
          placeholder="Message Chatoy…"
          className="max-h-40 flex-1 resize-none bg-transparent px-2 py-1.5 text-sm outline-none placeholder:text-text-muted"
        />
        <button
          onClick={() => void send()}
          disabled={busy || !input.trim()}
          className="rounded-lg bg-accent px-4 py-2 text-sm font-medium text-surface disabled:opacity-40"
        >
          {busy ? "…" : "Send"}
        </button>
      </div>
    </main>
  );
}

function Field({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <label className="block">
      <span className="mb-1 block text-xs text-text-muted">{label}</span>
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
            ? "max-w-[80%] whitespace-pre-wrap rounded-2xl bg-accent-soft px-4 py-2.5 text-sm text-text-primary"
            : "max-w-[85%] whitespace-pre-wrap rounded-2xl bg-surface-elevated px-4 py-2.5 text-sm text-text-secondary"
        }
      >
        {content || (busy ? <span className="text-text-muted">▋</span> : null)}
      </div>
    </div>
  );
}
