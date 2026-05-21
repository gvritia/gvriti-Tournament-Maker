export type User = {
  id: number;
  nickname: string;
  email: string;
  role: string;
  created_at: string;
};

export type TokenResponse = {
  access_token: string;
  token_type: string;
};

export type Season = {
  id: number;
  name: string;
  start_date: string;
  end_date: string;
  status: string;
};

export type SeasonRollover = {
  season: Season;
  tournaments: Tournament[];
};

export type Team = {
  id: number;
  name: string;
  city: string;
  address: string | null;
  manager_name: string | null;
  emblem_url: string | null;
  previous_season_place: number | null;
  created_at: string;
};

export type Match = {
  id: number;
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
  ticket_price: string | null;
  home_score: number | null;
  away_score: number | null;
  ticket_sold: number;
  income: string | null;
};

export type MatchEvent = {
  id: number;
  match_id: number;
  team_id: number;
  player_id: number;
  assist_player_id: number | null;
  event_type: string;
  minute: number;
  created_at: string;
};

export type MatchLineup = {
  id: number;
  match_id: number;
  team_id: number;
  player_id: number;
  is_starting: boolean;
  position: string;
  number: number;
};

export type RandomResult = {
  match: Match;
  events: MatchEvent[];
};

export type RandomSeasonResult = {
  season_id: number;
  generated_count: number;
  results: RandomResult[];
};

export type TeamSeasonStats = {
  id: number;
  team_id: number;
  season_id: number;
  played: number;
  wins: number;
  draws: number;
  losses: number;
  goals_scored: number;
  goals_conceded: number;
  goal_difference: number;
  points: number;
  place: number | null;
  cup_place: number | null;
};

export type PlayerSeasonStats = {
  id: number;
  player_id: number;
  season_id: number;
  goals: number;
  assists: number;
  saves: number;
  yellow_cards: number;
  red_cards: number;
};

export type CupMatchNode = {
  match: Match;
  winner_team_id: number | null;
};

export type CupBracket = {
  tournament_id: number;
  season_id: number;
  semifinals: CupMatchNode[];
  final: CupMatchNode | null;
  champion_team_id: number | null;
};

export type Player = {
  id: number;
  full_name: string;
  age: number | null;
  position: string;
  number: number;
  team_id: number;
  created_at: string;
};

export type Stadium = {
  id: number;
  name: string;
  city: string;
  address: string;
  capacity: number;
  home_team_id: number | null;
  created_at: string;
};

export type Referee = {
  id: number;
  full_name: string;
  created_at: string;
};

export type Tournament = {
  id: number;
  season_id: number;
  name: string;
  type: string;
  status: string;
  created_at: string;
};
