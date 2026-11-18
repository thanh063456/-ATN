import React from "react";
import { useNavigate } from "react-router-dom";
import { useQueryClient } from "@tanstack/react-query";
import {
  Menu,
  Search,
  LogOut,
  ShieldCheck,
  UserCheck,
  GraduationCap,
} from "lucide-react";
import { useAuthStore } from "../../stores/useAuthStore";
import { Badge } from "../common/Badge";
import { NotificationDropdown } from "./NotificationDropdown";

interface HeaderProps {
  onToggleSidebar: () => void;
}

export const Header: React.FC<HeaderProps> = ({ onToggleSidebar }) => {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
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
        return <ShieldCheck size={13} className="text-rose-600" />;
      case "STAFF":
        return <UserCheck size={13} className="text-amber-600" />;
      default:
        return <GraduationCap size={13} className="text-sky-600" />;
    }
  };

  return (
    <header className="h-[60px] bg-white border-b border-slate-200/80 flex items-center justify-between px-4 sm:px-6 sticky top-0 z-30 shadow-sm">
      {/* Left section: Toggle & Quick Search */}
      <div className="flex items-center gap-3 sm:gap-4">
        <button
          onClick={onToggleSidebar}
          className="p-1.5 rounded-md text-slate-500 hover:text-slate-800 hover:bg-slate-100 transition-colors"
          title="Thu gọn / Mở rộng menu"
          aria-label="Toggle Sidebar"
        >
          <Menu size={19} />
        </button>

        <form
          onSubmit={(e) => {
            e.preventDefault();
            const target = e.currentTarget.elements.namedItem("headerSearch") as HTMLInputElement;
            const term = target?.value?.trim();
            if (term) {
              navigate(`/search?q=${encodeURIComponent(term)}`);
            }
          }}
          className="flex items-center gap-2 bg-slate-100/80 hover:bg-slate-100 focus-within:bg-white focus-within:ring-2 focus-within:ring-dlu-navy-500/20 focus-within:border-dlu-navy-600 border border-slate-200 rounded-md px-3 py-1.5 w-64 sm:w-80 md:w-96 transition-all"
        >
          <Search size={15} className="text-slate-400 shrink-0" />
          <input
            name="headerSearch"
            type="text"
            placeholder="Tra cứu số hiệu văn bản, tiêu đề hoặc MSSV..."
            className="border-none bg-transparent outline-none text-xs text-slate-800 placeholder-slate-400 w-full"
          />
          <kbd className="hidden sm:inline-block px-1.5 py-0.5 text-[10px] font-mono text-slate-400 bg-white border border-slate-200 rounded shadow-2xs">
            ↵
          </kbd>
        </form>
      </div>

      {/* Right section: System status, Role Indicator, Profile */}
      <div className="flex items-center gap-2 sm:gap-4">
        {/* Backend Status indicator */}
        <div className="hidden lg:flex items-center gap-1.5 text-xs text-slate-600 bg-emerald-50/80 border border-emerald-200/60 px-2 py-0.5 rounded-full">
          <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
          <span className="font-medium text-emerald-800 text-[11px]">Hệ thống sẵn sàng</span>
        </div>

        {/* Static Role Display */}
        <div className="hidden sm:flex items-center gap-1.5">
          <Badge variant={getRoleBadgeVariant()} size="sm">
            <span className="inline-flex items-center gap-1">
              {getRoleIcon()}
              <span>{getRoleLabel()}</span>
            </span>
          </Badge>
        </div>

        {/* Nút Chuông Thông Báo Xét Duyệt Hồ Sơ */}
        <NotificationDropdown />

        {/* User Info Chip */}
        <div className="flex items-center gap-2 pl-2 sm:pl-3 border-l border-slate-200">
          <button
            onClick={() => navigate("/profile")}
            className="flex items-center gap-2 p-1 sm:px-2 sm:py-1 rounded-md hover:bg-slate-100 transition-colors text-left"
            title="Xem hồ sơ cá nhân & các tài liệu đã tải lên"
          >
            <div className="w-8 h-8 rounded-full bg-dlu-navy-900 text-white flex items-center justify-center font-bold text-xs shadow-xs">
              {user?.fullName?.charAt(0) || "U"}
            </div>

            <div className="hidden md:flex flex-col leading-tight">
              <span className="text-xs font-semibold text-slate-800 truncate max-w-[140px]">
                {user?.fullName || "Người dùng"}
              </span>
              <span className="text-[10px] text-slate-500 font-mono">
                {user?.mssv ? `MSSV: ${user.mssv}` : user?.role}
              </span>
            </div>
          </button>

          <button
            onClick={async () => {
              queryClient.clear();
              await logout();
              navigate("/login", { replace: true });
            }}
            className="p-1.5 text-slate-400 hover:text-rose-600 hover:bg-rose-50 rounded-md transition-colors"
            title="Đăng xuất"
            aria-label="Đăng xuất"
          >
            <LogOut size={16} />
          </button>
        </div>
      </div>
    </header>
  );
};
