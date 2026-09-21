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
  Sparkles,
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
      label: "Tra cứu toàn văn",
      path: "/search",
      icon: FileSearch,
      roles: ["ADMIN", "STAFF", "STUDENT"],
    },
    {
      label: "Phê duyệt & OCR",
      path: "/documents",
      icon: FileCheck2,
      roles: ["ADMIN", "STAFF"],
      badge: "CTSV",
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
            width: "36px",
            height: "36px",
            borderRadius: "10px",
            background: "linear-gradient(135deg, #6366f1 0%, #4338ca 100%)",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            flexShrink: 0,
            boxShadow: "0 4px 10px rgba(99, 102, 241, 0.4)",
          }}
        >
          <FileText size={20} color="#ffffff" />
        </div>
        {!collapsed && (
          <div style={{ overflow: "hidden", whiteSpace: "nowrap" }}>
            <div style={{ fontWeight: 700, fontSize: "0.95rem", letterSpacing: "-0.01em" }}>
              DocuCTSV <span style={{ color: "#818cf8", fontSize: "0.75rem" }}>OCR</span>
            </div>
            <div style={{ fontSize: "0.6875rem", color: "var(--gray-400)" }}>
              Số hóa Tài liệu CTSV
            </div>
          </div>
        )}
      </div>

      {/* Nav List */}
      <div style={{ flex: 1, padding: "1rem 0.75rem", display: "flex", flexDirection: "column", gap: "0.35rem", overflowY: "auto" }}>
        <div style={{ fontSize: "0.6875rem", fontWeight: 700, color: "var(--gray-500)", textTransform: "uppercase", padding: "0.5rem 0.75rem", letterSpacing: "0.05em" }}>
          {!collapsed ? "Menu Chức năng" : "•••"}
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
                gap: "0.85rem",
                padding: "0.65rem 0.85rem",
                borderRadius: "var(--radius-md)",
                fontSize: "0.875rem",
                fontWeight: isActive ? 600 : 500,
                color: isActive ? "#ffffff" : "var(--gray-400)",
                backgroundColor: isActive
                  ? "rgba(99, 102, 241, 0.2)"
                  : "transparent",
                border: isActive ? "1px solid rgba(99, 102, 241, 0.4)" : "1px solid transparent",
                transition: "all 0.15s ease",
              }}
            >
              <Icon size={19} color={isActive ? "#818cf8" : "currentColor"} />
              {!collapsed && (
                <span style={{ flex: 1, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
                  {item.label}
                </span>
              )}
              {!collapsed && item.badge && (
                <span
                  style={{
                    fontSize: "0.6875rem",
                    padding: "0.1rem 0.45rem",
                    borderRadius: "4px",
                    backgroundColor: "rgba(99, 102, 241, 0.3)",
                    color: "#a5b4fc",
                    fontWeight: 700,
                  }}
                >
                  {item.badge}
                </span>
              )}
            </Link>
          );
        })}
      </div>

      {/* Pro tip card / Model badge */}
      {!collapsed && (
        <div style={{ padding: "1rem", margin: "0.75rem", backgroundColor: "rgba(255, 255, 255, 0.04)", borderRadius: "var(--radius-md)", border: "1px solid rgba(255, 255, 255, 0.06)" }}>
          <div style={{ display: "flex", alignItems: "center", gap: "0.5rem", marginBottom: "0.25rem" }}>
            <Sparkles size={16} color="#818cf8" />
            <span style={{ fontSize: "0.75rem", fontWeight: 700, color: "#e2e8f0" }}>VietOCR Engine v2.0</span>
          </div>
          <p style={{ fontSize: "0.6875rem", color: "var(--gray-400)", lineHeight: 1.4 }}>
            Hỗ trợ nhận dạng văn bản tiếng Việt & tìm kiếm Elasticsearch.
          </p>
        </div>
      )}
    </aside>
  );
};
