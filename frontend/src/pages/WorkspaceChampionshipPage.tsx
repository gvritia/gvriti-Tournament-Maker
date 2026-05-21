import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useEffect, useMemo, useState, type FormEvent } from "react";
import { Link } from "react-router-dom";
import { DataTable } from "../components/DataTable";
import { useConfirmationDialog } from "../components/ConfirmationDialog";
import { MatchupInline } from "../components/MatchupInline";
import { TeamInline } from "../components/TeamInline";
import { useAuth } from "../features/auth/AuthProvider";
import { useLanguage, type Language } from "../features/i18n/LanguageProvider";
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

const championshipText: Record<
  Language,
  {
    title: string;
    intro: string;
    loadErrorTitle: string;
    createSchedule: string;
    recalculate: string;
    generateSeason: string;
    confirmSeasonTitle: string;
    confirmSeason: string;
    setupTitle: string;
    setupBody: string;
    standingsEyebrow: string;
    standingsTitle: string;
    teamsCount: (count: number) => string;
    scheduleEyebrow: string;
    scheduleTitle: string;
    matchesCount: (count: number) => string;
    leadersEyebrow: string;
    leadersTitle: string;
    seasonLabel: string;
    tournamentLabel: string;
    leaderMetricLabel: string;
    scheduleFormEyebrow: string;
    scheduleFormTitle: string;
    startDate: string;
    matchTime: string;
    intervalDays: string;
    fallbackStadium: string;
    homeStadiumsOnly: string;
    generating: string;
    generate: string;
    cancel: string;
    noStandings: string;
    noMatches: string;
    noLeaders: string;
    team: string;
    date: string;
    match: string;
    status: string;
    score: string;
    ticket: string;
    notPlayed: string;
    notSet: string;
    player: string;
    fallbackTeam: (id: number) => string;
    fallbackPlayer: (id: number) => string;
    scheduleCreated: (count: number) => string;
    standingsRecalculated: string;
    seasonGenerated: (count: number) => string;
    progressTitle: string;
    progressRunning: string;
    progressDone: string;
    progressError: string;
    progressHint: string;
    metricLabels: Record<string, string>;
    statusLabels: Record<string, string>;
    locale: string;
  }
