from __future__ import annotations

import argparse
import csv
from dataclasses import dataclass
from datetime import date, datetime, time, timedelta
from pathlib import Path
from typing import TextIO

from sqlalchemy import func, select
from sqlalchemy.orm import Session

import app.models  # noqa: F401
from app.core.constants import (
    CupStage,
    PlayerPosition,
    SeasonStatus,
    TournamentStatus,
    TournamentType,
)
from app.core.exceptions import AppError
from app.db.session import SessionLocal
from app.models.match import Match
from app.models.player import Player
from app.models.referee import Referee
from app.models.season import Season
from app.models.stadium import Stadium
from app.models.team import Team
from app.models.tournament import Tournament
from app.repositories.match import MatchRepository
from app.repositories.season import SeasonRepository
from app.repositories.stadium import StadiumRepository
from app.repositories.team import TeamRepository
from app.repositories.tournament import TournamentRepository
from app.schemas.cup import CupSemifinalsGenerate
from app.schemas.schedule import ChampionshipScheduleGenerate
from app.services.cup_service import CupService
from app.services.schedule_service import ScheduleService
from app.services.ticket_price_service import TicketPriceService

CSV_DELIMITER = ";"
DEFAULT_REFEREES = (
    "Alejandro Hernandez",
    "Ricardo de Burgos",
    "Jose Luis Munuera",
    "Cesar Soto",
    "Jesus Gil",
    "Javier Alberola",
    "Miguel Ortiz",
    "Guillermo Cuadra",
)
POSITION_BY_SOURCE = {
    "goalkeeper": PlayerPosition.GOALKEEPER,
    "defender": PlayerPosition.DEFENDER,
    "midfielder": PlayerPosition.MIDFIELDER,
    "attacker": PlayerPosition.FORWARD,
    "forward": PlayerPosition.FORWARD,
}


@dataclass(frozen=True)
class ClubSeedRow:
    club_id: int
    club_name: str
    city: str
    stadium: str
    stadium_address: str
    coach: str | None


@dataclass(frozen=True)
class PlayerSeedRow:
    club_id: int
    player_name: str
    age: int | None
    number: int | None
    position: PlayerPosition


@dataclass(frozen=True)
class DemoSeedSummary:
    seasons: int
    tournaments: int
    teams: int
    stadiums: int
    players: int
    referees: int
    matches: int


