"""add team emblem url

Revision ID: 7a1c2e9d4b6f
Revises: 4f2a7b91c8e3
Create Date: 2026-05-17 18:30:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "7a1c2e9d4b6f"
down_revision: str | None = "4f2a7b91c8e3"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "teams",
        sa.Column("emblem_url", sa.String(length=2048), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("teams", "emblem_url")
