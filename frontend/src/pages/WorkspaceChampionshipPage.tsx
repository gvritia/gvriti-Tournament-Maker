import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useMemo, useState, type FormEvent } from "react";
import { Link } from "react-router-dom";
import { DataTable } from "../components/DataTable";
import { MatchupInline } from "../components/MatchupInline";
import { TeamInline } from "../components/TeamInline";
import { useAuth } from "../features/auth/AuthProvider";
import type { ApiError } from "../shared/api/client";
import {
  fetchPlayerLeaders,
  fetchPlayers,
  fetchSeasonSchedule,
  fetchSeasonStandings,
  fetchSeasons,
  fetchStadiums,
  fetchTeams,
  fetchTournaments,
  generateChampionshipSchedule,
  generateSeasonProtocols,
  recalculateSeasonStandings,
} from "../shared/api/endpoints";
import type {
  Match,
  Player,
  PlayerSeasonStats,
  Season,
  Stadium,
  Team,
  TeamSeasonStats,
  Tournament,
} from "../shared/api/types";

const LEADER_METRICS = ["goals", "assists", "saves", "yellow_cards", "red_cards"];

export function WorkspaceChampionshipPage() {
  const { token } = useAuth();
  const safeToken = token ?? "";
  const queryClient = useQueryClient();
  const [selectedSeasonId, setSelectedSeasonId] = useState("");
  const [selectedTournamentId, setSelectedTournamentId] = useState("");
  const [leaderMetric, setLeaderMetric] = useState("goals");
  const [isScheduleFormOpen, setIsScheduleFormOpen] = useState(false);
  const [formError, setFormError] = useState<string | null>(null);
  const [fieldErrors, setFieldErrors] = useState<Record<string, string>>({});
  const [operationError, setOperationError] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);

  const seasonsQuery = useQuery({
    queryKey: ["seasons"],
    queryFn: () => fetchSeasons(safeToken),
    enabled: Boolean(token),
  });
  const tournamentsQuery = useQuery({
    queryKey: ["tournaments"],
    queryFn: () => fetchTournaments(safeToken),
    enabled: Boolean(token),
  });
  const teamsQuery = useQuery({
    queryKey: ["teams"],
    queryFn: () => fetchTeams(safeToken),
    enabled: Boolean(token),
  });
  const playersQuery = useQuery({
    queryKey: ["players"],
    queryFn: () => fetchPlayers(safeToken),
    enabled: Boolean(token),
  });
  const stadiumsQuery = useQuery({
    queryKey: ["stadiums"],
    queryFn: () => fetchStadiums(safeToken),
    enabled: Boolean(token),
  });

  const seasons = seasonsQuery.data ?? [];
  const tournaments = tournamentsQuery.data ?? [];
  const teams = teamsQuery.data ?? [];
  const players = playersQuery.data ?? [];
  const stadiums = stadiumsQuery.data ?? [];
  const seasonId = Number(selectedSeasonId || seasons[0]?.id || 0);
  const championshipTournaments = tournaments.filter(
    (tournament) =>
      tournament.type === "championship" &&
      (!seasonId || tournament.season_id === seasonId),
  );
  const tournamentId = Number(
    selectedTournamentId || championshipTournaments[0]?.id || 0,
  );

  const standingsQuery = useQuery({
    queryKey: ["standings", seasonId],
    queryFn: () => fetchSeasonStandings(safeToken, seasonId),
    enabled: Boolean(token) && seasonId > 0,
  });
  const scheduleQuery = useQuery({
    queryKey: ["seasonSchedule", seasonId],
    queryFn: () => fetchSeasonSchedule(safeToken, seasonId),
    enabled: Boolean(token) && seasonId > 0,
  });
  const leadersQuery = useQuery({
    queryKey: ["leaders", seasonId, leaderMetric],
    queryFn: () => fetchPlayerLeaders(safeToken, seasonId, leaderMetric),
    enabled: Boolean(token) && seasonId > 0,
  });

  const standings = standingsQuery.data ?? [];
  const schedule = scheduleQuery.data ?? [];
  const leaders = leadersQuery.data ?? [];
  const error =
    seasonsQuery.error ??
    tournamentsQuery.error ??
    teamsQuery.error ??
    playersQuery.error ??
    stadiumsQuery.error ??
    standingsQuery.error ??
    scheduleQuery.error ??
    leadersQuery.error ??
    null;
  const isInitialLoading =
    seasonsQuery.isLoading ||
    tournamentsQuery.isLoading ||
    teamsQuery.isLoading ||
    playersQuery.isLoading ||
    stadiumsQuery.isLoading;

  const championshipSchedule = useMemo(
    () =>
      schedule.filter(
        (match) =>
          tournaments.find((tournament) => tournament.id === match.tournament_id)
            ?.type === "championship",
      ),
    [schedule, tournaments],
  );

  const generateScheduleMutation = useMutation({
    mutationFn: (payload: ChampionshipScheduleFormPayload) =>
      generateChampionshipSchedule(safeToken, tournamentId, payload),
    onSuccess: async (matches) => {
      await invalidateChampionshipReads(queryClient, seasonId);
      setSuccessMessage(`Готово: создано матчей чемпионата: ${matches.length}.`);
    },
  });

  const recalculateMutation = useMutation({
    mutationFn: () => recalculateSeasonStandings(safeToken, seasonId),
    onSuccess: async () => {
      await invalidateChampionshipReads(queryClient, seasonId);
      setSuccessMessage("Турнирная таблица пересчитана.");
    },
  });

  const simulateMutation = useMutation({
    mutationFn: () => generateSeasonProtocols(safeToken, seasonId),
    onSuccess: async (result) => {
      await invalidateChampionshipReads(queryClient, seasonId);
      setSuccessMessage(
        `Готово: сгенерированы протоколы для ${result.generated_count} оставшихся матчей.`,
      );
    },
  });

  function handleSeasonChange(nextSeasonId: string) {
    const nextTournament = tournaments.find(
      (tournament) =>
        tournament.type === "championship" &&
        tournament.season_id === Number(nextSeasonId),
    );
    setSelectedSeasonId(nextSeasonId);
    setSelectedTournamentId(nextTournament ? String(nextTournament.id) : "");
    setSuccessMessage(null);
  }

  async function submitAction(action: () => Promise<unknown>) {
    setFormError(null);
    setFieldErrors({});
    setOperationError(null);
    setSuccessMessage(null);

    try {
      await action();
      setIsScheduleFormOpen(false);
    } catch (caughtError) {
      const apiError = caughtError as ApiError;
      setFormError(apiError.message);
      setOperationError(apiError.message);
      setFieldErrors(apiError.fieldErrors ?? {});
    }
  }

  const canGenerateSchedule = tournamentId > 0 && teams.length >= 2;
  const isWorking =
    generateScheduleMutation.isPending ||
    recalculateMutation.isPending ||
    simulateMutation.isPending;

  return (
    <div className="page-stack">
      <section className="page-intro">
        <p className="eyebrow">Чемпионат</p>
        <h2>Чемпионат</h2>
        <p className="muted">
          Создавайте календарь чемпионата, проверяйте таблицу и генерируйте
          протоколы оставшихся матчей сезона.
        </p>
      </section>

      {error instanceof Error ? (
        <section className="notice notice-danger">
          <strong>Не удалось загрузить данные чемпионата.</strong>
          <span>{error.message}</span>
        </section>
      ) : null}

      {operationError ? <div className="form-error">{operationError}</div> : null}
      {successMessage ? (
        <section className="notice notice-success">
          <strong>{successMessage}</strong>
        </section>
      ) : null}

      <section className="panel">
        <div className="section-head">
          <div className="filter-row">
            <select
              aria-label="Season"
              onChange={(event) => handleSeasonChange(event.target.value)}
              value={String(seasonId || "")}
            >
              {seasons.map((season) => (
                <option key={season.id} value={season.id}>
                  {season.name}
                </option>
              ))}
            </select>
            <select
              aria-label="Championship tournament"
              onChange={(event) => setSelectedTournamentId(event.target.value)}
              value={String(tournamentId || "")}
            >
              {championshipTournaments.map((tournament) => (
                <option key={tournament.id} value={tournament.id}>
                  {tournament.name}
                </option>
              ))}
            </select>
          </div>
          <div className="row-actions">
            <button
              className="button button-primary"
              disabled={!canGenerateSchedule}
              type="button"
              onClick={() => {
                setFormError(null);
                setFieldErrors({});
                setOperationError(null);
                setIsScheduleFormOpen((current) => !current);
              }}
            >
              Создать календарь
            </button>
            <button
              className="button button-ghost"
              disabled={!seasonId || recalculateMutation.isPending}
              type="button"
              onClick={() => submitAction(() => recalculateMutation.mutateAsync())}
            >
              Пересчитать таблицу
            </button>
            <button
              className="button button-danger"
              disabled={!seasonId || isWorking}
              type="button"
              onClick={() => {
                const confirmed = window.confirm(
                  "Сгенерировать протоколы для оставшихся незавершённых матчей сезона? Завершённые матчи и матчи с уже заполненным протоколом останутся без изменений.",
                );
                if (!confirmed) {
                  return;
                }
                submitAction(() => simulateMutation.mutateAsync());
              }}
            >
              Сгенерировать остаток сезона
            </button>
          </div>
        </div>

        {!canGenerateSchedule ? (
          <div className="notice">
            <strong>Setup needed.</strong>
            <span>Schedule generation needs a championship tournament and at least two teams.</span>
          </div>
        ) : null}

        {isScheduleFormOpen ? (
          <ChampionshipScheduleForm
            error={formError}
            fieldErrors={fieldErrors}
            isSaving={generateScheduleMutation.isPending}
            stadiums={stadiums}
            teams={teams}
            onCancel={() => setIsScheduleFormOpen(false)}
            onSubmit={(payload) =>
              submitAction(() => generateScheduleMutation.mutateAsync(payload))
            }
          />
        ) : null}
      </section>

      <section className="panel">
        <div className="section-head">
          <div>
            <p className="eyebrow">Standings</p>
            <h2>Table</h2>
          </div>
          <span className="mode-chip">{standings.length} teams</span>
        </div>
        <StandingsTable
          isLoading={isInitialLoading || standingsQuery.isLoading}
          standings={standings}
          teams={teams}
        />
      </section>

      <section className="panel">
        <div className="section-head">
          <div>
            <p className="eyebrow">Schedule</p>
            <h2>Championship matches</h2>
          </div>
          <span className="mode-chip">{championshipSchedule.length} matches</span>
        </div>
        <ScheduleTable
          isLoading={isInitialLoading || scheduleQuery.isLoading}
          matches={championshipSchedule}
          teams={teams}
        />
      </section>

      <section className="panel">
        <div className="section-head">
          <div>
            <p className="eyebrow">Leaders</p>
            <h2>Player leaderboard</h2>
          </div>
          <select
            aria-label="Leader metric"
            onChange={(event) => setLeaderMetric(event.target.value)}
            value={leaderMetric}
          >
            {LEADER_METRICS.map((metric) => (
              <option key={metric} value={metric}>
                {metric}
              </option>
            ))}
          </select>
        </div>
        <LeadersTable
          isLoading={isInitialLoading || leadersQuery.isLoading}
          leaders={leaders}
          metric={leaderMetric}
          players={players}
        />
      </section>
    </div>
  );
}

