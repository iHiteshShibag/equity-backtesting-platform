"""add role and is_active to users

Revision ID: 9a1c2f4e5b7d
Revises: 7fcb989ab662
Create Date: 2026-07-13 16:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '9a1c2f4e5b7d'
down_revision: Union[str, None] = '7fcb989ab662'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('users', sa.Column('role', sa.String(length=20), nullable=False, server_default='member'))
    op.add_column('users', sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.true()))
    op.execute("UPDATE users SET role = 'admin'")


def downgrade() -> None:
    op.drop_column('users', 'is_active')
    op.drop_column('users', 'role')
