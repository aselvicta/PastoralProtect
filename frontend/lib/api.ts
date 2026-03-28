const BASE = process.env.NEXT_PUBLIC_API_BASE_URL || "http://127.0.0.1:8000";

const TOKEN_KEY = "pastoralprotect_token";

/** Turn FastAPI JSON errors (and plain text) into a short message for users. */
export function parseApiErrorBody(text: string): string {
  const trimmed = text.trim();
  if (!trimmed) return "Something went wrong. Please try again.";
  try {
    const j = JSON.parse(trimmed) as { detail?: unknown };
    if (j.detail == null) return trimmed.length > 200 ? `${trimmed.slice(0, 200)}…` : trimmed;
    const d = j.detail;
    if (typeof d === "string") return d;
    if (Array.isArray(d)) {
      const first = d[0];
      if (typeof first === "string") return first;
      if (first && typeof first === "object" && first !== null && "msg" in first) {
        return String((first as { msg: string }).msg);
      }
    }
    return trimmed.length > 200 ? `${trimmed.slice(0, 200)}…` : trimmed;
  } catch {
    return trimmed.length > 200 ? `${trimmed.slice(0, 200)}…` : trimmed;
  }
}

async function throwIfNotOk(r: Response): Promise<void> {
  if (r.ok) return;
  const text = await r.text();
  throw new Error(parseApiErrorBody(text));
}

export function getStoredToken(): string | null {
  if (typeof window === "undefined") return null;
  return sessionStorage.getItem(TOKEN_KEY);
}

export function setStoredToken(token: string | null) {
  if (typeof window === "undefined") return;
  if (token) sessionStorage.setItem(TOKEN_KEY, token);
  else sessionStorage.removeItem(TOKEN_KEY);
  window.dispatchEvent(new Event("pastoral-auth-change"));
}

export async function apiGet<T>(path: string, token?: string | null): Promise<T> {
  const headers: HeadersInit = {};
  const t = token ?? getStoredToken();
  if (t) headers.Authorization = `Bearer ${t}`;
  const r = await fetch(`${BASE}${path}`, { cache: "no-store", headers });
  await throwIfNotOk(r);
  return r.json() as Promise<T>;
}

export async function apiPost<T>(path: string, body: unknown, token?: string | null): Promise<T> {
  const headers: HeadersInit = { "Content-Type": "application/json" };
  const t = token ?? getStoredToken();
  if (t) headers.Authorization = `Bearer ${t}`;
  const r = await fetch(`${BASE}${path}`, {
    method: "POST",
    headers,
    body: JSON.stringify(body),
  });
  await throwIfNotOk(r);
  return r.json() as Promise<T>;
}

export { BASE as API_BASE };
