from collections import Counter, defaultdict
from typing import Any

import pytest
from fastapi.testclient import TestClient


def auth_headers(client: TestClient) -> dict[str, str]:
    client.post(
        "/api/v1/auth/register",
        json={
            "nickname": "schedule-organizer",
            "email": "schedule-organizer@example.com",
            "password": "StrongPass123",
        },
    )
    response = client.post(
        "/api/v1/auth/login",
        json={
            "email": "schedule-organizer@example.com",
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


def setup_schedule_context(
    client: TestClient,
    headers: dict[str, str],
    *,
    team_count: int = 4,
    create_home_stadiums: bool = True,
) -> dict[str, Any]:
    season_id = create_season(client, headers)
    championship_id = create_tournament(
        client,
        headers,
        season_id,
        name="Premier League",
        tournament_type="championship",
    )
    team_ids = [
        create_team(client, headers, f"Team {index}", index)
        for index in range(1, team_count + 1)
    ]
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
    return {
        "season_id": season_id,
        "championship_id": championship_id,
        "team_ids": team_ids,
        "stadium_ids": stadium_ids,
    }


def generate_payload(team_ids: list[int], **overrides: Any) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "start_datetime": "2026-04-01T18:00:00",
        "match_time": "19:30:00",
        "interval_days": 4,
        "team_ids": team_ids,
    }
    payload.update(overrides)
    return payload


def test_generate_championship_schedule_creates_double_round_robin_for_four_teams(
    client: TestClient,
) -> None:
    headers = auth_headers(client)
    context = setup_schedule_context(client, headers)

    response = client.post(
        f"/api/v1/schedule/championships/{context['championship_id']}/generate",
        json=generate_payload(context["team_ids"]),
        headers=headers,
    )

    assert response.status_code == 201
    matches = response.json()
    assert len(matches) == len(context["team_ids"]) * (len(context["team_ids"]) - 1)
    assert {match["round_number"] for match in matches} == set(range(1, 7))
    assert all(
        match["tournament_id"] == context["championship_id"] for match in matches
    )
    assert all(match["season_id"] == context["season_id"] for match in matches)
    assert all(match["status"] == "scheduled" for match in matches)
    assert all(match["ticket_price"] is not None for match in matches)
    assert all("T19:30:00" in match["match_datetime"] for match in matches)

    stadium_by_team_id = dict(
        zip(context["team_ids"], context["stadium_ids"], strict=True)
    )
    for match in matches:
        assert match["stadium_id"] == stadium_by_team_id[match["home_team_id"]]

    unordered_pair_counts = Counter(
        tuple(sorted((match["home_team_id"], match["away_team_id"])))
        for match in matches
    )
    assert len(unordered_pair_counts) == 6
    assert set(unordered_pair_counts.values()) == {2}

    directions_by_pair: dict[tuple[int, int], set[tuple[int, int]]] = defaultdict(set)
    for match in matches:
        pair = tuple(sorted((match["home_team_id"], match["away_team_id"])))
        directions_by_pair[pair].add((match["home_team_id"], match["away_team_id"]))

    for first_team_id, second_team_id in unordered_pair_counts:
        assert directions_by_pair[(first_team_id, second_team_id)] == {
            (first_team_id, second_team_id),
            (second_team_id, first_team_id),
        }


def test_schedule_views_list_season_and_stadium_matches(
    client: TestClient,
) -> None:
    headers = auth_headers(client)
    context = setup_schedule_context(client, headers)
    response = client.post(
        f"/api/v1/schedule/championships/{context['championship_id']}/generate",
        json=generate_payload(context["team_ids"]),
        headers=headers,
    )
    assert response.status_code == 201

    season_response = client.get(
        f"/api/v1/schedule/seasons/{context['season_id']}/matches",
        headers=headers,
    )
    stadium_response = client.get(
        f"/api/v1/schedule/stadiums/{context['stadium_ids'][0]}/matches",
        headers=headers,
    )

    assert season_response.status_code == 200
    assert len(season_response.json()) == 12
    assert stadium_response.status_code == 200
    stadium_matches = stadium_response.json()
    assert len(stadium_matches) == 3
    assert all(
        match["stadium_id"] == context["stadium_ids"][0] for match in stadium_matches
    )
    assert all(
        match["home_team_id"] == context["team_ids"][0] for match in stadium_matches
    )


def test_season_schedule_view_filters_by_team_tournament_and_date_range(
    client: TestClient,
) -> None:
    headers = auth_headers(client)
    context = setup_schedule_context(client, headers)
    response = client.post(
        f"/api/v1/schedule/championships/{context['championship_id']}/generate",
        json=generate_payload(context["team_ids"]),
        headers=headers,
    )
    assert response.status_code == 201
    cup_id = create_tournament(
        client,
        headers,
        context["season_id"],
        name="National Cup",
        tournament_type="cup",
    )
    cup_match = create_match(
        client,
        headers,
        tournament_id=cup_id,
        season_id=context["season_id"],
        home_team_id=context["team_ids"][0],
        away_team_id=context["team_ids"][2],
        stadium_id=context["stadium_ids"][0],
        match_datetime="2026-04-29T18:00:00",
    )

    team_response = client.get(
        f"/api/v1/schedule/seasons/{context['season_id']}/matches",
        params={"team_id": context["team_ids"][0]},
        headers=headers,
    )
    championship_response = client.get(
        f"/api/v1/schedule/seasons/{context['season_id']}/matches",
        params={"tournament_id": context["championship_id"]},
        headers=headers,
    )
    cup_response = client.get(
        f"/api/v1/schedule/seasons/{context['season_id']}/matches",
        params={"tournament_id": cup_id},
        headers=headers,
    )
    date_response = client.get(
        f"/api/v1/schedule/seasons/{context['season_id']}/matches",
        params={"date_from": "2026-04-05", "date_to": "2026-04-13"},
        headers=headers,
    )
    combined_response = client.get(
        f"/api/v1/schedule/seasons/{context['season_id']}/matches",
        params={
            "team_id": context["team_ids"][0],
            "tournament_id": context["championship_id"],
            "date_from": "2026-04-05",
            "date_to": "2026-04-13",
        },
        headers=headers,
    )

    assert team_response.status_code == 200
    assert len(team_response.json()) == 7
    assert all(
        context["team_ids"][0] in {match["home_team_id"], match["away_team_id"]}
        for match in team_response.json()
    )

    assert championship_response.status_code == 200
    assert len(championship_response.json()) == 12
    assert {match["tournament_id"] for match in championship_response.json()} == {
        context["championship_id"]
    }

    assert cup_response.status_code == 200
    assert cup_response.json() == [cup_match]

    assert date_response.status_code == 200
    assert len(date_response.json()) == 6
    assert all(
        "2026-04-05" <= match["match_datetime"][:10] <= "2026-04-13"
        for match in date_response.json()
    )

    assert combined_response.status_code == 200
    assert len(combined_response.json()) == 3
    assert all(
        match["tournament_id"] == context["championship_id"]
        and context["team_ids"][0] in {match["home_team_id"], match["away_team_id"]}
        and "2026-04-05" <= match["match_datetime"][:10] <= "2026-04-13"
        for match in combined_response.json()
    )


def test_generate_championship_schedule_rejects_cup_tournament(
    client: TestClient,
) -> None:
    headers = auth_headers(client)
    context = setup_schedule_context(client, headers)
    cup_id = create_tournament(
        client,
        headers,
        context["season_id"],
        name="National Cup",
        tournament_type="cup",
    )

    response = client.post(
        f"/api/v1/schedule/championships/{cup_id}/generate",
        json=generate_payload(context["team_ids"]),
        headers=headers,
    )

    assert response.status_code == 400


def test_generate_championship_schedule_returns_404_for_missing_tournament(
    client: TestClient,
) -> None:
    headers = auth_headers(client)

    response = client.post(
        "/api/v1/schedule/championships/999/generate",
        json=generate_payload([1, 2]),
        headers=headers,
    )

    assert response.status_code == 404


def test_generate_championship_schedule_returns_404_for_missing_team(
    client: TestClient,
) -> None:
    headers = auth_headers(client)
    context = setup_schedule_context(client, headers, team_count=2)

    response = client.post(
        f"/api/v1/schedule/championships/{context['championship_id']}/generate",
        json=generate_payload([context["team_ids"][0], 999]),
        headers=headers,
    )

    assert response.status_code == 404


def test_generate_championship_schedule_returns_404_for_missing_stadium(
    client: TestClient,
) -> None:
    headers = auth_headers(client)
    context = setup_schedule_context(
        client,
        headers,
        team_count=2,
        create_home_stadiums=False,
    )

    response = client.post(
        f"/api/v1/schedule/championships/{context['championship_id']}/generate",
        json=generate_payload(context["team_ids"], fallback_stadium_id=999),
        headers=headers,
    )

    assert response.status_code == 404


@pytest.mark.parametrize(
    "path",
    [
        "/api/v1/schedule/seasons/999/matches",
        "/api/v1/schedule/stadiums/999/matches",
    ],
)
def test_schedule_views_return_404_for_missing_resources(
    client: TestClient,
    path: str,
) -> None:
    headers = auth_headers(client)

    response = client.get(path, headers=headers)

    assert response.status_code == 404


def test_season_schedule_view_rejects_invalid_filters(
    client: TestClient,
) -> None:
    headers = auth_headers(client)
    context = setup_schedule_context(client, headers)
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
    other_season_id = int(other_season_response.json()["id"])
    other_tournament_id = create_tournament(
        client,
        headers,
        other_season_id,
        name="Other League",
        tournament_type="championship",
    )

    missing_team_response = client.get(
        f"/api/v1/schedule/seasons/{context['season_id']}/matches",
        params={"team_id": 999},
        headers=headers,
    )
    other_tournament_response = client.get(
        f"/api/v1/schedule/seasons/{context['season_id']}/matches",
        params={"tournament_id": other_tournament_id},
        headers=headers,
    )
    invalid_dates_response = client.get(
        f"/api/v1/schedule/seasons/{context['season_id']}/matches",
        params={"date_from": "2026-04-10", "date_to": "2026-04-01"},
        headers=headers,
    )

    assert missing_team_response.status_code == 404
    assert other_tournament_response.status_code == 400
    assert invalid_dates_response.status_code == 400


def test_generate_championship_schedule_rejects_existing_calendar_conflict(
    client: TestClient,
) -> None:
    headers = auth_headers(client)
    context = setup_schedule_context(client, headers)
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
        tournament_id=cup_id,
        season_id=context["season_id"],
        home_team_id=context["team_ids"][0],
        away_team_id=context["team_ids"][1],
        stadium_id=context["stadium_ids"][0],
        match_datetime="2026-04-01T18:00:00",
    )

    response = client.post(
        f"/api/v1/schedule/championships/{context['championship_id']}/generate",
        json=generate_payload(context["team_ids"]),
        headers=headers,
    )
    season_response = client.get(
        f"/api/v1/schedule/seasons/{context['season_id']}/matches",
        headers=headers,
    )

    assert response.status_code == 409
    assert season_response.status_code == 200
    assert len(season_response.json()) == 1


@pytest.mark.parametrize(
    ("method", "path", "json_body"),
    [
        (
            "POST",
            "/api/v1/schedule/championships/1/generate",
            generate_payload([1, 2]),
        ),
        ("GET", "/api/v1/schedule/seasons/1/matches", None),
        ("GET", "/api/v1/schedule/stadiums/1/matches", None),
    ],
)
def test_schedule_endpoints_require_jwt(
    client: TestClient,
    method: str,
    path: str,
    json_body: dict[str, Any] | None,
) -> None:
    response = client.request(method, path, json=json_body)

    assert response.status_code == 401
    assert response.headers["WWW-Authenticate"] == "Bearer"
