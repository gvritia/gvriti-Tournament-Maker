from fastapi.testclient import TestClient


def auth_headers(client: TestClient) -> dict[str, str]:
    client.post(
        "/api/v1/auth/register",
        json={
            "nickname": "organizer",
            "email": "organizer@example.com",
            "password": "StrongPass123",
        },
    )
    response = client.post(
        "/api/v1/auth/login",
        json={"email": "organizer@example.com", "password": "StrongPass123"},
    )
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_crud_requires_authentication(client: TestClient) -> None:
    response = client.post(
        "/api/v1/teams/",
        json={"name": "Dinamo", "city": "Moscow"},
    )

    assert response.status_code == 401


def test_season_crud_and_conflicts(client: TestClient) -> None:
    headers = auth_headers(client)

    create_response = client.post(
        "/api/v1/seasons/",
        json={
            "name": "2026",
            "start_date": "2026-03-01",
            "end_date": "2026-11-30",
        },
        headers=headers,
    )

    assert create_response.status_code == 201
    season_id = create_response.json()["id"]

    duplicate_response = client.post(
        "/api/v1/seasons/",
        json={
            "name": "2026",
            "start_date": "2026-03-01",
            "end_date": "2026-11-30",
        },
        headers=headers,
    )
    assert duplicate_response.status_code == 409

    list_response = client.get("/api/v1/seasons/", headers=headers)
    assert list_response.status_code == 200
    assert len(list_response.json()) == 1

    update_response = client.patch(
        f"/api/v1/seasons/{season_id}",
        json={"status": "active"},
        headers=headers,
    )
    assert update_response.status_code == 200
    assert update_response.json()["status"] == "active"

    invalid_update_response = client.patch(
        f"/api/v1/seasons/{season_id}",
        json={"end_date": "2026-01-01"},
        headers=headers,
    )
    assert invalid_update_response.status_code == 400

    delete_response = client.delete(f"/api/v1/seasons/{season_id}", headers=headers)
    assert delete_response.status_code == 204
    assert (
        client.get(f"/api/v1/seasons/{season_id}", headers=headers).status_code == 404
    )


def test_season_rollover_reuses_workspace_and_copies_tournaments(
    client: TestClient,
) -> None:
    headers = auth_headers(client)

    source_response = client.post(
        "/api/v1/seasons/",
        json={
            "name": "2026/2027",
            "start_date": "2026-07-01",
            "end_date": "2027-05-31",
            "status": "finished",
        },
        headers=headers,
    )
    source_season_id = source_response.json()["id"]
    championship_response = client.post(
        "/api/v1/tournaments/",
        json={
            "season_id": source_season_id,
            "name": "Championship",
            "type": "championship",
            "status": "finished",
        },
        headers=headers,
    )
    cup_response = client.post(
        "/api/v1/tournaments/",
        json={
            "season_id": source_season_id,
            "name": "Cup",
            "type": "cup",
            "status": "finished",
        },
        headers=headers,
    )
    assert championship_response.status_code == 201
    assert cup_response.status_code == 201

    rollover_response = client.post(
        f"/api/v1/seasons/{source_season_id}/rollover",
        json={
            "name": "2027/2028",
            "start_date": "2027-07-01",
            "end_date": "2028-05-31",
            "copy_tournaments": True,
        },
        headers=headers,
    )

    assert rollover_response.status_code == 201
    payload = rollover_response.json()
    next_season = payload["season"]
    copied_tournaments = payload["tournaments"]
    assert next_season["name"] == "2027/2028"
    assert next_season["status"] == "planned"
    assert {tournament["name"] for tournament in copied_tournaments} == {
        "Championship",
        "Cup",
    }
    assert {tournament["type"] for tournament in copied_tournaments} == {
        "championship",
        "cup",
    }
    assert all(
        tournament["season_id"] == next_season["id"]
        for tournament in copied_tournaments
    )
    assert all(
        tournament["status"] == "planned" for tournament in copied_tournaments
    )

    teams_response = client.get("/api/v1/teams/", headers=headers)
    stadiums_response = client.get("/api/v1/stadiums/", headers=headers)
    assert len(teams_response.json()) == 20
    assert len(stadiums_response.json()) == 20

    duplicate_response = client.post(
        f"/api/v1/seasons/{source_season_id}/rollover",
        json={
            "name": "2027/2028",
            "start_date": "2027-07-01",
            "end_date": "2028-05-31",
        },
        headers=headers,
    )
    assert duplicate_response.status_code == 409


