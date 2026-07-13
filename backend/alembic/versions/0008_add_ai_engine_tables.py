"""add ai engine tables and proposal evaluation columns

Revision ID: 0008
Revises: 0007
Create Date: 2026-07-09 00:00:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0008"
down_revision: Union[str, None] = "0007"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # --- Extend proposals with evaluation columns (only add FK if columns exist) ---
    # Use batch mode for foreign key on SQLite
    with op.batch_alter_table("proposals") as batch_op:
        batch_op.create_foreign_key(
            "fk_proposals_human_approved_by",
            "users",
            ["human_approved_by"],
            ["id"],
            ondelete="SET NULL",
        )

    # --- ai_generation_jobs ---
    op.create_table(
        "ai_generation_jobs",
        sa.Column("id", sa.String(36), primary_key=True, nullable=False),
        sa.Column("user_id", sa.String(36), nullable=False),
        sa.Column("opportunity_id", sa.String(36), nullable=True),
        sa.Column("proposal_id", sa.String(36), nullable=True),
        sa.Column("job_type", sa.String(length=32), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="pending"),
        sa.Column("progress", sa.Float, nullable=True, server_default="0"),
        sa.Column("result_data", sa.Text, nullable=True),
        sa.Column("error_message", sa.Text, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["opportunity_id"], ["opportunities.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["proposal_id"], ["proposals.id"], ondelete="SET NULL"),
    )
    op.create_index(
        "ix_ai_generation_jobs_user_status",
        "ai_generation_jobs",
        ["user_id", "status"],
    )


def downgrade() -> None:
    op.drop_constraint("fk_proposals_human_approved_by", "proposals", type_="foreignkey")
    op.drop_index("ix_ai_generation_jobs_user_status", "ai_generation_jobs")
    op.drop_table("ai_generation_jobs")
