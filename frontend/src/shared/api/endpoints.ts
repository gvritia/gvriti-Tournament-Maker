import { apiRequest, getAllPages } from "./client";
import type {
  Match,
  MatchEvent,
  MatchLineup,
  Player,
  PlayerSeasonStats,
  CupBracket,
  RandomResult,
  RandomSeasonResult,
  Referee,
  Season,
  SeasonRollover,
  Stadium,
  Team,
  TeamSeasonStats,
  TokenResponse,
  Tournament,
  User,
} from "./types";

export type LoginPayload = {
  email: string;
  password: string;
};

export type RegisterPayload = {
  nickname: string;
  email: string;
  password: string;
};

export type RefereePayload = {
  full_name: string;
};

export type SeasonPayload = {
  name: string;
  start_date: string;
  end_date: string;
  status: string;
};

export type SeasonRolloverPayload = SeasonPayload & {
  copy_tournaments: boolean;
};

export type StadiumPayload = {
  name: string;
  city: string;
  address: string;
  capacity: number;
  home_team_id: number | null;
};

export type TeamPayload = {
  name: string;
  city: string;
  address: string | null;
  manager_name: string | null;
  emblem_url: string | null;
  previous_season_place: number | null;
};

export type PlayerPayload = {
  full_name: string;
  age: number | null;
  position: string;
  number: number;
  team_id: number;
};

export type TournamentPayload = {
  season_id: number;
  name: string;
  type: string;
  status: string;
};

export type MatchPayload = {
  tournament_id: number;
  season_id: number;
  home_team_id: number;
  away_team_id: number;
  stadium_id: number;
  referee_id: number | null;
  match_datetime: string;
  status: string;
  round_number: number;
  stage: string | null;
};

export type LineupPayload = {
  team_id: number;
  player_id: number;
  is_starting: boolean;
  position: string;
  number: number;
};

export type LineupGeneratePayload = {
  team_id: number;
  lineup_size: number;
  starting_size: number | null;
  preferred_player_ids: number[];
  replace_existing: boolean;
};

export type MatchEventPayload = {
  team_id: number;
  player_id: number;
  assist_player_id: number | null;
  event_type: string;
  minute: number;
};

export type ChampionshipSchedulePayload = {
  start_datetime: string;
  match_time: string | null;
  interval_days: number;
  team_ids: number[];
  fallback_stadium_id: number | null;
  stadium_ids_by_team: Record<number, number>;
};

export type CupSemifinalsPayload = {
  team_ids: number[] | null;
  use_previous_season_places: boolean;
  match_datetimes: string[];
  fallback_stadium_id: number | null;
  stadium_ids_by_team: Record<number, number>;
};

export type CupFinalPayload = {
  match_datetime: string;
  stadium_id: number;
};

export function login(payload: LoginPayload) {
  return apiRequest<TokenResponse>("/auth/login", {
    method: "POST",
    body: payload,
  });
}

export function register(payload: RegisterPayload) {
  return apiRequest<User>("/auth/register", {
    method: "POST",
    body: payload,
  });
}

export function fetchCurrentUser(token: string) {
  return apiRequest<User>("/auth/me", { token });
}

export function fetchSeasons(token: string) {
  return getAllPages<Season>("/seasons/", token);
}

export function createSeason(token: string, payload: SeasonPayload) {
  return apiRequest<Season>("/seasons/", {
    method: "POST",
    body: payload,
    token,
  });
}

export function updateSeason(token: string, seasonId: number, payload: SeasonPayload) {
  return apiRequest<Season>(`/seasons/${seasonId}`, {
    method: "PATCH",
    body: payload,
    token,
  });
}

export function deleteSeason(token: string, seasonId: number) {
  return apiRequest<void>(`/seasons/${seasonId}`, {
    method: "DELETE",
    token,
  });
}

export function rolloverSeason(
  token: string,
  seasonId: number,
  payload: SeasonRolloverPayload,
) {
  return apiRequest<SeasonRollover>(`/seasons/${seasonId}/rollover`, {
    method: "POST",
    body: payload,
    token,
  });
}

export function fetchTeams(token: string) {
  return getAllPages<Team>("/teams/", token);
}

export function createTeam(token: string, payload: TeamPayload) {
  return apiRequest<Team>("/teams/", {
    method: "POST",
    body: payload,
    token,
  });
}

