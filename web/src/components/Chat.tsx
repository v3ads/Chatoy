"use client";

import { useEffect, useRef, useState } from "react";
import Link from "next/link";
import MobileMenu from "@/components/MobileMenu";
import AppMenuLinks from "@/components/AppMenuLinks";
import ProjectModal from "@/components/ProjectModal";
import {
  ChatMessage,
  FinalPayload,
  MarketingAssetDTO,
  Project,
  getConfig,
  listAssets,
  listProjects,
  reportAssetMetrics,
  setConfig,
  streamChat,
} from "@/lib/api";

const PROJECT_KEY = "mythostack.projectId";

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

  const [projects, setProjects] = useState<Project[]>([]);
  const [projectId, setProjectId] = useState<string>("");
  const [showMemory, setShowMemory] = useState(false);
  const [assets, setAssets] = useState<MarketingAssetDTO[]>([]);
  const [showProjectModal, setShowProjectModal] = useState(false);

  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    setSessionId(crypto.randomUUID());
    // Sync the displayed config from the resolved API URL (getConfig sanitizes
    // away any stale ":8080" and applies the production fallback).
    const cfg = getConfig();
    setApiUrl(cfg.apiUrl);
    setToken(cfg.token);
    setConfig({ apiUrl: cfg.apiUrl });
  }, []);

  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight });
  }, [messages]);

  // Load the user's projects and select the active one (last used, else first).
  useEffect(() => {
    (async () => {
      try {
        const list = await listProjects();
        setProjects(list);
        const saved = typeof window !== "undefined" ? localStorage.getItem(PROJECT_KEY) : null;
        const active = list.find((p) => p.id === saved)?.id ?? list[0]?.id ?? "";
        setProjectId(active);
      } catch {
        /* projects are best-effort in the header; chat still works on the default */
      }
    })();
  }, []);

  function selectProject(id: string) {
    if (!id || id === projectId) return;
    setProjectId(id);
    if (typeof window !== "undefined") localStorage.setItem(PROJECT_KEY, id);
    setShowMemory(false);
    newChat(); // conversations are per-project — start a fresh thread on switch
  }

  function onProjectCreated(p: Project) {
    setProjects((ps) => [...ps, p]);
    setShowProjectModal(false);
    selectProject(p.id);
  }

  async function openMemory() {
    const next = !showMemory;
    setShowMemory(next);
    if (next && projectId) {
      try {
        setAssets((await listAssets(projectId)).assets);
      } catch {
        setAssets([]);
      }
    }
  }

  async function reportMetric(asset: MarketingAssetDTO) {
    if (asset.id == null) return;
    const entry = window.prompt(
      "Report a result for this asset (e.g. open_rate=42% or revenue=1200):",
    );
    if (!entry?.includes("=")) return;
    const [key, ...rest] = entry.split("=");
    try {
      const updated = await reportAssetMetrics(
        asset.id,
        { [key.trim()]: rest.join("=").trim() },
        projectId,
      );
      setAssets((as) => as.map((a) => (a.id === updated.id ? updated : a)));
    } catch (e) {
      setError((e as Error).message);
    }
  }

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
      { sessionId, message: text, projectId: projectId || undefined, businessProfile },
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
            userMessage = "The architect is temporarily offline. Retrying...";
          } else if (message.includes("401")) {
            userMessage = "Session expired. Please log in again.";
          } else if (message.includes("Failed to fetch")) {
            // In production, don't show the technical error to users
            if (process.env.NODE_ENV === 'production') {
              userMessage = "The architect is connecting. Please try again.";
            } else {
              userMessage = `Could not connect to the growth engine at ${apiUrl}.`;
            }
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
    <main className="mx-auto flex h-screen max-w-4xl flex-col bg-surface px-4 sm:px-6">
      <header className="flex items-center justify-between gap-3 border-b border-surface-border py-4 lg:py-6">
        <div className="flex min-w-0 items-center gap-2 sm:gap-4">
          <MobileMenu>
            {(close) => (
              <div className="flex flex-col gap-4">
                {projects.length > 0 && (
                  <div className="space-y-2">
                    <span className="text-[10px] font-bold uppercase tracking-wider text-text-muted">
                      Project
                    </span>
                    <select
                      value={projectId}
                      onChange={(e) => {
                        selectProject(e.target.value);
                        close();
                      }}
                      className="w-full rounded-lg border border-surface-border bg-surface px-3 py-2 text-sm font-medium text-text-primary outline-none focus:border-accent"
                    >
                      {projects.map((p) => (
                        <option key={p.id} value={p.id}>
                          {p.name}
                        </option>
                      ))}
                    </select>
                    <button
                      onClick={() => {
                        close();
                        setShowProjectModal(true);
                      }}
                      className="w-full rounded-lg border border-surface-border px-3 py-2 text-left text-sm font-medium text-text-secondary hover:text-text-primary"
                    >
                      + New project
                    </button>
                  </div>
                )}
                <div className="flex flex-col gap-1">
                  <button
                    onClick={() => {
                      close();
                      void openMemory();
                    }}
                    className="rounded-lg px-3 py-2.5 text-left text-sm font-medium text-text-secondary transition-colors hover:bg-surface-border hover:text-text-primary"
                  >
                    Memory
                  </button>
                  <button
                    onClick={() => {
                      close();
                      newChat();
                    }}
                    className="rounded-lg px-3 py-2.5 text-left text-sm font-medium text-text-secondary transition-colors hover:bg-surface-border hover:text-text-primary"
                  >
                    New Session
                  </button>
                </div>
                <div className="border-t border-surface-border pt-3">
                  <AppMenuLinks onNavigate={close} />
                </div>
              </div>
            )}
          </MobileMenu>

          <Link href="/" className="shrink-0 text-xl font-bold tracking-tight text-text-primary sm:text-2xl">
            Mytho<span className="text-accent">Stack</span>
          </Link>
          <div className="hidden items-center gap-2 rounded-full border border-accent/20 bg-accent/5 px-3 py-1 sm:flex">
            <div className="h-1.5 w-1.5 animate-pulse rounded-full bg-accent" />
            <span className="text-[10px] font-bold uppercase tracking-widest text-accent">
              {PHASE_LABEL[phase] ?? phase}
            </span>
          </div>
          {projects.length > 0 && (
            <div className="hidden items-center gap-1.5 lg:flex">
              <select
                value={projectId}
                onChange={(e) => selectProject(e.target.value)}
                title="Switch project — each keeps its own profile, voice, assets and memory"
                className="max-w-[10rem] rounded-lg border border-surface-border bg-surface-card px-2.5 py-1.5 text-xs font-medium text-text-primary outline-none focus:border-accent"
              >
                {projects.map((p) => (
                  <option key={p.id} value={p.id}>
                    {p.name}
                  </option>
                ))}
              </select>
              <button
                onClick={() => setShowProjectModal(true)}
                title="New project"
                className="flex h-7 w-7 items-center justify-center rounded-lg border border-surface-border bg-surface-card text-sm text-text-secondary transition-colors hover:text-text-primary"
              >
                +
              </button>
            </div>
          )}
        </div>
        <div className="hidden items-center gap-3 lg:flex">
          <Link
            href="/voice"
            className="rounded-lg border border-surface-border bg-surface-card px-4 py-2 text-xs font-bold uppercase tracking-wider text-text-primary transition-colors hover:bg-surface-border"
          >
            Voice
          </Link>
          <button
            onClick={openMemory}
            className="rounded-lg border border-surface-border bg-surface-card px-4 py-2 text-xs font-bold uppercase tracking-wider text-text-primary transition-colors hover:bg-surface-border"
          >
            Memory
          </button>
          <button
            onClick={newChat}
            className="rounded-lg border border-surface-border bg-surface-card px-4 py-2 text-xs font-bold uppercase tracking-wider text-text-primary transition-colors hover:bg-surface-border"
          >
            New Session
          </button>
          {/* Config button hidden for production */}
          {process.env.NODE_ENV === "development" && (
            <button
              onClick={() => setShowSettings((s) => !s)}
              className="rounded-lg border border-surface-border bg-surface-card px-4 py-2 text-xs font-bold uppercase tracking-wider text-text-primary transition-colors hover:bg-surface-border"
            >
              Config
            </button>
          )}
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

      {showMemory && (
        <section className="mt-4 rounded-xl border border-surface-border bg-surface-card p-6 shadow-xl">
          <div className="mb-3 flex items-center justify-between">
            <span className="text-[10px] font-bold uppercase tracking-[0.2em] text-accent">
              Project memory — past assets
            </span>
            <button
              onClick={() => setShowMemory(false)}
              className="text-xs text-text-muted hover:text-text-primary"
            >
              Close
            </button>
          </div>
          {assets.length === 0 ? (
            <p className="text-sm text-text-muted">
              No assets yet. Build one and it&apos;s logged here automatically — report its
              results to make the next recommendation smarter.
            </p>
          ) : (
            <ul className="space-y-2">
              {assets.map((a) => (
                <li
                  key={a.id ?? a.created_at}
                  className="flex flex-col gap-2 rounded-lg border border-surface-border bg-surface px-3 py-2 sm:flex-row sm:items-center sm:justify-between"
                >
                  <div className="min-w-0">
                    <div className="text-sm font-medium text-text-primary">
                      {a.asset_type.replace(/_/g, " ")}
                      {a.marketing_angle ? ` — ${a.marketing_angle}` : ""}
                    </div>
                    <div className="truncate text-xs text-text-muted">
                      {Object.keys(a.metrics).length
                        ? Object.entries(a.metrics)
                            .map(([k, v]) => `${k}: ${v}`)
                            .join("  ·  ")
                        : "no results reported yet"}
                    </div>
                  </div>
                  <button
                    onClick={() => void reportMetric(a)}
                    className="shrink-0 self-start rounded-lg border border-surface-border px-3 py-1.5 text-xs font-bold uppercase tracking-wider text-text-secondary hover:text-text-primary sm:self-auto"
                  >
                    Report result
                  </button>
                </li>
              ))}
            </ul>
          )}
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
          {/* Reconfigure hidden for production */}
          {process.env.NODE_ENV === "development" && (
            <button 
              onClick={() => setShowSettings(true)}
              className="mt-2 text-xs font-bold uppercase tracking-widest text-accent underline hover:no-underline"
            >
              Reconfigure Engine
            </button>
          )}
          {process.env.NODE_ENV === "production" && (
            <button 
              onClick={() => void send()}
              className="mt-2 text-xs font-bold uppercase tracking-widest text-accent underline hover:no-underline"
            >
              Try Again
            </button>
          )}
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

      <ProjectModal
        open={showProjectModal}
        onClose={() => setShowProjectModal(false)}
        onCreated={onProjectCreated}
      />
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
