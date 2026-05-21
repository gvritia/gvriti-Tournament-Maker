import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState, type FormEvent } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import { DataTable } from "../components/DataTable";
import { TeamMark } from "../components/TeamMark";
import { TeamInline } from "../components/TeamInline";
import { useAuth } from "../features/auth/AuthProvider";
import type { ApiError } from "../shared/api/client";
import {
  addMatchLineup,
  addMatchEvent,
  assignMatchReferee,
  deleteMatchEvent,
  deleteMatchLineup,
  deleteMatch,
  fetchMatchEvents,
  fetchMatchLineups,
  fetchMatch,
  fetchPlayers,
  fetchReferees,
  fetchSeasons,
  fetchStadiums,
  fetchTeams,
  fetchTournaments,
  finishMatch,
  generateMatchLineup,
  generateMatchProtocol,
  rescheduleMatch,
  updateMatchTicketPrice,
} from "../shared/api/endpoints";
import type {
  Match,
  MatchEvent,
  MatchLineup,
  Player,
  Referee,
  Season,
  Stadium,
  Team,
  Tournament,
} from "../shared/api/types";

type ActionMode = "reschedule" | "referee" | "ticket" | null;
type LineupMode = "manual" | "generate" | null;
type ProtocolMode = "event" | "finish" | null;

