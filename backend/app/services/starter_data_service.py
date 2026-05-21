from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.constants import PlayerPosition
from app.models.player import Player
from app.models.referee import Referee
from app.models.stadium import Stadium
from app.models.team import Team

DEFAULT_STADIUM_CAPACITY = 50000
DEFAULT_STARTER_REFEREES: tuple[str, ...] = (
    "Alejandro Hernandez",
    "Ricardo de Burgos",
    "Jose Luis Munuera",
    "Cesar Soto",
    "Jesus Gil",
    "Javier Alberola",
    "Miguel Ortiz",
    "Guillermo Cuadra",
)


@dataclass(frozen=True)
class StarterClub:
    name: str
    city: str
    stadium: str
    stadium_address: str
    manager_name: str
    emblem_url: str


@dataclass(frozen=True)
class StarterPlayer:
    name_suffix: str
    number: int
    position: PlayerPosition
    age: int


DEFAULT_STARTER_PLAYERS: tuple[StarterPlayer, ...] = (
    StarterPlayer("Goalkeeper", 1, PlayerPosition.GOALKEEPER, 27),
    StarterPlayer("Right Back", 2, PlayerPosition.DEFENDER, 24),
    StarterPlayer("Centre Back", 3, PlayerPosition.DEFENDER, 28),
    StarterPlayer("Left Back", 4, PlayerPosition.DEFENDER, 25),
    StarterPlayer("Stopper", 5, PlayerPosition.DEFENDER, 29),
    StarterPlayer("Holding Midfielder", 6, PlayerPosition.MIDFIELDER, 26),
    StarterPlayer("Central Midfielder", 7, PlayerPosition.MIDFIELDER, 23),
    StarterPlayer("Playmaker", 8, PlayerPosition.MIDFIELDER, 27),
    StarterPlayer("Right Forward", 9, PlayerPosition.FORWARD, 24),
    StarterPlayer("Striker", 10, PlayerPosition.FORWARD, 28),
    StarterPlayer("Left Forward", 11, PlayerPosition.FORWARD, 22),
    StarterPlayer("Reserve Goalkeeper", 12, PlayerPosition.GOALKEEPER, 23),
    StarterPlayer("Reserve Defender", 13, PlayerPosition.DEFENDER, 22),
    StarterPlayer("Reserve Full Back", 14, PlayerPosition.DEFENDER, 21),
    StarterPlayer("Reserve Midfielder", 15, PlayerPosition.MIDFIELDER, 24),
    StarterPlayer("Utility Midfielder", 16, PlayerPosition.MIDFIELDER, 20),
    StarterPlayer("Reserve Winger", 17, PlayerPosition.FORWARD, 21),
    StarterPlayer("Reserve Striker", 18, PlayerPosition.FORWARD, 25),
)


