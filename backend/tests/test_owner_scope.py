from typing import Any

from fastapi.testclient import TestClient

PASSWORD = "StrongPass123"


def auth_headers(client: TestClient, label: str) -> dict[str, str]:
    register_response = client.post(
        "/api/v1/auth/register",
        json={
            "nickname": f"{label}-organizer",
            "email": f"{label}@example.com",
            "password": PASSWORD,
        },
    )
    assert register_response.status_code == 201
    login_response = client.post(
        "/api/v1/auth/login",
        json={"email": f"{label}@example.com", "password": PASSWORD},
    )
    assert login_response.status_code == 200
    return {"Authorization": f"Bearer {login_response.json()['access_token']}"}


def create_season(
    client: TestClient,
    headers: dict[str, str],
    *,
    name: str = "2026",
) -> int:
    response = client.post(
        "/api/v1/seasons/",
        json={
            "name": name,
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
    *,
    season_id: int,
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
    *,
    name: str,
    previous_season_place: int | None = 1,
) -> int:
    payload: dict[str, Any] = {"name": name, "city": "Moscow"}
    if previous_season_place is not None:
        payload["previous_season_place"] = previous_season_place
    response = client.post("/api/v1/teams/", json=payload, headers=headers)
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


def create_referee(client: TestClient, headers: dict[str, str], *, name: str) -> int:
    response = client.post(
        "/api/v1/referees/",
        json={"full_name": name},
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


def create_match(
    client: TestClient,
    headers: dict[str, str],
    *,
    tournament_id: int,
    season_id: int,
    home_team_id: int,
    away_team_id: int,
    stadium_id: int,
    referee_id: int | None = None,
    match_datetime: str = "2026-04-01T18:00:00",
) -> dict[str, Any]:
    response = client.post(
        "/api/v1/matches/",
        json={
            "tournament_id": tournament_id,
            "season_id": season_id,
            "home_team_id": home_team_id,
            "away_team_id": away_team_id,
            "stadium_id": stadium_id,
            "referee_id": referee_id,
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
) -> dict[str, Any]:
    response = client.post(
        f"/api/v1/matches/{match_id}/events",
        json={
            "team_id": team_id,
            "player_id": player_id,
            "event_type": event_type,
            "minute": minute,
        },
        headers=headers,
    )
    assert response.status_code == 201
    return response.json()


def create_match_context(
    client: TestClient,
    headers: dict[str, str],
    *,
    prefix: str,
    season_name: str | None = None,
    team_name: str | None = None,
) -> dict[str, Any]:
    season_id = create_season(
        client,
        headers,
        name=season_name or f"{prefix} 2026",
    )
    tournament_id = create_tournament(
        client,
        headers,
        season_id=season_id,
        name=f"{prefix} Premier League",
    )
    home_team_id = create_team(
        client,
        headers,
        name=team_name or f"{prefix} Home FC",
        previous_season_place=1,
    )
    away_team_id = create_team(
        client,
        headers,
        name=f"{prefix} Away FC",
        previous_season_place=2,
    )
    stadium_id = create_stadium(
        client,
        headers,
        name=f"{prefix} Arena",
        home_team_id=home_team_id,
    )
    referee_id = create_referee(client, headers, name=f"{prefix} Referee")
    home_player_id = create_player(
        client,
        headers,
        team_id=home_team_id,
        full_name=f"{prefix} Home Forward",
        number=9,
    )
    away_player_id = create_player(
        client,
        headers,
        team_id=away_team_id,
        full_name=f"{prefix} Away Forward",
        number=10,
    )
    match = create_match(
        client,
        headers,
        tournament_id=tournament_id,
        season_id=season_id,
        home_team_id=home_team_id,
        away_team_id=away_team_id,
        stadium_id=stadium_id,
        referee_id=referee_id,
    )
    return {
        "season_id": season_id,
        "tournament_id": tournament_id,
        "home_team_id": home_team_id,
        "away_team_id": away_team_id,
        "stadium_id": stadium_id,
        "referee_id": referee_id,
        "home_player_id": home_player_id,
        "away_player_id": away_player_id,
        "match": match,
    }


def ids_from_list(response_json: list[dict[str, Any]]) -> set[int]:
    return {int(item["id"]) for item in response_json}


def test_core_resources_are_scoped_to_current_user(client: TestClient) -> None:
    owner_a = auth_headers(client, "owner-a")
    owner_b = auth_headers(client, "owner-b")
    context_a = create_match_context(
        client,
        owner_a,
        prefix="Shared",
        season_name="Shared 2026",
        team_name="Shared FC",
    )

    season_b_response = client.post(
        "/api/v1/seasons/",
        json={
            "name": "Shared 2026",
            "start_date": "2026-03-01",
            "end_date": "2026-11-30",
        },
        headers=owner_b,
    )
    team_b_response = client.post(
        "/api/v1/teams/",
        json={"name": "Shared FC", "city": "Moscow"},
        headers=owner_b,
    )
    assert season_b_response.status_code == 201
    assert team_b_response.status_code == 201
    season_b_id = season_b_response.json()["id"]
    tournament_b_id = create_tournament(
        client,
        owner_b,
        season_id=season_b_id,
        name="Shared Premier League",
    )

    assert context_a["season_id"] not in ids_from_list(
        client.get("/api/v1/seasons/", headers=owner_b).json()
    )
    assert context_a["home_team_id"] not in ids_from_list(
        client.get("/api/v1/teams/", headers=owner_b).json()
    )
    assert context_a["tournament_id"] not in ids_from_list(
        client.get("/api/v1/tournaments/", headers=owner_b).json()
    )
    assert client.get("/api/v1/matches/", headers=owner_b).json() == []

    actions = [
        ("GET", f"/api/v1/seasons/{context_a['season_id']}", None),
        ("PATCH", f"/api/v1/seasons/{context_a['season_id']}", {"status": "active"}),
        ("DELETE", f"/api/v1/seasons/{context_a['season_id']}", None),
        ("GET", f"/api/v1/teams/{context_a['home_team_id']}", None),
        ("PATCH", f"/api/v1/teams/{context_a['home_team_id']}", {"city": "Kazan"}),
        ("DELETE", f"/api/v1/teams/{context_a['home_team_id']}", None),
        ("GET", f"/api/v1/tournaments/{context_a['tournament_id']}", None),
        (
            "PATCH",
            f"/api/v1/tournaments/{context_a['tournament_id']}",
            {"status": "active"},
        ),
        ("DELETE", f"/api/v1/tournaments/{context_a['tournament_id']}", None),
        ("GET", f"/api/v1/matches/{context_a['match']['id']}", None),
        ("PATCH", f"/api/v1/matches/{context_a['match']['id']}", {"round_number": 2}),
        ("DELETE", f"/api/v1/matches/{context_a['match']['id']}", None),
    ]
    for method, path, json_body in actions:
        response = client.request(method, path, json=json_body, headers=owner_b)
        assert response.status_code == 404

    assert (
        client.get(
            f"/api/v1/seasons/{context_a['season_id']}",
            headers=owner_a,
        ).status_code
        == 200
    )
    assert (
        client.get(
            f"/api/v1/tournaments/{tournament_b_id}",
            headers=owner_b,
        ).status_code
        == 200
    )


def test_related_creation_rejects_foreign_ids(client: TestClient) -> None:
    owner_a = auth_headers(client, "foreign-a")
    owner_b = auth_headers(client, "foreign-b")
    context_a = create_match_context(client, owner_a, prefix="Foreign A")
    context_b = create_match_context(client, owner_b, prefix="Foreign B")

    tournament_response = client.post(
        "/api/v1/tournaments/",
        json={
            "season_id": context_a["season_id"],
            "name": "Foreign Tournament",
            "type": "cup",
        },
        headers=owner_b,
    )
    player_response = client.post(
        "/api/v1/players/",
        json={
            "full_name": "Foreign Player",
            "position": "forward",
            "number": 12,
            "team_id": context_a["home_team_id"],
        },
        headers=owner_b,
    )
    stadium_response = client.post(
        "/api/v1/stadiums/",
        json={
            "name": "Foreign Stadium",
            "city": "Moscow",
            "address": "Foreign street 1",
            "capacity": 30000,
            "home_team_id": context_a["home_team_id"],
        },
        headers=owner_b,
    )
    assert tournament_response.status_code == 404
    assert player_response.status_code == 404
    assert stadium_response.status_code == 404

    base_match_payload = {
        "tournament_id": context_b["tournament_id"],
        "season_id": context_b["season_id"],
        "home_team_id": context_b["home_team_id"],
        "away_team_id": context_b["away_team_id"],
        "stadium_id": context_b["stadium_id"],
        "referee_id": context_b["referee_id"],
        "match_datetime": "2026-04-08T18:00:00",
        "round_number": 1,
    }
    foreign_match_fields = {
        "tournament_id": context_a["tournament_id"],
        "season_id": context_a["season_id"],
        "home_team_id": context_a["home_team_id"],
        "away_team_id": context_a["away_team_id"],
        "stadium_id": context_a["stadium_id"],
        "referee_id": context_a["referee_id"],
    }
    for field, foreign_value in foreign_match_fields.items():
        payload = {**base_match_payload, field: foreign_value}
        response = client.post("/api/v1/matches/", json=payload, headers=owner_b)
        assert response.status_code == 404

    foreign_match_lineup_response = client.post(
        f"/api/v1/matches/{context_a['match']['id']}/lineups",
        json={
            "team_id": context_b["home_team_id"],
            "player_id": context_b["home_player_id"],
            "is_starting": True,
            "position": "forward",
            "number": 9,
        },
        headers=owner_b,
    )
    foreign_player_lineup_response = client.post(
        f"/api/v1/matches/{context_b['match']['id']}/lineups",
        json={
            "team_id": context_b["home_team_id"],
            "player_id": context_a["home_player_id"],
            "is_starting": True,
            "position": "forward",
            "number": 9,
        },
        headers=owner_b,
    )
    assert foreign_match_lineup_response.status_code == 404
    assert foreign_player_lineup_response.status_code == 404

    foreign_match_event_response = client.post(
        f"/api/v1/matches/{context_a['match']['id']}/events",
        json={
            "team_id": context_b["home_team_id"],
            "player_id": context_b["home_player_id"],
            "event_type": "goal",
            "minute": 20,
        },
        headers=owner_b,
    )
    foreign_player_event_response = client.post(
        f"/api/v1/matches/{context_b['match']['id']}/events",
        json={
            "team_id": context_b["home_team_id"],
            "player_id": context_a["home_player_id"],
            "event_type": "goal",
            "minute": 20,
        },
        headers=owner_b,
    )
    random_result_response = client.post(
        f"/api/v1/matches/{context_a['match']['id']}/generate-random-result",
        json={"seed": 10},
        headers=owner_b,
    )
    assert foreign_match_event_response.status_code == 404
    assert foreign_player_event_response.status_code == 404
    assert random_result_response.status_code == 404


def test_schedule_standings_and_statistics_are_user_scoped(
    client: TestClient,
) -> None:
    owner_a = auth_headers(client, "derived-a")
    owner_b = auth_headers(client, "derived-b")
    context_a = create_match_context(client, owner_a, prefix="Derived A")
    context_b = create_match_context(client, owner_b, prefix="Derived B")

    add_event(
        client,
        owner_a,
        match_id=context_a["match"]["id"],
        team_id=context_a["home_team_id"],
        player_id=context_a["home_player_id"],
        event_type="goal",
        minute=30,
    )
    finish_response = client.post(
        f"/api/v1/matches/{context_a['match']['id']}/finish",
        json={"home_score": 1, "away_score": 0},
        headers=owner_a,
    )
    assert finish_response.status_code == 200

    standings_a = client.get(
        f"/api/v1/standings/seasons/{context_a['season_id']}",
        headers=owner_a,
    )
    statistics_a = client.get(
        f"/api/v1/statistics/seasons/{context_a['season_id']}/players",
        headers=owner_a,
    )
    assert standings_a.status_code == 200
    assert statistics_a.status_code == 200
    assert len(standings_a.json()) == 2
    assert statistics_a.json()[0]["player_id"] == context_a["home_player_id"]

    foreign_paths = [
        ("GET", f"/api/v1/schedule/seasons/{context_a['season_id']}/matches"),
        ("GET", f"/api/v1/schedule/stadiums/{context_a['stadium_id']}/matches"),
        ("GET", f"/api/v1/standings/seasons/{context_a['season_id']}"),
        ("POST", f"/api/v1/standings/seasons/{context_a['season_id']}/recalculate"),
        ("GET", f"/api/v1/statistics/seasons/{context_a['season_id']}/players"),
        (
            "POST",
            f"/api/v1/statistics/seasons/{context_a['season_id']}/players/recalculate",
        ),
        ("GET", f"/api/v1/statistics/seasons/{context_a['season_id']}/leaders/goals"),
    ]
    for method, path in foreign_paths:
        response = client.request(method, path, headers=owner_b)
        assert response.status_code == 404

    season_schedule_b = client.get(
        f"/api/v1/schedule/seasons/{context_b['season_id']}/matches",
        headers=owner_b,
    )
    stadium_schedule_b = client.get(
        f"/api/v1/schedule/stadiums/{context_b['stadium_id']}/matches",
        headers=owner_b,
    )
    assert season_schedule_b.status_code == 200
    assert stadium_schedule_b.status_code == 200
    assert [match["id"] for match in season_schedule_b.json()] == [
        context_b["match"]["id"]
    ]
    assert [match["id"] for match in stadium_schedule_b.json()] == [
        context_b["match"]["id"]
    ]


def create_cup_context(
    client: TestClient,
    headers: dict[str, str],
    *,
    prefix: str,
) -> dict[str, Any]:
    season_id = create_season(client, headers, name=f"{prefix} Cup Season")
    cup_id = create_tournament(
        client,
        headers,
        season_id=season_id,
        name=f"{prefix} Cup",
        tournament_type="cup",
    )
    team_ids = [
        create_team(
            client,
            headers,
            name=f"{prefix} Team {index}",
            previous_season_place=index,
        )
        for index in range(1, 5)
    ]
    stadium_ids = [
        create_stadium(
            client,
            headers,
            name=f"{prefix} Team {index} Arena",
            home_team_id=team_id,
        )
        for index, team_id in enumerate(team_ids, start=1)
    ]
    neutral_stadium_id = create_stadium(
        client,
        headers,
        name=f"{prefix} Neutral Arena",
    )
    return {
        "season_id": season_id,
        "cup_id": cup_id,
        "team_ids": team_ids,
        "stadium_ids": stadium_ids,
        "neutral_stadium_id": neutral_stadium_id,
    }


def test_cup_bracket_and_auto_selection_are_user_scoped(
    client: TestClient,
) -> None:
    owner_a = auth_headers(client, "cup-a")
    owner_b = auth_headers(client, "cup-b")
    context_a = create_cup_context(client, owner_a, prefix="Owner A")
    context_b = create_cup_context(client, owner_b, prefix="Owner B")

    response_a = client.post(
        f"/api/v1/cups/{context_a['cup_id']}/semifinals",
        json={
            "team_ids": context_a["team_ids"],
            "match_datetimes": [
                "2026-04-01T18:00:00",
                "2026-04-02T18:00:00",
            ],
        },
        headers=owner_a,
    )
    assert response_a.status_code == 201

    foreign_bracket_response = client.get(
        f"/api/v1/cups/{context_a['cup_id']}/bracket",
        headers=owner_b,
    )
    foreign_semifinal_response = client.post(
        f"/api/v1/cups/{context_a['cup_id']}/semifinals",
        json={
            "team_ids": context_b["team_ids"],
            "match_datetimes": [
                "2026-04-03T18:00:00",
                "2026-04-04T18:00:00",
            ],
        },
        headers=owner_b,
    )
    foreign_final_response = client.post(
        f"/api/v1/cups/{context_a['cup_id']}/final",
        json={
            "match_datetime": "2026-04-08T19:00:00",
            "stadium_id": context_b["neutral_stadium_id"],
        },
        headers=owner_b,
    )
    assert foreign_bracket_response.status_code == 404
    assert foreign_semifinal_response.status_code == 404
    assert foreign_final_response.status_code == 404

    response_b = client.post(
        f"/api/v1/cups/{context_b['cup_id']}/semifinals",
        json={
            "use_previous_season_places": True,
            "match_datetimes": [
                "2026-04-01T18:00:00",
                "2026-04-02T18:00:00",
            ],
        },
        headers=owner_b,
    )
    assert response_b.status_code == 201
    selected_team_ids = {
        team_id
        for match in response_b.json()
        for team_id in (match["home_team_id"], match["away_team_id"])
    }
    assert selected_team_ids == set(context_b["team_ids"])
    assert selected_team_ids.isdisjoint(context_a["team_ids"])
