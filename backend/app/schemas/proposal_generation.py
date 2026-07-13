import uuid
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class ProposalVersionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    proposal_id: uuid.UUID
    version_number: int
    created_by: str = "ai"
    change_summary: str | None = None
    cover_letter: str | None = None
    executive_summary: str | None = None
    why_good_fit: str | None = None
    relevant_experience: str | None = None
    bid_amount: float | None = None
    bid_type: str | None = None
    estimated_duration: str | None = None
    milestones: str | None = None
    risk_notes: str | None = None
    confidence_explanation: str | None = None
    proposal_summary: str | None = None
    prompt_version: str | None = None
    model: str | None = None
    temperature: float | None = None
    tokens_used: int | None = None
    created_at: datetime


class ProposalGenerationResponse(BaseModel):
    proposal_id: uuid.UUID
    version_id: uuid.UUID
    version_number: int
    cover_letter: str | None = None
    bid_amount: Decimal | None = None
    bid_type: str | None = None
    estimated_duration: str | None = None
    status: str


class DuplicateProposalResponse(BaseModel):
    id: uuid.UUID
    project_id: uuid.UUID
    status: str
    cover_letter: str | None = None


class ProposalVersionListResponse(BaseModel):
    items: list[ProposalVersionResponse]
    total: int
    skip: int
    limit: int


# --- Proposal Improvement ---

class ImproveRequest(BaseModel):
    style: str = Field(
        ...,
        description="Improvement style: shorter, longer, more_technical, less_technical, more_persuasive, formal, casual, custom",
    )
    custom_instruction: str | None = Field(
        None,
        description="Custom instruction when style='custom'",
        max_length=1000,
    )
    focus_section: str | None = Field(
        None,
        description="Optional section to focus on (e.g. 'coverLetter', 'executiveSummary')",
    )


class ImproveResponse(BaseModel):
    proposal_id: uuid.UUID
    version_id: uuid.UUID
    version_number: int
    style: str
    cover_letter: str | None = None
    status: str


# --- Proposal Evaluation ---

class EvaluationScoreResponse(BaseModel):
    overall_score: float
    completeness_score: float
    persuasiveness_score: float
    relevance_score: float
    clarity_score: float
    formatting_score: float
    strengths: list[str]
    weaknesses: list[str]
    suggestions: list[str]


class EvaluationResponse(BaseModel):
    proposal_id: uuid.UUID
    version_id: uuid.UUID | None = None
    scores: EvaluationScoreResponse


# --- Human Approval ---

class ApproveRequest(BaseModel):
    pass


class RejectRequest(BaseModel):
    reason: str | None = Field(None, max_length=500)


class ApprovalResponse(BaseModel):
    id: uuid.UUID
    status: str
    message: str