export function WorkspaceMatchDetailActionsPage() {
  const { token } = useAuth();
  const { matchId } = useParams();
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const safeToken = token ?? "";
  const numericMatchId = Number(matchId);
  const isValidMatchId = Number.isInteger(numericMatchId) && numericMatchId > 0;
  const [actionMode, setActionMode] = useState<ActionMode>(null);
  const [lineupMode, setLineupMode] = useState<LineupMode>(null);
  const [protocolMode, setProtocolMode] = useState<ProtocolMode>(null);
  const [formError, setFormError] = useState<string | null>(null);
  const [lineupError, setLineupError] = useState<string | null>(null);
  const [lineupFieldErrors, setLineupFieldErrors] = useState<Record<string, string>>(
    {},
  );
  const [protocolError, setProtocolError] = useState<string | null>(null);
  const [protocolFieldErrors, setProtocolFieldErrors] = useState<
    Record<string, string>
  >({});
  const [fieldErrors, setFieldErrors] = useState<Record<string, string>>({});
  const [operationError, setOperationError] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);

  const matchQuery = useQuery({
    queryKey: ["match", numericMatchId],
    queryFn: () => fetchMatch(safeToken, numericMatchId),
    enabled: Boolean(token) && isValidMatchId,
  });
  const seasonsQuery = useQuery({
    queryKey: ["seasons"],
    queryFn: () => fetchSeasons(safeToken),
    enabled: Boolean(token) && isValidMatchId,
  });
  const tournamentsQuery = useQuery({
    queryKey: ["tournaments"],
    queryFn: () => fetchTournaments(safeToken),
    enabled: Boolean(token) && isValidMatchId,
  });
  const teamsQuery = useQuery({
    queryKey: ["teams"],
    queryFn: () => fetchTeams(safeToken),
    enabled: Boolean(token) && isValidMatchId,
  });
  const playersQuery = useQuery({
    queryKey: ["players"],
    queryFn: () => fetchPlayers(safeToken),
    enabled: Boolean(token) && isValidMatchId,
  });
  const stadiumsQuery = useQuery({
    queryKey: ["stadiums"],
    queryFn: () => fetchStadiums(safeToken),
    enabled: Boolean(token) && isValidMatchId,
  });
  const refereesQuery = useQuery({
    queryKey: ["referees"],
    queryFn: () => fetchReferees(safeToken),
    enabled: Boolean(token) && isValidMatchId,
  });
  const lineupsQuery = useQuery({
    queryKey: ["lineups", numericMatchId],
    queryFn: () => fetchMatchLineups(safeToken, numericMatchId),
    enabled: Boolean(token) && isValidMatchId,
  });
  const eventsQuery = useQuery({
    queryKey: ["events", numericMatchId],
    queryFn: () => fetchMatchEvents(safeToken, numericMatchId),
    enabled: Boolean(token) && isValidMatchId,
  });

  const match = matchQuery.data;
  const seasons = seasonsQuery.data ?? [];
  const tournaments = tournamentsQuery.data ?? [];
  const teams = teamsQuery.data ?? [];
  const players = playersQuery.data ?? [];
  const stadiums = stadiumsQuery.data ?? [];
  const referees = refereesQuery.data ?? [];
  const areRefereesLoaded = !refereesQuery.isLoading && !refereesQuery.isFetching;
  const lineups = lineupsQuery.data ?? [];
  const events = eventsQuery.data ?? [];
  const error =
    matchQuery.error ??
    seasonsQuery.error ??
    tournamentsQuery.error ??
    teamsQuery.error ??
    playersQuery.error ??
    stadiumsQuery.error ??
    refereesQuery.error ??
    lineupsQuery.error ??
    eventsQuery.error ??
    null;

  const rescheduleMutation = useMutation({
    mutationFn: (matchDatetime: string) =>
      rescheduleMatch(safeToken, numericMatchId, matchDatetime),
    onSuccess: async (updatedMatch) => {
      await invalidateMatchDetailReads(queryClient, updatedMatch);
    },
  });
  const refereeMutation = useMutation({
    mutationFn: (refereeId: number) =>
      assignMatchReferee(safeToken, numericMatchId, refereeId),
    onSuccess: async (updatedMatch) => {
      await invalidateMatchDetailReads(queryClient, updatedMatch);
    },
  });
  const ticketMutation = useMutation({
    mutationFn: (ticketPrice: string) =>
      updateMatchTicketPrice(safeToken, numericMatchId, ticketPrice),
    onSuccess: async (updatedMatch) => {
      await invalidateMatchDetailReads(queryClient, updatedMatch);
    },
  });
  const protocolMutation = useMutation({
    mutationFn: () => generateMatchProtocol(safeToken, numericMatchId),
    onSuccess: async (result) => {
      await invalidateMatchDetailReads(queryClient, result.match);
      setSuccessMessage(`Protocol generated with ${result.events.length} events.`);
    },
  });
  const deleteMutation = useMutation({
    mutationFn: () => deleteMatch(safeToken, numericMatchId),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ["matches"] });
      await queryClient.invalidateQueries({ queryKey: ["match", numericMatchId] });
      navigate("/app/matches");
    },
  });
  const addLineupMutation = useMutation({
    mutationFn: (payload: {
      team_id: number;
      player_id: number;
      is_starting: boolean;
      position: string;
      number: number;
    }) => addMatchLineup(safeToken, numericMatchId, payload),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ["lineups", numericMatchId] });
    },
  });
  const generateLineupMutation = useMutation({
    mutationFn: (payload: {
      team_id: number;
      lineup_size: number;
      starting_size: number | null;
      preferred_player_ids: number[];
      replace_existing: boolean;
    }) => generateMatchLineup(safeToken, numericMatchId, payload),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ["lineups", numericMatchId] });
    },
  });
  const deleteLineupMutation = useMutation({
    mutationFn: (lineupId: number) => deleteMatchLineup(safeToken, lineupId),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ["lineups", numericMatchId] });
    },
  });
  const addEventMutation = useMutation({
    mutationFn: (payload: {
      team_id: number;
      player_id: number;
      assist_player_id: number | null;
      event_type: string;
      minute: number;
    }) => addMatchEvent(safeToken, numericMatchId, payload),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ["events", numericMatchId] });
    },
  });
  const deleteEventMutation = useMutation({
    mutationFn: (eventId: number) => deleteMatchEvent(safeToken, eventId),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ["events", numericMatchId] });
    },
  });
  const finishMutation = useMutation({
    mutationFn: (payload: { homeScore: number; awayScore: number }) =>
      finishMatch(safeToken, numericMatchId, payload.homeScore, payload.awayScore),
    onSuccess: async (updatedMatch) => {
      await invalidateMatchDetailReads(queryClient, updatedMatch);
    },
  });

  if (!isValidMatchId) {
    return (
      <div className="page-stack">
        <section className="notice notice-danger">
          <strong>Invalid match address.</strong>
          <Link to="/app/matches">Back to matches</Link>
        </section>
      </div>
    );
  }

  const isFinished = match?.status === "finished";
  const isSaving =
    rescheduleMutation.isPending ||
    refereeMutation.isPending ||
    ticketMutation.isPending ||
    protocolMutation.isPending ||
    deleteMutation.isPending;
  const isLineupSaving =
    addLineupMutation.isPending ||
    generateLineupMutation.isPending ||
    deleteLineupMutation.isPending;
  const isProtocolSaving =
    addEventMutation.isPending || deleteEventMutation.isPending || finishMutation.isPending;

  function openAction(mode: ActionMode) {
    setActionMode(mode);
    setFormError(null);
    setFieldErrors({});
    setOperationError(null);
    setSuccessMessage(null);
  }

  function closeAction() {
    setActionMode(null);
    setFormError(null);
    setFieldErrors({});
  }

  function openLineup(mode: LineupMode) {
    setLineupMode(mode);
    setLineupError(null);
    setLineupFieldErrors({});
    setSuccessMessage(null);
  }

  function closeLineup() {
    setLineupMode(null);
    setLineupError(null);
    setLineupFieldErrors({});
  }

  function openProtocol(mode: ProtocolMode) {
    setProtocolMode(mode);
    setProtocolError(null);
    setProtocolFieldErrors({});
    setSuccessMessage(null);
  }

  function closeProtocol() {
    setProtocolMode(null);
    setProtocolError(null);
    setProtocolFieldErrors({});
  }

  async function submitAction(action: () => Promise<unknown>) {
    setFormError(null);
    setFieldErrors({});
    setOperationError(null);
    setSuccessMessage(null);

    try {
      await action();
      closeAction();
    } catch (caughtError) {
      const apiError = caughtError as ApiError;
      setFormError(apiError.message);
      setFieldErrors(apiError.fieldErrors ?? {});
    }
  }

  async function submitLineupAction(action: () => Promise<unknown>) {
    setLineupError(null);
    setLineupFieldErrors({});
    setSuccessMessage(null);

    try {
      await action();
      closeLineup();
    } catch (caughtError) {
      const apiError = caughtError as ApiError;
      setLineupError(apiError.message);
      setLineupFieldErrors(apiError.fieldErrors ?? {});
    }
  }

  async function submitProtocolAction(action: () => Promise<unknown>) {
    setProtocolError(null);
    setProtocolFieldErrors({});
    setSuccessMessage(null);

    try {
      await action();
      closeProtocol();
    } catch (caughtError) {
      const apiError = caughtError as ApiError;
      setProtocolError(apiError.message);
      setProtocolFieldErrors(apiError.fieldErrors ?? {});
    }
  }

  async function handleDeleteLineup(lineup: MatchLineup) {
    const confirmed = window.confirm(
      "Убрать этого игрока из состава на матч?",
    );
    if (!confirmed) {
      return;
    }

    setLineupError(null);
    setSuccessMessage(null);
    try {
      await deleteLineupMutation.mutateAsync(lineup.id);
    } catch (caughtError) {
      const apiError = caughtError as ApiError;
      setLineupError(apiError.message);
    }
  }

  async function handleDeleteEvent(event: MatchEvent) {
    const confirmed = window.confirm("Удалить это событие протокола?");
    if (!confirmed) {
      return;
    }

    setProtocolError(null);
    setSuccessMessage(null);
    try {
      await deleteEventMutation.mutateAsync(event.id);
    } catch (caughtError) {
      const apiError = caughtError as ApiError;
      setProtocolError(apiError.message);
    }
  }

  async function handleDelete() {
    if (!match) {
      return;
    }
    const confirmed = window.confirm(
      `Удалить матч "${renderMatchPair(match, teams)}"? Это действие нельзя отменить.`,
    );
    if (!confirmed) {
      return;
    }

    setOperationError(null);
    setSuccessMessage(null);
    try {
      await deleteMutation.mutateAsync();
    } catch (caughtError) {
      const apiError = caughtError as ApiError;
      setOperationError(apiError.message);
    }
  }

  async function handleGenerateProtocol() {
    setFormError(null);
    setFieldErrors({});
    setOperationError(null);
    setSuccessMessage(null);

    try {
      await protocolMutation.mutateAsync();
    } catch (caughtError) {
      const apiError = caughtError as ApiError;
      setOperationError(apiError.message);
    }
  }

  return (
    <div className="page-stack">
      <Link className="back-link" to="/app/matches">
        Назад к матчам
      </Link>

      {error instanceof Error ? (
        <section className="notice notice-danger">
          <strong>Не удалось загрузить матч.</strong>
          <span>{error.message}</span>
        </section>
      ) : null}

      {operationError ? <div className="form-error">{operationError}</div> : null}
      {successMessage ? (
        <section className="notice notice-success">
          <strong>{successMessage}</strong>
        </section>
      ) : null}

      {match ? (
        <>
          <section className="panel match-detail-head">
            <div>
              <p className="eyebrow">
                {getTournamentName(match.tournament_id, tournaments)}
              </p>
              <MatchupTitle match={match} teams={teams} />
              <div className="match-scoreline">{renderScore(match)}</div>
            </div>
            <span className={`status status-${match.status}`}>{match.status}</span>
          </section>

          {areRefereesLoaded && referees.length === 0 && !isFinished ? (
            <section className="notice">
              <strong>Сначала создайте судью.</strong>
              <span>
                Назначение судьи и генерация протокола требуют хотя бы одного
                доступного судьи в разделе{" "}
                <Link className="auth-link" to="/app/referees">
                  «Судьи»
                </Link>
                .
              </span>
            </section>
          ) : null}

          <div className="split-grid">
            <section className="panel">
              <p className="eyebrow">Summary</p>
              <h2>Match data</h2>
              <div className="meta-grid">
                <span>Season: {getSeasonName(match.season_id, seasons)}</span>
                <span>Date: {formatDateTime(match.match_datetime)}</span>
                <span>Stadium: {getStadiumName(match.stadium_id, stadiums)}</span>
                <span>Referee: {getRefereeName(match.referee_id, referees)}</span>
                <span>Round: {match.round_number}</span>
                <span>Stage: {match.stage ?? "none"}</span>
                <span>Ticket: {match.ticket_price ?? "not set"}</span>
                <span>Sold: {match.ticket_sold}</span>
              </div>
              {isFinished ? (
                <p className="warning-text">
                  Матч завершён. Расписание, судья, билет и удаление
                  заблокированы правилами турнира.
                </p>
              ) : null}
            </section>

            <section className="panel">
              <p className="eyebrow">Actions</p>
              <h2>Match actions</h2>
              <div className="action-list">
                <button
                  className="button button-neutral"
                  disabled={isFinished}
                  type="button"
                  onClick={() => openAction("reschedule")}
                >
                  Reschedule
                </button>
                <button
                  className="button button-neutral"
                  disabled={isFinished || !areRefereesLoaded || referees.length === 0}
                  type="button"
                  onClick={() => openAction("referee")}
                >
                  Assign referee
                </button>
                <button
                  className="button button-neutral"
                  disabled={isFinished}
                  type="button"
                  onClick={() => openAction("ticket")}
                >
                  Change ticket
                </button>
                <button
                  className="button button-primary"
                  disabled={
                    isFinished ||
                    isSaving ||
                    ((!areRefereesLoaded || referees.length === 0) &&
                      match.referee_id === null)
                  }
                  type="button"
                  onClick={handleGenerateProtocol}
                >
                  {protocolMutation.isPending ? "Генерируем..." : "Сгенерировать протокол"}
                </button>
                <button
                  className="button button-danger"
                  disabled={isFinished || deleteMutation.isPending}
                  type="button"
                  onClick={handleDelete}
                >
                  Delete
                </button>
              </div>
            </section>
          </div>

          {actionMode === "reschedule" ? (
            <RescheduleForm
              error={formError}
              fieldErrors={fieldErrors}
              isSaving={isSaving}
              match={match}
              onCancel={closeAction}
              onSubmit={(matchDatetime) =>
                submitAction(() => rescheduleMutation.mutateAsync(matchDatetime))
              }
            />
          ) : null}

          {actionMode === "referee" ? (
            <RefereeAssignForm
              error={formError}
              fieldErrors={fieldErrors}
              isSaving={isSaving}
              match={match}
              referees={referees}
              onCancel={closeAction}
              onSubmit={(refereeId) =>
                submitAction(() => refereeMutation.mutateAsync(refereeId))
              }
            />
          ) : null}

          {actionMode === "ticket" ? (
            <TicketPriceForm
              error={formError}
              fieldErrors={fieldErrors}
              isSaving={isSaving}
              match={match}
              onCancel={closeAction}
              onSubmit={(ticketPrice) =>
                submitAction(() => ticketMutation.mutateAsync(ticketPrice))
              }
            />
          ) : null}

          <section className="panel">
            <div className="section-head">
              <div>
                <p className="eyebrow">Lineups</p>
                <h2>Lineups</h2>
              </div>
              <div className="row-actions">
                <button
                  className="button button-ghost"
                  disabled={isFinished}
                  type="button"
                  onClick={() => openLineup("manual")}
                >
                  Add player
                </button>
                <button
                  className="button button-primary"
                  disabled={isFinished}
                  type="button"
                  onClick={() => openLineup("generate")}
                >
                  Generate lineup
                </button>
              </div>
            </div>

            {lineupError ? <div className="form-error">{lineupError}</div> : null}

            {lineupMode === "manual" ? (
              <LineupAddForm
                error={lineupError}
                fieldErrors={lineupFieldErrors}
                isSaving={isLineupSaving}
                lineups={lineups}
                match={match}
                players={players}
                teams={teams}
                onCancel={closeLineup}
                onSubmit={(payload) =>
                  submitLineupAction(() => addLineupMutation.mutateAsync(payload))
                }
              />
            ) : null}

            {lineupMode === "generate" ? (
              <LineupGenerateForm
                error={lineupError}
                fieldErrors={lineupFieldErrors}
                isSaving={isLineupSaving}
                match={match}
                onCancel={closeLineup}
                onSubmit={(payload) =>
                  submitLineupAction(() =>
                    generateLineupMutation.mutateAsync(payload),
                  )
                }
              />
            ) : null}

            <LineupsTable
              isDeleting={deleteLineupMutation.isPending || isFinished}
              lineups={lineups}
              players={players}
              teams={teams}
              onDelete={handleDeleteLineup}
            />
          </section>

          <div className="split-grid">
            <section className="panel">
              <div className="section-head">
                <div>
                  <p className="eyebrow">Protocol</p>
                  <h2>Protocol events</h2>
                </div>
                <div className="row-actions">
                  <button
                    className="button button-ghost"
                    disabled={isFinished}
                    type="button"
                    onClick={() => openProtocol("event")}
                  >
                    Add event
                  </button>
                  <button
                    className="button button-primary"
                    disabled={isFinished}
                    type="button"
                    onClick={() => openProtocol("finish")}
                  >
                    Finish match
                  </button>
                </div>
              </div>

              {protocolError ? (
                <div className="form-error">{protocolError}</div>
              ) : null}

              {protocolMode === "event" ? (
                <ProtocolEventForm
                  error={protocolError}
                  fieldErrors={protocolFieldErrors}
                  isSaving={isProtocolSaving}
                  match={match}
                  players={players}
                  teams={teams}
                  onCancel={closeProtocol}
                  onSubmit={(payload) =>
                    submitProtocolAction(() =>
                      addEventMutation.mutateAsync(payload),
                    )
                  }
                />
              ) : null}

              {protocolMode === "finish" ? (
                <FinishMatchForm
                  error={protocolError}
                  fieldErrors={protocolFieldErrors}
                  isSaving={isProtocolSaving}
                  match={match}
                  onCancel={closeProtocol}
                  onSubmit={(payload) =>
                    submitProtocolAction(() => finishMutation.mutateAsync(payload))
                  }
                />
              ) : null}

              <ProtocolEventsTable
                events={events}
                isDeleting={deleteEventMutation.isPending || isFinished}
                players={players}
                teams={teams}
                onDelete={handleDeleteEvent}
              />
            </section>
          </div>
        </>
      ) : (
        <section className="panel">
          <p className="eyebrow">Loading</p>
          <h2>Loading match</h2>
        </section>
      )}
    </div>
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
        <label className="field">
          <span>Date</span>
          <input
            onChange={(event) => setDate(event.target.value)}
            required
            type="date"
            value={date}
          />
          <FieldError message={fieldErrors.match_datetime} />
        </label>
        <label className="field">
          <span>Time</span>
          <input
            onChange={(event) => setTime(event.target.value)}
            required
            type="time"
            value={time}
          />
        </label>
      </div>
      <FormActions
        isSaving={isSaving}
        isSubmitDisabled={!date || !time}
        onCancel={onCancel}
      />
    </form>
  );
}

