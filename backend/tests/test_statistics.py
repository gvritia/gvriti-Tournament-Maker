from typing import Any

import pytest
from fastapi.testclient import TestClient


def auth_headers(client: TestClient) -> dict[str, str]:
    client.post(
        "/api/v1/auth/register",
        json={
            "nickname": "stats-organizer",
            "email": "stats-organizer@example.com",
            "password": "StrongPass123",
        },
    )
    response = client.post(
        "/api/v1/auth/login",
        json={
            "email": "stats-organizer@example.com",
            "password": "StrongPass123",
        },
    )
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def create_season(client: TestClient, headers: dict[str, str]) -> int:
    response = client.post(
        "/api/v1/seasons/",
        json={
            "name": "2026",
            "start_date": "2026-03-01",
            "end_date": "2026-11-30",
        },
        headers=headers,
    )
    assert response.status_code == 201
    return int(response.json()["id"])


def create_tournament(
    client: TestClient,
    headers: dict[str, str],
    season_id: int,
) -> int:
    response = client.post(
        "/api/v1/tournaments/",
        json={
            "season_id": season_id,
            "name": "Premier League",
            "type": "championship",
        },
        headers=headers,
    )
    assert response.status_code == 201
    return int(response.json()["id"])


def create_team(client: TestClient, headers: dict[str, str], name: str) -> int:
    response = client.post(
        "/api/v1/teams/",
        json={"name": name, "city": "Moscow"},
        headers=headers,
    )
    assert response.status_code == 201
    return int(response.json()["id"])


def create_player(
    client: TestClient,
    headers: dict[str, str],
    *,
    team_id: int,
    full_name: str,
    number: int,
) -> int:
    response = client.post(
        "/api/v1/players/",
        json={
            "full_name": full_name,
            "position": "forward",
            "number": number,
            "team_id": team_id,
        },
        headers=headers,
    )
    assert response.status_code == 201
    return int(response.json()["id"])


def create_stadium(client: TestClient, headers: dict[str, str]) -> int:
    response = client.post(
        "/api/v1/stadiums/",
        json={
            "name": "National Arena",
            "city": "Moscow",
            "address": "Main street 1",
            "capacity": 50000,
        },
        headers=headers,
    )
    assert response.status_code == 201
    return int(response.json()["id"])


def create_match(
    client: TestClient,
    headers: dict[str, str],
    *,
    tournament_id: int,
    season_id: int,
    home_team_id: int,
    away_team_id: int,
    stadium_id: int,
    match_datetime: str,
) -> dict[str, Any]:
    response = client.post(
        "/api/v1/matches/",
        json={
            "tournament_id": tournament_id,
            "season_id": season_id,
            "home_team_id": home_team_id,
            "away_team_id": away_team_id,
            "stadium_id": stadium_id,
            "match_datetime": match_datetime,
            "round_number": 1,
        },
        headers=headers,
    )
    assert response.status_code == 201
    return response.json()


def add_event(
    client: TestClient,
    headers: dict[str, str],
    *,
    match_id: int,
    team_id: int,
    player_id: int,
    event_type: str,
    minute: int,
    assist_player_id: int | None = None,
) -> None:
    response = client.post(
        f"/api/v1/matches/{match_id}/events",
        json={
            "team_id": team_id,
            "player_id": player_id,
            "assist_player_id": assist_player_id,
            "event_type": event_type,
            "minute": minute,
        },
        headers=headers,
    )
    assert response.status_code == 201


def finish_match(
    client: TestClient,
    headers: dict[str, str],
    *,
    match_id: int,
    home_score: int,
    away_score: int,
) -> None:
    response = client.post(
        f"/api/v1/matches/{match_id}/finish",
        json={"home_score": home_score, "away_score": away_score},
        headers=headers,
    )
    assert response.status_code == 200


def setup_statistics_context(
    client: TestClient,
    headers: dict[str, str],
) -> dict[str, Any]:
    season_id = create_season(client, headers)
    tournament_id = create_tournament(client, headers, season_id)
    stadium_id = create_stadium(client, headers)
    home_team_id = create_team(client, headers, "Home Team")
    away_team_id = create_team(client, headers, "Away Team")
    scorer_id = create_player(
        client,
        headers,
        team_id=home_team_id,
        full_name="Scorer",
        number=9,
    )
    assistant_id = create_player(
        client,
        headers,
        team_id=home_team_id,
        full_name="Assistant",
        number=10,
    )
    goalkeeper_id = create_player(
        client,
        headers,
        team_id=away_team_id,
        full_name="Goalkeeper",
        number=1,
    )
    defender_id = create_player(
        client,
        headers,
        team_id=away_team_id,
        full_name="Defender",
        number=5,
    )
    return {
        "season_id": season_id,
        "tournament_id": tournament_id,
        "stadium_id": stadium_id,
        "home_team_id": home_team_id,
        "away_team_id": away_team_id,
        "scorer_id": scorer_id,
        "assistant_id": assistant_id,
        "goalkeeper_id": goalkeeper_id,
        "defender_id": defender_id,
    }


