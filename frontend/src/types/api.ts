export interface Opportunity {
  id: string;
  title: string;
  description: string;
  budget_min?: number;
  budget_max?: number;
  currency: string;
  status: string;
  score?: number;
  estimated_earnings?: number;
  category?: string;
  skills?: string[];
  created_at: string;
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  size: number;
}

export interface ApiError {
  detail: string;
  error_code?: string;
}