class DemoDataSeeder:
    def __init__(
        self,
        db: Session,
        *,
        default_stadium_capacity: int = 50000,
    ) -> None:
        self.db = db
        self.default_stadium_capacity = default_stadium_capacity

    def seed_from_csv(
        self,
        *,
        clubs_csv: Path,
        squads_csv: Path,
        season_name: str = "LaLiga Demo 2026/27",
        season_start: date = date(2026, 8, 1),
        season_end: date = date(2027, 6, 30),
        championship_name: str = "LaLiga Demo Championship",
        cup_name: str = "LaLiga Demo Cup",
        generate_cup_semifinals: bool = True,
        generate_championship_schedule: bool = False,
    ) -> DemoSeedSummary:
        clubs = read_clubs_csv(clubs_csv)
        players = read_squads_csv(squads_csv)

        season = self._upsert_season(
            name=season_name,
            start_date=season_start,
            end_date=season_end,
        )
        championship = self._upsert_tournament(
            season_id=season.id,
            name=championship_name,
            tournament_type=TournamentType.CHAMPIONSHIP,
        )
        cup = self._upsert_tournament(
            season_id=season.id,
            name=cup_name,
            tournament_type=TournamentType.CUP,
        )
        teams_by_source_id = self._upsert_teams_and_stadiums(clubs)
        self._upsert_players(players=players, teams_by_source_id=teams_by_source_id)
        self._upsert_referees()
        self.db.commit()

        if generate_championship_schedule:
            self._generate_championship_schedule(
                tournament=championship,
                team_ids=[teams_by_source_id[club.club_id].id for club in clubs],
                season_start=season_start,
            )
        if generate_cup_semifinals:
            self._generate_cup_semifinals(cup=cup, season_end=season_end)

        return self._build_summary()

    def _upsert_season(
        self,
        *,
        name: str,
        start_date: date,
        end_date: date,
    ) -> Season:
        season = self.db.scalar(select(Season).where(Season.name == name))
        if season is None:
            season = Season(
                name=name,
                start_date=start_date,
                end_date=end_date,
                status=SeasonStatus.ACTIVE,
            )
            self.db.add(season)
        else:
            season.start_date = start_date
            season.end_date = end_date
            season.status = SeasonStatus.ACTIVE
        self.db.flush()
        return season

    def _upsert_tournament(
        self,
        *,
        season_id: int,
        name: str,
        tournament_type: TournamentType,
    ) -> Tournament:
        tournament = self.db.scalar(
            select(Tournament).where(
                Tournament.season_id == season_id,
                Tournament.name == name,
            )
        )
        if tournament is None:
            tournament = Tournament(
                season_id=season_id,
                name=name,
                type=tournament_type,
                status=TournamentStatus.ACTIVE,
            )
            self.db.add(tournament)
        else:
            tournament.type = tournament_type
            tournament.status = TournamentStatus.ACTIVE
        self.db.flush()
        return tournament

    def _upsert_teams_and_stadiums(
        self,
        clubs: list[ClubSeedRow],
    ) -> dict[int, Team]:
        teams_by_source_id: dict[int, Team] = {}
        for previous_place, club in enumerate(clubs, start=1):
            team = self._upsert_team(club=club, previous_place=previous_place)
            self._upsert_stadium(club=club, team=team)
            teams_by_source_id[club.club_id] = team
        return teams_by_source_id

    def _upsert_team(self, *, club: ClubSeedRow, previous_place: int) -> Team:
        team = self.db.scalar(select(Team).where(Team.name == club.club_name))
        if team is None:
            team = Team(
                name=club.club_name,
                city=club.city,
                address=club.stadium_address,
                manager_name=club.coach,
                previous_season_place=previous_place,
            )
            self.db.add(team)
        else:
            team.city = club.city
            team.address = club.stadium_address
            team.manager_name = club.coach
            team.previous_season_place = previous_place
        self.db.flush()
        return team

    def _upsert_stadium(self, *, club: ClubSeedRow, team: Team) -> Stadium:
        stadium = self.db.scalar(select(Stadium).where(Stadium.name == club.stadium))
        if stadium is None:
            stadium = Stadium(
                name=club.stadium,
                city=club.city,
                address=club.stadium_address,
                capacity=self.default_stadium_capacity,
                home_team_id=team.id,
            )
            self.db.add(stadium)
        else:
            stadium.city = club.city
            stadium.address = club.stadium_address
            stadium.capacity = self.default_stadium_capacity
            stadium.home_team_id = team.id
        self.db.flush()
        return stadium

    def _upsert_players(
        self,
        *,
        players: list[PlayerSeedRow],
        teams_by_source_id: dict[int, Team],
    ) -> None:
        players_by_club: dict[int, list[PlayerSeedRow]] = {}
        for player in players:
            players_by_club.setdefault(player.club_id, []).append(player)

        for club_id, team in teams_by_source_id.items():
            existing_players = {
                player.full_name: player
                for player in self.db.scalars(
                    select(Player).where(Player.team_id == team.id)
                )
            }
            used_numbers: set[int] = set()
            for player_row in players_by_club.get(club_id, []):
                number = self._resolve_player_number(
                    preferred_number=player_row.number,
                    used_numbers=used_numbers,
                )
                player = existing_players.get(player_row.player_name)
                if player is None:
                    player = Player(
                        full_name=player_row.player_name,
                        age=player_row.age,
                        position=player_row.position,
                        number=number,
                        team_id=team.id,
                    )
                    self.db.add(player)
                else:
                    player.age = player_row.age
                    player.position = player_row.position
                    player.number = number
                    player.team_id = team.id
        self.db.flush()

    def _resolve_player_number(
        self,
        *,
        preferred_number: int | None,
        used_numbers: set[int],
    ) -> int:
        if (
            preferred_number is not None
            and 1 <= preferred_number <= 99
            and preferred_number not in used_numbers
        ):
            used_numbers.add(preferred_number)
            return preferred_number

        for number in range(1, 100):
            if number not in used_numbers:
                used_numbers.add(number)
                return number
        raise ValueError("Cannot assign a unique player number between 1 and 99.")

    def _upsert_referees(self) -> None:
        for full_name in DEFAULT_REFEREES:
            referee = self.db.scalar(
                select(Referee).where(Referee.full_name == full_name)
            )
            if referee is None:
                self.db.add(Referee(full_name=full_name))
        self.db.flush()

    def _generate_championship_schedule(
        self,
        *,
        tournament: Tournament,
        team_ids: list[int],
        season_start: date,
    ) -> None:
        existing_match = self.db.scalar(
            select(Match).where(Match.tournament_id == tournament.id).limit(1)
        )
        if existing_match is not None:
            return

        schedule_service = ScheduleService(
            matches=MatchRepository(self.db),
            tournaments=TournamentRepository(self.db),
            seasons=SeasonRepository(self.db),
            teams=TeamRepository(self.db),
            stadiums=StadiumRepository(self.db),
            ticket_prices=TicketPriceService(),
        )
        payload = ChampionshipScheduleGenerate(
            start_datetime=datetime.combine(
                season_start + timedelta(days=14),
                time(hour=19),
            ),
            match_time=time(hour=19),
            interval_days=4,
            team_ids=team_ids,
        )
        schedule_service.generate_championship_schedule(
            tournament_id=tournament.id,
            payload=payload,
        )

    def _generate_cup_semifinals(self, *, cup: Tournament, season_end: date) -> None:
        existing_semifinal = self.db.scalar(
            select(Match)
            .where(Match.tournament_id == cup.id, Match.stage == CupStage.SEMIFINAL)
            .limit(1)
        )
        if existing_semifinal is not None:
            return

        cup_service = CupService(
            matches=MatchRepository(self.db),
            tournaments=TournamentRepository(self.db),
            teams=TeamRepository(self.db),
            stadiums=StadiumRepository(self.db),
            schedule=ScheduleService(MatchRepository(self.db)),
            ticket_prices=TicketPriceService(),
        )
        first_semifinal_date = season_end - timedelta(days=30)
        payload = CupSemifinalsGenerate(
            use_previous_season_places=True,
            match_datetimes=[
                datetime.combine(first_semifinal_date, time(hour=20)),
                datetime.combine(
                    first_semifinal_date + timedelta(days=1),
                    time(hour=20),
                ),
            ],
        )
        cup_service.generate_semifinals(tournament_id=cup.id, payload=payload)

    def _build_summary(self) -> DemoSeedSummary:
        return DemoSeedSummary(
            seasons=self._count(Season),
            tournaments=self._count(Tournament),
            teams=self._count(Team),
            stadiums=self._count(Stadium),
            players=self._count(Player),
            referees=self._count(Referee),
            matches=self._count(Match),
        )

    def _count(self, model: type) -> int:
        return int(self.db.scalar(select(func.count()).select_from(model)) or 0)


