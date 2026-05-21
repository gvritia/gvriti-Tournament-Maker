import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useMemo, useState, type FormEvent, type ReactNode } from "react";
import { DataTable } from "../components/DataTable";
import { useConfirmationDialog } from "../components/ConfirmationDialog";
import { TeamInline } from "../components/TeamInline";
import { useAuth } from "../features/auth/AuthProvider";
import type { ApiError } from "../shared/api/client";
import {
  createSeason,
  createReferee,
  createStadium,
  deleteReferee,
  deleteSeason,
  deleteStadium,
  fetchReferees,
  fetchSeasons,
  fetchStadiums,
  fetchTeams,
  fetchTournaments,
  rolloverSeason,
  updateSeason,
  updateReferee,
  updateStadium,
} from "../shared/api/endpoints";
import type { Referee, Season, Stadium, Team, Tournament } from "../shared/api/types";

export function WorkspaceSeasonsPage() {
  const { token } = useAuth();
  const safeToken = token ?? "";
  const queryClient = useQueryClient();
  const confirmation = useConfirmationDialog();
  const [search, setSearch] = useState("");
  const [status, setStatus] = useState("all");
  const [editingSeason, setEditingSeason] = useState<Season | null>(null);
  const [rolloverSourceSeason, setRolloverSourceSeason] =
    useState<Season | null>(null);
  const [isFormOpen, setIsFormOpen] = useState(false);
  const [formError, setFormError] = useState<string | null>(null);
  const [fieldErrors, setFieldErrors] = useState<Record<string, string>>({});
  const [operationError, setOperationError] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);

  const seasonsQuery = useQuery({
    queryKey: ["seasons"],
    queryFn: () => fetchSeasons(safeToken),
    enabled: Boolean(token),
  });

  const seasons = seasonsQuery.data ?? [];
  const filteredSeasons = useMemo(() => {
    const normalizedSearch = search.trim().toLowerCase();
    return seasons.filter((season) => {
      const bySearch =
        !normalizedSearch ||
        season.name.toLowerCase().includes(normalizedSearch);
      const byStatus = status === "all" || season.status === status;
      return bySearch && byStatus;
    });
  }, [search, seasons, status]);

  const createMutation = useMutation({
    mutationFn: (payload: SeasonFormValues) => createSeason(safeToken, payload),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ["seasons"] });
    },
  });

  const updateMutation = useMutation({
    mutationFn: (payload: { id: number; values: SeasonFormValues }) =>
      updateSeason(safeToken, payload.id, payload.values),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ["seasons"] });
    },
  });

  const rolloverMutation = useMutation({
    mutationFn: (payload: { id: number; values: SeasonRolloverFormValues }) =>
      rolloverSeason(safeToken, payload.id, {
        name: payload.values.name,
        start_date: payload.values.start_date,
        end_date: payload.values.end_date,
        status: payload.values.status,
        copy_tournaments: payload.values.copy_tournaments,
      }),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ["seasons"] });
      await queryClient.invalidateQueries({ queryKey: ["tournaments"] });
      await queryClient.invalidateQueries({ queryKey: ["matches"] });
    },
  });

  const deleteMutation = useMutation({
    mutationFn: (seasonId: number) => deleteSeason(safeToken, seasonId),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ["seasons"] });
      await queryClient.invalidateQueries({ queryKey: ["tournaments"] });
      await queryClient.invalidateQueries({ queryKey: ["matches"] });
    },
  });

  const isSaving =
    createMutation.isPending ||
    updateMutation.isPending ||
    rolloverMutation.isPending;

  function openCreateForm() {
    setEditingSeason(null);
    setRolloverSourceSeason(null);
    setFormError(null);
    setFieldErrors({});
    setOperationError(null);
    setSuccessMessage(null);
    setIsFormOpen(true);
  }

  function openEditForm(season: Season) {
    setEditingSeason(season);
    setRolloverSourceSeason(null);
    setFormError(null);
    setFieldErrors({});
    setOperationError(null);
    setSuccessMessage(null);
    setIsFormOpen(true);
  }

  function openRolloverForm(season: Season) {
    setEditingSeason(null);
    setRolloverSourceSeason(season);
    setFormError(null);
    setFieldErrors({});
    setOperationError(null);
    setSuccessMessage(null);
    setIsFormOpen(false);
  }

  function closeForm() {
    setIsFormOpen(false);
    setEditingSeason(null);
    setRolloverSourceSeason(null);
    setFormError(null);
    setFieldErrors({});
  }

  async function handleSaveSeason(values: SeasonFormValues) {
    setFormError(null);
    setFieldErrors({});
    setOperationError(null);
    setSuccessMessage(null);

    try {
      if (editingSeason) {
        await updateMutation.mutateAsync({ id: editingSeason.id, values });
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

  async function handleRolloverSeason(values: SeasonRolloverFormValues) {
    if (!rolloverSourceSeason) {
      return;
    }

    setFormError(null);
    setFieldErrors({});
    setOperationError(null);
    setSuccessMessage(null);

    try {
      const result = await rolloverMutation.mutateAsync({
        id: rolloverSourceSeason.id,
        values,
      });
      closeForm();
      setSuccessMessage(
        `Создан сезон "${result.season.name}", скопировано турниров: ${result.tournaments.length}.`,
      );
    } catch (caughtError) {
      const apiError = caughtError as ApiError;
      setFormError(apiError.message);
      setFieldErrors(apiError.fieldErrors ?? {});
    }
  }

  async function handleDeleteSeason(season: Season) {
    const confirmed = await confirmation.confirm({
      message: `Удалить сезон "${season.name}"? Связанные турниры и матчи могут быть затронуты правилами турнира.`,
      confirmLabel: "Удалить",
      tone: "danger",
    });
    if (!confirmed) {
      return;
    }

    setOperationError(null);

    try {
      await deleteMutation.mutateAsync(season.id);
    } catch (caughtError) {
      const apiError = caughtError as ApiError;
      setOperationError(apiError.message);
    }
  }

  return (
    <CatalogPage
      eyebrow="Сезоны"
      title="Сезоны"
      description="Управляйте сезонами текущего пользователя: создавайте периоды соревнований, меняйте даты и статус."
      error={seasonsQuery.error}
      filters={
        <>
          <input
            aria-label="Поиск сезона"
            onChange={(event) => setSearch(event.target.value)}
            placeholder="Название сезона"
            value={search}
          />
          <select
            aria-label="Статус сезона"
            onChange={(event) => setStatus(event.target.value)}
            value={status}
          >
            <option value="all">Все статусы</option>
            <option value="planned">planned</option>
            <option value="active">active</option>
            <option value="finished">finished</option>
          </select>
        </>
      }
      action={
        <button className="button button-primary" type="button" onClick={openCreateForm}>
          Создать сезон
        </button>
      }
    >
      {operationError ? <div className="form-error">{operationError}</div> : null}
      {successMessage ? (
        <div className="notice notice-success">
          <strong>{successMessage}</strong>
        </div>
      ) : null}

      {isFormOpen ? (
        <SeasonForm
          key={editingSeason?.id ?? "new"}
          initialValues={
            editingSeason
              ? {
                  name: editingSeason.name,
                  start_date: editingSeason.start_date,
                  end_date: editingSeason.end_date,
                  status: editingSeason.status,
                }
              : getDefaultSeasonValues()
          }
          isSaving={isSaving}
          mode={editingSeason ? "edit" : "create"}
          error={formError}
          fieldErrors={fieldErrors}
          onCancel={closeForm}
          onSubmit={handleSaveSeason}
        />
      ) : null}

      {rolloverSourceSeason ? (
        <SeasonRolloverForm
          key={rolloverSourceSeason.id}
          initialValues={getDefaultRolloverValues(rolloverSourceSeason)}
          isSaving={isSaving}
          sourceSeason={rolloverSourceSeason}
          error={formError}
          fieldErrors={fieldErrors}
          onCancel={closeForm}
          onSubmit={handleRolloverSeason}
        />
      ) : null}

      <DataTable
        rows={filteredSeasons}
        getRowKey={(season) => season.id}
        emptyText="Сезоны не найдены"
        isLoading={seasonsQuery.isLoading}
        columns={[
          { key: "name", header: "Сезон", render: (season) => season.name },
          {
            key: "dates",
            header: "Период",
            render: (season) =>
              `${formatDate(season.start_date)} - ${formatDate(season.end_date)}`,
          },
          {
            key: "status",
            header: "Статус",
            render: (season) => (
              <span className={`status status-${season.status}`}>
                {season.status}
              </span>
            ),
          },
          {
            key: "actions",
            header: "Действия",
            render: (season) => (
              <div className="row-actions">
                <button
                  className="button button-ghost"
                  type="button"
                  onClick={() => openEditForm(season)}
                >
                  Изменить
                </button>
                <button
                  className="button button-ghost"
                  disabled={rolloverMutation.isPending}
                  type="button"
                  onClick={() => openRolloverForm(season)}
                >
                  Следующий сезон
                </button>
                <button
                  className="button button-danger"
                  disabled={deleteMutation.isPending}
                  type="button"
                  onClick={() => handleDeleteSeason(season)}
                >
                  Удалить
                </button>
              </div>
            ),
          },
        ]}
      />
      {confirmation.dialog}
    </CatalogPage>
  );
}

export function WorkspaceStadiumsPage() {
  const { token } = useAuth();
  const safeToken = token ?? "";
  const queryClient = useQueryClient();
  const confirmation = useConfirmationDialog();
  const [search, setSearch] = useState("");
  const [editingStadium, setEditingStadium] = useState<Stadium | null>(null);
  const [isFormOpen, setIsFormOpen] = useState(false);
  const [formError, setFormError] = useState<string | null>(null);
  const [fieldErrors, setFieldErrors] = useState<Record<string, string>>({});
  const [operationError, setOperationError] = useState<string | null>(null);

  const stadiumsQuery = useQuery({
    queryKey: ["stadiums"],
    queryFn: () => fetchStadiums(safeToken),
    enabled: Boolean(token),
  });
  const teamsQuery = useQuery({
    queryKey: ["teams"],
    queryFn: () => fetchTeams(safeToken),
    enabled: Boolean(token),
  });

  const stadiums = stadiumsQuery.data ?? [];
  const teams = teamsQuery.data ?? [];
  const error = stadiumsQuery.error ?? teamsQuery.error ?? null;
  const filteredStadiums = useMemo(() => {
    const normalizedSearch = search.trim().toLowerCase();
    if (!normalizedSearch) {
      return stadiums;
    }

    return stadiums.filter((stadium) =>
      [stadium.name, stadium.city, stadium.address]
        .join(" ")
        .toLowerCase()
        .includes(normalizedSearch),
    );
  }, [search, stadiums]);

  const createMutation = useMutation({
    mutationFn: (payload: StadiumFormPayload) => createStadium(safeToken, payload),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ["stadiums"] });
    },
  });

  const updateMutation = useMutation({
    mutationFn: (payload: { id: number; values: StadiumFormPayload }) =>
      updateStadium(safeToken, payload.id, payload.values),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ["stadiums"] });
      await queryClient.invalidateQueries({ queryKey: ["matches"] });
    },
  });

  const deleteMutation = useMutation({
    mutationFn: (stadiumId: number) => deleteStadium(safeToken, stadiumId),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ["stadiums"] });
      await queryClient.invalidateQueries({ queryKey: ["matches"] });
    },
  });

  const isSaving = createMutation.isPending || updateMutation.isPending;

  function openCreateForm() {
    setEditingStadium(null);
    setFormError(null);
    setFieldErrors({});
    setOperationError(null);
    setIsFormOpen(true);
  }

  function openEditForm(stadium: Stadium) {
    setEditingStadium(stadium);
    setFormError(null);
    setFieldErrors({});
    setOperationError(null);
    setIsFormOpen(true);
  }

  function closeForm() {
    setIsFormOpen(false);
    setEditingStadium(null);
    setFormError(null);
    setFieldErrors({});
  }

  async function handleSaveStadium(values: StadiumFormPayload) {
    setFormError(null);
    setFieldErrors({});
    setOperationError(null);

    try {
      if (editingStadium) {
        await updateMutation.mutateAsync({ id: editingStadium.id, values });
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

  async function handleDeleteStadium(stadium: Stadium) {
    const confirmed = await confirmation.confirm({
      message: `Удалить стадион "${stadium.name}"? Матчи и домашняя команда могут быть затронуты правилами турнира.`,
      confirmLabel: "Удалить",
      tone: "danger",
    });
    if (!confirmed) {
      return;
    }

    setOperationError(null);

    try {
      await deleteMutation.mutateAsync(stadium.id);
    } catch (caughtError) {
      const apiError = caughtError as ApiError;
      setOperationError(apiError.message);
    }
  }

  return (
    <CatalogPage
      eyebrow="Стадионы"
      title="Стадионы"
      description="Стадионы не зависят от сезона напрямую. Домашняя команда берется из `home_team_id`."
      error={error}
      filters={
        <input
          aria-label="Поиск стадиона"
          onChange={(event) => setSearch(event.target.value)}
          placeholder="Название, город или адрес"
          value={search}
        />
      }
      action={
        <button className="button button-primary" type="button" onClick={openCreateForm}>
          Создать стадион
        </button>
      }
    >
      {operationError ? <div className="form-error">{operationError}</div> : null}

      {isFormOpen ? (
        <StadiumForm
          key={editingStadium?.id ?? "new"}
          initialValues={
            editingStadium
              ? {
                  name: editingStadium.name,
                  city: editingStadium.city,
                  address: editingStadium.address,
                  capacity: String(editingStadium.capacity),
                  home_team_id: editingStadium.home_team_id
                    ? String(editingStadium.home_team_id)
                    : "",
                }
              : getDefaultStadiumValues()
          }
          isSaving={isSaving}
          mode={editingStadium ? "edit" : "create"}
          teams={teams}
          error={formError}
          fieldErrors={fieldErrors}
          onCancel={closeForm}
          onSubmit={handleSaveStadium}
        />
      ) : null}

      <DataTable
        rows={filteredStadiums}
        getRowKey={(stadium) => stadium.id}
        emptyText="Стадионы не найдены"
        isLoading={stadiumsQuery.isLoading || teamsQuery.isLoading}
        columns={[
          { key: "name", header: "Стадион", render: (stadium) => stadium.name },
          { key: "city", header: "Город", render: (stadium) => stadium.city },
          {
            key: "capacity",
            header: "Вместимость",
            render: (stadium) => stadium.capacity.toLocaleString("ru-RU"),
          },
          {
            key: "homeTeam",
            header: "Домашняя команда",
            render: (stadium) => (
              <TeamInline
                fallbackName={getTeamName(stadium.home_team_id, teams)}
                team={getTeamById(stadium.home_team_id, teams)}
              />
            ),
          },
          {
            key: "address",
            header: "Адрес",
            render: (stadium) => stadium.address,
          },
          {
            key: "actions",
            header: "Действия",
            render: (stadium) => (
              <div className="row-actions">
                <button
                  className="button button-ghost"
                  type="button"
                  onClick={() => openEditForm(stadium)}
                >
                  Изменить
                </button>
                <button
                  className="button button-danger"
                  disabled={deleteMutation.isPending}
                  type="button"
                  onClick={() => handleDeleteStadium(stadium)}
                >
                  Удалить
                </button>
              </div>
            ),
          },
        ]}
      />
      {confirmation.dialog}
    </CatalogPage>
  );
}

export function WorkspaceRefereesPage() {
  const { token } = useAuth();
  const safeToken = token ?? "";
  const queryClient = useQueryClient();
  const confirmation = useConfirmationDialog();
  const [search, setSearch] = useState("");
  const [editingReferee, setEditingReferee] = useState<Referee | null>(null);
  const [isFormOpen, setIsFormOpen] = useState(false);
  const [formError, setFormError] = useState<string | null>(null);
  const [fieldErrors, setFieldErrors] = useState<Record<string, string>>({});
  const [operationError, setOperationError] = useState<string | null>(null);

  const refereesQuery = useQuery({
    queryKey: ["referees"],
    queryFn: () => fetchReferees(safeToken),
    enabled: Boolean(token),
  });

  const referees = refereesQuery.data ?? [];
  const filteredReferees = useMemo(() => {
    const normalizedSearch = search.trim().toLowerCase();
    if (!normalizedSearch) {
      return referees;
    }

    return referees.filter((referee) =>
      referee.full_name.toLowerCase().includes(normalizedSearch),
    );
  }, [referees, search]);

  const createMutation = useMutation({
    mutationFn: (fullName: string) =>
      createReferee(safeToken, { full_name: fullName }),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ["referees"] });
    },
  });

  const updateMutation = useMutation({
    mutationFn: (payload: { id: number; fullName: string }) =>
      updateReferee(safeToken, payload.id, { full_name: payload.fullName }),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ["referees"] });
    },
  });

  const deleteMutation = useMutation({
    mutationFn: (refereeId: number) => deleteReferee(safeToken, refereeId),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ["referees"] });
    },
  });

  const isSaving = createMutation.isPending || updateMutation.isPending;

  function openCreateForm() {
    setEditingReferee(null);
    setFormError(null);
    setFieldErrors({});
    setOperationError(null);
    setIsFormOpen(true);
  }

  function openEditForm(referee: Referee) {
    setEditingReferee(referee);
    setFormError(null);
    setFieldErrors({});
    setOperationError(null);
    setIsFormOpen(true);
  }

  function closeForm() {
    setIsFormOpen(false);
    setEditingReferee(null);
    setFormError(null);
    setFieldErrors({});
  }

  async function handleSaveReferee(fullName: string) {
    setFormError(null);
    setFieldErrors({});
    setOperationError(null);

    try {
      if (editingReferee) {
        await updateMutation.mutateAsync({
          id: editingReferee.id,
          fullName,
        });
      } else {
        await createMutation.mutateAsync(fullName);
      }
      closeForm();
    } catch (caughtError) {
      const apiError = caughtError as ApiError;
      setFormError(apiError.message);
      setFieldErrors(apiError.fieldErrors ?? {});
    }
  }

  async function handleDeleteReferee(referee: Referee) {
    const confirmed = await confirmation.confirm({
      message: `Удалить судью "${referee.full_name}"? Это действие нельзя отменить.`,
      confirmLabel: "Удалить",
      tone: "danger",
    });
    if (!confirmed) {
      return;
    }

    setOperationError(null);

    try {
      await deleteMutation.mutateAsync(referee.id);
    } catch (caughtError) {
      const apiError = caughtError as ApiError;
      setOperationError(apiError.message);
    }
  }

  return (
    <CatalogPage
      eyebrow="Судьи"
      title="Судьи"
      description="Список судей вашей рабочей области. Одного судью нельзя назначить на параллельные матчи."
      error={refereesQuery.error}
      filters={
        <input
          aria-label="Поиск судьи"
          onChange={(event) => setSearch(event.target.value)}
          placeholder="ФИО судьи"
          value={search}
        />
      }
      action={
        <button className="button button-primary" type="button" onClick={openCreateForm}>
          Создать судью
        </button>
      }
    >
      {operationError ? <div className="form-error">{operationError}</div> : null}

      {isFormOpen ? (
        <RefereeForm
          key={editingReferee?.id ?? "new"}
          initialName={editingReferee?.full_name ?? ""}
          isSaving={isSaving}
          mode={editingReferee ? "edit" : "create"}
          error={formError}
          fieldError={fieldErrors.full_name}
          onCancel={closeForm}
          onSubmit={handleSaveReferee}
        />
      ) : null}

      <DataTable
        rows={filteredReferees}
        getRowKey={(referee) => referee.id}
        emptyText="Судьи не найдены"
        isLoading={refereesQuery.isLoading}
        columns={[
          {
            key: "name",
            header: "Судья",
            render: (referee) => referee.full_name,
          },
          {
            key: "created",
            header: "Создан",
            render: (referee) => formatDate(referee.created_at),
          },
          {
            key: "actions",
            header: "Действия",
            render: (referee) => (
              <div className="row-actions">
                <button
                  className="button button-ghost"
                  type="button"
                  onClick={() => openEditForm(referee)}
                >
                  Изменить
                </button>
                <button
                  className="button button-danger"
                  disabled={deleteMutation.isPending}
                  type="button"
                  onClick={() => handleDeleteReferee(referee)}
                >
                  Удалить
                </button>
              </div>
            ),
          },
        ]}
      />
      {confirmation.dialog}
    </CatalogPage>
  );
}

