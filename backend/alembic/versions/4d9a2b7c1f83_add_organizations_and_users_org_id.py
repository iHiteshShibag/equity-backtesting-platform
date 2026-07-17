"""add organizations table and users.org_id, backfill existing users

Revision ID: 4d9a2b7c1f83
Revises: 3c8f1a6e0d45
Create Date: 2026-07-15 10:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '4d9a2b7c1f83'
down_revision: Union[str, None] = '3c8f1a6e0d45'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'organizations',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('name', sa.String(length=200), nullable=False),
        sa.Column('tier', sa.String(length=20), nullable=False, server_default='free'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    op.add_column('users', sa.Column('org_id', sa.Integer(), sa.ForeignKey('organizations.id'), nullable=True))

    # Backfill: every pre-existing user goes into a single default org so
    # org_id has a real value everywhere going forward (new users get one too,
    # see app/modules/users/router.py). Left nullable rather than NOT NULL
    # since this is scaffolding, not an enforced invariant yet.
    conn = op.get_bind()
    default_org_id = conn.execute(
        sa.text("INSERT INTO organizations (name, tier) VALUES ('Default Organization', 'free') RETURNING id")
    ).scalar()
    conn.execute(sa.text("UPDATE users SET org_id = :org_id"), {"org_id": default_org_id})


def downgrade() -> None:
    op.drop_column('users', 'org_id')
    op.drop_table('organizations')
