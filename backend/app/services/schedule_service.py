from datetime import datetime, timedelta
from decimal import Decimal

from sqlalchemy.exc import IntegrityError

from app.core.constants import MatchStatus, TournamentType
from app.core.exceptions import BusinessRuleError, ConflictError, NotFoundError
from app.models.match import Match
from app.models.stadium import Stadium
from app.models.team import Team
from app.repositories.match import MatchRepository
from app.repositories.season import SeasonRepository
from app.repositories.stadium import StadiumRepository
from app.repositories.team import TeamRepository
from app.repositories.tournament import TournamentRepository
from app.schemas.schedule import ChampionshipScheduleGenerate
from app.services.ticket_price_service import TicketPriceService
from app.utils.datetime_utils import start_of_day, start_of_week


class ScheduleService:
    def __init__(
        self,
        matches: MatchRepository,
        tournaments: TournamentRepository | None = None,
        seasons: SeasonRepository | None = None,
        teams: TeamRepository | None = None,
        stadiums: StadiumRepository | None = None,
        ticket_prices: TicketPriceService | None = None,
    ) -> None:
        self.matches = matches
        self.tournaments = tournaments
        self.seasons = seasons
        self.teams = teams
        self.stadiums = stadiums
        self.ticket_prices = ticket_prices

    def validate_team_can_play_at(
        self,
        *,
        team_id: int,
        match_datetime: datetime,
        exclude_match_id: int | None = None,
    ) -> None:
        """Validate calendar limits before scheduling or moving a match."""
        day_start = start_of_day(match_datetime)
        day_matches = self.matches.list_team_matches_between(
            team_id=team_id,
            starts_at=day_start,
            ends_at=day_start + timedelta(days=1),
            exclude_match_id=exclude_match_id,
        )
        if day_matches:
            raise ConflictError("A team cannot play more than one match per day.")

        week_start = start_of_week(match_datetime)
        week_matches = self.matches.list_team_matches_between(
            team_id=team_id,
            starts_at=week_start,
            ends_at=week_start + timedelta(days=7),
            exclude_match_id=exclude_match_id,
        )
        if len(week_matches) >= 2:
            raise ConflictError("A team cannot play more than two matches per week.")

    def validate_teams_can_play_at(
        self,
        *,
        home_team_id: int,
        away_team_id: int,
        match_datetime: datetime,
        exclude_match_id: int | None = None,
    ) -> None:
        self.validate_team_can_play_at(
            team_id=home_team_id,
            match_datetime=match_datetime,
            exclude_match_id=exclude_match_id,
        )
        self.validate_team_can_play_at(
            team_id=away_team_id,
            match_datetime=match_datetime,
            exclude_match_id=exclude_match_id,
        )

    def generate_championship_schedule(
        self,
        *,
        tournament_id: int,
        payload: ChampionshipScheduleGenerate,
    ) -> list[Match]:
        (
            tournaments,
            seasons,
            teams,
            stadiums,
            ticket_prices,
        ) = self._require_generation_dependencies()

        tournament = tournaments.get(tournament_id)
        if tournament is None:
            raise NotFoundError("Tournament not found.")
        if tournament.type != TournamentType.CHAMPIONSHIP:
            raise BusinessRuleError(
                "Championship schedule can be generated only for "
                "championship tournaments."
            )
        season = seasons.get(tournament.season_id)
        if season is None:
            raise NotFoundError("Season not found.")

        team_ids = self._validate_team_ids(payload.team_ids)
        teams_by_id = self._get_teams_by_id(teams, team_ids)
        stadiums_by_team_id = self._resolve_stadiums_by_team_id(
            stadiums=stadiums,
            team_ids=team_ids,
            payload=payload,
        )
        rounds = self._build_double_round_robin_rounds(team_ids)
        previous_season_table_size = teams.get_previous_season_table_size()

        created_matches: list[Match] = []
        try:
            for round_index, pairings in enumerate(rounds):
                match_datetime = self._get_round_datetime(
                    start_datetime=payload.start_datetime,
                    round_index=round_index,
                    interval_days=payload.interval_days,
                    payload=payload,
                )
                round_number = round_index + 1
                for home_team_id, away_team_id in pairings:
                    self.validate_teams_can_play_at(
                        home_team_id=home_team_id,
                        away_team_id=away_team_id,
                        match_datetime=match_datetime,
                    )
                    home_team = teams_by_id[home_team_id]
                    away_team = teams_by_id[away_team_id]
                    stadium = stadiums_by_team_id[home_team_id]
                    match = Match(
                        tournament_id=tournament.id,
                        season_id=season.id,
                        home_team_id=home_team_id,
                        away_team_id=away_team_id,
                        stadium_id=stadium.id,
                        referee_id=None,
                        match_datetime=match_datetime,
                        status=MatchStatus.SCHEDULED,
                        round_number=round_number,
                        stage=None,
                        ticket_price=ticket_prices.calculate_default_price(
                            stadium=stadium,
                            home_team=home_team,
                            away_team=away_team,
                            previous_season_table_size=previous_season_table_size,
                        ),
                        ticket_sold=0,
                        income=Decimal("0.00"),
                    )
                    self.matches.add(match)
                    created_matches.append(match)
            self.matches.db.commit()
            for match in created_matches:
                self.matches.db.refresh(match)
        except (BusinessRuleError, ConflictError, NotFoundError):
            self.matches.db.rollback()
            raise
        except IntegrityError as exc:
            self.matches.db.rollback()
            raise ConflictError(
                "Could not generate schedule because of a conflict."
            ) from exc
        return created_matches

    def list_season_matches(self, season_id: int) -> list[Match]:
        if self.seasons is None:
            raise RuntimeError("Season repository is required for schedule views.")
        season = self.seasons.get(season_id)
        if season is None:
            raise NotFoundError("Season not found.")
        return self.matches.list_by_season(season_id)

    def list_stadium_matches(self, stadium_id: int) -> list[Match]:
        if self.stadiums is None:
            raise RuntimeError("Stadium repository is required for schedule views.")
        stadium = self.stadiums.get(stadium_id)
        if stadium is None:
            raise NotFoundError("Stadium not found.")
        return self.matches.list_by_stadium(stadium_id)

    def _require_generation_dependencies(
        self,
    ) -> tuple[
        TournamentRepository,
        SeasonRepository,
        TeamRepository,
        StadiumRepository,
        TicketPriceService,
    ]:
        if (
            self.tournaments is None
            or self.seasons is None
            or self.teams is None
            or self.stadiums is None
            or self.ticket_prices is None
        ):
            raise RuntimeError("Schedule generation dependencies are not configured.")
        return (
            self.tournaments,
            self.seasons,
            self.teams,
            self.stadiums,
            self.ticket_prices,
        )

    def _validate_team_ids(self, team_ids: list[int]) -> list[int]:
        seen: set[int] = set()
        for team_id in team_ids:
            if team_id <= 0:
                raise BusinessRuleError("Team ids must be positive.")
            if team_id in seen:
                raise BusinessRuleError("Team ids must be unique.")
            seen.add(team_id)
        return team_ids

    def _get_teams_by_id(
        self,
        teams: TeamRepository,
        team_ids: list[int],
    ) -> dict[int, Team]:
        teams_by_id: dict[int, Team] = {}
        for team_id in team_ids:
            team = teams.get(team_id)
            if team is None:
                raise NotFoundError("Team not found.")
            teams_by_id[team_id] = team
        return teams_by_id

    def _resolve_stadiums_by_team_id(
        self,
        *,
        stadiums: StadiumRepository,
        team_ids: list[int],
        payload: ChampionshipScheduleGenerate,
    ) -> dict[int, Stadium]:
        team_id_set = set(team_ids)
        mapped_team_ids = set(payload.stadium_ids_by_team)
        if not mapped_team_ids.issubset(team_id_set):
            raise BusinessRuleError(
                "Stadium mapping can contain only teams from the generated schedule."
            )

        fallback_stadium = None
        if payload.fallback_stadium_id is not None:
            fallback_stadium = stadiums.get(payload.fallback_stadium_id)
            if fallback_stadium is None:
                raise NotFoundError("Stadium not found.")

        mapped_stadiums: dict[int, Stadium] = {}
        for team_id, stadium_id in payload.stadium_ids_by_team.items():
            stadium = stadiums.get(stadium_id)
            if stadium is None:
                raise NotFoundError("Stadium not found.")
            mapped_stadiums[team_id] = stadium

        stadiums_by_team_id: dict[int, Stadium] = {}
        for team_id in team_ids:
            stadium = (
                stadiums.get_home_stadium_for_team(team_id)
                or mapped_stadiums.get(team_id)
                or fallback_stadium
            )
            if stadium is None:
                raise BusinessRuleError(
                    "Each team needs a home stadium, team stadium mapping, "
                    "or fallback stadium."
                )
            stadiums_by_team_id[team_id] = stadium
        return stadiums_by_team_id

    def _build_double_round_robin_rounds(
        self,
        team_ids: list[int],
    ) -> list[list[tuple[int, int]]]:
        rotated_team_ids: list[int | None] = list(team_ids)
        if len(rotated_team_ids) % 2 != 0:
            rotated_team_ids.append(None)

        single_leg_rounds: list[list[tuple[int, int]]] = []
        round_count = len(rotated_team_ids) - 1
        for round_index in range(round_count):
            pairings: list[tuple[int, int]] = []
            for pair_index in range(len(rotated_team_ids) // 2):
                first_team_id = rotated_team_ids[pair_index]
                second_team_id = rotated_team_ids[-pair_index - 1]
                if first_team_id is None or second_team_id is None:
                    continue
                if round_index % 2 == 0:
                    pairings.append((first_team_id, second_team_id))
                else:
                    pairings.append((second_team_id, first_team_id))
            single_leg_rounds.append(pairings)
            rotated_team_ids = [
                rotated_team_ids[0],
                rotated_team_ids[-1],
                *rotated_team_ids[1:-1],
            ]

        second_leg_rounds = [
            [(away_team_id, home_team_id) for home_team_id, away_team_id in pairings]
            for pairings in single_leg_rounds
        ]
        return [*single_leg_rounds, *second_leg_rounds]

    def _get_round_datetime(
        self,
        *,
        start_datetime: datetime,
        round_index: int,
        interval_days: int,
        payload: ChampionshipScheduleGenerate,
    ) -> datetime:
        match_datetime = start_datetime + timedelta(days=round_index * interval_days)
        if payload.match_time is None:
            return match_datetime
        return match_datetime.replace(
            hour=payload.match_time.hour,
            minute=payload.match_time.minute,
            second=payload.match_time.second,
            microsecond=payload.match_time.microsecond,
        )
