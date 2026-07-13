import { api } from "@/lib/api";
import type { PaginatedResponse } from "@/types/api";
import type { Opportunity } from "@/types/api";

export interface JobFilters {
  search?: string;
  status?: string;
  category?: string;
  min_budget?: number;
  max_budget?: number;
  page?: number;
  size?: number;
}

export const jobsService = {
  async list(filters: JobFilters = {}): Promise<PaginatedResponse<Opportunity>> {
    const params = new URLSearchParams();
    Object.entries(filters).forEach(([k, v]) => { if (v !== undefined && v !== "") params.set(k, String(v)); });
    const res = await api.get("/opportunities", { params });
    return res.data;
  },

  async getById(id: string): Promise<Opportunity> {
    const res = await api.get(`/opportunities/${id}`);
    return res.data;
  },
};