function LineupAddForm({
  match,
  teams,
  players,
  lineups,
  isSaving,
  error,
  fieldErrors,
  onCancel,
  onSubmit,
}: {
  match: Match;
  teams: Team[];
  players: Player[];
  lineups: MatchLineup[];
  isSaving: boolean;
  error: string | null;
  fieldErrors: Record<string, string>;
  onCancel: () => void;
  onSubmit: (payload: {
    team_id: number;
    player_id: number;
    is_starting: boolean;
    position: string;
    number: number;
  }) => Promise<void>;
}) {
  const participantTeams = teams.filter(
    (team) => team.id === match.home_team_id || team.id === match.away_team_id,
  );
  const [teamId, setTeamId] = useState(String(match.home_team_id));
  const selectedTeamPlayers = players.filter(
    (player) => player.team_id === Number(teamId),
  );
  const usedPlayerIds = new Set(lineups.map((lineup) => lineup.player_id));
  const availablePlayers = selectedTeamPlayers.filter(
    (player) => !usedPlayerIds.has(player.id),
  );
  const [playerId, setPlayerId] = useState(
    availablePlayers[0] ? String(availablePlayers[0].id) : "",
  );
  const selectedPlayer = players.find((player) => player.id === Number(playerId));
  const [position, setPosition] = useState(selectedPlayer?.position ?? "");
  const [number, setNumber] = useState(
    selectedPlayer ? String(selectedPlayer.number) : "",
  );
  const [isStarting, setIsStarting] = useState(true);

  function handleTeamChange(nextTeamId: string) {
    const nextPlayers = players.filter((player) => player.team_id === Number(nextTeamId));
    const nextAvailablePlayers = nextPlayers.filter(
      (player) => !usedPlayerIds.has(player.id),
    );
    const nextPlayer = nextAvailablePlayers[0];
    setTeamId(nextTeamId);
    setPlayerId(nextPlayer ? String(nextPlayer.id) : "");
    setPosition(nextPlayer?.position ?? "");
    setNumber(nextPlayer ? String(nextPlayer.number) : "");
  }

  function handlePlayerChange(nextPlayerId: string) {
    const nextPlayer = players.find((player) => player.id === Number(nextPlayerId));
    setPlayerId(nextPlayerId);
    setPosition(nextPlayer?.position ?? "");
    setNumber(nextPlayer ? String(nextPlayer.number) : "");
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    await onSubmit({
      team_id: Number(teamId),
      player_id: Number(playerId),
      is_starting: isStarting,
      position: position.trim(),
      number: Number(number),
    });
  }

  return (
    <form className="inline-form" onSubmit={handleSubmit}>
      <FormHeading eyebrow="Lineup" title="Add player" />
      {error ? <div className="form-error">{error}</div> : null}
      <div className="form-grid">
        <label className="field">
          <span>Team</span>
          <select onChange={(event) => handleTeamChange(event.target.value)} value={teamId}>
            {participantTeams.map((team) => (
              <option key={team.id} value={team.id}>
                {team.name}
              </option>
            ))}
          </select>
          <FieldError message={fieldErrors.team_id} />
        </label>
        <label className="field">
          <span>Player</span>
          <select
            onChange={(event) => handlePlayerChange(event.target.value)}
            required
            value={playerId}
          >
            {availablePlayers.map((player) => (
              <option key={player.id} value={player.id}>
                #{player.number} {player.full_name}
              </option>
            ))}
          </select>
          <FieldError message={fieldErrors.player_id} />
        </label>
        <label className="field">
          <span>Position</span>
          <input
            onChange={(event) => setPosition(event.target.value)}
            required
            value={position}
          />
          <FieldError message={fieldErrors.position} />
        </label>
        <label className="field">
          <span>Number</span>
          <input
            min={1}
            max={99}
            onChange={(event) => setNumber(event.target.value)}
            required
            type="number"
            value={number}
          />
          <FieldError message={fieldErrors.number} />
        </label>
        <label className="field">
          <span>Role</span>
          <select
            onChange={(event) => setIsStarting(event.target.value === "yes")}
            value={isStarting ? "yes" : "no"}
          >
            <option value="yes">starting</option>
            <option value="no">bench</option>
          </select>
          <FieldError message={fieldErrors.is_starting} />
        </label>
      </div>
      <FormActions
        isSaving={isSaving}
        isSubmitDisabled={!playerId || !position.trim() || Number(number) < 1}
        onCancel={onCancel}
      />
    </form>
  );
}

