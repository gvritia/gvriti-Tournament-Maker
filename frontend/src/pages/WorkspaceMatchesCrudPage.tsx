import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useMemo, useState, type FormEvent } from "react";
import { Link } from "react-router-dom";
import { DataTable } from "../components/DataTable";
import { MatchupInline } from "../components/MatchupInline";
import { useAuth } from "../features/auth/AuthProvider";
import type { ApiError } from "../shared/api/client";
import {
  assignMatchReferee,
  createMatch,
  deleteMatch,
  fetchMatches,
  fetchReferees,
  fetchSeasons,
  fetchStadiums,
  fetchTeams,
  fetchTournaments,
  rescheduleMatch,
  updateMatchTicketPrice,
} from "../shared/api/endpoints";
import type {
  Match,
  Referee,
  Season,
  Stadium,
  Team,
  Tournament,
} from "../shared/api/types";

type MatchFormValues = {
  season_id: string;
  tournament_id: string;
  home_team_id: string;
  away_team_id: string;
  stadium_id: string;
  referee_id: string;
  match_date: string;
  match_time: string;
  round_number: string;
  stage: string;
};

type MatchFormPayload = {
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

type ActionMode = "create" | "reschedule" | "referee" | "ticket" | null;

export function WorkspaceMatchesCrudPage() {
  const { token } = useAuth();
  const safeToken = token ?? "";
  const queryClient = useQueryClient();
  const [seasonId, setSeasonId] = useState("all");
  const [tournamentId, setTournamentId] = useState("all");
  const [teamId, setTeamId] = useState("all");
  const [status, setStatus] = useState("all");
  const [dateFrom, setDateFrom] = useState("");
  const [dateTo, setDateTo] = useState("");
  const [actionMode, setActionMode] = useState<ActionMode>(null);
  const [selectedMatch, setSelectedMatch] = useState<Match | null>(null);
  const [formError, setFormError] = useState<string | null>(null);
  const [fieldErrors, setFieldErrors] = useState<Record<string, string>>({});
  const [operationError, setOperationError] = useState<string | null>(null);

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
  const stadiumsQuery = useQuery({
    queryKey: ["stadiums"],
    queryFn: () => fetchStadiums(safeToken),
    enabled: Boolean(token),
  });
  const refereesQuery = useQuery({
    queryKey: ["referees"],
    queryFn: () => fetchReferees(safeToken),
    enabled: Boolean(token),
  });
  const matchesQuery = useQuery({
    queryKey: ["matches"],
    queryFn: () => fetchMatches(safeToken),
    enabled: Boolean(token),
  });

  const seasons = seasonsQuery.data ?? [];
  const tournaments = tournamentsQuery.data ?? [];
  const teams = teamsQuery.data ?? [];
  const stadiums = stadiumsQuery.data ?? [];
  const referees = refereesQuery.data ?? [];
  const matches = matchesQuery.data ?? [];
  const error =
    seasonsQuery.error ??
    tournamentsQuery.error ??
    teamsQuery.error ??
    stadiumsQuery.error ??
    refereesQuery.error ??
    matchesQuery.error ??
    null;
  const isInitialLoading =
    seasonsQuery.isLoading ||
    tournamentsQuery.isLoading ||
    teamsQuery.isLoading ||
    stadiumsQuery.isLoading ||
    refereesQuery.isLoading ||
    matchesQuery.isLoading;

  const filteredMatches = useMemo(() => {
    return matches.filter((match) => {
      const matchDate = match.match_datetime.slice(0, 10);
      const bySeason = seasonId === "all" || match.season_id === Number(seasonId);
      const byTournament =
        tournamentId === "all" || match.tournament_id === Number(tournamentId);
      const byTeam =
        teamId === "all" ||
        match.home_team_id === Number(teamId) ||
        match.away_team_id === Number(teamId);
      const byStatus = status === "all" || match.status === status;
      const byDateFrom = !dateFrom || matchDate >= dateFrom;
      const byDateTo = !dateTo || matchDate <= dateTo;

      return (
        bySeason &&
        byTournament &&
        byTeam &&
        byStatus &&
        byDateFrom &&
        byDateTo
      );
    });
  }, [dateFrom, dateTo, matches, seasonId, status, teamId, tournamentId]);

  const createMutation = useMutation({
    mutationFn: (payload: MatchFormPayload) => createMatch(safeToken, payload),
    onSuccess: async (match) => {
      await invalidateMatchReads(queryClient, match.id);
    },
  });

  const rescheduleMutation = useMutation({
    mutationFn: (payload: { matchId: number; matchDatetime: string }) =>
      rescheduleMatch(safeToken, payload.matchId, payload.matchDatetime),
    onSuccess: async (match) => {
      await invalidateMatchReads(queryClient, match.id);
    },
  });

  const refereeMutation = useMutation({
    mutationFn: (payload: { matchId: number; refereeId: number }) =>
      assignMatchReferee(safeToken, payload.matchId, payload.refereeId),
    onSuccess: async (match) => {
      await invalidateMatchReads(queryClient, match.id);
    },
  });

  const ticketMutation = useMutation({
    mutationFn: (payload: { matchId: number; ticketPrice: string }) =>
      updateMatchTicketPrice(safeToken, payload.matchId, payload.ticketPrice),
    onSuccess: async (match) => {
      await invalidateMatchReads(queryClient, match.id);
    },
  });

  const deleteMutation = useMutation({
    mutationFn: (match: Match) => deleteMatch(safeToken, match.id),
    onSuccess: async (_data, match) => {
      await invalidateMatchReads(queryClient, match.id);
    },
  });

  const isSaving =
    createMutation.isPending ||
    rescheduleMutation.isPending ||
    refereeMutation.isPending ||
    ticketMutation.isPending;
  const canCreateMatch =
    seasons.length > 0 &&
    tournaments.length > 0 &&
    teams.length >= 2 &&
    stadiums.length > 0;

  function openAction(mode: ActionMode, match: Match | null = null) {
    setActionMode(mode);
    setSelectedMatch(match);
    setFormError(null);
    setFieldErrors({});
    setOperationError(null);
  }

  function closeAction() {
    setActionMode(null);
    setSelectedMatch(null);
    setFormError(null);
    setFieldErrors({});
  }

  async function handleCreate(values: MatchFormPayload) {
    await submitAction(async () => {
      await createMutation.mutateAsync(values);
    });
  }

  async function handleReschedule(matchDatetime: string) {
    if (!selectedMatch) {
      return;
    }
    await submitAction(async () => {
      await rescheduleMutation.mutateAsync({
        matchId: selectedMatch.id,
        matchDatetime,
      });
    });
  }

  async function handleReferee(refereeId: number) {
    if (!selectedMatch) {
      return;
    }
    await submitAction(async () => {
      await refereeMutation.mutateAsync({ matchId: selectedMatch.id, refereeId });
    });
  }

  async function handleTicket(ticketPrice: string) {
    if (!selectedMatch) {
      return;
    }
    await submitAction(async () => {
      await ticketMutation.mutateAsync({
        matchId: selectedMatch.id,
        ticketPrice,
      });
    });
  }

  async function submitAction(action: () => Promise<void>) {
    setFormError(null);
    setFieldErrors({});
    setOperationError(null);

    try {
      await action();
      closeAction();
    } catch (caughtError) {
      const apiError = caughtError as ApiError;
      setFormError(apiError.message);
      setFieldErrors(apiError.fieldErrors ?? {});
    }
  }

  async function handleDelete(match: Match) {
    const confirmed = window.confirm(
      `Удалить матч "${renderMatchPair(match, teams)}"? Это действие нельзя отменить.`,
    );
    if (!confirmed) {
      return;
    }

    setOperationError(null);
    try {
      await deleteMutation.mutateAsync(match);
    } catch (caughtError) {
      const apiError = caughtError as ApiError;
      setOperationError(apiError.message);
    }
  }

  return (
    <div className="page-stack">
      <section className="page-intro">
        <p className="eyebrow">Матчи</p>
        <h2>Матчи</h2>
        <p className="muted">
          Создавайте матчи и управляйте расписанием, назначением судьи, ценой
          билета и удалением, пока матч не завершён.
        </p>
      </section>

      {error instanceof Error ? (
        <section className="notice notice-danger">
          <strong>Не удалось загрузить матчи.</strong>
          <span>{error.message}</span>
        </section>
      ) : null}

      <section className="panel">
        <div className="section-head">
          <div className="filter-row">
            <FilterSelect
              label="Season"
              value={seasonId}
              onChange={setSeasonId}
              allLabel="All seasons"
              options={seasons.map((season) => ({
                value: String(season.id),
                label: season.name,
              }))}
            />
            <FilterSelect
              label="Tournament"
              value={tournamentId}
              onChange={setTournamentId}
              allLabel="All tournaments"
              options={tournaments.map((tournament) => ({
                value: String(tournament.id),
                label: tournament.name,
              }))}
            />
            <FilterSelect
              label="Team"
              value={teamId}
              onChange={setTeamId}
              allLabel="All teams"
              options={teams.map((team) => ({
                value: String(team.id),
                label: team.name,
              }))}
            />
            <select
              aria-label="Status"
              onChange={(event) => setStatus(event.target.value)}
              value={status}
            >
              <option value="all">All statuses</option>
              <option value="scheduled">scheduled</option>
              <option value="postponed">postponed</option>
              <option value="finished">finished</option>
              <option value="cancelled">cancelled</option>
            </select>
            <input
              aria-label="Date from"
              onChange={(event) => setDateFrom(event.target.value)}
              type="date"
              value={dateFrom}
            />
            <input
              aria-label="Date to"
              onChange={(event) => setDateTo(event.target.value)}
              type="date"
              value={dateTo}
            />
          </div>
          <button
            className="button button-primary"
            disabled={!canCreateMatch}
            type="button"
            onClick={() => openAction("create")}
          >
            Create match
          </button>
        </div>

        {operationError ? <div className="form-error">{operationError}</div> : null}

        {!canCreateMatch ? (
          <div className="notice">
            <strong>Complete setup first.</strong>
            <span>
              Creating a match requires a season, tournament, two teams, and a stadium.
            </span>
          </div>
        ) : null}

        {actionMode === "create" ? (
          <MatchCreateForm
            error={formError}
            fieldErrors={fieldErrors}
            isSaving={isSaving}
            seasons={seasons}
            stadiums={stadiums}
            teams={teams}
            tournaments={tournaments}
            referees={referees}
            onCancel={closeAction}
            onSubmit={handleCreate}
          />
        ) : null}

        {actionMode === "reschedule" && selectedMatch ? (
          <RescheduleForm
            error={formError}
            fieldErrors={fieldErrors}
            isSaving={isSaving}
            match={selectedMatch}
            onCancel={closeAction}
            onSubmit={handleReschedule}
          />
        ) : null}

        {actionMode === "referee" && selectedMatch ? (
          <RefereeAssignForm
            error={formError}
            fieldErrors={fieldErrors}
            isSaving={isSaving}
            match={selectedMatch}
            referees={referees}
            onCancel={closeAction}
            onSubmit={handleReferee}
          />
        ) : null}

        {actionMode === "ticket" && selectedMatch ? (
          <TicketPriceForm
            error={formError}
            fieldErrors={fieldErrors}
            isSaving={isSaving}
            match={selectedMatch}
            onCancel={closeAction}
            onSubmit={handleTicket}
          />
        ) : null}

        <DataTable
          rows={filteredMatches}
          getRowKey={(match) => match.id}
          emptyText="No matches found"
          isLoading={isInitialLoading}
          pageSize={50}
          columns={[
            {
              key: "date",
              header: "Date",
              render: (match) => formatDateTime(match.match_datetime),
            },
            {
              key: "tournament",
              header: "Tournament",
              render: (match) => getTournamentName(match.tournament_id, tournaments),
            },
            {
              key: "teams",
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
                <span className={`status status-${match.status}`}>
                  {match.status}
                </span>
              ),
            },
            { key: "score", header: "Score", render: renderScore },
            {
              key: "stadium",
              header: "Stadium",
              render: (match) => getStadiumName(match.stadium_id, stadiums),
            },
            {
              key: "referee",
              header: "Referee",
              render: (match) => getRefereeName(match.referee_id, referees),
            },
            {
              key: "ticket",
              header: "Ticket",
              render: (match) => match.ticket_price ?? "not set",
            },
            {
              key: "actions",
              header: "Actions",
              render: (match) => {
                const isFinished = match.status === "finished";
                return (
                  <div className="row-actions">
                    <Link className="button button-ghost" to={`/app/matches/${match.id}`}>
                      Open
                    </Link>
                    <button
                      className="button button-ghost"
                      disabled={isFinished}
                      type="button"
                      onClick={() => openAction("reschedule", match)}
                    >
                      Reschedule
                    </button>
                    <button
                      className="button button-ghost"
                      disabled={isFinished || referees.length === 0}
                      type="button"
                      onClick={() => openAction("referee", match)}
                    >
                      Referee
                    </button>
                    <button
                      className="button button-ghost"
                      disabled={isFinished}
                      type="button"
                      onClick={() => openAction("ticket", match)}
                    >
                      Ticket
                    </button>
                    <button
                      className="button button-danger"
                      disabled={isFinished || deleteMutation.isPending}
                      type="button"
                      onClick={() => handleDelete(match)}
                    >
                      Удалить
                    </button>
                  </div>
                );
              },
            },
          ]}
        />
      </section>
    </div>
  );
}

