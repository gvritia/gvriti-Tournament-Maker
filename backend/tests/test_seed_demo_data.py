from pathlib import Path

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.constants import CupStage, PlayerPosition, TournamentType
from app.models.match import Match
from app.models.player import Player
from app.models.referee import Referee
from app.models.stadium import Stadium
from app.models.team import Team
from app.models.tournament import Tournament
from app.models.user import User
from app.scripts.seed_demo_data import (
    DemoDataSeeder,
    read_clubs_csv,
    read_squads_csv,
)


def write_demo_csvs(tmp_path: Path) -> tuple[Path, Path]:
    clubs_csv = tmp_path / "clubs.csv"
    clubs_csv.write_text(
        "\n".join(
            [
                "club_id;club_name;city;stadium;stadium_address;coach;founded;country;logo;squad",
                "1;Alpha FC;Madrid;Alpha Arena;Alpha Street;Coach A;1901;Spain;https://example.com/alpha.png;",
                "2;Beta FC;Barcelona;Beta Arena;Beta Street;Coach B;1902;Spain;https://example.com/beta.png;",
                "3;Gamma FC;Sevilla;Gamma Arena;Gamma Street;Coach C;1903;Spain;https://example.com/gamma.png;",
                "4;Delta FC;Valencia;Delta Arena;Delta Street;Coach D;1904;Spain;https://example.com/delta.png;",
            ]
        ),
        encoding="utf-8",
    )
    squads_csv = tmp_path / "squads.csv"
    squads_csv.write_text(
        "\n".join(
            [
                "club_id;club_name;player_id;player_name;age;number;position",
                "1;Alpha FC;101;Alpha Keeper;24.0;1;Goalkeeper",
                "1;Alpha FC;102;Alpha Forward;27.0;9;Attacker",
                "1;Alpha FC;103;Alpha Duplicate Number;18.0;9;Midfielder",
                "2;Beta FC;201;Beta Defender;25.0;4;Defender",
                "2;Beta FC;202;Beta Forward;22.0;11;Attacker",
                "3;Gamma FC;301;Gamma Midfielder;30.0;8;Midfielder",
                "3;Gamma FC;302;Gamma Forward;21.0;10;Attacker",
                "4;Delta FC;401;Delta Keeper;20.0;1;Goalkeeper",
                "4;Delta FC;402;Delta Defender;29.0;5;Defender",
            ]
        ),
        encoding="utf-8",
    )
    return clubs_csv, squads_csv


def test_demo_seed_csv_readers_parse_semicolon_files(tmp_path: Path) -> None:
    clubs_csv, squads_csv = write_demo_csvs(tmp_path)

    clubs = read_clubs_csv(clubs_csv)
    players = read_squads_csv(squads_csv)

    assert len(clubs) == 4
    assert clubs[0].club_name == "Alpha FC"
    assert clubs[0].coach == "Coach A"
    assert clubs[0].logo == "https://example.com/alpha.png"
    assert len(players) == 9
    assert players[1].age == 27
    assert players[1].position == PlayerPosition.FORWARD


def test_demo_seed_csv_readers_accept_tab_files(tmp_path: Path) -> None:
    clubs_csv = tmp_path / "clubs.tsv"
    clubs_csv.write_text(
        "\n".join(
            [
                "club_id\tclub_name\tcity\tstadium\tstadium_address\tcoach\tlogo",
                "529\tBarcelona\tBarcelona\tCamp Nou\tLes Corts\tH. Flick\thttps://media.api-sports.io/football/teams/529.png",
            ]
        ),
        encoding="utf-8",
    )

    clubs = read_clubs_csv(clubs_csv)

    assert len(clubs) == 1
    assert clubs[0].club_name == "Barcelona"
    assert clubs[0].logo == "https://media.api-sports.io/football/teams/529.png"


def test_demo_data_seeder_is_idempotent_and_resolves_duplicate_numbers(
    db_session: Session,
    tmp_path: Path,
) -> None:
    clubs_csv, squads_csv = write_demo_csvs(tmp_path)
    seeder = DemoDataSeeder(db_session, default_stadium_capacity=30000)

    first_summary = seeder.seed_from_csv(clubs_csv=clubs_csv, squads_csv=squads_csv)
    second_summary = seeder.seed_from_csv(clubs_csv=clubs_csv, squads_csv=squads_csv)

    assert first_summary == second_summary
    assert second_summary.seasons == 1
    assert second_summary.tournaments == 2
    assert second_summary.teams == 4
    assert second_summary.stadiums == 4
    assert second_summary.players == 9
    assert second_summary.referees == 8
    assert second_summary.matches == 2

    owner = db_session.scalar(select(User).where(User.email == "demo@example.com"))
    assert owner is not None

    teams = list(db_session.scalars(select(Team).order_by(Team.previous_season_place)))
    assert {team.owner_id for team in teams} == {owner.id}
    assert [team.name for team in teams] == [
        "Alpha FC",
        "Beta FC",
        "Gamma FC",
        "Delta FC",
    ]
    assert [team.previous_season_place for team in teams] == [1, 2, 3, 4]
    assert [team.emblem_url for team in teams] == [
        "https://example.com/alpha.png",
        "https://example.com/beta.png",
        "https://example.com/gamma.png",
        "https://example.com/delta.png",
    ]

    stadiums = list(db_session.scalars(select(Stadium).order_by(Stadium.name)))
    assert len(stadiums) == 4
    assert {stadium.owner_id for stadium in stadiums} == {owner.id}
    assert {stadium.capacity for stadium in stadiums} == {30000}
    assert {stadium.home_team_id for stadium in stadiums} == {team.id for team in teams}

    tournaments = list(db_session.scalars(select(Tournament).order_by(Tournament.type)))
    assert {tournament.owner_id for tournament in tournaments} == {owner.id}
    assert {tournament.type for tournament in tournaments} == {
        TournamentType.CHAMPIONSHIP,
        TournamentType.CUP,
    }

    alpha_team_id = teams[0].id
    alpha_numbers = sorted(
        player.number
        for player in db_session.scalars(
            select(Player).where(Player.team_id == alpha_team_id)
        )
    )
    assert alpha_numbers == [1, 2, 9]

    referees = list(db_session.scalars(select(Referee)))
    assert {referee.owner_id for referee in referees} == {owner.id}
    assert len(referees) == 8

    cup_matches = list(db_session.scalars(select(Match).order_by(Match.id)))
    assert {match.owner_id for match in cup_matches} == {owner.id}
    assert [match.stage for match in cup_matches] == [
        CupStage.SEMIFINAL,
        CupStage.SEMIFINAL,
    ]
    assert [(match.home_team_id, match.away_team_id) for match in cup_matches] == [
        (teams[0].id, teams[3].id),
        (teams[1].id, teams[2].id),
    ]
