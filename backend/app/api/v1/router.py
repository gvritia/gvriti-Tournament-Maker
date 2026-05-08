from fastapi import APIRouter

from app.api.v1.endpoints import (
    auth,
    lineups,
    matches,
    players,
    protocol,
    referees,
    schedule,
    seasons,
    stadiums,
    standings,
    statistics,
    teams,
    tournaments,
    users,
)

api_router = APIRouter()
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(seasons.router, prefix="/seasons", tags=["seasons"])
api_router.include_router(teams.router, prefix="/teams", tags=["teams"])
api_router.include_router(players.router, prefix="/players", tags=["players"])
api_router.include_router(stadiums.router, prefix="/stadiums", tags=["stadiums"])
api_router.include_router(referees.router, prefix="/referees", tags=["referees"])
api_router.include_router(
    tournaments.router, prefix="/tournaments", tags=["tournaments"]
)
api_router.include_router(matches.router, prefix="/matches", tags=["matches"])
api_router.include_router(lineups.router, tags=["lineups"])
api_router.include_router(protocol.router, tags=["match-protocol"])
api_router.include_router(schedule.router, prefix="/schedule", tags=["schedule"])
api_router.include_router(standings.router, prefix="/standings", tags=["standings"])
api_router.include_router(statistics.router, prefix="/statistics", tags=["statistics"])
