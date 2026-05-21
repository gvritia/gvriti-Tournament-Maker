import {
  Building2,
  CalendarDays,
  CalendarRange,
  ClipboardList,
  ListTree,
  LogIn,
  LogOut,
  Menu,
  ShieldCheck,
  Trophy,
  UserCheck,
  UsersRound,
  X,
} from "lucide-react";
import { useState } from "react";
import { Link, NavLink, Outlet, useNavigate } from "react-router-dom";
import { useAuth } from "../features/auth/AuthProvider";

type ShellMode = "preview" | "workspace";

type NavItem = {
  to: string;
  label: string;
  icon: typeof ClipboardList;
  end?: boolean;
};

const previewNavItems: NavItem[] = [
  { to: "/", label: "Обзор", icon: ClipboardList, end: true },
  { to: "/teams", label: "Команды", icon: UsersRound },
  { to: "/matches", label: "Матчи", icon: CalendarDays },
  { to: "/championship", label: "Чемпионат", icon: Trophy },
  { to: "/cup", label: "Кубок", icon: ShieldCheck },
];

const workspaceNavItems: NavItem[] = [
  { to: "/app", label: "Обзор", icon: ClipboardList, end: true },
  { to: "/app/seasons", label: "Сезоны", icon: CalendarRange },
  { to: "/app/teams", label: "Команды", icon: UsersRound },
  { to: "/app/players", label: "Игроки", icon: UsersRound },
  { to: "/app/stadiums", label: "Стадионы", icon: Building2 },
  { to: "/app/referees", label: "Судьи", icon: UserCheck },
  { to: "/app/tournaments", label: "Турниры", icon: ListTree },
  { to: "/app/matches", label: "Матчи", icon: CalendarDays },
  { to: "/app/championship", label: "Чемпионат", icon: Trophy },
  { to: "/app/cup", label: "Кубок", icon: ShieldCheck },
];

export function AppShell({ mode }: { mode: ShellMode }) {
  const [isOpen, setIsOpen] = useState(false);
  const navigate = useNavigate();
  const { user, logout } = useAuth();
  const isWorkspace = mode === "workspace";
  const navItems = isWorkspace ? workspaceNavItems : previewNavItems;

  function handleLogout() {
    logout();
    navigate("/");
  }

  return (
    <div className="app-shell">
      <aside className={`sidebar ${isOpen ? "sidebar-open" : ""}`}>
        <div className="sidebar-head">
          <Link
            to={isWorkspace ? "/app" : "/"}
            className="brand"
            onClick={() => setIsOpen(false)}
          >
            <span className="brand-mark">TM</span>
            <span>
              <strong>Tournament Maker</strong>
              <small>{isWorkspace ? "рабочая область" : "просмотр"}</small>
            </span>
          </Link>
          <button
            className="icon-button mobile-only"
            type="button"
            aria-label="Закрыть меню"
            onClick={() => setIsOpen(false)}
          >
            <X size={18} />
          </button>
        </div>

        <nav className="sidebar-nav" aria-label="Main navigation">
          {navItems.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              end={item.end}
              className={({ isActive }) =>
                `nav-link ${isActive ? "nav-link-active" : ""}`
              }
              onClick={() => setIsOpen(false)}
            >
              <item.icon size={18} />
              <span>{item.label}</span>
            </NavLink>
          ))}
        </nav>
      </aside>

      {isOpen ? (
        <button
          className="sidebar-backdrop"
          type="button"
          aria-label="Закрыть меню"
          onClick={() => setIsOpen(false)}
        />
      ) : null}

      <div className="workspace">
        <header className="topbar">
          <button
            className="icon-button mobile-only"
            type="button"
            aria-label="Открыть меню"
            onClick={() => setIsOpen(true)}
          >
            <Menu size={20} />
          </button>
          <div>
            <div className="eyebrow">
              {isWorkspace ? "Рабочая область" : "Открытый просмотр"}
            </div>
            <h1>Рабочий кабинет организатора</h1>
          </div>
          <div className="topbar-actions">
            {isWorkspace ? (
              <>
                <span className="mode-chip">{user?.nickname ?? "Организатор"}</span>
                <button
                  className="button button-ghost"
                  type="button"
                  onClick={handleLogout}
                >
                  <LogOut size={16} />
                  Выйти
                </button>
              </>
            ) : (
              <>
                <span className="mode-chip">Только просмотр</span>
                <Link className="button button-ghost" to="/login">
                  <LogIn size={16} />
                  Войти
                </Link>
              </>
            )}
          </div>
        </header>

        <main className="content">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
