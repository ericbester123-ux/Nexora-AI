"""create proposal review tables and extend proposal_versions

Revision ID: 0007
Revises: 0006
Create Date: 2026-07-07 00:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0007"
down_revision: Union[str, None] = "0006"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # --- Extend proposals ---
    op.add_column("proposals", sa.Column("title", sa.String(length=255), nullable=True))

    # --- Extend proposal_versions ---
    op.add_column(
        "proposal_versions",
        sa.Column("created_by", sa.String(length=16), nullable=False, server_default="ai"),
    )
    op.add_column(
        "proposal_versions",
        sa.Column("change_summary", sa.Text, nullable=True),
    )

    # --- proposal_notes ---
    op.create_table(
        "proposal_notes",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("proposal_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("content", sa.Text, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["proposal_id"], ["proposals.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_proposal_notes_proposal_id", "proposal_notes", ["proposal_id"])

    # --- audit_logs ---
    op.create_table(
        "audit_logs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("proposal_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("action", sa.String(length=64), nullable=False),
        sa.Column("details", sa.Text, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["proposal_id"], ["proposals.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_audit_logs_proposal_id", "audit_logs", ["proposal_id"])

    # --- proposal_status_history ---
    op.create_table(
        "proposal_status_history",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("proposal_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("from_status", sa.String(length=32), nullable=True),
        sa.Column("to_status", sa.String(length=32), nullable=False),
        sa.Column("changed_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["proposal_id"], ["proposals.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["changed_by"], ["users.id"], ondelete="SET NULL"),
    )
    op.create_index(
        "ix_proposal_status_history_proposal_id",
        "proposal_status_history",
        ["proposal_id"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_proposal_status_history_proposal_id", table_name="proposal_status_history"
    )
    op.drop_table("proposal_status_history")
    op.drop_index("ix_audit_logs_proposal_id", table_name="audit_logs")
    op.drop_table("audit_logs")
    op.drop_index("ix_proposal_notes_proposal_id", table_name="proposal_notes")
    op.drop_table("proposal_notes")
    op.drop_column("proposal_versions", "change_summary")
    op.drop_column("proposal_versions", "created_by")
    op.drop_column("proposals", "title")
