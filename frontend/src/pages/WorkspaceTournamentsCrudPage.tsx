import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useMemo, useState, type FormEvent } from "react";
import { DataTable } from "../components/DataTable";
import { useAuth } from "../features/auth/AuthProvider";
import type { ApiError } from "../shared/api/client";
import {
  createTournament,
  deleteTournament,
  fetchSeasons,
  fetchTournaments,
  updateTournament,
} from "../shared/api/endpoints";
import type { Season, Tournament } from "../shared/api/types";

const TOURNAMENT_TYPES = ["championship", "cup"];
const TOURNAMENT_STATUSES = ["planned", "active", "finished", "cancelled"];

type TournamentFormValues = {
  season_id: string;
  name: string;
  type: string;
  status: string;
};

type TournamentFormPayload = {
  season_id: number;
  name: string;
  type: string;
  status: string;
};

export function WorkspaceTournamentsCrudPage() {
  const { token } = useAuth();
  const safeToken = token ?? "";
  const queryClient = useQueryClient();
  const [search, setSearch] = useState("");
  const [seasonId, setSeasonId] = useState("all");
  const [type, setType] = useState("all");
  const [status, setStatus] = useState("all");
  const [editingTournament, setEditingTournament] = useState<Tournament | null>(
    null,
  );
  const [isFormOpen, setIsFormOpen] = useState(false);
  const [formError, setFormError] = useState<string | null>(null);
  const [fieldErrors, setFieldErrors] = useState<Record<string, string>>({});
  const [operationError, setOperationError] = useState<string | null>(null);

  const tournamentsQuery = useQuery({
    queryKey: ["tournaments"],
    queryFn: () => fetchTournaments(safeToken),
    enabled: Boolean(token),
  });
  const seasonsQuery = useQuery({
    queryKey: ["seasons"],
    queryFn: () => fetchSeasons(safeToken),
    enabled: Boolean(token),
  });

  const tournaments = tournamentsQuery.data ?? [];
  const seasons = seasonsQuery.data ?? [];
  const error = tournamentsQuery.error ?? seasonsQuery.error ?? null;

  const filteredTournaments = useMemo(() => {
    const normalizedSearch = search.trim().toLowerCase();
    return tournaments.filter((tournament) => {
      const tournamentSeason = getSeasonName(tournament.season_id, seasons);
      const bySearch =
        !normalizedSearch ||
        [tournament.name, tournamentSeason]
          .join(" ")
          .toLowerCase()
          .includes(normalizedSearch);
      const bySeason =
        seasonId === "all" || tournament.season_id === Number(seasonId);
      const byType = type === "all" || tournament.type === type;
      const byStatus = status === "all" || tournament.status === status;

      return bySearch && bySeason && byType && byStatus;
    });
  }, [search, seasonId, seasons, status, tournaments, type]);

  const createMutation = useMutation({
    mutationFn: (payload: TournamentFormPayload) =>
      createTournament(safeToken, payload),
    onSuccess: async () => {
      await invalidateTournamentReads(queryClient);
    },
  });

  const updateMutation = useMutation({
    mutationFn: (payload: { id: number; values: TournamentFormPayload }) =>
      updateTournament(safeToken, payload.id, payload.values),
    onSuccess: async () => {
      await invalidateTournamentReads(queryClient);
    },
  });

  const deleteMutation = useMutation({
    mutationFn: (tournamentId: number) => deleteTournament(safeToken, tournamentId),
    onSuccess: async () => {
      await invalidateTournamentReads(queryClient);
    },
  });

  const isSaving = createMutation.isPending || updateMutation.isPending;

  function openCreateForm() {
    setEditingTournament(null);
    setFormError(null);
    setFieldErrors({});
    setOperationError(null);
    setIsFormOpen(true);
  }

  function openEditForm(tournament: Tournament) {
    setEditingTournament(tournament);
    setFormError(null);
    setFieldErrors({});
    setOperationError(null);
    setIsFormOpen(true);
  }

  function closeForm() {
    setIsFormOpen(false);
    setEditingTournament(null);
    setFormError(null);
    setFieldErrors({});
  }

  async function handleSaveTournament(values: TournamentFormPayload) {
    setFormError(null);
    setFieldErrors({});
    setOperationError(null);

    try {
      if (editingTournament) {
        await updateMutation.mutateAsync({
          id: editingTournament.id,
          values,
        });
      } else {
        await createMutation.mutateAsync(values);
      }
      closeForm();
    } catch (caughtError) {
      const apiError = caughtError as ApiError;
      setFormError(apiError.message);
      setFieldErrors(apiError.fieldErrors ?? {});
    }
  }

  async function handleDeleteTournament(tournament: Tournament) {
    const confirmed = window.confirm(
      `Удалить турнир "${tournament.name}"? Связанные матчи и расписание могут быть затронуты правилами турнира.`,
    );
    if (!confirmed) {
      return;
    }

    setOperationError(null);

    try {
      await deleteMutation.mutateAsync(tournament.id);
    } catch (caughtError) {
      const apiError = caughtError as ApiError;
      setOperationError(apiError.message);
    }
  }

  return (
    <div className="page-stack">
      <section className="page-intro">
        <p className="eyebrow">Турниры</p>
        <h2>Tournaments</h2>
        <p className="muted">
          Manage championships and cups inside seasons. Schedule generation and
          cup bracket workflows stay in their dedicated screens.
        </p>
      </section>

      {error instanceof Error ? (
        <section className="notice notice-danger">
          <strong>Не удалось загрузить турниры.</strong>
          <span>{error.message}</span>
        </section>
      ) : null}

      <section className="panel">
        <div className="section-head">
          <div className="filter-row">
            <input
              aria-label="Search tournaments"
              onChange={(event) => setSearch(event.target.value)}
              placeholder="Name or season"
              value={search}
            />
            <select
              aria-label="Filter by season"
              onChange={(event) => setSeasonId(event.target.value)}
              value={seasonId}
            >
              <option value="all">All seasons</option>
              {seasons.map((season) => (
                <option key={season.id} value={season.id}>
                  {season.name}
                </option>
              ))}
            </select>
            <select
              aria-label="Filter by type"
              onChange={(event) => setType(event.target.value)}
              value={type}
            >
              <option value="all">All types</option>
              {TOURNAMENT_TYPES.map((tournamentType) => (
                <option key={tournamentType} value={tournamentType}>
                  {tournamentType}
                </option>
              ))}
            </select>
            <select
              aria-label="Filter by status"
              onChange={(event) => setStatus(event.target.value)}
              value={status}
            >
              <option value="all">All statuses</option>
              {TOURNAMENT_STATUSES.map((tournamentStatus) => (
                <option key={tournamentStatus} value={tournamentStatus}>
                  {tournamentStatus}
                </option>
              ))}
            </select>
          </div>
          <button
            className="button button-primary"
            disabled={seasons.length === 0}
            type="button"
            onClick={openCreateForm}
          >
            Create tournament
          </button>
        </div>

        {operationError ? <div className="form-error">{operationError}</div> : null}

        {seasons.length === 0 ? (
          <div className="notice">
            <strong>Create a season first.</strong>
            <span>Tournaments must belong to a season.</span>
          </div>
        ) : null}

        {isFormOpen ? (
          <TournamentForm
            key={editingTournament?.id ?? "new"}
            initialValues={tournamentToFormValues(editingTournament, seasons)}
            isSaving={isSaving}
            mode={editingTournament ? "edit" : "create"}
            seasons={seasons}
            error={formError}
            fieldErrors={fieldErrors}
            onCancel={closeForm}
            onSubmit={handleSaveTournament}
          />
        ) : null}

        <DataTable
          rows={filteredTournaments}
          getRowKey={(tournament) => tournament.id}
          emptyText="No tournaments found"
          columns={[
            {
              key: "name",
              header: "Tournament",
              render: (tournament) => tournament.name,
            },
            {
              key: "season",
              header: "Season",
              render: (tournament) =>
                getSeasonName(tournament.season_id, seasons),
            },
            {
              key: "type",
              header: "Type",
              render: (tournament) => tournament.type,
            },
            {
              key: "status",
              header: "Status",
              render: (tournament) => (
                <span className={`status status-${tournament.status}`}>
                  {tournament.status}
                </span>
              ),
            },
            {
              key: "created",
              header: "Created",
              render: (tournament) => formatDate(tournament.created_at),
            },
            {
              key: "actions",
              header: "Actions",
              render: (tournament) => (
                <div className="row-actions">
                  <button
                    className="button button-ghost"
                    type="button"
                    onClick={() => openEditForm(tournament)}
                  >
                    Edit
                  </button>
                  <button
                    className="button button-danger"
                    disabled={deleteMutation.isPending}
                    type="button"
                    onClick={() => handleDeleteTournament(tournament)}
                  >
                    Удалить
                  </button>
                </div>
              ),
            },
          ]}
        />
      </section>
    </div>
  );
}

