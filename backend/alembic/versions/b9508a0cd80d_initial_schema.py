"""initial schema

Revision ID: b9508a0cd80d
Revises:
Create Date: 2026-05-08 16:47:22.127778
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "b9508a0cd80d"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("nickname", sa.String(length=80), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column(
            "role",
            sa.Enum("organizer", "admin", name="userrole", native_enum=False),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_users_email"), "users", ["email"], unique=True)
    op.create_index(op.f("ix_users_id"), "users", ["id"], unique=False)
    op.create_index(op.f("ix_users_nickname"), "users", ["nickname"], unique=True)

    op.create_table(
        "seasons",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("start_date", sa.Date(), nullable=False),
        sa.Column("end_date", sa.Date(), nullable=False),
        sa.Column(
            "status",
            sa.Enum(
                "planned",
                "active",
                "finished",
                "archived",
                name="seasonstatus",
                native_enum=False,
            ),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_seasons_id"), "seasons", ["id"], unique=False)
    op.create_index(op.f("ix_seasons_name"), "seasons", ["name"], unique=True)

    op.create_table(
        "teams",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=160), nullable=False),
        sa.Column("city", sa.String(length=120), nullable=False),
        sa.Column("address", sa.String(length=255), nullable=True),
        sa.Column("manager_name", sa.String(length=160), nullable=True),
        sa.Column("previous_season_place", sa.Integer(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_teams_id"), "teams", ["id"], unique=False)
    op.create_index(op.f("ix_teams_name"), "teams", ["name"], unique=True)

    op.create_table(
        "referees",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("full_name", sa.String(length=160), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_referees_full_name"), "referees", ["full_name"])
    op.create_index(op.f("ix_referees_id"), "referees", ["id"], unique=False)

    op.create_table(
        "stadiums",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=160), nullable=False),
        sa.Column("city", sa.String(length=120), nullable=False),
        sa.Column("address", sa.String(length=255), nullable=False),
        sa.Column("capacity", sa.Integer(), nullable=False),
        sa.Column("home_team_id", sa.Integer(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint("capacity > 0", name="ck_stadium_capacity"),
        sa.ForeignKeyConstraint(["home_team_id"], ["teams.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_stadiums_id"), "stadiums", ["id"], unique=False)
    op.create_index(op.f("ix_stadiums_name"), "stadiums", ["name"], unique=False)

    op.create_table(
        "tournaments",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("season_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=160), nullable=False),
        sa.Column(
            "type",
            sa.Enum(
                "championship",
                "cup",
                name="tournamenttype",
                native_enum=False,
            ),
            nullable=False,
        ),
        sa.Column(
            "status",
            sa.Enum(
                "planned",
                "active",
                "finished",
                "cancelled",
                name="tournamentstatus",
                native_enum=False,
            ),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["season_id"], ["seasons.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_tournaments_id"), "tournaments", ["id"], unique=False)
    op.create_index(op.f("ix_tournaments_name"), "tournaments", ["name"])

    op.create_table(
        "players",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("full_name", sa.String(length=160), nullable=False),
        sa.Column("age", sa.Integer(), nullable=True),
        sa.Column(
            "position",
            sa.Enum(
                "goalkeeper",
                "defender",
                "midfielder",
                "forward",
                name="playerposition",
                native_enum=False,
            ),
            nullable=False,
        ),
        sa.Column("number", sa.Integer(), nullable=False),
        sa.Column("team_id", sa.Integer(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["team_id"], ["teams.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("team_id", "number", name="uq_player_number"),
    )
    op.create_index(op.f("ix_players_full_name"), "players", ["full_name"])
    op.create_index(op.f("ix_players_id"), "players", ["id"], unique=False)

    op.create_table(
        "matches",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("tournament_id", sa.Integer(), nullable=False),
        sa.Column("season_id", sa.Integer(), nullable=False),
        sa.Column("home_team_id", sa.Integer(), nullable=False),
        sa.Column("away_team_id", sa.Integer(), nullable=False),
        sa.Column("stadium_id", sa.Integer(), nullable=False),
        sa.Column("referee_id", sa.Integer(), nullable=True),
        sa.Column("match_datetime", sa.DateTime(timezone=True), nullable=False),
        sa.Column(
            "status",
            sa.Enum(
                "scheduled",
                "finished",
                "postponed",
                "cancelled",
                name="matchstatus",
                native_enum=False,
            ),
            nullable=False,
        ),
        sa.Column("round_number", sa.Integer(), nullable=False),
        sa.Column(
            "stage",
            sa.Enum("semifinal", "final", name="cupstage", native_enum=False),
            nullable=True,
        ),
        sa.Column("home_score", sa.Integer(), nullable=True),
        sa.Column("away_score", sa.Integer(), nullable=True),
        sa.Column("ticket_price", sa.Numeric(precision=10, scale=2), nullable=True),
        sa.Column("ticket_sold", sa.Integer(), nullable=False),
        sa.Column("income", sa.Numeric(precision=12, scale=2), nullable=True),
        sa.CheckConstraint(
            "away_score IS NULL OR away_score >= 0", name="ck_away_score"
        ),
        sa.CheckConstraint(
            "home_score IS NULL OR home_score >= 0", name="ck_home_score"
        ),
        sa.CheckConstraint(
            "home_team_id <> away_team_id", name="ck_match_distinct_teams"
        ),
        sa.CheckConstraint("ticket_sold >= 0", name="ck_match_ticket_sold"),
        sa.ForeignKeyConstraint(["away_team_id"], ["teams.id"]),
        sa.ForeignKeyConstraint(["home_team_id"], ["teams.id"]),
        sa.ForeignKeyConstraint(["referee_id"], ["referees.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["season_id"], ["seasons.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["stadium_id"], ["stadiums.id"]),
        sa.ForeignKeyConstraint(
            ["tournament_id"],
            ["tournaments.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_matches_id"), "matches", ["id"], unique=False)
    op.create_index("ix_matches_datetime", "matches", ["match_datetime"])

    op.create_table(
        "team_season_stats",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("team_id", sa.Integer(), nullable=False),
        sa.Column("season_id", sa.Integer(), nullable=False),
        sa.Column("played", sa.Integer(), nullable=False),
        sa.Column("wins", sa.Integer(), nullable=False),
        sa.Column("draws", sa.Integer(), nullable=False),
        sa.Column("losses", sa.Integer(), nullable=False),
        sa.Column("goals_scored", sa.Integer(), nullable=False),
        sa.Column("goals_conceded", sa.Integer(), nullable=False),
        sa.Column("goal_difference", sa.Integer(), nullable=False),
        sa.Column("points", sa.Integer(), nullable=False),
        sa.Column("place", sa.Integer(), nullable=True),
        sa.Column("cup_place", sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(["season_id"], ["seasons.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["team_id"], ["teams.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("team_id", "season_id", name="uq_team_season_stats"),
    )
    op.create_index(
        op.f("ix_team_season_stats_id"),
        "team_season_stats",
        ["id"],
        unique=False,
    )

    op.create_table(
        "player_season_stats",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("player_id", sa.Integer(), nullable=False),
        sa.Column("season_id", sa.Integer(), nullable=False),
        sa.Column("goals", sa.Integer(), nullable=False),
        sa.Column("assists", sa.Integer(), nullable=False),
        sa.Column("saves", sa.Integer(), nullable=False),
        sa.Column("yellow_cards", sa.Integer(), nullable=False),
        sa.Column("red_cards", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["player_id"], ["players.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["season_id"], ["seasons.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("player_id", "season_id", name="uq_player_season_stats"),
    )
    op.create_index(
        op.f("ix_player_season_stats_id"),
        "player_season_stats",
        ["id"],
        unique=False,
    )

    op.create_table(
        "match_lineups",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("match_id", sa.Integer(), nullable=False),
        sa.Column("team_id", sa.Integer(), nullable=False),
        sa.Column("player_id", sa.Integer(), nullable=False),
        sa.Column("is_starting", sa.Boolean(), nullable=False),
        sa.Column("position", sa.String(length=80), nullable=False),
        sa.Column("number", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["match_id"], ["matches.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["player_id"], ["players.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["team_id"], ["teams.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("match_id", "player_id", name="uq_match_lineup_player"),
    )
    op.create_index(op.f("ix_match_lineups_id"), "match_lineups", ["id"], unique=False)

    op.create_table(
        "match_events",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("match_id", sa.Integer(), nullable=False),
        sa.Column("team_id", sa.Integer(), nullable=False),
        sa.Column("player_id", sa.Integer(), nullable=False),
        sa.Column("assist_player_id", sa.Integer(), nullable=True),
        sa.Column(
            "event_type",
            sa.Enum(
                "goal",
                "assist",
                "save",
                "yellow_card",
                "red_card",
                name="matcheventtype",
                native_enum=False,
            ),
            nullable=False,
        ),
        sa.Column("minute", sa.Integer(), nullable=False),
        sa.CheckConstraint("minute >= 0", name="ck_match_event_minute"),
        sa.ForeignKeyConstraint(
            ["assist_player_id"],
            ["players.id"],
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(["match_id"], ["matches.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["player_id"], ["players.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["team_id"], ["teams.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_match_events_id"), "match_events", ["id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_match_events_id"), table_name="match_events")
    op.drop_table("match_events")
    op.drop_index(op.f("ix_match_lineups_id"), table_name="match_lineups")
    op.drop_table("match_lineups")
    op.drop_index(
        op.f("ix_player_season_stats_id"),
        table_name="player_season_stats",
    )
    op.drop_table("player_season_stats")
    op.drop_index(op.f("ix_team_season_stats_id"), table_name="team_season_stats")
    op.drop_table("team_season_stats")
    op.drop_index("ix_matches_datetime", table_name="matches")
    op.drop_index(op.f("ix_matches_id"), table_name="matches")
    op.drop_table("matches")
    op.drop_index(op.f("ix_players_id"), table_name="players")
    op.drop_index(op.f("ix_players_full_name"), table_name="players")
    op.drop_table("players")
    op.drop_index(op.f("ix_tournaments_name"), table_name="tournaments")
    op.drop_index(op.f("ix_tournaments_id"), table_name="tournaments")
    op.drop_table("tournaments")
    op.drop_index(op.f("ix_stadiums_name"), table_name="stadiums")
    op.drop_index(op.f("ix_stadiums_id"), table_name="stadiums")
    op.drop_table("stadiums")
    op.drop_index(op.f("ix_referees_id"), table_name="referees")
    op.drop_index(op.f("ix_referees_full_name"), table_name="referees")
    op.drop_table("referees")
    op.drop_index(op.f("ix_teams_name"), table_name="teams")
    op.drop_index(op.f("ix_teams_id"), table_name="teams")
    op.drop_table("teams")
    op.drop_index(op.f("ix_seasons_name"), table_name="seasons")
    op.drop_index(op.f("ix_seasons_id"), table_name="seasons")
    op.drop_table("seasons")
    op.drop_index(op.f("ix_users_nickname"), table_name="users")
    op.drop_index(op.f("ix_users_id"), table_name="users")
    op.drop_index(op.f("ix_users_email"), table_name="users")
    op.drop_table("users")
