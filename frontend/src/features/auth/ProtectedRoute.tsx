import { LogOut } from "lucide-react";
import { Navigate, Outlet, useLocation } from "react-router-dom";
import { useAuth } from "./AuthProvider";

export function ProtectedRoute() {
  const location = useLocation();
  const { isAuthenticated, isLoadingUser, logout, user, userError } = useAuth();

  if (!isAuthenticated) {
    return <Navigate to="/login" replace state={{ from: location }} />;
  }

  if (isLoadingUser) {
    return (
      <div className="content">
        <section className="panel">
          <p className="eyebrow">Loading</p>
          <h2>Проверяем сессию</h2>
        </section>
      </div>
    );
  }

  if (userError) {
    return (
      <div className="content">
        <section className="panel session-panel">
          <p className="eyebrow">Session</p>
          <h2>Не удалось подтвердить вход</h2>
          <p className="muted">{userError.message}</p>
          <button className="button button-ghost" type="button" onClick={logout}>
            <LogOut size={16} />
            Очистить сессию
          </button>
        </section>
      </div>
    );
  }

  if (!user) {
    return <Navigate to="/login" replace state={{ from: location }} />;
  }

  return <Outlet />;
}