function MatchCreateForm({
  seasons,
  tournaments,
  teams,
  stadiums,
  referees,
  isSaving,
  error,
  fieldErrors,
  onCancel,
  onSubmit,
}: {
  seasons: Season[];
  tournaments: Tournament[];
  teams: Team[];
  stadiums: Stadium[];
  referees: Referee[];
  isSaving: boolean;
  error: string | null;
  fieldErrors: Record<string, string>;
  onCancel: () => void;
  onSubmit: (values: MatchFormPayload) => Promise<void>;
}) {
  const [values, setValues] = useState(() =>
    getDefaultMatchValues(seasons, tournaments, teams, stadiums),
  );

  const selectedTournament = tournaments.find(
    (tournament) => tournament.id === Number(values.tournament_id),
  );
  const filteredTournaments = tournaments.filter(
    (tournament) => tournament.season_id === Number(values.season_id),
  );
  const isCup = selectedTournament?.type === "cup";
  const awayTeamOptions = teams.filter(
    (team) => String(team.id) !== values.home_team_id,
  );

  function updateSeason(nextSeasonId: string) {
    const nextTournaments = tournaments.filter(
      (tournament) => tournament.season_id === Number(nextSeasonId),
    );
    setValues((current) => ({
      ...current,
      season_id: nextSeasonId,
      tournament_id: nextTournaments[0]
        ? String(nextTournaments[0].id)
        : current.tournament_id,
    }));
  }

  function updateHomeTeam(nextHomeTeamId: string) {
    setValues((current) => ({
      ...current,
      home_team_id: nextHomeTeamId,
      away_team_id:
        current.away_team_id === nextHomeTeamId
          ? String(teams.find((team) => String(team.id) !== nextHomeTeamId)?.id ?? "")
          : current.away_team_id,
    }));
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    await onSubmit({
      season_id: Number(values.season_id),
      tournament_id: Number(values.tournament_id),
      home_team_id: Number(values.home_team_id),
      away_team_id: Number(values.away_team_id),
      stadium_id: Number(values.stadium_id),
      referee_id: values.referee_id ? Number(values.referee_id) : null,
      match_datetime: `${values.match_date}T${values.match_time}:00`,
      status: "scheduled",
      round_number: Number(values.round_number),
      stage: isCup && values.stage ? values.stage : null,
    });
  }

  return (
    <form className="inline-form" onSubmit={handleSubmit}>
      <FormHeading eyebrow="Create" title="New match" />
      {error ? <div className="form-error">{error}</div> : null}
      <div className="form-grid">
        <SelectField
          label="Season"
          value={values.season_id}
          error={fieldErrors.season_id}
          onChange={updateSeason}
          options={seasons.map((season) => ({
            value: String(season.id),
            label: season.name,
          }))}
        />
        <SelectField
          label="Tournament"
          value={values.tournament_id}
          error={fieldErrors.tournament_id}
          onChange={(tournament_id) =>
            setValues((current) => ({ ...current, tournament_id }))
          }
          options={filteredTournaments.map((tournament) => ({
            value: String(tournament.id),
            label: tournament.name,
          }))}
        />
        <SelectField
          label="Home team"
          value={values.home_team_id}
          error={fieldErrors.home_team_id}
          onChange={updateHomeTeam}
          options={teams.map((team) => ({
            value: String(team.id),
            label: team.name,
          }))}
        />
        <SelectField
          label="Away team"
          value={values.away_team_id}
          error={fieldErrors.away_team_id}
          onChange={(away_team_id) =>
            setValues((current) => ({ ...current, away_team_id }))
          }
          options={awayTeamOptions.map((team) => ({
            value: String(team.id),
            label: team.name,
          }))}
        />
        <SelectField
          label="Stadium"
          value={values.stadium_id}
          error={fieldErrors.stadium_id}
          onChange={(stadium_id) =>
            setValues((current) => ({ ...current, stadium_id }))
          }
          options={stadiums.map((stadium) => ({
            value: String(stadium.id),
            label: stadium.name,
          }))}
        />
        <SelectField
          label="Referee"
          value={values.referee_id}
          error={fieldErrors.referee_id}
          onChange={(referee_id) =>
            setValues((current) => ({ ...current, referee_id }))
          }
          options={[
            { value: "", label: "Не назначен" },
            ...referees.map((referee) => ({
              value: String(referee.id),
              label: referee.full_name,
            })),
          ]}
        />
        <DateTimeFields
          date={values.match_date}
          time={values.match_time}
          error={fieldErrors.match_datetime}
          onDateChange={(match_date) =>
            setValues((current) => ({ ...current, match_date }))
          }
          onTimeChange={(match_time) =>
            setValues((current) => ({ ...current, match_time }))
          }
        />
        <label className="field">
          <span>Round</span>
          <input
            min={1}
            onChange={(event) =>
              setValues((current) => ({
                ...current,
                round_number: event.target.value,
              }))
            }
            required
            type="number"
            value={values.round_number}
          />
          <FieldError message={fieldErrors.round_number} />
        </label>
        <SelectField
          label="Cup stage"
          value={values.stage}
          disabled={!isCup}
          error={fieldErrors.stage}
          onChange={(stage) => setValues((current) => ({ ...current, stage }))}
          options={[
            { value: "", label: "None" },
            { value: "semifinal", label: "semifinal" },
            { value: "final", label: "final" },
          ]}
        />
      </div>
      <FormActions
        isSaving={isSaving}
        isSubmitDisabled={
          !values.season_id ||
          !values.tournament_id ||
          !values.home_team_id ||
          !values.away_team_id ||
          values.home_team_id === values.away_team_id ||
          !values.stadium_id ||
          !values.match_date ||
          !values.match_time ||
          Number(values.round_number) < 1
        }
        onCancel={onCancel}
      />
    </form>
  );
}

