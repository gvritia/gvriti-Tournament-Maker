import type { Match, Team } from "../shared/api/types";
import { TeamMark } from "./TeamMark";

type MatchupInlineProps = {
  match: Pick<Match, "home_team_id" | "away_team_id">;
  teams: Team[];
};

export function MatchupInline({ match, teams }: MatchupInlineProps) {
  const homeTeam = teams.find((team) => team.id === match.home_team_id);
  const awayTeam = teams.find((team) => team.id === match.away_team_id);

  return (
    <span className="matchup-inline">
      <MatchupTeam
        fallbackName={`Team ${match.home_team_id}`}
        team={homeTeam}
      />
      <span className="matchup-inline-separator">-</span>
      <MatchupTeam
        fallbackName={`Team ${match.away_team_id}`}
        team={awayTeam}
      />
    </span>
  );
}

function MatchupTeam({
  fallbackName,
  team,
}: {
  fallbackName: string;
  team: Team | undefined;
}) {
  if (!team) {
    return <span className="matchup-inline-name">{fallbackName}</span>;
  }

  return (
    <span className="matchup-inline-team">
      <TeamMark team={team} />
      <span className="matchup-inline-name">{team.name}</span>
    </span>
  );
}
