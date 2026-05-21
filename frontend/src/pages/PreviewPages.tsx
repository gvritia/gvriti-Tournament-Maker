import {
  CalendarPlus,
  CircleDollarSign,
  Play,
  RefreshCw,
  ShieldCheck,
  Trophy,
  WandSparkles,
} from "lucide-react";
import { Link, useParams } from "react-router-dom";
import { ActionPanel } from "../components/ActionPanel";
import { DataTable } from "../components/DataTable";
import { TeamProfile } from "../components/TeamProfile";
import {
  getTeamName,
  previewMatches,
  previewPlayers,
  previewStandings,
  previewTeams,
} from "../data/previewData";

export function PreviewDashboard() {
  const nearestMatch = previewMatches[0];

  return (
    <div className="page-stack">
      <section className="notice">
        <strong>Режим просмотра.</strong>
        <span>
          Можно открыть вкладки и оценить интерфейс. Все рабочие действия
          заблокированы до входа.
        </span>
      </section>

      <div className="kpi-grid">
        <MetricCard label="Команды" value={previewTeams.length} />
        <MetricCard label="Матчи" value={previewMatches.length} />
        <MetricCard label="Завершено" value={1} />
        <MetricCard label="Турниры" value={2} />
      </div>

      <div className="split-grid">
        <section className="panel">
          <p className="eyebrow">Nearest match</p>
          <h2>{getTeamName(nearestMatch.homeTeamId)} - {getTeamName(nearestMatch.awayTeamId)}</h2>
          <div className="match-scoreline">vs</div>
          <div className="meta-grid">
            <span>{nearestMatch.date}</span>
            <span>{nearestMatch.stadium}</span>
            <span>Судья: {nearestMatch.referee}</span>
            <span>Билет: {nearestMatch.ticketPrice}</span>
          </div>
        </section>

        <ActionPanel
          title="Быстрые действия"
          description="В preview все действия выключены. После входа здесь будут создание матча, генерация календаря и симуляция сезона."
          actions={[
            { label: "Создать матч", icon: <CalendarPlus size={16} />, tone: "primary" },
            { label: "Генерировать календарь", icon: <WandSparkles size={16} /> },
            { label: "Симулировать сезон", icon: <Play size={16} /> },
          ]}
        />
      </div>

      <section className="panel">
        <div className="section-head">
          <div>
            <p className="eyebrow">Standings preview</p>
            <h2>Таблица чемпионата</h2>
          </div>
          <Link className="button button-ghost" to="/championship">
            Открыть
          </Link>
        </div>
        <StandingsTable compact />
      </section>
    </div>
  );
}

export function TeamsPage() {
  return (
    <div className="page-stack">
      <PageIntro
        eyebrow="Teams"
        title="Команды"
        description="Будущий рабочий список клубов с фильтрами, эмблемами и переходом на страницу команды."
      />
      <section className="panel">
        <div className="section-head">
          <div className="filter-row">
            <input placeholder="Поиск по названию" disabled />
            <input placeholder="Город" disabled />
          </div>
          <button className="button button-primary" type="button" disabled>
            Создать команду
          </button>
        </div>
        <DataTable
          rows={previewTeams}
          getRowKey={(team) => team.id}
          columns={[
            {
              key: "team",
              header: "Команда",
              render: (team) => (
                <Link className="team-link" to={`/teams/${team.id}`}>
                  <span className="team-emblem">{team.shortName}</span>
                  {team.name}
                </Link>
              ),
            },
            { key: "city", header: "Город", render: (team) => team.city },
            { key: "stadium", header: "Стадион", render: (team) => team.stadiumName },
            {
              key: "place",
              header: "Прошлый сезон",
              render: (team) => team.previousSeasonPlace,
            },
            {
              key: "actions",
              header: "Действия",
              render: () => (
                <button className="button button-neutral" type="button" disabled>
                  Изменить
                </button>
              ),
            },
          ]}
        />
      </section>
    </div>
  );
}

export function TeamDetailPage() {
  const { teamId } = useParams();
  const team = previewTeams.find((item) => item.id === teamId) ?? previewTeams[0];
  const players = previewPlayers.filter((player) => player.teamId === team.id);
  const matches = previewMatches.filter(
    (match) => match.homeTeamId === team.id || match.awayTeamId === team.id,
  );

  return (
    <div className="page-stack">
      <Link className="back-link" to="/teams">
        ← К списку команд
      </Link>
      <TeamProfile
        team={team}
        players={players}
        matches={matches}
        getTeamName={getTeamName}
      />
    </div>
  );
}

