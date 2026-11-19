/**
 * frontend/src/stores/useAuthStore.ts — Auth State Management
 *
 * Dùng Supabase Auth session làm source of truth.
 * - login/register thực sự qua Supabase Auth
 * - Token (JWT) được lấy từ Supabase session và gửi tới FastAPI backend
 * - Role & MSSV được lấy từ user_metadata hoặc backend profile
 */
import { create } from "zustand";
import { supabase } from "../lib/supabase";
import type { Session, User } from "@supabase/supabase-js";

export type UserRole = "ADMIN" | "STAFF" | "STUDENT";

export interface UserProfile {
  id: string;
  username: string;
  fullName: string;
  email: string;
  mssv?: string;
  role: UserRole;
  avatarUrl?: string;
}

interface AuthState {
  user: UserProfile | null;
  session: Session | null;
  token: string | null;
  isAuthenticated: boolean;
  isLoading: boolean;

  // Actions
  login: (user: UserProfile, token: string, session: Session) => void;
  logout: () => Promise<void>;
  setSession: (session: Session | null) => void;
  setRole: (role: UserRole) => void;
  updateProfile: (profile: Partial<UserProfile>) => void;
}

/** Chuyển Supabase User → UserProfile app */
export const buildUserProfile = (
  supaUser: User,
  roleOverride?: UserRole,
  mssvOverride?: string
): UserProfile => {
  const meta = supaUser.user_metadata ?? {};
  return {
    id: supaUser.id,
    username: meta.username ?? supaUser.email?.split("@")[0] ?? "user",
    fullName: meta.full_name ?? meta.name ?? supaUser.email ?? "Người dùng",
    email: supaUser.email ?? "",
    mssv: mssvOverride ?? meta.mssv,
    role: roleOverride ?? (meta.role as UserRole) ?? "STUDENT",
  };
};

const getInitialUser = (): UserProfile | null => {
  try {
    const raw = localStorage.getItem("user_profile");
    return raw ? JSON.parse(raw) : null;
  } catch {
    return null;
  }
};
const initialToken = localStorage.getItem("access_token");
const initialUser = getInitialUser();

export const useAuthStore = create<AuthState>((set) => ({
  user: initialUser,
  session: null,
  token: initialToken,
  isAuthenticated: !!(initialToken && initialUser),
  isLoading: false,

  login: (user, token, session) => {
    localStorage.setItem("access_token", token);
    localStorage.setItem("user_profile", JSON.stringify(user));
    set({ user, token, session, isAuthenticated: true, isLoading: false });
  },

  logout: async () => {
    try {
      await supabase.auth.signOut();
    } catch (e) {
      // ignore
    }
    localStorage.removeItem("access_token");
    localStorage.removeItem("user_profile");
    set({
      user: null,
      token: null,
      session: null,
      isAuthenticated: false,
      isLoading: false,
    });
  },

  setSession: (session) => {
    if (session) {
      const user = buildUserProfile(session.user);
      localStorage.setItem("access_token", session.access_token);
      localStorage.setItem("user_profile", JSON.stringify(user));
      set({
        session,
        user,
        token: session.access_token,
        isAuthenticated: true,
        isLoading: false,
      });
    } else {
      set({ isLoading: false });
    }
  },

  setRole: (role) =>
    set((state) => {
      const updated = state.user ? { ...state.user, role } : null;
      if (updated) localStorage.setItem("user_profile", JSON.stringify(updated));
      return { user: updated };
    }),

  updateProfile: (profile) =>
    set((state) => {
      const updated = state.user ? { ...state.user, ...profile } : null;
      if (updated) localStorage.setItem("user_profile", JSON.stringify(updated));
      return { user: updated };
    }),
}));
