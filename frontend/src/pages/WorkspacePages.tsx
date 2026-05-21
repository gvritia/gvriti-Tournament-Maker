import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Link, useParams } from "react-router-dom";
import { DataTable } from "../components/DataTable";
import { MatchupInline } from "../components/MatchupInline";
import { TeamInline } from "../components/TeamInline";
import { TeamMark } from "../components/TeamMark";
import { useAuth } from "../features/auth/AuthProvider";
import type { ApiError } from "../shared/api/client";
import {
  createMatch,
  createTeam,
  deleteTeam,
  fetchMatches,
  fetchMatch,
  fetchPlayers,
  fetchReferees,
  fetchSeasons,
  fetchStadiums,
  fetchTeam,
  fetchTeams,
  fetchTournaments,
  updateTeam,
} from "../shared/api/endpoints";
import type {
  Match,
  Player,
  Referee,
  Season,
  Stadium,
  Team,
  Tournament,
} from "../shared/api/types";
import { useMemo, useState, type FormEvent } from "react";

export function WorkspaceDashboard() {
  const { token, user } = useAuth();
  const safeToken = token ?? "";

  const seasonsQuery = useQuery({
    queryKey: ["seasons"],
    queryFn: () => fetchSeasons(safeToken),
    enabled: Boolean(token),
  });
  const teamsQuery = useQuery({
    queryKey: ["teams"],
    queryFn: () => fetchTeams(safeToken),
    enabled: Boolean(token),
  });
  const matchesQuery = useQuery({
    queryKey: ["matches"],
    queryFn: () => fetchMatches(safeToken),
    enabled: Boolean(token),
  });

  const seasons = seasonsQuery.data ?? [];
  const teams = teamsQuery.data ?? [];
  const matches = matchesQuery.data ?? [];
  const finishedMatches = matches.filter((match) => match.status === "finished");
  const scheduledMatches = matches.filter((match) => match.status === "scheduled");

  const error =
    seasonsQuery.error ?? teamsQuery.error ?? matchesQuery.error ?? null;
  const isInitialLoading =
    seasonsQuery.isLoading || teamsQuery.isLoading || matchesQuery.isLoading;

  return (
    <div className="page-stack">
      <section className="notice notice-success">
        <strong>Вы вошли как {user?.nickname ?? "организатор"}.</strong>
        <span>Загружаем данные вашей рабочей области.</span>
      </section>

      {!isInitialLoading && teams.length >= 20 && seasons.length === 0 ? (
        <section className="notice">
          <strong>Стартовые команды уже созданы.</strong>
          <span>
            В вашем кабинете есть базовые LaLiga-команды со стартовыми игроками,
            домашними стадионами и логотипами. Их можно редактировать, а для
            расписания создайте сезон и турнир.
          </span>
        </section>
      ) : null}

      {error instanceof Error ? (
        <section className="notice notice-danger">
          <strong>Не удалось загрузить данные.</strong>
          <span>{error.message}</span>
        </section>
      ) : null}

      <div className="kpi-grid">
        <MetricCard label="Сезоны" value={isInitialLoading ? "..." : seasons.length} />
        <MetricCard label="Команды" value={isInitialLoading ? "..." : teams.length} />
        <MetricCard
          label="Запланировано"
          value={isInitialLoading ? "..." : scheduledMatches.length}
        />
        <MetricCard
          label="Завершено"
          value={isInitialLoading ? "..." : finishedMatches.length}
        />
      </div>

      <section className="panel">
        <div className="section-head">
          <div>
            <p className="eyebrow">Real teams</p>
            <h2>Команды</h2>
          </div>
          <Link className="button button-ghost" to="/app/teams">
            Открыть команды
          </Link>
        </div>
        <DataTable
          rows={teams}
          getRowKey={(team) => team.id}
          emptyText="Команд пока нет"
          isLoading={teamsQuery.isLoading}
          columns={[
            {
              key: "name",
              header: "Команда",
              render: (team) => (
                <Link className="team-link" to={`/app/teams/${team.id}`}>
                  <TeamMark team={team} />
                  {team.name}
                </Link>
              ),
            },
            { key: "city", header: "Город", render: (team) => team.city },
            {
              key: "manager",
              header: "Менеджер",
              render: (team) => team.manager_name ?? "не указан",
            },
            {
              key: "place",
              header: "Прошлый сезон",
              render: (team) => team.previous_season_place ?? "нет",
            },
          ]}
        />
      </section>

      <section className="panel">
        <div className="section-head">
          <div>
            <p className="eyebrow">Real matches</p>
            <h2>Ближайшие матчи</h2>
          </div>
          <Link className="button button-ghost" to="/app/matches">
            Открыть матчи
          </Link>
        </div>
        <DataTable
          rows={matches.slice(0, 8)}
          getRowKey={(match) => match.id}
          emptyText="Матчей пока нет"
          isLoading={matchesQuery.isLoading}
          columns={[
            {
              key: "date",
              header: "Дата",
              render: (match) => formatDateTime(match.match_datetime),
            },
            {
              key: "pair",
              header: "Команды",
              render: (match) => (
                <Link className="auth-link" to={`/app/matches/${match.id}`}>
                  <MatchupInline match={match} teams={teams} />
                </Link>
              ),
            },
            {
              key: "status",
              header: "Статус",
              render: (match) => (
                <span className={`status status-${match.status}`}>
                  {match.status}
                </span>
              ),
            },
            {
              key: "score",
              header: "Счет",
              render: (match) =>
                match.status === "finished"
                  ? `${match.home_score ?? 0}:${match.away_score ?? 0}`
                  : "не сыгран",
            },
            {
              key: "ticket",
              header: "Билет",
              render: (match) => match.ticket_price ?? "нет",
            },
          ]}
        />
      </section>
    </div>
  );
}

