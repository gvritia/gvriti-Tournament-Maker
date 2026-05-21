import { Link } from "react-router-dom";
import { DataTable } from "./DataTable";
import type { MatchPreview, PlayerPreview, TeamPreview } from "../data/previewData";

type TeamProfileProps = {
  team: TeamPreview;
  players: PlayerPreview[];
  matches: MatchPreview[];
  getTeamName: (teamId: string) => string;
};

export function TeamProfile({
  team,
  players,
  matches,
  getTeamName,
}: TeamProfileProps) {
  return (
    <div className="page-grid">
      <section className="panel team-hero">
        <div className="team-emblem team-emblem-lg">{team.shortName}</div>
        <div>
          <p className="eyebrow">Team detail</p>
          <h2>{team.name}</h2>
          <div className="meta-grid">
            <span>Город: {team.city}</span>
            <span>Стадион: {team.stadiumName}</span>
            <span>Менеджер: {team.manager}</span>
            <span>Место прошлого сезона: {team.previousSeasonPlace}</span>
          </div>
          <p className="muted">{team.address}</p>
        </div>
      </section>

      <section className="panel">
        <div className="section-head">
          <div>
            <p className="eyebrow">Roster</p>
            <h2>Состав</h2>
          </div>
          <button className="button button-neutral" type="button" disabled>
            Добавить игрока
          </button>
        </div>
        <DataTable
          rows={players}
          getRowKey={(player) => player.id}
          columns={[
            { key: "number", header: "#", render: (player) => player.number },
            { key: "name", header: "Игрок", render: (player) => player.name },
            {
              key: "position",
              header: "Позиция",
              render: (player) => player.position,
            },
            { key: "age", header: "Возраст", render: (player) => player.age },
          ]}
        />
      </section>

      <section className="panel">
        <div className="section-head">
          <div>
            <p className="eyebrow">Team matches</p>
            <h2>Матчи команды</h2>
          </div>
          <button className="button button-neutral" type="button" disabled>
            Создать матч
          </button>
        </div>
        <DataTable
          rows={matches}
          getRowKey={(match) => match.id}
          columns={[
            { key: "date", header: "Дата", render: (match) => match.date },
            {
              key: "pair",
              header: "Пара",
              render: (match) => (
                <Link to={`/matches/${match.id}`}>
                  {getTeamName(match.homeTeamId)} - {getTeamName(match.awayTeamId)}
                </Link>
              ),
            },
            {
              key: "status",
              header: "Статус",
              render: (match) => (
                <span className={`status status-${match.status}`}>
                  {match.statusLabel}
                </span>
              ),
            },
            {
              key: "score",
              header: "Счет",
              render: (match) =>
                match.status === "finished"
                  ? `${match.homeScore}:${match.awayScore}`
                  : "не сыгран",
            },
          ]}
        />
      </section>
    </div>
  );
}