function LineupGenerateForm({
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
  onSubmit: (payload: {
    team_id: number;
    lineup_size: number;
    starting_size: number | null;
    preferred_player_ids: number[];
    replace_existing: boolean;
  }) => Promise<void>;
}) {
  const [teamId, setTeamId] = useState(String(match.home_team_id));
  const [lineupSize, setLineupSize] = useState("11");
  const [startingSize, setStartingSize] = useState("11");
  const [replaceExisting, setReplaceExisting] = useState(false);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    await onSubmit({
      team_id: Number(teamId),
      lineup_size: Number(lineupSize),
      starting_size: startingSize ? Number(startingSize) : null,
      preferred_player_ids: [],
      replace_existing: replaceExisting,
    });
  }

  return (
    <form className="inline-form" onSubmit={handleSubmit}>
      <FormHeading eyebrow="Lineup" title="Generate lineup" />
      {error ? <div className="form-error">{error}</div> : null}
      <div className="form-grid">
        <label className="field">
          <span>Team</span>
          <select onChange={(event) => setTeamId(event.target.value)} value={teamId}>
            <option value={match.home_team_id}>Home team</option>
            <option value={match.away_team_id}>Away team</option>
          </select>
          <FieldError message={fieldErrors.team_id} />
        </label>
        <label className="field">
          <span>Lineup size</span>
          <input
            min={1}
            max={25}
            onChange={(event) => setLineupSize(event.target.value)}
            required
            type="number"
            value={lineupSize}
          />
          <FieldError message={fieldErrors.lineup_size} />
        </label>
        <label className="field">
          <span>Starting size</span>
          <input
            min={0}
            max={11}
            onChange={(event) => setStartingSize(event.target.value)}
            type="number"
            value={startingSize}
          />
          <FieldError message={fieldErrors.starting_size} />
        </label>
        <label className="field">
          <span>Replace existing</span>
          <select
            onChange={(event) => setReplaceExisting(event.target.value === "yes")}
            value={replaceExisting ? "yes" : "no"}
          >
            <option value="no">no</option>
            <option value="yes">yes</option>
          </select>
          <FieldError message={fieldErrors.replace_existing} />
        </label>
      </div>
      <FormActions
        isSaving={isSaving}
        isSubmitDisabled={
          Number(lineupSize) < 1 ||
          Number(lineupSize) > 25 ||
          (startingSize !== "" && Number(startingSize) > Number(lineupSize))
        }
        onCancel={onCancel}
      />
    </form>
  );
}

