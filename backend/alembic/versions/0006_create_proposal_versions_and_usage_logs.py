"""create proposal_versions and ai_usage_logs tables

Revision ID: 0006
Revises: 0005
Create Date: 2026-07-07 00:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0006"
down_revision: Union[str, None] = "0005"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # --- proposal_versions ---
    op.create_table(
        "proposal_versions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("proposal_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("version_number", sa.Integer, nullable=False),
        sa.Column("cover_letter", sa.Text, nullable=True),
        sa.Column("executive_summary", sa.Text, nullable=True),
        sa.Column("why_good_fit", sa.Text, nullable=True),
        sa.Column("relevant_experience", sa.Text, nullable=True),
        sa.Column("bid_amount", sa.Float, nullable=True),
        sa.Column("bid_type", sa.String(length=50), nullable=True),
        sa.Column("estimated_duration", sa.String(length=255), nullable=True),
        sa.Column("milestones", sa.Text, nullable=True),
        sa.Column("risk_notes", sa.Text, nullable=True),
        sa.Column("confidence_explanation", sa.Text, nullable=True),
        sa.Column("proposal_summary", sa.Text, nullable=True),
        sa.Column("raw_ai_response", sa.Text, nullable=True),
        sa.Column("prompt_version", sa.String(length=50), nullable=True),
        sa.Column("model", sa.String(length=255), nullable=True),
        sa.Column("temperature", sa.Float, nullable=True),
        sa.Column("tokens_used", sa.Integer, nullable=True),
        sa.Column("user_edits", sa.Text, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["proposal_id"], ["proposals.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_proposal_versions_proposal_id", "proposal_versions", ["proposal_id"])

    # --- ai_usage_logs ---
    op.create_table(
        "ai_usage_logs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("provider", sa.String(length=255), nullable=False),
        sa.Column("model", sa.String(length=255), nullable=False),
        sa.Column("prompt_tokens", sa.Integer, nullable=False, server_default="0"),
        sa.Column("completion_tokens", sa.Integer, nullable=False, server_default="0"),
        sa.Column("total_tokens", sa.Integer, nullable=False, server_default="0"),
        sa.Column("estimated_cost_usd", sa.Float, nullable=True),
        sa.Column("latency_ms", sa.Integer, nullable=True),
        sa.Column("endpoint", sa.String(length=255), nullable=True),
        sa.Column("error_message", sa.Text, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_ai_usage_logs_user_id", "ai_usage_logs", ["user_id"])


def downgrade() -> None:
    op.drop_index("ix_ai_usage_logs_user_id", table_name="ai_usage_logs")
    op.drop_table("ai_usage_logs")
    op.drop_index("ix_proposal_versions_proposal_id", table_name="proposal_versions")
    op.drop_table("proposal_versions")
