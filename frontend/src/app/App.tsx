import {
  createBrowserRouter,
  createHashRouter,
  Navigate,
  RouterProvider,
} from "react-router-dom";
import { AppShell } from "../components/AppShell";
import { AuthProvider } from "../features/auth/AuthProvider";
import { ProtectedRoute } from "../features/auth/ProtectedRoute";
import { LanguageProvider } from "../features/i18n/LanguageProvider";
import { AuthPage } from "../pages/AuthPage";
import {
  ChampionshipPage,
  CupPage,
  MatchDetailPage,
  MatchesPage,
  PreviewDashboard,
  TeamDetailPage,
  TeamsPage,
} from "../pages/PreviewPages";
import {
  WorkspaceRefereesPage,
  WorkspaceSeasonsPage,
  WorkspaceStadiumsPage,
} from "../pages/WorkspaceCatalogPages";
import {
  WorkspaceDashboard,
  WorkspacePlaceholder,
  WorkspaceTeamDetailPage,
} from "../pages/WorkspacePages";
import { WorkspaceChampionshipPage } from "../pages/WorkspaceChampionshipPage";
import { WorkspaceCupPage } from "../pages/WorkspaceCupPage";
import { WorkspaceMatchDetailActionsPage } from "../pages/WorkspaceMatchDetailActionsPage";
import { WorkspaceMatchesCrudPage } from "../pages/WorkspaceMatchesCrudPage";
import { WorkspacePlayersCrudPage } from "../pages/WorkspacePlayersCrudPage";
import { WorkspaceTeamsCrudPage } from "../pages/WorkspaceTeamsCrudPage";
import { WorkspaceTournamentsCrudPage } from "../pages/WorkspaceTournamentsCrudPage";

// GitHub Pages hosts the site under a subpath and cannot serve unknown
// routes. Hash routing keeps every deep link reachable on Pages and adds no
// extra config. Locally and inside Docker we still use a normal browser
// router with the configured `base` from index.html.
const useHashRouter = import.meta.env.VITE_USE_HASH_ROUTER === "true";
const createRouter = useHashRouter ? createHashRouter : createBrowserRouter;

const router = createRouter([
  {
    path: "/",
    element: <AppShell mode="preview" />,
    children: [
      { index: true, element: <PreviewDashboard /> },
      { path: "teams", element: <TeamsPage /> },
      { path: "teams/:teamId", element: <TeamDetailPage /> },
      { path: "matches", element: <MatchesPage /> },
      { path: "matches/:matchId", element: <MatchDetailPage /> },
      { path: "championship", element: <ChampionshipPage /> },
      { path: "cup", element: <CupPage /> },
      { path: "login", element: <AuthPage mode="login" /> },
      { path: "register", element: <AuthPage mode="register" /> },
      { path: "*", element: <Navigate to="/" replace /> },
    ],
  },
  {
    path: "/app",
    element: <ProtectedRoute />,
    children: [
      {
        element: <AppShell mode="workspace" />,
        children: [
          { index: true, element: <WorkspaceDashboard /> },
          { path: "seasons", element: <WorkspaceSeasonsPage /> },
          { path: "teams", element: <WorkspaceTeamsCrudPage /> },
          { path: "teams/:teamId", element: <WorkspaceTeamDetailPage /> },
          { path: "players", element: <WorkspacePlayersCrudPage /> },
          { path: "stadiums", element: <WorkspaceStadiumsPage /> },
          { path: "referees", element: <WorkspaceRefereesPage /> },
          { path: "tournaments", element: <WorkspaceTournamentsCrudPage /> },
          { path: "matches", element: <WorkspaceMatchesCrudPage /> },
          { path: "matches/:matchId", element: <WorkspaceMatchDetailActionsPage /> },
          {
            path: "championship",
            element: <WorkspaceChampionshipPage />,
          },
          { path: "cup", element: <WorkspaceCupPage /> },
        ],
      },
    ],
  },
]);

export function App() {
  return (
    <LanguageProvider>
      <AuthProvider>
        <RouterProvider router={router} />
      </AuthProvider>
    </LanguageProvider>
  );
}