export function MatchesPage() {
  return (
    <div className="page-stack">
      <PageIntro
        eyebrow="Matches"
        title="Матчи"
        description="Фильтры, цена билета и статус видны сразу. В preview действия заблокированы."
      />
      <section className="panel">
        <div className="section-head">
          <div className="filter-row">
            <select disabled>
              <option>Все турниры</option>
            </select>
            <select disabled>
              <option>Все статусы</option>
            </select>
            <input type="date" disabled />
          </div>
          <button className="button button-primary" type="button" disabled>
            Создать матч
          </button>
        </div>
        <MatchesTable />
      </section>
    </div>
  );
}

export function MatchDetailPage() {
  const { matchId } = useParams();
  const match = previewMatches.find((item) => item.id === matchId) ?? previewMatches[0];
  const isFinished = match.status === "finished";

  return (
    <div className="page-stack">
      <Link className="back-link" to="/matches">
        ← К списку матчей
      </Link>

      <section className="panel match-detail-head">
        <div>
          <p className="eyebrow">{match.tournament}</p>
          <h2>
            {getTeamName(match.homeTeamId)} - {getTeamName(match.awayTeamId)}
          </h2>
          <div className="match-scoreline">
            {isFinished ? `${match.homeScore}:${match.awayScore}` : "vs"}
          </div>
        </div>
        <span className={`status status-${match.status}`}>{match.statusLabel}</span>
      </section>

      <div className="split-grid">
        <section className="panel">
          <p className="eyebrow">Schedule / actions</p>
          <h2>Расписание и параметры</h2>
          <div className="meta-grid">
            <span>{match.date}</span>
            <span>{match.stadium}</span>
            <span>Судья: {match.referee}</span>
            <span>Билет: {match.ticketPrice}</span>
          </div>
          {isFinished ? (
            <p className="warning-text">
              Матч завершен. Обычное редактирование, перенос, судья и цена
              билета заблокированы.
            </p>
          ) : null}
        </section>

        <ActionPanel
          title="Действия матча"
          description="В рабочем режиме система проверит календарь, судью, составы и протокол. В режиме просмотра все кнопки выключены."
          actions={[
            { label: "Перенести", icon: <RefreshCw size={16} /> },
            { label: "Изменить цену", icon: <CircleDollarSign size={16} /> },
            { label: "Генерировать протокол", icon: <WandSparkles size={16} />, tone: "primary" },
          ]}
        />
      </div>

      <section className="panel">
        <p className="eyebrow">Lineups</p>
        <h2>Составы</h2>
        <p className="muted">
          Здесь появятся ручной список игроков и генерация состава с правилом
          ровно одного стартового goalkeeper.
        </p>
      </section>

      <section className="panel">
        <p className="eyebrow">Protocol</p>
        <h2>События матча</h2>
        <p className="muted">
          Timeline для голов, ассистов, сейвов и карточек будет подключен к
          рабочие данные после входа.
        </p>
      </section>
    </div>
  );
}

export function ChampionshipPage() {
  return (
    <div className="page-stack">
      <PageIntro
        eyebrow="Championship"
        title="Чемпионат"
        description="Календарь, турнирная таблица и статистика игроков с отдельными колонками показателей."
      />
      <ActionPanel
        title="Управление чемпионатом"
        description="Генерация полного расписания и симуляция сезона будут доступны после входа."
        actions={[
          { label: "Сгенерировать расписание", icon: <WandSparkles size={16} />, tone: "primary" },
          { label: "Симулировать сезон", icon: <Play size={16} /> },
        ]}
      />
      <section className="panel">
        <StandingsTable />
      </section>
    </div>
  );
}

export function CupPage() {
  return (
    <div className="page-stack">
      <PageIntro
        eyebrow="Cup"
        title="Кубок"
        description="Операционный bracket: полуфиналы, финал, чемпион и переходы к матчам."
      />
      <ActionPanel
        title="Генерация кубка"
        description="В рабочем режиме можно создать полуфиналы и финал по победителям."
        actions={[
          { label: "Сгенерировать полуфиналы", icon: <ShieldCheck size={16} />, tone: "primary" },
          { label: "Сгенерировать финал", icon: <Trophy size={16} /> },
        ]}
      />
      <section className="panel bracket">
        <BracketColumn title="Semifinals" matchIds={["m1", "m2"]} />
        <BracketColumn title="Final" matchIds={["m3"]} />
        <div className="bracket-card champion-card">
          <p className="eyebrow">Champion</p>
          <strong>Определится после финала</strong>
        </div>
      </section>
    </div>
  );
}

