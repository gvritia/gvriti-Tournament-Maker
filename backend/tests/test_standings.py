from typing import Any

import pytest
from fastapi.testclient import TestClient


def auth_headers(client: TestClient) -> dict[str, str]:
    client.post(
        "/api/v1/auth/register",
        json={
            "nickname": "standings-organizer",
            "email": "standings-organizer@example.com",
            "password": "StrongPass123",
        },
    )
    response = client.post(
        "/api/v1/auth/login",
        json={
            "email": "standings-organizer@example.com",
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
    *,
    name: str,
    tournament_type: str,
) -> int:
    response = client.post(
        "/api/v1/tournaments/",
        json={
            "season_id": season_id,
            "name": name,
            "type": tournament_type,
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


def add_goal(
    client: TestClient,
    headers: dict[str, str],
    *,
    match_id: int,
    team_id: int,
    player_id: int,
    minute: int,
) -> None:
    response = client.post(
        f"/api/v1/matches/{match_id}/events",
        json={
            "team_id": team_id,
            "player_id": player_id,
            "event_type": "goal",
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


def setup_standings_context(
    client: TestClient,
    headers: dict[str, str],
) -> dict[str, Any]:
    season_id = create_season(client, headers)
    championship_id = create_tournament(
        client,
        headers,
        season_id,
        name="Premier League",
        tournament_type="championship",
    )
    cup_id = create_tournament(
        client,
        headers,
        season_id,
        name="National Cup",
        tournament_type="cup",
    )
    stadium_id = create_stadium(client, headers)
    team_a_id = create_team(client, headers, "Team A")
    team_b_id = create_team(client, headers, "Team B")
    team_c_id = create_team(client, headers, "Team C")
    player_a_id = create_player(
        client,
        headers,
        team_id=team_a_id,
        full_name="Team A Forward",
        number=9,
    )
    player_b_id = create_player(
        client,
        headers,
        team_id=team_b_id,
        full_name="Team B Forward",
        number=9,
    )
    player_c_id = create_player(
        client,
        headers,
        team_id=team_c_id,
        full_name="Team C Forward",
        number=9,
    )
    return {
        "season_id": season_id,
        "championship_id": championship_id,
        "cup_id": cup_id,
        "stadium_id": stadium_id,
        "team_a_id": team_a_id,
        "team_b_id": team_b_id,
        "team_c_id": team_c_id,
        "player_a_id": player_a_id,
        "player_b_id": player_b_id,
        "player_c_id": player_c_id,
    }


def test_recalculate_and_get_standings_from_finished_championship_matches(
    client: TestClient,
) -> None:
    headers = auth_headers(client)
    context = setup_standings_context(client, headers)

    match_a_b = create_match(
        client,
        headers,
        tournament_id=context["championship_id"],
        season_id=context["season_id"],
        home_team_id=context["team_a_id"],
        away_team_id=context["team_b_id"],
        stadium_id=context["stadium_id"],
        match_datetime="2026-04-01T18:00:00",
    )
    add_goal(
        client,
        headers,
        match_id=match_a_b["id"],
        team_id=context["team_a_id"],
        player_id=context["player_a_id"],
        minute=10,
    )
    add_goal(
        client,
        headers,
        match_id=match_a_b["id"],
        team_id=context["team_a_id"],
        player_id=context["player_a_id"],
        minute=20,
    )
    finish_match(client, headers, match_id=match_a_b["id"], home_score=2, away_score=0)

    match_a_c = create_match(
        client,
        headers,
        tournament_id=context["championship_id"],
        season_id=context["season_id"],
        home_team_id=context["team_a_id"],
        away_team_id=context["team_c_id"],
        stadium_id=context["stadium_id"],
        match_datetime="2026-04-08T18:00:00",
    )
    add_goal(
        client,
        headers,
        match_id=match_a_c["id"],
        team_id=context["team_a_id"],
        player_id=context["player_a_id"],
        minute=15,
    )
    add_goal(
        client,
        headers,
        match_id=match_a_c["id"],
        team_id=context["team_c_id"],
        player_id=context["player_c_id"],
        minute=70,
    )
    finish_match(client, headers, match_id=match_a_c["id"], home_score=1, away_score=1)

    create_match(
        client,
        headers,
        tournament_id=context["championship_id"],
        season_id=context["season_id"],
        home_team_id=context["team_b_id"],
        away_team_id=context["team_c_id"],
        stadium_id=context["stadium_id"],
        match_datetime="2026-04-15T18:00:00",
    )

    cup_match = create_match(
        client,
        headers,
        tournament_id=context["cup_id"],
        season_id=context["season_id"],
        home_team_id=context["team_a_id"],
        away_team_id=context["team_b_id"],
        stadium_id=context["stadium_id"],
        match_datetime="2026-04-22T18:00:00",
    )
    for minute in (5, 15, 25, 35, 45):
        add_goal(
            client,
            headers,
            match_id=cup_match["id"],
            team_id=context["team_b_id"],
            player_id=context["player_b_id"],
            minute=minute,
        )
    finish_match(client, headers, match_id=cup_match["id"], home_score=0, away_score=5)

    recalculate_response = client.post(
        f"/api/v1/standings/seasons/{context['season_id']}/recalculate",
        headers=headers,
    )
    get_response = client.get(
        f"/api/v1/standings/seasons/{context['season_id']}",
        headers=headers,
    )

    assert recalculate_response.status_code == 200
    assert get_response.status_code == 200
    standings = get_response.json()
    assert [row["team_id"] for row in standings] == [
        context["team_a_id"],
        context["team_c_id"],
        context["team_b_id"],
    ]

    team_a, team_c, team_b = standings
    assert team_a["played"] == 2
    assert team_a["wins"] == 1
    assert team_a["draws"] == 1
    assert team_a["points"] == 4
    assert team_a["goals_scored"] == 3
    assert team_a["goals_conceded"] == 1
    assert team_a["goal_difference"] == 2
    assert team_a["place"] == 1

    assert team_c["played"] == 1
    assert team_c["draws"] == 1
    assert team_c["points"] == 1
    assert team_c["place"] == 2

    assert team_b["played"] == 1
    assert team_b["losses"] == 1
    assert team_b["points"] == 0
    assert team_b["goals_scored"] == 0
    assert team_b["goals_conceded"] == 2
    assert team_b["place"] == 3


def test_recalculate_standings_is_idempotent(client: TestClient) -> None:
    headers = auth_headers(client)
    context = setup_standings_context(client, headers)
    create_match(
        client,
        headers,
        tournament_id=context["championship_id"],
        season_id=context["season_id"],
        home_team_id=context["team_a_id"],
        away_team_id=context["team_b_id"],
        stadium_id=context["stadium_id"],
        match_datetime="2026-04-01T18:00:00",
    )

    first_response = client.post(
        f"/api/v1/standings/seasons/{context['season_id']}/recalculate",
        headers=headers,
    )
    second_response = client.post(
        f"/api/v1/standings/seasons/{context['season_id']}/recalculate",
        headers=headers,
    )

    assert first_response.status_code == 200
    assert second_response.status_code == 200
    assert len(first_response.json()) == 2
    assert len(second_response.json()) == 2


@pytest.mark.parametrize(
    ("method", "path"),
    [
        ("GET", "/api/v1/standings/seasons/999"),
        ("POST", "/api/v1/standings/seasons/999/recalculate"),
    ],
)
def test_standings_returns_404_for_missing_season(
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
        ("GET", "/api/v1/standings/seasons/1"),
        ("POST", "/api/v1/standings/seasons/1/recalculate"),
    ],
)
def test_standings_endpoints_require_jwt(
    client: TestClient,
    method: str,
    path: str,
) -> None:
    response = client.request(method, path)

    assert response.status_code == 401
    assert response.headers["WWW-Authenticate"] == "Bearer"
