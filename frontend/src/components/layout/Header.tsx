import React from "react";
import { useNavigate } from "react-router-dom";
import {
  Menu,
  Search,
  LogOut,
  ShieldCheck,
  UserCheck,
  GraduationCap,
  Activity,
} from "lucide-react";
import { useAuthStore } from "../../stores/useAuthStore";
import { Badge } from "../common/Badge";

interface HeaderProps {
  onToggleSidebar: () => void;
}

export const Header: React.FC<HeaderProps> = ({ onToggleSidebar }) => {
  const navigate = useNavigate();
  const { user, logout } = useAuthStore();

  const getRoleBadgeVariant = () => {
    switch (user?.role) {
      case "ADMIN":
        return "danger";
      case "STAFF":
        return "warning";
      default:
        return "info";
    }
  };

  const getRoleLabel = () => {
    switch (user?.role) {
      case "ADMIN":
        return "Quản trị viên (ADMIN)";
      case "STAFF":
        return "Cán bộ CTSV (STAFF)";
      default:
        return "Sinh viên (STUDENT)";
    }
  };

  const getRoleIcon = () => {
    switch (user?.role) {
      case "ADMIN":
        return <ShieldCheck size={13} color="#ef4444" />;
      case "STAFF":
        return <UserCheck size={13} color="#d97706" />;
      default:
        return <GraduationCap size={13} color="#0284c7" />;
    }
  };

  return (
    <header
      style={{
        height: "var(--header-height)",
        backgroundColor: "var(--bg-surface)",
        borderBottom: "1px solid var(--border-color)",
        display: "flex",
        alignItems: "center",
        justifyContent: "space-between",
        padding: "0 1.5rem",
        position: "sticky",
        top: 0,
        zIndex: 40,
      }}
    >
      {/* Left section: Toggle & Quick Search */}
      <div style={{ display: "flex", alignItems: "center", gap: "1rem" }}>
        <button
          onClick={onToggleSidebar}
          style={{
            padding: "0.5rem",
            borderRadius: "var(--radius-sm)",
            color: "var(--gray-600)",
            display: "flex",
          }}
          title="Toggle Sidebar"
        >
          <Menu size={20} />
        </button>

        <div
          onClick={() => navigate("/search")}
          style={{
            display: "flex",
            alignItems: "center",
            gap: "0.5rem",
            backgroundColor: "var(--gray-100)",
            padding: "0.45rem 0.85rem",
            borderRadius: "var(--radius-md)",
            color: "var(--gray-500)",
            fontSize: "0.8125rem",
            cursor: "pointer",
            width: "280px",
            border: "1px solid transparent",
            transition: "all 0.15s ease",
          }}
        >
          <Search size={15} />
          <span>Tra cứu tài liệu CTSV...</span>
          <kbd
            style={{
              marginLeft: "auto",
              padding: "0.1rem 0.35rem",
              backgroundColor: "#ffffff",
              border: "1px solid var(--border-color)",
              borderRadius: "4px",
              fontSize: "0.6875rem",
              color: "var(--gray-500)",
            }}
          >
            ⌘K
          </kbd>
        </div>
      </div>

      {/* Right section: System status, Static Role Indicator, Profile */}
      <div style={{ display: "flex", alignItems: "center", gap: "1.25rem" }}>
        {/* Backend & ES Live Status indicator */}
        <div style={{ display: "flex", alignItems: "center", gap: "0.4rem", fontSize: "0.75rem", color: "var(--success-700)", backgroundColor: "var(--success-50)", padding: "0.25rem 0.6rem", borderRadius: "9999px", border: "1px solid #bbf7d0" }}>
          <Activity size={13} className="animate-pulse" />
          <span style={{ fontWeight: 600 }}>Hệ thống Online</span>
        </div>

        {/* Static Role Display (Fixed, no dropdown change) */}
        <div style={{ display: "flex", alignItems: "center", gap: "0.4rem" }}>
          <span style={{ fontSize: "0.75rem", color: "var(--gray-500)", fontWeight: 500 }}>Vai trò:</span>
          <Badge variant={getRoleBadgeVariant()}>
            <span style={{ display: "inline-flex", alignItems: "center", gap: "4px" }}>
              {getRoleIcon()}
              <span>{getRoleLabel()}</span>
            </span>
          </Badge>
        </div>

        {/* User Info */}
        <div style={{ display: "flex", alignItems: "center", gap: "0.75rem", paddingLeft: "0.75rem", borderLeft: "1px solid var(--border-color)" }}>
          <div
            style={{
              width: "34px",
              height: "34px",
              borderRadius: "50%",
              backgroundColor: "var(--primary-100)",
              color: "var(--primary-700)",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              fontWeight: 700,
              fontSize: "0.875rem",
            }}
          >
            {user?.fullName?.charAt(0) || "U"}
          </div>

          <div style={{ display: "flex", flexDirection: "column" }}>
            <span style={{ fontSize: "0.8125rem", fontWeight: 600, color: "var(--gray-900)" }}>
              {user?.fullName}
            </span>
            <div style={{ display: "flex", alignItems: "center", gap: "0.3rem", fontSize: "0.6875rem", color: "var(--gray-500)" }}>
              {getRoleIcon()}
              <span>{user?.mssv ? `MSSV: ${user.mssv}` : user?.role}</span>
            </div>
          </div>

          <button
            onClick={() => {
              logout();
              navigate("/login");
            }}
            style={{
              padding: "0.45rem",
              color: "var(--gray-400)",
              borderRadius: "var(--radius-sm)",
              display: "flex",
            }}
            title="Đăng xuất"
          >
            <LogOut size={17} />
          </button>
        </div>
      </div>
    </header>
  );
};
