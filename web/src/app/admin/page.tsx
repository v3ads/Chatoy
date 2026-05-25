"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import MobileMenu from "@/components/MobileMenu";
import AppMenuLinks from "@/components/AppMenuLinks";
import {
  AvailableModel,
  KnowledgeStatus,
  ModelConfig,
  getAvailableModels,
  getKnowledgeStatus,
  getModelConfig,
  seedKnowledge,
  setModelConfig,
} from "@/lib/api";

type Role = "architect" | "writer" | "voice";
const ROLES: { key: Role; label: string; hint: string }[] = [
  { key: "architect", label: "Architect", hint: "Strategy / interview agent" },
  { key: "writer", label: "Writer", hint: "Writes the marketing copy" },
  { key: "voice", label: "Voice", hint: "Analyzes writing samples" },
];

export default function AdminPage() {
  const [models, setModels] = useState<AvailableModel[]>([]);
  const [config, setConfig] = useState<ModelConfig>({
    architect: null,
    writer: null,
    voice: null,
  });
  const [loading, setLoading] = useState(true);
  const [denied, setDenied] = useState(false);
  const [error, setError] = useState("");
  const [saving, setSaving] = useState(false);
  const [savedAt, setSavedAt] = useState<number | null>(null);
  const [knowledge, setKnowledge] = useState<KnowledgeStatus | null>(null);
  const [seeding, setSeeding] = useState(false);
  const [kbNotice, setKbNotice] = useState("");
  const [modelsReason, setModelsReason] = useState("");

  useEffect(() => {
    // Essential settings + knowledge status gate the page — load them first.
    (async () => {
      try {
        const [cfg, kb] = await Promise.all([getModelConfig(), getKnowledgeStatus()]);
        setConfig(cfg);
        setKnowledge(kb);
      } catch (e) {
        const status = (e as { status?: number }).status;
        if (status === 401 || status === 403) {
          setDenied(true);
        } else {
          setError((e as Error).message);
        }
      } finally {
        setLoading(false);
      }
    })();
    // The OpenRouter model list can be slow or unavailable; load it separately so
    // it never blocks the page. The reason (if empty) is shown next to Save.
    getAvailableModels()
      .then((res) => {
        setModels(res.models);
        setModelsReason(res.reason ?? "");
      })
      .catch(() =>
        setModelsReason("Couldn't load the model list (the request failed or timed out)."),
      );
  }, []);

  async function save() {
    setSaving(true);
    setError("");
    try {
      const updated = await setModelConfig(config);
      setConfig(updated);
      setSavedAt(Date.now());
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setSaving(false);
    }
  }

  async function seed() {
    setSeeding(true);
    setError("");
    setKbNotice("");
    try {
      const res = await seedKnowledge();
      setKnowledge((k) => ({ ...(k ?? { semantic: true }), count: res.count, semantic: true }));
      if (!res.ok) setKbNotice(res.reason ?? "Semantic indexing is unavailable right now.");
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setSeeding(false);
    }
  }

  if (loading) {
    return <div className="p-8 text-text-muted">Loading…</div>;
  }

  if (denied) {
    return (
      <main className="mx-auto max-w-md px-6 py-24 text-center">
        <h1 className="text-2xl font-semibold">Admin only</h1>
        <p className="mt-3 text-text-secondary">
          You need to be signed in as an administrator to view this page.
        </p>
        <Link href="/" className="mt-6 inline-block text-accent hover:underline">
          ← Back to home
        </Link>
      </main>
    );
  }

  return (
    <main className="mx-auto max-w-2xl px-4 py-10 sm:px-6 sm:py-12">
      <div className="flex items-center justify-between gap-3">
        <h1 className="text-2xl font-semibold tracking-tight">Model settings</h1>
        <div className="flex items-center gap-3">
          <Link href="/chat" className="hidden text-sm text-text-secondary hover:text-text-primary lg:inline">
            ← Back to app
          </Link>
          <div className="lg:hidden">
            <MobileMenu>{(close) => <AppMenuLinks onNavigate={close} />}</MobileMenu>
          </div>
        </div>
      </div>
      <p className="mt-2 text-sm text-text-muted">
        Choose the OpenRouter model for each agent. Leave on “Default (Claude)” to use the
        built-in model. If a chosen model fails, it automatically falls back to Claude.
        Changes apply to all users immediately.
      </p>

      <div className="mt-8 space-y-5">
        {ROLES.map(({ key, label, hint }) => (
          <label key={key} className="block">
            <span className="text-sm font-medium text-text-primary">{label}</span>
            <span className="ml-2 text-xs text-text-muted">{hint}</span>
            <select
              value={config[key] ?? ""}
              onChange={(e) =>
                setConfig((c) => ({ ...c, [key]: e.target.value || null }))
              }
              className="mt-1.5 w-full rounded-md border border-surface-border bg-surface px-3 py-2 text-text-primary outline-none focus:border-accent"
            >
              <option value="">— Default (Claude) —</option>
              {models.map((m) => (
                <option key={m.id} value={m.id}>
                  {m.name}
                </option>
              ))}
            </select>
          </label>
        ))}
      </div>

      {error && <p className="mt-4 text-sm text-red-400">{error}</p>}

      <div className="mt-8 flex items-center gap-3">
        <button
          onClick={save}
          disabled={saving}
          className="rounded-lg bg-accent px-5 py-2.5 font-medium text-surface disabled:opacity-40"
        >
          {saving ? "Saving…" : "Save"}
        </button>
        {savedAt && !saving && (
          <span className="text-sm text-accent">Saved.</span>
        )}
        {models.length === 0 && (
          <span className="text-sm text-text-muted">
            {modelsReason || "No OpenRouter models loaded."}
          </span>
        )}
      </div>

      <section className="mt-12 border-t border-surface-border pt-8">
        <h2 className="text-lg font-semibold tracking-tight">Knowledge base</h2>
        <p className="mt-1 text-sm text-text-muted">
          Direct-response frameworks the Architect and Writer retrieve from via semantic
          search.
        </p>
        {knowledge && (
          <p className="mt-3 text-sm text-text-secondary">
            {knowledge.semantic
              ? `${knowledge.count} chunk(s) indexed.`
              : "Semantic search isn’t configured — set the OpenAI key in Railway, then seed."}
          </p>
        )}
        {knowledge?.semantic && knowledge.persistent === false && (
          <p className="mt-1 text-sm text-amber-400">
            Store is in-memory, not pgvector — seeded data is lost on restart and isn’t
            shared across workers. Set MYTHOSTACK_DATABASE_URL on the backend to persist.
          </p>
        )}
        <button
          onClick={seed}
          disabled={seeding || !knowledge?.semantic}
          className="mt-3 rounded-lg border border-surface-border px-4 py-2 text-sm text-text-secondary hover:text-text-primary disabled:opacity-40"
        >
          {seeding ? "Seeding…" : "Seed / refresh knowledge base"}
        </button>
        {kbNotice && <p className="mt-3 text-sm text-amber-400">{kbNotice}</p>}
      </section>
    </main>
  );
}
