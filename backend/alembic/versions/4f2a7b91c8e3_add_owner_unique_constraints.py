"""add owner unique constraints

Revision ID: 4f2a7b91c8e3
Revises: 9d3f4e1a6b2c
Create Date: 2026-05-10 14:30:00.000000
"""

from collections.abc import Sequence

from alembic import op

revision: str = "4f2a7b91c8e3"
down_revision: str | None = "9d3f4e1a6b2c"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_unique_constraint(
        "uq_referee_owner_full_name",
        "referees",
        ["owner_id", "full_name"],
    )
    op.create_unique_constraint(
        "uq_stadium_owner_name",
        "stadiums",
        ["owner_id", "name"],
    )
    op.create_unique_constraint(
        "uq_tournament_owner_season_name",
        "tournaments",
        ["owner_id", "season_id", "name"],
    )


def downgrade() -> None:
    op.drop_constraint(
        "uq_tournament_owner_season_name",
        "tournaments",
        type_="unique",
    )
    op.drop_constraint("uq_stadium_owner_name", "stadiums", type_="unique")
    op.drop_constraint("uq_referee_owner_full_name", "referees", type_="unique")
