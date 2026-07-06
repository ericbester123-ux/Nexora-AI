"""extend users with profile fields, create preferences tables

Revision ID: 0003
Revises: 0002
Create Date: 2026-07-06 00:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0003"
down_revision: Union[str, None] = "0002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # --- Extend users table with profile columns ---
    op.add_column("users", sa.Column("first_name", sa.String(length=128), nullable=True))
    op.add_column("users", sa.Column("last_name", sa.String(length=128), nullable=True))
    op.add_column("users", sa.Column("display_name", sa.String(length=255), nullable=True))
    op.add_column("users", sa.Column("timezone", sa.String(length=64), nullable=True))
    op.add_column("users", sa.Column("country", sa.String(length=4), nullable=True))
    op.add_column("users", sa.Column("preferred_currency", sa.String(length=3), nullable=True))
    op.add_column("users", sa.Column("profile_photo_url", sa.String(length=1024), nullable=True))
    op.add_column("users", sa.Column("biography", sa.Text, nullable=True))
    op.add_column("users", sa.Column("portfolio_url", sa.String(length=1024), nullable=True))
    op.add_column("users", sa.Column("years_of_experience", sa.Integer, nullable=True))
    op.add_column("users", sa.Column("primary_skills", postgresql.JSON, nullable=True))
    op.add_column("users", sa.Column("secondary_skills", postgresql.JSON, nullable=True))

    # --- User preferences table ---
    op.create_table(
        "user_preferences",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("min_budget", sa.Numeric(12, 2), nullable=True),
        sa.Column("max_budget", sa.Numeric(12, 2), nullable=True),
        sa.Column("preferred_categories", postgresql.JSON, nullable=True),
        sa.Column("preferred_technologies", postgresql.JSON, nullable=True),
        sa.Column("preferred_countries", postgresql.JSON, nullable=True),
        sa.Column("preferred_languages", postgresql.JSON, nullable=True),
        sa.Column("min_client_rating", sa.Float, nullable=True),
        sa.Column("require_payment_verified", sa.Boolean, nullable=False, server_default=sa.false()),
        sa.Column("max_competition_level", sa.Integer, nullable=True),
        sa.Column("max_daily_recommendations", sa.Integer, nullable=False, server_default="10"),
        sa.Column("preferred_project_age", sa.String(length=16), nullable=True),
        sa.Column("preferred_delivery_time", sa.String(length=16), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_user_preferences_user_id", "user_preferences", ["user_id"], unique=True)

    # --- AI preferences table ---
    op.create_table(
        "ai_preferences",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("ai_enabled", sa.Boolean, nullable=False, server_default=sa.true()),
        sa.Column("proposal_tone", sa.String(length=32), nullable=False, server_default="professional"),
        sa.Column("proposal_length", sa.String(length=16), nullable=False, server_default="medium"),
        sa.Column("writing_style", sa.String(length=32), nullable=False, server_default="concise"),
        sa.Column("automatically_include_portfolio", sa.Boolean, nullable=False, server_default=sa.true()),
        sa.Column("confidence_threshold", sa.Float, nullable=False, server_default="0.7"),
        sa.Column("bid_recommendation_style", sa.String(length=32), nullable=False, server_default="balanced"),
        sa.Column("ai_learning_enabled", sa.Boolean, nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_ai_preferences_user_id", "ai_preferences", ["user_id"], unique=True)

    # --- Notification preferences table ---
    op.create_table(
        "notification_preferences",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("push_enabled", sa.Boolean, nullable=False, server_default=sa.true()),
        sa.Column("email_enabled", sa.Boolean, nullable=False, server_default=sa.true()),
        sa.Column("high_confidence_projects", sa.Boolean, nullable=False, server_default=sa.true()),
        sa.Column("new_opportunities", sa.Boolean, nullable=False, server_default=sa.true()),
        sa.Column("messages", sa.Boolean, nullable=False, server_default=sa.true()),
        sa.Column("daily_summary", sa.Boolean, nullable=False, server_default=sa.true()),
        sa.Column("weekly_summary", sa.Boolean, nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
    )
    op.create_index(
        "ix_notification_preferences_user_id", "notification_preferences", ["user_id"], unique=True
    )


def downgrade() -> None:
    op.drop_index("ix_notification_preferences_user_id", table_name="notification_preferences")
    op.drop_table("notification_preferences")
    op.drop_index("ix_ai_preferences_user_id", table_name="ai_preferences")
    op.drop_table("ai_preferences")
    op.drop_index("ix_user_preferences_user_id", table_name="user_preferences")
    op.drop_table("user_preferences")

    op.drop_column("users", "secondary_skills")
    op.drop_column("users", "primary_skills")
    op.drop_column("users", "years_of_experience")
    op.drop_column("users", "portfolio_url")
    op.drop_column("users", "biography")
    op.drop_column("users", "profile_photo_url")
    op.drop_column("users", "preferred_currency")
    op.drop_column("users", "country")
    op.drop_column("users", "timezone")
    op.drop_column("users", "display_name")
    op.drop_column("users", "last_name")
    op.drop_column("users", "first_name")
