import uuid
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


# --- Status transitions ---

class StatusTransitionRequest(BaseModel):
    pass


class StatusTransitionResponse(BaseModel):
    id: uuid.UUID
    status: str
    message: str


# --- Proposal Editor ---

class ProposalEditRequest(BaseModel):
    model_config = ConfigDict(json_schema_extra={
        "example": {
            "cover_letter": "Updated proposal cover letter...",
            "bid_amount": 2500.00,
            "estimated_duration": "3 weeks",
            "change_summary": "Updated pricing and timeline",
        }
    })

    title: str | None = None
    cover_letter: str | None = None
    executive_summary: str | None = None
    why_good_fit: str | None = None
    relevant_experience: str | None = None
    bid_amount: Decimal | None = None
    bid_type: str | None = None
    estimated_duration: str | None = None
    milestones: str | None = None
    risk_notes: str | None = None
    confidence_explanation: str | None = None
    proposal_summary: str | None = None
    change_summary: str | None = None


class ProposalEditResponse(BaseModel):
    proposal_id: uuid.UUID
    version_id: uuid.UUID
    version_number: int
    status: str


# --- Rollback ---

class RollbackRequest(BaseModel):
    model_config = ConfigDict(json_schema_extra={
        "example": {
            "version_id": "00000000-0000-0000-0000-000000000000",
            "change_summary": "Reverting to original scope",
        }
    })

    version_id: uuid.UUID
    change_summary: str | None = None


class RollbackResponse(BaseModel):
    proposal_id: uuid.UUID
    version_id: uuid.UUID
    version_number: int
    status: str
    message: str


# --- Comparison ---

class SectionDiff(BaseModel):
    section: str
    old_value: str | None = None
    new_value: str | None = None
    change_type: str  # "added", "removed", "modified", "unchanged"


class ComparisonStats(BaseModel):
    total_sections: int
    changed_sections: int
    added_sections: int
    removed_sections: int
    modified_sections: int
    words_added: int
    words_removed: int


class ComparisonResponse(BaseModel):
    proposal_id: uuid.UUID
    version_old: int
    version_new: int
    section_diffs: list[SectionDiff]
    stats: ComparisonStats


# --- Submission Readiness ---

class ReadinessCheck(BaseModel):
    field: str
    status: str  # "pass" or "fail"
    message: str


class ReadinessResponse(BaseModel):
    ready: bool
    checks: list[ReadinessCheck]


# --- Proposal Notes ---

class NoteCreateRequest(BaseModel):
    model_config = ConfigDict(json_schema_extra={
        "example": {"content": "Client mentioned budget flexibility in the call."}
    })

    content: str = Field(..., min_length=1)


class NoteUpdateRequest(BaseModel):
    model_config = ConfigDict(json_schema_extra={
        "example": {"content": "Updated: budget confirmed at $3k."}
    })

    content: str = Field(..., min_length=1)


class NoteResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    proposal_id: uuid.UUID
    user_id: uuid.UUID
    content: str
    created_at: datetime
    updated_at: datetime


class NoteListResponse(BaseModel):
    items: list[NoteResponse]
    total: int


# --- Audit Log ---

class AuditLogEntry(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    proposal_id: uuid.UUID | None = None
    user_id: uuid.UUID
    action: str
    details: str | None = None
    created_at: datetime


class AuditLogListResponse(BaseModel):
    items: list[AuditLogEntry]
    total: int


# --- ProposalVersion extended response ---

class ProposalVersionDetailResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    proposal_id: uuid.UUID
    version_number: int
    created_by: str
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


class ProposalVersionListResponse(BaseModel):
    items: list[ProposalVersionDetailResponse]
    total: int
    skip: int
    limit: int
