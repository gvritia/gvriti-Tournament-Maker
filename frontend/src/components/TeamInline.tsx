import type { Team } from "../shared/api/types";
import { TeamMark } from "./TeamMark";

type TeamInlineProps = {
  fallbackName: string;
  team?: Team;
};

export function TeamInline({ fallbackName, team }: TeamInlineProps) {
  if (!team) {
    return <span className="team-inline-name">{fallbackName}</span>;
  }

  return (
    <span className="team-inline">
      <TeamMark team={team} />
      <span className="team-inline-name">{team.name}</span>
    </span>
  );
}
