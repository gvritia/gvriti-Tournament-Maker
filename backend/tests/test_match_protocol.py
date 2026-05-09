from typing import Any

import pytest
from fastapi.testclient import TestClient


def auth_headers(client: TestClient) -> dict[str, str]:
    client.post(
        "/api/v1/auth/register",
        json={
            "nickname": "protocol-organizer",
            "email": "protocol-organizer@example.com",
            "password": "StrongPass123",
        },
    )
    response = client.post(
        "/api/v1/auth/login",
        json={
            "email": "protocol-organizer@example.com",
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
            "name": "Premier League",
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
) -> dict[str, Any]:
    response = client.post(
        "/api/v1/matches/",
        json={
            "tournament_id": tournament_id,
            "season_id": season_id,
            "home_team_id": home_team_id,
            "away_team_id": away_team_id,
            "stadium_id": stadium_id,
            "match_datetime": "2026-04-01T18:00:00",
            "round_number": 1,
        },
        headers=headers,
    )
    assert response.status_code == 201
    return response.json()


def setup_protocol_context(
    client: TestClient,
    headers: dict[str, str],
    *,
    include_extra_team: bool = False,
    tournament_type: str = "championship",
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
    extra_team_id = (
        create_team(client, headers, "Extra Team") if include_extra_team else None
    )
    home_player_id = create_player(
        client,
        headers,
        team_id=home_team_id,
        full_name="Home Scorer",
        number=9,
    )
    home_assist_id = create_player(
        client,
        headers,
        team_id=home_team_id,
        full_name="Home Assistant",
        number=10,
    )
    away_player_id = create_player(
        client,
        headers,
        team_id=away_team_id,
        full_name="Away Defender",
        number=5,
    )
    extra_player_id = (
        create_player(
            client,
            headers,
            team_id=extra_team_id,
            full_name="Extra Player",
            number=7,
        )
        if extra_team_id is not None
        else None
    )
    match = create_match(
        client,
        headers,
        tournament_id=tournament_id,
        season_id=season_id,
        home_team_id=home_team_id,
        away_team_id=away_team_id,
        stadium_id=stadium_id,
    )
    return {
        "season_id": season_id,
        "tournament_id": tournament_id,
        "stadium_id": stadium_id,
        "home_team_id": home_team_id,
        "away_team_id": away_team_id,
        "extra_team_id": extra_team_id,
        "home_player_id": home_player_id,
        "home_assist_id": home_assist_id,
        "away_player_id": away_player_id,
        "extra_player_id": extra_player_id,
        "match": match,
    }


def create_event_payload(
    *,
    team_id: int,
    player_id: int,
    event_type: str,
    minute: int = 10,
    assist_player_id: int | None = None,
) -> dict[str, Any]:
    return {
        "team_id": team_id,
        "player_id": player_id,
        "assist_player_id": assist_player_id,
        "event_type": event_type,
        "minute": minute,
    }


def add_event(
    client: TestClient,
    headers: dict[str, str],
    *,
    match_id: int,
    payload: dict[str, Any],
) -> dict[str, Any]:
    response = client.post(
        f"/api/v1/matches/{match_id}/events",
        json=payload,
        headers=headers,
    )
    assert response.status_code == 201
    return response.json()


def test_add_list_update_and_delete_match_event(client: TestClient) -> None:
    headers = auth_headers(client)
    context = setup_protocol_context(client, headers)
    match_id = context["match"]["id"]

    goal = add_event(
        client,
        headers,
        match_id=match_id,
        payload=create_event_payload(
            team_id=context["home_team_id"],
            player_id=context["home_player_id"],
            assist_player_id=context["home_assist_id"],
            event_type="goal",
            minute=12,
        ),
    )
    card = add_event(
        client,
        headers,
        match_id=match_id,
        payload=create_event_payload(
            team_id=context["away_team_id"],
            player_id=context["away_player_id"],
            event_type="yellow_card",
            minute=30,
        ),
    )

    list_response = client.get(f"/api/v1/matches/{match_id}/events", headers=headers)
    assert list_response.status_code == 200
    assert [event["id"] for event in list_response.json()] == [goal["id"], card["id"]]

    update_response = client.patch(
        f"/api/v1/events/{card['id']}",
        json={"minute": 31, "event_type": "red_card"},
        headers=headers,
    )
    assert update_response.status_code == 200
    assert update_response.json()["minute"] == 31
    assert update_response.json()["event_type"] == "red_card"

    delete_response = client.delete(f"/api/v1/events/{card['id']}", headers=headers)
    assert delete_response.status_code == 204
    assert (
        client.get(f"/api/v1/events/{card['id']}", headers=headers).status_code == 404
    )


def test_add_event_rejects_team_that_is_not_match_participant(
    client: TestClient,
) -> None:
    headers = auth_headers(client)
    context = setup_protocol_context(client, headers, include_extra_team=True)

    response = client.post(
        f"/api/v1/matches/{context['match']['id']}/events",
        json=create_event_payload(
            team_id=context["extra_team_id"],
            player_id=context["extra_player_id"],
            event_type="goal",
        ),
        headers=headers,
    )

    assert response.status_code == 400


def test_add_event_rejects_player_from_another_team(client: TestClient) -> None:
    headers = auth_headers(client)
    context = setup_protocol_context(client, headers)

    response = client.post(
        f"/api/v1/matches/{context['match']['id']}/events",
        json=create_event_payload(
            team_id=context["home_team_id"],
            player_id=context["away_player_id"],
            event_type="goal",
        ),
        headers=headers,
    )

    assert response.status_code == 400


def test_add_event_rejects_assist_from_another_team(client: TestClient) -> None:
    headers = auth_headers(client)
    context = setup_protocol_context(client, headers)

    response = client.post(
        f"/api/v1/matches/{context['match']['id']}/events",
        json=create_event_payload(
            team_id=context["home_team_id"],
            player_id=context["home_player_id"],
            assist_player_id=context["away_player_id"],
            event_type="goal",
        ),
        headers=headers,
    )

    assert response.status_code == 400


def test_finish_match_success(client: TestClient) -> None:
    headers = auth_headers(client)
    context = setup_protocol_context(client, headers)
    match_id = context["match"]["id"]
    add_event(
        client,
        headers,
        match_id=match_id,
        payload=create_event_payload(
            team_id=context["home_team_id"],
            player_id=context["home_player_id"],
            event_type="goal",
        ),
    )

    response = client.post(
        f"/api/v1/matches/{match_id}/finish",
        json={"home_score": 1, "away_score": 0},
        headers=headers,
    )

    assert response.status_code == 200
    assert response.json()["status"] == "finished"
    assert response.json()["home_score"] == 1
    assert response.json()["away_score"] == 0


def test_finish_championship_match_recalculates_standings_and_player_stats(
    client: TestClient,
) -> None:
    headers = auth_headers(client)
    context = setup_protocol_context(client, headers)
    match_id = context["match"]["id"]
    add_event(
        client,
        headers,
        match_id=match_id,
        payload=create_event_payload(
            team_id=context["home_team_id"],
            player_id=context["home_player_id"],
            assist_player_id=context["home_assist_id"],
            event_type="goal",
        ),
    )

    finish_response = client.post(
        f"/api/v1/matches/{match_id}/finish",
        json={"home_score": 1, "away_score": 0},
        headers=headers,
    )
    standings_response = client.get(
        f"/api/v1/standings/seasons/{context['season_id']}",
        headers=headers,
    )
    stats_response = client.get(
        f"/api/v1/statistics/seasons/{context['season_id']}/players",
        headers=headers,
    )
    repeated_finish_response = client.post(
        f"/api/v1/matches/{match_id}/finish",
        json={"home_score": 1, "away_score": 0},
        headers=headers,
    )
    repeated_stats_response = client.get(
        f"/api/v1/statistics/seasons/{context['season_id']}/players",
        headers=headers,
    )

    assert finish_response.status_code == 200
    assert standings_response.status_code == 200
    standings = standings_response.json()
    assert [row["team_id"] for row in standings] == [
        context["home_team_id"],
        context["away_team_id"],
    ]
    assert standings[0]["played"] == 1
    assert standings[0]["wins"] == 1
    assert standings[0]["points"] == 3
    assert standings[0]["goals_scored"] == 1
    assert standings[0]["goals_conceded"] == 0
    assert standings[1]["played"] == 1
    assert standings[1]["losses"] == 1
    assert standings[1]["points"] == 0

    assert stats_response.status_code == 200
    stats_by_player = {row["player_id"]: row for row in stats_response.json()}
    assert stats_by_player[context["home_player_id"]]["goals"] == 1
    assert stats_by_player[context["home_assist_id"]]["assists"] == 1

    assert repeated_finish_response.status_code == 400
    assert repeated_stats_response.json() == stats_response.json()


def test_finish_cup_match_updates_player_stats_without_standings(
    client: TestClient,
) -> None:
    headers = auth_headers(client)
    context = setup_protocol_context(
        client,
        headers,
        tournament_type="cup",
    )
    match_id = context["match"]["id"]
    add_event(
        client,
        headers,
        match_id=match_id,
        payload=create_event_payload(
            team_id=context["away_team_id"],
            player_id=context["away_player_id"],
            event_type="goal",
        ),
    )

    finish_response = client.post(
        f"/api/v1/matches/{match_id}/finish",
        json={"home_score": 0, "away_score": 1},
        headers=headers,
    )
    standings_response = client.get(
        f"/api/v1/standings/seasons/{context['season_id']}",
        headers=headers,
    )
    stats_response = client.get(
        f"/api/v1/statistics/seasons/{context['season_id']}/players",
        headers=headers,
    )

    assert finish_response.status_code == 200
    assert standings_response.status_code == 200
    assert standings_response.json() == []

    assert stats_response.status_code == 200
    stats_by_player = {row["player_id"]: row for row in stats_response.json()}
    assert stats_by_player[context["away_player_id"]]["goals"] == 1


def test_finish_match_rejects_score_that_does_not_match_goals(
    client: TestClient,
) -> None:
    headers = auth_headers(client)
    context = setup_protocol_context(client, headers)
    match_id = context["match"]["id"]
    add_event(
        client,
        headers,
        match_id=match_id,
        payload=create_event_payload(
            team_id=context["home_team_id"],
            player_id=context["home_player_id"],
            event_type="goal",
        ),
    )

    response = client.post(
        f"/api/v1/matches/{match_id}/finish",
        json={"home_score": 0, "away_score": 0},
        headers=headers,
    )

    assert response.status_code == 400


def test_add_event_rejects_finished_match(client: TestClient) -> None:
    headers = auth_headers(client)
    context = setup_protocol_context(client, headers)
    match_id = context["match"]["id"]
    finish_response = client.post(
        f"/api/v1/matches/{match_id}/finish",
        json={"home_score": 0, "away_score": 0},
        headers=headers,
    )
    assert finish_response.status_code == 200

    response = client.post(
        f"/api/v1/matches/{match_id}/events",
        json=create_event_payload(
            team_id=context["home_team_id"],
            player_id=context["home_player_id"],
            event_type="yellow_card",
        ),
        headers=headers,
    )

    assert response.status_code == 400


@pytest.mark.parametrize(
    ("method", "path", "json_body"),
    [
        ("GET", "/api/v1/matches/1/events", None),
        (
            "POST",
            "/api/v1/matches/1/events",
            {
                "team_id": 1,
                "player_id": 1,
                "event_type": "goal",
                "minute": 10,
            },
        ),
        ("GET", "/api/v1/events/1", None),
        ("PATCH", "/api/v1/events/1", {"minute": 11}),
        ("DELETE", "/api/v1/events/1", None),
        ("POST", "/api/v1/matches/1/finish", {"home_score": 0, "away_score": 0}),
    ],
)
def test_match_protocol_endpoints_require_jwt(
    client: TestClient,
    method: str,
    path: str,
    json_body: dict[str, Any] | None,
) -> None:
    response = client.request(method, path, json=json_body)

    assert response.status_code == 401
    assert response.headers["WWW-Authenticate"] == "Bearer"
