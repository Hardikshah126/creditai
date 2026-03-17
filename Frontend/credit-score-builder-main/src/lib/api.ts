const API_BASE = "http://localhost:8000/api/v1";

function getToken(): string | null {
  return localStorage.getItem("token");
}

export function saveToken(token: string) {
  localStorage.setItem("token", token);
}

export function clearToken() {
  localStorage.removeItem("token");
  localStorage.removeItem("user");
}

export function getUser() {
  const u = localStorage.getItem("user");
  return u ? JSON.parse(u) : null;
}

export function saveUser(user: object) {
  localStorage.setItem("user", JSON.stringify(user));
}

export async function apiFetch(path: string, options: RequestInit = {}) {
  const token = getToken();
  const res = await fetch(`${API_BASE}${path}`, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...options.headers,
    },
  });

  if (!res.ok) {
    const error = await res.json().catch(() => ({ detail: "Unknown error" }));
    throw new Error(error.detail || `HTTP ${res.status}`);
  }

  return res.json();
}

// ── Auth ──────────────────────────────────────────────────────────────────────

export async function signup(data: {
  name: string;
  phone: string;
  country: string;
  email?: string;
  password: string;
}) {
  const res = await apiFetch("/auth/signup", {
    method: "POST",
    body: JSON.stringify(data),
  });
  saveToken(res.access_token);
  saveUser(res.user);
  return res;
}

export async function login(identifier: string, password: string) {
  const res = await apiFetch("/auth/login", {
    method: "POST",
    body: JSON.stringify({ identifier, password }),
  });
  saveToken(res.access_token);
  saveUser(res.user);
  return res;
}

// ── Submissions ───────────────────────────────────────────────────────────────

export async function createSubmission() {
  return apiFetch("/submissions/", { method: "POST" });
}

export async function uploadDocument(
  submissionId: number,
  file: File,
  docType: string
) {
  const token = getToken();
  const form = new FormData();
  form.append("file", file);
  form.append("doc_type", docType);

  const res = await fetch(
    `${API_BASE}/submissions/${submissionId}/documents`,
    {
      method: "POST",
      headers: {
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
      },
      body: form,
    }
  );

  if (!res.ok) {
    const error = await res.json().catch(() => ({ detail: "Upload failed" }));
    throw new Error(error.detail || `HTTP ${res.status}`);
  }

  return res.json();
}

export async function getDashboard() {
  return apiFetch("/submissions/dashboard");
}

// ── Agent ─────────────────────────────────────────────────────────────────────

export async function sendMessage(submissionId: number, content: string) {
  return apiFetch(`/agent/${submissionId}/message`, {
    method: "POST",
    body: JSON.stringify({ content }),
  });
}

export async function getConversation(submissionId: number) {
  return apiFetch(`/agent/${submissionId}/conversation`);
}

// ── Reports ───────────────────────────────────────────────────────────────────

export async function generateReport(submissionId: number) {
  return apiFetch(`/reports/${submissionId}/generate`, { method: "POST" });
}

export async function getLatestReport() {
  return apiFetch("/reports/latest");
}

export async function shareReport(submissionId: number) {
  return apiFetch(`/reports/${submissionId}/share`, { method: "POST" });
}

export async function getReportPdfUrl(submissionId: number): Promise<string> {
  return `${API_BASE}/reports/${submissionId}/pdf`;
}

// ── Lender ────────────────────────────────────────────────────────────────────

export async function getLenderApplicants(search?: string, riskTier?: string) {
  const params = new URLSearchParams();
  if (search) params.set("search", search);
  if (riskTier) params.set("risk_tier", riskTier);
  const query = params.toString();
  return apiFetch(`/lender/applicants${query ? `?${query}` : ""}`);
}

export async function getLenderReport(reportId: number) {
  return apiFetch(`/lender/applicants/${reportId}`);
}

export async function recordDecision(
  reportId: number,
  decision: string,
  notes?: string
) {
  return apiFetch(`/lender/applicants/${reportId}/decision`, {
    method: "PATCH",
    body: JSON.stringify({ decision, notes }),
  });
}

// ── History ───────────────────────────────────────────────────────────────────

export async function getHistory() {
  return apiFetch("/history/");
}

// ── Settings ──────────────────────────────────────────────────────────────────

export async function updateProfile(data: {
  name?: string;
  phone?: string;
  country?: string;
  email?: string;
}) {
  return apiFetch("/settings/profile", {
    method: "PATCH",
    body: JSON.stringify(data),
  });
}