def test_season_rollover_can_skip_tournament_copy(client: TestClient) -> None:
    headers = auth_headers(client)

    source_response = client.post(
        "/api/v1/seasons/",
        json={
            "name": "2026/2027",
            "start_date": "2026-07-01",
            "end_date": "2027-05-31",
        },
        headers=headers,
    )
    source_season_id = source_response.json()["id"]
    client.post(
        "/api/v1/tournaments/",
        json={
            "season_id": source_season_id,
            "name": "Championship",
            "type": "championship",
        },
        headers=headers,
    )

    rollover_response = client.post(
        f"/api/v1/seasons/{source_season_id}/rollover",
        json={
            "name": "2027/2028",
            "start_date": "2027-07-01",
            "end_date": "2028-05-31",
            "copy_tournaments": False,
        },
        headers=headers,
    )

    assert rollover_response.status_code == 201
    assert rollover_response.json()["tournaments"] == []


def test_team_crud(client: TestClient) -> None:
    headers = auth_headers(client)

    create_response = client.post(
        "/api/v1/teams/",
        json={
            "name": "Dinamo",
            "city": "Moscow",
            "manager_name": "Ivan Petrov",
            "emblem_url": "https://example.com/dinamo.png",
            "previous_season_place": 2,
        },
        headers=headers,
    )

    assert create_response.status_code == 201
    assert create_response.json()["emblem_url"] == "https://example.com/dinamo.png"
    team_id = create_response.json()["id"]

    duplicate_response = client.post(
        "/api/v1/teams/",
        json={"name": "Dinamo", "city": "Moscow"},
        headers=headers,
    )
    assert duplicate_response.status_code == 409

    update_response = client.patch(
        f"/api/v1/teams/{team_id}",
        json={
            "city": "Saint Petersburg",
            "emblem_url": "https://example.com/dinamo-new.png",
        },
        headers=headers,
    )
    assert update_response.status_code == 200
    assert update_response.json()["city"] == "Saint Petersburg"
    assert update_response.json()["emblem_url"] == "https://example.com/dinamo-new.png"

    invalid_emblem_response = client.patch(
        f"/api/v1/teams/{team_id}",
        json={"emblem_url": "not-a-url"},
        headers=headers,
    )
    assert invalid_emblem_response.status_code == 422

    assert client.delete(f"/api/v1/teams/{team_id}", headers=headers).status_code == 204
    assert client.get(f"/api/v1/teams/{team_id}", headers=headers).status_code == 404


def test_player_crud_validates_team_and_number(client: TestClient) -> None:
    headers = auth_headers(client)

    missing_team_response = client.post(
        "/api/v1/players/",
        json={
            "full_name": "Alex Forward",
            "age": 24,
            "position": "forward",
            "number": 9,
            "team_id": 999,
        },
        headers=headers,
    )
    assert missing_team_response.status_code == 404

    team_response = client.post(
        "/api/v1/teams/",
        json={"name": "Spartak", "city": "Moscow"},
        headers=headers,
    )
    team_id = team_response.json()["id"]

    create_response = client.post(
        "/api/v1/players/",
        json={
            "full_name": "Alex Forward",
            "age": 24,
            "position": "forward",
            "number": 9,
            "team_id": team_id,
        },
        headers=headers,
    )
    assert create_response.status_code == 201
    player_id = create_response.json()["id"]

    duplicate_number_response = client.post(
        "/api/v1/players/",
        json={
            "full_name": "Second Forward",
            "age": 25,
            "position": "forward",
            "number": 9,
            "team_id": team_id,
        },
        headers=headers,
    )
    assert duplicate_number_response.status_code == 409

    update_response = client.patch(
        f"/api/v1/players/{player_id}",
        json={"number": 10},
        headers=headers,
    )
    assert update_response.status_code == 200
    assert update_response.json()["number"] == 10

    assert (
        client.delete(f"/api/v1/players/{player_id}", headers=headers).status_code
        == 204
    )