export function WorkspaceTeamsPage() {
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
      await queryClient.invalidateQueries({ queryKey: ["teams"] });
      await queryClient.invalidateQueries({ queryKey: ["stadiums"] });
      await queryClient.invalidateQueries({ queryKey: ["matches"] });
    },
  });

  const updateMutation = useMutation({
    mutationFn: (payload: { id: number; values: TeamFormPayload }) =>
      updateTeam(safeToken, payload.id, payload.values),
    onSuccess: async (team) => {
      await queryClient.invalidateQueries({ queryKey: ["teams"] });
      await queryClient.invalidateQueries({ queryKey: ["team", team.id] });
      await queryClient.invalidateQueries({ queryKey: ["stadiums"] });
      await queryClient.invalidateQueries({ queryKey: ["matches"] });
    },
  });

  const deleteMutation = useMutation({
    mutationFn: (teamId: number) => deleteTeam(safeToken, teamId),
    onSuccess: async (_data, teamId) => {
      await queryClient.invalidateQueries({ queryKey: ["teams"] });
      await queryClient.invalidateQueries({ queryKey: ["team", teamId] });
      await queryClient.invalidateQueries({ queryKey: ["stadiums"] });
      await queryClient.invalidateQueries({ queryKey: ["matches"] });
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
        <h2>Команды</h2>
        <p className="muted">
          Управляйте командами, ищите клубы и открывайте подробные страницы.
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
              aria-label="Поиск команды"
              onChange={(event) => setSearch(event.target.value)}
              placeholder="Название, город или менеджер"
              value={search}
            />
          </div>
          <button className="button button-primary" type="button" onClick={openCreateForm}>
            Создать команду
          </button>
        </div>

        {operationError ? <div className="form-error">{operationError}</div> : null}

        {isFormOpen ? (
          <TeamForm
            key={editingTeam?.id ?? "new"}
            initialValues={
              editingTeam
                ? {
                    name: editingTeam.name,
                    city: editingTeam.city,
                    address: editingTeam.address ?? "",
                    manager_name: editingTeam.manager_name ?? "",
                    emblem_url: editingTeam.emblem_url ?? "",
                    previous_season_place: editingTeam.previous_season_place
                      ? String(editingTeam.previous_season_place)
                      : "",
                  }
                : getDefaultTeamValues()
            }
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
          emptyText="Команды не найдены"
          columns={[
            {
              key: "team",
              header: "Команда",
              render: (team) => (
                <Link className="team-link" to={`/app/teams/${team.id}`}>
                  <TeamMark team={team} />
                  {team.name}
                </Link>
              ),
            },
            { key: "city", header: "Город", render: (team) => team.city },
            {
              key: "stadium",
              header: "Домашний стадион",
              render: (team) => getHomeStadiumName(team.id, stadiums),
            },
            {
              key: "manager",
              header: "Менеджер",
              render: (team) => team.manager_name ?? "не указан",
            },
            {
              key: "place",
              header: "Прошлый сезон",
              render: (team) => team.previous_season_place ?? "нет",
            },
            {
              key: "actions",
              header: "Действия",
              render: (team) => (
                <Link className="button button-ghost" to={`/app/teams/${team.id}`}>
                  Открыть
                </Link>
              ),
            },
          ]}
        />
      </section>
    </div>
  );
}

export function WorkspaceTeamDetailPage() {
  const { token } = useAuth();
  const { teamId } = useParams();
  const safeToken = token ?? "";
  const numericTeamId = Number(teamId);
  const isValidTeamId = Number.isInteger(numericTeamId) && numericTeamId > 0;

  const teamQuery = useQuery({
    queryKey: ["team", numericTeamId],
    queryFn: () => fetchTeam(safeToken, numericTeamId),
    enabled: Boolean(token) && isValidTeamId,
  });
  const playersQuery = useQuery({
    queryKey: ["players"],
    queryFn: () => fetchPlayers(safeToken),
    enabled: Boolean(token) && isValidTeamId,
  });
  const matchesQuery = useQuery({
    queryKey: ["matches"],
    queryFn: () => fetchMatches(safeToken),
    enabled: Boolean(token) && isValidTeamId,
  });
  const stadiumsQuery = useQuery({
    queryKey: ["stadiums"],
    queryFn: () => fetchStadiums(safeToken),
    enabled: Boolean(token) && isValidTeamId,
  });
  const teamsQuery = useQuery({
    queryKey: ["teams"],
    queryFn: () => fetchTeams(safeToken),
    enabled: Boolean(token) && isValidTeamId,
  });

  if (!isValidTeamId) {
    return (
      <div className="page-stack">
        <section className="notice notice-danger">
          <strong>Некорректный адрес команды.</strong>
          <Link to="/app/teams">Вернуться к списку</Link>
        </section>
      </div>
    );
  }

  const team = teamQuery.data;
  const players = (playersQuery.data ?? []).filter(
    (player) => player.team_id === numericTeamId,
  );
  const matches = (matchesQuery.data ?? []).filter(
    (match) =>
      match.home_team_id === numericTeamId || match.away_team_id === numericTeamId,
  );
  const stadiums = stadiumsQuery.data ?? [];
  const teams = teamsQuery.data ?? [];
  const homeStadium = stadiums.find(
    (stadium) => stadium.home_team_id === numericTeamId,
  );
  const error =
    teamQuery.error ??
    playersQuery.error ??
    matchesQuery.error ??
    stadiumsQuery.error ??
    teamsQuery.error ??
    null;
  const isRelatedDataLoading =
    playersQuery.isLoading ||
    matchesQuery.isLoading ||
    stadiumsQuery.isLoading ||
    teamsQuery.isLoading;

  return (
    <div className="page-stack">
      <Link className="back-link" to="/app/teams">
        ← К списку команд
      </Link>

      {error instanceof Error ? (
        <section className="notice notice-danger">
          <strong>Не удалось загрузить команду.</strong>
          <span>{error.message}</span>
        </section>
      ) : null}

      {team ? (
        <>
          <section className="panel team-hero">
            <TeamMark team={team} size="large" />
            <div>
              <p className="eyebrow">Team detail</p>
              <h2>{team.name}</h2>
              <div className="meta-grid">
                <span>Город: {team.city}</span>
                <span>Стадион: {homeStadium?.name ?? "не указан"}</span>
                <span>Менеджер: {team.manager_name ?? "не указан"}</span>
                <span>
                  Место прошлого сезона: {team.previous_season_place ?? "нет"}
                </span>
              </div>
              <p className="muted">{team.address ?? "Адрес не указан"}</p>
            </div>
          </section>

          <div className="split-grid">
            <section className="panel">
              <p className="eyebrow">Home stadium</p>
              <h2>{homeStadium?.name ?? "Домашний стадион не назначен"}</h2>
              {homeStadium ? (
                <div className="meta-grid">
                  <span>Город: {homeStadium.city}</span>
                  <span>Вместимость: {homeStadium.capacity}</span>
                  <span>Адрес: {homeStadium.address}</span>
                </div>
              ) : (
                <p className="muted">
                  Связь берется из `Stadium.home_team_id`. Назначьте домашнюю
                  команду на странице стадионов.
                </p>
              )}
              <Link className="button button-ghost" to="/app/stadiums">
                Открыть стадионы
              </Link>
            </section>

            <section className="panel">
              <p className="eyebrow">Actions</p>
              <h2>Действия команды</h2>
              <div className="action-list">
                <Link className="button button-primary" to="/app/teams">
                  Редактировать в списке
                </Link>
                <Link className="button button-neutral" to="/app/players">
                  Добавить игрока
                </Link>
              </div>
            </section>
          </div>

          <section className="panel">
            <div className="section-head">
              <div>
                <p className="eyebrow">Roster</p>
                <h2>Состав</h2>
              </div>
              <span className="mode-chip">{players.length} игроков</span>
            </div>
            <PlayersTable
              isLoading={isRelatedDataLoading}
              players={players}
            />
          </section>

          <section className="panel">
            <div className="section-head">
              <div>
                <p className="eyebrow">Team matches</p>
                <h2>Матчи команды</h2>
              </div>
              <span className="mode-chip">{matches.length} матчей</span>
            </div>
            <TeamMatchesTable
              isLoading={isRelatedDataLoading}
              matches={matches}
              team={team}
              teams={teams}
            />
          </section>
        </>
      ) : (
        <section className="panel">
          <p className="eyebrow">Loading</p>
          <h2>Загружаем команду</h2>
        </section>
      )}
    </div>
  );
}

export function WorkspaceMatchesPage() {
  const { token } = useAuth();
  const safeToken = token ?? "";
  const queryClient = useQueryClient();
  const [seasonId, setSeasonId] = useState("all");
  const [tournamentId, setTournamentId] = useState("all");
  const [teamId, setTeamId] = useState("all");
  const [status, setStatus] = useState("all");
  const [dateFrom, setDateFrom] = useState("");
  const [dateTo, setDateTo] = useState("");
  const [isFormOpen, setIsFormOpen] = useState(false);
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
      await queryClient.invalidateQueries({ queryKey: ["matches"] });
      await queryClient.invalidateQueries({ queryKey: ["match", match.id] });
    },
  });

  function openCreateForm() {
    setFormError(null);
    setFieldErrors({});
    setOperationError(null);
    setIsFormOpen(true);
  }

  function closeForm() {
    setIsFormOpen(false);
    setFormError(null);
    setFieldErrors({});
  }

  async function handleCreateMatch(values: MatchFormPayload) {
    setFormError(null);
    setFieldErrors({});
    setOperationError(null);

    try {
      await createMutation.mutateAsync(values);
      closeForm();
    } catch (caughtError) {
      const apiError = caughtError as ApiError;
      setFormError(apiError.message);
      setFieldErrors(apiError.fieldErrors ?? {});
    }
  }

  const canCreateMatch =
    seasons.length > 0 &&
    tournaments.length > 0 &&
    teams.length >= 2 &&
    stadiums.length > 0;

  return (
    <div className="page-stack">
      <section className="page-intro">
        <p className="eyebrow">Матчи</p>
        <h2>Матчи</h2>
        <p className="muted">
          Реальный список матчей с фильтрами, статусом, ценой билета и переходом
          в detail. Изменение расписания будет отдельным слоем.
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
            <select
              aria-label="Сезон"
              onChange={(event) => setSeasonId(event.target.value)}
              value={seasonId}
            >
              <option value="all">Все сезоны</option>
              {seasons.map((season) => (
                <option key={season.id} value={season.id}>
                  {season.name}
                </option>
              ))}
            </select>
            <select
              aria-label="Турнир"
              onChange={(event) => setTournamentId(event.target.value)}
              value={tournamentId}
            >
              <option value="all">Все турниры</option>
              {tournaments.map((tournament) => (
                <option key={tournament.id} value={tournament.id}>
                  {tournament.name}
                </option>
              ))}
            </select>
            <select
              aria-label="Команда"
              onChange={(event) => setTeamId(event.target.value)}
              value={teamId}
            >
              <option value="all">Все команды</option>
              {teams.map((team) => (
                <option key={team.id} value={team.id}>
                  {team.name}
                </option>
              ))}
            </select>
            <select
              aria-label="Статус"
              onChange={(event) => setStatus(event.target.value)}
              value={status}
            >
              <option value="all">Все статусы</option>
              <option value="scheduled">scheduled</option>
              <option value="finished">finished</option>
              <option value="cancelled">cancelled</option>
            </select>
            <input
              aria-label="Дата от"
              onChange={(event) => setDateFrom(event.target.value)}
              type="date"
              value={dateFrom}
            />
            <input
              aria-label="Дата до"
              onChange={(event) => setDateTo(event.target.value)}
              type="date"
              value={dateTo}
            />
          </div>
          <button
            className="button button-primary"
            disabled={!canCreateMatch}
            type="button"
            onClick={openCreateForm}
          >
            Создать матч
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

        {isFormOpen ? (
          <MatchCreateForm
            error={formError}
            fieldErrors={fieldErrors}
            isSaving={createMutation.isPending}
            seasons={seasons}
            stadiums={stadiums}
            teams={teams}
            tournaments={tournaments}
            referees={referees}
            onCancel={closeForm}
            onSubmit={handleCreateMatch}
          />
        ) : null}

        <MatchesDataTable
          matches={filteredMatches}
          teams={teams}
          stadiums={stadiums}
          referees={referees}
          tournaments={tournaments}
        />
      </section>
    </div>
  );
}