export function AuthPage({ mode }: { mode: "login" | "register" }) {
  return (
    <div className="auth-layout">
      <section className="panel auth-panel">
        <p className="eyebrow">{mode === "login" ? "Login" : "Register"}</p>
        <h2>{mode === "login" ? "Вход" : "Регистрация"}</h2>
        <p className="muted">
          Форма пока показывает будущий экран. Подключение JWT будет следующим
          отдельным шагом.
        </p>
        {mode === "register" ? <input placeholder="Nickname" disabled /> : null}
        <input placeholder="Email" disabled />
        <input placeholder="Password" type="password" disabled />
        <button className="button button-primary" type="button" disabled>
          {mode === "login" ? "Войти" : "Зарегистрироваться"}
        </button>
        <Link to={mode === "login" ? "/register" : "/login"} className="auth-link">
          {mode === "login" ? "Создать аккаунт" : "Уже есть аккаунт"}
        </Link>
      </section>
    </div>
  );
}

function MetricCard({ label, value }: { label: string; value: number }) {
  return (
    <section className="panel metric-card">
      <span>{label}</span>
      <strong>{value}</strong>
    </section>
  );
}

function PageIntro({
  eyebrow,
  title,
  description,
}: {
  eyebrow: string;
  title: string;
  description: string;
}) {
  return (
    <section className="page-intro">
      <p className="eyebrow">{eyebrow}</p>
      <h2>{title}</h2>
      <p className="muted">{description}</p>
    </section>
  );
}

function MatchesTable() {
  return (
    <DataTable
      rows={previewMatches}
      getRowKey={(match) => match.id}
      columns={[
        { key: "date", header: "Дата", render: (match) => match.date },
        { key: "tournament", header: "Турнир", render: (match) => match.tournament },
        {
          key: "teams",
          header: "Матч",
          render: (match) => (
            <Link to={`/matches/${match.id}`}>
              {getTeamName(match.homeTeamId)} - {getTeamName(match.awayTeamId)}
            </Link>
          ),
        },
        {
          key: "status",
          header: "Статус",
          render: (match) => (
            <span className={`status status-${match.status}`}>{match.statusLabel}</span>
          ),
        },
        {
          key: "score",
          header: "Счет",
          render: (match) =>
            match.status === "finished"
              ? `${match.homeScore}:${match.awayScore}`
              : "не сыгран",
        },
        { key: "stadium", header: "Стадион", render: (match) => match.stadium },
        { key: "referee", header: "Судья", render: (match) => match.referee },
        { key: "price", header: "Билет", render: (match) => match.ticketPrice },
        {
          key: "actions",
          header: "Действия",
          render: () => (
            <button className="button button-neutral" type="button" disabled>
              Изменить
            </button>
          ),
        },
      ]}
    />
  );
}

function StandingsTable({ compact = false }: { compact?: boolean }) {
  return (
    <DataTable
      rows={previewStandings}
      getRowKey={(row) => row.teamId}
      columns={[
        { key: "place", header: "#", render: (row) => row.place },
        { key: "team", header: "Команда", render: (row) => getTeamName(row.teamId) },
        { key: "played", header: "И", render: (row) => row.played },
        ...(compact
          ? [
              { key: "gd", header: "+/-", render: (row: (typeof previewStandings)[number]) => row.goalDifference },
              { key: "points", header: "О", render: (row: (typeof previewStandings)[number]) => row.points },
            ]
          : [
              { key: "wins", header: "В", render: (row: (typeof previewStandings)[number]) => row.wins },
              { key: "draws", header: "Н", render: (row: (typeof previewStandings)[number]) => row.draws },
              { key: "losses", header: "П", render: (row: (typeof previewStandings)[number]) => row.losses },
              { key: "gs", header: "ЗГ", render: (row: (typeof previewStandings)[number]) => row.goalsScored },
              { key: "gc", header: "ПГ", render: (row: (typeof previewStandings)[number]) => row.goalsConceded },
              { key: "gd", header: "+/-", render: (row: (typeof previewStandings)[number]) => row.goalDifference },
              { key: "points", header: "О", render: (row: (typeof previewStandings)[number]) => row.points },
            ]),
      ]}
    />
  );
}

function BracketColumn({ title, matchIds }: { title: string; matchIds: string[] }) {
  return (
    <div className="bracket-column">
      <p className="eyebrow">{title}</p>
      {matchIds.map((matchId) => {
        const match = previewMatches.find((item) => item.id === matchId) ?? previewMatches[0];
        return (
          <Link className="bracket-card" to={`/matches/${match.id}`} key={match.id}>
            <span>{match.tournament}</span>
            <strong>{getTeamName(match.homeTeamId)}</strong>
            <strong>{getTeamName(match.awayTeamId)}</strong>
            <small>{match.statusLabel}</small>
          </Link>
        );
      })}
    </div>
  );
}
