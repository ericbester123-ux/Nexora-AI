"""
Proposal CRUD, AI generation, and human review endpoints.
"""

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel

from app.dependencies.auth import (
    CurrentUser,
    get_ai_preference_repository,
    get_audit_service,
    get_proposal_evaluator,
    get_proposal_generation_service,
    get_proposal_improver,
    get_proposal_note_service,
    get_proposal_review_service,
    get_proposal_service,
    get_proposal_version_repository,
    get_user_preference_repository,
)
from app.repositories.preference_repository import (
    AIPreferenceRepository,
    UserPreferenceRepository,
)
from app.repositories.proposal_version_repository import ProposalVersionRepository
from app.schemas.auth import MessageResponse
from app.schemas.proposal import ProposalCreate, ProposalResponse, ProposalUpdate
from app.schemas.proposal_generation import (
    ApprovalResponse,
    ApproveRequest,
    DuplicateProposalResponse,
    EvaluationResponse,
    EvaluationScoreResponse,
    ImproveRequest,
    ImproveResponse,
    ProposalGenerationResponse,
    RejectRequest,
)
from app.schemas.proposal_review import (
    AuditLogEntry,
    AuditLogListResponse,
    ComparisonResponse,
    NoteCreateRequest,
    NoteListResponse,
    NoteResponse,
    NoteUpdateRequest,
    ProposalEditRequest,
    ProposalEditResponse,
    ProposalVersionDetailResponse,
    ProposalVersionListResponse,
    ReadinessResponse,
    RollbackRequest,
    RollbackResponse,
    StatusTransitionResponse,
)
from app.services.audit_service import AuditService
from app.services.proposal_evaluator import ProposalEvaluator
from app.services.proposal_generation_service import ProposalGenerationService
from app.services.proposal_improver import ProposalImprover
from app.services.proposal_note_service import ProposalNoteService
from app.services.proposal_review_service import ProposalReviewService
from app.services.proposal_service import ProposalService


class Page(BaseModel):
    items: list[ProposalResponse]
    total: int
    page: int
    size: int


router = APIRouter(prefix="/proposals", tags=["Proposals"])


# --- CRUD ---