export function WorkspaceMatchDetailPage() {
  const { token } = useAuth();
  const { matchId } = useParams();
  const safeToken = token ?? "";
  const numericMatchId = Number(matchId);
  const isValidMatchId = Number.isInteger(numericMatchId) && numericMatchId > 0;

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

  if (!isValidMatchId) {
    return (
      <div className="page-stack">
        <section className="notice notice-danger">
          <strong>Некорректный адрес матча.</strong>
          <Link to="/app/matches">Вернуться к списку</Link>
        </section>
      </div>
    );
  }

  const match = matchQuery.data;
  const seasons = seasonsQuery.data ?? [];
  const tournaments = tournamentsQuery.data ?? [];
  const teams = teamsQuery.data ?? [];
  const stadiums = stadiumsQuery.data ?? [];
  const referees = refereesQuery.data ?? [];
  const error =
    matchQuery.error ??
    seasonsQuery.error ??
    tournamentsQuery.error ??
    teamsQuery.error ??
    stadiumsQuery.error ??
    refereesQuery.error ??
    null;

  if (!match) {
    return (
      <div className="page-stack">
        <Link className="back-link" to="/app/matches">
          ← К списку матчей
        </Link>
        {error instanceof Error ? (
          <section className="notice notice-danger">
            <strong>Не удалось загрузить матч.</strong>
            <span>{error.message}</span>
          </section>
        ) : (
          <section className="panel">
            <p className="eyebrow">Loading</p>
            <h2>Загружаем матч</h2>
          </section>
        )}
      </div>
    );
  }

  const isFinished = match.status === "finished";

  return (
    <div className="page-stack">
      <Link className="back-link" to="/app/matches">
        ← К списку матчей
      </Link>

      {error instanceof Error ? (
        <section className="notice notice-danger">
          <strong>Часть данных матча не загрузилась.</strong>
          <span>{error.message}</span>
        </section>
      ) : null}

      <section className="panel match-detail-head">
        <div>
          <p className="eyebrow">
            {getTournamentName(match.tournament_id, tournaments)}
          </p>
          <h2>{renderMatchPair(match, teams)}</h2>
          <div className="match-scoreline">{renderScore(match)}</div>
        </div>
        <span className={`status status-${match.status}`}>{match.status}</span>
      </section>

      <div className="split-grid">
        <section className="panel">
          <p className="eyebrow">Summary</p>
          <h2>Основная информация</h2>
          <div className="meta-grid">
            <span>Сезон: {getSeasonName(match.season_id, seasons)}</span>
            <span>Дата: {formatDateTime(match.match_datetime)}</span>
            <span>Стадион: {getStadiumName(match.stadium_id, stadiums)}</span>
            <span>Судья: {getRefereeName(match.referee_id, referees)}</span>
            <span>Раунд: {match.round_number}</span>
            <span>Стадия: {match.stage ?? "нет"}</span>
            <span>Билет: {match.ticket_price ?? "нет"}</span>
            <span>Продано: {match.ticket_sold}</span>
          </div>
          {isFinished ? (
            <p className="warning-text">
              Матч завершен. Обычное редактирование, перенос, судья и цена
              билета заблокированы правилами турнира.
            </p>
          ) : null}
        </section>

        <section className="panel">
          <p className="eyebrow">Actions</p>
          <h2>Действия матча</h2>
          <div className="action-list">
            <button className="button button-neutral" type="button" disabled>
              Перенести
            </button>
            <button className="button button-neutral" type="button" disabled>
              Назначить судью
            </button>
            <button className="button button-neutral" type="button" disabled>
              Изменить цену
            </button>
            <button className="button button-primary" type="button" disabled>
              Генерировать протокол
            </button>
          </div>
          <p className="muted">
            Кнопки подключатся отдельным слоем, чтобы не смешивать чтение и
            мутации.
          </p>
        </section>
      </div>

      <div className="split-grid">
        <section className="panel">
          <p className="eyebrow">Lineups</p>
          <h2>Составы</h2>
          <p className="muted">
            Здесь будет ручной и автоматический lineup workflow для обеих
            команд.
          </p>
        </section>

        <section className="panel">
          <p className="eyebrow">Protocol</p>
          <h2>Протокол</h2>
          <p className="muted">
            Здесь будет timeline событий, finish workflow и generate protocol.
          </p>
        </section>
      </div>
    </div>
  );
}

