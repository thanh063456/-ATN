import axios from "axios";
import { supabase } from "../lib/supabase";

export const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000/api/v1";

export const apiClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: 120000, // 120 giây (hỗ trợ upload các file PDF scan dung lượng lớn)
});

apiClient.interceptors.request.use(async (config) => {
  try {
    // 1. Thử lấy token mới nhất từ Supabase session (tự động refresh nếu token đã hoặc sắp hết hạn)
    const { data } = await supabase.auth.getSession();
    if (data?.session?.access_token) {
      const freshToken = data.session.access_token;
      localStorage.setItem("access_token", freshToken);
      config.headers.Authorization = `Bearer ${freshToken}`;
      return config;
    }
  } catch {
    // Không làm gián đoạn request nếu Supabase network tạm thời chậm
  }

  // 2. Fallback sang localStorage nếu là token backend tự cấp hoặc khi offline
  const token = localStorage.getItem("access_token");
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

apiClient.interceptors.response.use(
  (response) => response,
  async (error) => {
    // Khi token hết hạn (401), thử refresh session trước khi logout
    if (error.response?.status === 401) {
      try {
        const { data } = await supabase.auth.refreshSession();
        if (data?.session?.access_token) {
          const freshToken = data.session.access_token;
          localStorage.setItem("access_token", freshToken);
          const originalRequest = error.config;
          if (originalRequest && !originalRequest._retry) {
            originalRequest._retry = true;
            originalRequest.headers.Authorization = `Bearer ${freshToken}`;
            return apiClient(originalRequest);
          }
        }
      } catch {
        // Refresh thất bại
      }

      const storedToken = localStorage.getItem("access_token");
      if (storedToken) {
        console.warn("[API] 401 Unauthorized — clearing expired token");
        localStorage.removeItem("access_token");
        localStorage.removeItem("user_profile");
        // Redirect về login nếu chưa ở trang login
        if (!window.location.pathname.includes("/login")) {
          window.location.href = "/login";
        }
      }
    }
    const message =
      error.response?.data?.detail ||
      error.response?.data?.message ||
      error.message ||
      "Đã có lỗi xảy ra";
    return Promise.reject(new Error(message));
  }
);
