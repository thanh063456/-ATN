import axios from "axios";

export const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000/api/v1";

export const apiClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: 120000, // 120 giây (hỗ trợ upload các file PDF scan dung lượng lớn)
});

apiClient.interceptors.request.use((config) => {
  const token = localStorage.getItem("access_token");
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    // Khi token hết hạn (401), tự động xóa token cũ và redirect về login
    if (error.response?.status === 401) {
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
