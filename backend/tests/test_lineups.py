from typing import Any

import pytest
from fastapi.testclient import TestClient


def auth_headers(client: TestClient) -> dict[str, str]:
    client.post(
        "/api/v1/auth/register",
        json={
            "nickname": "lineup-organizer",
            "email": "lineup-organizer@example.com",
            "password": "StrongPass123",
        },
    )
    response = client.post(
        "/api/v1/auth/login",
        json={
            "email": "lineup-organizer@example.com",
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
    position: str = "forward",
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
            "match_datetime": match_datetime,
            "round_number": 1,
        },
        headers=headers,
    )
    assert response.status_code == 201
    return response.json()


def create_lineup_payload(
    *,
    team_id: int,
    player_id: int,
    number: int,
    position: str = "forward",
    is_starting: bool = True,
) -> dict[str, Any]:
    return {
        "team_id": team_id,
        "player_id": player_id,
        "is_starting": is_starting,
        "position": position,
        "number": number,
    }


def add_match_event(
    client: TestClient,
    headers: dict[str, str],
    *,
    match_id: int,
    team_id: int,
    player_id: int,
    event_type: str,
    minute: int,
) -> None:
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


def setup_lineup_context(
    client: TestClient,
    headers: dict[str, str],
    *,
    include_extra_team: bool = False,
) -> dict[str, Any]:
    season_id = create_season(client, headers)
    tournament_id = create_tournament(client, headers, season_id)
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
        full_name="Home Forward",
        number=9,
    )
    second_home_player_id = create_player(
        client,
        headers,
        team_id=home_team_id,
        full_name="Home Winger",
        number=11,
    )
    extra_player_id = (
        create_player(
            client,
            headers,
            team_id=extra_team_id,
            full_name="Extra Forward",
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
        "second_home_player_id": second_home_player_id,
        "extra_player_id": extra_player_id,
        "match": match,
    }


def test_add_list_update_and_delete_lineup(client: TestClient) -> None:
    headers = auth_headers(client)
    context = setup_lineup_context(client, headers)

    create_response = client.post(
        f"/api/v1/matches/{context['match']['id']}/lineups",
        json=create_lineup_payload(
            team_id=context["home_team_id"],
            player_id=context["home_player_id"],
            number=9,
        ),
        headers=headers,
    )
    assert create_response.status_code == 201
    lineup = create_response.json()
    assert lineup["match_id"] == context["match"]["id"]

    list_response = client.get(
        f"/api/v1/matches/{context['match']['id']}/lineups",
        headers=headers,
    )
    assert list_response.status_code == 200
    assert len(list_response.json()) == 1

    update_response = client.patch(
        f"/api/v1/lineups/{lineup['id']}",
        json={"is_starting": False, "position": "winger", "number": 19},
        headers=headers,
    )
    assert update_response.status_code == 200
    assert update_response.json()["is_starting"] is False
    assert update_response.json()["number"] == 19

    get_response = client.get(f"/api/v1/lineups/{lineup['id']}", headers=headers)
    assert get_response.status_code == 200
    assert get_response.json()["position"] == "winger"

    delete_response = client.delete(f"/api/v1/lineups/{lineup['id']}", headers=headers)
    assert delete_response.status_code == 204
    assert (
        client.get(f"/api/v1/lineups/{lineup['id']}", headers=headers).status_code
        == 404
    )


def test_lineup_rejects_team_that_is_not_match_participant(
    client: TestClient,
) -> None:
    headers = auth_headers(client)
    context = setup_lineup_context(client, headers, include_extra_team=True)

    response = client.post(
        f"/api/v1/matches/{context['match']['id']}/lineups",
        json=create_lineup_payload(
            team_id=context["extra_team_id"],
            player_id=context["extra_player_id"],
            number=7,
        ),
        headers=headers,
    )

    assert response.status_code == 400


def test_lineup_rejects_player_from_another_team(client: TestClient) -> None:
    headers = auth_headers(client)
    context = setup_lineup_context(client, headers, include_extra_team=True)

    response = client.post(
        f"/api/v1/matches/{context['match']['id']}/lineups",
        json=create_lineup_payload(
            team_id=context["home_team_id"],
            player_id=context["extra_player_id"],
            number=7,
        ),
        headers=headers,
    )

    assert response.status_code == 400


def test_lineup_rejects_duplicate_player(client: TestClient) -> None:
    headers = auth_headers(client)
    context = setup_lineup_context(client, headers)
    payload = create_lineup_payload(
        team_id=context["home_team_id"],
        player_id=context["home_player_id"],
        number=9,
    )
    create_response = client.post(
        f"/api/v1/matches/{context['match']['id']}/lineups",
        json=payload,
        headers=headers,
    )
    assert create_response.status_code == 201

    response = client.post(
        f"/api/v1/matches/{context['match']['id']}/lineups",
        json=payload,
        headers=headers,
    )

    assert response.status_code == 409


def test_lineup_rejects_duplicate_team_number(client: TestClient) -> None:
    headers = auth_headers(client)
    context = setup_lineup_context(client, headers)
    create_response = client.post(
        f"/api/v1/matches/{context['match']['id']}/lineups",
        json=create_lineup_payload(
            team_id=context["home_team_id"],
            player_id=context["home_player_id"],
            number=10,
        ),
        headers=headers,
    )
    assert create_response.status_code == 201

    response = client.post(
        f"/api/v1/matches/{context['match']['id']}/lineups",
        json=create_lineup_payload(
            team_id=context["home_team_id"],
            player_id=context["second_home_player_id"],
            number=10,
        ),
        headers=headers,
    )

    assert response.status_code == 409


def test_lineup_rejects_suspended_player_after_red_card(
    client: TestClient,
) -> None:
    headers = auth_headers(client)
    context = setup_lineup_context(client, headers)
    next_match = create_match(
        client,
        headers,
        tournament_id=context["tournament_id"],
        season_id=context["season_id"],
        home_team_id=context["home_team_id"],
        away_team_id=context["away_team_id"],
        stadium_id=context["stadium_id"],
        match_datetime="2026-04-03T18:00:00",
    )
    add_match_event(
        client,
        headers,
        match_id=context["match"]["id"],
        team_id=context["home_team_id"],
        player_id=context["home_player_id"],
        event_type="red_card",
        minute=80,
    )

    response = client.post(
        f"/api/v1/matches/{next_match['id']}/lineups",
        json=create_lineup_payload(
            team_id=context["home_team_id"],
            player_id=context["home_player_id"],
            number=9,
        ),
        headers=headers,
    )

    assert response.status_code == 409


def test_generate_lineup_selects_eligible_players(client: TestClient) -> None:
    headers = auth_headers(client)
    context = setup_lineup_context(client, headers)
    goalkeeper_id = create_player(
        client,
        headers,
        team_id=context["home_team_id"],
        full_name="Home Goalkeeper",
        number=1,
        position="goalkeeper",
    )
    defender_id = create_player(
        client,
        headers,
        team_id=context["home_team_id"],
        full_name="Home Defender",
        number=5,
        position="defender",
    )

    response = client.post(
        f"/api/v1/matches/{context['match']['id']}/lineups/generate",
        json={
            "team_id": context["home_team_id"],
            "lineup_size": 3,
            "starting_size": 2,
            "preferred_player_ids": [context["second_home_player_id"]],
        },
        headers=headers,
    )

    assert response.status_code == 201
    lineups = response.json()
    assert len(lineups) == 3
    assert [lineup["is_starting"] for lineup in lineups] == [True, True, False]
    assert lineups[0]["player_id"] == context["second_home_player_id"]
    generated_player_ids = {lineup["player_id"] for lineup in lineups}
    assert goalkeeper_id in generated_player_ids
    assert defender_id in generated_player_ids
    assert len({lineup["number"] for lineup in lineups}) == 3


def test_generate_lineup_starts_exactly_one_goalkeeper_from_preferred_players(
    client: TestClient,
) -> None:
    headers = auth_headers(client)
    context = setup_lineup_context(client, headers)
    first_goalkeeper_id = create_player(
        client,
        headers,
        team_id=context["home_team_id"],
        full_name="First Goalkeeper",
        number=1,
        position="goalkeeper",
    )
    second_goalkeeper_id = create_player(
        client,
        headers,
        team_id=context["home_team_id"],
        full_name="Second Goalkeeper",
        number=12,
        position="goalkeeper",
    )

    response = client.post(
        f"/api/v1/matches/{context['match']['id']}/lineups/generate",
        json={
            "team_id": context["home_team_id"],
            "lineup_size": 4,
            "starting_size": 3,
            "preferred_player_ids": [
                first_goalkeeper_id,
                second_goalkeeper_id,
                context["second_home_player_id"],
            ],
        },
        headers=headers,
    )

    assert response.status_code == 201
    starting_lineups = [
        lineup for lineup in response.json() if lineup["is_starting"] is True
    ]
    assert (
        sum(1 for lineup in starting_lineups if lineup["position"] == "goalkeeper") == 1
    )


def test_generate_lineup_promotes_goalkeeper_into_starting_lineup(
    client: TestClient,
) -> None:
    headers = auth_headers(client)
    context = setup_lineup_context(client, headers)
    goalkeeper_id = create_player(
        client,
        headers,
        team_id=context["home_team_id"],
        full_name="Home Goalkeeper",
        number=1,
        position="goalkeeper",
    )

    response = client.post(
        f"/api/v1/matches/{context['match']['id']}/lineups/generate",
        json={
            "team_id": context["home_team_id"],
            "lineup_size": 3,
            "starting_size": 2,
            "preferred_player_ids": [
                context["home_player_id"],
                context["second_home_player_id"],
            ],
        },
        headers=headers,
    )

    assert response.status_code == 201
    starting_lineups = [
        lineup for lineup in response.json() if lineup["is_starting"] is True
    ]
    assert goalkeeper_id in {lineup["player_id"] for lineup in starting_lineups}
    assert (
        sum(1 for lineup in starting_lineups if lineup["position"] == "goalkeeper") == 1
    )


def test_generate_lineup_replaces_suspended_preferred_player(
    client: TestClient,
) -> None:
    headers = auth_headers(client)
    context = setup_lineup_context(client, headers)
    replacement_player_id = create_player(
        client,
        headers,
        team_id=context["home_team_id"],
        full_name="Home Replacement",
        number=14,
    )
    next_match = create_match(
        client,
        headers,
        tournament_id=context["tournament_id"],
        season_id=context["season_id"],
        home_team_id=context["home_team_id"],
        away_team_id=context["away_team_id"],
        stadium_id=context["stadium_id"],
        match_datetime="2026-04-03T18:00:00",
    )
    add_match_event(
        client,
        headers,
        match_id=context["match"]["id"],
        team_id=context["home_team_id"],
        player_id=context["home_player_id"],
        event_type="red_card",
        minute=80,
    )

    response = client.post(
        f"/api/v1/matches/{next_match['id']}/lineups/generate",
        json={
            "team_id": context["home_team_id"],
            "lineup_size": 2,
            "preferred_player_ids": [context["home_player_id"]],
        },
        headers=headers,
    )

    assert response.status_code == 201
    generated_player_ids = {lineup["player_id"] for lineup in response.json()}
    assert context["home_player_id"] not in generated_player_ids
    assert replacement_player_id in generated_player_ids


def test_generate_lineup_rejects_existing_team_lineup(client: TestClient) -> None:
    headers = auth_headers(client)
    context = setup_lineup_context(client, headers)
    create_response = client.post(
        f"/api/v1/matches/{context['match']['id']}/lineups",
        json=create_lineup_payload(
            team_id=context["home_team_id"],
            player_id=context["home_player_id"],
            number=9,
        ),
        headers=headers,
    )
    assert create_response.status_code == 201

    response = client.post(
        f"/api/v1/matches/{context['match']['id']}/lineups/generate",
        json={"team_id": context["home_team_id"], "lineup_size": 2},
        headers=headers,
    )

    assert response.status_code == 409


def test_generate_lineup_can_replace_existing_team_lineup(
    client: TestClient,
) -> None:
    headers = auth_headers(client)
    context = setup_lineup_context(client, headers)
    create_response = client.post(
        f"/api/v1/matches/{context['match']['id']}/lineups",
        json=create_lineup_payload(
            team_id=context["home_team_id"],
            player_id=context["home_player_id"],
            number=9,
        ),
        headers=headers,
    )
    assert create_response.status_code == 201

    response = client.post(
        f"/api/v1/matches/{context['match']['id']}/lineups/generate",
        json={
            "team_id": context["home_team_id"],
            "lineup_size": 2,
            "replace_existing": True,
        },
        headers=headers,
    )
    list_response = client.get(
        f"/api/v1/matches/{context['match']['id']}/lineups",
        headers=headers,
    )

    assert response.status_code == 201
    assert len(response.json()) == 2
    assert list_response.status_code == 200
    assert len(list_response.json()) == 2


def test_generate_lineup_rejects_wrong_team_preferred_player(
    client: TestClient,
) -> None:
    headers = auth_headers(client)
    context = setup_lineup_context(client, headers, include_extra_team=True)

    response = client.post(
        f"/api/v1/matches/{context['match']['id']}/lineups/generate",
        json={
            "team_id": context["home_team_id"],
            "lineup_size": 2,
            "preferred_player_ids": [context["extra_player_id"]],
        },
        headers=headers,
    )

    assert response.status_code == 400


def test_generate_lineup_rejects_not_enough_eligible_players(
    client: TestClient,
) -> None:
    headers = auth_headers(client)
    context = setup_lineup_context(client, headers)

    response = client.post(
        f"/api/v1/matches/{context['match']['id']}/lineups/generate",
        json={"team_id": context["home_team_id"], "lineup_size": 3},
        headers=headers,
    )

    assert response.status_code == 409


@pytest.mark.parametrize(
    ("method", "path", "json_body"),
    [
        ("GET", "/api/v1/matches/1/lineups", None),
        (
            "POST",
            "/api/v1/matches/1/lineups",
            {
                "team_id": 1,
                "player_id": 1,
                "is_starting": True,
                "position": "forward",
                "number": 9,
            },
        ),
        (
            "POST",
            "/api/v1/matches/1/lineups/generate",
            {"team_id": 1, "lineup_size": 11},
        ),
        ("GET", "/api/v1/lineups/1", None),
        ("PATCH", "/api/v1/lineups/1", {"number": 10}),
        ("DELETE", "/api/v1/lineups/1", None),
    ],
)
def test_lineup_endpoints_require_jwt(
    client: TestClient,
    method: str,
    path: str,
    json_body: dict[str, Any] | None,
) -> None:
    response = client.request(method, path, json=json_body)

    assert response.status_code == 401
    assert response.headers["WWW-Authenticate"] == "Bearer"
