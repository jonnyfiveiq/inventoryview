import { useCallback } from "react";
import { useAuthStore } from "@/stores/auth";
import { login as apiLogin, revokeToken } from "@/api/auth";

export function useAuth() {
  const { token, isAuthenticated, username, login: storeLogin, logout: storeLogout, isTokenExpired } = useAuthStore();

  const login = useCallback(async (loginUsername: string, password: string) => {
    const session = await apiLogin({ username: loginUsername, password });
    storeLogin(session.token, session.expires_at, loginUsername);
  }, [storeLogin]);

  const logout = useCallback(async () => {
    if (token) {
      try {
        await revokeToken(token);
      } catch {
        // Token revocation failed, still log out locally
      }
    }
    storeLogout();
  }, [token, storeLogout]);

  return { isAuthenticated, username, token, isTokenExpired, login, logout };
}