function RescheduleForm({
  match,
  isSaving,
  error,
  fieldErrors,
  onCancel,
  onSubmit,
}: {
  match: Match;
  isSaving: boolean;
  error: string | null;
  fieldErrors: Record<string, string>;
  onCancel: () => void;
  onSubmit: (matchDatetime: string) => Promise<void>;
}) {
  const [date, setDate] = useState(match.match_datetime.slice(0, 10));
  const [time, setTime] = useState(match.match_datetime.slice(11, 16));

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    await onSubmit(`${date}T${time}:00`);
  }

  return (
    <form className="inline-form" onSubmit={handleSubmit}>
      <FormHeading eyebrow="Schedule" title="Reschedule match" />
      {error ? <div className="form-error">{error}</div> : null}
      <div className="form-grid">
        <DateTimeFields
          date={date}
          time={time}
          error={fieldErrors.match_datetime}
          onDateChange={setDate}
          onTimeChange={setTime}
        />
      </div>
      <FormActions
        isSaving={isSaving}
        isSubmitDisabled={!date || !time}
        onCancel={onCancel}
      />
    </form>
  );
}

function RefereeAssignForm({
  match,
  referees,
  isSaving,
  error,
  fieldErrors,
  onCancel,
  onSubmit,
}: {
  match: Match;
  referees: Referee[];
  isSaving: boolean;
  error: string | null;
  fieldErrors: Record<string, string>;
  onCancel: () => void;
  onSubmit: (refereeId: number) => Promise<void>;
}) {
  const [refereeId, setRefereeId] = useState(
    match.referee_id ? String(match.referee_id) : String(referees[0]?.id ?? ""),
  );

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    await onSubmit(Number(refereeId));
  }

  return (
    <form className="inline-form" onSubmit={handleSubmit}>
      <FormHeading eyebrow="Referee" title="Assign referee" />
      {error ? <div className="form-error">{error}</div> : null}
      <SelectField
        label="Referee"
        value={refereeId}
        error={fieldErrors.referee_id}
        onChange={setRefereeId}
        options={referees.map((referee) => ({
          value: String(referee.id),
          label: referee.full_name,
        }))}
      />
      <FormActions
        isSaving={isSaving}
        isSubmitDisabled={!refereeId}
        onCancel={onCancel}
      />
    </form>
  );
}

