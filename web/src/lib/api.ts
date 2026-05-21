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
  return {
    apiUrl: localStorage.getItem(API_URL_KEY) || DEFAULT_API_URL,
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