export function WorkspaceTournamentsPage() {
  const { token } = useAuth();
  const safeToken = token ?? "";
  const [search, setSearch] = useState("");
  const [type, setType] = useState("all");
  const [status, setStatus] = useState("all");

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
      const bySearch =
        !normalizedSearch ||
        tournament.name.toLowerCase().includes(normalizedSearch);
      const byType = type === "all" || tournament.type === type;
      const byStatus = status === "all" || tournament.status === status;
      return bySearch && byType && byStatus;
    });
  }, [search, status, tournaments, type]);

  return (
    <CatalogPage
      eyebrow="Турниры"
      title="Турниры"
      description="Чемпионаты и кубки внутри сезонов. Генерация календарей и сеток подключается в отдельных workflow-экранах."
      error={error}
      filters={
        <>
          <input
            aria-label="Поиск турнира"
            onChange={(event) => setSearch(event.target.value)}
            placeholder="Название турнира"
            value={search}
          />
          <select
            aria-label="Тип турнира"
            onChange={(event) => setType(event.target.value)}
            value={type}
          >
            <option value="all">Все типы</option>
            <option value="championship">championship</option>
            <option value="cup">cup</option>
          </select>
          <select
            aria-label="Статус турнира"
            onChange={(event) => setStatus(event.target.value)}
            value={status}
          >
            <option value="all">Все статусы</option>
            <option value="planned">planned</option>
            <option value="active">active</option>
            <option value="finished">finished</option>
          </select>
        </>
      }
      actionLabel="Создать турнир"
    >
      <DataTable
        rows={filteredTournaments}
        getRowKey={(tournament) => tournament.id}
        emptyText="Турниры не найдены"
        isLoading={tournamentsQuery.isLoading || seasonsQuery.isLoading}
        columns={[
          {
            key: "name",
            header: "Турнир",
            render: (tournament) => tournament.name,
          },
          {
            key: "season",
            header: "Сезон",
            render: (tournament) => getSeasonName(tournament.season_id, seasons),
          },
          { key: "type", header: "Тип", render: (tournament) => tournament.type },
          {
            key: "status",
            header: "Статус",
            render: (tournament) => (
              <span className={`status status-${tournament.status}`}>
                {tournament.status}
              </span>
            ),
          },
        ]}
      />
    </CatalogPage>
  );
}