> = {
  ru: {
    title: "Чемпионат",
    intro:
      "Создавайте календарь чемпионата, проверяйте таблицу и генерируйте протоколы оставшихся матчей сезона.",
    loadErrorTitle: "Не удалось загрузить данные чемпионата.",
    createSchedule: "Создать календарь",
    recalculate: "Пересчитать таблицу",
    generateSeason: "Сгенерировать остаток сезона",
    confirmSeasonTitle: "Подтвердите действие",
    confirmSeason:
      "Сгенерировать протоколы для оставшихся незавершённых матчей сезона? Завершённые матчи и матчи с уже заполненным протоколом останутся без изменений.",
    setupTitle: "Нужно подготовить данные.",
    setupBody:
      "Для генерации календаря нужен турнир чемпионата и минимум две команды.",
    standingsEyebrow: "Таблица",
    standingsTitle: "Турнирная таблица",
    teamsCount: (count) => `${count} команд`,
    scheduleEyebrow: "Календарь",
    scheduleTitle: "Матчи чемпионата",
    matchesCount: (count) => `${count} матчей`,
    leadersEyebrow: "Лидеры",
    leadersTitle: "Статистика игроков",
    seasonLabel: "Сезон",
    tournamentLabel: "Турнир чемпионата",
    leaderMetricLabel: "Метрика лидеров",
    scheduleFormEyebrow: "Календарь",
    scheduleFormTitle: "Генерация календаря чемпионата",
    startDate: "Дата начала",
    matchTime: "Время матча",
    intervalDays: "Интервал в днях",
    fallbackStadium: "Запасной стадион",
    homeStadiumsOnly: "Использовать только домашние стадионы",
    generating: "Генерируем...",
    generate: "Сгенерировать",
    cancel: "Отмена",
    noStandings: "Турнирной таблицы пока нет",
    noMatches: "Матчей чемпионата пока нет",
    noLeaders: "Лидеров пока нет",
    team: "Команда",
    date: "Дата",
    match: "Матч",
    status: "Статус",
    score: "Счёт",
    ticket: "Билет",
    notPlayed: "не сыгран",
    notSet: "не задан",
    player: "Игрок",
    fallbackTeam: (id) => `Команда ${id}`,
    fallbackPlayer: (id) => `Игрок ${id}`,
    scheduleCreated: (count) => `Готово: создано матчей чемпионата: ${count}.`,
    standingsRecalculated: "Турнирная таблица пересчитана.",
    seasonGenerated: (count) =>
      `Готово: сгенерированы протоколы для ${count} оставшихся матчей.`,
    progressTitle: "Генерация остатка сезона",
    progressRunning: "Идёт генерация протоколов и обновление таблицы.",
    progressDone: "Генерация завершена.",
    progressError: "Генерация остановилась с ошибкой.",
    progressHint:
      "Окно можно оставить открытым: данные обновятся автоматически после завершения операции.",
    metricLabels: {
      goals: "Голы",
      assists: "Передачи",
      saves: "Сейвы",
      yellow_cards: "Жёлтые карточки",
      red_cards: "Красные карточки",
    },
    statusLabels: {
      scheduled: "запланирован",
      finished: "завершён",
      cancelled: "отменён",
    },
    locale: "ru-RU",
  },
  en: {
    title: "Championship",
    intro:
      "Create the championship schedule, review the table, and generate protocols for the remaining season matches.",
    loadErrorTitle: "Could not load championship data.",
    createSchedule: "Create schedule",
    recalculate: "Recalculate table",
    generateSeason: "Generate season remainder",
    confirmSeasonTitle: "Confirm action",
    confirmSeason:
      "Generate protocols for the remaining unfinished season matches? Finished matches and matches that already have a protocol will stay unchanged.",
    setupTitle: "Setup needed.",
    setupBody:
      "Schedule generation needs a championship tournament and at least two teams.",
    standingsEyebrow: "Standings",
    standingsTitle: "Table",
    teamsCount: (count) => `${count} teams`,
    scheduleEyebrow: "Schedule",
    scheduleTitle: "Championship matches",
    matchesCount: (count) => `${count} matches`,
    leadersEyebrow: "Leaders",
    leadersTitle: "Player leaderboard",
    seasonLabel: "Season",
    tournamentLabel: "Championship tournament",
    leaderMetricLabel: "Leader metric",
    scheduleFormEyebrow: "Schedule",
    scheduleFormTitle: "Generate championship schedule",
    startDate: "Start date",
    matchTime: "Match time",
    intervalDays: "Interval days",
    fallbackStadium: "Fallback stadium",
    homeStadiumsOnly: "Use home stadiums only",
    generating: "Generating...",
    generate: "Generate",
    cancel: "Cancel",
    noStandings: "No standings yet",
    noMatches: "No championship matches yet",
    noLeaders: "No leaders yet",
    team: "Team",
    date: "Date",
    match: "Match",
    status: "Status",
    score: "Score",
    ticket: "Ticket",
    notPlayed: "not played",
    notSet: "not set",
    player: "Player",
    fallbackTeam: (id) => `Team ${id}`,
    fallbackPlayer: (id) => `Player ${id}`,
    scheduleCreated: (count) => `Done: created ${count} championship matches.`,
    standingsRecalculated: "Standings recalculated.",
    seasonGenerated: (count) =>
      `Done: generated protocols for ${count} remaining matches.`,
    progressTitle: "Season remainder generation",
    progressRunning: "Generating protocols and updating standings.",
    progressDone: "Generation finished.",
    progressError: "Generation stopped with an error.",
    progressHint:
      "You can keep this panel open: data refreshes automatically when the operation finishes.",
    metricLabels: {
      goals: "Goals",
      assists: "Assists",
      saves: "Saves",
      yellow_cards: "Yellow cards",
      red_cards: "Red cards",
    },
    statusLabels: {
      scheduled: "scheduled",
      finished: "finished",
      cancelled: "cancelled",
    },
    locale: "en-US",
  },
};

