import { create } from "zustand";

interface AuthState {
  token: string | null;
  expiresAt: string | null;
  username: string | null;
  isAuthenticated: boolean;
  login: (token: string, expiresAt: string, username?: string) => void;
  logout: () => void;
  isTokenExpired: () => boolean;
}

export const useAuthStore = create<AuthState>((set, get) => ({
  token: sessionStorage.getItem("iv_token"),
  expiresAt: sessionStorage.getItem("iv_expires_at"),
  username: sessionStorage.getItem("iv_username"),
  isAuthenticated: !!sessionStorage.getItem("iv_token"),

  login: (token, expiresAt, username) => {
    sessionStorage.setItem("iv_token", token);
    sessionStorage.setItem("iv_expires_at", expiresAt);
    if (username) sessionStorage.setItem("iv_username", username);
    set({ token, expiresAt, username: username ?? null, isAuthenticated: true });
  },

  logout: () => {
    sessionStorage.removeItem("iv_token");
    sessionStorage.removeItem("iv_expires_at");
    sessionStorage.removeItem("iv_username");
    set({ token: null, expiresAt: null, username: null, isAuthenticated: false });
  },

  isTokenExpired: () => {
    const expiresAt = get().expiresAt;
    if (!expiresAt) return true;
    return new Date(expiresAt) <= new Date();
  },
}));
