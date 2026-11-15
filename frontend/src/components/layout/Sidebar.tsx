import React from "react";
import { Link, useLocation } from "react-router-dom";
import {
  LayoutDashboard,
  UploadCloud,
  FileSearch,
  FileCheck2,
  Users,
  FolderKanban,
  FileText,
  UserCircle,
} from "lucide-react";
import { useAuthStore } from "../../stores/useAuthStore";

interface SidebarProps {
  collapsed: boolean;
  onToggle: () => void;
}

export const Sidebar: React.FC<SidebarProps> = ({ collapsed }) => {
  const location = useLocation();
  const { user } = useAuthStore();

  const role = user?.role || "STAFF";

  const navigation = [
    {
      label: "Tổng quan",
      path: "/",
      icon: LayoutDashboard,
      roles: ["ADMIN", "STAFF", "STUDENT"],
    },
    {
      label: "Upload tài liệu",
      path: "/upload",
      icon: UploadCloud,
      roles: ["ADMIN", "STAFF", "STUDENT"],
      highlight: true,
    },
    {
      label: role === "STUDENT" ? "Kho hồ sơ công khai" : "Quản lý Văn bản & Hồ sơ",
      path: "/documents",
      icon: FileCheck2,
      roles: ["ADMIN", "STAFF", "STUDENT"],
      badge: role === "STUDENT" ? undefined : "CTSV",
    },
    {
      label: "Tra cứu toàn văn",
      path: "/search",
      icon: FileSearch,
      roles: ["ADMIN", "STAFF", "STUDENT"],
    },
    {
      label: "Hồ sơ cá nhân",
      path: "/profile",
      icon: UserCircle,
      roles: ["ADMIN", "STAFF", "STUDENT"],
    },
    {
      label: "Quản trị người dùng",
      path: "/admin/users",
      icon: Users,
      roles: ["ADMIN"],
    },
    {
      label: "Danh mục biểu mẫu",
      path: "/admin/categories",
      icon: FolderKanban,
      roles: ["ADMIN"],
    },
  ];

  const allowedNav = navigation.filter((item) => item.roles.includes(role));

  return (
    <aside
      style={{
        width: collapsed ? "var(--sidebar-collapsed-width)" : "var(--sidebar-width)",
        backgroundColor: "var(--bg-sidebar)",
        color: "#ffffff",
        height: "100vh",
        position: "sticky",
        top: 0,
        display: "flex",
        flexDirection: "column",
        transition: "width 0.25s ease",
        zIndex: 50,
        flexShrink: 0,
        borderRight: "1px solid rgba(255, 255, 255, 0.08)",
      }}
    >
      {/* Brand Logo */}
      <div
        style={{
          height: "var(--header-height)",
          display: "flex",
          alignItems: "center",
          gap: "0.75rem",
          padding: "0 1.25rem",
          borderBottom: "1px solid rgba(255, 255, 255, 0.08)",
        }}
      >
        <div
          style={{
            width: "34px",
            height: "34px",
            borderRadius: "var(--radius-sm)",
            backgroundColor: "#1e3a8a",
            border: "1px solid rgba(255, 255, 255, 0.2)",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            flexShrink: 0,
          }}
        >
          <FileText size={18} color="#93c5fd" />
        </div>
        {!collapsed && (
          <div style={{ overflow: "hidden", whiteSpace: "nowrap" }}>
            <div style={{ fontWeight: 700, fontSize: "0.875rem", letterSpacing: "0.02em", color: "#f8fafc" }}>
              ĐẠI HỌC ĐÀ LẠT
            </div>
            <div style={{ fontSize: "0.6875rem", color: "#94a3b8" }}>
              Phòng Công tác Sinh viên
            </div>
          </div>
        )}
      </div>

      {/* Nav List */}
      <div style={{ flex: 1, padding: "0.85rem 0.5rem", display: "flex", flexDirection: "column", gap: "0.25rem", overflowY: "auto" }}>
        <div style={{ fontSize: "0.6875rem", fontWeight: 600, color: "#64748b", padding: "0.4rem 0.75rem", letterSpacing: "0.04em" }}>
          {!collapsed ? "Hồ sơ & Nghiệp vụ" : "•••"}
        </div>
        {allowedNav.map((item) => {
          const isActive = location.pathname === item.path || (item.path !== "/" && location.pathname.startsWith(item.path));
          const Icon = item.icon;

          return (
            <Link
              key={item.path}
              to={item.path}
              title={collapsed ? item.label : undefined}
              style={{
                display: "flex",
                alignItems: "center",
                gap: "0.75rem",
                padding: "0.6rem 0.75rem",
                borderRadius: "var(--radius-md)",
                fontSize: "0.8125rem",
                fontWeight: isActive ? 600 : 500,
                color: isActive ? "#ffffff" : "#94a3b8",
                backgroundColor: isActive ? "rgba(37, 99, 235, 0.2)" : "transparent",
                borderLeft: isActive ? "3px solid #60a5fa" : "3px solid transparent",
                transition: "all 0.15s ease",
              }}
            >
              <Icon size={18} color={isActive ? "#60a5fa" : "currentColor"} />
              {!collapsed && (
                <span style={{ flex: 1, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
                  {item.label}
                </span>
              )}
              {!collapsed && item.badge && (
                <span
                  style={{
                    fontSize: "0.625rem",
                    padding: "0.1rem 0.4rem",
                    borderRadius: "2px",
                    backgroundColor: "rgba(255, 255, 255, 0.1)",
                    color: "#bfdbfe",
                    fontWeight: 600,
                  }}
                >
                  {item.badge}
                </span>
              )}
            </Link>
          );
        })}
      </div>

      {/* Footer Info Box */}
      {!collapsed && (
        <div style={{ padding: "0.75rem 1rem", margin: "0.65rem", backgroundColor: "rgba(255, 255, 255, 0.03)", borderRadius: "var(--radius-sm)", border: "1px solid rgba(255, 255, 255, 0.06)" }}>
          <div style={{ fontSize: "0.6875rem", fontWeight: 600, color: "#cbd5e1" }}>
            Kho lưu trữ số CTSV
          </div>
          <div style={{ fontSize: "0.625rem", color: "#64748b", marginTop: "0.2rem" }}>
            Trường Đại học Đà Lạt
          </div>
        </div>
      )}
    </aside>
  );
};