def read_clubs_csv(path: Path) -> list[ClubSeedRow]:
    with _open_csv(path) as file:
        reader = csv.DictReader(file, delimiter=CSV_DELIMITER)
        return [
            ClubSeedRow(
                club_id=_required_int(row, "club_id"),
                club_name=_required_text(row, "club_name"),
                city=_required_text(row, "city"),
                stadium=_required_text(row, "stadium"),
                stadium_address=_required_text(row, "stadium_address"),
                coach=_optional_text(row, "coach"),
            )
            for row in reader
        ]


def read_squads_csv(path: Path) -> list[PlayerSeedRow]:
    with _open_csv(path) as file:
        reader = csv.DictReader(file, delimiter=CSV_DELIMITER)
        return [
            PlayerSeedRow(
                club_id=_required_int(row, "club_id"),
                player_name=_required_text(row, "player_name"),
                age=_optional_age(row.get("age")),
                number=_optional_int(row.get("number")),
                position=_parse_position(_required_text(row, "position")),
            )
            for row in reader
        ]


def _open_csv(path: Path) -> TextIO:
    return path.open("r", encoding="utf-8-sig", newline="")


def _required_text(row: dict[str, str], field: str) -> str:
    value = (row.get(field) or "").strip()
    if not value:
        raise ValueError(f"CSV field {field!r} is required.")
    return value[:160]


