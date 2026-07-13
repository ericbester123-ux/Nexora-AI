import { api } from "@/lib/api";
import type { PaginatedResponse } from "@/types/api";
import type {
  ApprovalResponse,
  AuditLogEntry,
  ComparisonResponse,
  EvaluationResponse,
  ImproveRequest,
  ImproveResponse,
  Note,
  Proposal,
  ProposalEditRequest,
  ProposalVersion,
  ReadinessResponse,
  StatusTransitionResponse,
} from "@/types/proposal";

export const proposalService = {
  async list(params?: { skip?: number; limit?: number; status?: string }): Promise<PaginatedResponse<Proposal>> {
    const res = await api.get("/proposals", { params });
    return res.data;
  },

  async getById(id: string): Promise<Proposal> {
    const res = await api.get(`/proposals/${id}`);
    return res.data;
  },

  async create(data: { project_id: string; cover_letter?: string; bid_amount?: number }): Promise<Proposal> {
    const res = await api.post("/proposals", data);
    return res.data;
  },

  async review(id: string): Promise<StatusTransitionResponse> {
    const res = await api.post(`/proposals/${id}/review`);
    return res.data;
  },

  async markReady(id: string): Promise<StatusTransitionResponse> {
    const res = await api.post(`/proposals/${id}/ready`);
    return res.data;
  },

  async markSubmitted(id: string): Promise<StatusTransitionResponse> {
    const res = await api.post(`/proposals/${id}/submitted`);
    return res.data;
  },

  async archive(id: string): Promise<StatusTransitionResponse> {
    const res = await api.post(`/proposals/${id}/archive`);
    return res.data;
  },

  async readiness(id: string): Promise<ReadinessResponse> {
    const res = await api.get(`/proposals/${id}/readiness`);
    return res.data;
  },

  async edit(id: string, data: ProposalEditRequest) {
    const res = await api.post(`/proposals/${id}/edit`, data);
    return res.data;
  },

  async versions(id: string): Promise<PaginatedResponse<ProposalVersion>> {
    const res = await api.get(`/proposals/${id}/versions`);
    return res.data;
  },

  async rollback(id: string, versionId: string, changeSummary?: string) {
    const res = await api.post(`/proposals/${id}/rollback`, {
      version_id: versionId,
      change_summary: changeSummary,
    });
    return res.data;
  },

  async compare(id: string, v1: string, v2: string): Promise<ComparisonResponse> {
    const res = await api.get(`/proposals/${id}/compare`, { params: { v1, v2 } });
    return res.data;
  },

  async notes(id: string): Promise<{ items: Note[]; total: number }> {
    const res = await api.get(`/proposals/${id}/notes`);
    return res.data;
  },

  async createNote(id: string, content: string): Promise<Note> {
    const res = await api.post(`/proposals/${id}/notes`, { content });
    return res.data;
  },

  async auditLog(id: string): Promise<{ items: AuditLogEntry[]; total: number }> {
    const res = await api.get(`/proposals/${id}/audit-log`);
    return res.data;
  },

  async duplicate(id: string): Promise<Proposal> {
    const res = await api.post(`/proposals/${id}/duplicate`);
    return res.data;
  },

  async improve(id: string, data: ImproveRequest): Promise<ImproveResponse> {
    const res = await api.post(`/proposals/${id}/improve`, data);
    return res.data;
  },

  async evaluate(id: string): Promise<EvaluationResponse> {
    const res = await api.post(`/proposals/${id}/evaluate`);
    return res.data;
  },

  async requestApproval(id: string): Promise<StatusTransitionResponse> {
    const res = await api.post(`/proposals/${id}/request-approval`);
    return res.data;
  },

  async approve(id: string): Promise<ApprovalResponse> {
    const res = await api.post(`/proposals/${id}/approve`);
    return res.data;
  },

  async reject(id: string, reason?: string): Promise<ApprovalResponse> {
    const res = await api.post(`/proposals/${id}/reject`, { reason });
    return res.data;
  },

  async queue(id: string): Promise<StatusTransitionResponse> {
    const res = await api.post(`/proposals/${id}/queue`);
    return res.data;
  },
};