export function WorkspacePlaceholder({ title }: { title: string }) {
  return (
    <div className="page-stack">
      <section className="panel">
        <p className="eyebrow">Раздел</p>
        <h2>{title}</h2>
        <p className="muted">
          Этот раздел будет подключен следующим небольшим слоем. Основные данные
          рабочей области уже доступны на главной странице.
        </p>
      </section>
    </div>
  );
}

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
      <div>
        <p className="eyebrow">Create</p>
        <h2>New match</h2>
      </div>

      {error ? <div className="form-error">{error}</div> : null}

      <div className="form-grid">
        <label className="field">
          <span>Season</span>
          <select
            onChange={(event) => updateSeason(event.target.value)}
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
          <span>Tournament</span>
          <select
            onChange={(event) =>
              setValues((current) => ({
                ...current,
                tournament_id: event.target.value,
              }))
            }
            required
            value={values.tournament_id}
          >
            {filteredTournaments.map((tournament) => (
              <option key={tournament.id} value={tournament.id}>
                {tournament.name}
              </option>
            ))}
          </select>
          {fieldErrors.tournament_id ? (
            <small className="field-error">{fieldErrors.tournament_id}</small>
          ) : null}
        </label>

        <label className="field">
          <span>Home team</span>
          <select
            onChange={(event) => updateHomeTeam(event.target.value)}
            required
            value={values.home_team_id}
          >
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

        <label className="field">
          <span>Away team</span>
          <select
            onChange={(event) =>
              setValues((current) => ({
                ...current,
                away_team_id: event.target.value,
              }))
            }
            required
            value={values.away_team_id}
          >
            {awayTeamOptions.map((team) => (
              <option key={team.id} value={team.id}>
                {team.name}
              </option>
            ))}
          </select>
          {fieldErrors.away_team_id ? (
            <small className="field-error">{fieldErrors.away_team_id}</small>
          ) : null}
        </label>

        <label className="field">
          <span>Stadium</span>
          <select
            onChange={(event) =>
              setValues((current) => ({ ...current, stadium_id: event.target.value }))
            }
            required
            value={values.stadium_id}
          >
            {stadiums.map((stadium) => (
              <option key={stadium.id} value={stadium.id}>
                {stadium.name}
              </option>
            ))}
          </select>
          {fieldErrors.stadium_id ? (
            <small className="field-error">{fieldErrors.stadium_id}</small>
          ) : null}
        </label>

        <label className="field">
          <span>Referee</span>
          <select
            onChange={(event) =>
              setValues((current) => ({ ...current, referee_id: event.target.value }))
            }
            value={values.referee_id}
          >
            <option value="">Не назначен</option>
            {referees.map((referee) => (
              <option key={referee.id} value={referee.id}>
                {referee.full_name}
              </option>
            ))}
          </select>
          {fieldErrors.referee_id ? (
            <small className="field-error">{fieldErrors.referee_id}</small>
          ) : null}
        </label>

        <label className="field">
          <span>Date</span>
          <input
            onChange={(event) =>
              setValues((current) => ({ ...current, match_date: event.target.value }))
            }
            required
            type="date"
            value={values.match_date}
          />
          {fieldErrors.match_datetime ? (
            <small className="field-error">{fieldErrors.match_datetime}</small>
          ) : null}
        </label>

        <label className="field">
          <span>Time</span>
          <input
            onChange={(event) =>
              setValues((current) => ({ ...current, match_time: event.target.value }))
            }
            required
            type="time"
            value={values.match_time}
          />
        </label>

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
          {fieldErrors.round_number ? (
            <small className="field-error">{fieldErrors.round_number}</small>
          ) : null}
        </label>

        <label className="field">
          <span>Cup stage</span>
          <select
            disabled={!isCup}
            onChange={(event) =>
              setValues((current) => ({ ...current, stage: event.target.value }))
            }
            value={values.stage}
          >
            <option value="">None</option>
            <option value="semifinal">semifinal</option>
            <option value="final">final</option>
          </select>
          {fieldErrors.stage ? (
            <small className="field-error">{fieldErrors.stage}</small>
          ) : null}
        </label>
      </div>

      <div className="form-actions">
        <button
          className="button button-primary"
          disabled={
            isSaving ||
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

function TeamForm({
  initialValues,
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
      address: emptyStringToNull(values.address),
      manager_name: emptyStringToNull(values.manager_name),
      emblem_url: emptyStringToNull(values.emblem_url),
      previous_season_place: values.previous_season_place
        ? Number(values.previous_season_place)
        : null,
    });
  }

  return (
    <form className="inline-form" onSubmit={handleSubmit}>
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
          <span>City</span>
          <input
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
          <span>Address</span>
          <input
            onChange={(event) =>
              setValues((current) => ({ ...current, address: event.target.value }))
            }
            value={values.address}
          />
          {fieldErrors.address ? (
            <small className="field-error">{fieldErrors.address}</small>
          ) : null}
        </label>
        <label className="field">
          <span>Manager</span>
          <input
            onChange={(event) =>
              setValues((current) => ({
                ...current,
                manager_name: event.target.value,
              }))
            }
            value={values.manager_name}
          />
          {fieldErrors.manager_name ? (
            <small className="field-error">{fieldErrors.manager_name}</small>
          ) : null}
        </label>
        <label className="field">
          <span>Emblem URL</span>
          <input
            onChange={(event) =>
              setValues((current) => ({
                ...current,
                emblem_url: event.target.value,
              }))
            }
            value={values.emblem_url}
          />
          {fieldErrors.emblem_url ? (
            <small className="field-error">{fieldErrors.emblem_url}</small>
          ) : null}
        </label>
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
        <button className="button button-ghost" type="button" onClick={onCancel}>
          Cancel
        </button>
      </div>
    </form>
  );
}