function TicketPriceForm({
  match,
  isSaving,
  error,
  fieldErrors,
  onCancel,
  onSubmit,
}: {
  match: Match;
  isSaving: boolean;
  error: string | null;
  fieldErrors: Record<string, string>;
  onCancel: () => void;
  onSubmit: (ticketPrice: string) => Promise<void>;
}) {
  const [ticketPrice, setTicketPrice] = useState(match.ticket_price ?? "");

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    await onSubmit(ticketPrice);
  }

  return (
    <form className="inline-form" onSubmit={handleSubmit}>
      <FormHeading eyebrow="Ticket" title="Change ticket price" />
      {error ? <div className="form-error">{error}</div> : null}
      <label className="field">
        <span>Ticket price</span>
        <input
          min="0.01"
          onChange={(event) => setTicketPrice(event.target.value)}
          required
          step="0.01"
          type="number"
          value={ticketPrice}
        />
        <FieldError message={fieldErrors.ticket_price} />
      </label>
      <FormActions
        isSaving={isSaving}
        isSubmitDisabled={!ticketPrice || Number(ticketPrice) <= 0}
        onCancel={onCancel}
      />
    </form>
  );
}

function FilterSelect({
  allLabel,
  label,
  onChange,
  options,
  value,
}: {
  allLabel: string;
  label: string;
  onChange: (value: string) => void;
  options: Array<{ value: string; label: string }>;
  value: string;
}) {
  return (
    <select
      aria-label={label}
      onChange={(event) => onChange(event.target.value)}
      value={value}
    >
      <option value="all">{allLabel}</option>
      {options.map((option) => (
        <option key={option.value} value={option.value}>
          {option.label}
        </option>
      ))}
    </select>
  );
}

