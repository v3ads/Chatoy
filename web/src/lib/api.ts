// Browser-side client for the MythoStack backend.
//
// Auth: requests carry a bearer JWT the backend verifies against Supabase. The
// token is the live Supabase session access token when logged in; otherwise it
// falls back to a "dev token" pasted in Settings (handy when the backend runs
// with CHATOY_AUTH_DISABLED=true or you're testing without login).

import { supabase } from "@/lib/supabase";

const API_URL_KEY = "mythostack.apiUrl";
const TOKEN_KEY = "mythostack.token";

const DEFAULT_API_URL =
  process.env.NEXT_PUBLIC_API_URL ?? "http://127.0.0.1:8000";

export interface AppConfig {
  apiUrl: string;
  token: string;
}

export function getConfig(): AppConfig {
  if (typeof window === "undefined") {
    return { apiUrl: DEFAULT_API_URL, token: "" };
  }
  // The deployed API URL (NEXT_PUBLIC_API_URL) always wins, so a stale
  // localStorage value can never point the app at the wrong backend in prod.
  const apiUrl =
    process.env.NEXT_PUBLIC_API_URL || localStorage.getItem(API_URL_KEY) || DEFAULT_API_URL;
  return {
    apiUrl,
    token: localStorage.getItem(TOKEN_KEY) || "",
  };
}

export function setConfig(config: Partial<AppConfig>): void {
  if (typeof window === "undefined") return;
  if (config.apiUrl !== undefined) localStorage.setItem(API_URL_KEY, config.apiUrl);
  if (config.token !== undefined) localStorage.setItem(TOKEN_KEY, config.token);
}

// The bearer token for a request: prefer the live Supabase session (auto
// refreshed), else the manually configured dev token.
async function getAccessToken(): Promise<string> {
  if (supabase) {
    const { data } = await supabase.auth.getSession();
    if (data.session?.access_token) return data.session.access_token;
  }
  return getConfig().token;
}

export interface ChatMessage {
  role: "user" | "assistant";
  content: string;
}

export interface FinalPayload {
  session_id: string;
  reply: string;
  new_messages: ChatMessage[];
  next_step: string;
  current_strategy: Record<string, unknown> | null;
  retrieved_frameworks: string[];
}

function authHeaders(token: string): Record<string, string> {
  const headers: Record<string, string> = { "Content-Type": "application/json" };
  if (token) headers.Authorization = `Bearer ${token}`;
  return headers;
}

function parseEventBlock(block: string): { event: string; data: string } {
  let event = "message";
  const dataLines: string[] = [];
  for (const line of block.split("\n")) {
    if (line.startsWith(":")) continue; // comment / keep-alive
    if (line.startsWith("event:")) {
      event = line.slice(6).trim();
    } else if (line.startsWith("data:")) {
      // Per SSE, strip a single leading space; multiple data lines join with \n.
      let value = line.slice(5);
      if (value.startsWith(" ")) value = value.slice(1);
      dataLines.push(value);
    }
  }
  return { event, data: dataLines.join("\n") };
}

export interface StreamHandlers {
  onToken: (text: string) => void;
  onFinal: (payload: FinalPayload) => void;
  onError: (message: string) => void;
  signal?: AbortSignal;
}

export async function streamChat(
  input: {
    sessionId: string;
    message: string;
    businessProfile?: Record<string, unknown> | null;
  },
  handlers: StreamHandlers,
): Promise<void> {
  const { apiUrl } = getConfig();
  const token = await getAccessToken();
  let res: Response;
  try {
    res = await fetch(`${apiUrl}/chat/stream`, {
      method: "POST",
      headers: authHeaders(token),
      body: JSON.stringify({
        session_id: input.sessionId,
        message: input.message,
        business_profile: input.businessProfile ?? undefined,
      }),
      signal: handlers.signal,
    });
  } catch (err) {
    handlers.onError(`Network error: ${(err as Error).message}`);
    return;
  }

  if (!res.ok || !res.body) {
    let detail = `HTTP ${res.status}`;
    try {
      const body = (await res.json()) as { detail?: string };
      if (body.detail) detail = body.detail;
    } catch {
      /* ignore */
    }
    handlers.onError(detail);
    return;
  }

  const reader = res.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";

  while (true) {
    const { value, done } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true }).replace(/\r\n/g, "\n");
    let sep: number;
    while ((sep = buffer.indexOf("\n\n")) !== -1) {
      const block = buffer.slice(0, sep);
      buffer = buffer.slice(sep + 2);
      const { event, data } = parseEventBlock(block);
      if (event === "token") {
        handlers.onToken(data);
      } else if (event === "final") {
        try {
          handlers.onFinal(JSON.parse(data) as FinalPayload);
        } catch {
          /* ignore malformed final */
        }
      } else if (event === "error") {
        handlers.onError(data);
      }
      // "done" — end of stream marker, no action.
    }
  }
}

export interface VoiceProfileResponse {
  user_id: string;
  profile: Record<string, string>;
  rendered: string;
}

export async function getVoiceProfile(): Promise<VoiceProfileResponse | null> {
  const { apiUrl } = getConfig();
  const token = await getAccessToken();
  const res = await fetch(`${apiUrl}/voice/me`, {
    headers: authHeaders(token),
  });
  if (!res.ok) return null;
  return res.json();
}

export async function analyzeVoice(samples: string[]): Promise<VoiceProfileResponse> {
  const { apiUrl } = getConfig();
  const token = await getAccessToken();
  const res = await fetch(`${apiUrl}/voice/analyze`, {
    method: "POST",
    headers: authHeaders(token),
    body: JSON.stringify({ samples }),
  });
  if (!res.ok) {
    const body = await res.json();
    throw new Error(body.detail || "Failed to analyze voice");
  }
  return res.json();
}

// --- Admin: per-role model selection (OpenRouter) ---

export interface AvailableModel {
  id: string;
  name: string;
}

export interface ModelConfig {
  architect: string | null;
  writer: string | null;
  voice: string | null;
}

async function adminFetch<T>(path: string, init?: RequestInit): Promise<T> {
  const { apiUrl } = getConfig();
  const token = await getAccessToken();
  const res = await fetch(`${apiUrl}${path}`, {
    ...init,
    headers: { ...authHeaders(token), ...(init?.headers ?? {}) },
  });
  if (!res.ok) {
    let detail = `HTTP ${res.status}`;
    try {
      detail = (await res.json()).detail ?? detail;
    } catch {
      /* ignore */
    }
    const err = new Error(detail) as Error & { status?: number };
    err.status = res.status;
    throw err;
  }
  return res.json() as Promise<T>;
}

export function getAvailableModels(): Promise<AvailableModel[]> {
  return adminFetch<AvailableModel[]>("/admin/models/available");
}

export function getModelConfig(): Promise<ModelConfig> {
  return adminFetch<ModelConfig>("/admin/models");
}

export function setModelConfig(cfg: ModelConfig): Promise<ModelConfig> {
  return adminFetch<ModelConfig>("/admin/models", {
    method: "PUT",
    body: JSON.stringify(cfg),
  });
}

export interface KnowledgeStatus {
  count: number;
  semantic: boolean;
  backend?: string | null;
  persistent?: boolean;
}

export function getKnowledgeStatus(): Promise<KnowledgeStatus> {
  return adminFetch<KnowledgeStatus>("/admin/knowledge");
}

export function seedKnowledge(): Promise<{ count: number; chunks: number }> {
  return adminFetch<{ count: number; chunks: number }>("/admin/knowledge/seed", {
    method: "POST",
  });
}