def _optional_text(row: dict[str, str], field: str) -> str | None:
    value = (row.get(field) or "").strip()
    return value[:160] if value else None


def _required_int(row: dict[str, str], field: str) -> int:
    value = _optional_int(row.get(field))
    if value is None:
        raise ValueError(f"CSV field {field!r} must be an integer.")
    return value


def _optional_int(value: str | None) -> int | None:
    if value is None or not value.strip():
        return None
    return int(float(value))


def _optional_age(value: str | None) -> int | None:
    age = _optional_int(value)
    if age is None:
        return None
    return min(max(age, 14), 60)


def _parse_position(value: str) -> PlayerPosition:
    position = POSITION_BY_SOURCE.get(value.strip().lower())
    if position is None:
        raise ValueError(f"Unsupported player position: {value}.")
    return position


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Seed LaLiga demo data from CSV.")
    parser.add_argument("--clubs-csv", type=Path, required=True)
    parser.add_argument("--squads-csv", type=Path, required=True)
    parser.add_argument("--season-name", default="LaLiga Demo 2026/27")
    parser.add_argument(
        "--season-start",
        type=date.fromisoformat,
        default=date(2026, 8, 1),
    )
    parser.add_argument(
        "--season-end",
        type=date.fromisoformat,
        default=date(2027, 6, 30),
    )
    parser.add_argument(
        "--championship-name",
        default="LaLiga Demo Championship",
    )
    parser.add_argument("--cup-name", default="LaLiga Demo Cup")
    parser.add_argument("--default-stadium-capacity", type=int, default=50000)
    parser.add_argument(
        "--skip-cup-semifinals",
        action="store_true",
        help="Create cup tournament data without creating semifinal matches.",
    )
    parser.add_argument(
        "--generate-championship-schedule",
        action="store_true",
        help="Also create a full double round-robin championship schedule.",
    )
    return parser


def main() -> None:
    args = build_parser().parse_args()
    with SessionLocal() as db:
        try:
            summary = DemoDataSeeder(
                db,
                default_stadium_capacity=args.default_stadium_capacity,
            ).seed_from_csv(
                clubs_csv=args.clubs_csv,
                squads_csv=args.squads_csv,
                season_name=args.season_name,
                season_start=args.season_start,
                season_end=args.season_end,
                championship_name=args.championship_name,
                cup_name=args.cup_name,
                generate_cup_semifinals=not args.skip_cup_semifinals,
                generate_championship_schedule=args.generate_championship_schedule,
            )
        except (AppError, ValueError) as exc:
            db.rollback()
            raise SystemExit(f"Could not seed demo data: {exc}") from exc

    print("Demo data seed complete.")
    print(f"Seasons: {summary.seasons}")
    print(f"Tournaments: {summary.tournaments}")
    print(f"Teams: {summary.teams}")
    print(f"Stadiums: {summary.stadiums}")
    print(f"Players: {summary.players}")
    print(f"Referees: {summary.referees}")
    print(f"Matches: {summary.matches}")


if __name__ == "__main__":
    main()
