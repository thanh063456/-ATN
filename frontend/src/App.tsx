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

/** Khôi phục session từ Supabase khi app khởi động */
const useSupabaseAuth = () => {
  const { setSession } = useAuthStore();

  useEffect(() => {
    try {
      supabase.auth.getSession()
        .then(({ data }) => {
          if (data?.session) {
            setSession(data.session);
          }
        })
        .catch((err) => {
          console.warn("Supabase getSession skipped:", err);
        });

      const { data: authListener } = supabase.auth.onAuthStateChange(
        (_event, session) => {
          if (session) setSession(session);
        }
      );

      return () => {
        authListener?.subscription?.unsubscribe();
      };
    } catch (err) {
      console.warn("Supabase auth listener initialization error:", err);
    }
  }, [setSession]);
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
      </BrowserRouter>
    </QueryClientProvider>
  );
};

export default App;
