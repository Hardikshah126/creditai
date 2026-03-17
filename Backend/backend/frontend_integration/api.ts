/**
 * CreditAI API client
 * Drop this in: src/lib/api.ts
 *
 * All API calls go through here. Reads the JWT from localStorage,
 * attaches it to every request, and throws HTTPError on non-2xx responses.
 */

const BASE_URL = import.meta.env.VITE_API_URL ?? "http://localhost:8000/api/v1";

// ─── Types (mirror backend schemas) ──────────────────────────────────────────

export interface TokenResponse {
  access_token: string;
  token_type: string;
  user_id: string;
  name: string;
  role: string;
}

export interface UserResponse {
  id: string;
  name: string;
  phone: string;
  email: string | null;
  country: string;
  role: string;
  created_at: string;
}

export interface DocumentResponse {
  id: string;
  doc_type: string;
  file_name: string;
  file_size_bytes: number | null;
  processing_status: string;
  confidence_score: number | null;
  created_at: string;
}

export interface SubmissionResponse {
  id: string;
  status: string;
  created_at: string;
  updated_at: string;
  documents: DocumentResponse[];
}

export interface ChatReplyResponse {
  submission_id: string;
  ai_message: string;
  chips: string[] | null;
  is_complete: boolean;
  turn_index: number;
}

export interface ChatMessage {
  role: "ai" | "user";
  message: string;
  chips: string[] | null;
  turn_index: number;
  created_at: string;
}

export interface SignalBreakdown {
  title: string;
  icon: string;
  contribution: number;
  strength: "strong" | "good" | "moderate" | "weak";
  percent: number;
  detail: string;
}

export interface CreditReportResponse {
  id: string;
  submission_id: string;
  score: number;
  risk_tier: "low" | "medium" | "high";
  model_version: string;
  breakdown: SignalBreakdown[];
  summary_text: string | null;
  positive_signals: string[];
  improvement_areas: string[];
  share_token: string | null;
  is_shared_with_lender: boolean;
  created_at: string;
}

export interface LenderApplicantSummary {
  report_id: string;
  applicant_name: string;
  applicant_country: string;
  score: number;
  risk_tier: "low" | "medium" | "high";
  sources: string[];
  submitted_at: string;
}

export interface LenderDecisionRequest {
  report_id: string;
  decision: "approved" | "declined" | "manual_review";
  notes?: string;
}

// ─── Token helpers ────────────────────────────────────────────────────────────

export const TOKEN_KEY = "creditai_token";
export const USER_KEY = "creditai_user";

export function saveSession(token: TokenResponse) {
  localStorage.setItem(TOKEN_KEY, token.access_token);
  localStorage.setItem(
    USER_KEY,
    JSON.stringify({ id: token.user_id, name: token.name, role: token.role })
  );
}

export function clearSession() {
  localStorage.removeItem(TOKEN_KEY);
  localStorage.removeItem(USER_KEY);
}

export function getToken(): string | null {
  return localStorage.getItem(TOKEN_KEY);
}

export function getSessionUser(): { id: string; name: string; role: string } | null {
  const raw = localStorage.getItem(USER_KEY);
  return raw ? JSON.parse(raw) : null;
}

// ─── Fetch wrapper ────────────────────────────────────────────────────────────

class APIError extends Error {
  constructor(
    public status: number,
    public detail: string
  ) {
    super(detail);
    this.name = "APIError";
  }
}

async function request<T>(
  path: string,
  options: RequestInit = {},
  isFormData = false
): Promise<T> {
  const token = getToken();
  const headers: Record<string, string> = {
    ...(isFormData ? {} : { "Content-Type": "application/json" }),
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
    ...(options.headers as Record<string, string>),
  };

  const res = await fetch(`${BASE_URL}${path}`, { ...options, headers });

  if (!res.ok) {
    let detail = `HTTP ${res.status}`;
    try {
      const body = await res.json();
      detail = body.detail ?? detail;
    } catch {}
    throw new APIError(res.status, detail);
  }

  if (res.status === 204) return undefined as T;
  return res.json();
}

// ─── Auth ─────────────────────────────────────────────────────────────────────

export const api = {
  auth: {
    signup: (body: {
      name: string;
      phone: string;
      country: string;
      password: string;
      email?: string;
      role?: string;
    }) => request<TokenResponse>("/auth/signup", { method: "POST", body: JSON.stringify(body) }),

    login: (phone: string, password: string) =>
      request<TokenResponse>("/auth/login", {
        method: "POST",
        body: JSON.stringify({ phone, password }),
      }),

    me: () => request<UserResponse>("/auth/me"),

    updateMe: (body: Partial<UserResponse>) =>
      request<UserResponse>("/auth/me", { method: "PUT", body: JSON.stringify(body) }),
  },

  // ─── Submissions ────────────────────────────────────────────────────────────

  submissions: {
    create: () =>
      request<SubmissionResponse>("/submissions", { method: "POST", body: JSON.stringify({}) }),

    get: (id: string) => request<SubmissionResponse>(`/submissions/${id}`),

    list: () => request<SubmissionResponse[]>("/submissions"),

    uploadDocument: (submissionId: string, file: File, docType: string) => {
      const form = new FormData();
      form.append("file", file);
      form.append("doc_type", docType);
      return request<DocumentResponse>(
        `/submissions/${submissionId}/documents`,
        { method: "POST", body: form },
        true
      );
    },

    analyze: (submissionId: string) =>
      request<{ status: string; documents_processed: number }>(
        `/submissions/${submissionId}/analyze`,
        { method: "POST" }
      ),
  },

  // ─── Chat ───────────────────────────────────────────────────────────────────

  chat: {
    start: (submissionId: string) =>
      request<ChatReplyResponse>(`/chat/start?submission_id=${submissionId}`, { method: "POST" }),

    reply: (submissionId: string, message: string) =>
      request<ChatReplyResponse>("/chat/reply", {
        method: "POST",
        body: JSON.stringify({ submission_id: submissionId, message }),
      }),

    history: (submissionId: string) =>
      request<{ submission_id: string; messages: ChatMessage[] }>(
        `/chat/${submissionId}/history`
      ),
  },

  // ─── Reports ────────────────────────────────────────────────────────────────

  reports: {
    generate: (submissionId: string) =>
      request<CreditReportResponse>(`/reports/${submissionId}/generate`, { method: "POST" }),

    myLatest: () => request<CreditReportResponse>("/reports/my/latest"),

    myHistory: () => request<CreditReportResponse[]>("/reports/my/history"),

    share: (reportId: string) =>
      request<{ share_token: string; share_url: string }>(
        `/reports/${reportId}/share`,
        { method: "POST" }
      ),

    getShared: (token: string) => request<CreditReportResponse>(`/reports/shared/${token}`),
  },

  // ─── Lender ─────────────────────────────────────────────────────────────────

  lender: {
    listApplicants: (params?: { risk_tier?: string; search?: string }) => {
      const qs = new URLSearchParams();
      if (params?.risk_tier) qs.set("risk_tier", params.risk_tier);
      if (params?.search) qs.set("search", params.search);
      return request<LenderApplicantSummary[]>(
        `/reports/lender/applicants?${qs.toString()}`
      );
    },

    getReport: (reportId: string) =>
      request<CreditReportResponse>(`/reports/lender/${reportId}`),

    recordDecision: (body: LenderDecisionRequest) =>
      request("/reports/lender/decision", { method: "POST", body: JSON.stringify(body) }),
  },
};

export { APIError };
