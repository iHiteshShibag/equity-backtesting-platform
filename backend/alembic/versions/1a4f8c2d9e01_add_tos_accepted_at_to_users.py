"""add tos_accepted_at to users

Revision ID: 1a4f8c2d9e01
Revises: 8e2d4f6a1b73
Create Date: 2026-07-15 09:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '1a4f8c2d9e01'
down_revision: Union[str, None] = '8e2d4f6a1b73'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('users', sa.Column('tos_accepted_at', sa.DateTime(timezone=True), nullable=True))


def downgrade() -> None:
    op.drop_column('users', 'tos_accepted_at')
