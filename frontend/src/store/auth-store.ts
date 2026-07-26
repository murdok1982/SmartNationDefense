import { create } from "zustand";
import {
  login as apiLogin,
  clearTokens,
  getAccessToken,
  getRefreshToken,
  refreshAccessToken,
  decodeJwtPayload,
} from "@/lib/api";

interface AuthState {
  username: string | null;
  clearance: string | null;
  isAuthenticated: boolean;
  hydrated: boolean;
  restore: () => Promise<void>;
  login: (username: string, password: string) => Promise<void>;
  logout: () => void;
}

function claimsFromToken(token: string): { username: string | null; clearance: string | null } {
  const payload = decodeJwtPayload(token);
  return {
    username: typeof payload?.username === "string" ? payload.username : null,
    clearance: typeof payload?.clearance === "string" ? payload.clearance : null,
  };
}

export const useAuthStore = create<AuthState>((set) => ({
  username: null,
  clearance: null,
  isAuthenticated: false,
  hydrated: false,

  restore: async () => {
    let token = getAccessToken();
    if (!token && getRefreshToken()) {
      token = await refreshAccessToken();
    }
    if (token) {
      const { username, clearance } = claimsFromToken(token);
      set({ isAuthenticated: true, username, clearance, hydrated: true });
    } else {
      set({ isAuthenticated: false, username: null, clearance: null, hydrated: true });
    }
  },

  login: async (username, password) => {
    const tokens = await apiLogin(username, password);
    const claims = claimsFromToken(tokens.access_token);
    set({
      isAuthenticated: true,
      username: claims.username ?? username,
      clearance: claims.clearance,
    });
  },

  logout: () => {
    clearTokens();
    set({ isAuthenticated: false, username: null, clearance: null });
  },
}));
