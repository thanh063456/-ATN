import React, { useEffect, Suspense, lazy } from "react";
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { AppLayout } from "./components/layout/AppLayout";
import { useAuthStore } from "./stores/useAuthStore";
import { supabase } from "./lib/supabase";

// Code splitting các trang lớn bằng React.lazy để tối ưu bundle size ban đầu (<200kB)
const LoginPage = lazy(() => import("./pages/LoginPage").then(m => ({ default: m.LoginPage })));
const RegisterPage = lazy(() => import("./pages/RegisterPage").then(m => ({ default: m.RegisterPage })));
const VerifyPage = lazy(() => import("./pages/VerifyPage").then(m => ({ default: m.VerifyPage })));
const DashboardPage = lazy(() => import("./pages/DashboardPage").then(m => ({ default: m.DashboardPage })));
const UploadPage = lazy(() => import("./pages/UploadPage").then(m => ({ default: m.UploadPage })));
const SearchPage = lazy(() => import("./pages/SearchPage").then(m => ({ default: m.SearchPage })));
const DocumentsPage = lazy(() => import("./pages/DocumentsPage").then(m => ({ default: m.DocumentsPage })));
const DocumentDetailPage = lazy(() => import("./pages/DocumentDetailPage").then(m => ({ default: m.DocumentDetailPage })));
const UserManagementPage = lazy(() => import("./pages/UserManagementPage").then(m => ({ default: m.UserManagementPage })));
const CategoryManagementPage = lazy(() => import("./pages/CategoryManagementPage").then(m => ({ default: m.CategoryManagementPage })));

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
            if (storedToken) {
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
            // Token hết hạn hoặc bị thu hồi → logout sạch
            logout();
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
          backgroundColor: "#0f172a",
        }}
      >
        <div
          style={{
            width: 36,
            height: 36,
            border: "3px solid rgba(99,102,241,0.3)",
            borderTopColor: "#6366f1",
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
        <Suspense
          fallback={
            <div
              style={{
                minHeight: "100vh",
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                backgroundColor: "#f8fafc",
              }}
            >
              <div
                style={{
                  width: 32,
                  height: 32,
                  border: "3px solid #e2e8f0",
                  borderTopColor: "#4f46e5",
                  borderRadius: "50%",
                  animation: "spin 0.6s linear infinite",
                }}
              />
            </div>
          }
        >
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
              <Route path="documents/:id" element={<DocumentDetailPage />} />
              <Route path="admin/users" element={<UserManagementPage />} />
              <Route path="admin/categories" element={<CategoryManagementPage />} />
            </Route>

            {/* Fallback */}
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </Suspense>
      </BrowserRouter>
    </QueryClientProvider>
  );
};

export default App;
