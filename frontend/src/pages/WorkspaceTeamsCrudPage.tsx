import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useMemo, useState, type FormEvent } from "react";
import { Link } from "react-router-dom";
import { DataTable } from "../components/DataTable";
import { TeamMark } from "../components/TeamMark";
import { useAuth } from "../features/auth/AuthProvider";
import type { ApiError } from "../shared/api/client";
import {
  createTeam,
  deleteTeam,
  fetchStadiums,
  fetchTeams,
  updateTeam,
} from "../shared/api/endpoints";
import type { Stadium, Team } from "../shared/api/types";

type TeamFormValues = {
  name: string;
  city: string;
  address: string;
  manager_name: string;
  emblem_url: string;
  previous_season_place: string;
};

type TeamFormPayload = {
  name: string;
  city: string;
  address: string | null;
  manager_name: string | null;
  emblem_url: string | null;
  previous_season_place: number | null;
};

export function WorkspaceTeamsCrudPage() {
  const { token } = useAuth();
  const safeToken = token ?? "";
  const queryClient = useQueryClient();
  const [search, setSearch] = useState("");
  const [editingTeam, setEditingTeam] = useState<Team | null>(null);
  const [isFormOpen, setIsFormOpen] = useState(false);
  const [formError, setFormError] = useState<string | null>(null);
  const [fieldErrors, setFieldErrors] = useState<Record<string, string>>({});
  const [operationError, setOperationError] = useState<string | null>(null);

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

  const teams = teamsQuery.data ?? [];
  const stadiums = stadiumsQuery.data ?? [];
  const error = teamsQuery.error ?? stadiumsQuery.error ?? null;
  const filteredTeams = useMemo(() => {
    const normalizedSearch = search.trim().toLowerCase();
    if (!normalizedSearch) {
      return teams;
    }

    return teams.filter((team) =>
      [team.name, team.city, team.manager_name ?? ""]
        .join(" ")
        .toLowerCase()
        .includes(normalizedSearch),
    );
  }, [search, teams]);

  const createMutation = useMutation({
    mutationFn: (payload: TeamFormPayload) => createTeam(safeToken, payload),
    onSuccess: async () => {
      await invalidateTeamReads(queryClient);
    },
  });

  const updateMutation = useMutation({
    mutationFn: (payload: { id: number; values: TeamFormPayload }) =>
      updateTeam(safeToken, payload.id, payload.values),
    onSuccess: async (team) => {
      await queryClient.invalidateQueries({ queryKey: ["team", team.id] });
      await invalidateTeamReads(queryClient);
    },
  });

  const deleteMutation = useMutation({
    mutationFn: (teamId: number) => deleteTeam(safeToken, teamId),
    onSuccess: async (_data, teamId) => {
      await queryClient.invalidateQueries({ queryKey: ["team", teamId] });
      await invalidateTeamReads(queryClient);
    },
  });

  const isSaving = createMutation.isPending || updateMutation.isPending;

  function openCreateForm() {
    setEditingTeam(null);
    setFormError(null);
    setFieldErrors({});
    setOperationError(null);
    setIsFormOpen(true);
  }

  function openEditForm(team: Team) {
    setEditingTeam(team);
    setFormError(null);
    setFieldErrors({});
    setOperationError(null);
    setIsFormOpen(true);
  }

  function closeForm() {
    setIsFormOpen(false);
    setEditingTeam(null);
    setFormError(null);
    setFieldErrors({});
  }

  async function handleSaveTeam(values: TeamFormPayload) {
    setFormError(null);
    setFieldErrors({});
    setOperationError(null);

    try {
      if (editingTeam) {
        await updateMutation.mutateAsync({ id: editingTeam.id, values });
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

  async function handleDeleteTeam(team: Team) {
    const confirmed = window.confirm(
      `Удалить команду "${team.name}"? Связанные стадионы и матчи могут быть затронуты правилами турнира.`,
    );
    if (!confirmed) {
      return;
    }

    setOperationError(null);

    try {
      await deleteMutation.mutateAsync(team.id);
    } catch (caughtError) {
      const apiError = caughtError as ApiError;
      setOperationError(apiError.message);
    }
  }

  return (
    <div className="page-stack">
      <section className="page-intro">
        <p className="eyebrow">Команды</p>
        <h2>Teams</h2>
        <p className="muted">
          Manage clubs, badges, managers, and previous-season placement inside
          вашей рабочей области.
        </p>
      </section>

      {error instanceof Error ? (
        <section className="notice notice-danger">
          <strong>Не удалось загрузить команды.</strong>
          <span>{error.message}</span>
        </section>
      ) : null}

      <section className="panel">
        <div className="section-head">
          <div className="filter-row">
            <input
              aria-label="Search teams"
              onChange={(event) => setSearch(event.target.value)}
              placeholder="Name, city, or manager"
              value={search}
            />
          </div>
          <button className="button button-primary" type="button" onClick={openCreateForm}>
            Create team
          </button>
        </div>

        {operationError ? <div className="form-error">{operationError}</div> : null}

        {isFormOpen ? (
          <TeamForm
            key={editingTeam?.id ?? "new"}
            initialValues={teamToFormValues(editingTeam)}
            isSaving={isSaving}
            mode={editingTeam ? "edit" : "create"}
            error={formError}
            fieldErrors={fieldErrors}
            onCancel={closeForm}
            onSubmit={handleSaveTeam}
          />
        ) : null}

        <DataTable
          rows={filteredTeams}
          getRowKey={(team) => team.id}
          emptyText="No teams found"
          columns={[
            {
              key: "team",
              header: "Team",
              render: (team) => (
                <Link className="team-link" to={`/app/teams/${team.id}`}>
                  <TeamMark team={team} />
                  {team.name}
                </Link>
              ),
            },
            { key: "city", header: "City", render: (team) => team.city },
            {
              key: "stadium",
              header: "Home stadium",
              render: (team) => getHomeStadiumName(team.id, stadiums),
            },
            {
              key: "manager",
              header: "Manager",
              render: (team) => team.manager_name ?? "not set",
            },
            {
              key: "place",
              header: "Previous place",
              render: (team) => team.previous_season_place ?? "none",
            },
            {
              key: "actions",
              header: "Actions",
              render: (team) => (
                <div className="row-actions">
                  <Link className="button button-ghost" to={`/app/teams/${team.id}`}>
                    Open
                  </Link>
                  <button
                    className="button button-ghost"
                    type="button"
                    onClick={() => openEditForm(team)}
                  >
                    Edit
                  </button>
                  <button
                    className="button button-danger"
                    disabled={deleteMutation.isPending}
                    type="button"
                    onClick={() => handleDeleteTeam(team)}
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

function TeamForm({
  initialValues,
  mode,
  isSaving,
  error,
  fieldErrors,
  onCancel,
  onSubmit,
}: {
  initialValues: TeamFormValues;
  mode: "create" | "edit";
  isSaving: boolean;
  error: string | null;
  fieldErrors: Record<string, string>;
  onCancel: () => void;
  onSubmit: (values: TeamFormPayload) => Promise<void>;
}) {
  const [values, setValues] = useState(initialValues);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    await onSubmit({
      name: values.name.trim(),
      city: values.city.trim(),
      address: emptyToNull(values.address),
      manager_name: emptyToNull(values.manager_name),
      emblem_url: emptyToNull(values.emblem_url),
      previous_season_place: values.previous_season_place
        ? Number(values.previous_season_place)
        : null,
    });
  }

  return (
    <form className="inline-form" onSubmit={handleSubmit}>
      <div>
        <p className="eyebrow">{mode === "create" ? "Create" : "Edit"}</p>
        <h2>{mode === "create" ? "New team" : "Edit team"}</h2>
      </div>

      {error ? <div className="form-error">{error}</div> : null}

      <div className="form-grid">
        <TextField
          autoFocus
          error={fieldErrors.name}
          label="Name"
          required
          value={values.name}
          onChange={(name) => setValues((current) => ({ ...current, name }))}
        />
        <TextField
          error={fieldErrors.city}
          label="City"
          required
          value={values.city}
          onChange={(city) => setValues((current) => ({ ...current, city }))}
        />
        <TextField
          error={fieldErrors.address}
          label="Address"
          value={values.address}
          onChange={(address) => setValues((current) => ({ ...current, address }))}
        />
        <TextField
          error={fieldErrors.manager_name}
          label="Manager"
          value={values.manager_name}
          onChange={(manager_name) =>
            setValues((current) => ({ ...current, manager_name }))
          }
        />
        <TextField
          error={fieldErrors.emblem_url}
          label="Emblem URL"
          placeholder="https://example.com/badge.png"
          value={values.emblem_url}
          onChange={(emblem_url) =>
            setValues((current) => ({ ...current, emblem_url }))
          }
        />
        <label className="field">
          <span>Previous season place</span>
          <input
            min={1}
            onChange={(event) =>
              setValues((current) => ({
                ...current,
                previous_season_place: event.target.value,
              }))
            }
            type="number"
            value={values.previous_season_place}
          />
          {fieldErrors.previous_season_place ? (
            <small className="field-error">
              {fieldErrors.previous_season_place}
            </small>
          ) : null}
        </label>
      </div>

      <div className="form-actions">
        <button
          className="button button-primary"
          disabled={isSaving || !values.name.trim() || !values.city.trim()}
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

function TextField({
  autoFocus,
  error,
  label,
  onChange,
  placeholder,
  required,
  type = "text",
  value,
}: {
  autoFocus?: boolean;
  error?: string;
  label: string;
  onChange: (value: string) => void;
  placeholder?: string;
  required?: boolean;
  type?: string;
  value: string;
}) {
  return (
    <label className="field">
      <span>{label}</span>
      <input
        autoFocus={autoFocus}
        minLength={required ? 1 : undefined}
        onChange={(event) => onChange(event.target.value)}
        placeholder={placeholder}
        required={required}
        type={type}
        value={value}
      />
      {error ? <small className="field-error">{error}</small> : null}
    </label>
  );
}

function teamToFormValues(team: Team | null): TeamFormValues {
  if (!team) {
    return {
      name: "",
      city: "",
      address: "",
      manager_name: "",
      emblem_url: "",
      previous_season_place: "",
    };
  }

  return {
    name: team.name,
    city: team.city,
    address: team.address ?? "",
    manager_name: team.manager_name ?? "",
    emblem_url: team.emblem_url ?? "",
    previous_season_place: team.previous_season_place
      ? String(team.previous_season_place)
      : "",
  };
}

function getHomeStadiumName(teamId: number, stadiums: Stadium[]) {
  return (
    stadiums.find((stadium) => stadium.home_team_id === teamId)?.name ?? "not set"
  );
}

function emptyToNull(value: string) {
  const trimmed = value.trim();
  return trimmed ? trimmed : null;
}

async function invalidateTeamReads(queryClient: ReturnType<typeof useQueryClient>) {
  await queryClient.invalidateQueries({ queryKey: ["teams"] });
  await queryClient.invalidateQueries({ queryKey: ["stadiums"] });
  await queryClient.invalidateQueries({ queryKey: ["matches"] });
}