function TournamentForm({
  initialValues,
  mode,
  seasons,
  isSaving,
  error,
  fieldErrors,
  onCancel,
  onSubmit,
}: {
  initialValues: TournamentFormValues;
  mode: "create" | "edit";
  seasons: Season[];
  isSaving: boolean;
  error: string | null;
  fieldErrors: Record<string, string>;
  onCancel: () => void;
  onSubmit: (values: TournamentFormPayload) => Promise<void>;
}) {
  const [values, setValues] = useState(initialValues);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    await onSubmit({
      season_id: Number(values.season_id),
      name: values.name.trim(),
      type: values.type,
      status: values.status,
    });
  }

  return (
    <form className="inline-form" onSubmit={handleSubmit}>
      <div>
        <p className="eyebrow">{mode === "create" ? "Create" : "Edit"}</p>
        <h2>{mode === "create" ? "New tournament" : "Edit tournament"}</h2>
      </div>

      {error ? <div className="form-error">{error}</div> : null}

      <div className="form-grid">
        <label className="field">
          <span>Name</span>
          <input
            autoFocus
            onChange={(event) =>
              setValues((current) => ({ ...current, name: event.target.value }))
            }
            required
            value={values.name}
          />
          {fieldErrors.name ? (
            <small className="field-error">{fieldErrors.name}</small>
          ) : null}
        </label>

        <label className="field">
          <span>Season</span>
          <select
            onChange={(event) =>
              setValues((current) => ({
                ...current,
                season_id: event.target.value,
              }))
            }
            required
            value={values.season_id}
          >
            {seasons.map((season) => (
              <option key={season.id} value={season.id}>
                {season.name}
              </option>
            ))}
          </select>
          {fieldErrors.season_id ? (
            <small className="field-error">{fieldErrors.season_id}</small>
          ) : null}
        </label>

        <label className="field">
          <span>Type</span>
          <select
            onChange={(event) =>
              setValues((current) => ({ ...current, type: event.target.value }))
            }
            value={values.type}
          >
            {TOURNAMENT_TYPES.map((tournamentType) => (
              <option key={tournamentType} value={tournamentType}>
                {tournamentType}
              </option>
            ))}
          </select>
          {fieldErrors.type ? (
            <small className="field-error">{fieldErrors.type}</small>
          ) : null}
        </label>

        <label className="field">
          <span>Status</span>
          <select
            onChange={(event) =>
              setValues((current) => ({ ...current, status: event.target.value }))
            }
            value={values.status}
          >
            {TOURNAMENT_STATUSES.map((tournamentStatus) => (
              <option key={tournamentStatus} value={tournamentStatus}>
                {tournamentStatus}
              </option>
            ))}
          </select>
          {fieldErrors.status ? (
            <small className="field-error">{fieldErrors.status}</small>
          ) : null}
        </label>
      </div>

      <div className="form-actions">
        <button
          className="button button-primary"
          disabled={isSaving || !values.name.trim() || !values.season_id}
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
    </form>
  );
}

function tournamentToFormValues(
  tournament: Tournament | null,
  seasons: Season[],
): TournamentFormValues {
  if (!tournament) {
    return {
      season_id: seasons[0] ? String(seasons[0].id) : "",
      name: "",
      type: "championship",
      status: "planned",
    };
  }

  return {
    season_id: String(tournament.season_id),
    name: tournament.name,
    type: tournament.type,
    status: tournament.status,
  };
}

function getSeasonName(seasonId: number, seasons: Season[]) {
  return seasons.find((season) => season.id === seasonId)?.name ?? `Season ${seasonId}`;
}

function formatDate(value: string) {
  return new Intl.DateTimeFormat("ru-RU", { dateStyle: "short" }).format(
    new Date(value),
  );
}

async function invalidateTournamentReads(
  queryClient: ReturnType<typeof useQueryClient>,
) {
  await queryClient.invalidateQueries({ queryKey: ["tournaments"] });
  await queryClient.invalidateQueries({ queryKey: ["matches"] });
}
