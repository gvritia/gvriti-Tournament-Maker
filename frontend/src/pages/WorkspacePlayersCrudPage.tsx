import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useMemo, useState, type FormEvent } from "react";
import { Link } from "react-router-dom";
import { DataTable } from "../components/DataTable";
import { TeamInline } from "../components/TeamInline";
import { useAuth } from "../features/auth/AuthProvider";
import type { ApiError } from "../shared/api/client";
import {
  createPlayer,
  deletePlayer,
  fetchPlayers,
  fetchTeams,
  updatePlayer,
} from "../shared/api/endpoints";
import type { Player, Team } from "../shared/api/types";

const PLAYER_POSITIONS = ["goalkeeper", "defender", "midfielder", "forward"];

type PlayerFormValues = {
  full_name: string;
  age: string;
  position: string;
  number: string;
  team_id: string;
};

type PlayerFormPayload = {
  full_name: string;
  age: number | null;
  position: string;
  number: number;
  team_id: number;
};

export function WorkspacePlayersCrudPage() {
  const { token } = useAuth();
  const safeToken = token ?? "";
  const queryClient = useQueryClient();
  const [search, setSearch] = useState("");
  const [teamId, setTeamId] = useState("all");
  const [position, setPosition] = useState("all");
  const [editingPlayer, setEditingPlayer] = useState<Player | null>(null);
  const [isFormOpen, setIsFormOpen] = useState(false);
  const [formError, setFormError] = useState<string | null>(null);
  const [fieldErrors, setFieldErrors] = useState<Record<string, string>>({});
  const [operationError, setOperationError] = useState<string | null>(null);

  const playersQuery = useQuery({
    queryKey: ["players"],
    queryFn: () => fetchPlayers(safeToken),
    enabled: Boolean(token),
  });
  const teamsQuery = useQuery({
    queryKey: ["teams"],
    queryFn: () => fetchTeams(safeToken),
    enabled: Boolean(token),
  });

  const players = playersQuery.data ?? [];
  const teams = teamsQuery.data ?? [];
  const error = playersQuery.error ?? teamsQuery.error ?? null;
  const isInitialLoading = playersQuery.isLoading || teamsQuery.isLoading;

  const filteredPlayers = useMemo(() => {
    const normalizedSearch = search.trim().toLowerCase();
    return players.filter((player) => {
      const playerTeam = getTeamName(player.team_id, teams).toLowerCase();
      const bySearch =
        !normalizedSearch ||
        [player.full_name, playerTeam, String(player.number)]
          .join(" ")
          .toLowerCase()
          .includes(normalizedSearch);
      const byTeam = teamId === "all" || player.team_id === Number(teamId);
      const byPosition = position === "all" || player.position === position;

      return bySearch && byTeam && byPosition;
    });
  }, [players, position, search, teamId, teams]);

  const createMutation = useMutation({
    mutationFn: (payload: PlayerFormPayload) => createPlayer(safeToken, payload),
    onSuccess: async (player) => {
      await invalidatePlayerReads(queryClient, player.team_id);
    },
  });

  const updateMutation = useMutation({
    mutationFn: (payload: { id: number; values: PlayerFormPayload }) =>
      updatePlayer(safeToken, payload.id, payload.values),
    onSuccess: async (player, payload) => {
      await invalidatePlayerReads(queryClient, player.team_id);
      if (editingPlayer && editingPlayer.team_id !== player.team_id) {
        await queryClient.invalidateQueries({
          queryKey: ["team", editingPlayer.team_id],
        });
      }
      await queryClient.invalidateQueries({ queryKey: ["player", payload.id] });
    },
  });

  const deleteMutation = useMutation({
    mutationFn: (player: Player) => deletePlayer(safeToken, player.id),
    onSuccess: async (_data, player) => {
      await invalidatePlayerReads(queryClient, player.team_id);
      await queryClient.invalidateQueries({ queryKey: ["player", player.id] });
    },
  });

  const isSaving = createMutation.isPending || updateMutation.isPending;

  function openCreateForm() {
    setEditingPlayer(null);
    setFormError(null);
    setFieldErrors({});
    setOperationError(null);
    setIsFormOpen(true);
  }

  function openEditForm(player: Player) {
    setEditingPlayer(player);
    setFormError(null);
    setFieldErrors({});
    setOperationError(null);
    setIsFormOpen(true);
  }

  function closeForm() {
    setIsFormOpen(false);
    setEditingPlayer(null);
    setFormError(null);
    setFieldErrors({});
  }

  async function handleSavePlayer(values: PlayerFormPayload) {
    setFormError(null);
    setFieldErrors({});
    setOperationError(null);

    try {
      if (editingPlayer) {
        await updateMutation.mutateAsync({ id: editingPlayer.id, values });
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

  async function handleDeletePlayer(player: Player) {
    const confirmed = window.confirm(
      `Удалить игрока "${player.full_name}"? Составы и протоколы могут заблокировать удаление, если игрок уже используется в матчах.`,
    );
    if (!confirmed) {
      return;
    }

    setOperationError(null);

    try {
      await deleteMutation.mutateAsync(player);
    } catch (caughtError) {
      const apiError = caughtError as ApiError;
      setOperationError(apiError.message);
    }
  }

  return (
    <div className="page-stack">
      <section className="page-intro">
        <p className="eyebrow">Игроки</p>
        <h2>Players</h2>
        <p className="muted">
          Manage player rosters through team links. Shirt numbers stay unique
          внутри каждой команды.
        </p>
      </section>

      {error instanceof Error ? (
        <section className="notice notice-danger">
          <strong>Не удалось загрузить игроков.</strong>
          <span>{error.message}</span>
        </section>
      ) : null}

      <section className="panel">
        <div className="section-head">
          <div className="filter-row">
            <input
              aria-label="Search players"
              onChange={(event) => setSearch(event.target.value)}
              placeholder="Name, team, or number"
              value={search}
            />
            <select
              aria-label="Filter by team"
              onChange={(event) => setTeamId(event.target.value)}
              value={teamId}
            >
              <option value="all">All teams</option>
              {teams.map((team) => (
                <option key={team.id} value={team.id}>
                  {team.name}
                </option>
              ))}
            </select>
            <select
              aria-label="Filter by position"
              onChange={(event) => setPosition(event.target.value)}
              value={position}
            >
              <option value="all">All positions</option>
              {PLAYER_POSITIONS.map((playerPosition) => (
                <option key={playerPosition} value={playerPosition}>
                  {playerPosition}
                </option>
              ))}
            </select>
          </div>
          <button
            className="button button-primary"
            disabled={teams.length === 0}
            type="button"
            onClick={openCreateForm}
          >
            Create player
          </button>
        </div>

        {operationError ? <div className="form-error">{operationError}</div> : null}

        {teams.length === 0 ? (
          <div className="notice">
            <strong>Create a team first.</strong>
            <span>Players must belong to a team.</span>
          </div>
        ) : null}

        {isFormOpen ? (
          <PlayerForm
            key={editingPlayer?.id ?? "new"}
            initialValues={playerToFormValues(editingPlayer, teams)}
            isSaving={isSaving}
            mode={editingPlayer ? "edit" : "create"}
            teams={teams}
            error={formError}
            fieldErrors={fieldErrors}
            onCancel={closeForm}
            onSubmit={handleSavePlayer}
          />
        ) : null}

        <DataTable
          rows={filteredPlayers}
          getRowKey={(player) => player.id}
          emptyText="No players found"
          isLoading={isInitialLoading}
          pageSize={50}
          columns={[
            { key: "number", header: "#", render: (player) => player.number },
            {
              key: "name",
              header: "Player",
              render: (player) => player.full_name,
            },
            {
              key: "team",
              header: "Team",
              render: (player) => (
                <Link className="auth-link" to={`/app/teams/${player.team_id}`}>
                  <TeamInline
                    fallbackName={`Team ${player.team_id}`}
                    team={getTeamById(player.team_id, teams)}
                  />
                </Link>
              ),
            },
            {
              key: "position",
              header: "Position",
              render: (player) => player.position,
            },
            {
              key: "age",
              header: "Age",
              render: (player) => player.age ?? "not set",
            },
            {
              key: "actions",
              header: "Actions",
              render: (player) => (
                <div className="row-actions">
                  <button
                    className="button button-ghost"
                    type="button"
                    onClick={() => openEditForm(player)}
                  >
                    Edit
                  </button>
                  <button
                    className="button button-danger"
                    disabled={deleteMutation.isPending}
                    type="button"
                    onClick={() => handleDeletePlayer(player)}
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

function PlayerForm({
  initialValues,
  mode,
  teams,
  isSaving,
  error,
  fieldErrors,
  onCancel,
  onSubmit,
}: {
  initialValues: PlayerFormValues;
  mode: "create" | "edit";
  teams: Team[];
  isSaving: boolean;
  error: string | null;
  fieldErrors: Record<string, string>;
  onCancel: () => void;
  onSubmit: (values: PlayerFormPayload) => Promise<void>;
}) {
  const [values, setValues] = useState(initialValues);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    await onSubmit({
      full_name: values.full_name.trim(),
      age: values.age ? Number(values.age) : null,
      position: values.position,
      number: Number(values.number),
      team_id: Number(values.team_id),
    });
  }

  return (
    <form className="inline-form" onSubmit={handleSubmit}>
      <div>
        <p className="eyebrow">{mode === "create" ? "Create" : "Edit"}</p>
        <h2>{mode === "create" ? "New player" : "Edit player"}</h2>
      </div>

      {error ? <div className="form-error">{error}</div> : null}

      <div className="form-grid">
        <label className="field">
          <span>Full name</span>
          <input
            autoFocus
            onChange={(event) =>
              setValues((current) => ({
                ...current,
                full_name: event.target.value,
              }))
            }
            required
            value={values.full_name}
          />
          {fieldErrors.full_name ? (
            <small className="field-error">{fieldErrors.full_name}</small>
          ) : null}
        </label>

        <label className="field">
          <span>Team</span>
          <select
            onChange={(event) =>
              setValues((current) => ({ ...current, team_id: event.target.value }))
            }
            required
            value={values.team_id}
          >
            {teams.map((team) => (
              <option key={team.id} value={team.id}>
                {team.name}
              </option>
            ))}
          </select>
          {fieldErrors.team_id ? (
            <small className="field-error">{fieldErrors.team_id}</small>
          ) : null}
        </label>

        <label className="field">
          <span>Position</span>
          <select
            onChange={(event) =>
              setValues((current) => ({ ...current, position: event.target.value }))
            }
            value={values.position}
          >
            {PLAYER_POSITIONS.map((playerPosition) => (
              <option key={playerPosition} value={playerPosition}>
                {playerPosition}
              </option>
            ))}
          </select>
          {fieldErrors.position ? (
            <small className="field-error">{fieldErrors.position}</small>
          ) : null}
        </label>

        <label className="field">
          <span>Number</span>
          <input
            min={1}
            max={99}
            onChange={(event) =>
              setValues((current) => ({ ...current, number: event.target.value }))
            }
            required
            type="number"
            value={values.number}
          />
          {fieldErrors.number ? (
            <small className="field-error">{fieldErrors.number}</small>
          ) : null}
        </label>

        <label className="field">
          <span>Age</span>
          <input
            min={14}
            max={60}
            onChange={(event) =>
              setValues((current) => ({ ...current, age: event.target.value }))
            }
            type="number"
            value={values.age}
          />
          {fieldErrors.age ? (
            <small className="field-error">{fieldErrors.age}</small>
          ) : null}
        </label>
      </div>

      <div className="form-actions">
        <button
          className="button button-primary"
          disabled={
            isSaving ||
            !values.full_name.trim() ||
            !values.team_id ||
            Number(values.number) < 1 ||
            Number(values.number) > 99
          }
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

function playerToFormValues(
  player: Player | null,
  teams: Team[],
): PlayerFormValues {
  if (!player) {
    return {
      full_name: "",
      age: "",
      position: "midfielder",
      number: "1",
      team_id: teams[0] ? String(teams[0].id) : "",
    };
  }

  return {
    full_name: player.full_name,
    age: player.age ? String(player.age) : "",
    position: player.position,
    number: String(player.number),
    team_id: String(player.team_id),
  };
}

function getTeamName(teamId: number, teams: Team[]) {
  return teams.find((team) => team.id === teamId)?.name ?? `Team ${teamId}`;
}

function getTeamById(teamId: number, teams: Team[]) {
  return teams.find((team) => team.id === teamId);
}

async function invalidatePlayerReads(
  queryClient: ReturnType<typeof useQueryClient>,
  teamId: number,
) {
  await queryClient.invalidateQueries({ queryKey: ["players"] });
  await queryClient.invalidateQueries({ queryKey: ["team", teamId] });
  await queryClient.invalidateQueries({ queryKey: ["matches"] });
}