def test_stadium_crud_validates_home_team(client: TestClient) -> None:
    headers = auth_headers(client)

    missing_team_response = client.post(
        "/api/v1/stadiums/",
        json={
            "name": "National Arena",
            "city": "Moscow",
            "address": "Main street 1",
            "capacity": 50000,
            "home_team_id": 999,
        },
        headers=headers,
    )
    assert missing_team_response.status_code == 404

    team_response = client.post(
        "/api/v1/teams/",
        json={"name": "Lokomotiv", "city": "Moscow"},
        headers=headers,
    )
    team_id = team_response.json()["id"]

    create_response = client.post(
        "/api/v1/stadiums/",
        json={
            "name": "National Arena",
            "city": "Moscow",
            "address": "Main street 1",
            "capacity": 50000,
            "home_team_id": team_id,
        },
        headers=headers,
    )
    assert create_response.status_code == 201
    stadium_id = create_response.json()["id"]

    duplicate_response = client.post(
        "/api/v1/stadiums/",
        json={
            "name": "National Arena",
            "city": "Moscow",
            "address": "Second street 2",
            "capacity": 30000,
        },
        headers=headers,
    )
    assert duplicate_response.status_code == 409

    update_response = client.patch(
        f"/api/v1/stadiums/{stadium_id}",
        json={"home_team_id": None, "capacity": 55000},
        headers=headers,
    )
    assert update_response.status_code == 200
    assert update_response.json()["home_team_id"] is None
    assert update_response.json()["capacity"] == 55000

    assert (
        client.delete(f"/api/v1/stadiums/{stadium_id}", headers=headers).status_code
        == 204
    )


def test_referee_crud(client: TestClient) -> None:
    headers = auth_headers(client)

    create_response = client.post(
        "/api/v1/referees/",
        json={"full_name": "Sergey Ivanov"},
        headers=headers,
    )

    assert create_response.status_code == 201
    referee_id = create_response.json()["id"]

    duplicate_response = client.post(
        "/api/v1/referees/",
        json={"full_name": "Sergey Ivanov"},
        headers=headers,
    )
    assert duplicate_response.status_code == 409

    update_response = client.patch(
        f"/api/v1/referees/{referee_id}",
        json={"full_name": "Alexey Ivanov"},
        headers=headers,
    )
    assert update_response.status_code == 200
    assert update_response.json()["full_name"] == "Alexey Ivanov"

    assert (
        client.delete(f"/api/v1/referees/{referee_id}", headers=headers).status_code
        == 204
    )
    assert (
        client.get(f"/api/v1/referees/{referee_id}", headers=headers).status_code == 404
    )


def test_tournament_crud_validates_season_and_name(client: TestClient) -> None:
    headers = auth_headers(client)

    missing_season_response = client.post(
        "/api/v1/tournaments/",
        json={
            "season_id": 999,
            "name": "Premier League",
            "type": "championship",
        },
        headers=headers,
    )
    assert missing_season_response.status_code == 404

    season_response = client.post(
        "/api/v1/seasons/",
        json={
            "name": "2026",
            "start_date": "2026-03-01",
            "end_date": "2026-11-30",
        },
        headers=headers,
    )
    season_id = season_response.json()["id"]

    create_response = client.post(
        "/api/v1/tournaments/",
        json={
            "season_id": season_id,
            "name": "Premier League",
            "type": "championship",
        },
        headers=headers,
    )
    assert create_response.status_code == 201
    tournament_id = create_response.json()["id"]

    duplicate_response = client.post(
        "/api/v1/tournaments/",
        json={
            "season_id": season_id,
            "name": "Premier League",
            "type": "cup",
        },
        headers=headers,
    )
    assert duplicate_response.status_code == 409

    update_response = client.patch(
        f"/api/v1/tournaments/{tournament_id}",
        json={"status": "active"},
        headers=headers,
    )
    assert update_response.status_code == 200
    assert update_response.json()["status"] == "active"

    assert (
        client.delete(
            f"/api/v1/tournaments/{tournament_id}", headers=headers
        ).status_code
        == 204
    )
    assert (
        client.get(f"/api/v1/tournaments/{tournament_id}", headers=headers).status_code
        == 404
    )
