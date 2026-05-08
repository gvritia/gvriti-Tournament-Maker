from decimal import Decimal

from sqlalchemy.exc import IntegrityError

from app.core.constants import CupStage, MatchStatus, TournamentType
from app.core.exceptions import BusinessRuleError, ConflictError, NotFoundError
from app.models.match import Match
from app.models.stadium import Stadium
from app.models.team import Team
from app.models.tournament import Tournament
from app.repositories.match import MatchRepository
from app.repositories.stadium import StadiumRepository
from app.repositories.team import TeamRepository
from app.repositories.tournament import TournamentRepository
from app.schemas.cup import (
    CupBracketRead,
    CupFinalGenerate,
    CupMatchNode,
    CupSemifinalsGenerate,
)
from app.schemas.match import MatchRead
from app.services.schedule_service import ScheduleService
from app.services.ticket_price_service import TicketPriceService


class CupService:
    def __init__(
        self,
        matches: MatchRepository,
        tournaments: TournamentRepository,
        teams: TeamRepository,
        stadiums: StadiumRepository,
        schedule: ScheduleService,
        ticket_prices: TicketPriceService,
    ) -> None:
        self.matches = matches
        self.tournaments = tournaments
        self.teams = teams
        self.stadiums = stadiums
        self.schedule = schedule
        self.ticket_prices = ticket_prices

    def generate_semifinals(
        self,
        *,
        tournament_id: int,
        payload: CupSemifinalsGenerate,
    ) -> list[Match]:
        tournament = self._get_cup_tournament(tournament_id)
        self._ensure_no_stage_matches(
            tournament_id=tournament.id,
            stage=CupStage.SEMIFINAL,
            message="Cup semifinals already exist.",
        )
        team_ids = self._validate_team_ids(payload.team_ids)
        teams_by_id = self._get_teams_by_id(team_ids)
        stadiums_by_team_id = self._resolve_stadiums_by_team_id(
            team_ids=team_ids,
            fallback_stadium_id=payload.fallback_stadium_id,
            stadium_ids_by_team=payload.stadium_ids_by_team,
        )
        pairings = [
            (team_ids[0], team_ids[3], payload.match_datetimes[0]),
            (team_ids[1], team_ids[2], payload.match_datetimes[1]),
        ]
        previous_season_table_size = self.teams.get_previous_season_table_size()

        created_matches: list[Match] = []
        try:
            for home_team_id, away_team_id, match_datetime in pairings:
                self.schedule.validate_teams_can_play_at(
                    home_team_id=home_team_id,
                    away_team_id=away_team_id,
                    match_datetime=match_datetime,
                )
                match = self._build_match(
                    tournament=tournament,
                    home_team=teams_by_id[home_team_id],
                    away_team=teams_by_id[away_team_id],
                    stadium=stadiums_by_team_id[home_team_id],
                    match_datetime=match_datetime,
                    round_number=1,
                    stage=CupStage.SEMIFINAL,
                    previous_season_table_size=previous_season_table_size,
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
                "Could not generate cup semifinals because of a conflict."
            ) from exc
        return created_matches

    def generate_final(
        self,
        *,
        tournament_id: int,
        payload: CupFinalGenerate,
    ) -> Match:
        tournament = self._get_cup_tournament(tournament_id)
        self._ensure_no_stage_matches(
            tournament_id=tournament.id,
            stage=CupStage.FINAL,
            message="Cup final already exists.",
        )
        stadium = self._get_stadium(payload.stadium_id)
        semifinals = self.matches.list_by_tournament_and_stage(
            tournament_id=tournament.id,
            stage=CupStage.SEMIFINAL,
        )
        if len(semifinals) != 2:
            raise BusinessRuleError("Cup final requires exactly two semifinals.")

        winner_team_ids = [
            self._get_match_winner_team_id(match) for match in semifinals
        ]
        home_team = self._get_team(winner_team_ids[0])
        away_team = self._get_team(winner_team_ids[1])
        previous_season_table_size = self.teams.get_previous_season_table_size()

        try:
            self.schedule.validate_teams_can_play_at(
                home_team_id=home_team.id,
                away_team_id=away_team.id,
                match_datetime=payload.match_datetime,
            )
            match = self._build_match(
                tournament=tournament,
                home_team=home_team,
                away_team=away_team,
                stadium=stadium,
                match_datetime=payload.match_datetime,
                round_number=2,
                stage=CupStage.FINAL,
                previous_season_table_size=previous_season_table_size,
            )
            self.matches.add(match)
            self.matches.db.commit()
            self.matches.db.refresh(match)
        except (BusinessRuleError, ConflictError, NotFoundError):
            self.matches.db.rollback()
            raise
        except IntegrityError as exc:
            self.matches.db.rollback()
            raise ConflictError(
                "Could not generate cup final because of a conflict."
            ) from exc
        return match

    def get_bracket(self, tournament_id: int) -> CupBracketRead:
        tournament = self._get_cup_tournament(tournament_id)
        semifinals = self.matches.list_by_tournament_and_stage(
            tournament_id=tournament.id,
            stage=CupStage.SEMIFINAL,
        )
        finals = self.matches.list_by_tournament_and_stage(
            tournament_id=tournament.id,
            stage=CupStage.FINAL,
        )
        final_match = finals[0] if finals else None
        return CupBracketRead(
            tournament_id=tournament.id,
            season_id=tournament.season_id,
            semifinals=[self._to_match_node(match) for match in semifinals],
            final=self._to_match_node(final_match) if final_match is not None else None,
            champion_team_id=(
                self._get_finished_match_winner_team_id(final_match)
                if final_match is not None
                else None
            ),
        )

    def _build_match(
        self,
        *,
        tournament: Tournament,
        home_team: Team,
        away_team: Team,
        stadium: Stadium,
        match_datetime,
        round_number: int,
        stage: CupStage,
        previous_season_table_size: int | None,
    ) -> Match:
        return Match(
            tournament_id=tournament.id,
            season_id=tournament.season_id,
            home_team_id=home_team.id,
            away_team_id=away_team.id,
            stadium_id=stadium.id,
            referee_id=None,
            match_datetime=match_datetime,
            status=MatchStatus.SCHEDULED,
            round_number=round_number,
            stage=stage,
            ticket_price=self.ticket_prices.calculate_default_price(
                stadium=stadium,
                home_team=home_team,
                away_team=away_team,
                previous_season_table_size=previous_season_table_size,
            ),
            ticket_sold=0,
            income=Decimal("0.00"),
        )

    def _get_cup_tournament(self, tournament_id: int) -> Tournament:
        tournament = self.tournaments.get(tournament_id)
        if tournament is None:
            raise NotFoundError("Tournament not found.")
        if tournament.type != TournamentType.CUP:
            raise BusinessRuleError(
                "Cup bracket can be managed only for cup tournaments."
            )
        return tournament

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

    def _validate_team_ids(self, team_ids: list[int]) -> list[int]:
        seen: set[int] = set()
        for team_id in team_ids:
            if team_id <= 0:
                raise BusinessRuleError("Team ids must be positive.")
            if team_id in seen:
                raise BusinessRuleError("Cup semifinals require four unique teams.")
            seen.add(team_id)
        return team_ids

    def _get_teams_by_id(self, team_ids: list[int]) -> dict[int, Team]:
        return {team_id: self._get_team(team_id) for team_id in team_ids}

    def _resolve_stadiums_by_team_id(
        self,
        *,
        team_ids: list[int],
        fallback_stadium_id: int | None,
        stadium_ids_by_team: dict[int, int],
    ) -> dict[int, Stadium]:
        team_id_set = set(team_ids)
        mapped_team_ids = set(stadium_ids_by_team)
        if not mapped_team_ids.issubset(team_id_set):
            raise BusinessRuleError(
                "Stadium mapping can contain only teams from the cup semifinals."
            )

        fallback_stadium = None
        if fallback_stadium_id is not None:
            fallback_stadium = self._get_stadium(fallback_stadium_id)

        mapped_stadiums = {
            team_id: self._get_stadium(stadium_id)
            for team_id, stadium_id in stadium_ids_by_team.items()
        }
        stadiums_by_team_id: dict[int, Stadium] = {}
        for team_id in team_ids:
            stadium = (
                self.stadiums.get_home_stadium_for_team(team_id)
                or mapped_stadiums.get(team_id)
                or fallback_stadium
            )
            if stadium is None:
                raise BusinessRuleError(
                    "Each cup semifinal home team needs a home stadium, team "
                    "stadium mapping, or fallback stadium."
                )
            stadiums_by_team_id[team_id] = stadium
        return stadiums_by_team_id

    def _ensure_no_stage_matches(
        self,
        *,
        tournament_id: int,
        stage: CupStage,
        message: str,
    ) -> None:
        if self.matches.list_by_tournament_and_stage(
            tournament_id=tournament_id,
            stage=stage,
        ):
            raise ConflictError(message)

    def _get_match_winner_team_id(self, match: Match) -> int:
        winner_team_id = self._get_finished_match_winner_team_id(match)
        if winner_team_id is None:
            raise BusinessRuleError(
                "Cup match winner cannot be determined from an unfinished or "
                "drawn match."
            )
        return winner_team_id

    def _get_finished_match_winner_team_id(self, match: Match) -> int | None:
        if (
            match.status != MatchStatus.FINISHED
            or match.home_score is None
            or match.away_score is None
            or match.home_score == match.away_score
        ):
            return None
        if match.home_score > match.away_score:
            return match.home_team_id
        return match.away_team_id

    def _to_match_node(self, match: Match) -> CupMatchNode:
        return CupMatchNode(
            match=MatchRead.model_validate(match),
            winner_team_id=self._get_finished_match_winner_team_id(match),
        )