export function fetchTeam(token: string, teamId: number) {
  return apiRequest<Team>(`/teams/${teamId}`, { token });
}

export function updateTeam(token: string, teamId: number, payload: TeamPayload) {
  return apiRequest<Team>(`/teams/${teamId}`, {
    method: "PATCH",
    body: payload,
    token,
  });
}

export function deleteTeam(token: string, teamId: number) {
  return apiRequest<void>(`/teams/${teamId}`, {
    method: "DELETE",
    token,
  });
}

export function fetchPlayers(token: string) {
  return getAllPages<Player>("/players/", token);
}

export function createPlayer(token: string, payload: PlayerPayload) {
  return apiRequest<Player>("/players/", {
    method: "POST",
    body: payload,
    token,
  });
}

export function updatePlayer(
  token: string,
  playerId: number,
  payload: PlayerPayload,
) {
  return apiRequest<Player>(`/players/${playerId}`, {
    method: "PATCH",
    body: payload,
    token,
  });
}

export function deletePlayer(token: string, playerId: number) {
  return apiRequest<void>(`/players/${playerId}`, {
    method: "DELETE",
    token,
  });
}

export function fetchStadiums(token: string) {
  return getAllPages<Stadium>("/stadiums/", token);
}

export function createStadium(token: string, payload: StadiumPayload) {
  return apiRequest<Stadium>("/stadiums/", {
    method: "POST",
    body: payload,
    token,
  });
}

export function updateStadium(
  token: string,
  stadiumId: number,
  payload: StadiumPayload,
) {
  return apiRequest<Stadium>(`/stadiums/${stadiumId}`, {
    method: "PATCH",
    body: payload,
    token,
  });
}

export function deleteStadium(token: string, stadiumId: number) {
  return apiRequest<void>(`/stadiums/${stadiumId}`, {
    method: "DELETE",
    token,
  });
}

export function fetchMatches(token: string) {
  return getAllPages<Match>("/matches/", token);
}

export function createMatch(token: string, payload: MatchPayload) {
  return apiRequest<Match>("/matches/", {
    method: "POST",
    body: payload,
    token,
  });
}

export function fetchMatch(token: string, matchId: number) {
  return apiRequest<Match>(`/matches/${matchId}`, { token });
}

export function deleteMatch(token: string, matchId: number) {
  return apiRequest<void>(`/matches/${matchId}`, {
    method: "DELETE",
    token,
  });
}

export function rescheduleMatch(
  token: string,
  matchId: number,
  matchDatetime: string,
) {
  return apiRequest<Match>(`/matches/${matchId}/reschedule`, {
    method: "POST",
    body: { match_datetime: matchDatetime },
    token,
  });
}

export function assignMatchReferee(
  token: string,
  matchId: number,
  refereeId: number,
) {
  return apiRequest<Match>(`/matches/${matchId}/assign-referee`, {
    method: "POST",
    body: { referee_id: refereeId },
    token,
  });
}

export function updateMatchTicketPrice(
  token: string,
  matchId: number,
  ticketPrice: string,
) {
  return apiRequest<Match>(`/matches/${matchId}/ticket-price`, {
    method: "POST",
    body: { ticket_price: ticketPrice },
    token,
  });
}

export function generateMatchProtocol(token: string, matchId: number) {
  return apiRequest<RandomResult>(`/matches/${matchId}/generate-protocol`, {
    method: "POST",
    body: { seed: null },
    token,
    timeoutMs: 30000,
  });
}

export function fetchMatchLineups(token: string, matchId: number) {
  return apiRequest<MatchLineup[]>(`/matches/${matchId}/lineups`, { token });
}

export function addMatchLineup(
  token: string,
  matchId: number,
  payload: LineupPayload,
) {
  return apiRequest<MatchLineup>(`/matches/${matchId}/lineups`, {
    method: "POST",
    body: payload,
    token,
  });
}

export function generateMatchLineup(
  token: string,
  matchId: number,
  payload: LineupGeneratePayload,
) {
  return apiRequest<MatchLineup[]>(`/matches/${matchId}/lineups/generate`, {
    method: "POST",
    body: payload,
    token,
  });
}

export function deleteMatchLineup(token: string, lineupId: number) {
  return apiRequest<void>(`/lineups/${lineupId}`, {
    method: "DELETE",
    token,
  });
}