function CatalogPage({
  eyebrow,
  title,
  description,
  error,
  filters,
  actionLabel,
  action,
  children,
}: {
  eyebrow: string;
  title: string;
  description: string;
  error: Error | null;
  filters: ReactNode;
  actionLabel?: string;
  action?: ReactNode;
  children: ReactNode;
}) {
  return (
    <div className="page-stack">
      <section className="page-intro">
        <p className="eyebrow">{eyebrow}</p>
        <h2>{title}</h2>
        <p className="muted">{description}</p>
      </section>

      {error ? (
        <section className="notice notice-danger">
          <strong>Не удалось загрузить данные.</strong>
          <span>{error.message}</span>
        </section>
      ) : null}

      <section className="panel">
        <div className="section-head">
          <div className="filter-row">{filters}</div>
          {action ?? (
            <button className="button button-primary" type="button" disabled>
              {actionLabel}
            </button>
          )}
        </div>
        {children}
      </section>
    </div>
  );
}

type SeasonFormValues = {
  name: string;
  start_date: string;
  end_date: string;
  status: string;
};

type SeasonRolloverFormValues = SeasonFormValues & {
  copy_tournaments: boolean;
};

function SeasonForm({
  initialValues,
  mode,
  isSaving,
  error,
  fieldErrors,
  onCancel,
  onSubmit,
}: {
  initialValues: SeasonFormValues;
  mode: "create" | "edit";
  isSaving: boolean;
  error: string | null;
  fieldErrors: Record<string, string>;
  onCancel: () => void;
  onSubmit: (values: SeasonFormValues) => Promise<void>;
}) {
  const [values, setValues] = useState(initialValues);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    await onSubmit({
      ...values,
      name: values.name.trim(),
    });
  }

  return (
    <form className="inline-form" onSubmit={handleSubmit}>
      <div>
        <p className="eyebrow">{mode === "create" ? "Create" : "Edit"}</p>
        <h2>{mode === "create" ? "Новый сезон" : "Редактирование сезона"}</h2>
      </div>

      {error ? <div className="form-error">{error}</div> : null}

      <div className="form-grid">
        <label className="field">
          <span>Название</span>
          <input
            autoFocus
            minLength={1}
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
          <span>Статус</span>
          <select
            onChange={(event) =>
              setValues((current) => ({ ...current, status: event.target.value }))
            }
            value={values.status}
          >
            <option value="planned">planned</option>
            <option value="active">active</option>
            <option value="finished">finished</option>
            <option value="archived">archived</option>
          </select>
          {fieldErrors.status ? (
            <small className="field-error">{fieldErrors.status}</small>
          ) : null}
        </label>

        <label className="field">
          <span>Дата начала</span>
          <input
            onChange={(event) =>
              setValues((current) => ({
                ...current,
                start_date: event.target.value,
              }))
            }
            required
            type="date"
            value={values.start_date}
          />
          {fieldErrors.start_date ? (
            <small className="field-error">{fieldErrors.start_date}</small>
          ) : null}
        </label>

        <label className="field">
          <span>Дата окончания</span>
          <input
            onChange={(event) =>
              setValues((current) => ({ ...current, end_date: event.target.value }))
            }
            required
            type="date"
            value={values.end_date}
          />
          {fieldErrors.end_date ? (
            <small className="field-error">{fieldErrors.end_date}</small>
          ) : null}
        </label>
      </div>

      <div className="form-actions">
        <button
          className="button button-primary"
          disabled={isSaving || !values.name.trim()}
          type="submit"
        >
          {isSaving ? "Сохраняем..." : "Сохранить"}
        </button>
        <button
          className="button button-ghost"
          disabled={isSaving}
          type="button"
          onClick={onCancel}
        >
          Отмена
        </button>
      </div>
    </form>
  );
}

