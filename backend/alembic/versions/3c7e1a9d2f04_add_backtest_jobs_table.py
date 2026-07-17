"""add backtest_jobs table

Revision ID: 3c7e1a9d2f04
Revises: 9a1c2f4e5b7d
Create Date: 2026-07-13 17:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = '3c7e1a9d2f04'
down_revision: Union[str, None] = '9a1c2f4e5b7d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table('backtest_jobs',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('user_id', sa.Integer(), nullable=False),
    sa.Column('status', sa.String(length=20), nullable=False, server_default='pending'),
    sa.Column('request', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
    sa.Column('result', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    sa.Column('error', sa.Text(), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
    sa.ForeignKeyConstraint(['user_id'], ['users.id']),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_backtest_jobs_user_id'), 'backtest_jobs', ['user_id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_backtest_jobs_user_id'), table_name='backtest_jobs')
    op.drop_table('backtest_jobs')