function LineupsTable({
  isDeleting,
  lineups,
  players,
  teams,
  onDelete,
}: {
  isDeleting: boolean;
  lineups: MatchLineup[];
  players: Player[];
  teams: Team[];
  onDelete: (lineup: MatchLineup) => void;
}) {
  return (
    <DataTable
      rows={lineups}
      getRowKey={(lineup) => lineup.id}
      emptyText="No lineup entries yet"
      columns={[
        {
          key: "team",
          header: "Team",
          render: (lineup) => (
            <TeamInline
              fallbackName={`Team ${lineup.team_id}`}
              team={getTeamById(lineup.team_id, teams)}
            />
          ),
        },
        {
          key: "player",
          header: "Player",
          render: (lineup) => getPlayerName(lineup.player_id, players),
        },
        { key: "number", header: "#", render: (lineup) => lineup.number },
        {
          key: "position",
          header: "Position",
          render: (lineup) => lineup.position,
        },
        {
          key: "starting",
          header: "Role",
          render: (lineup) => (lineup.is_starting ? "starting" : "bench"),
        },
        {
          key: "actions",
          header: "Actions",
          render: (lineup) => (
            <button
              className="button button-danger"
              disabled={isDeleting}
              type="button"
              onClick={() => onDelete(lineup)}
            >
              Remove
            </button>
          ),
        },
      ]}
    />
  );
}