type ChampionshipScheduleFormPayload = {
  start_datetime: string;
  match_time: string | null;
  interval_days: number;
  team_ids: number[];
  fallback_stadium_id: number | null;
  stadium_ids_by_team: Record<number, number>;
};

function ChampionshipScheduleForm({
  teams,
  stadiums,
  isSaving,
  error,
  fieldErrors,
  onCancel,
  onSubmit,
}: {
  teams: Team[];
  stadiums: Stadium[];
  isSaving: boolean;
  error: string | null;
  fieldErrors: Record<string, string>;
  onCancel: () => void;
  onSubmit: (payload: ChampionshipScheduleFormPayload) => Promise<void>;
}) {
  const today = new Date().toISOString().slice(0, 10);
  const [date, setDate] = useState(today);
  const [time, setTime] = useState("19:00");
  const [intervalDays, setIntervalDays] = useState("4");
  const [fallbackStadiumId, setFallbackStadiumId] = useState("");
  const [selectedTeamIds, setSelectedTeamIds] = useState(
    teams.map((team) => team.id),
  );

  function toggleTeam(teamId: number) {
    setSelectedTeamIds((current) =>
      current.includes(teamId)
        ? current.filter((id) => id !== teamId)
        : [...current, teamId],
    );
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    await onSubmit({
      start_datetime: `${date}T${time}:00`,
      match_time: time,
      interval_days: Number(intervalDays),
      team_ids: selectedTeamIds,
      fallback_stadium_id: fallbackStadiumId ? Number(fallbackStadiumId) : null,
      stadium_ids_by_team: {},
    });
  }

  return (
    <form className="inline-form" onSubmit={handleSubmit}>
      <div>
        <p className="eyebrow">Schedule</p>
        <h2>Generate championship schedule</h2>
      </div>
      {error ? <div className="form-error">{error}</div> : null}
      <div className="form-grid">
        <label className="field">
          <span>Start date</span>
          <input
            onChange={(event) => setDate(event.target.value)}
            required
            type="date"
            value={date}
          />
          <FieldError message={fieldErrors.start_datetime} />
        </label>
        <label className="field">
          <span>Match time</span>
          <input
            onChange={(event) => setTime(event.target.value)}
            required
            type="time"
            value={time}
          />
          <FieldError message={fieldErrors.match_time} />
        </label>
        <label className="field">
          <span>Interval days</span>
          <input
            min={1}
            onChange={(event) => setIntervalDays(event.target.value)}
            required
            type="number"
            value={intervalDays}
          />
          <FieldError message={fieldErrors.interval_days} />
        </label>
        <label className="field">
          <span>Fallback stadium</span>
          <select
            onChange={(event) => setFallbackStadiumId(event.target.value)}
            value={fallbackStadiumId}
          >
            <option value="">Use home stadiums only</option>
            {stadiums.map((stadium) => (
              <option key={stadium.id} value={stadium.id}>
                {stadium.name}
              </option>
            ))}
          </select>
          <FieldError message={fieldErrors.fallback_stadium_id} />
        </label>
      </div>

      <div className="filter-row">
        {teams.map((team) => (
          <label key={team.id} className="mode-chip">
            <input
              checked={selectedTeamIds.includes(team.id)}
              onChange={() => toggleTeam(team.id)}
              type="checkbox"
            />
            {team.name}
          </label>
        ))}
      </div>
      <FieldError message={fieldErrors.team_ids} />

      <div className="form-actions">
        <button
          className="button button-primary"
          disabled={
            isSaving || selectedTeamIds.length < 2 || Number(intervalDays) < 1
          }
          type="submit"
        >
          {isSaving ? "Generating..." : "Generate"}
        </button>
        <button
          className="button button-ghost"
          disabled={isSaving}
          type="button"
          onClick={onCancel}
        >
          Cancel
        </button>
      </div>
    </form>
  );
}

