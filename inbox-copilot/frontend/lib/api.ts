import type {
  ActionResponse,
  AuditListResponse,
  DraftResponse,
  EmailDetail,
  EmailListResponse,
} from "./types";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000";

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${API_URL}${path}`, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      ...(init?.headers || {}),
    },
    cache: "no-store",
  });
  if (!res.ok) {
    const text = await res.text();
    throw new Error(`API ${res.status}: ${text}`);
  }
  return res.json() as Promise<T>;
}

export const api = {
  listDrafts: (emailId: string) =>
    request<DraftResponse[]>(`/emails/${emailId}/drafts`),
  listEmails: (params?: { category?: string; priority?: string; limit?: number }) => {
    const qs = new URLSearchParams();
    if (params?.category) qs.set("category", params.category);
    if (params?.priority) qs.set("priority", params.priority);
    if (params?.limit) qs.set("limit", String(params.limit));
    const q = qs.toString();
    return request<EmailListResponse>(`/emails${q ? `?${q}` : ""}`);
  },

  getEmail: (id: string) => request<EmailDetail>(`/emails/${id}`),

  createDraft: (emailId: string, body?: { tone?: string; instructions?: string }) =>
    request<DraftResponse>(`/emails/${emailId}/draft`, {
      method: "POST",
      body: JSON.stringify(body || {}),
    }),

  getDraft: (draftId: string) => request<DraftResponse>(`/drafts/${draftId}`),

  approve: (draftId: string) =>
    request<ActionResponse>(`/drafts/${draftId}/approve`, { method: "POST" }),

  reject: (draftId: string, reason: string) =>
    request<ActionResponse>(`/drafts/${draftId}/reject`, {
      method: "POST",
      body: JSON.stringify({ reason }),
    }),

  send: (draftId: string) =>
    request<ActionResponse>(`/drafts/${draftId}/send`, { method: "POST" }),

  regenerate: (draftId: string, body?: { tone?: string; instructions?: string }) =>
    request<DraftResponse>(`/drafts/${draftId}/regenerate`, {
      method: "POST",
      body: JSON.stringify(body || {}),
    }),

  listAudit: (params?: { entity_id?: string; action?: string; limit?: number }) => {
    const qs = new URLSearchParams();
    if (params?.entity_id) qs.set("entity_id", params.entity_id);
    if (params?.action) qs.set("action", params.action);
    if (params?.limit) qs.set("limit", String(params.limit));
    const q = qs.toString();
    return request<AuditListResponse>(`/audit${q ? `?${q}` : ""}`);
  },
};