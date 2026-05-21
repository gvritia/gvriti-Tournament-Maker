from decimal import Decimal
from typing import Any

import pytest
from fastapi.testclient import TestClient


def auth_headers(client: TestClient) -> dict[str, str]:
    client.post(
        "/api/v1/auth/register",
        json={
            "nickname": "match-organizer",
            "email": "match-organizer@example.com",
            "password": "StrongPass123",
        },
    )
    response = client.post(
        "/api/v1/auth/login",
        json={
            "email": "match-organizer@example.com",
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
    name: str = "Premier League",
    tournament_type: str = "championship",
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


def create_referee(client: TestClient, headers: dict[str, str]) -> int:
    response = client.post(
        "/api/v1/referees/",
        json={"full_name": "Sergey Ivanov"},
        headers=headers,
    )
    assert response.status_code == 201
    return int(response.json()["id"])


def create_match_payload(
    *,
    tournament_id: int,
    season_id: int,
    home_team_id: int,
    away_team_id: int,
    stadium_id: int,
    match_datetime: str = "2026-04-01T18:00:00",
    referee_id: int | None = None,
) -> dict[str, Any]:
    return {
        "tournament_id": tournament_id,
        "season_id": season_id,
        "home_team_id": home_team_id,
        "away_team_id": away_team_id,
        "stadium_id": stadium_id,
        "referee_id": referee_id,
        "match_datetime": match_datetime,
        "round_number": 1,
    }


def create_match(
    client: TestClient,
    headers: dict[str, str],
    payload: dict[str, Any],
) -> dict[str, Any]:
    response = client.post("/api/v1/matches/", json=payload, headers=headers)
    assert response.status_code == 201
    return response.json()


def setup_match_context(
    client: TestClient,
    headers: dict[str, str],
    *,
    team_count: int = 2,
) -> dict[str, Any]:
    season_id = create_season(client, headers)
    tournament_id = create_tournament(client, headers, season_id)
    stadium_id = create_stadium(client, headers)
    team_ids = [
        create_team(client, headers, f"Team {index}", index)
        for index in range(1, team_count + 1)
    ]
    return {
        "season_id": season_id,
        "tournament_id": tournament_id,
        "stadium_id": stadium_id,
        "team_ids": team_ids,
    }


def decimal_from_response(value: Any) -> Decimal:
    return Decimal(str(value)).quantize(Decimal("0.01"))


def test_create_match_success(client: TestClient) -> None:
    headers = auth_headers(client)
    context = setup_match_context(client, headers, team_count=2)

    response = client.post(
        "/api/v1/matches/",
        json=create_match_payload(
            tournament_id=context["tournament_id"],
            season_id=context["season_id"],
            home_team_id=context["team_ids"][0],
            away_team_id=context["team_ids"][1],
            stadium_id=context["stadium_id"],
        ),
        headers=headers,
    )

    assert response.status_code == 201
    body = response.json()
    assert body["status"] == "scheduled"
    assert body["home_team_id"] == context["team_ids"][0]
    assert body["away_team_id"] == context["team_ids"][1]
    assert decimal_from_response(body["ticket_price"]) == Decimal("60.00")


def test_create_match_rejects_same_home_and_away_team(client: TestClient) -> None:
    headers = auth_headers(client)
    context = setup_match_context(client, headers, team_count=1)

    response = client.post(
        "/api/v1/matches/",
        json=create_match_payload(
            tournament_id=context["tournament_id"],
            season_id=context["season_id"],
            home_team_id=context["team_ids"][0],
            away_team_id=context["team_ids"][0],
            stadium_id=context["stadium_id"],
        ),
        headers=headers,
    )

    assert response.status_code == 400


def test_create_match_rejects_finished_status(client: TestClient) -> None:
    headers = auth_headers(client)
    context = setup_match_context(client, headers, team_count=2)
    payload = create_match_payload(
        tournament_id=context["tournament_id"],
        season_id=context["season_id"],
        home_team_id=context["team_ids"][0],
        away_team_id=context["team_ids"][1],
        stadium_id=context["stadium_id"],
    )
    payload["status"] = "finished"

    response = client.post("/api/v1/matches/", json=payload, headers=headers)

    assert response.status_code == 400


def test_update_match_rejects_finished_status(client: TestClient) -> None:
    headers = auth_headers(client)
    context = setup_match_context(client, headers, team_count=2)
    match = create_match(
        client,
        headers,
        create_match_payload(
            tournament_id=context["tournament_id"],
            season_id=context["season_id"],
            home_team_id=context["team_ids"][0],
            away_team_id=context["team_ids"][1],
            stadium_id=context["stadium_id"],
        ),
    )

    response = client.patch(
        f"/api/v1/matches/{match['id']}",
        json={"status": "finished", "home_score": 0, "away_score": 0},
        headers=headers,
    )

    assert response.status_code == 400


def test_create_match_rejects_tournament_season_mismatch(
    client: TestClient,
) -> None:
    headers = auth_headers(client)
    context = setup_match_context(client, headers, team_count=2)
    other_season_response = client.post(
        "/api/v1/seasons/",
        json={
            "name": "2027",
            "start_date": "2027-03-01",
            "end_date": "2027-11-30",
        },
        headers=headers,
    )
    assert other_season_response.status_code == 201

    response = client.post(
        "/api/v1/matches/",
        json=create_match_payload(
            tournament_id=context["tournament_id"],
            season_id=other_season_response.json()["id"],
            home_team_id=context["team_ids"][0],
            away_team_id=context["team_ids"][1],
            stadium_id=context["stadium_id"],
        ),
        headers=headers,
    )

    assert response.status_code == 400


@pytest.mark.parametrize(
    ("missing_field", "expected_status"),
    [
        ("home_team_id", 404),
        ("tournament_id", 404),
        ("season_id", 404),
        ("stadium_id", 404),
    ],
)
def test_create_match_validates_related_entities(
    client: TestClient,
    missing_field: str,
    expected_status: int,
) -> None:
    headers = auth_headers(client)
    context = setup_match_context(client, headers, team_count=2)
    payload = create_match_payload(
        tournament_id=context["tournament_id"],
        season_id=context["season_id"],
        home_team_id=context["team_ids"][0],
        away_team_id=context["team_ids"][1],
        stadium_id=context["stadium_id"],
    )
    payload[missing_field] = 999

    response = client.post("/api/v1/matches/", json=payload, headers=headers)

    assert response.status_code == expected_status


def test_create_match_rejects_second_team_match_in_one_day(
    client: TestClient,
) -> None:
    headers = auth_headers(client)
    context = setup_match_context(client, headers, team_count=3)
    cup_id = create_tournament(
        client,
        headers,
        context["season_id"],
        name="National Cup",
        tournament_type="cup",
    )
    create_match(
        client,
        headers,
        create_match_payload(
            tournament_id=context["tournament_id"],
            season_id=context["season_id"],
            home_team_id=context["team_ids"][0],
            away_team_id=context["team_ids"][1],
            stadium_id=context["stadium_id"],
            match_datetime="2026-04-01T18:00:00",
        ),
    )

    response = client.post(
        "/api/v1/matches/",
        json=create_match_payload(
            tournament_id=cup_id,
            season_id=context["season_id"],
            home_team_id=context["team_ids"][0],
            away_team_id=context["team_ids"][2],
            stadium_id=context["stadium_id"],
            match_datetime="2026-04-01T20:00:00",
        ),
        headers=headers,
    )

    assert response.status_code == 409


def test_create_match_rejects_third_team_match_in_week(client: TestClient) -> None:
    headers = auth_headers(client)
    context = setup_match_context(client, headers, team_count=4)
    create_match(
        client,
        headers,
        create_match_payload(
            tournament_id=context["tournament_id"],
            season_id=context["season_id"],
            home_team_id=context["team_ids"][0],
            away_team_id=context["team_ids"][1],
            stadium_id=context["stadium_id"],
            match_datetime="2026-04-06T18:00:00",
        ),
    )
    create_match(
        client,
        headers,
        create_match_payload(
            tournament_id=context["tournament_id"],
            season_id=context["season_id"],
            home_team_id=context["team_ids"][0],
            away_team_id=context["team_ids"][2],
            stadium_id=context["stadium_id"],
            match_datetime="2026-04-08T18:00:00",
        ),
    )

    response = client.post(
        "/api/v1/matches/",
        json=create_match_payload(
            tournament_id=context["tournament_id"],
            season_id=context["season_id"],
            home_team_id=context["team_ids"][0],
            away_team_id=context["team_ids"][3],
            stadium_id=context["stadium_id"],
            match_datetime="2026-04-10T18:00:00",
        ),
        headers=headers,
    )

    assert response.status_code == 409


def test_reschedule_match_success(client: TestClient) -> None:
    headers = auth_headers(client)
    context = setup_match_context(client, headers, team_count=2)
    match = create_match(
        client,
        headers,
        create_match_payload(
            tournament_id=context["tournament_id"],
            season_id=context["season_id"],
            home_team_id=context["team_ids"][0],
            away_team_id=context["team_ids"][1],
            stadium_id=context["stadium_id"],
            match_datetime="2026-04-01T18:00:00",
        ),
    )

    response = client.post(
        f"/api/v1/matches/{match['id']}/reschedule",
        json={"match_datetime": "2026-04-02T19:00:00"},
        headers=headers,
    )

    assert response.status_code == 200
    assert response.json()["match_datetime"].startswith("2026-04-02T19:00:00")


def test_reschedule_match_rejects_calendar_conflict(client: TestClient) -> None:
    headers = auth_headers(client)
    context = setup_match_context(client, headers, team_count=3)
    create_match(
        client,
        headers,
        create_match_payload(
            tournament_id=context["tournament_id"],
            season_id=context["season_id"],
            home_team_id=context["team_ids"][0],
            away_team_id=context["team_ids"][1],
            stadium_id=context["stadium_id"],
            match_datetime="2026-04-01T18:00:00",
        ),
    )
    match_to_move = create_match(
        client,
        headers,
        create_match_payload(
            tournament_id=context["tournament_id"],
            season_id=context["season_id"],
            home_team_id=context["team_ids"][0],
            away_team_id=context["team_ids"][2],
            stadium_id=context["stadium_id"],
            match_datetime="2026-04-03T18:00:00",
        ),
    )

    response = client.post(
        f"/api/v1/matches/{match_to_move['id']}/reschedule",
        json={"match_datetime": "2026-04-01T20:00:00"},
        headers=headers,
    )

    assert response.status_code == 409


def test_assign_referee_success(client: TestClient) -> None:
    headers = auth_headers(client)
    context = setup_match_context(client, headers, team_count=2)
    referee_id = create_referee(client, headers)
    match = create_match(
        client,
        headers,
        create_match_payload(
            tournament_id=context["tournament_id"],
            season_id=context["season_id"],
            home_team_id=context["team_ids"][0],
            away_team_id=context["team_ids"][1],
            stadium_id=context["stadium_id"],
        ),
    )

    response = client.post(
        f"/api/v1/matches/{match['id']}/assign-referee",
        json={"referee_id": referee_id},
        headers=headers,
    )

    assert response.status_code == 200
    assert response.json()["referee_id"] == referee_id


def test_assign_referee_rejects_parallel_match(client: TestClient) -> None:
    headers = auth_headers(client)
    context = setup_match_context(client, headers, team_count=4)
    referee_id = create_referee(client, headers)
    first_match = create_match(
        client,
        headers,
        create_match_payload(
            tournament_id=context["tournament_id"],
            season_id=context["season_id"],
            home_team_id=context["team_ids"][0],
            away_team_id=context["team_ids"][1],
            stadium_id=context["stadium_id"],
            match_datetime="2026-04-01T18:00:00",
        ),
    )
    second_match = create_match(
        client,
        headers,
        create_match_payload(
            tournament_id=context["tournament_id"],
            season_id=context["season_id"],
            home_team_id=context["team_ids"][2],
            away_team_id=context["team_ids"][3],
            stadium_id=context["stadium_id"],
            match_datetime="2026-04-01T18:00:00",
        ),
    )
    client.post(
        f"/api/v1/matches/{first_match['id']}/assign-referee",
        json={"referee_id": referee_id},
        headers=headers,
    )

    response = client.post(
        f"/api/v1/matches/{second_match['id']}/assign-referee",
        json={"referee_id": referee_id},
        headers=headers,
    )

    assert response.status_code == 409


def test_set_manual_ticket_price_keeps_price_after_reschedule(
    client: TestClient,
) -> None:
    headers = auth_headers(client)
    context = setup_match_context(client, headers, team_count=2)
    match = create_match(
        client,
        headers,
        create_match_payload(
            tournament_id=context["tournament_id"],
            season_id=context["season_id"],
            home_team_id=context["team_ids"][0],
            away_team_id=context["team_ids"][1],
            stadium_id=context["stadium_id"],
        ),
    )

    price_response = client.post(
        f"/api/v1/matches/{match['id']}/ticket-price",
        json={"ticket_price": "42.50"},
        headers=headers,
    )
    reschedule_response = client.post(
        f"/api/v1/matches/{match['id']}/reschedule",
        json={"match_datetime": "2026-04-08T18:00:00"},
        headers=headers,
    )

    assert price_response.status_code == 200
    assert decimal_from_response(price_response.json()["ticket_price"]) == Decimal(
        "42.50"
    )
    assert reschedule_response.status_code == 200
    assert decimal_from_response(reschedule_response.json()["ticket_price"]) == Decimal(
        "42.50"
    )


@pytest.mark.parametrize(
    ("method", "path_suffix", "json_body"),
    [
        ("PATCH", "", {"round_number": 2}),
        ("DELETE", "", None),
        ("POST", "/assign-referee", {"referee_id": "REFEREE_ID"}),
        ("POST", "/reschedule", {"match_datetime": "2026-04-08T18:00:00"}),
        ("POST", "/ticket-price", {"ticket_price": "42.50"}),
    ],
)
def test_finished_match_rejects_normal_edit_actions(
    client: TestClient,
    method: str,
    path_suffix: str,
    json_body: dict[str, Any] | None,
) -> None:
    headers = auth_headers(client)
    context = setup_match_context(client, headers, team_count=2)
    referee_id = create_referee(client, headers)
    match = create_match(
        client,
        headers,
        create_match_payload(
            tournament_id=context["tournament_id"],
            season_id=context["season_id"],
            home_team_id=context["team_ids"][0],
            away_team_id=context["team_ids"][1],
            stadium_id=context["stadium_id"],
        ),
    )
    finish_response = client.post(
        f"/api/v1/matches/{match['id']}/finish",
        json={"home_score": 0, "away_score": 0},
        headers=headers,
    )
    assert finish_response.status_code == 200

    if json_body is not None:
        json_body = {
            key: referee_id if value == "REFEREE_ID" else value
            for key, value in json_body.items()
        }

    response = client.request(
        method,
        f"/api/v1/matches/{match['id']}{path_suffix}",
        json=json_body,
        headers=headers,
    )

    assert response.status_code == 400


@pytest.mark.parametrize(
    ("method", "path", "json_body"),
    [
        ("GET", "/api/v1/matches/", None),
        (
            "POST",
            "/api/v1/matches/",
            {
                "tournament_id": 1,
                "season_id": 1,
                "home_team_id": 1,
                "away_team_id": 2,
                "stadium_id": 1,
                "match_datetime": "2026-04-01T18:00:00",
                "round_number": 1,
            },
        ),
        ("GET", "/api/v1/matches/1", None),
        ("PATCH", "/api/v1/matches/1", {"round_number": 2}),
        ("DELETE", "/api/v1/matches/1", None),
        ("POST", "/api/v1/matches/1/assign-referee", {"referee_id": 1}),
        (
            "POST",
            "/api/v1/matches/1/reschedule",
            {"match_datetime": "2026-04-02T18:00:00"},
        ),
        ("POST", "/api/v1/matches/1/ticket-price", {"ticket_price": "30.00"}),
    ],
)
def test_match_endpoints_require_jwt(
    client: TestClient,
    method: str,
    path: str,
    json_body: dict[str, Any] | None,
) -> None:
    response = client.request(method, path, json=json_body)

    assert response.status_code == 401
    assert response.headers["WWW-Authenticate"] == "Bearer"
