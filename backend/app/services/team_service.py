from sqlalchemy.exc import IntegrityError

from app.core.exceptions import ConflictError, NotFoundError
from app.models.team import Team
from app.repositories.team import TeamRepository
from app.schemas.team import TeamCreate, TeamUpdate


class TeamService:
    def __init__(self, teams: TeamRepository) -> None:
        self.teams = teams

    def list_teams(self, *, offset: int = 0, limit: int = 100) -> list[Team]:
        return self.teams.list(offset=offset, limit=limit)

    def get_team(self, team_id: int) -> Team:
        team = self.teams.get(team_id)
        if team is None:
            raise NotFoundError("Team not found.")
        return team

    def create_team(self, payload: TeamCreate) -> Team:
        if self.teams.get_by_name(payload.name) is not None:
            raise ConflictError("A team with this name already exists.")

        team = Team(**payload.model_dump())
        try:
            self.teams.add(team)
            self.teams.db.commit()
            self.teams.db.refresh(team)
        except IntegrityError as exc:
            self.teams.db.rollback()
            raise ConflictError("A team with this name already exists.") from exc
        return team

    def update_team(self, team_id: int, payload: TeamUpdate) -> Team:
        team = self.get_team(team_id)
        data = payload.model_dump(exclude_unset=True)

        new_name = data.get("name")
        if new_name is not None:
            existing = self.teams.get_by_name(new_name)
            if existing is not None and existing.id != team_id:
                raise ConflictError("A team with this name already exists.")

        for field, value in data.items():
            setattr(team, field, value)

        try:
            self.teams.db.commit()
            self.teams.db.refresh(team)
        except IntegrityError as exc:
            self.teams.db.rollback()
            raise ConflictError("A team with this name already exists.") from exc
        return team

    def delete_team(self, team_id: int) -> None:
        team = self.get_team(team_id)
        self.teams.delete(team)
        self.teams.db.commit()
