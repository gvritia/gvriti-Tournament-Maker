import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { fetchCurrentUser, login, register } from "../../shared/api/endpoints";
import type { LoginPayload, RegisterPayload } from "../../shared/api/endpoints";
import type { User } from "../../shared/api/types";

const TOKEN_KEY = "tournament-maker-token";

// On a GitHub Pages public preview build there is no backend, so any
// JWT still sitting in localStorage from a local Docker session would
// only generate noisy 401 errors. We force the session to start empty
// in that mode; the AuthPage already shows a friendly notice instead
// of letting the user attempt to log in against the placeholder API.
const IS_PUBLIC_PREVIEW = import.meta.env.VITE_USE_HASH_ROUTER === "true";

type AuthContextValue = {
  token: string | null;
  user: User | null;
  userError: Error | null;
  isAuthenticated: boolean;
  isLoadingUser: boolean;
  loginUser: (payload: LoginPayload) => Promise<void>;
  registerUser: (payload: RegisterPayload) => Promise<void>;
  logout: () => void;
};

const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const queryClient = useQueryClient();
  const [token, setToken] = useState(() =>
    IS_PUBLIC_PREVIEW ? null : localStorage.getItem(TOKEN_KEY),
  );

  const clearSession = useCallback(() => {
    localStorage.removeItem(TOKEN_KEY);
    setToken(null);
    queryClient.clear();
  }, [queryClient]);

  const currentUserQuery = useQuery({
    queryKey: ["me"],
    queryFn: () => fetchCurrentUser(token ?? ""),
    enabled: Boolean(token),
    retry: false,
  });

  useEffect(() => {
    const status = (currentUserQuery.error as { status?: number } | null)?.status;
    if (status === 401) {
      clearSession();
    }
  }, [clearSession, currentUserQuery.error]);

  const loginUser = useCallback(
    async (payload: LoginPayload) => {
      const response = await login(payload);
      localStorage.setItem(TOKEN_KEY, response.access_token);
      setToken(response.access_token);
      await queryClient.invalidateQueries({ queryKey: ["me"] });
    },
    [queryClient],
  );

  const registerUser = useCallback(
    async (payload: RegisterPayload) => {
      await register(payload);
      await loginUser({ email: payload.email, password: payload.password });
    },
    [loginUser],
  );

  const logout = useCallback(() => {
    clearSession();
  }, [clearSession]);

  const value = useMemo<AuthContextValue>(
    () => ({
      token,
      user: currentUserQuery.data ?? null,
      userError: currentUserQuery.error,
      isAuthenticated: Boolean(token),
      isLoadingUser: currentUserQuery.isLoading,
      loginUser,
      registerUser,
      logout,
    }),
    [
      currentUserQuery.data,
      currentUserQuery.error,
      currentUserQuery.isLoading,
      loginUser,
      logout,
      registerUser,
      token,
    ],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth must be used inside AuthProvider");
  }
  return context;
}
