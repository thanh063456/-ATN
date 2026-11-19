/**
 * frontend/src/api/auth.ts — Auth API helpers
 *
 * Kết hợp Supabase Auth (sign_in/sign_up) và FastAPI backend (/auth/signup, /auth/confirm-user, /auth/me).
 * Tự động giải quyết vấn đề "Email not confirmed" bằng Supabase Admin API qua backend.
 */
import { supabase, isAllowedEmail } from "../lib/supabase";
import { apiClient } from "./client";

export interface UserResponse {
  id: string;
  supabase_uid?: string;
  username: string;
  email: string;
  full_name: string;
  mssv?: string;
  role_name: "ADMIN" | "STAFF" | "STUDENT";
  is_active: boolean;
  created_at: string;
}

export interface RegisterPayload {
  email: string;
  password: string;
  fullName: string;
  mssv?: string;
}

export interface LoginPayload {
  email: string;
  password: string;
}

export const authApi = {
  /**
   * Đăng nhập qua Supabase Auth.
   * Nếu tài khoản chưa xác nhận email, tự động gọi backend để xác thực (auto-confirm) và thử lại.
   */
  login: async (payload: LoginPayload) => {
    if (!isAllowedEmail(payload.email)) {
      throw new Error("Chỉ tài khoản email @dlu.edu.vn mới được phép đăng nhập");
    }

    // 1. Thử đăng nhập qua Supabase Auth
    try {
      let supaRes = await supabase.auth.signInWithPassword({
        email: payload.email,
        password: payload.password,
      });

      // Nếu bị kẹt lỗi Email not confirmed, tự động kích hoạt qua backend rồi đăng nhập lại
      if (supaRes.error && supaRes.error.message.toLowerCase().includes("email not confirmed")) {
        try {
          await apiClient.post("/auth/confirm-user", { email: payload.email });
          supaRes = await supabase.auth.signInWithPassword({
            email: payload.email,
            password: payload.password,
          });
        } catch (confirmErr) {
          console.warn("Auto confirm attempt failed:", confirmErr);
        }
      }

      if (supaRes.data?.session && supaRes.data?.user) {
        return {
          session: supaRes.data.session,
          user: supaRes.data.user,
          token: supaRes.data.session.access_token,
        };
      }
    } catch (supaErr) {
      console.warn("Supabase auth failed or blocked, trying backend direct login:", supaErr);
    }

    // 2. Fallback: Đăng nhập trực tiếp qua FastAPI backend (an toàn 100%, không phụ thuộc mạng Supabase)
    const backendRes = await apiClient.post<{
      access_token: string;
      token_type: string;
      expires_in: number;
      user: UserResponse;
    }>("/auth/login", {
      username: payload.email,
      password: payload.password,
    });

    const backendUser = backendRes.data.user;
    const token = backendRes.data.access_token;

    const mockUser: any = {
      id: String(backendUser.id),
      email: backendUser.email,
      user_metadata: {
        full_name: backendUser.full_name,
        role: backendUser.role_name,
        mssv: backendUser.mssv,
      },
    };

    const mockSession: any = {
      access_token: token,
      user: mockUser,
    };

    return {
      session: mockSession,
      user: mockUser,
      token: token,
      backendUser: backendUser,
    };
  },

  /**
   * Đăng ký tài khoản mới.
   * Gọi backend /auth/signup (sử dụng Supabase Admin API với email_confirm: True),
   * giúp tài khoản có thể đăng nhập ngay mà không cần đợi xác nhận email.
   */
  register: async (payload: RegisterPayload) => {
    if (!isAllowedEmail(payload.email)) {
      throw new Error("Chỉ email đuôi @dlu.edu.vn mới được phép tạo tài khoản");
    }

    // 1. Tạo user qua backend với auto email confirm
    const backendRes = await apiClient.post<UserResponse>("/auth/signup", {
      email: payload.email,
      password: payload.password,
      full_name: payload.fullName,
      mssv: payload.mssv || null,
    });

    // 2. Tự động đăng nhập luôn để lấy session
    let authData = { session: null as any, user: null as any };
    try {
      const loginRes = await supabase.auth.signInWithPassword({
        email: payload.email,
        password: payload.password,
      });
      authData = loginRes.data;
    } catch (loginErr) {
      console.warn("Auto login after registration skipped:", loginErr);
    }

    return {
      backendUser: backendRes.data,
      ...authData,
    };
  },

  /**
   * Lấy thông tin user từ FastAPI backend (role, mssv, is_active...).
   */
  getMe: async (): Promise<UserResponse> => {
    const res = await apiClient.get<UserResponse>("/auth/me");
    return res.data;
  },

  /** Đăng xuất khỏi Supabase session. */
  signOut: async () => {
    await supabase.auth.signOut();
  },
};