type ChampionshipText = (typeof championshipText)[Language];

export function WorkspaceChampionshipPage() {
  const { token } = useAuth();
  const { language } = useLanguage();
  const text = championshipText[language];
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
  const [seasonGenerationProgress, setSeasonGenerationProgress] = useState<{
    isOpen: boolean;
    status: "running" | "done" | "error";
    value: number;
  }>({ isOpen: false, status: "running", value: 0 });
  const confirmation = useConfirmationDialog();

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
      setSuccessMessage(text.scheduleCreated(matches.length));
    },
  });

  const recalculateMutation = useMutation({
    mutationFn: () => recalculateSeasonStandings(safeToken, seasonId),
    onSuccess: async () => {
      await invalidateChampionshipReads(queryClient, seasonId);
      setSuccessMessage(text.standingsRecalculated);
    },
  });

  const simulateMutation = useMutation({
    mutationFn: () => generateSeasonProtocols(safeToken, seasonId),
    onSuccess: async (result) => {
      await invalidateChampionshipReads(queryClient, seasonId);
      setSeasonGenerationProgress({
        isOpen: true,
        status: "done",
        value: 100,
      });
      setSuccessMessage(text.seasonGenerated(result.generated_count));
    },
    onError: () => {
      setSeasonGenerationProgress({
        isOpen: true,
        status: "error",
        value: 100,
      });
    },
  });

  useEffect(() => {
    if (!simulateMutation.isPending) {
      return undefined;
    }

    const intervalId = window.setInterval(() => {
      setSeasonGenerationProgress((current) => ({
        ...current,
        isOpen: true,
        status: "running",
        value: Math.min(92, current.value + 7),
      }));
    }, 700);

    return () => window.clearInterval(intervalId);
  }, [simulateMutation.isPending]);

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

  function runSeasonGeneration() {
    setSeasonGenerationProgress({
      isOpen: true,
      status: "running",
      value: 8,
    });
    submitAction(() => simulateMutation.mutateAsync());
  }

  async function requestSeasonGeneration() {
    const confirmed = await confirmation.confirm({
      title: text.confirmSeasonTitle,
      message: text.confirmSeason,
      confirmLabel: text.generate,
      cancelLabel: text.cancel,
      tone: "danger",
    });

    if (confirmed) {
      runSeasonGeneration();
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
        <p className="eyebrow">{text.title}</p>
        <h2>{text.title}</h2>
        <p className="muted">{text.intro}</p>
      </section>

      {error instanceof Error ? (
        <section className="notice notice-danger">
          <strong>{text.loadErrorTitle}</strong>
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
              aria-label={text.seasonLabel}
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
              aria-label={text.tournamentLabel}
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
              {text.createSchedule}
            </button>
            <button
              className="button button-ghost"
              disabled={!seasonId || recalculateMutation.isPending}
              type="button"
              onClick={() => submitAction(() => recalculateMutation.mutateAsync())}
            >
              {text.recalculate}
            </button>
            <button
              className="button button-danger"
              disabled={!seasonId || isWorking}
              type="button"
              onClick={requestSeasonGeneration}
            >
              {text.generateSeason}
            </button>
          </div>
        </div>

        {!canGenerateSchedule ? (
          <div className="notice">
            <strong>{text.setupTitle}</strong>
            <span>{text.setupBody}</span>
          </div>
        ) : null}

        {seasonGenerationProgress.isOpen ? (
          <SeasonGenerationProgress
            progress={seasonGenerationProgress.value}
            status={seasonGenerationProgress.status}
            text={text}
            onClose={() =>
              setSeasonGenerationProgress((current) => ({
                ...current,
                isOpen: false,
              }))
            }
          />
        ) : null}

        {isScheduleFormOpen ? (
          <ChampionshipScheduleForm
            error={formError}
            fieldErrors={fieldErrors}
            isSaving={generateScheduleMutation.isPending}
            text={text}
            stadiums={stadiums}
            teams={teams}
            onCancel={() => setIsScheduleFormOpen(false)}
            onSubmit={(payload) =>
              submitAction(() => generateScheduleMutation.mutateAsync(payload))
            }
          />
        ) : null}
      </section>

      {confirmation.dialog}

      <section className="panel">
        <div className="section-head">
          <div>
            <p className="eyebrow">{text.standingsEyebrow}</p>
            <h2>{text.standingsTitle}</h2>
          </div>
          <span className="mode-chip">{text.teamsCount(standings.length)}</span>
        </div>
        <StandingsTable
          isLoading={isInitialLoading || standingsQuery.isLoading}
          standings={standings}
          text={text}
          teams={teams}
        />
      </section>

      <section className="panel">
        <div className="section-head">
          <div>
            <p className="eyebrow">{text.scheduleEyebrow}</p>
            <h2>{text.scheduleTitle}</h2>
          </div>
          <span className="mode-chip">
            {text.matchesCount(championshipSchedule.length)}
          </span>
        </div>
        <ScheduleTable
          isLoading={isInitialLoading || scheduleQuery.isLoading}
          matches={championshipSchedule}
          text={text}
          teams={teams}
        />
      </section>

      <section className="panel">
        <div className="section-head">
          <div>
            <p className="eyebrow">{text.leadersEyebrow}</p>
            <h2>{text.leadersTitle}</h2>
          </div>
          <select
            aria-label={text.leaderMetricLabel}
            onChange={(event) => setLeaderMetric(event.target.value)}
            value={leaderMetric}
          >
            {LEADER_METRICS.map((metric) => (
              <option key={metric} value={metric}>
                {text.metricLabels[metric]}
              </option>
            ))}
          </select>
        </div>
        <LeadersTable
          isLoading={isInitialLoading || leadersQuery.isLoading}
          leaders={leaders}
          metric={leaderMetric}
          text={text}
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

function SeasonGenerationProgress({
  progress,
  status,
  text,
  onClose,
}: {
  progress: number;
  status: "running" | "done" | "error";
  text: ChampionshipText;
  onClose: () => void;
}) {
  const statusText =
    status === "done"
      ? text.progressDone
      : status === "error"
        ? text.progressError
        : text.progressRunning;

  return (
    <div className={`progress-panel progress-panel-${status}`}>
      <div className="section-head">
        <div>
          <p className="eyebrow">{text.progressTitle}</p>
          <h2>{statusText}</h2>
        </div>
        {status !== "running" ? (
          <button className="button button-ghost" type="button" onClick={onClose}>
            {text.cancel}
          </button>
        ) : null}
      </div>
      <div
        className="progress-bar"
        role="progressbar"
        aria-valuemin={0}
        aria-valuemax={100}
        aria-valuenow={Math.round(progress)}
      >
        <div className="progress-fill" style={{ width: `${progress}%` }} />
      </div>
      <div className="progress-meta">
        <span>{Math.round(progress)}%</span>
        <span>{text.progressHint}</span>
      </div>
    </div>
  );
}

function ChampionshipScheduleForm({
  teams,
  stadiums,
  isSaving,
  error,
  fieldErrors,
  text,
  onCancel,
  onSubmit,
}: {
  teams: Team[];
  stadiums: Stadium[];
  isSaving: boolean;
  error: string | null;
  fieldErrors: Record<string, string>;
  text: ChampionshipText;
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
        <p className="eyebrow">{text.scheduleFormEyebrow}</p>
        <h2>{text.scheduleFormTitle}</h2>
      </div>
      {error ? <div className="form-error">{error}</div> : null}
      <div className="form-grid">
        <label className="field">
          <span>{text.startDate}</span>
          <input
            onChange={(event) => setDate(event.target.value)}
            required
            type="date"
            value={date}
          />
          <FieldError message={fieldErrors.start_datetime} />
        </label>
        <label className="field">
          <span>{text.matchTime}</span>
          <input
            onChange={(event) => setTime(event.target.value)}
            required
            type="time"
            value={time}
          />
          <FieldError message={fieldErrors.match_time} />
        </label>
        <label className="field">
          <span>{text.intervalDays}</span>
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
          <span>{text.fallbackStadium}</span>
          <select
            onChange={(event) => setFallbackStadiumId(event.target.value)}
            value={fallbackStadiumId}
          >
            <option value="">{text.homeStadiumsOnly}</option>
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
          {isSaving ? text.generating : text.generate}
        </button>
        <button
          className="button button-ghost"
          disabled={isSaving}
          type="button"
          onClick={onCancel}
        >
          {text.cancel}
        </button>
      </div>
    </form>
  );
}

function StandingsTable({
  isLoading,
  standings,
  text,
  teams,
}: {
  isLoading: boolean;
  standings: TeamSeasonStats[];
  text: ChampionshipText;
  teams: Team[];
}) {
  const sorted = [...standings].sort(
    (left, right) => (left.place ?? 9999) - (right.place ?? 9999),
  );

  return (
    <DataTable
      rows={sorted}
      getRowKey={(row) => row.id}
      emptyText={text.noStandings}
      isLoading={isLoading}
      columns={[
        { key: "place", header: "#", render: (row) => row.place ?? "-" },
        {
          key: "team",
          header: text.team,
          render: (row) => (
            <TeamInline
              fallbackName={text.fallbackTeam(row.team_id)}
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
  text,
  teams,
}: {
  isLoading: boolean;
  matches: Match[];
  text: ChampionshipText;
  teams: Team[];
}) {
  return (
    <DataTable
      rows={matches}
      getRowKey={(match) => match.id}
      emptyText={text.noMatches}
      isLoading={isLoading}
      pageSize={50}
      columns={[
        {
          key: "date",
          header: text.date,
          render: (match) => formatDateTime(match.match_datetime, text.locale),
        },
        {
          key: "match",
          header: text.match,
          render: (match) => (
            <Link className="auth-link" to={`/app/matches/${match.id}`}>
              <MatchupInline match={match} teams={teams} />
            </Link>
          ),
        },
        {
          key: "status",
          header: text.status,
          render: (match) => (
            <span className={`status status-${match.status}`}>
              {text.statusLabels[match.status] ?? match.status}
            </span>
          ),
        },
        {
          key: "score",
          header: text.score,
          render: (match) =>
            match.status === "finished"
              ? `${match.home_score ?? 0}:${match.away_score ?? 0}`
              : text.notPlayed,
        },
        {
          key: "ticket",
          header: text.ticket,
          render: (match) => match.ticket_price ?? text.notSet,
        },
      ]}
    />
  );
}

function LeadersTable({
  isLoading,
  leaders,
  metric,
  text,
  players,
}: {
  isLoading: boolean;
  leaders: PlayerSeasonStats[];
  metric: string;
  text: ChampionshipText;
  players: Player[];
}) {
  return (
    <DataTable
      rows={leaders}
      getRowKey={(leader) => leader.id}
      emptyText={text.noLeaders}
      isLoading={isLoading}
      pageSize={25}
      columns={[
        {
          key: "player",
          header: text.player,
          render: (leader) =>
            getPlayerName(leader.player_id, players, text),
        },
        {
          key: "value",
          header: text.metricLabels[metric],
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

function getTeamById(teamId: number, teams: Team[]) {
  return teams.find((team) => team.id === teamId);
}

function getPlayerName(
  playerId: number,
  players: Player[],
  text: ChampionshipText,
) {
  return (
    players.find((player) => player.id === playerId)?.full_name ??
    text.fallbackPlayer(playerId)
  );
}

function formatDateTime(value: string, locale: string) {
  return new Intl.DateTimeFormat(locale, {
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