def test_recalculate_player_stats_and_leaderboards(client: TestClient) -> None:
    headers = auth_headers(client)
    context = setup_statistics_context(client, headers)
    match = create_match(
        client,
        headers,
        tournament_id=context["tournament_id"],
        season_id=context["season_id"],
        home_team_id=context["home_team_id"],
        away_team_id=context["away_team_id"],
        stadium_id=context["stadium_id"],
        match_datetime="2026-04-01T18:00:00",
    )

    add_event(
        client,
        headers,
        match_id=match["id"],
        team_id=context["home_team_id"],
        player_id=context["scorer_id"],
        assist_player_id=context["assistant_id"],
        event_type="goal",
        minute=10,
    )
    add_event(
        client,
        headers,
        match_id=match["id"],
        team_id=context["home_team_id"],
        player_id=context["assistant_id"],
        event_type="assist",
        minute=11,
    )
    add_event(
        client,
        headers,
        match_id=match["id"],
        team_id=context["away_team_id"],
        player_id=context["goalkeeper_id"],
        event_type="save",
        minute=20,
    )
    add_event(
        client,
        headers,
        match_id=match["id"],
        team_id=context["away_team_id"],
        player_id=context["defender_id"],
        event_type="yellow_card",
        minute=30,
    )
    add_event(
        client,
        headers,
        match_id=match["id"],
        team_id=context["away_team_id"],
        player_id=context["defender_id"],
        event_type="red_card",
        minute=80,
    )
    finish_match(client, headers, match_id=match["id"], home_score=1, away_score=0)

    unfinished_match = create_match(
        client,
        headers,
        tournament_id=context["tournament_id"],
        season_id=context["season_id"],
        home_team_id=context["home_team_id"],
        away_team_id=context["away_team_id"],
        stadium_id=context["stadium_id"],
        match_datetime="2026-04-08T18:00:00",
    )
    add_event(
        client,
        headers,
        match_id=unfinished_match["id"],
        team_id=context["home_team_id"],
        player_id=context["scorer_id"],
        event_type="goal",
        minute=10,
    )

    recalculate_response = client.post(
        f"/api/v1/statistics/seasons/{context['season_id']}/players/recalculate",
        headers=headers,
    )
    list_response = client.get(
        f"/api/v1/statistics/seasons/{context['season_id']}/players",
        headers=headers,
    )
    goal_leaders_response = client.get(
        f"/api/v1/statistics/seasons/{context['season_id']}/leaders/goals",
        headers=headers,
    )
    assist_leaders_response = client.get(
        f"/api/v1/statistics/seasons/{context['season_id']}/leaders/assists",
        params={"limit": 1},
        headers=headers,
    )

    assert recalculate_response.status_code == 200
    assert list_response.status_code == 200
    stats_by_player = {row["player_id"]: row for row in list_response.json()}

    assert stats_by_player[context["scorer_id"]]["goals"] == 1
    assert stats_by_player[context["assistant_id"]]["assists"] == 2
    assert stats_by_player[context["goalkeeper_id"]]["saves"] == 1
    assert stats_by_player[context["defender_id"]]["yellow_cards"] == 1
    assert stats_by_player[context["defender_id"]]["red_cards"] == 1

    assert goal_leaders_response.status_code == 200
    assert goal_leaders_response.json()[0]["player_id"] == context["scorer_id"]
    assert assist_leaders_response.status_code == 200
    assert assist_leaders_response.json() == [stats_by_player[context["assistant_id"]]]


def test_recalculate_player_stats_is_idempotent(client: TestClient) -> None:
    headers = auth_headers(client)
    context = setup_statistics_context(client, headers)
    match = create_match(
        client,
        headers,
        tournament_id=context["tournament_id"],
        season_id=context["season_id"],
        home_team_id=context["home_team_id"],
        away_team_id=context["away_team_id"],
        stadium_id=context["stadium_id"],
        match_datetime="2026-04-01T18:00:00",
    )
    add_event(
        client,
        headers,
        match_id=match["id"],
        team_id=context["home_team_id"],
        player_id=context["scorer_id"],
        event_type="goal",
        minute=10,
    )
    finish_match(client, headers, match_id=match["id"], home_score=1, away_score=0)

    first_response = client.post(
        f"/api/v1/statistics/seasons/{context['season_id']}/players/recalculate",
        headers=headers,
    )
    second_response = client.post(
        f"/api/v1/statistics/seasons/{context['season_id']}/players/recalculate",
        headers=headers,
    )

    assert first_response.status_code == 200
    assert second_response.status_code == 200
    assert first_response.json() == second_response.json()


def test_player_leaderboard_rejects_unsupported_metric(client: TestClient) -> None:
    headers = auth_headers(client)
    context = setup_statistics_context(client, headers)

    response = client.get(
        f"/api/v1/statistics/seasons/{context['season_id']}/leaders/unknown",
        headers=headers,
    )

    assert response.status_code == 400


@pytest.mark.parametrize(
    ("method", "path"),
    [
        ("GET", "/api/v1/statistics/seasons/999/players"),
        ("POST", "/api/v1/statistics/seasons/999/players/recalculate"),
        ("GET", "/api/v1/statistics/seasons/999/leaders/goals"),
    ],
)
def test_statistics_returns_404_for_missing_season(
    client: TestClient,
    method: str,
    path: str,
) -> None:
    headers = auth_headers(client)

    response = client.request(method, path, headers=headers)

    assert response.status_code == 404


@pytest.mark.parametrize(
    ("method", "path"),
    [
        ("GET", "/api/v1/statistics/seasons/1/players"),
        ("POST", "/api/v1/statistics/seasons/1/players/recalculate"),
        ("GET", "/api/v1/statistics/seasons/1/leaders/goals"),
    ],
)
def test_statistics_endpoints_require_jwt(
    client: TestClient,
    method: str,
    path: str,
) -> None:
    response = client.request(method, path)

    assert response.status_code == 401
    assert response.headers["WWW-Authenticate"] == "Bearer"