function getDefaultTeamValues(): TeamFormValues {
  return {
    name: "",
    city: "",
    address: "",
    manager_name: "",
    emblem_url: "",
    previous_season_place: "",
  };
}

function emptyStringToNull(value: string) {
  const trimmed = value.trim();
  return trimmed ? trimmed : null;
}

function MetricCard({ label, value }: { label: string; value: number | string }) {
  return (
    <section className="panel metric-card">
      <span>{label}</span>
      <strong>{value}</strong>
    </section>
  );
}

function getHomeStadiumName(teamId: number, stadiums: Stadium[]) {
  return (
    stadiums.find((stadium) => stadium.home_team_id === teamId)?.name ??
    "не указан"
  );
}

function getTeamById(teamId: number, teams: Team[]) {
  return teams.find((team) => team.id === teamId);
}

function PlayersTable({
  isLoading,
  players,
}: {
  isLoading: boolean;
  players: Player[];
}) {
  return (
    <DataTable
      rows={players}
      getRowKey={(player) => player.id}
      emptyText="Игроков пока нет"
      isLoading={isLoading}
      columns={[
        { key: "number", header: "#", render: (player) => player.number },
        { key: "name", header: "Игрок", render: (player) => player.full_name },
        { key: "position", header: "Позиция", render: (player) => player.position },
        { key: "age", header: "Возраст", render: (player) => player.age ?? "нет" },
      ]}
    />
  );
}