function SeasonRolloverForm({
  initialValues,
  isSaving,
  sourceSeason,
  error,
  fieldErrors,
  onCancel,
  onSubmit,
}: {
  initialValues: SeasonRolloverFormValues;
  isSaving: boolean;
  sourceSeason: Season;
  error: string | null;
  fieldErrors: Record<string, string>;
  onCancel: () => void;
  onSubmit: (values: SeasonRolloverFormValues) => Promise<void>;
}) {
  const [values, setValues] = useState(initialValues);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    await onSubmit({
      ...values,
      name: values.name.trim(),
    });
  }

  return (
    <form className="inline-form" onSubmit={handleSubmit}>
      <div>
        <p className="eyebrow">Rollover</p>
        <h2>Следующий сезон</h2>
        <p className="muted">
          Команды, игроки, стадионы и судьи уже общие для всего кабинета. Здесь
          создается новый сезон, а турниры можно скопировать из "{sourceSeason.name}".
        </p>
      </div>

      {error ? <div className="form-error">{error}</div> : null}

      <div className="form-grid">
        <label className="field">
          <span>Название</span>
          <input
            autoFocus
            minLength={1}
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
          <span>Статус</span>
          <select
            onChange={(event) =>
              setValues((current) => ({ ...current, status: event.target.value }))
            }
            value={values.status}
          >
            <option value="planned">planned</option>
            <option value="active">active</option>
          </select>
          {fieldErrors.status ? (
            <small className="field-error">{fieldErrors.status}</small>
          ) : null}
        </label>

        <label className="field">
          <span>Дата начала</span>
          <input
            onChange={(event) =>
              setValues((current) => ({
                ...current,
                start_date: event.target.value,
              }))
            }
            required
            type="date"
            value={values.start_date}
          />
          {fieldErrors.start_date ? (
            <small className="field-error">{fieldErrors.start_date}</small>
          ) : null}
        </label>

        <label className="field">
          <span>Дата окончания</span>
          <input
            onChange={(event) =>
              setValues((current) => ({ ...current, end_date: event.target.value }))
            }
            required
            type="date"
            value={values.end_date}
          />
          {fieldErrors.end_date ? (
            <small className="field-error">{fieldErrors.end_date}</small>
          ) : null}
        </label>

        <label className="field">
          <span>Турниры</span>
          <label className="mode-chip">
            <input
              checked={values.copy_tournaments}
              onChange={(event) =>
                setValues((current) => ({
                  ...current,
                  copy_tournaments: event.target.checked,
                }))
              }
              type="checkbox"
            />
            Скопировать турниры прошлого сезона
          </label>
          {fieldErrors.copy_tournaments ? (
            <small className="field-error">{fieldErrors.copy_tournaments}</small>
          ) : null}
        </label>
      </div>

      <div className="form-actions">
        <button
          className="button button-primary"
          disabled={isSaving || !values.name.trim()}
          type="submit"
        >
          {isSaving ? "Создаем..." : "Создать следующий сезон"}
        </button>
        <button
          className="button button-ghost"
          disabled={isSaving}
          type="button"
          onClick={onCancel}
        >
          Отмена
        </button>
      </div>
    </form>
  );
}

