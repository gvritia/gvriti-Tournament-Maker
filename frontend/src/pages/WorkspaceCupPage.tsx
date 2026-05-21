import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState, type FormEvent } from "react";
import { Link } from "react-router-dom";
import { MatchupInline } from "../components/MatchupInline";
import { TeamInline } from "../components/TeamInline";
import { useAuth } from "../features/auth/AuthProvider";
import type { ApiError } from "../shared/api/client";
import {
  fetchCupBracket,
  fetchSeasons,
  fetchStadiums,
  fetchTeams,
  fetchTournaments,
  generateCupFinal,
  generateCupSemifinals,
} from "../shared/api/endpoints";
import type {
  CupBracket,
  CupMatchNode,
  Match,
  Season,
  Stadium,
  Team,
  Tournament,
} from "../shared/api/types";

export function WorkspaceCupPage() {
  const { token } = useAuth();
  const safeToken = token ?? "";
  const queryClient = useQueryClient();
  const [selectedSeasonId, setSelectedSeasonId] = useState("");
  const [selectedTournamentId, setSelectedTournamentId] = useState("");
  const [semifinalFormOpen, setSemifinalFormOpen] = useState(false);
  const [finalFormOpen, setFinalFormOpen] = useState(false);
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
  const stadiumsQuery = useQuery({
    queryKey: ["stadiums"],
    queryFn: () => fetchStadiums(safeToken),
    enabled: Boolean(token),
  });

  const seasons = seasonsQuery.data ?? [];
  const tournaments = tournamentsQuery.data ?? [];
  const teams = teamsQuery.data ?? [];
  const stadiums = stadiumsQuery.data ?? [];
  const seasonId = Number(selectedSeasonId || seasons[0]?.id || 0);
  const cupTournaments = tournaments.filter(
    (tournament) =>
      tournament.type === "cup" && (!seasonId || tournament.season_id === seasonId),
  );
  const tournamentId = Number(selectedTournamentId || cupTournaments[0]?.id || 0);

  const bracketQuery = useQuery({
    queryKey: ["cupBracket", tournamentId],
    queryFn: () => fetchCupBracket(safeToken, tournamentId),
    enabled: Boolean(token) && tournamentId > 0,
  });

  const bracket = bracketQuery.data;
  const semifinals = bracket?.semifinals ?? [];
  const hasSemifinals = semifinals.length > 0;
  const hasFinal = Boolean(bracket?.final);
  const hasFinishedSemifinalWinners =
    semifinals.length === 2 &&
    semifinals.every(
      (node) => node.match.status === "finished" && Boolean(node.winner_team_id),
    );
  const error =
    seasonsQuery.error ??
    tournamentsQuery.error ??
    teamsQuery.error ??
    stadiumsQuery.error ??
    bracketQuery.error ??
    null;

  const semifinalsMutation = useMutation({
    mutationFn: (payload: CupSemifinalsFormPayload) =>
      generateCupSemifinals(safeToken, tournamentId, payload),
    onSuccess: async (matches) => {
      await invalidateCupReads(queryClient, tournamentId);
      setSuccessMessage(`Generated ${matches.length} cup semifinals.`);
    },
  });
  const finalMutation = useMutation({
    mutationFn: (payload: CupFinalFormPayload) =>
      generateCupFinal(safeToken, tournamentId, payload),
    onSuccess: async () => {
      await invalidateCupReads(queryClient, tournamentId);
      setSuccessMessage("Cup final generated.");
    },
  });

  function handleSeasonChange(nextSeasonId: string) {
    const nextTournament = tournaments.find(
      (tournament) =>
        tournament.type === "cup" && tournament.season_id === Number(nextSeasonId),
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
      setSemifinalFormOpen(false);
      setFinalFormOpen(false);
    } catch (caughtError) {
      const apiError = caughtError as ApiError;
      setFormError(apiError.message);
      setOperationError(apiError.message);
      setFieldErrors(apiError.fieldErrors ?? {});
    }
  }

  const canGenerateSemifinals =
    tournamentId > 0 && teams.length >= 4 && !bracketQuery.isLoading && !hasSemifinals;
  const canGenerateFinal =
    tournamentId > 0 &&
    stadiums.length > 0 &&
    !bracketQuery.isLoading &&
    hasFinishedSemifinalWinners &&
    !hasFinal;

  return (
    <div className="page-stack">
      <section className="page-intro">
        <p className="eyebrow">Кубок</p>
        <h2>Кубок</h2>
        <p className="muted">
          Создавайте полуфиналы, добавляйте финал после определения победителей
          и проверяйте кубковую сетку.
        </p>
      </section>

      {error instanceof Error ? (
        <section className="notice notice-danger">
          <strong>Не удалось загрузить данные кубка.</strong>
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
              aria-label="Cup tournament"
              onChange={(event) => setSelectedTournamentId(event.target.value)}
              value={String(tournamentId || "")}
            >
              {cupTournaments.map((tournament) => (
                <option key={tournament.id} value={tournament.id}>
                  {tournament.name}
                </option>
              ))}
            </select>
          </div>
          <div className="row-actions">
            <button
              className="button button-primary"
              disabled={!canGenerateSemifinals}
              type="button"
              onClick={() => {
                setFormError(null);
                setFieldErrors({});
                setOperationError(null);
                setSemifinalFormOpen((current) => !current);
                setFinalFormOpen(false);
              }}
            >
              Generate semifinals
            </button>
            <button
              className="button button-ghost"
              disabled={!canGenerateFinal}
              type="button"
              onClick={() => {
                setFormError(null);
                setFieldErrors({});
                setOperationError(null);
                setFinalFormOpen((current) => !current);
                setSemifinalFormOpen(false);
              }}
            >
              Generate final
            </button>
          </div>
        </div>

        {!canGenerateSemifinals ? (
          <div className="notice">
            <strong>Setup needed.</strong>
            <span>{getCupSetupMessage(tournamentId, teams.length, hasSemifinals)}</span>
          </div>
        ) : null}

        {!canGenerateFinal ? (
          <div className="notice">
            <strong>Final locked.</strong>
            <span>
              {getCupFinalMessage(
                tournamentId,
                stadiums.length,
                hasFinishedSemifinalWinners,
                hasFinal,
              )}
            </span>
          </div>
        ) : null}

        {semifinalFormOpen ? (
          <CupSemifinalsForm
            error={formError}
            fieldErrors={fieldErrors}
            isSaving={semifinalsMutation.isPending}
            stadiums={stadiums}
            teams={teams}
            onCancel={() => setSemifinalFormOpen(false)}
            onSubmit={(payload) =>
              submitAction(() => semifinalsMutation.mutateAsync(payload))
            }
          />
        ) : null}

        {finalFormOpen ? (
          <CupFinalForm
            error={formError}
            fieldErrors={fieldErrors}
            isSaving={finalMutation.isPending}
            stadiums={stadiums}
            onCancel={() => setFinalFormOpen(false)}
            onSubmit={(payload) => submitAction(() => finalMutation.mutateAsync(payload))}
          />
        ) : null}
      </section>

      <section className="panel">
        <div className="section-head">
          <div>
            <p className="eyebrow">Bracket</p>
            <h2>Cup bracket</h2>
          </div>
          {bracket?.champion_team_id ? (
            <span className="mode-chip">
              Champion:{" "}
              <TeamInline
                fallbackName={`Team ${bracket.champion_team_id}`}
                team={getTeamById(bracket.champion_team_id, teams)}
              />
            </span>
          ) : (
            <span className="mode-chip">No champion yet</span>
          )}
        </div>
        <CupBracketView bracket={bracket} teams={teams} />
      </section>
    </div>
  );
}

type CupSemifinalsFormPayload = {
  team_ids: number[] | null;
  use_previous_season_places: boolean;
  match_datetimes: string[];
  fallback_stadium_id: number | null;
  stadium_ids_by_team: Record<number, number>;
};

type CupFinalFormPayload = {
  match_datetime: string;
  stadium_id: number;
};

function CupSemifinalsForm({
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
  onSubmit: (payload: CupSemifinalsFormPayload) => Promise<void>;
}) {
  const today = new Date().toISOString().slice(0, 10);
  const [usePlaces, setUsePlaces] = useState(false);
  const [selectedTeamIds, setSelectedTeamIds] = useState(
    teams.slice(0, 4).map((team) => team.id),
  );
  const [dateOne, setDateOne] = useState(today);
  const [timeOne, setTimeOne] = useState("19:00");
  const [dateTwo, setDateTwo] = useState(today);
  const [timeTwo, setTimeTwo] = useState("21:00");
  const [fallbackStadiumId, setFallbackStadiumId] = useState("");

  function toggleTeam(teamId: number) {
    setSelectedTeamIds((current) =>
      current.includes(teamId)
        ? current.filter((id) => id !== teamId)
        : current.length < 4
          ? [...current, teamId]
          : current,
    );
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    await onSubmit({
      team_ids: usePlaces ? null : selectedTeamIds,
      use_previous_season_places: usePlaces,
      match_datetimes: [`${dateOne}T${timeOne}:00`, `${dateTwo}T${timeTwo}:00`],
      fallback_stadium_id: fallbackStadiumId ? Number(fallbackStadiumId) : null,
      stadium_ids_by_team: {},
    });
  }

  return (
    <form className="inline-form" onSubmit={handleSubmit}>
      <div>
        <p className="eyebrow">Cup</p>
        <h2>Generate semifinals</h2>
      </div>
      {error ? <div className="form-error">{error}</div> : null}
      <div className="form-grid">
        <label className="field">
          <span>Selection mode</span>
          <select
            onChange={(event) => setUsePlaces(event.target.value === "places")}
            value={usePlaces ? "places" : "manual"}
          >
            <option value="manual">manual teams</option>
            <option value="places">previous season places</option>
          </select>
          <FieldError message={fieldErrors.use_previous_season_places} />
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
        <DateTimeFields
          date={dateOne}
          label="Semifinal 1"
          time={timeOne}
          onDateChange={setDateOne}
          onTimeChange={setTimeOne}
        />
        <DateTimeFields
          date={dateTwo}
          label="Semifinal 2"
          time={timeTwo}
          onDateChange={setDateTwo}
          onTimeChange={setTimeTwo}
        />
      </div>

      {!usePlaces ? (
        <>
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
        </>
      ) : null}

      <div className="form-actions">
        <button
          className="button button-primary"
          disabled={isSaving || (!usePlaces && selectedTeamIds.length !== 4)}
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

function CupFinalForm({
  stadiums,
  isSaving,
  error,
  fieldErrors,
  onCancel,
  onSubmit,
}: {
  stadiums: Stadium[];
  isSaving: boolean;
  error: string | null;
  fieldErrors: Record<string, string>;
  onCancel: () => void;
  onSubmit: (payload: CupFinalFormPayload) => Promise<void>;
}) {
  const today = new Date().toISOString().slice(0, 10);
  const [date, setDate] = useState(today);
  const [time, setTime] = useState("20:00");
  const [stadiumId, setStadiumId] = useState(stadiums[0] ? String(stadiums[0].id) : "");

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    await onSubmit({
      match_datetime: `${date}T${time}:00`,
      stadium_id: Number(stadiumId),
    });
  }

  return (
    <form className="inline-form" onSubmit={handleSubmit}>
      <div>
        <p className="eyebrow">Cup</p>
        <h2>Generate final</h2>
      </div>
      {error ? <div className="form-error">{error}</div> : null}
      <div className="form-grid">
        <DateTimeFields
          date={date}
          label="Final"
          time={time}
          onDateChange={setDate}
          onTimeChange={setTime}
        />
        <label className="field">
          <span>Stadium</span>
          <select
            onChange={(event) => setStadiumId(event.target.value)}
            required
            value={stadiumId}
          >
            {stadiums.map((stadium) => (
              <option key={stadium.id} value={stadium.id}>
                {stadium.name}
              </option>
            ))}
          </select>
          <FieldError message={fieldErrors.stadium_id} />
        </label>
      </div>
      <p className="muted">
        Финал можно создать только после двух завершённых полуфиналов с явными победителями.
      </p>
      <div className="form-actions">
        <button
          className="button button-primary"
          disabled={isSaving || !stadiumId}
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

function CupBracketView({
  bracket,
  teams,
}: {
  bracket?: CupBracket;
  teams: Team[];
}) {
  if (!bracket) {
    return <p className="muted">No bracket yet.</p>;
  }

  return (
    <div className="bracket">
      <div className="bracket-column">
        <p className="eyebrow">Semifinals</p>
        {bracket.semifinals.length > 0 ? (
          bracket.semifinals.map((node) => (
            <CupMatchCard key={node.match.id} node={node} teams={teams} />
          ))
        ) : (
          <div className="bracket-card">
            <span>No semifinals</span>
          </div>
        )}
      </div>
      <div className="bracket-column">
        <p className="eyebrow">Final</p>
        {bracket.final ? (
          <CupMatchCard node={bracket.final} teams={teams} />
        ) : (
          <div className="bracket-card">
            <span>No final yet</span>
          </div>
        )}
      </div>
      <div className="bracket-card champion-card">
        <p className="eyebrow">Champion</p>
        <strong>
          {bracket.champion_team_id ? (
            <TeamInline
              fallbackName={`Team ${bracket.champion_team_id}`}
              team={getTeamById(bracket.champion_team_id, teams)}
            />
          ) : (
            "Not decided"
          )}
        </strong>
      </div>
    </div>
  );
}

function CupMatchCard({ node, teams }: { node: CupMatchNode; teams: Team[] }) {
  const match = node.match;

  return (
    <div className="bracket-card">
      <span>{formatDateTime(match.match_datetime)}</span>
      <strong>
        <MatchupInline match={match} teams={teams} />
      </strong>
      <small>Status: {match.status}</small>
      <small>
        Score:{" "}
        {match.status === "finished"
          ? `${match.home_score ?? 0}:${match.away_score ?? 0}`
          : "not played"}
      </small>
      <small>
        Winner:{" "}
        {node.winner_team_id ? (
          <TeamInline
            fallbackName={`Team ${node.winner_team_id}`}
            team={getTeamById(node.winner_team_id, teams)}
          />
        ) : (
          "none"
        )}
      </small>
      <Link className="button button-ghost" to={`/app/matches/${match.id}`}>
        Open match
      </Link>
    </div>
  );
}

function DateTimeFields({
  date,
  label,
  onDateChange,
  onTimeChange,
  time,
}: {
  date: string;
  label: string;
  onDateChange: (value: string) => void;
  onTimeChange: (value: string) => void;
  time: string;
}) {
  return (
    <>
      <label className="field">
        <span>{label} date</span>
        <input
          onChange={(event) => onDateChange(event.target.value)}
          required
          type="date"
          value={date}
        />
      </label>
      <label className="field">
        <span>{label} time</span>
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

function FieldError({ message }: { message?: string }) {
  return message ? <small className="field-error">{message}</small> : null;
}

function getTeamName(teamId: number, teams: Team[]) {
  return teams.find((team) => team.id === teamId)?.name ?? `Team ${teamId}`;
}

function getTeamById(teamId: number, teams: Team[]) {
  return teams.find((team) => team.id === teamId);
}

function getCupSetupMessage(
  tournamentId: number,
  teamCount: number,
  hasSemifinals: boolean,
) {
  if (hasSemifinals) {
    return "Semifinals already exist for this cup.";
  }
  if (!tournamentId) {
    return "Cup semifinals need a cup tournament.";
  }
  if (teamCount < 4) {
    return "Cup semifinals need at least four teams.";
  }
  return "Cup semifinals are not ready yet.";
}

function getCupFinalMessage(
  tournamentId: number,
  stadiumCount: number,
  hasFinishedSemifinalWinners: boolean,
  hasFinal: boolean,
) {
  if (hasFinal) {
    return "The cup final already exists.";
  }
  if (!tournamentId) {
    return "Cup final generation needs a cup tournament.";
  }
  if (stadiumCount === 0) {
    return "Cup final generation needs at least one stadium.";
  }
  if (!hasFinishedSemifinalWinners) {
    return "Finish both semifinals with clear winners before generating the final.";
  }
  return "Cup final generation is not ready yet.";
}

function formatDateTime(value: string) {
  return new Intl.DateTimeFormat("ru-RU", {
    dateStyle: "short",
    timeStyle: "short",
  }).format(new Date(value));
}

async function invalidateCupReads(
  queryClient: ReturnType<typeof useQueryClient>,
  tournamentId: number,
) {
  await queryClient.invalidateQueries({ queryKey: ["matches"] });
  await queryClient.invalidateQueries({ queryKey: ["cupBracket", tournamentId] });
}