function ProtocolEventForm({
  match,
  teams,
  players,
  isSaving,
  error,
  fieldErrors,
  onCancel,
  onSubmit,
}: {
  match: Match;
  teams: Team[];
  players: Player[];
  isSaving: boolean;
  error: string | null;
  fieldErrors: Record<string, string>;
  onCancel: () => void;
  onSubmit: (payload: {
    team_id: number;
    player_id: number;
    assist_player_id: number | null;
    event_type: string;
    minute: number;
  }) => Promise<void>;
}) {
  const participantTeams = teams.filter(
    (team) => team.id === match.home_team_id || team.id === match.away_team_id,
  );
  const [teamId, setTeamId] = useState(String(match.home_team_id));
  const teamPlayers = players.filter((player) => player.team_id === Number(teamId));
  const [playerId, setPlayerId] = useState(
    teamPlayers[0] ? String(teamPlayers[0].id) : "",
  );
  const [assistPlayerId, setAssistPlayerId] = useState("");
  const [eventType, setEventType] = useState("goal");
  const [minute, setMinute] = useState("1");

  function handleTeamChange(nextTeamId: string) {
    const nextPlayers = players.filter(
      (player) => player.team_id === Number(nextTeamId),
    );
    setTeamId(nextTeamId);
    setPlayerId(nextPlayers[0] ? String(nextPlayers[0].id) : "");
    setAssistPlayerId("");
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    await onSubmit({
      team_id: Number(teamId),
      player_id: Number(playerId),
      assist_player_id: assistPlayerId ? Number(assistPlayerId) : null,
      event_type: eventType,
      minute: Number(minute),
    });
  }

  return (
    <form className="inline-form" onSubmit={handleSubmit}>
      <FormHeading eyebrow="Protocol" title="Add event" />
      {error ? <div className="form-error">{error}</div> : null}
      <div className="form-grid">
        <label className="field">
          <span>Team</span>
          <select onChange={(event) => handleTeamChange(event.target.value)} value={teamId}>
            {participantTeams.map((team) => (
              <option key={team.id} value={team.id}>
                {team.name}
              </option>
            ))}
          </select>
          <FieldError message={fieldErrors.team_id} />
        </label>
        <label className="field">
          <span>Player</span>
          <select
            onChange={(event) => setPlayerId(event.target.value)}
            required
            value={playerId}
          >
            {teamPlayers.map((player) => (
              <option key={player.id} value={player.id}>
                #{player.number} {player.full_name}
              </option>
            ))}
          </select>
          <FieldError message={fieldErrors.player_id} />
        </label>
        <label className="field">
          <span>Event</span>
          <select
            onChange={(event) => setEventType(event.target.value)}
            value={eventType}
          >
            <option value="goal">goal</option>
            <option value="assist">assist</option>
            <option value="save">save</option>
            <option value="yellow_card">yellow_card</option>
            <option value="red_card">red_card</option>
          </select>
          <FieldError message={fieldErrors.event_type} />
        </label>
        <label className="field">
          <span>Assist player</span>
          <select
            disabled={eventType !== "goal"}
            onChange={(event) => setAssistPlayerId(event.target.value)}
            value={assistPlayerId}
          >
            <option value="">None</option>
            {teamPlayers
              .filter((player) => String(player.id) !== playerId)
              .map((player) => (
                <option key={player.id} value={player.id}>
                  {player.full_name}
                </option>
              ))}
          </select>
          <FieldError message={fieldErrors.assist_player_id} />
        </label>
        <label className="field">
          <span>Minute</span>
          <input
            min={0}
            max={130}
            onChange={(event) => setMinute(event.target.value)}
            required
            type="number"
            value={minute}
          />
          <FieldError message={fieldErrors.minute} />
        </label>
      </div>
      <FormActions
        isSaving={isSaving}
        isSubmitDisabled={!playerId || Number(minute) < 0 || Number(minute) > 130}
        onCancel={onCancel}
      />
    </form>
  );
}