function getDefaultSeasonValues(): SeasonFormValues {
  const currentYear = new Date().getFullYear();
  return {
    name: `${currentYear}/${currentYear + 1}`,
    start_date: `${currentYear}-07-01`,
    end_date: `${currentYear + 1}-05-31`,
    status: "planned",
  };
}

function getDefaultRolloverValues(season: Season): SeasonRolloverFormValues {
  return {
    name: getNextSeasonName(season.name),
    start_date: addYearsToDateValue(season.start_date, 1),
    end_date: addYearsToDateValue(season.end_date, 1),
    status: "planned",
    copy_tournaments: true,
  };
}

function getNextSeasonName(name: string): string {
  const nextName = name.replace(/\d{4}/g, (year) => String(Number(year) + 1));
  if (nextName !== name) {
    return nextName;
  }
  return `${name} next`;
}

function addYearsToDateValue(value: string, years: number): string {
  const [year, month, day] = value.split("-").map(Number);
  if (!year || !month || !day) {
    return value;
  }

  const date = new Date(Date.UTC(year + years, month - 1, day));
  return date.toISOString().slice(0, 10);
}

type StadiumFormValues = {
  name: string;
  city: string;
  address: string;
  capacity: string;
  home_team_id: string;
};

type StadiumFormPayload = {
  name: string;
  city: string;
  address: string;
  capacity: number;
  home_team_id: number | null;
};

