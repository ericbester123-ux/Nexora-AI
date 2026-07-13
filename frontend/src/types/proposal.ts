export interface Proposal {
  id: string;
  project_id: string;
  user_id: string;
  title?: string;
  cover_letter?: string;
  bid_amount?: number;
  bid_type?: string;
  estimated_duration?: string;
  status: string;
  ai_score?: number;
  ai_generated?: boolean;
  ai_evaluation_score?: number;
  rejection_reason?: string;
  human_approved_at?: string;
  created_at: string;
  updated_at: string;
}

export interface ProposalVersion {
  id: string;
  proposal_id: string;
  version_number: number;
  created_by: string;
  change_summary?: string;
  cover_letter?: string;
  executive_summary?: string;
  bid_amount?: number;
  bid_type?: string;
  estimated_duration?: string;
  created_at: string;
}

export interface ReadinessCheck {
  field: string;
  status: "pass" | "fail";
  message: string;
}

export interface ReadinessResponse {
  ready: boolean;
  checks: ReadinessCheck[];
}

export interface StatusTransitionResponse {
  id: string;
  status: string;
  message: string;
}

export interface Note {
  id: string;
  proposal_id: string;
  user_id: string;
  content: string;
  created_at: string;
  updated_at: string;
}

export interface AuditLogEntry {
  id: string;
  proposal_id: string;
  user_id: string;
  action: string;
  details?: string;
  created_at: string;
}

export interface ComparisonResponse {
  proposal_id: string;
  version_old: number;
  version_new: number;
  section_diffs: Array<{
    section: string;
    old_value?: string;
    new_value?: string;
    change_type: string;
  }>;
}

export interface ProposalEditRequest {
  cover_letter?: string;
  bid_amount?: number;
  bid_type?: string;
  estimated_duration?: string;
  change_summary?: string;
}

export interface ImproveRequest {
  style: string;
  custom_instruction?: string;
  focus_section?: string;
}

export interface ImproveResponse {
  proposal_id: string;
  version_id: string;
  version_number: number;
  style: string;
  cover_letter?: string;
  status: string;
}

export interface EvaluationScoreResponse {
  overall_score: number;
  completeness_score: number;
  persuasiveness_score: number;
  relevance_score: number;
  clarity_score: number;
  formatting_score: number;
  strengths: string[];
  weaknesses: string[];
  suggestions: string[];
}

export interface EvaluationResponse {
  proposal_id: string;
  version_id?: string;
  scores: EvaluationScoreResponse;
}

export interface ApprovalResponse {
  id: string;
  status: string;
  message: string;
}
