from typing import Any

import pytest
from fastapi.testclient import TestClient


def auth_headers(client: TestClient) -> dict[str, str]:
    client.post(
        "/api/v1/auth/register",
        json={
            "nickname": "cup-organizer",
            "email": "cup-organizer@example.com",
            "password": "StrongPass123",
        },
    )
    response = client.post(
        "/api/v1/auth/login",
        json={
            "email": "cup-organizer@example.com",
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


def create_team(
    client: TestClient,
    headers: dict[str, str],
    name: str,
    previous_season_place: int,
) -> int:
    response = client.post(
        "/api/v1/teams/",
        json={
            "name": name,
            "city": "Moscow",
            "previous_season_place": previous_season_place,
        },
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


def create_stadium(
    client: TestClient,
    headers: dict[str, str],
    *,
    name: str,
    home_team_id: int | None = None,
) -> int:
    response = client.post(
        "/api/v1/stadiums/",
        json={
            "name": name,
            "city": "Moscow",
            "address": f"{name} street 1",
            "capacity": 50000,
            "home_team_id": home_team_id,
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


def setup_cup_context(
    client: TestClient,
    headers: dict[str, str],
    *,
    create_home_stadiums: bool = True,
) -> dict[str, Any]:
    season_id = create_season(client, headers)
    cup_id = create_tournament(
        client,
        headers,
        season_id,
        name="National Cup",
        tournament_type="cup",
    )
    team_ids = [
        create_team(client, headers, f"Team {index}", index) for index in range(1, 5)
    ]
    player_ids_by_team = {
        team_id: create_player(
            client,
            headers,
            team_id=team_id,
            full_name=f"Team {index} Forward",
            number=9,
        )
        for index, team_id in enumerate(team_ids, start=1)
    }
    stadium_ids = []
    if create_home_stadiums:
        stadium_ids = [
            create_stadium(
                client,
                headers,
                name=f"Team {index} Arena",
                home_team_id=team_id,
            )
            for index, team_id in enumerate(team_ids, start=1)
        ]
    neutral_stadium_id = create_stadium(client, headers, name="Cup Final Arena")
    return {
        "season_id": season_id,
        "cup_id": cup_id,
        "team_ids": team_ids,
        "player_ids_by_team": player_ids_by_team,
        "stadium_ids": stadium_ids,
        "neutral_stadium_id": neutral_stadium_id,
    }


def semifinal_payload(team_ids: list[int], **overrides: Any) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "team_ids": team_ids,
        "match_datetimes": [
            "2026-04-01T18:00:00",
            "2026-04-02T18:00:00",
        ],
    }
    payload.update(overrides)
    return payload


def generate_semifinals(
    client: TestClient,
    headers: dict[str, str],
    *,
    cup_id: int,
    payload: dict[str, Any],
) -> list[dict[str, Any]]:
    response = client.post(
        f"/api/v1/cups/{cup_id}/semifinals",
        json=payload,
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


def test_cup_semifinals_final_and_bracket_flow(client: TestClient) -> None:
    headers = auth_headers(client)
    context = setup_cup_context(client, headers)

    semifinals = generate_semifinals(
        client,
        headers,
        cup_id=context["cup_id"],
        payload=semifinal_payload(context["team_ids"]),
    )

    assert len(semifinals) == 2
    assert [match["stage"] for match in semifinals] == ["semifinal", "semifinal"]
    assert [match["round_number"] for match in semifinals] == [1, 1]
    assert [(match["home_team_id"], match["away_team_id"]) for match in semifinals] == [
        (context["team_ids"][0], context["team_ids"][3]),
        (context["team_ids"][1], context["team_ids"][2]),
    ]
    assert semifinals[0]["stadium_id"] == context["stadium_ids"][0]
    assert semifinals[1]["stadium_id"] == context["stadium_ids"][1]

    bracket_response = client.get(
        f"/api/v1/cups/{context['cup_id']}/bracket",
        headers=headers,
    )
    assert bracket_response.status_code == 200
    assert len(bracket_response.json()["semifinals"]) == 2
    assert bracket_response.json()["final"] is None
    assert bracket_response.json()["champion_team_id"] is None

    first_winner_id = context["team_ids"][0]
    second_winner_id = context["team_ids"][2]
    add_goal(
        client,
        headers,
        match_id=semifinals[0]["id"],
        team_id=first_winner_id,
        player_id=context["player_ids_by_team"][first_winner_id],
        minute=25,
    )
    finish_match(
        client,
        headers,
        match_id=semifinals[0]["id"],
        home_score=1,
        away_score=0,
    )
    add_goal(
        client,
        headers,
        match_id=semifinals[1]["id"],
        team_id=second_winner_id,
        player_id=context["player_ids_by_team"][second_winner_id],
        minute=40,
    )
    finish_match(
        client,
        headers,
        match_id=semifinals[1]["id"],
        home_score=0,
        away_score=1,
    )

    final_response = client.post(
        f"/api/v1/cups/{context['cup_id']}/final",
        json={
            "match_datetime": "2026-04-08T19:00:00",
            "stadium_id": context["neutral_stadium_id"],
        },
        headers=headers,
    )

    assert final_response.status_code == 201
    final_match = final_response.json()
    assert final_match["stage"] == "final"
    assert final_match["round_number"] == 2
    assert final_match["home_team_id"] == first_winner_id
    assert final_match["away_team_id"] == second_winner_id
    assert final_match["stadium_id"] == context["neutral_stadium_id"]

    add_goal(
        client,
        headers,
        match_id=final_match["id"],
        team_id=second_winner_id,
        player_id=context["player_ids_by_team"][second_winner_id],
        minute=75,
    )
    finish_match(
        client,
        headers,
        match_id=final_match["id"],
        home_score=0,
        away_score=1,
    )

    final_bracket_response = client.get(
        f"/api/v1/cups/{context['cup_id']}/bracket",
        headers=headers,
    )

    assert final_bracket_response.status_code == 200
    bracket = final_bracket_response.json()
    assert [node["winner_team_id"] for node in bracket["semifinals"]] == [
        first_winner_id,
        second_winner_id,
    ]
    assert bracket["final"]["winner_team_id"] == second_winner_id
    assert bracket["champion_team_id"] == second_winner_id


def test_generate_cup_semifinals_rejects_non_cup_tournament(
    client: TestClient,
) -> None:
    headers = auth_headers(client)
    context = setup_cup_context(client, headers)
    championship_id = create_tournament(
        client,
        headers,
        context["season_id"],
        name="Premier League",
        tournament_type="championship",
    )

    response = client.post(
        f"/api/v1/cups/{championship_id}/semifinals",
        json=semifinal_payload(context["team_ids"]),
        headers=headers,
    )

    assert response.status_code == 400


def test_generate_cup_semifinals_returns_404_for_missing_tournament(
    client: TestClient,
) -> None:
    headers = auth_headers(client)

    response = client.post(
        "/api/v1/cups/999/semifinals",
        json=semifinal_payload([1, 2, 3, 4]),
        headers=headers,
    )

    assert response.status_code == 404


def test_generate_cup_semifinals_returns_404_for_missing_team(
    client: TestClient,
) -> None:
    headers = auth_headers(client)
    context = setup_cup_context(client, headers)

    response = client.post(
        f"/api/v1/cups/{context['cup_id']}/semifinals",
        json=semifinal_payload([context["team_ids"][0], 999, 998, 997]),
        headers=headers,
    )

    assert response.status_code == 404


def test_generate_cup_semifinals_returns_404_for_missing_stadium(
    client: TestClient,
) -> None:
    headers = auth_headers(client)
    context = setup_cup_context(client, headers, create_home_stadiums=False)

    response = client.post(
        f"/api/v1/cups/{context['cup_id']}/semifinals",
        json=semifinal_payload(context["team_ids"], fallback_stadium_id=999),
        headers=headers,
    )

    assert response.status_code == 404


def test_generate_cup_semifinals_rejects_duplicate_teams(
    client: TestClient,
) -> None:
    headers = auth_headers(client)
    context = setup_cup_context(client, headers)
    team_ids = [
        context["team_ids"][0],
        context["team_ids"][0],
        context["team_ids"][1],
        context["team_ids"][2],
    ]

    response = client.post(
        f"/api/v1/cups/{context['cup_id']}/semifinals",
        json=semifinal_payload(team_ids),
        headers=headers,
    )

    assert response.status_code == 400


def test_generate_cup_semifinals_rejects_existing_calendar_conflict(
    client: TestClient,
) -> None:
    headers = auth_headers(client)
    context = setup_cup_context(client, headers)
    championship_id = create_tournament(
        client,
        headers,
        context["season_id"],
        name="Premier League",
        tournament_type="championship",
    )
    create_match(
        client,
        headers,
        tournament_id=championship_id,
        season_id=context["season_id"],
        home_team_id=context["team_ids"][0],
        away_team_id=context["team_ids"][1],
        stadium_id=context["stadium_ids"][0],
        match_datetime="2026-04-01T20:00:00",
    )

    response = client.post(
        f"/api/v1/cups/{context['cup_id']}/semifinals",
        json=semifinal_payload(context["team_ids"]),
        headers=headers,
    )
    bracket_response = client.get(
        f"/api/v1/cups/{context['cup_id']}/bracket",
        headers=headers,
    )

    assert response.status_code == 409
    assert bracket_response.status_code == 200
    assert bracket_response.json()["semifinals"] == []


def test_generate_cup_semifinals_rejects_duplicate_bracket(
    client: TestClient,
) -> None:
    headers = auth_headers(client)
    context = setup_cup_context(client, headers)
    generate_semifinals(
        client,
        headers,
        cup_id=context["cup_id"],
        payload=semifinal_payload(context["team_ids"]),
    )

    response = client.post(
        f"/api/v1/cups/{context['cup_id']}/semifinals",
        json=semifinal_payload(
            context["team_ids"],
            match_datetimes=[
                "2026-04-08T18:00:00",
                "2026-04-09T18:00:00",
            ],
        ),
        headers=headers,
    )

    assert response.status_code == 409


def test_generate_cup_final_requires_finished_semifinals(
    client: TestClient,
) -> None:
    headers = auth_headers(client)
    context = setup_cup_context(client, headers)
    generate_semifinals(
        client,
        headers,
        cup_id=context["cup_id"],
        payload=semifinal_payload(context["team_ids"]),
    )

    response = client.post(
        f"/api/v1/cups/{context['cup_id']}/final",
        json={
            "match_datetime": "2026-04-08T19:00:00",
            "stadium_id": context["neutral_stadium_id"],
        },
        headers=headers,
    )

    assert response.status_code == 400


def test_generate_cup_final_returns_404_for_missing_stadium(
    client: TestClient,
) -> None:
    headers = auth_headers(client)
    context = setup_cup_context(client, headers)

    response = client.post(
        f"/api/v1/cups/{context['cup_id']}/final",
        json={
            "match_datetime": "2026-04-08T19:00:00",
            "stadium_id": 999,
        },
        headers=headers,
    )

    assert response.status_code == 404


def test_generate_cup_final_rejects_drawn_semifinal(
    client: TestClient,
) -> None:
    headers = auth_headers(client)
    context = setup_cup_context(client, headers)
    semifinals = generate_semifinals(
        client,
        headers,
        cup_id=context["cup_id"],
        payload=semifinal_payload(context["team_ids"]),
    )
    for team_id, minute in (
        (semifinals[0]["home_team_id"], 12),
        (semifinals[0]["away_team_id"], 55),
    ):
        add_goal(
            client,
            headers,
            match_id=semifinals[0]["id"],
            team_id=team_id,
            player_id=context["player_ids_by_team"][team_id],
            minute=minute,
        )
    finish_match(
        client,
        headers,
        match_id=semifinals[0]["id"],
        home_score=1,
        away_score=1,
    )
    add_goal(
        client,
        headers,
        match_id=semifinals[1]["id"],
        team_id=semifinals[1]["home_team_id"],
        player_id=context["player_ids_by_team"][semifinals[1]["home_team_id"]],
        minute=20,
    )
    finish_match(
        client,
        headers,
        match_id=semifinals[1]["id"],
        home_score=1,
        away_score=0,
    )

    response = client.post(
        f"/api/v1/cups/{context['cup_id']}/final",
        json={
            "match_datetime": "2026-04-08T19:00:00",
            "stadium_id": context["neutral_stadium_id"],
        },
        headers=headers,
    )

    assert response.status_code == 400


@pytest.mark.parametrize(
    ("method", "path", "json_body"),
    [
        ("GET", "/api/v1/cups/1/bracket", None),
        ("POST", "/api/v1/cups/1/semifinals", semifinal_payload([1, 2, 3, 4])),
        (
            "POST",
            "/api/v1/cups/1/final",
            {"match_datetime": "2026-04-08T19:00:00", "stadium_id": 1},
        ),
    ],
)
def test_cup_endpoints_require_jwt(
    client: TestClient,
    method: str,
    path: str,
    json_body: dict[str, Any] | None,
) -> None:
    response = client.request(method, path, json=json_body)

    assert response.status_code == 401
    assert response.headers["WWW-Authenticate"] == "Bearer"
