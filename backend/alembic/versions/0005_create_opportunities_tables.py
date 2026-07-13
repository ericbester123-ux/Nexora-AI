"""create opportunities and import_history tables

Revision ID: 0005
Revises: 0004
Create Date: 2026-07-07 00:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0005"
down_revision: Union[str, None] = "0004"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # --- import_history ---
    op.create_table(
        "import_history",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("platform", sa.String(length=64), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("duration_ms", sa.Float, nullable=True),
        sa.Column("opportunities_found", sa.Integer, nullable=False, server_default="0"),
        sa.Column("imported", sa.Integer, nullable=False, server_default="0"),
        sa.Column("updated", sa.Integer, nullable=False, server_default="0"),
        sa.Column("skipped", sa.Integer, nullable=False, server_default="0"),
        sa.Column("failed", sa.Integer, nullable=False, server_default="0"),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="in_progress"),
        sa.Column("error_messages", sa.Text, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_import_history_user_id", "import_history", ["user_id"])
    op.create_index("ix_import_history_platform", "import_history", ["platform"])
    op.create_index("ix_import_history_status", "import_history", ["status"])

    # --- opportunities ---
    op.create_table(
        "opportunities",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("import_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("external_id", sa.String(length=255), nullable=True),
        sa.Column("platform", sa.String(length=64), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("url", sa.String(length=1024), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="new"),
        sa.Column("project_type", sa.String(length=64), nullable=True),
        sa.Column("experience_level", sa.String(length=32), nullable=True),
        sa.Column("duration", sa.String(length=64), nullable=True),
        sa.Column("budget_min", sa.Float, nullable=True),
        sa.Column("budget_max", sa.Float, nullable=True),
        sa.Column("budget_type", sa.String(length=16), nullable=True),
        sa.Column("currency", sa.String(length=3), nullable=False, server_default="USD"),
        sa.Column("skills", postgresql.JSON, nullable=True),
        sa.Column("category", sa.String(length=128), nullable=True),
        sa.Column("subcategory", sa.String(length=128), nullable=True),
        sa.Column("country", sa.String(length=4), nullable=True),
        sa.Column("client_rating", sa.Float, nullable=True),
        sa.Column("client_reviews_count", sa.Integer, nullable=True),
        sa.Column("client_payment_verified", sa.Boolean, nullable=True),
        sa.Column("client_total_hired", sa.Integer, nullable=True),
        sa.Column("is_remote", sa.Boolean, nullable=False, server_default=sa.true()),
        sa.Column("is_negotiable", sa.Boolean, nullable=False, server_default=sa.false()),
        sa.Column("is_ai_scored", sa.Boolean, nullable=False, server_default=sa.false()),
        sa.Column("ai_score", sa.Float, nullable=True),
        sa.Column("ai_match_reason", sa.Text, nullable=True),
        sa.Column("content_hash", sa.String(length=64), nullable=True),
        sa.Column("posted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("deadline", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["import_id"], ["import_history.id"], ondelete="SET NULL"),
    )
    op.create_index("ix_opportunities_user_id", "opportunities", ["user_id"])
    op.create_index(
        "ix_opportunities_user_platform_external",
        "opportunities",
        ["user_id", "platform", "external_id"],
        unique=True,
    )
    op.create_index("ix_opportunities_platform", "opportunities", ["platform"])
    op.create_index("ix_opportunities_status", "opportunities", ["status"])
    op.create_index("ix_opportunities_import_id", "opportunities", ["import_id"])
    op.create_index("ix_opportunities_content_hash", "opportunities", ["content_hash"])


def downgrade() -> None:
    op.drop_index("ix_opportunities_content_hash", table_name="opportunities")
    op.drop_index("ix_opportunities_import_id", table_name="opportunities")
    op.drop_index("ix_opportunities_status", table_name="opportunities")
    op.drop_index("ix_opportunities_platform", table_name="opportunities")
    op.drop_index("ix_opportunities_user_platform_external", table_name="opportunities")
    op.drop_index("ix_opportunities_user_id", table_name="opportunities")
    op.drop_table("opportunities")
    op.drop_index("ix_import_history_status", table_name="import_history")
    op.drop_index("ix_import_history_platform", table_name="import_history")
    op.drop_index("ix_import_history_user_id", table_name="import_history")
    op.drop_table("import_history")
