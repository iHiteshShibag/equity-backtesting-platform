"""add ingestion_runs table

Revision ID: 5b8f2e1c7a93
Revises: 3c7e1a9d2f04
Create Date: 2026-07-13 18:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '5b8f2e1c7a93'
down_revision: Union[str, None] = '3c7e1a9d2f04'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table('ingestion_runs',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('trigger', sa.String(length=20), nullable=False),
    sa.Column('status', sa.String(length=20), nullable=False, server_default='running'),
    sa.Column('step', sa.String(length=100), nullable=True),
    sa.Column('prices_success', sa.Integer(), nullable=False, server_default='0'),
    sa.Column('prices_failed', sa.Integer(), nullable=False, server_default='0'),
    sa.Column('funds_success', sa.Integer(), nullable=False, server_default='0'),
    sa.Column('funds_failed', sa.Integer(), nullable=False, server_default='0'),
    sa.Column('error', sa.Text(), nullable=True),
    sa.Column('started_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('finished_at', sa.DateTime(timezone=True), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )


def downgrade() -> None:
    op.drop_table('ingestion_runs')
