import { useState, type FormEvent } from "react";
import { Link, useLocation, useNavigate } from "react-router-dom";
import { useAuth } from "../features/auth/AuthProvider";
import type { ApiError } from "../shared/api/client";

type AuthMode = "login" | "register";

type LocationState = {
  from?: {
    pathname?: string;
  };
};

export function AuthPage({ mode }: { mode: AuthMode }) {
  const navigate = useNavigate();
  const location = useLocation();
  const { loginUser, registerUser } = useAuth();
  const [nickname, setNickname] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [fieldErrors, setFieldErrors] = useState<Record<string, string>>({});
  const [isSubmitting, setIsSubmitting] = useState(false);

  const targetPath =
    (location.state as LocationState | null)?.from?.pathname ?? "/app";

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError(null);
    setFieldErrors({});
    setIsSubmitting(true);

    try {
      if (mode === "login") {
        await loginUser({ email, password });
      } else {
        await registerUser({ nickname, email, password });
      }
      navigate(targetPath, { replace: true });
    } catch (caughtError) {
      const apiError = caughtError as ApiError;
      setError(apiError.message);
      setFieldErrors(apiError.fieldErrors ?? {});
    } finally {
      setIsSubmitting(false);
    }
  }

  const isPublicPreview = import.meta.env.VITE_USE_HASH_ROUTER === "true";

  if (isPublicPreview) {
    return (
      <div className="auth-layout">
        <div className="panel auth-panel">
          <p className="eyebrow">{mode === "login" ? "Login" : "Register"}</p>
          <h2>{mode === "login" ? "Вход" : "Регистрация"}</h2>
          <div className="notice notice-warning">
            <strong>Это публичный просмотр.</strong>
            <span>
              Регистрация и вход в этом режиме недоступны. Откройте рабочую
              версию приложения, чтобы перейти в кабинет организатора.
            </span>
          </div>
          <Link to="/" className="button button-ghost">
            Назад к просмотру
          </Link>
        </div>
      </div>
    );
  }

  return (
    <div className="auth-layout">
      <form className="panel auth-panel" onSubmit={handleSubmit}>
        <p className="eyebrow">{mode === "login" ? "Login" : "Register"}</p>
        <h2>{mode === "login" ? "Вход" : "Регистрация"}</h2>
        <p className="muted">
          После входа откроется защищенный кабинет с данными текущего
          организатора.
        </p>

        {error ? <div className="form-error">{error}</div> : null}

        {mode === "register" ? (
          <label className="field">
            <span>Никнейм</span>
            <input
              autoComplete="nickname"
              minLength={3}
              name="nickname"
              onChange={(event) => setNickname(event.target.value)}
              required
              value={nickname}
            />
            {fieldErrors.nickname ? (
              <small className="field-error">{fieldErrors.nickname}</small>
            ) : null}
          </label>
        ) : null}

        <label className="field">
          <span>Email</span>
          <input
            autoComplete="email"
            name="email"
            onChange={(event) => setEmail(event.target.value)}
            required
            type="email"
            value={email}
          />
          {fieldErrors.email ? (
            <small className="field-error">{fieldErrors.email}</small>
          ) : null}
        </label>

        <label className="field">
          <span>Пароль</span>
          <input
            autoComplete={mode === "login" ? "current-password" : "new-password"}
            minLength={mode === "register" ? 8 : 1}
            name="password"
            onChange={(event) => setPassword(event.target.value)}
            required
            type="password"
            value={password}
          />
          {fieldErrors.password ? (
            <small className="field-error">{fieldErrors.password}</small>
          ) : null}
        </label>

        <button className="button button-primary" disabled={isSubmitting} type="submit">
          {isSubmitting
            ? "Отправляем..."
            : mode === "login"
              ? "Войти"
              : "Зарегистрироваться"}
        </button>

        <Link to={mode === "login" ? "/register" : "/login"} className="auth-link">
          {mode === "login" ? "Создать аккаунт" : "Уже есть аккаунт"}
        </Link>
      </form>
    </div>
  );
}
