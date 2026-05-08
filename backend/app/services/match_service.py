from datetime import datetime
from decimal import Decimal

from sqlalchemy.exc import IntegrityError

from app.core.constants import MatchStatus
from app.core.exceptions import BusinessRuleError, ConflictError, NotFoundError
from app.models.match import Match
from app.models.referee import Referee
from app.models.season import Season
from app.models.stadium import Stadium
from app.models.team import Team
from app.models.tournament import Tournament
from app.repositories.match import MatchRepository
from app.repositories.referee import RefereeRepository
from app.repositories.season import SeasonRepository
from app.repositories.stadium import StadiumRepository
from app.repositories.team import TeamRepository
from app.repositories.tournament import TournamentRepository
from app.schemas.match import MatchCreate, MatchUpdate
from app.services.schedule_service import ScheduleService
from app.services.ticket_price_service import TICKET_PRICE_QUANT, TicketPriceService
from app.services.validation_service import ValidationService


class MatchService:
    def __init__(
        self,
        matches: MatchRepository,
        tournaments: TournamentRepository,
        seasons: SeasonRepository,
        teams: TeamRepository,
        stadiums: StadiumRepository,
        referees: RefereeRepository,
        schedule: ScheduleService,
        ticket_prices: TicketPriceService,
        validation: ValidationService,
    ) -> None:
        self.matches = matches
        self.tournaments = tournaments
        self.seasons = seasons
        self.teams = teams
        self.stadiums = stadiums
        self.referees = referees
        self.schedule = schedule
        self.ticket_prices = ticket_prices
        self.validation = validation

    def list_matches(self, *, offset: int = 0, limit: int = 100) -> list[Match]:
        return self.matches.list(offset=offset, limit=limit)

    def get_match(self, match_id: int) -> Match:
        match = self.matches.get(match_id)
        if match is None:
            raise NotFoundError("Match not found.")
        return match

    def create_match(self, payload: MatchCreate) -> Match:
        if payload.home_team_id == payload.away_team_id:
            raise BusinessRuleError("Home and away teams must be different.")
        if payload.status == MatchStatus.FINISHED:
            raise BusinessRuleError("Match cannot be created with finished status.")

        tournament = self._get_tournament(payload.tournament_id)
        season = self._get_season(payload.season_id)
        self._ensure_match_belongs_to_tournament_season(
            tournament=tournament,
            season=season,
        )
        home_team = self._get_team(payload.home_team_id)
        away_team = self._get_team(payload.away_team_id)
        stadium = self._get_stadium(payload.stadium_id)
        if payload.referee_id is not None:
            self._get_referee(payload.referee_id)

        self._validate_calendar(
            home_team_id=home_team.id,
            away_team_id=away_team.id,
            match_datetime=payload.match_datetime,
        )
        if payload.referee_id is not None:
            self.validation.ensure_referee_is_available(
                referee_id=payload.referee_id,
                match_datetime=payload.match_datetime,
            )

        data = payload.model_dump()
        data["ticket_price"] = self.ticket_prices.calculate_default_price(
            stadium=stadium,
            home_team=home_team,
            away_team=away_team,
            previous_season_table_size=self.teams.get_previous_season_table_size(),
        )
        data["ticket_sold"] = 0
        data["income"] = Decimal("0.00")

        match = Match(**data)
        try:
            self.matches.add(match)
            self.matches.db.commit()
            self.matches.db.refresh(match)
        except IntegrityError as exc:
            self.matches.db.rollback()
            raise ConflictError(
                "Could not create match because of a conflict."
            ) from exc
        return match

    def update_match(self, match_id: int, payload: MatchUpdate) -> Match:
        match = self.get_match(match_id)
        data = payload.model_dump(exclude_unset=True)

        self._validate_required_update_fields(data)
        if "stadium_id" in data:
            self._get_stadium(data["stadium_id"])
        if data.get("referee_id") is not None:
            self._get_referee(data["referee_id"])

        effective_match_datetime = data.get("match_datetime", match.match_datetime)
        effective_referee_id = data.get("referee_id", match.referee_id)
        if "match_datetime" in data:
            self._validate_calendar(
                home_team_id=match.home_team_id,
                away_team_id=match.away_team_id,
                match_datetime=effective_match_datetime,
                exclude_match_id=match.id,
            )
        if ("match_datetime" in data or "referee_id" in data) and (
            effective_referee_id is not None
        ):
            self.validation.ensure_referee_is_available(
                referee_id=effective_referee_id,
                match_datetime=effective_match_datetime,
                exclude_match_id=match.id,
            )

        for field, value in data.items():
            setattr(match, field, value)
        self._sync_income(match)

        return self._commit_match(
            match, "Could not update match because of a conflict."
        )

    def delete_match(self, match_id: int) -> None:
        match = self.get_match(match_id)
        self.matches.delete(match)
        self.matches.db.commit()

    def assign_referee(self, match_id: int, referee_id: int) -> Match:
        match = self.get_match(match_id)
        self._get_referee(referee_id)
        self.validation.ensure_referee_is_available(
            referee_id=referee_id,
            match_datetime=match.match_datetime,
            exclude_match_id=match.id,
        )
        match.referee_id = referee_id
        return self._commit_match(match, "Could not assign referee to match.")

    def reschedule_match(self, match_id: int, match_datetime: datetime) -> Match:
        match = self.get_match(match_id)
        self._validate_calendar(
            home_team_id=match.home_team_id,
            away_team_id=match.away_team_id,
            match_datetime=match_datetime,
            exclude_match_id=match.id,
        )
        if match.referee_id is not None:
            self.validation.ensure_referee_is_available(
                referee_id=match.referee_id,
                match_datetime=match_datetime,
                exclude_match_id=match.id,
            )
        match.match_datetime = match_datetime
        return self._commit_match(match, "Could not reschedule match.")

    def set_manual_ticket_price(self, match_id: int, ticket_price: Decimal) -> Match:
        match = self.get_match(match_id)
        match.ticket_price = ticket_price.quantize(TICKET_PRICE_QUANT)
        self._sync_income(match)
        return self._commit_match(match, "Could not update match ticket price.")

    def _get_tournament(self, tournament_id: int) -> Tournament:
        tournament = self.tournaments.get(tournament_id)
        if tournament is None:
            raise NotFoundError("Tournament not found.")
        return tournament

    def _get_season(self, season_id: int) -> Season:
        season = self.seasons.get(season_id)
        if season is None:
            raise NotFoundError("Season not found.")
        return season

    def _get_team(self, team_id: int) -> Team:
        team = self.teams.get(team_id)
        if team is None:
            raise NotFoundError("Team not found.")
        return team

    def _get_stadium(self, stadium_id: int) -> Stadium:
        stadium = self.stadiums.get(stadium_id)
        if stadium is None:
            raise NotFoundError("Stadium not found.")
        return stadium

    def _get_referee(self, referee_id: int) -> Referee:
        referee = self.referees.get(referee_id)
        if referee is None:
            raise NotFoundError("Referee not found.")
        return referee

    def _ensure_match_belongs_to_tournament_season(
        self,
        *,
        tournament: Tournament,
        season: Season,
    ) -> None:
        if tournament.season_id != season.id:
            raise BusinessRuleError("Match season must match tournament season.")

    def _validate_calendar(
        self,
        *,
        home_team_id: int,
        away_team_id: int,
        match_datetime: datetime,
        exclude_match_id: int | None = None,
    ) -> None:
        self.schedule.validate_teams_can_play_at(
            home_team_id=home_team_id,
            away_team_id=away_team_id,
            match_datetime=match_datetime,
            exclude_match_id=exclude_match_id,
        )

    def _validate_required_update_fields(self, data: dict[str, object]) -> None:
        for field in ("stadium_id", "match_datetime", "status", "round_number"):
            if field in data and data[field] is None:
                raise BusinessRuleError(f"{field} cannot be null.")
        for field in ("ticket_price", "ticket_sold"):
            if field in data and data[field] is None:
                raise BusinessRuleError(f"{field} cannot be null.")

    def _sync_income(self, match: Match) -> None:
        if match.ticket_price is None:
            match.income = None
            return
        match.income = (match.ticket_price * match.ticket_sold).quantize(
            TICKET_PRICE_QUANT
        )

    def _commit_match(self, match: Match, conflict_message: str) -> Match:
        try:
            self.matches.db.commit()
            self.matches.db.refresh(match)
        except IntegrityError as exc:
            self.matches.db.rollback()
            raise ConflictError(conflict_message) from exc
        return match
