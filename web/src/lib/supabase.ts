import { createClient, SupabaseClient } from "@supabase/supabase-js";

// Public, browser-safe values (anon key is meant to be exposed). Set these in
// .env.local (dev) and in Vercel (prod). When absent, the app runs in "dev
// token" mode: you paste a bearer token in Settings instead of logging in.
const url = process.env.NEXT_PUBLIC_SUPABASE_URL;
const anonKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY;

export const isSupabaseConfigured = Boolean(url && anonKey);

export const supabase: SupabaseClient | null = isSupabaseConfigured
  ? createClient(url as string, anonKey as string, {
      auth: { persistSession: true, autoRefreshToken: true },
    })
  : null;
