"""add index_memberships table, seed NIFTY100 point-in-time membership

Revision ID: 3c8f1a6e0d45
Revises: 2b5e9d3f7a12
Create Date: 2026-07-15 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '3c8f1a6e0d45'
down_revision: Union[str, None] = '2b5e9d3f7a12'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


index_memberships_table = sa.table(
    'index_memberships',
    sa.column('index_name', sa.String),
    sa.column('ticker', sa.String),
    sa.column('start_date', sa.Date),
    sa.column('end_date', sa.Date),
)


def upgrade() -> None:
    op.create_table(
        'index_memberships',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('index_name', sa.String(length=50), nullable=False, server_default='NIFTY100'),
        sa.Column('ticker', sa.String(length=20), nullable=False, index=True),
        sa.Column('start_date', sa.Date(), nullable=False),
        sa.Column('end_date', sa.Date(), nullable=True),
    )

    # Seed from the manually-compiled list -- see index_membership_seed.py
    # for provenance and caveats (best-effort, not a licensed data feed).
    from app.modules.market_data.index_membership_seed import seed_rows
    from app.modules.market_data.universe import NIFTY100_TICKERS

    rows = seed_rows('NIFTY100', NIFTY100_TICKERS)
    if rows:
        op.bulk_insert(index_memberships_table, rows)


def downgrade() -> None:
    op.drop_table('index_memberships')