export function fetchMatchEvents(token: string, matchId: number) {
  return apiRequest<MatchEvent[]>(`/matches/${matchId}/events`, { token });
}

export function addMatchEvent(
  token: string,
  matchId: number,
  payload: MatchEventPayload,
) {
  return apiRequest<MatchEvent>(`/matches/${matchId}/events`, {
    method: "POST",
    body: payload,
    token,
  });
}

export function deleteMatchEvent(token: string, eventId: number) {
  return apiRequest<void>(`/events/${eventId}`, {
    method: "DELETE",
    token,
  });
}

export function finishMatch(
  token: string,
  matchId: number,
  homeScore: number,
  awayScore: number,
) {
  return apiRequest<Match>(`/matches/${matchId}/finish`, {
    method: "POST",
    body: { home_score: homeScore, away_score: awayScore },
    token,
  });
}

export function generateChampionshipSchedule(
  token: string,
  tournamentId: number,
  payload: ChampionshipSchedulePayload,
) {
  return apiRequest<Match[]>(`/schedule/championships/${tournamentId}/generate`, {
    method: "POST",
    body: payload,
    token,
    timeoutMs: 60000,
  });
}

export function fetchSeasonSchedule(token: string, seasonId: number) {
  return apiRequest<Match[]>(`/schedule/seasons/${seasonId}/matches`, { token });
}

export function fetchSeasonStandings(token: string, seasonId: number) {
  return apiRequest<TeamSeasonStats[]>(`/standings/seasons/${seasonId}`, {
    token,
  });
}

export function recalculateSeasonStandings(token: string, seasonId: number) {
  return apiRequest<TeamSeasonStats[]>(
    `/standings/seasons/${seasonId}/recalculate`,
    {
      method: "POST",
      token,
    },
  );
}

export function generateSeasonProtocols(token: string, seasonId: number) {
  return apiRequest<RandomSeasonResult>(`/seasons/${seasonId}/generate-protocols`, {
    method: "POST",
    body: { seed: null },
    token,
    timeoutMs: 120000,
  });
}

export function fetchPlayerLeaders(
  token: string,
  seasonId: number,
  metric: string,
) {
  return apiRequest<PlayerSeasonStats[]>(
    `/statistics/seasons/${seasonId}/leaders/${metric}`,
    { token },
  );
}

export function fetchCupBracket(token: string, tournamentId: number) {
  return apiRequest<CupBracket>(`/cups/${tournamentId}/bracket`, { token });
}

export function generateCupSemifinals(
  token: string,
  tournamentId: number,
  payload: CupSemifinalsPayload,
) {
  return apiRequest<Match[]>(`/cups/${tournamentId}/semifinals`, {
    method: "POST",
    body: payload,
    token,
    timeoutMs: 60000,
  });
}

export function generateCupFinal(
  token: string,
  tournamentId: number,
  payload: CupFinalPayload,
) {
  return apiRequest<Match>(`/cups/${tournamentId}/final`, {
    method: "POST",
    body: payload,
    token,
    timeoutMs: 30000,
  });
}

export function fetchReferees(token: string) {
  return getAllPages<Referee>("/referees/", token);
}

export function createReferee(token: string, payload: RefereePayload) {
  return apiRequest<Referee>("/referees/", {
    method: "POST",
    body: payload,
    token,
  });
}

export function updateReferee(
  token: string,
  refereeId: number,
  payload: RefereePayload,
) {
  return apiRequest<Referee>(`/referees/${refereeId}`, {
    method: "PATCH",
    body: payload,
    token,
  });
}

export function deleteReferee(token: string, refereeId: number) {
  return apiRequest<void>(`/referees/${refereeId}`, {
    method: "DELETE",
    token,
  });
}

export function fetchTournaments(token: string) {
  return getAllPages<Tournament>("/tournaments/", token);
}

export function createTournament(token: string, payload: TournamentPayload) {
  return apiRequest<Tournament>("/tournaments/", {
    method: "POST",
    body: payload,
    token,
  });
}

export function updateTournament(
  token: string,
  tournamentId: number,
  payload: TournamentPayload,
) {
  return apiRequest<Tournament>(`/tournaments/${tournamentId}`, {
    method: "PATCH",
    body: payload,
    token,
  });
}

export function deleteTournament(token: string, tournamentId: number) {
  return apiRequest<void>(`/tournaments/${tournamentId}`, {
    method: "DELETE",
    token,
  });
}
