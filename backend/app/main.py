from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.router import api_router
from app.core.config import settings

API_DESCRIPTION = (
    "Backend API for managing user-scoped football seasons, teams, players, "
    "stadiums, referees, tournaments, matches, lineups, protocols, standings, "
    "statistics, schedules, and cup brackets."
)

OPENAPI_TAGS = [
    {"name": "auth", "description": "Registration, login, and current user."},
    {"name": "users", "description": "Authenticated user profile operations."},
    {"name": "seasons", "description": "User-owned competition seasons."},
    {"name": "teams", "description": "User-owned football clubs."},
    {"name": "players", "description": "Players assigned to user-owned teams."},
    {"name": "stadiums", "description": "Venues and home stadium assignments."},
    {"name": "referees", "description": "Match officials."},
    {"name": "tournaments", "description": "Championship and cup tournaments."},
    {"name": "matches", "description": "Match CRUD and match actions."},
    {"name": "lineups", "description": "Manual and generated match lineups."},
    {"name": "match-protocol", "description": "Match events and finishing."},
    {"name": "random-results", "description": "Random realistic match results."},
    {"name": "cups", "description": "Cup semifinals, finals, and bracket views."},
    {"name": "schedule", "description": "Championship and venue schedules."},
    {"name": "standings", "description": "Championship standings."},
    {"name": "statistics", "description": "Player season stats and leaders."},
    {"name": "health", "description": "Service healthcheck."},
]


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.app_name,
        description=API_DESCRIPTION,
        version="0.1.0",
        debug=settings.debug,
        openapi_tags=OPENAPI_TAGS,
    )

    if settings.cors_origin_list:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=settings.cors_origin_list,
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

    @app.get("/health", tags=["health"])
    def health_check() -> dict[str, str]:
        return {"status": "ok", "service": settings.app_name}

    app.include_router(api_router, prefix=settings.api_v1_prefix)
    return app


app = create_app()