function TeamMatchesTable({
  isLoading,
  matches,
  team,
  teams,
}: {
  isLoading: boolean;
  matches: Match[];
  team: Team;
  teams: Team[];
}) {
  return (
    <DataTable
      rows={matches}
      getRowKey={(match) => match.id}
      emptyText="Матчей команды пока нет"
      isLoading={isLoading}
      columns={[
        {
          key: "date",
          header: "Дата",
          render: (match) => formatDateTime(match.match_datetime),
        },
        {
          key: "side",
          header: "Роль",
          render: (match) =>
            match.home_team_id === team.id ? "дома" : "в гостях",
        },
        {
          key: "opponent",
          header: "Соперник",
          render: (match) => {
            const opponentId =
              match.home_team_id === team.id
                ? match.away_team_id
                : match.home_team_id;
            return (
              <TeamInline
                fallbackName={`Team ${opponentId}`}
                team={getTeamById(opponentId, teams)}
              />
            );
          },
        },
        {
          key: "status",
          header: "Статус",
          render: (match) => (
            <span className={`status status-${match.status}`}>{match.status}</span>
          ),
        },
        {
          key: "score",
          header: "Счет",
          render: (match) =>
            match.status === "finished"
              ? `${match.home_score ?? 0}:${match.away_score ?? 0}`
              : "не сыгран",
        },
        {
          key: "ticket",
          header: "Билет",
          render: (match) => match.ticket_price ?? "нет",
        },
        {
          key: "actions",
          header: "Действия",
          render: (match) => (
            <Link className="button button-ghost" to={`/app/matches/${match.id}`}>
              Открыть
            </Link>
          ),
        },
      ]}
    />
  );
}

