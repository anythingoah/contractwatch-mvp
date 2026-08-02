/**
 * Thin, typed fetch wrapper around the FastAPI backend.
 *
 * Auth: the backend sets an httpOnly cookie on login/signup — the frontend
 * never sees or stores the raw token (no localStorage), it just sends
 * `credentials: "include"` so the browser attaches the cookie automatically.
 */
const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export class ApiError extends Error {
  status: number;
  constructor(message: string, status: number) {
    super(message);
    this.status = status;
    this.name = "ApiError";
  }
}

function getErrorDetail(body: unknown): string | null {
  if (
    typeof body === "object" &&
    body !== null &&
    "detail" in body
  ) {
    const detail = body.detail;
    if (typeof detail === "string") return detail;
    if (Array.isArray(detail)) {
      const first = detail[0];
      if (typeof first === "object" && first !== null && "msg" in first && typeof first.msg === "string") {
        return first.msg;
      }
    }
  }
  return null;
}

async function request<T>(path: string, options: RequestInit = {}, timeoutMs =  60000): Promise<T> {
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), timeoutMs);

  let res: Response;
  try {
    res = await fetch(`${API_URL}${path}`, {
      ...options,
      credentials: "include", // send the httpOnly auth cookie
      headers: { "Content-Type": "application/json", ...(options.headers as Record<string, string>) },
      signal: controller.signal,
    });
  } catch (err: unknown) {
    clearTimeout(timeout);
    if (err instanceof Error && err.name === "AbortError") throw new ApiError("Request timed out", 0);
    throw new ApiError("Network error — check your connection", 0);
  }
  clearTimeout(timeout);

  if (!res.ok) {
    const body: unknown = await res.json().catch(() => null);
    throw new ApiError(getErrorDetail(body) ?? `Request failed: ${res.status}`, res.status);
  }
  if (res.status === 204) return null as T;
  const text = await res.text();
return text ? JSON.parse(text) as T : (null as T);
}

// --- Domain types (mirrors backend Pydantic response models) ---

export interface User {
  id: number;
  email: string;
  plan: string;
}

export interface Monitor {
  id: number;
  name: string;
  type: "rest" | "mcp";
  status: "healthy" | "breaking_change" | "unreachable" | "pending";
  frequency: "daily" | "hourly" | "every_15_min";
  last_checked: string | null;
  created_at: string;
  change_count: number;
}

export interface Change {
  id: number;
  change_type: string;
  severity: "critical" | "warning" | "info";
  summary: string;
  details: Record<string, unknown> | null;
  acknowledged: boolean;
  created_at: string;
}

export interface RecentChange {
  id: number;
  monitor_id: number;
  monitor_name: string;
  change_type: string;
  severity: "critical" | "warning" | "info";
  summary: string;
  created_at: string;
}

export interface CheckResult {
  status: string;
  changes_detected: number;
  breaking: boolean;
}

export interface AlertChannelInput {
  type: "slack" | "email" | "webhook";
  configuration: Record<string, string>;
}

export interface MonitorCreateInput {
  name: string;
  type: "rest" | "mcp";
  frequency: "daily" | "hourly" | "every_15_min";
  api_url?: string;
  openapi_spec_url?: string;
  mcp_server_url?: string;
  mcp_transport?: string;
  channels: AlertChannelInput[];
}

export const api = {
  signup: (email: string, password: string) =>
    request<User>("/auth/signup", { method: "POST", body: JSON.stringify({ email, password }) }),
  login: (email: string, password: string) =>
    request<User>("/auth/login", { method: "POST", body: JSON.stringify({ email, password }) }),
  logout: () => request<{ status: string }>("/auth/logout", { method: "POST" }),
  me: () => request<User>("/auth/me"),

  listMonitors: () => request<Monitor[]>("/monitors"),
  getMonitor: (id: number) => request<Monitor>(`/monitors/${id}`),
  createMonitor: (payload: MonitorCreateInput) =>
    request<Monitor>("/monitors", { method: "POST", body: JSON.stringify(payload) }),
  deleteMonitor: (id: number) => request<null>(`/monitors/${id}`, { method: "DELETE" }),
  checkNow: (id: number) => request<CheckResult>(`/monitors/${id}/check`, { method: "POST" }),
  getChanges: (id: number) => request<Change[]>(`/monitors/${id}/changes`),
  getRecentChanges: (limit = 20) => request<RecentChange[]>(`/monitors/changes?limit=${limit}`),
};