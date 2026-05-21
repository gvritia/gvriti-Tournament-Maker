import {
  Building2,
  CalendarDays,
  CalendarRange,
  ClipboardList,
  Languages,
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
import { useLanguage, type Language } from "../features/i18n/LanguageProvider";

type ShellMode = "preview" | "workspace";

type NavItem = {
  to: string;
  labelKey: NavLabelKey;
  icon: typeof ClipboardList;
  end?: boolean;
};

const previewNavItems: NavItem[] = [
  { to: "/", labelKey: "overview", icon: ClipboardList, end: true },
  { to: "/teams", labelKey: "teams", icon: UsersRound },
  { to: "/matches", labelKey: "matches", icon: CalendarDays },
  { to: "/championship", labelKey: "championship", icon: Trophy },
  { to: "/cup", labelKey: "cup", icon: ShieldCheck },
];

const workspaceNavItems: NavItem[] = [
  { to: "/app", labelKey: "overview", icon: ClipboardList, end: true },
  { to: "/app/seasons", labelKey: "seasons", icon: CalendarRange },
  { to: "/app/teams", labelKey: "teams", icon: UsersRound },
  { to: "/app/players", labelKey: "players", icon: UsersRound },
  { to: "/app/stadiums", labelKey: "stadiums", icon: Building2 },
  { to: "/app/referees", labelKey: "referees", icon: UserCheck },
  { to: "/app/tournaments", labelKey: "tournaments", icon: ListTree },
  { to: "/app/matches", labelKey: "matches", icon: CalendarDays },
  { to: "/app/championship", labelKey: "championship", icon: Trophy },
  { to: "/app/cup", labelKey: "cup", icon: ShieldCheck },
];

type NavLabelKey =
  | "overview"
  | "seasons"
  | "teams"
  | "players"
  | "stadiums"
  | "referees"
  | "tournaments"
  | "matches"
  | "championship"
  | "cup";

const shellText: Record<
  Language,
  {
    nav: Record<NavLabelKey, string>;
    preview: string;
    workspace: string;
    closeMenu: string;
    openMenu: string;
    mainNavigation: string;
    organizerCabinet: string;
    organizer: string;
    readonly: string;
    logout: string;
    login: string;
    languageLabel: string;
  }
> = {
  ru: {
    nav: {
      overview: "Обзор",
      seasons: "Сезоны",
      teams: "Команды",
      players: "Игроки",
      stadiums: "Стадионы",
      referees: "Судьи",
      tournaments: "Турниры",
      matches: "Матчи",
      championship: "Чемпионат",
      cup: "Кубок",
    },
    preview: "просмотр",
    workspace: "рабочая область",
    closeMenu: "Закрыть меню",
    openMenu: "Открыть меню",
    mainNavigation: "Основная навигация",
    organizerCabinet: "Рабочий кабинет организатора",
    organizer: "Организатор",
    readonly: "Только просмотр",
    logout: "Выйти",
    login: "Войти",
    languageLabel: "Переключить язык",
  },
  en: {
    nav: {
      overview: "Overview",
      seasons: "Seasons",
      teams: "Teams",
      players: "Players",
      stadiums: "Stadiums",
      referees: "Referees",
      tournaments: "Tournaments",
      matches: "Matches",
      championship: "Championship",
      cup: "Cup",
    },
    preview: "preview",
    workspace: "workspace",
    closeMenu: "Close menu",
    openMenu: "Open menu",
    mainNavigation: "Main navigation",
    organizerCabinet: "Organizer workspace",
    organizer: "Organizer",
    readonly: "Read only",
    logout: "Log out",
    login: "Log in",
    languageLabel: "Switch language",
  },
};

export function AppShell({ mode }: { mode: ShellMode }) {
  const [isOpen, setIsOpen] = useState(false);
  const navigate = useNavigate();
  const { user, logout } = useAuth();
  const { language, toggleLanguage } = useLanguage();
  const text = shellText[language];
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
              <small>{isWorkspace ? text.workspace : text.preview}</small>
            </span>
          </Link>
          <button
            className="icon-button mobile-only"
            type="button"
            aria-label={text.closeMenu}
            onClick={() => setIsOpen(false)}
          >
            <X size={18} />
          </button>
        </div>

        <nav className="sidebar-nav" aria-label={text.mainNavigation}>
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
              <span>{text.nav[item.labelKey]}</span>
            </NavLink>
          ))}
        </nav>
      </aside>

      {isOpen ? (
        <button
          className="sidebar-backdrop"
          type="button"
          aria-label={text.closeMenu}
          onClick={() => setIsOpen(false)}
        />
      ) : null}

      <div className="workspace">
        <header className="topbar">
          <button
            className="icon-button mobile-only"
            type="button"
            aria-label={text.openMenu}
            onClick={() => setIsOpen(true)}
          >
            <Menu size={20} />
          </button>
          <div>
            <div className="eyebrow">
              {isWorkspace ? text.workspace : text.preview}
            </div>
            <h1>{text.organizerCabinet}</h1>
          </div>
          <div className="topbar-actions">
            <button
              className="button button-ghost language-toggle"
              type="button"
              aria-label={text.languageLabel}
              onClick={toggleLanguage}
            >
              <Languages size={16} />
              {language === "ru" ? "RU" : "EN"}
            </button>
            {isWorkspace ? (
              <>
                <span className="mode-chip">{user?.nickname ?? text.organizer}</span>
                <button
                  className="button button-ghost"
                  type="button"
                  onClick={handleLogout}
                >
                  <LogOut size={16} />
                  {text.logout}
                </button>
              </>
            ) : (
              <>
                <span className="mode-chip">{text.readonly}</span>
                <Link className="button button-ghost" to="/login">
                  <LogIn size={16} />
                  {text.login}
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