function StadiumForm({
  initialValues,
  mode,
  teams,
  isSaving,
  error,
  fieldErrors,
  onCancel,
  onSubmit,
}: {
  initialValues: StadiumFormValues;
  mode: "create" | "edit";
  teams: Team[];
  isSaving: boolean;
  error: string | null;
  fieldErrors: Record<string, string>;
  onCancel: () => void;
  onSubmit: (values: StadiumFormPayload) => Promise<void>;
}) {
  const [values, setValues] = useState(initialValues);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    await onSubmit({
      name: values.name.trim(),
      city: values.city.trim(),
      address: values.address.trim(),
      capacity: Number(values.capacity),
      home_team_id: values.home_team_id ? Number(values.home_team_id) : null,
    });
  }

  return (
    <form className="inline-form" onSubmit={handleSubmit}>
      <div>
        <p className="eyebrow">{mode === "create" ? "Create" : "Edit"}</p>
        <h2>{mode === "create" ? "Новый стадион" : "Редактирование стадиона"}</h2>
      </div>

      {error ? <div className="form-error">{error}</div> : null}

      <div className="form-grid">
        <label className="field">
          <span>Название</span>
          <input
            autoFocus
            minLength={1}
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
          <span>Город</span>
          <input
            minLength={1}
            onChange={(event) =>
              setValues((current) => ({ ...current, city: event.target.value }))
            }
            required
            value={values.city}
          />
          {fieldErrors.city ? (
            <small className="field-error">{fieldErrors.city}</small>
          ) : null}
        </label>

        <label className="field">
          <span>Адрес</span>
          <input
            minLength={1}
            onChange={(event) =>
              setValues((current) => ({ ...current, address: event.target.value }))
            }
            required
            value={values.address}
          />
          {fieldErrors.address ? (
            <small className="field-error">{fieldErrors.address}</small>
          ) : null}
        </label>

        <label className="field">
          <span>Вместимость</span>
          <input
            min={1}
            onChange={(event) =>
              setValues((current) => ({ ...current, capacity: event.target.value }))
            }
            required
            type="number"
            value={values.capacity}
          />
          {fieldErrors.capacity ? (
            <small className="field-error">{fieldErrors.capacity}</small>
          ) : null}
        </label>

        <label className="field">
          <span>Домашняя команда</span>
          <select
            onChange={(event) =>
              setValues((current) => ({
                ...current,
                home_team_id: event.target.value,
              }))
            }
            value={values.home_team_id}
          >
            <option value="">Не назначена</option>
            {teams.map((team) => (
              <option key={team.id} value={team.id}>
                {team.name}
              </option>
            ))}
          </select>
          {fieldErrors.home_team_id ? (
            <small className="field-error">{fieldErrors.home_team_id}</small>
          ) : null}
        </label>
      </div>

      <div className="form-actions">
        <button
          className="button button-primary"
          disabled={
            isSaving ||
            !values.name.trim() ||
            !values.city.trim() ||
            !values.address.trim() ||
            Number(values.capacity) <= 0
          }
          type="submit"
        >
          {isSaving ? "Сохраняем..." : "Сохранить"}
        </button>
        <button
          className="button button-ghost"
          disabled={isSaving}
          type="button"
          onClick={onCancel}
        >
          Отмена
        </button>
      </div>
    </form>
  );
}

