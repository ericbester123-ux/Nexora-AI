"""add subscription_status to user

Revision ID: 0009
Revises: 0008
Create Date: 2026-07-11 22:45:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '0009'
down_revision: Union[str, None] = '0008'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('users', sa.Column('subscription_status', sa.String(length=32), nullable=False, server_default='pending'))


def downgrade() -> None:
    op.drop_column('users', 'subscription_status')