function MatchesDataTable({
  matches,
  teams,
  stadiums,
  referees,
  tournaments,
}: {
  matches: Match[];
  teams: Team[];
  stadiums: Stadium[];
  referees: Referee[];
  tournaments: Tournament[];
}) {
  return (
    <DataTable
      rows={matches}
      getRowKey={(match) => match.id}
      emptyText="Матчи не найдены"
      columns={[
        {
          key: "date",
          header: "Дата",
          render: (match) => formatDateTime(match.match_datetime),
        },
        {
          key: "tournament",
          header: "Турнир",
          render: (match) => getTournamentName(match.tournament_id, tournaments),
        },
        {
          key: "teams",
          header: "Матч",
          render: (match) => (
            <Link to={`/app/matches/${match.id}`}>
              {renderMatchPair(match, teams)}
            </Link>
          ),
        },
        {
          key: "status",
          header: "Статус",
          render: (match) => (
            <span className={`status status-${match.status}`}>{match.status}</span>
          ),
        },
        { key: "score", header: "Счет", render: renderScore },
        {
          key: "stadium",
          header: "Стадион",
          render: (match) => getStadiumName(match.stadium_id, stadiums),
        },
        {
          key: "referee",
          header: "Судья",
          render: (match) => getRefereeName(match.referee_id, referees),
        },
        {
          key: "ticket",
          header: "Билет",
          render: (match) => match.ticket_price ?? "нет",
        },
        {
          key: "actions",
          header: "Действия",
          render: (match) => (
            <Link className="button button-ghost" to={`/app/matches/${match.id}`}>
              Открыть
            </Link>
          ),
        },
      ]}
    />
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
    : "не сыгран";
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
    return "не назначен";
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
