from collections import Counter
from typing import Any

import pytest
from fastapi.testclient import TestClient


def auth_headers(client: TestClient) -> dict[str, str]:
    client.post(
        "/api/v1/auth/register",
        json={
            "nickname": "random-organizer",
            "email": "random-organizer@example.com",
            "password": "StrongPass123",
        },
    )
    response = client.post(
        "/api/v1/auth/login",
        json={
            "email": "random-organizer@example.com",
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
    tournament_type: str = "championship",
) -> int:
    response = client.post(
        "/api/v1/tournaments/",
        json={
            "season_id": season_id,
            "name": f"{tournament_type.title()} Tournament",
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
    position: str,
) -> int:
    response = client.post(
        "/api/v1/players/",
        json={
            "full_name": full_name,
            "position": position,
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
    stage: str | None = None,
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "tournament_id": tournament_id,
        "season_id": season_id,
        "home_team_id": home_team_id,
        "away_team_id": away_team_id,
        "stadium_id": stadium_id,
        "match_datetime": "2026-04-01T18:00:00",
        "round_number": 1,
    }
    if stage is not None:
        payload["stage"] = stage
    response = client.post("/api/v1/matches/", json=payload, headers=headers)
    assert response.status_code == 201
    return response.json()


def setup_random_result_context(
    client: TestClient,
    headers: dict[str, str],
    *,
    tournament_type: str = "championship",
    stage: str | None = None,
    with_players: bool = True,
) -> dict[str, Any]:
    season_id = create_season(client, headers)
    tournament_id = create_tournament(
        client,
        headers,
        season_id,
        tournament_type=tournament_type,
    )
    stadium_id = create_stadium(client, headers)
    home_team_id = create_team(client, headers, "Home Team")
    away_team_id = create_team(client, headers, "Away Team")
    if with_players:
        for team_id, prefix in (
            (home_team_id, "Home"),
            (away_team_id, "Away"),
        ):
            create_player(
                client,
                headers,
                team_id=team_id,
                full_name=f"{prefix} Goalkeeper",
                number=1,
                position="goalkeeper",
            )
            create_player(
                client,
                headers,
                team_id=team_id,
                full_name=f"{prefix} Forward",
                number=9,
                position="forward",
            )
            create_player(
                client,
                headers,
                team_id=team_id,
                full_name=f"{prefix} Midfielder",
                number=10,
                position="midfielder",
            )
    match = create_match(
        client,
        headers,
        tournament_id=tournament_id,
        season_id=season_id,
        home_team_id=home_team_id,
        away_team_id=away_team_id,
        stadium_id=stadium_id,
        stage=stage,
    )
    return {
        "season_id": season_id,
        "tournament_id": tournament_id,
        "stadium_id": stadium_id,
        "home_team_id": home_team_id,
        "away_team_id": away_team_id,
        "match": match,
    }


def add_goal_event(
    client: TestClient,
    headers: dict[str, str],
    *,
    match_id: int,
    team_id: int,
    player_id: int,
) -> None:
    response = client.post(
        f"/api/v1/matches/{match_id}/events",
        json={
            "team_id": team_id,
            "player_id": player_id,
            "event_type": "goal",
            "minute": 10,
        },
        headers=headers,
    )
    assert response.status_code == 201


def get_first_player_id(
    client: TestClient,
    headers: dict[str, str],
    team_id: int,
) -> int:
    response = client.get("/api/v1/players/", headers=headers)
    assert response.status_code == 200
    for player in response.json():
        if player["team_id"] == team_id:
            return int(player["id"])
    raise AssertionError("Expected a player for team.")


def event_counts_by_team(events: list[dict[str, Any]], event_type: str) -> Counter[int]:
    return Counter(
        event["team_id"] for event in events if event["event_type"] == event_type
    )


def test_generate_random_result_finishes_match_and_creates_bounded_protocol(
    client: TestClient,
) -> None:
    headers = auth_headers(client)
    context = setup_random_result_context(client, headers)

    response = client.post(
        f"/api/v1/matches/{context['match']['id']}/generate-random-result",
        json={"seed": 42},
        headers=headers,
    )

    assert response.status_code == 200
    body = response.json()
    match = body["match"]
    events = body["events"]

    assert match["status"] == "finished"
    assert 0 <= match["home_score"] <= 5
    assert 0 <= match["away_score"] <= 5

    goals_by_team = event_counts_by_team(events, "goal")
    assert goals_by_team[context["home_team_id"]] == match["home_score"]
    assert goals_by_team[context["away_team_id"]] == match["away_score"]

    yellow_cards_by_team = event_counts_by_team(events, "yellow_card")
    red_cards_by_team = event_counts_by_team(events, "red_card")
    saves_by_team = event_counts_by_team(events, "save")
    for team_id in (context["home_team_id"], context["away_team_id"]):
        assert yellow_cards_by_team[team_id] <= 5
        assert red_cards_by_team[team_id] <= 1
        assert saves_by_team[team_id] <= 10

    list_events_response = client.get(
        f"/api/v1/matches/{context['match']['id']}/events",
        headers=headers,
    )
    assert list_events_response.status_code == 200
    assert list_events_response.json() == events


def test_generate_random_result_rejects_match_without_players(
    client: TestClient,
) -> None:
    headers = auth_headers(client)
    context = setup_random_result_context(client, headers, with_players=False)

    response = client.post(
        f"/api/v1/matches/{context['match']['id']}/generate-random-result",
        json={"seed": 3},
        headers=headers,
    )

    assert response.status_code == 400


def test_generate_random_result_rejects_existing_protocol_events(
    client: TestClient,
) -> None:
    headers = auth_headers(client)
    context = setup_random_result_context(client, headers)
    add_goal_event(
        client,
        headers,
        match_id=context["match"]["id"],
        team_id=context["home_team_id"],
        player_id=get_first_player_id(client, headers, context["home_team_id"]),
    )

    response = client.post(
        f"/api/v1/matches/{context['match']['id']}/generate-random-result",
        json={"seed": 4},
        headers=headers,
    )

    assert response.status_code == 409


def test_generate_random_result_rejects_finished_match(client: TestClient) -> None:
    headers = auth_headers(client)
    context = setup_random_result_context(client, headers)
    first_response = client.post(
        f"/api/v1/matches/{context['match']['id']}/generate-random-result",
        json={"seed": 5},
        headers=headers,
    )
    assert first_response.status_code == 200

    response = client.post(
        f"/api/v1/matches/{context['match']['id']}/generate-random-result",
        json={"seed": 6},
        headers=headers,
    )

    assert response.status_code == 400


def test_generate_random_result_returns_404_for_missing_match(
    client: TestClient,
) -> None:
    headers = auth_headers(client)

    response = client.post(
        "/api/v1/matches/999/generate-random-result",
        json={"seed": 7},
        headers=headers,
    )

    assert response.status_code == 404


def test_generate_random_result_breaks_cup_stage_draw(client: TestClient) -> None:
    headers = auth_headers(client)
    context = setup_random_result_context(
        client,
        headers,
        tournament_type="cup",
        stage="semifinal",
    )

    response = client.post(
        f"/api/v1/matches/{context['match']['id']}/generate-random-result",
        json={"seed": 1},
        headers=headers,
    )

    assert response.status_code == 200
    match = response.json()["match"]
    assert match["status"] == "finished"
    assert match["home_score"] != match["away_score"]


@pytest.mark.parametrize(
    ("method", "path", "json_body"),
    [
        (
            "POST",
            "/api/v1/matches/1/generate-random-result",
            {"seed": 1},
        ),
    ],
)
def test_random_result_endpoints_require_jwt(
    client: TestClient,
    method: str,
    path: str,
    json_body: dict[str, Any],
) -> None:
    response = client.request(method, path, json=json_body)

    assert response.status_code == 401
    assert response.headers["WWW-Authenticate"] == "Bearer"
