"""add freelancer fields to user

Revision ID: 0010
Revises: 0009
Create Date: 2026-07-12 11:05:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '0010'
down_revision: Union[str, None] = '0009'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table('users') as batch_op:
        batch_op.add_column(sa.Column('freelancer_user_id', sa.String(length=64), nullable=True))
        batch_op.add_column(sa.Column('freelancer_oauth_token', sa.Text(), nullable=True))
        batch_op.add_column(sa.Column('freelancer_refresh_token', sa.Text(), nullable=True))
        batch_op.add_column(sa.Column('freelancer_token_expires_at', sa.DateTime(timezone=True), nullable=True))
        batch_op.add_column(sa.Column('freelancer_connected_at', sa.DateTime(timezone=True), nullable=True))
        batch_op.create_unique_constraint('uq_users_freelancer_user_id', ['freelancer_user_id'])


def downgrade() -> None:
    with op.batch_alter_table('users') as batch_op:
        batch_op.drop_constraint('uq_users_freelancer_user_id', type_='unique')
        batch_op.drop_column('freelancer_connected_at')
        batch_op.drop_column('freelancer_token_expires_at')
        batch_op.drop_column('freelancer_refresh_token')
        batch_op.drop_column('freelancer_oauth_token')
        batch_op.drop_column('freelancer_user_id')