function SelectField({
  disabled,
  error,
  label,
  onChange,
  options,
  value,
}: {
  disabled?: boolean;
  error?: string;
  label: string;
  onChange: (value: string) => void;
  options: Array<{ value: string; label: string }>;
  value: string;
}) {
  return (
    <label className="field">
      <span>{label}</span>
      <select
        disabled={disabled}
        onChange={(event) => onChange(event.target.value)}
        required
        value={value}
      >
        {options.map((option) => (
          <option key={option.value || "empty"} value={option.value}>
            {option.label}
          </option>
        ))}
      </select>
      <FieldError message={error} />
    </label>
  );
}

function DateTimeFields({
  date,
  error,
  onDateChange,
  onTimeChange,
  time,
}: {
  date: string;
  error?: string;
  onDateChange: (value: string) => void;
  onTimeChange: (value: string) => void;
  time: string;
}) {
  return (
    <>
      <label className="field">
        <span>Date</span>
        <input
          onChange={(event) => onDateChange(event.target.value)}
          required
          type="date"
          value={date}
        />
        <FieldError message={error} />
      </label>
      <label className="field">
        <span>Time</span>
        <input
          onChange={(event) => onTimeChange(event.target.value)}
          required
          type="time"
          value={time}
        />
      </label>
    </>
  );
}