function FinishMatchForm({
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
  onSubmit: (payload: { homeScore: number; awayScore: number }) => Promise<void>;
}) {
  const [homeScore, setHomeScore] = useState(String(match.home_score ?? 0));
  const [awayScore, setAwayScore] = useState(String(match.away_score ?? 0));

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    await onSubmit({
      homeScore: Number(homeScore),
      awayScore: Number(awayScore),
    });
  }

  return (
    <form className="inline-form" onSubmit={handleSubmit}>
      <FormHeading eyebrow="Finish" title="Finish match" />
      {error ? <div className="form-error">{error}</div> : null}
      <div className="form-grid">
        <label className="field">
          <span>Home score</span>
          <input
            min={0}
            onChange={(event) => setHomeScore(event.target.value)}
            required
            type="number"
            value={homeScore}
          />
          <FieldError message={fieldErrors.home_score} />
        </label>
        <label className="field">
          <span>Away score</span>
          <input
            min={0}
            onChange={(event) => setAwayScore(event.target.value)}
            required
            type="number"
            value={awayScore}
          />
          <FieldError message={fieldErrors.away_score} />
        </label>
      </div>
      <p className="muted">
        Итоговый счёт должен совпадать с голами, внесёнными в протокол.
      </p>
      <FormActions
        isSaving={isSaving}
        isSubmitDisabled={Number(homeScore) < 0 || Number(awayScore) < 0}
        onCancel={onCancel}
      />
    </form>
  );
}

