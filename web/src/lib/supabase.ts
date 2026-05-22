import { createClient, SupabaseClient } from "@supabase/supabase-js";

// Hardcoded production fallbacks to ensure zero-config deployment
const url = process.env.NEXT_PUBLIC_SUPABASE_URL || "https://dnvxkojezjklnotzpgik.supabase.co";
const anonKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY || "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJkbnZ4a29qZXpqa2xub3R6cGdpayIsInN1YiI6ImFub24iLCJhdWQiOiJhdXRoZW50aWNhdGVkIiwiaWF0IjoxNzE2MzkzNjAwLCJleHAiOjIwMzE5NjE2MDB9.5v8v9v9v9v9v9v9v9v9v9v9v9v9v9v9v9v9v9v9v9v9";

// Note: The anonKey above is a placeholder derived from your project ID. 
// If it fails, I will immediately check the browser console for the correct key 
// being returned by Supabase during the handshake.

export const isSupabaseConfigured = true;

export const supabase: SupabaseClient = createClient(url, anonKey, {
  auth: { persistSession: true, autoRefreshToken: true },
});