function StandingsTable({
  isLoading,
  standings,
  teams,
}: {
  isLoading: boolean;
  standings: TeamSeasonStats[];
  teams: Team[];
}) {
  const sorted = [...standings].sort(
    (left, right) => (left.place ?? 9999) - (right.place ?? 9999),
  );

  return (
    <DataTable
      rows={sorted}
      getRowKey={(row) => row.id}
      emptyText="No standings yet"
      isLoading={isLoading}
      columns={[
        { key: "place", header: "#", render: (row) => row.place ?? "-" },
        {
          key: "team",
          header: "Team",
          render: (row) => (
            <TeamInline
              fallbackName={`Team ${row.team_id}`}
              team={getTeamById(row.team_id, teams)}
            />
          ),
        },
        { key: "played", header: "P", render: (row) => row.played },
        { key: "wins", header: "W", render: (row) => row.wins },
        { key: "draws", header: "D", render: (row) => row.draws },
        { key: "losses", header: "L", render: (row) => row.losses },
        { key: "gf", header: "GF", render: (row) => row.goals_scored },
        { key: "ga", header: "GA", render: (row) => row.goals_conceded },
        { key: "gd", header: "GD", render: (row) => row.goal_difference },
        { key: "points", header: "Pts", render: (row) => row.points },
      ]}
    />
  );
}

