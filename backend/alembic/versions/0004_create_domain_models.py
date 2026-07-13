"""create domain models — technologies, categories, clients, projects, proposals, templates

Revision ID: 0004
Revises: 0003
Create Date: 2026-07-06 00:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0004"
down_revision: Union[str, None] = "0003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # --- technologies ---
    op.create_table(
        "technologies",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("slug", sa.String(length=120), nullable=False),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("category", sa.String(length=64), nullable=True),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_technologies_name", "technologies", ["name"], unique=True)
    op.create_index("ix_technologies_slug", "technologies", ["slug"], unique=True)

    # --- project_categories ---
    op.create_table(
        "project_categories",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("slug", sa.String(length=120), nullable=False),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("icon", sa.String(length=64), nullable=True),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_project_categories_name", "project_categories", ["name"], unique=True)
    op.create_index("ix_project_categories_slug", "project_categories", ["slug"], unique=True)

    # --- clients ---
    op.create_table(
        "clients",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("external_id", sa.String(length=255), nullable=True),
        sa.Column("platform", sa.String(length=64), nullable=True),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("company", sa.String(length=255), nullable=True),
        sa.Column("email", sa.String(length=255), nullable=True),
        sa.Column("website", sa.String(length=1024), nullable=True),
        sa.Column("country", sa.String(length=4), nullable=True),
        sa.Column("rating", sa.Float, nullable=True),
        sa.Column("total_spent", sa.Numeric(12, 2), nullable=True),
        sa.Column("total_hired", sa.Integer, nullable=True),
        sa.Column("is_payment_verified", sa.Boolean, nullable=False, server_default=sa.false()),
        sa.Column("notes", sa.Text, nullable=True),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_clients_user_id", "clients", ["user_id"])
    op.create_index(
        "ix_clients_user_platform_external", "clients", ["user_id", "platform", "external_id"], unique=True
    )

    # --- proposal_templates ---
    op.create_table(
        "proposal_templates",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("cover_letter_template", sa.Text, nullable=False),
        sa.Column("is_default", sa.Boolean, nullable=False, server_default=sa.false()),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default=sa.true()),
        sa.Column("category", sa.String(length=64), nullable=True),
        sa.Column("tags", postgresql.JSON, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_proposal_templates_user_id", "proposal_templates", ["user_id"])

    # --- projects ---
    op.create_table(
        "projects",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("client_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("external_id", sa.String(length=255), nullable=True),
        sa.Column("platform", sa.String(length=64), nullable=True),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="open"),
        sa.Column("project_type", sa.String(length=32), nullable=True),
        sa.Column("experience_level", sa.String(length=32), nullable=True),
        sa.Column("duration", sa.String(length=32), nullable=True),
        sa.Column("budget_min", sa.Numeric(12, 2), nullable=True),
        sa.Column("budget_max", sa.Numeric(12, 2), nullable=True),
        sa.Column("budget_type", sa.String(length=16), nullable=True),
        sa.Column("currency", sa.String(length=3), nullable=False, server_default="USD"),
        sa.Column("estimated_duration", sa.String(length=64), nullable=True),
        sa.Column("scope", sa.String(length=32), nullable=True),
        sa.Column("client_rating", sa.Float, nullable=True),
        sa.Column("client_reviews_count", sa.Integer, nullable=True),
        sa.Column("client_country", sa.String(length=4), nullable=True),
        sa.Column("client_payment_verified", sa.Boolean, nullable=True),
        sa.Column("client_total_spent", sa.Numeric(12, 2), nullable=True),
        sa.Column("client_total_hired", sa.Integer, nullable=True),
        sa.Column("url", sa.String(length=1024), nullable=True),
        sa.Column("is_negotiable", sa.Boolean, nullable=False, server_default=sa.false()),
        sa.Column("is_remote", sa.Boolean, nullable=False, server_default=sa.true()),
        sa.Column("is_archived", sa.Boolean, nullable=False, server_default=sa.false()),
        sa.Column("required_skills", postgresql.JSON, nullable=True),
        sa.Column("proposals_count", sa.Integer, nullable=False, server_default="0"),
        sa.Column("is_ai_recommended", sa.Boolean, nullable=False, server_default=sa.false()),
        sa.Column("ai_confidence_score", sa.Float, nullable=True),
        sa.Column("ai_match_reason", sa.Text, nullable=True),
        sa.Column("ai_recommendation_note", sa.Text, nullable=True),
        sa.Column("posted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("deadline", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["client_id"], ["clients.id"], ondelete="SET NULL"),
    )
    op.create_index("ix_projects_user_id", "projects", ["user_id"])
    op.create_index("ix_projects_client_id", "projects", ["client_id"])
    op.create_index("ix_projects_user_status", "projects", ["user_id", "status"])
    op.create_index("ix_projects_platform_external", "projects", ["platform", "external_id"])

    # --- junction: project_technologies ---
    op.create_table(
        "project_technologies",
        sa.Column("project_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("technology_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["technology_id"], ["technologies.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("project_id", "technology_id"),
    )

    # --- junction: project_category_links ---
    op.create_table(
        "project_category_links",
        sa.Column("project_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("category_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["category_id"], ["project_categories.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("project_id", "category_id"),
    )

    # --- proposals ---
    op.create_table(
        "proposals",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("project_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="draft"),
        sa.Column("cover_letter", sa.Text, nullable=True),
        sa.Column("bid_amount", sa.Numeric(12, 2), nullable=True),
        sa.Column("bid_type", sa.String(length=16), nullable=True),
        sa.Column("currency", sa.String(length=3), nullable=False, server_default="USD"),
        sa.Column("estimated_duration", sa.String(length=64), nullable=True),
        sa.Column("ai_generated", sa.Boolean, nullable=False, server_default=sa.false()),
        sa.Column("ai_generation_version", sa.String(length=64), nullable=True),
        sa.Column("ai_confidence_score", sa.Float, nullable=True),
        sa.Column("template_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("is_auto_submitted", sa.Boolean, nullable=False, server_default=sa.false()),
        sa.Column("requires_human_approval", sa.Boolean, nullable=False, server_default=sa.true()),
        sa.Column("human_approved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("submitted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("response_from_client", sa.Text, nullable=True),
        sa.Column("client_viewed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("client_interview_request", sa.Boolean, nullable=False, server_default=sa.false()),
        sa.Column("rejection_reason", sa.String(length=255), nullable=True),
        sa.Column("ai_evaluation_score", sa.Float, nullable=True),
        sa.Column("ai_evaluation_data", sa.Text, nullable=True),
        sa.Column("human_approved_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["template_id"], ["proposal_templates.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["human_approved_by"], ["users.id"], ondelete="SET NULL"),
    )
    op.create_index("ix_proposals_project_id", "proposals", ["project_id"])
    op.create_index("ix_proposals_user_id", "proposals", ["user_id"])
    op.create_index("ix_proposals_user_status", "proposals", ["user_id", "status"])


def downgrade() -> None:
    op.drop_index("ix_proposals_user_status", table_name="proposals")
    op.drop_index("ix_proposals_user_id", table_name="proposals")
    op.drop_index("ix_proposals_project_id", table_name="proposals")
    op.drop_table("proposals")
    op.drop_table("project_category_links")
    op.drop_table("project_technologies")
    op.drop_index("ix_projects_platform_external", table_name="projects")
    op.drop_index("ix_projects_user_status", table_name="projects")
    op.drop_index("ix_projects_client_id", table_name="projects")
    op.drop_index("ix_projects_user_id", table_name="projects")
    op.drop_table("projects")
    op.drop_index("ix_proposal_templates_user_id", table_name="proposal_templates")
    op.drop_table("proposal_templates")
    op.drop_index("ix_clients_user_platform_external", table_name="clients")
    op.drop_index("ix_clients_user_id", table_name="clients")
    op.drop_table("clients")
    op.drop_index("ix_project_categories_slug", table_name="project_categories")
    op.drop_index("ix_project_categories_name", table_name="project_categories")
    op.drop_table("project_categories")
    op.drop_index("ix_technologies_slug", table_name="technologies")
    op.drop_index("ix_technologies_name", table_name="technologies")
    op.drop_table("technologies")