function getDefaultStadiumValues(): StadiumFormValues {
  return {
    name: "",
    city: "",
    address: "",
    capacity: "10000",
    home_team_id: "",
  };
}

function RefereeForm({
  initialName,
  mode,
  isSaving,
  error,
  fieldError,
  onCancel,
  onSubmit,
}: {
  initialName: string;
  mode: "create" | "edit";
  isSaving: boolean;
  error: string | null;
  fieldError?: string;
  onCancel: () => void;
  onSubmit: (fullName: string) => Promise<void>;
}) {
  const [fullName, setFullName] = useState(initialName);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    await onSubmit(fullName.trim());
  }

  return (
    <form className="inline-form" onSubmit={handleSubmit}>
      <div>
        <p className="eyebrow">{mode === "create" ? "Create" : "Edit"}</p>
        <h2>{mode === "create" ? "Новый судья" : "Редактирование судьи"}</h2>
      </div>

      {error ? <div className="form-error">{error}</div> : null}

      <label className="field">
        <span>ФИО судьи</span>
        <input
          autoFocus
          minLength={1}
          onChange={(event) => setFullName(event.target.value)}
          required
          value={fullName}
        />
        {fieldError ? <small className="field-error">{fieldError}</small> : null}
      </label>

      <div className="form-actions">
        <button
          className="button button-primary"
          disabled={isSaving || !fullName.trim()}
          type="submit"
        >
          {isSaving ? "Сохраняем..." : "Сохранить"}
        </button>
        <button
          className="button button-ghost"
          disabled={isSaving}
          type="button"
          onClick={onCancel}
        >
          Отмена
        </button>
      </div>
    </form>
  );
}

function getTeamName(teamId: number | null, teams: Team[]) {
  if (!teamId) {
    return "не указана";
  }

  return teams.find((team) => team.id === teamId)?.name ?? `Team ${teamId}`;
}

function getTeamById(teamId: number | null, teams: Team[]) {
  if (!teamId) {
    return undefined;
  }

  return teams.find((team) => team.id === teamId);
}

function getSeasonName(seasonId: number, seasons: Season[]) {
  return seasons.find((season) => season.id === seasonId)?.name ?? `Season ${seasonId}`;
}

function formatDate(value: string) {
  return new Intl.DateTimeFormat("ru-RU", { dateStyle: "short" }).format(
    new Date(value),
  );
}