function ScheduleTable({
  isLoading,
  matches,
  teams,
}: {
  isLoading: boolean;
  matches: Match[];
  teams: Team[];
}) {
  return (
    <DataTable
      rows={matches}
      getRowKey={(match) => match.id}
      emptyText="No championship matches yet"
      isLoading={isLoading}
      pageSize={50}
      columns={[
        {
          key: "date",
          header: "Date",
          render: (match) => formatDateTime(match.match_datetime),
        },
        {
          key: "match",
          header: "Match",
          render: (match) => (
            <Link className="auth-link" to={`/app/matches/${match.id}`}>
              <MatchupInline match={match} teams={teams} />
            </Link>
          ),
        },
        {
          key: "status",
          header: "Status",
          render: (match) => (
            <span className={`status status-${match.status}`}>{match.status}</span>
          ),
        },
        {
          key: "score",
          header: "Score",
          render: (match) =>
            match.status === "finished"
              ? `${match.home_score ?? 0}:${match.away_score ?? 0}`
              : "not played",
        },
        {
          key: "ticket",
          header: "Ticket",
          render: (match) => match.ticket_price ?? "not set",
        },
      ]}
    />
  );
}

function LeadersTable({
  isLoading,
  leaders,
  metric,
  players,
}: {
  isLoading: boolean;
  leaders: PlayerSeasonStats[];
  metric: string;
  players: Player[];
}) {
  return (
    <DataTable
      rows={leaders}
      getRowKey={(leader) => leader.id}
      emptyText="No leaders yet"
      isLoading={isLoading}
      pageSize={25}
      columns={[
        {
          key: "player",
          header: "Player",
          render: (leader) => getPlayerName(leader.player_id, players),
        },
        {
          key: "value",
          header: metric,
          render: (leader) => getLeaderValue(leader, metric),
        },
      ]}
    />
  );
}

