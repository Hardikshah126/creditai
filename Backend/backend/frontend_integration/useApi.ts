/**
 * React Query hooks for all API calls.
 * Drop in: src/hooks/useApi.ts
 *
 * Usage:
 *   const { data: report } = useMyLatestReport();
 *   const generate = useGenerateReport();
 *   generate.mutateAsync(submissionId);
 */
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api";

// ── Query keys ────────────────────────────────────────────────────────────────

export const QK = {
  me: ["me"],
  submissions: ["submissions"],
  submission: (id: string) => ["submissions", id],
  chatHistory: (id: string) => ["chat", id],
  myLatestReport: ["reports", "latest"],
  myHistory: ["reports", "history"],
  lenderApplicants: (params?: object) => ["lender", "applicants", params],
  lenderReport: (id: string) => ["lender", "report", id],
  sharedReport: (token: string) => ["shared", token],
};

// ── Auth ──────────────────────────────────────────────────────────────────────

export function useMe() {
  return useQuery({ queryKey: QK.me, queryFn: api.auth.me, retry: false });
}

// ── Submissions ───────────────────────────────────────────────────────────────

export function useSubmissions() {
  return useQuery({ queryKey: QK.submissions, queryFn: api.submissions.list });
}

export function useSubmission(id: string) {
  return useQuery({
    queryKey: QK.submission(id),
    queryFn: () => api.submissions.get(id),
    enabled: !!id,
  });
}

export function useCreateSubmission() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: api.submissions.create,
    onSuccess: () => qc.invalidateQueries({ queryKey: QK.submissions }),
  });
}

export function useUploadDocument() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({
      submissionId,
      file,
      docType,
    }: {
      submissionId: string;
      file: File;
      docType: string;
    }) => api.submissions.uploadDocument(submissionId, file, docType),
    onSuccess: (_, vars) => {
      qc.invalidateQueries({ queryKey: QK.submission(vars.submissionId) });
    },
  });
}

export function useAnalyzeDocuments() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (submissionId: string) => api.submissions.analyze(submissionId),
    onSuccess: (_, submissionId) => {
      qc.invalidateQueries({ queryKey: QK.submission(submissionId) });
    },
  });
}

// ── Chat ──────────────────────────────────────────────────────────────────────

export function useChatHistory(submissionId: string) {
  return useQuery({
    queryKey: QK.chatHistory(submissionId),
    queryFn: () => api.chat.history(submissionId),
    enabled: !!submissionId,
  });
}

export function useStartChat() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (submissionId: string) => api.chat.start(submissionId),
    onSuccess: (_, submissionId) => {
      qc.invalidateQueries({ queryKey: QK.chatHistory(submissionId) });
    },
  });
}

export function useSendMessage() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ submissionId, message }: { submissionId: string; message: string }) =>
      api.chat.reply(submissionId, message),
    onSuccess: (data) => {
      qc.invalidateQueries({ queryKey: QK.chatHistory(data.submission_id) });
    },
  });
}

// ── Reports ───────────────────────────────────────────────────────────────────

export function useMyLatestReport() {
  return useQuery({
    queryKey: QK.myLatestReport,
    queryFn: api.reports.myLatest,
    retry: false,
  });
}

export function useMyReportHistory() {
  return useQuery({ queryKey: QK.myHistory, queryFn: api.reports.myHistory });
}

export function useGenerateReport() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (submissionId: string) => api.reports.generate(submissionId),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: QK.myLatestReport });
      qc.invalidateQueries({ queryKey: QK.myHistory });
    },
  });
}

export function useShareReport() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (reportId: string) => api.reports.share(reportId),
    onSuccess: () => qc.invalidateQueries({ queryKey: QK.myLatestReport }),
  });
}

export function useSharedReport(token: string) {
  return useQuery({
    queryKey: QK.sharedReport(token),
    queryFn: () => api.reports.getShared(token),
    enabled: !!token,
  });
}

// ── Lender ────────────────────────────────────────────────────────────────────

export function useLenderApplicants(params?: { risk_tier?: string; search?: string }) {
  return useQuery({
    queryKey: QK.lenderApplicants(params),
    queryFn: () => api.lender.listApplicants(params),
  });
}

export function useLenderReport(reportId: string) {
  return useQuery({
    queryKey: QK.lenderReport(reportId),
    queryFn: () => api.lender.getReport(reportId),
    enabled: !!reportId,
  });
}

export function useRecordDecision() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: api.lender.recordDecision,
    onSuccess: () => qc.invalidateQueries({ queryKey: ["lender"] }),
  });
}
