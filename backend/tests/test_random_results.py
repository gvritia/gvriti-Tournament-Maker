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


def create_referee(client: TestClient, headers: dict[str, str]) -> int:
    response = client.post(
        "/api/v1/referees/",
        json={"full_name": "Random Result Referee"},
        headers=headers,
    )
    assert response.status_code == 201
    return int(response.json()["id"])


def delete_all_referees(client: TestClient, headers: dict[str, str]) -> None:
    response = client.get("/api/v1/referees/", headers=headers)
    assert response.status_code == 200
    for referee in response.json():
        delete_response = client.delete(
            f"/api/v1/referees/{referee['id']}",
            headers=headers,
        )
        assert delete_response.status_code == 204


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
    match_datetime: str = "2026-04-01T18:00:00",
    stage: str | None = None,
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "tournament_id": tournament_id,
        "season_id": season_id,
        "home_team_id": home_team_id,
        "away_team_id": away_team_id,
        "stadium_id": stadium_id,
        "match_datetime": match_datetime,
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
    with_referee: bool = True,
) -> dict[str, Any]:
    season_id = create_season(client, headers)
    tournament_id = create_tournament(
        client,
        headers,
        season_id,
        tournament_type=tournament_type,
    )
    stadium_id = create_stadium(client, headers)
    if not with_referee:
        delete_all_referees(client, headers)
    referee_id = create_referee(client, headers) if with_referee else None
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
                full_name=f"{prefix} Reserve Goalkeeper",
                number=12,
                position="goalkeeper",
            )
            for number in range(2, 12):
                create_player(
                    client,
                    headers,
                    team_id=team_id,
                    full_name=f"{prefix} Player {number}",
                    number=number,
                    position="midfielder" if number < 8 else "forward",
                )
            for number in range(13, 16):
                create_player(
                    client,
                    headers,
                    team_id=team_id,
                    full_name=f"{prefix} Reserve {number}",
                    number=number,
                    position="defender",
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
        "referee_id": referee_id,
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


def add_match_event(
    client: TestClient,
    headers: dict[str, str],
    *,
    match_id: int,
    team_id: int,
    player_id: int,
    event_type: str,
    minute: int = 10,
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


def get_first_player_id(
    client: TestClient,
    headers: dict[str, str],
    team_id: int,
) -> int:
    offset = 0
    limit = 100
    while True:
        response = client.get(
            f"/api/v1/players/?offset={offset}&limit={limit}",
            headers=headers,
        )
        assert response.status_code == 200
        players = response.json()
        for player in players:
            if player["team_id"] == team_id:
                return int(player["id"])
        if len(players) < limit:
            break
        offset += limit
    raise AssertionError("Expected a player for team.")


def get_first_player_id_by_position(
    client: TestClient,
    headers: dict[str, str],
    team_id: int,
    *,
    position: str,
) -> int:
    offset = 0
    limit = 100
    while True:
        response = client.get(
            f"/api/v1/players/?offset={offset}&limit={limit}",
            headers=headers,
        )
        assert response.status_code == 200
        players = response.json()
        for player in players:
            if player["team_id"] == team_id and player["position"] == position:
                return int(player["id"])
        if len(players) < limit:
            break
        offset += limit
    raise AssertionError(f"Expected a {position} for team.")


def event_counts_by_team(events: list[dict[str, Any]], event_type: str) -> Counter[int]:
    return Counter(
        event["team_id"] for event in events if event["event_type"] == event_type
    )


def assert_generated_protocol_core_data(
    client: TestClient,
    headers: dict[str, str],
    *,
    match: dict[str, Any],
) -> None:
    assert match["referee_id"] is not None

    lineups_response = client.get(
        f"/api/v1/matches/{match['id']}/lineups",
        headers=headers,
    )
    assert lineups_response.status_code == 200
    lineups = lineups_response.json()
    for team_id in (match["home_team_id"], match["away_team_id"]):
        starting_lineups = [
            lineup
            for lineup in lineups
            if lineup["team_id"] == team_id and lineup["is_starting"] is True
        ]
        assert len(starting_lineups) == 11
        assert (
            sum(1 for lineup in starting_lineups if lineup["position"] == "goalkeeper")
            == 1
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
    assert_generated_protocol_core_data(client, headers, match=match)
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

    standings_response = client.get(
        f"/api/v1/standings/seasons/{context['season_id']}",
        headers=headers,
    )
    stats_response = client.get(
        f"/api/v1/statistics/seasons/{context['season_id']}/players",
        headers=headers,
    )

    assert standings_response.status_code == 200
    standings_by_team = {row["team_id"]: row for row in standings_response.json()}
    home_standing = standings_by_team[context["home_team_id"]]
    away_standing = standings_by_team[context["away_team_id"]]
    assert home_standing["played"] == 1
    assert home_standing["goals_scored"] == match["home_score"]
    assert home_standing["goals_conceded"] == match["away_score"]
    assert away_standing["played"] == 1
    assert away_standing["goals_scored"] == match["away_score"]
    assert away_standing["goals_conceded"] == match["home_score"]

    if match["home_score"] > match["away_score"]:
        assert home_standing["points"] == 3
        assert away_standing["points"] == 0
    elif match["home_score"] == match["away_score"]:
        assert home_standing["points"] == 1
        assert away_standing["points"] == 1
    else:
        assert home_standing["points"] == 0
        assert away_standing["points"] == 3

    assert stats_response.status_code == 200
    player_stats = stats_response.json()
    assert sum(row["goals"] for row in player_stats) == (
        match["home_score"] + match["away_score"]
    )
    assert sum(row["assists"] for row in player_stats) == sum(
        1
        for event in events
        if event["event_type"] == "goal" and event["assist_player_id"] is not None
    )
    assert sum(row["saves"] for row in player_stats) == sum(
        1 for event in events if event["event_type"] == "save"
    )
    assert sum(row["yellow_cards"] for row in player_stats) == sum(
        1 for event in events if event["event_type"] == "yellow_card"
    )
    assert sum(row["red_cards"] for row in player_stats) == sum(
        1 for event in events if event["event_type"] == "red_card"
    )


def test_generate_match_protocol_alias_finishes_match(
    client: TestClient,
) -> None:
    headers = auth_headers(client)
    context = setup_random_result_context(client, headers)

    response = client.post(
        f"/api/v1/matches/{context['match']['id']}/generate-protocol",
        json={"seed": 42},
        headers=headers,
    )

    assert response.status_code == 200
    body = response.json()
    assert body["match"]["status"] == "finished"
    assert_generated_protocol_core_data(client, headers, match=body["match"])
    assert body["events"]
    goals_by_team = event_counts_by_team(body["events"], "goal")
    assert goals_by_team[context["home_team_id"]] == body["match"]["home_score"]
    assert goals_by_team[context["away_team_id"]] == body["match"]["away_score"]


def test_generate_season_protocols_finishes_all_matches(
    client: TestClient,
) -> None:
    headers = auth_headers(client)
    context = setup_random_result_context(client, headers)
    second_match = create_match(
        client,
        headers,
        tournament_id=context["tournament_id"],
        season_id=context["season_id"],
        home_team_id=context["away_team_id"],
        away_team_id=context["home_team_id"],
        stadium_id=context["stadium_id"],
        match_datetime="2026-04-08T18:00:00",
    )

    response = client.post(
        f"/api/v1/seasons/{context['season_id']}/generate-protocols",
        json={"seed": 100},
        headers=headers,
    )

    assert response.status_code == 200
    body = response.json()
    assert body["season_id"] == context["season_id"]
    assert body["generated_count"] == 2
    assert {result["match"]["id"] for result in body["results"]} == {
        context["match"]["id"],
        second_match["id"],
    }
    assert all(result["match"]["status"] == "finished" for result in body["results"])
    for result in body["results"]:
        assert_generated_protocol_core_data(client, headers, match=result["match"])
    for result in body["results"]:
        goals_by_team = event_counts_by_team(result["events"], "goal")
        assert (
            goals_by_team[result["match"]["home_team_id"]]
            == result["match"]["home_score"]
        )
        assert (
            goals_by_team[result["match"]["away_team_id"]]
            == result["match"]["away_score"]
        )

    standings_response = client.get(
        f"/api/v1/standings/seasons/{context['season_id']}",
        headers=headers,
    )
    stats_response = client.get(
        f"/api/v1/statistics/seasons/{context['season_id']}/players",
        headers=headers,
    )

    assert standings_response.status_code == 200
    assert {row["played"] for row in standings_response.json()} == {2}

    assert stats_response.status_code == 200
    total_score = sum(
        result["match"]["home_score"] + result["match"]["away_score"]
        for result in body["results"]
    )
    assert sum(row["goals"] for row in stats_response.json()) == total_score


def test_generate_season_protocols_skips_matches_with_existing_protocol(
    client: TestClient,
) -> None:
    headers = auth_headers(client)
    context = setup_random_result_context(client, headers)
    second_match = create_match(
        client,
        headers,
        tournament_id=context["tournament_id"],
        season_id=context["season_id"],
        home_team_id=context["away_team_id"],
        away_team_id=context["home_team_id"],
        stadium_id=context["stadium_id"],
        match_datetime="2026-04-08T18:00:00",
    )
    add_goal_event(
        client,
        headers,
        match_id=second_match["id"],
        team_id=context["away_team_id"],
        player_id=get_first_player_id(client, headers, context["away_team_id"]),
    )

    response = client.post(
        f"/api/v1/seasons/{context['season_id']}/generate-protocols",
        json={"seed": 100},
        headers=headers,
    )
    first_match_response = client.get(
        f"/api/v1/matches/{context['match']['id']}",
        headers=headers,
    )
    first_events_response = client.get(
        f"/api/v1/matches/{context['match']['id']}/events",
        headers=headers,
    )
    second_match_response = client.get(
        f"/api/v1/matches/{second_match['id']}",
        headers=headers,
    )
    second_events_response = client.get(
        f"/api/v1/matches/{second_match['id']}/events",
        headers=headers,
    )

    assert response.status_code == 200
    body = response.json()
    assert body["generated_count"] == 1
    assert [result["match"]["id"] for result in body["results"]] == [
        context["match"]["id"]
    ]
    assert first_match_response.status_code == 200
    assert first_match_response.json()["status"] == "finished"
    assert first_events_response.status_code == 200
    assert first_events_response.json()
    assert second_match_response.status_code == 200
    assert second_match_response.json()["status"] == "scheduled"
    assert second_events_response.status_code == 200
    assert len(second_events_response.json()) == 1


def test_generate_season_protocols_skips_finished_matches(
    client: TestClient,
) -> None:
    headers = auth_headers(client)
    context = setup_random_result_context(client, headers)
    second_match = create_match(
        client,
        headers,
        tournament_id=context["tournament_id"],
        season_id=context["season_id"],
        home_team_id=context["away_team_id"],
        away_team_id=context["home_team_id"],
        stadium_id=context["stadium_id"],
        match_datetime="2026-04-08T18:00:00",
    )
    first_response = client.post(
        f"/api/v1/matches/{context['match']['id']}/generate-protocol",
        json={"seed": 10},
        headers=headers,
    )
    assert first_response.status_code == 200
    first_match_before = first_response.json()["match"]

    response = client.post(
        f"/api/v1/seasons/{context['season_id']}/generate-protocols",
        json={"seed": 100},
        headers=headers,
    )
    first_match_after = client.get(
        f"/api/v1/matches/{context['match']['id']}",
        headers=headers,
    ).json()

    assert response.status_code == 200
    body = response.json()
    assert body["generated_count"] == 1
    assert [result["match"]["id"] for result in body["results"]] == [second_match["id"]]
    assert body["results"][0]["match"]["status"] == "finished"
    assert first_match_after == first_match_before


def test_generate_season_protocols_skips_cancelled_matches(
    client: TestClient,
) -> None:
    headers = auth_headers(client)
    context = setup_random_result_context(client, headers)
    second_match = create_match(
        client,
        headers,
        tournament_id=context["tournament_id"],
        season_id=context["season_id"],
        home_team_id=context["away_team_id"],
        away_team_id=context["home_team_id"],
        stadium_id=context["stadium_id"],
        match_datetime="2026-04-08T18:00:00",
    )
    cancel_response = client.patch(
        f"/api/v1/matches/{context['match']['id']}",
        json={"status": "cancelled"},
        headers=headers,
    )
    assert cancel_response.status_code == 200

    response = client.post(
        f"/api/v1/seasons/{context['season_id']}/generate-protocols",
        json={"seed": 101},
        headers=headers,
    )
    cancelled_match_response = client.get(
        f"/api/v1/matches/{context['match']['id']}",
        headers=headers,
    )

    assert response.status_code == 200
    body = response.json()
    assert body["generated_count"] == 1
    assert [result["match"]["id"] for result in body["results"]] == [second_match["id"]]
    assert body["results"][0]["match"]["status"] == "finished"
    assert cancelled_match_response.status_code == 200
    assert cancelled_match_response.json()["status"] == "cancelled"


def test_generate_match_protocol_uses_substitutes_after_red_card_suspension(
    client: TestClient,
) -> None:
    headers = auth_headers(client)
    context = setup_random_result_context(client, headers)
    second_match = create_match(
        client,
        headers,
        tournament_id=context["tournament_id"],
        season_id=context["season_id"],
        home_team_id=context["home_team_id"],
        away_team_id=context["away_team_id"],
        stadium_id=context["stadium_id"],
        match_datetime="2026-04-03T18:00:00",
    )
    suspended_player_id = get_first_player_id_by_position(
        client,
        headers,
        context["home_team_id"],
        position="midfielder",
    )
    add_match_event(
        client,
        headers,
        match_id=context["match"]["id"],
        team_id=context["home_team_id"],
        player_id=suspended_player_id,
        event_type="red_card",
        minute=80,
    )
    finish_response = client.post(
        f"/api/v1/matches/{context['match']['id']}/finish",
        json={"home_score": 0, "away_score": 0},
        headers=headers,
    )
    assert finish_response.status_code == 200

    response = client.post(
        f"/api/v1/matches/{second_match['id']}/generate-protocol",
        json={"seed": 55},
        headers=headers,
    )
    lineups_response = client.get(
        f"/api/v1/matches/{second_match['id']}/lineups",
        headers=headers,
    )

    assert response.status_code == 200
    assert response.json()["match"]["status"] == "finished"
    assert lineups_response.status_code == 200
    home_starters = [
        lineup
        for lineup in lineups_response.json()
        if lineup["team_id"] == context["home_team_id"]
        and lineup["is_starting"] is True
    ]
    assert len(home_starters) == 11
    assert suspended_player_id not in {lineup["player_id"] for lineup in home_starters}


def test_generate_match_protocol_rejects_invalid_existing_lineup(
    client: TestClient,
) -> None:
    headers = auth_headers(client)
    context = setup_random_result_context(client, headers)
    player_id = get_first_player_id(client, headers, context["home_team_id"])
    lineup_response = client.post(
        f"/api/v1/matches/{context['match']['id']}/lineups",
        json={
            "team_id": context["home_team_id"],
            "player_id": player_id,
            "is_starting": True,
            "position": "forward",
            "number": 99,
        },
        headers=headers,
    )
    assert lineup_response.status_code == 201

    response = client.post(
        f"/api/v1/matches/{context['match']['id']}/generate-protocol",
        json={"seed": 12},
        headers=headers,
    )

    assert response.status_code == 409
    assert (
        response.json()["detail"]
        == "Protocol generation requires each existing team lineup to have "
        "at least 11 starters."
    )


def test_generate_match_protocol_rejects_team_without_goalkeeper(
    client: TestClient,
) -> None:
    headers = auth_headers(client)
    context = setup_random_result_context(client, headers, with_players=False)
    for team_id, prefix in (
        (context["home_team_id"], "Home"),
        (context["away_team_id"], "Away"),
    ):
        for number in range(1, 12):
            create_player(
                client,
                headers,
                team_id=team_id,
                full_name=f"{prefix} Field {number}",
                number=number,
                position="midfielder",
            )

    response = client.post(
        f"/api/v1/matches/{context['match']['id']}/generate-protocol",
        json={"seed": 13},
        headers=headers,
    )

    assert response.status_code == 409
    assert (
        response.json()["detail"]
        == "Protocol generation requires an eligible goalkeeper for each team."
    )


def test_generate_season_protocols_rejects_missing_referee_without_partial_changes(
    client: TestClient,
) -> None:
    headers = auth_headers(client)
    context = setup_random_result_context(client, headers, with_referee=False)
    second_match = create_match(
        client,
        headers,
        tournament_id=context["tournament_id"],
        season_id=context["season_id"],
        home_team_id=context["away_team_id"],
        away_team_id=context["home_team_id"],
        stadium_id=context["stadium_id"],
        match_datetime="2026-04-08T18:00:00",
    )

    response = client.post(
        f"/api/v1/seasons/{context['season_id']}/generate-protocols",
        json={"seed": 77},
        headers=headers,
    )
    first_events_response = client.get(
        f"/api/v1/matches/{context['match']['id']}/events",
        headers=headers,
    )
    second_events_response = client.get(
        f"/api/v1/matches/{second_match['id']}/events",
        headers=headers,
    )

    assert response.status_code == 400
    assert (
        response.json()["detail"]
        == "Protocol generation requires a referee or at least one referee "
        "available for automatic assignment."
    )
    assert first_events_response.status_code == 200
    assert first_events_response.json() == []
    assert second_events_response.status_code == 200
    assert second_events_response.json() == []


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


def test_generate_match_protocol_rejects_missing_referee_pool(
    client: TestClient,
) -> None:
    headers = auth_headers(client)
    context = setup_random_result_context(client, headers, with_referee=False)

    response = client.post(
        f"/api/v1/matches/{context['match']['id']}/generate-protocol",
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
    stats_before = client.get(
        f"/api/v1/statistics/seasons/{context['season_id']}/players",
        headers=headers,
    ).json()
    standings_before = client.get(
        f"/api/v1/standings/seasons/{context['season_id']}",
        headers=headers,
    ).json()

    response = client.post(
        f"/api/v1/matches/{context['match']['id']}/generate-random-result",
        json={"seed": 6},
        headers=headers,
    )

    assert response.status_code == 400
    assert (
        client.get(
            f"/api/v1/statistics/seasons/{context['season_id']}/players",
            headers=headers,
        ).json()
        == stats_before
    )
    assert (
        client.get(
            f"/api/v1/standings/seasons/{context['season_id']}",
            headers=headers,
        ).json()
        == standings_before
    )


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
        (
            "POST",
            "/api/v1/matches/1/generate-protocol",
            {"seed": 1},
        ),
        (
            "POST",
            "/api/v1/seasons/1/generate-protocols",
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