function FormHeading({ eyebrow, title }: { eyebrow: string; title: string }) {
  return (
    <div>
      <p className="eyebrow">{eyebrow}</p>
      <h2>{title}</h2>
    </div>
  );
}

function FormActions({
  isSaving,
  isSubmitDisabled,
  onCancel,
}: {
  isSaving: boolean;
  isSubmitDisabled: boolean;
  onCancel: () => void;
}) {
  return (
    <div className="form-actions">
      <button
        className="button button-primary"
        disabled={isSaving || isSubmitDisabled}
        type="submit"
      >
        {isSaving ? "Saving..." : "Save"}
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
  );
}

function FieldError({ message }: { message?: string }) {
  return message ? <small className="field-error">{message}</small> : null;
}

function getDefaultMatchValues(
  seasons: Season[],
  tournaments: Tournament[],
  teams: Team[],
  stadiums: Stadium[],
): MatchFormValues {
  const currentSeason = seasons[0];
  const currentTournament =
    tournaments.find((tournament) => tournament.season_id === currentSeason?.id) ??
    tournaments[0];
  const today = new Date();
  const date = today.toISOString().slice(0, 10);

  return {
    season_id: currentSeason ? String(currentSeason.id) : "",
    tournament_id: currentTournament ? String(currentTournament.id) : "",
    home_team_id: teams[0] ? String(teams[0].id) : "",
    away_team_id: teams[1] ? String(teams[1].id) : "",
    stadium_id: stadiums[0] ? String(stadiums[0].id) : "",
    referee_id: "",
    match_date: date,
    match_time: "19:00",
    round_number: "1",
    stage: "",
  };
}

