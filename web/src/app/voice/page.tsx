"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { isSupabaseConfigured, supabase } from "@/lib/supabase";
import { analyzeVoice, getVoiceProfile, VoiceProfileResponse } from "@/lib/api";

export default function VoicePage() {
  const router = useRouter();
  const [ready, setReady] = useState(!isSupabaseConfigured);
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  
  const [samples, setSamples] = useState(["", "", ""]);
  const [profile, setProfile] = useState<VoiceProfileResponse | null>(null);

  useEffect(() => {
    if (!isSupabaseConfigured || !supabase) {
      setLoading(false);
      return;
    }
    supabase.auth.getSession().then(({ data }) => {
      if (!data.session) {
        router.replace("/login");
        return;
      }
      setReady(true);
      fetchProfile();
    });
  }, [router]);

  async function fetchProfile() {
    try {
      const data = await getVoiceProfile();
      setProfile(data);
    } catch (err) {
      console.error("Failed to fetch profile", err);
    } finally {
      setLoading(false);
    }
  }

  async function handleAnalyze() {
    const validSamples = samples.filter(s => s.trim().length > 0);
    if (validSamples.length === 0) {
      setError("Please provide at least one writing sample.");
      return;
    }

    setBusy(true);
    setError("");
    try {
      const data = await analyzeVoice(validSamples);
      setProfile(data);
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setBusy(false);
    }
  }

  function updateSample(index: number, value: string) {
    const newSamples = [...samples];
    newSamples[index] = value;
    setSamples(newSamples);
  }

  function addSample() {
    setSamples([...samples, ""]);
  }

  if (!ready || loading) {
    return <div className="p-8 text-text-muted">Loading…</div>;
  }

  return (
    <main className="mx-auto min-h-screen max-w-4xl bg-surface px-6 py-12">
      <header className="mb-12 flex items-center justify-between">
        <div>
          <Link href="/chat" className="text-sm font-bold uppercase tracking-widest text-accent hover:text-accent-dim">
            ← Back to Architect
          </Link>
          <h1 className="mt-4 text-4xl font-bold text-text-primary">Voice Training</h1>
          <p className="mt-2 text-text-secondary">
            Teach the Asset Engine how you write so it can build campaigns that sound like you.
          </p>
        </div>
      </header>

      <div className="grid gap-12 lg:grid-cols-2">
        <section className="space-y-8">
          <div className="space-y-4">
            <h2 className="text-xl font-semibold text-text-primary">Your Writing Samples</h2>
            <p className="text-sm text-text-muted leading-relaxed">
              Paste 3-5 examples of your best writing (emails, blog posts, or social updates). 
              The more variety you provide, the more accurate the "fingerprint" will be.
            </p>
          </div>

          <div className="space-y-6">
            {samples.map((sample, i) => (
              <div key={i} className="space-y-2">
                <label className="text-[10px] font-bold uppercase tracking-wider text-text-muted">Sample #{i + 1}</label>
                <textarea
                  value={sample}
                  onChange={(e) => updateSample(i, e.target.value)}
                  rows={4}
                  placeholder="Paste writing sample here..."
                  className="w-full rounded-xl border border-surface-border bg-surface-card px-4 py-3 text-sm text-text-primary outline-none focus:border-accent transition-colors"
                />
              </div>
            ))}
            
            <button 
              onClick={addSample}
              className="text-sm font-bold text-accent hover:text-accent-dim"
            >
              + Add another sample
            </button>
          </div>

          {error && (
            <div className="rounded-lg bg-red-950/20 border border-red-900/30 p-4 text-sm text-red-300">
              {error}
            </div>
          )}

          <button
            onClick={handleAnalyze}
            disabled={busy}
            className="w-full rounded-xl bg-accent py-4 text-lg font-bold text-surface transition-all hover:bg-accent-dim disabled:opacity-50"
          >
            {busy ? "Analyzing Voice Fingerprint..." : "Train Asset Engine"}
          </button>
        </section>

        <section className="space-y-8">
          <div className="rounded-2xl border border-surface-border bg-surface-card p-8">
            <h2 className="text-xl font-semibold text-text-primary">Current Voice Profile</h2>
            
            {!profile ? (
              <div className="mt-8 text-center py-12 border-2 border-dashed border-surface-border rounded-xl">
                <p className="text-sm text-text-muted">No voice profile trained yet.</p>
              </div>
            ) : (
              <div className="mt-8 space-y-6">
                <div className="rounded-xl bg-accent/5 border border-accent/10 p-4">
                  <h3 className="text-[10px] font-bold uppercase tracking-[0.2em] text-accent">Strategic Tone</h3>
                  <p className="mt-2 text-sm text-text-primary leading-relaxed">
                    {profile.profile.tone}
                  </p>
                </div>

                <div className="grid gap-4 sm:grid-cols-2">
                  {Object.entries(profile.profile).filter(([k]) => k !== 'tone').map(([k, v]) => (
                    <div key={k} className="space-y-1">
                      <h4 className="text-[10px] font-bold uppercase tracking-wider text-text-muted">{k.replace(/_/g, ' ')}</h4>
                      <p className="text-xs text-text-secondary leading-snug">{v}</p>
                    </div>
                  ))}
                </div>

                <div className="pt-6 border-t border-surface-border">
                  <h3 className="text-[10px] font-bold uppercase tracking-wider text-text-muted">Writer Instructions</h3>
                  <div className="mt-3 rounded-lg bg-surface p-4 font-mono text-[11px] text-text-muted whitespace-pre-wrap leading-relaxed">
                    {profile.rendered}
                  </div>
                </div>
              </div>
            )}
          </div>

          <div className="rounded-2xl border border-accent/20 bg-accent/5 p-6">
            <h3 className="text-sm font-bold text-text-primary">How this works</h3>
            <p className="mt-2 text-xs text-text-secondary leading-relaxed">
              Our Asset Engine uses these samples to build a multi-dimensional "style map" of your writing. 
              It doesn't just copy your words—it learns your sentence cadence, humor level, and 
              vocabulary preferences so it can architect new campaigns that actually sound like you.
            </p>
          </div>
        </section>
      </div>
    </main>
  );
}
// trigger voice route: Fri May 22 18:05:00 UTC 2026