function ProtocolEventsTable({
  events,
  players,
  teams,
  isDeleting,
  onDelete,
}: {
  events: MatchEvent[];
  players: Player[];
  teams: Team[];
  isDeleting: boolean;
  onDelete: (event: MatchEvent) => void;
}) {
  const sortedEvents = [...events].sort((left, right) => left.minute - right.minute);

  return (
    <DataTable
      rows={sortedEvents}
      getRowKey={(event) => event.id}
      emptyText="No protocol events yet"
      columns={[
        { key: "minute", header: "Min", render: (event) => event.minute },
        {
          key: "type",
          header: "Event",
          render: (event) => event.event_type,
        },
        {
          key: "team",
          header: "Team",
          render: (event) => (
            <TeamInline
              fallbackName={`Team ${event.team_id}`}
              team={getTeamById(event.team_id, teams)}
            />
          ),
        },
        {
          key: "player",
          header: "Player",
          render: (event) => getPlayerName(event.player_id, players),
        },
        {
          key: "assist",
          header: "Assist",
          render: (event) =>
            event.assist_player_id
              ? getPlayerName(event.assist_player_id, players)
              : "none",
        },
        {
          key: "actions",
          header: "Actions",
          render: (event) => (
            <button
              className="button button-danger"
              disabled={isDeleting}
              type="button"
              onClick={() => onDelete(event)}
            >
              Remove
            </button>
          ),
        },
      ]}
    />
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
      <label className="field">
        <span>Referee</span>
        <select
          onChange={(event) => setRefereeId(event.target.value)}
          required
          value={refereeId}
        >
          {referees.map((referee) => (
            <option key={referee.id} value={referee.id}>
              {referee.full_name}
            </option>
          ))}
        </select>
        <FieldError message={fieldErrors.referee_id} />
      </label>
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

function MatchupTitle({ match, teams }: { match: Match; teams: Team[] }) {
  const homeTeam = getTeamById(match.home_team_id, teams);
  const awayTeam = getTeamById(match.away_team_id, teams);

  return (
    <div className="matchup-title" aria-label={renderMatchPair(match, teams)}>
      <MatchupTeam team={homeTeam} fallbackName={`Team ${match.home_team_id}`} />
      <span className="matchup-separator">-</span>
      <MatchupTeam team={awayTeam} fallbackName={`Team ${match.away_team_id}`} />
    </div>
  );
}

function MatchupTeam({
  team,
  fallbackName,
}: {
  team: Team | undefined;
  fallbackName: string;
}) {
  if (!team) {
    return <h2 className="matchup-team-name">{fallbackName}</h2>;
  }

  return (
    <div className="matchup-team">
      <TeamMark team={team} size="large" />
      <h2 className="matchup-team-name">{team.name}</h2>
    </div>
  );
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

function getSeasonName(seasonId: number, seasons: Season[]) {
  return seasons.find((season) => season.id === seasonId)?.name ?? `Season ${seasonId}`;
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

async function invalidateMatchDetailReads(
  queryClient: ReturnType<typeof useQueryClient>,
  match: Match,
) {
  await queryClient.invalidateQueries({ queryKey: ["matches"] });
  await queryClient.invalidateQueries({ queryKey: ["match", match.id] });
  await queryClient.invalidateQueries({ queryKey: ["lineups", match.id] });
  await queryClient.invalidateQueries({ queryKey: ["events", match.id] });
  await queryClient.invalidateQueries({ queryKey: ["standings"] });
  await queryClient.invalidateQueries({ queryKey: ["leaders"] });
  await queryClient.invalidateQueries({ queryKey: ["cupBracket"] });
}
