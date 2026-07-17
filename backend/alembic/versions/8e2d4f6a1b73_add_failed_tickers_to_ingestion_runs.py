"""add failed ticker lists to ingestion_runs

Revision ID: 8e2d4f6a1b73
Revises: 5b8f2e1c7a93
Create Date: 2026-07-13 18:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = '8e2d4f6a1b73'
down_revision: Union[str, None] = '5b8f2e1c7a93'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('ingestion_runs', sa.Column('prices_failed_tickers', postgresql.JSONB(astext_type=sa.Text()), nullable=True))
    op.add_column('ingestion_runs', sa.Column('funds_failed_tickers', postgresql.JSONB(astext_type=sa.Text()), nullable=True))


def downgrade() -> None:
    op.drop_column('ingestion_runs', 'funds_failed_tickers')
    op.drop_column('ingestion_runs', 'prices_failed_tickers')