DEFAULT_STARTER_CLUBS: tuple[StarterClub, ...] = (
    StarterClub(
        name="Barcelona",
        city="Barcelona",
        stadium="Camp Nou",
        stadium_address="Les Corts, 08028",
        manager_name="H. Flick",
        emblem_url="https://media.api-sports.io/football/teams/529.png",
    ),
    StarterClub(
        name="Atletico Madrid",
        city="Madrid",
        stadium="Estadio Civitas Metropolitano",
        stadium_address="Rosas",
        manager_name="D. Simeone",
        emblem_url="https://media.api-sports.io/football/teams/530.png",
    ),
    StarterClub(
        name="Athletic Club",
        city="Bilbao",
        stadium="San Mames Barria",
        stadium_address="Rafael Moreno Pitxitxi Kalea",
        manager_name="Ernesto Valverde",
        emblem_url="https://media.api-sports.io/football/teams/531.png",
    ),
    StarterClub(
        name="Valencia",
        city="Valencia",
        stadium="Estadio de Mestalla",
        stadium_address="Avenida de Suecia",
        manager_name="Carlos Corberan",
        emblem_url="https://media.api-sports.io/football/teams/532.png",
    ),
    StarterClub(
        name="Villarreal",
        city="Villarreal",
        stadium="Estadio de la Ceramica",
        stadium_address="Plaza Labrador",
        manager_name="Marcelino",
        emblem_url="https://media.api-sports.io/football/teams/533.png",
    ),
    StarterClub(
        name="Las Palmas",
        city="Las Palmas de Gran Canaria",
        stadium="Estadio de Gran Canaria",
        stadium_address="Avenida Pio XII 29",
        manager_name="Diego Martinez",
        emblem_url="https://media.api-sports.io/football/teams/534.png",
    ),
    StarterClub(
        name="Sevilla",
        city="Sevilla",
        stadium="Estadio Ramon Sanchez Pizjuan",
        stadium_address="Avenida de Eduardo Dato",
        manager_name="M. Almeyda",
        emblem_url="https://media.api-sports.io/football/teams/536.png",
    ),
    StarterClub(
        name="Leganes",
        city="Leganes",
        stadium="Estadio Municipal de Butarque",
        stadium_address="Calle Arquitectura",
        manager_name="Borja Jimenez",
        emblem_url="https://media.api-sports.io/football/teams/537.png",
    ),
    StarterClub(
        name="Celta Vigo",
        city="Vigo",
        stadium="Abanca-Balaidos",
        stadium_address="Avenida de Balaidos",
        manager_name="Claudio Giraldez",
        emblem_url="https://media.api-sports.io/football/teams/538.png",
    ),
    StarterClub(
        name="Espanyol",
        city="Cornella de Llobregat",
        stadium="Stage Front Stadium",
        stadium_address="Avenida Baix Llobregat 100",
        manager_name="Manolo Gonzalez",
        emblem_url="https://media.api-sports.io/football/teams/540.png",
    ),
    StarterClub(
        name="Real Madrid",
        city="Madrid",
        stadium="Estadio Santiago Bernabeu",
        stadium_address="Avenida de Concha Espina 1, Chamartin",
        manager_name="Xabi Alonso",
        emblem_url="https://media.api-sports.io/football/teams/541.png",
    ),
    StarterClub(
        name="Alaves",
        city="Vitoria-Gasteiz",
        stadium="Estadio de Mendizorroza",
        stadium_address="Paseo de Cervantes",
        manager_name="Quique Sanchez Flores",
        emblem_url="https://media.api-sports.io/football/teams/542.png",
    ),
    StarterClub(
        name="Real Betis",
        city="Sevilla",
        stadium="Estadio Benito Villamarin",
        stadium_address="Avenida de Heliopolis",
        manager_name="M. Pellegrini",
        emblem_url="https://media.api-sports.io/football/teams/543.png",
    ),
    StarterClub(
        name="Getafe",
        city="Getafe",
        stadium="Estadio Coliseum",
        stadium_address="Avenida de Teresa de Calcuta",
        manager_name="Jose Bordalas",
        emblem_url="https://media.api-sports.io/football/teams/546.png",
    ),
    StarterClub(
        name="Girona",
        city="Girona",
        stadium="Estadi Municipal de Montilivi",
        stadium_address="Avenida Montlivi 141",
        manager_name="Michel",
        emblem_url="https://media.api-sports.io/football/teams/547.png",
    ),
    StarterClub(
        name="Real Sociedad",
        city="Donostia-San Sebastian",
        stadium="Reale Arena",
        stadium_address="Paseo de Anoeta 1",
        manager_name="Sergio Francisco",
        emblem_url="https://media.api-sports.io/football/teams/548.png",
    ),
    StarterClub(
        name="Valladolid",
        city="Valladolid",
        stadium="Estadio Municipal Jose Zorrilla",
        stadium_address="Avenida del Mundial 82",
        manager_name="G. Almada",
        emblem_url="https://media.api-sports.io/football/teams/720.png",
    ),
    StarterClub(
        name="Osasuna",
        city="Irunea",
        stadium="Estadio El Sadar",
        stadium_address="Carretera El Sadar",
        manager_name="A. Lisci",
        emblem_url="https://media.api-sports.io/football/teams/727.png",
    ),
    StarterClub(
        name="Rayo Vallecano",
        city="Madrid",
        stadium="Estadio de Vallecas",
        stadium_address="Calle Payaso Fofo",
        manager_name="Inigo Perez",
        emblem_url="https://media.api-sports.io/football/teams/728.png",
    ),
    StarterClub(
        name="Mallorca",
        city="Palma de Mallorca",
        stadium="Estadi Mallorca Son Moix",
        stadium_address="Cami dels Reis",
        manager_name="Arrasate",
        emblem_url="https://media.api-sports.io/football/teams/798.png",
    ),
)


class StarterDataService:
    def __init__(
        self,
        db: Session,
        *,
        default_stadium_capacity: int = DEFAULT_STADIUM_CAPACITY,
    ) -> None:
        self.db = db
        self.default_stadium_capacity = default_stadium_capacity

    def seed_for_new_owner(self, *, owner_id: int) -> None:
        existing_team = self.db.scalar(
            select(Team.id).where(Team.owner_id == owner_id).limit(1)
        )
        if existing_team is not None:
            self._seed_referees_for_owner(owner_id=owner_id)
            self.db.flush()
            return

        for previous_place, club in enumerate(DEFAULT_STARTER_CLUBS, start=1):
            team = Team(
                owner_id=owner_id,
                name=club.name,
                city=club.city,
                address=club.stadium_address,
                manager_name=club.manager_name,
                emblem_url=club.emblem_url,
                previous_season_place=previous_place,
            )
            self.db.add(team)
            self.db.flush()
            self._seed_players_for_team(owner_id=owner_id, team=team)
            self.db.add(
                Stadium(
                    owner_id=owner_id,
                    name=club.stadium,
                    city=club.city,
                    address=club.stadium_address,
                    capacity=self.default_stadium_capacity,
                    home_team_id=team.id,
                )
            )
        self.db.flush()
        self._seed_referees_for_owner(owner_id=owner_id)
        self.db.flush()

    def _seed_players_for_team(self, *, owner_id: int, team: Team) -> None:
        for player in DEFAULT_STARTER_PLAYERS:
            self.db.add(
                Player(
                    owner_id=owner_id,
                    full_name=f"{team.name} {player.name_suffix}",
                    age=player.age,
                    position=player.position,
                    number=player.number,
                    team_id=team.id,
                )
            )

    def _seed_referees_for_owner(self, *, owner_id: int) -> None:
        existing_referee = self.db.scalar(
            select(Referee.id).where(Referee.owner_id == owner_id).limit(1)
        )
        if existing_referee is not None:
            return

        for full_name in DEFAULT_STARTER_REFEREES:
            self.db.add(Referee(owner_id=owner_id, full_name=full_name))
