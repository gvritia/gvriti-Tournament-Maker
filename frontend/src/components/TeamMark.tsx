import { useState } from "react";
import type { Team } from "../shared/api/types";

type TeamMarkProps = {
  team: Pick<Team, "name" | "emblem_url">;
  size?: "normal" | "large";
};

export function TeamMark({ team, size = "normal" }: TeamMarkProps) {
  const [imageFailed, setImageFailed] = useState(false);
  const imageClassName =
    size === "large" ? "team-emblem-img team-emblem-lg" : "team-emblem-img";
  const markClassName =
    size === "large" ? "team-emblem team-emblem-lg" : "team-emblem";

  if (team.emblem_url && !imageFailed) {
    return (
      <img
        className={imageClassName}
        src={team.emblem_url}
        alt=""
        onError={() => setImageFailed(true)}
      />
    );
  }

  return <span className={markClassName}>{team.name.slice(0, 2).toUpperCase()}</span>;
}