function renderMatchPair(match: Match, teams: Team[]) {
  const home = teams.find((team) => team.id === match.home_team_id)?.name;
  const away = teams.find((team) => team.id === match.away_team_id)?.name;
  return `${home ?? `Team ${match.home_team_id}`} - ${
    away ?? `Team ${match.away_team_id}`
  }`;
}

function renderScore(match: Match) {
  return match.status === "finished"
    ? `${match.home_score ?? 0}:${match.away_score ?? 0}`
    : "not played";
}

function getTournamentName(tournamentId: number, tournaments: Tournament[]) {
  return (
    tournaments.find((tournament) => tournament.id === tournamentId)?.name ??
    `Tournament ${tournamentId}`
  );
}

function getStadiumName(stadiumId: number, stadiums: Stadium[]) {
  return stadiums.find((stadium) => stadium.id === stadiumId)?.name ?? `Stadium ${stadiumId}`;
}

function getRefereeName(refereeId: number | null, referees: Referee[]) {
  if (!refereeId) {
    return "not assigned";
  }

  return (
    referees.find((referee) => referee.id === refereeId)?.full_name ??
    `Referee ${refereeId}`
  );
}

function formatDateTime(value: string) {
  return new Intl.DateTimeFormat("ru-RU", {
    dateStyle: "short",
    timeStyle: "short",
  }).format(new Date(value));
}

async function invalidateMatchReads(
  queryClient: ReturnType<typeof useQueryClient>,
  matchId: number,
) {
  await queryClient.invalidateQueries({ queryKey: ["matches"] });
  await queryClient.invalidateQueries({ queryKey: ["match", matchId] });
  await queryClient.invalidateQueries({ queryKey: ["standings"] });
  await queryClient.invalidateQueries({ queryKey: ["leaders"] });
  await queryClient.invalidateQueries({ queryKey: ["cupBracket"] });
}
