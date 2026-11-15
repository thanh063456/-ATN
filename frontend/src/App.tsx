import React, { useEffect } from "react";
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { AppLayout } from "./components/layout/AppLayout";
import { LoginPage } from "./pages/LoginPage";
import { RegisterPage } from "./pages/RegisterPage";
import { VerifyPage } from "./pages/VerifyPage";
import { DashboardPage } from "./pages/DashboardPage";
import { UploadPage } from "./pages/UploadPage";
import { SearchPage } from "./pages/SearchPage";
import { DocumentsPage } from "./pages/DocumentsPage";
import { DocumentDetailPage } from "./pages/DocumentDetailPage";
import { UserManagementPage } from "./pages/UserManagementPage";
import { CategoryManagementPage } from "./pages/CategoryManagementPage";
import { ProfilePage } from "./pages/ProfilePage";
import { useAuthStore } from "./stores/useAuthStore";
import { supabase } from "./lib/supabase";

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      refetchOnWindowFocus: false,
      retry: 1,
    },
  },
});

/** Khôi phục session từ Supabase khi app khởi động và xử lý token hết hạn */
const useSupabaseAuth = () => {
  const { setSession, logout } = useAuthStore();

  useEffect(() => {
    try {
      // Kiểm tra session hiện tại khi app load
      supabase.auth.getSession()
        .then(({ data }) => {
          if (data?.session) {
            setSession(data.session);
          } else {
            // Không có session hợp lệ → xóa token cũ khỏi localStorage
            const storedToken = localStorage.getItem("access_token");
            if (storedToken && !storedToken.startsWith("demo_")) {
              console.warn("[Auth] Stored token invalid, clearing...");
              localStorage.removeItem("access_token");
              localStorage.removeItem("user_profile");
            }
          }
        })
        .catch((err) => {
          console.warn("Supabase getSession skipped:", err);
        });

      const { data: authListener } = supabase.auth.onAuthStateChange(
        (event, session) => {
          if (event === "SIGNED_IN" || event === "TOKEN_REFRESHED") {
            if (session) setSession(session);
          } else if (event === "SIGNED_OUT") {
            // Token hết hạn hoặc bị thu hồi → chỉ gọi nếu còn token hoặc đang authenticated
            const storedToken = localStorage.getItem("access_token");
            if (storedToken || useAuthStore.getState().isAuthenticated) {
              logout();
            }
          }
        }
      );

      return () => {
        authListener?.subscription?.unsubscribe();
      };
    } catch (err) {
      console.warn("Supabase auth listener initialization error:", err);
    }
  }, [setSession, logout]);
};

const ProtectedRoute: React.FC<{ children: React.ReactNode }> = ({
  children,
}) => {
  const { isAuthenticated, isLoading } = useAuthStore();

  if (isLoading) {
    return (
      <div
        style={{
          minHeight: "100vh",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          backgroundColor: "#0e1e33",
        }}
      >
        <div
          style={{
            width: 36,
            height: 36,
            border: "3px solid rgba(255, 255, 255, 0.15)",
            borderTopColor: "#60a5fa",
            borderRadius: "50%",
            animation: "spin 0.7s linear infinite",
          }}
        />
      </div>
    );
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }
  return <>{children}</>;
};

export const App: React.FC = () => {
  useSupabaseAuth();

  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <Routes>
          {/* Public Auth & Verification Routes */}
          <Route path="/login" element={<LoginPage />} />
          <Route path="/register" element={<RegisterPage />} />
          <Route path="/verify/:id" element={<VerifyPage />} />

          {/* Protected Application Routes */}
          <Route
            path="/"
            element={
              <ProtectedRoute>
                <AppLayout />
              </ProtectedRoute>
            }
          >
            <Route index element={<DashboardPage />} />
            <Route path="upload" element={<UploadPage />} />
            <Route path="search" element={<SearchPage />} />
            <Route path="documents" element={<DocumentsPage />} />
            <Route path="document" element={<Navigate to="/documents" replace />} />
            <Route path="docs" element={<Navigate to="/documents" replace />} />
            <Route path="documents/:id" element={<DocumentDetailPage />} />
            <Route path="document/:id" element={<Navigate to="/documents/:id" replace />} />
            <Route path="admin/users" element={<UserManagementPage />} />
            <Route path="admin/categories" element={<CategoryManagementPage />} />
            <Route path="profile" element={<ProfilePage />} />
          </Route>

          {/* Fallback */}
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </BrowserRouter>
    </QueryClientProvider>
  );
};

export default App;
