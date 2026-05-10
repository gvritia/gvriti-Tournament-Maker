"""add owner scope

Revision ID: 9d3f4e1a6b2c
Revises: b9508a0cd80d
Create Date: 2026-05-09 22:30:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "9d3f4e1a6b2c"
down_revision: str | None = "b9508a0cd80d"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

OWNER_TABLES = (
    "seasons",
    "teams",
    "referees",
    "stadiums",
    "tournaments",
    "players",
    "matches",
    "team_season_stats",
    "player_season_stats",
    "match_lineups",
    "match_events",
)


def upgrade() -> None:
    bind = op.get_bind()
    owner_id = bind.execute(
        sa.text("SELECT id FROM users ORDER BY id LIMIT 1")
    ).scalar()
    if owner_id is None:
        owner_id = bind.execute(sa.text("""
                INSERT INTO users (nickname, email, password_hash, role)
                VALUES (
                    'demo-owner',
                    'demo-owner@example.com',
                    '$2b$12$8jXLsZUL3nKjR3bA9j1mguYkxWNU9FsShyX8FYioAvU0dR2rXLu8S',
                    'organizer'
                )
                RETURNING id
                """)).scalar_one()

    for table_name in OWNER_TABLES:
        op.add_column(table_name, sa.Column("owner_id", sa.Integer(), nullable=True))
        op.execute(
            sa.text(f"UPDATE {table_name} SET owner_id = :owner_id").bindparams(
                owner_id=owner_id
            )
        )
        op.alter_column(table_name, "owner_id", nullable=False)
        op.create_index(
            op.f(f"ix_{table_name}_owner_id"),
            table_name,
            ["owner_id"],
            unique=False,
        )
        op.create_foreign_key(
            f"fk_{table_name}_owner_id_users",
            table_name,
            "users",
            ["owner_id"],
            ["id"],
            ondelete="CASCADE",
        )

    op.drop_index(op.f("ix_seasons_name"), table_name="seasons")
    op.create_index(op.f("ix_seasons_name"), "seasons", ["name"], unique=False)
    op.create_unique_constraint(
        "uq_season_owner_name",
        "seasons",
        ["owner_id", "name"],
    )

    op.drop_index(op.f("ix_teams_name"), table_name="teams")
    op.create_index(op.f("ix_teams_name"), "teams", ["name"], unique=False)
    op.create_unique_constraint(
        "uq_team_owner_name",
        "teams",
        ["owner_id", "name"],
    )


def downgrade() -> None:
    op.drop_constraint("uq_team_owner_name", "teams", type_="unique")
    op.drop_index(op.f("ix_teams_name"), table_name="teams")
    op.create_index(op.f("ix_teams_name"), "teams", ["name"], unique=True)

    op.drop_constraint("uq_season_owner_name", "seasons", type_="unique")
    op.drop_index(op.f("ix_seasons_name"), table_name="seasons")
    op.create_index(op.f("ix_seasons_name"), "seasons", ["name"], unique=True)

    for table_name in reversed(OWNER_TABLES):
        op.drop_constraint(
            f"fk_{table_name}_owner_id_users",
            table_name,
            type_="foreignkey",
        )
        op.drop_index(op.f(f"ix_{table_name}_owner_id"), table_name=table_name)
        op.drop_column(table_name, "owner_id")
