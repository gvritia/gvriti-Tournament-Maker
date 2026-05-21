export type TeamPreview = {
  id: string;
  name: string;
  shortName: string;
  city: string;
  address: string;
  manager: string;
  previousSeasonPlace: number;
  stadiumName: string;
};

export type PlayerPreview = {
  id: string;
  teamId: string;
  name: string;
  position: string;
  number: number;
  age: number;
};

export type MatchStatus = "scheduled" | "finished";

export type MatchPreview = {
  id: string;
  tournament: string;
  date: string;
  homeTeamId: string;
  awayTeamId: string;
  status: MatchStatus;
  statusLabel: string;
  stadium: string;
  referee: string;
  ticketPrice: string;
  homeScore?: number;
  awayScore?: number;
};

export const previewTeams: TeamPreview[] = [
  {
    id: "lions",
    name: "North Lions",
    shortName: "NL",
    city: "Санкт-Петербург",
    address: "Набережная лига, 14",
    manager: "Алексей Волков",
    previousSeasonPlace: 1,
    stadiumName: "North Arena",
  },
  {
    id: "steel",
    name: "Steel United",
    shortName: "SU",
    city: "Екатеринбург",
    address: "Проспект чемпионов, 8",
    manager: "Илья Серов",
    previousSeasonPlace: 2,
    stadiumName: "Steel Park",
  },
  {
    id: "river",
    name: "River City",
    shortName: "RC",
    city: "Казань",
    address: "Улица стадионная, 3",
    manager: "Дамир Халиков",
    previousSeasonPlace: 3,
    stadiumName: "River Ground",
  },
  {
    id: "atlas",
    name: "Atlas FC",
    shortName: "AF",
    city: "Москва",
    address: "Южный проспект, 27",
    manager: "Михаил Орлов",
    previousSeasonPlace: 4,
    stadiumName: "Atlas Bowl",
  },
];

export const previewPlayers: PlayerPreview[] = [
  {
    id: "p1",
    teamId: "lions",
    name: "Никита Лапин",
    position: "Goalkeeper",
    number: 1,
    age: 29,
  },
  {
    id: "p2",
    teamId: "lions",
    name: "Матвей Романов",
    position: "Defender",
    number: 4,
    age: 25,
  },
  {
    id: "p3",
    teamId: "lions",
    name: "Олег Климов",
    position: "Midfielder",
    number: 8,
    age: 27,
  },
  {
    id: "p4",
    teamId: "lions",
    name: "Даниил Светлов",
    position: "Forward",
    number: 11,
    age: 23,
  },
  {
    id: "p5",
    teamId: "steel",
    name: "Павел Громов",
    position: "Goalkeeper",
    number: 1,
    age: 31,
  },
  {
    id: "p6",
    teamId: "steel",
    name: "Егор Белов",
    position: "Forward",
    number: 9,
    age: 26,
  },
];

export const previewMatches: MatchPreview[] = [
  {
    id: "m1",
    tournament: "Championship",
    date: "2026-06-03 19:30",
    homeTeamId: "lions",
    awayTeamId: "steel",
    status: "scheduled",
    statusLabel: "scheduled",
    stadium: "North Arena",
    referee: "не назначен",
    ticketPrice: "45.00",
  },
  {
    id: "m2",
    tournament: "Cup semifinal",
    date: "2026-06-05 20:00",
    homeTeamId: "river",
    awayTeamId: "atlas",
    status: "finished",
    statusLabel: "finished",
    stadium: "River Ground",
    referee: "Иван Морозов",
    ticketPrice: "38.50",
    homeScore: 2,
    awayScore: 1,
  },
  {
    id: "m3",
    tournament: "Championship",
    date: "2026-06-08 18:00",
    homeTeamId: "atlas",
    awayTeamId: "lions",
    status: "scheduled",
    statusLabel: "scheduled",
    stadium: "Atlas Bowl",
    referee: "Мария Соколова",
    ticketPrice: "42.00",
  },
];

export const previewStandings = [
  {
    place: 1,
    teamId: "lions",
    played: 10,
    wins: 7,
    draws: 2,
    losses: 1,
    goalsScored: 21,
    goalsConceded: 8,
    goalDifference: 13,
    points: 23,
  },
  {
    place: 2,
    teamId: "steel",
    played: 10,
    wins: 6,
    draws: 1,
    losses: 3,
    goalsScored: 18,
    goalsConceded: 12,
    goalDifference: 6,
    points: 19,
  },
  {
    place: 3,
    teamId: "river",
    played: 10,
    wins: 5,
    draws: 3,
    losses: 2,
    goalsScored: 16,
    goalsConceded: 13,
    goalDifference: 3,
    points: 18,
  },
];

export function getTeamName(teamId: string) {
  return previewTeams.find((team) => team.id === teamId)?.name ?? "Unknown team";
}
