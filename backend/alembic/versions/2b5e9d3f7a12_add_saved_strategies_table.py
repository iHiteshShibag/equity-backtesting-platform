"""add saved_strategies table

Revision ID: 2b5e9d3f7a12
Revises: 1a4f8c2d9e01
Create Date: 2026-07-15 09:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = '2b5e9d3f7a12'
down_revision: Union[str, None] = '1a4f8c2d9e01'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'saved_strategies',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id'), nullable=False, index=True),
        sa.Column('name', sa.String(length=200), nullable=False),
        sa.Column('request', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('rebalance_freq', sa.String(length=20), nullable=False),
        sa.Column('next_rebalance_date', sa.Date(), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )


def downgrade() -> None:
    op.drop_table('saved_strategies')