@router.get("", response_model=Page, summary="List proposals for the current user")
async def list_proposals(
    current_user: CurrentUser,
    proposal_service: Annotated[ProposalService, Depends(get_proposal_service)],
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    search: str | None = Query(None),
    status: str | None = Query(None),
    project_id: uuid.UUID | None = Query(None),
) -> Page:
    items, total = await proposal_service.get_all(
        user_id=current_user.id,
        skip=skip,
        limit=limit,
        search=search,
        status=status,
        project_id=project_id,
    )
    return Page(items=items, total=total, page=(skip // limit) + 1, size=limit)


@router.get("/{proposal_id}", response_model=ProposalResponse, summary="Get a proposal by ID")
async def get_proposal(
    proposal_id: uuid.UUID,
    current_user: CurrentUser,
    proposal_service: Annotated[ProposalService, Depends(get_proposal_service)],
) -> ProposalResponse:
    proposal = await proposal_service.get_by_id(proposal_id, user_id=current_user.id)
    return ProposalResponse.model_validate(proposal)


@router.post("", response_model=ProposalResponse, status_code=201, summary="Create a new proposal")
async def create_proposal(
    payload: ProposalCreate,
    current_user: CurrentUser,
    proposal_service: Annotated[ProposalService, Depends(get_proposal_service)],
) -> ProposalResponse:
    proposal = await proposal_service.create(user_id=current_user.id, payload=payload)
    return ProposalResponse.model_validate(proposal)


@router.put("/{proposal_id}", response_model=ProposalResponse, summary="Update a proposal")
async def update_proposal(
    proposal_id: uuid.UUID,
    payload: ProposalUpdate,
    current_user: CurrentUser,
    proposal_service: Annotated[ProposalService, Depends(get_proposal_service)],
) -> ProposalResponse:
    proposal = await proposal_service.update(proposal_id, payload, user_id=current_user.id)
    return ProposalResponse.model_validate(proposal)


@router.delete("/{proposal_id}", response_model=MessageResponse, summary="Delete a proposal")
async def delete_proposal(
    proposal_id: uuid.UUID,
    current_user: CurrentUser,
    proposal_service: Annotated[ProposalService, Depends(get_proposal_service)],
) -> MessageResponse:
    await proposal_service.delete(proposal_id, user_id=current_user.id)
    return MessageResponse(message="Proposal deleted successfully.")


# --- AI Proposal Generation ---


@router.post(
    "/{proposal_id}/generate-proposal",
    response_model=ProposalGenerationResponse,
    summary="Generate a proposal for an opportunity using AI",
)
async def generate_proposal(
    proposal_id: uuid.UUID,
    current_user: CurrentUser,
    gen_service: Annotated[ProposalGenerationService, Depends(get_proposal_generation_service)],
    user_pref_repo: Annotated[UserPreferenceRepository, Depends(get_user_preference_repository)],
    ai_pref_repo: Annotated[AIPreferenceRepository, Depends(get_ai_preference_repository)],
) -> ProposalGenerationResponse:
    user_prefs = await user_pref_repo.get_by_user_id(current_user.id)
    ai_prefs = await ai_pref_repo.get_by_user_id(current_user.id)
    proposal, version, _ = await gen_service.generate_proposal(
        user=current_user,
        opportunity_id=proposal_id,
        user_preferences=user_prefs,
        ai_preferences=ai_prefs,
    )
    return ProposalGenerationResponse(
        proposal_id=proposal.id,
        version_id=version.id,
        version_number=version.version_number,
        cover_letter=proposal.cover_letter,
        bid_amount=proposal.bid_amount,
        bid_type=proposal.bid_type,
        estimated_duration=proposal.estimated_duration,
        status=proposal.status,
    )


@router.post(
    "/{proposal_id}/regenerate",
    response_model=ProposalGenerationResponse,
    summary="Regenerate an existing proposal, creating a new version",
)
async def regenerate_proposal(
    proposal_id: uuid.UUID,
    current_user: CurrentUser,
    gen_service: Annotated[ProposalGenerationService, Depends(get_proposal_generation_service)],
    user_pref_repo: Annotated[UserPreferenceRepository, Depends(get_user_preference_repository)],
    ai_pref_repo: Annotated[AIPreferenceRepository, Depends(get_ai_preference_repository)],
) -> ProposalGenerationResponse:
    user_prefs = await user_pref_repo.get_by_user_id(current_user.id)
    ai_prefs = await ai_pref_repo.get_by_user_id(current_user.id)
    proposal, version, _ = await gen_service.regenerate(
        user=current_user,
        proposal_id=proposal_id,
        user_preferences=user_prefs,
        ai_preferences=ai_prefs,
    )
    return ProposalGenerationResponse(
        proposal_id=proposal.id,
        version_id=version.id,
        version_number=version.version_number,
        cover_letter=version.cover_letter,
        bid_amount=None,
        bid_type=version.bid_type,
        estimated_duration=version.estimated_duration,
        status=proposal.status,
    )


@router.post(
    "/{proposal_id}/duplicate",
    response_model=DuplicateProposalResponse,
    summary="Duplicate an existing proposal",
)
async def duplicate_proposal(
    proposal_id: uuid.UUID,
    current_user: CurrentUser,
    proposal_service: Annotated[ProposalService, Depends(get_proposal_service)],
) -> DuplicateProposalResponse:
    existing = await proposal_service.get_by_id(proposal_id, user_id=current_user.id)
    new_proposal = await proposal_service.create(
        user_id=current_user.id,
        payload=ProposalCreate(
            project_id=existing.project_id,
            cover_letter=existing.cover_letter,
            bid_amount=existing.bid_amount,
        ),
    )
    return DuplicateProposalResponse(
        id=new_proposal.id,
        project_id=new_proposal.project_id,
        status=new_proposal.status,
        cover_letter=new_proposal.cover_letter,
    )


# --- Version History ---


@router.get(
    "/{proposal_id}/versions",
    response_model=ProposalVersionListResponse,
    summary="List all versions of a proposal",
)
async def list_proposal_versions(
    proposal_id: uuid.UUID,
    current_user: CurrentUser,
    proposal_service: Annotated[ProposalService, Depends(get_proposal_service)],
    version_repo: Annotated[ProposalVersionRepository, Depends(get_proposal_version_repository)],
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
) -> ProposalVersionListResponse:
    await proposal_service.get_by_id(proposal_id, user_id=current_user.id)
    versions, total = await version_repo.get_by_proposal_id(
        proposal_id=proposal_id, skip=skip, limit=limit
    )
    return ProposalVersionListResponse(
        items=[ProposalVersionDetailResponse.model_validate(v) for v in versions],
        total=total,
        skip=skip,
        limit=limit,
    )


@router.get(
    "/{proposal_id}/versions/{version_id}",
    response_model=ProposalVersionDetailResponse,
    summary="Get a specific proposal version",
)
async def get_proposal_version(
    proposal_id: uuid.UUID,
    version_id: uuid.UUID,
    current_user: CurrentUser,
    proposal_service: Annotated[ProposalService, Depends(get_proposal_service)],
    version_repo: Annotated[ProposalVersionRepository, Depends(get_proposal_version_repository)],
) -> ProposalVersionDetailResponse:
    await proposal_service.get_by_id(proposal_id, user_id=current_user.id)
    version = await version_repo.get_by_id_and_proposal_id(version_id, proposal_id)
    if version is None:
        raise HTTPException(status_code=404, detail="Version not found.")
    return ProposalVersionDetailResponse.model_validate(version)


# --- Review Workflow ---


@router.post(
    "/{proposal_id}/review",
    response_model=StatusTransitionResponse,
    summary="Move proposal to Under Review status",
    description="Transitions a proposal from 'draft' to 'under_review'. The proposal must belong to the current user. Returns 400 if the transition is invalid.",
)
async def review_proposal(
    proposal_id: uuid.UUID,
    current_user: CurrentUser,
    review_service: Annotated[ProposalReviewService, Depends(get_proposal_review_service)],
) -> StatusTransitionResponse:
    proposal = await review_service.review(proposal_id, current_user.id)
    return StatusTransitionResponse(
        id=proposal.id, status=proposal.status, message="Proposal moved to Under Review."
    )


@router.post(
    "/{proposal_id}/ready",
    response_model=StatusTransitionResponse,
    summary="Validate and mark proposal as Ready to Submit",
    description="Validates that cover_letter, bid_amount, and estimated_duration are set and the opportunity is open, then transitions from 'under_review' to 'ready_to_submit'. Returns 422 if validation fails, 400 if transition is invalid.",
)
async def ready_proposal(
    proposal_id: uuid.UUID,
    current_user: CurrentUser,
    review_service: Annotated[ProposalReviewService, Depends(get_proposal_review_service)],
) -> StatusTransitionResponse:
    proposal = await review_service.mark_ready(proposal_id, current_user.id)
    return StatusTransitionResponse(
        id=proposal.id,
        status=proposal.status,
        message="Proposal marked as Ready to Submit.",
    )


@router.post(
    "/{proposal_id}/submitted",
    response_model=StatusTransitionResponse,
    summary="Mark proposal as Submitted (user records manual submission)",
)
async def submitted_proposal(
    proposal_id: uuid.UUID,
    current_user: CurrentUser,
    review_service: Annotated[ProposalReviewService, Depends(get_proposal_review_service)],
) -> StatusTransitionResponse:
    proposal = await review_service.mark_submitted(proposal_id, current_user.id)
    return StatusTransitionResponse(
        id=proposal.id, status=proposal.status, message="Proposal marked as Submitted."
    )


@router.post(
    "/{proposal_id}/archive",
    response_model=StatusTransitionResponse,
    summary="Archive a proposal",
)
async def archive_proposal(
    proposal_id: uuid.UUID,
    current_user: CurrentUser,
    review_service: Annotated[ProposalReviewService, Depends(get_proposal_review_service)],
) -> StatusTransitionResponse:
    proposal = await review_service.archive(proposal_id, current_user.id)
    return StatusTransitionResponse(
        id=proposal.id, status=proposal.status, message="Proposal archived."
    )


@router.get(
    "/{proposal_id}/readiness",
    response_model=ReadinessResponse,
    summary="Check if a proposal is ready to submit",
)
async def readiness_check(
    proposal_id: uuid.UUID,
    current_user: CurrentUser,
    review_service: Annotated[ProposalReviewService, Depends(get_proposal_review_service)],
) -> ReadinessResponse:
    proposal = await review_service._assert_ownership(proposal_id, current_user.id)
    errors = await review_service.validate_readiness(proposal)
    checks = [
        {
            "field": "cover_letter",
            "status": "pass" if proposal.cover_letter and proposal.cover_letter.strip() else "fail",
            "message": "Cover letter is required." if not proposal.cover_letter or not proposal.cover_letter.strip() else "Cover letter is set.",
        },
        {
            "field": "bid_amount",
            "status": "pass" if proposal.bid_amount is not None else "fail",
            "message": "Bid amount is required." if proposal.bid_amount is None else "Bid amount is set.",
        },
        {
            "field": "estimated_duration",
            "status": "pass" if proposal.estimated_duration else "fail",
            "message": "Delivery estimate is required." if not proposal.estimated_duration else "Delivery estimate is set.",
        },
    ]
    return ReadinessResponse(ready=len(errors) == 0, checks=checks)


# --- Editing ---


@router.post(
    "/{proposal_id}/edit",
    response_model=ProposalEditResponse,
    summary="Edit a proposal (creates a new version)",
    description="Creates a new ProposalVersion snapshot with the provided fields and updates the proposal record. If the current status is 'draft' or 'under_review', transitions to 'edited'. Returns the new version id and number.",
)
async def edit_proposal(
    proposal_id: uuid.UUID,
    payload: ProposalEditRequest,
    current_user: CurrentUser,
    review_service: Annotated[ProposalReviewService, Depends(get_proposal_review_service)],
) -> ProposalEditResponse:
    proposal, version = await review_service.edit_proposal(
        proposal_id=proposal_id,
        user_id=current_user.id,
        title=payload.title,
        cover_letter=payload.cover_letter,
        executive_summary=payload.executive_summary,
        why_good_fit=payload.why_good_fit,
        relevant_experience=payload.relevant_experience,
        bid_amount=float(payload.bid_amount) if payload.bid_amount is not None else None,
        bid_type=payload.bid_type,
        estimated_duration=payload.estimated_duration,
        milestones=payload.milestones,
        risk_notes=payload.risk_notes,
        confidence_explanation=payload.confidence_explanation,
        proposal_summary=payload.proposal_summary,
        change_summary=payload.change_summary,
    )
    return ProposalEditResponse(
        proposal_id=proposal.id,
        version_id=version.id,
        version_number=version.version_number,
        status=proposal.status,
    )


# --- Rollback ---


@router.post(
    "/{proposal_id}/rollback",
    response_model=RollbackResponse,
    summary="Rollback to a previous version",
    description="Restores proposal content from a specified version, creating a new version with the restored data. The version_id must belong to the same proposal. Returns 404 if the version is not found.",
)
async def rollback_proposal(
    proposal_id: uuid.UUID,
    payload: RollbackRequest,
    current_user: CurrentUser,
    review_service: Annotated[ProposalReviewService, Depends(get_proposal_review_service)],
) -> RollbackResponse:
    proposal, version = await review_service.rollback(
        proposal_id=proposal_id,
        user_id=current_user.id,
        version_id=payload.version_id,
        change_summary=payload.change_summary,
    )
    return RollbackResponse(
        proposal_id=proposal.id,
        version_id=version.id,
        version_number=version.version_number,
        status=proposal.status,
        message=f"Rolled back to version {payload.version_id}.",
    )


# --- Comparison ---


@router.get(
    "/{proposal_id}/compare",
    response_model=ComparisonResponse,
    summary="Compare two proposal versions",
    description="Returns a section-by-section diff between two versions of a proposal, including change statistics (words added/removed, sections modified). Both version IDs are required query parameters.",
)
async def compare_versions(
    proposal_id: uuid.UUID,
    current_user: CurrentUser,
    review_service: Annotated[ProposalReviewService, Depends(get_proposal_review_service)],
    v1: uuid.UUID = Query(..., description="First version ID"),
    v2: uuid.UUID = Query(..., description="Second version ID"),
) -> ComparisonResponse:
    result = await review_service.compare_versions(
        proposal_id=proposal_id,
        user_id=current_user.id,
        version_id_a=v1,
        version_id_b=v2,
    )
    return ComparisonResponse(**result)


# --- Notes ---


@router.get(
    "/{proposal_id}/notes",
    response_model=NoteListResponse,
    summary="List notes for a proposal",
)
async def list_notes(
    proposal_id: uuid.UUID,
    current_user: CurrentUser,
    note_service: Annotated[ProposalNoteService, Depends(get_proposal_note_service)],
    proposal_service: Annotated[ProposalService, Depends(get_proposal_service)],
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
) -> NoteListResponse:
    await proposal_service.get_by_id(proposal_id, user_id=current_user.id)
    items, total = await note_service.get_by_proposal_id(
        proposal_id=proposal_id, skip=skip, limit=limit
    )
    return NoteListResponse(
        items=[NoteResponse.model_validate(n) for n in items],
        total=total,
    )


@router.post(
    "/{proposal_id}/notes",
    response_model=NoteResponse,
    status_code=201,
    summary="Create a private note on a proposal",
)
async def create_note(
    proposal_id: uuid.UUID,
    payload: NoteCreateRequest,
    current_user: CurrentUser,
    note_service: Annotated[ProposalNoteService, Depends(get_proposal_note_service)],
    proposal_service: Annotated[ProposalService, Depends(get_proposal_service)],
) -> NoteResponse:
    await proposal_service.get_by_id(proposal_id, user_id=current_user.id)
    note = await note_service.create(
        proposal_id=proposal_id,
        user_id=current_user.id,
        content=payload.content,
    )
    return NoteResponse.model_validate(note)


@router.put(
    "/notes/{note_id}",
    response_model=NoteResponse,
    summary="Update a private note",
)
async def update_note(
    note_id: uuid.UUID,
    payload: NoteUpdateRequest,
    current_user: CurrentUser,
    note_service: Annotated[ProposalNoteService, Depends(get_proposal_note_service)],
) -> NoteResponse:
    note = await note_service.update(
        note_id=note_id,
        user_id=current_user.id,
        content=payload.content,
    )
    return NoteResponse.model_validate(note)


@router.delete(
    "/notes/{note_id}",
    response_model=MessageResponse,
    summary="Delete a private note",
)
async def delete_note(
    note_id: uuid.UUID,
    current_user: CurrentUser,
    note_service: Annotated[ProposalNoteService, Depends(get_proposal_note_service)],
) -> MessageResponse:
    await note_service.delete(note_id=note_id, user_id=current_user.id)
    return MessageResponse(message="Note deleted successfully.")


# --- Audit Log ---


@router.get(
    "/{proposal_id}/audit-log",
    response_model=AuditLogListResponse,
    summary="Get audit trail for a proposal",
    description="Returns a chronological list of all actions performed on a proposal (status changes, edits, rollbacks, notes), ordered most recent first. Supports pagination.",
)
async def get_audit_log(
    proposal_id: uuid.UUID,
    current_user: CurrentUser,
    audit_service: Annotated[AuditService, Depends(get_audit_service)],
    proposal_service: Annotated[ProposalService, Depends(get_proposal_service)],
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
) -> AuditLogListResponse:
    await proposal_service.get_by_id(proposal_id, user_id=current_user.id)
    items, total = await audit_service.get_proposal_log(
        proposal_id=proposal_id, skip=skip, limit=limit
    )
    return AuditLogListResponse(
        items=[AuditLogEntry.model_validate(e) for e in items],
        total=total,
    )


# --- AI Improvement ---


@router.post(
    "/{proposal_id}/improve",
    response_model=ImproveResponse,
    summary="Improve a proposal using AI with a specific style",
    description="Regenerates the proposal with a chosen improvement style (shorter, longer, more technical, etc.), creating a new version.",
)
async def improve_proposal(
    proposal_id: uuid.UUID,
    payload: ImproveRequest,
    current_user: CurrentUser,
    improver: Annotated[ProposalImprover, Depends(get_proposal_improver)],
) -> ImproveResponse:
    proposal, version, _ = await improver.improve(
        user=current_user,
        proposal_id=proposal_id,
        style=payload.style,
        custom_instruction=payload.custom_instruction,
        focus_section=payload.focus_section,
    )
    return ImproveResponse(
        proposal_id=proposal.id,
        version_id=version.id,
        version_number=version.version_number,
        style=payload.style,
        cover_letter=version.cover_letter,
        status=proposal.status,
    )


# --- AI Evaluation ---


@router.post(
    "/{proposal_id}/evaluate",
    response_model=EvaluationResponse,
    summary="Evaluate proposal quality using AI",
    description="Scores the proposal on completeness, persuasiveness, relevance, clarity, and formatting with specific feedback.",
)
async def evaluate_proposal(
    proposal_id: uuid.UUID,
    current_user: CurrentUser,
    evaluator: Annotated[ProposalEvaluator, Depends(get_proposal_evaluator)],
    proposal_service: Annotated[ProposalService, Depends(get_proposal_service)],
    version_repo: Annotated[ProposalVersionRepository, Depends(get_proposal_version_repository)],
) -> EvaluationResponse:
    proposal = await proposal_service.get_by_id(proposal_id, user_id=current_user.id)
    versions, _ = await version_repo.get_by_proposal_id(proposal_id, limit=1)
    version = versions[0] if versions else None
    result = await evaluator.evaluate(
        user=current_user,
        proposal=proposal,
        version=version,
    )
    return EvaluationResponse(
        proposal_id=proposal.id,
        version_id=version.id if version else None,
        scores=EvaluationScoreResponse(
            overall_score=result.overall_score,
            completeness_score=result.completeness_score,
            persuasiveness_score=result.persuasiveness_score,
            relevance_score=result.relevance_score,
            clarity_score=result.clarity_score,
            formatting_score=result.formatting_score,
            strengths=result.strengths,
            weaknesses=result.weaknesses,
            suggestions=result.suggestions,
        ),
    )


# --- Human Approval Flow ---


@router.post(
    "/{proposal_id}/request-approval",
    response_model=StatusTransitionResponse,
    summary="Request human approval for an AI-generated proposal",
    description="Transitions from 'ai_generated' to 'awaiting_approval'.",
)
async def request_approval(
    proposal_id: uuid.UUID,
    current_user: CurrentUser,
    review_service: Annotated[ProposalReviewService, Depends(get_proposal_review_service)],
) -> StatusTransitionResponse:
    proposal = await review_service.request_approval(proposal_id, current_user.id)
    return StatusTransitionResponse(
        id=proposal.id,
        status=proposal.status,
        message="Proposal sent for human approval.",
    )


@router.post(
    "/{proposal_id}/approve",
    response_model=ApprovalResponse,
    summary="Approve an AI-generated proposal",
    description="Transitions from 'awaiting_approval' to 'approved', recording the approving user.",
)
async def approve_proposal(
    proposal_id: uuid.UUID,
    current_user: CurrentUser,
    review_service: Annotated[ProposalReviewService, Depends(get_proposal_review_service)],
) -> ApprovalResponse:
    proposal = await review_service.approve(proposal_id, current_user.id)
    return ApprovalResponse(
        id=proposal.id,
        status=proposal.status,
        message="Proposal approved.",
    )


@router.post(
    "/{proposal_id}/reject",
    response_model=ApprovalResponse,
    summary="Reject an AI-generated proposal",
    description="Transitions from 'awaiting_approval' to 'rejected' with an optional reason.",
)
async def reject_proposal(
    proposal_id: uuid.UUID,
    payload: RejectRequest,
    current_user: CurrentUser,
    review_service: Annotated[ProposalReviewService, Depends(get_proposal_review_service)],
) -> ApprovalResponse:
    proposal = await review_service.reject(proposal_id, current_user.id, reason=payload.reason)
    return ApprovalResponse(
        id=proposal.id,
        status=proposal.status,
        message="Proposal rejected." + (f" Reason: {payload.reason}" if payload.reason else ""),
    )


@router.post(
    "/{proposal_id}/queue",
    response_model=StatusTransitionResponse,
    summary="Queue an approved proposal for submission",
    description="Transitions from 'approved' to 'queued'.",
)
async def queue_proposal(
    proposal_id: uuid.UUID,
    current_user: CurrentUser,
    review_service: Annotated[ProposalReviewService, Depends(get_proposal_review_service)],
) -> StatusTransitionResponse:
    proposal = await review_service.queue(proposal_id, current_user.id)
    return StatusTransitionResponse(
        id=proposal.id,
        status=proposal.status,
        message="Proposal queued for submission.",
    )