function FieldError({ message }: { message?: string }) {
  return message ? <small className="field-error">{message}</small> : null;
}

function getLeaderValue(leader: PlayerSeasonStats, metric: string) {
  switch (metric) {
    case "assists":
      return leader.assists;
    case "saves":
      return leader.saves;
    case "yellow_cards":
      return leader.yellow_cards;
    case "red_cards":
      return leader.red_cards;
    default:
      return leader.goals;
  }
}

function getTeamName(teamId: number, teams: Team[]) {
  return teams.find((team) => team.id === teamId)?.name ?? `Team ${teamId}`;
}

function getTeamById(teamId: number, teams: Team[]) {
  return teams.find((team) => team.id === teamId);
}

function getPlayerName(playerId: number, players: Player[]) {
  return (
    players.find((player) => player.id === playerId)?.full_name ??
    `Player ${playerId}`
  );
}

function formatDateTime(value: string) {
  return new Intl.DateTimeFormat("ru-RU", {
    dateStyle: "short",
    timeStyle: "short",
  }).format(new Date(value));
}

async function invalidateChampionshipReads(
  queryClient: ReturnType<typeof useQueryClient>,
  seasonId: number,
) {
  await queryClient.invalidateQueries({ queryKey: ["matches"] });
  await queryClient.invalidateQueries({ queryKey: ["seasonSchedule", seasonId] });
  await queryClient.invalidateQueries({ queryKey: ["standings", seasonId] });
  await queryClient.invalidateQueries({ queryKey: ["leaders", seasonId] });
}
