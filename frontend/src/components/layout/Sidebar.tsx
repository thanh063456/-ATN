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
      label: role === "STUDENT" ? "Lịch sử upload" : "Quản lý Văn bản & Hồ sơ",
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
      className={`h-screen sticky top-0 flex flex-col shrink-0 z-40 bg-[#0a192f] text-slate-200 border-r border-slate-800/80 transition-all duration-200 select-none ${
        collapsed ? "w-[72px]" : "w-64"
      }`}
    >
      {/* Brand Header */}
      <div className="h-[60px] flex items-center gap-3 px-4 border-b border-slate-800/80 shrink-0">
        <div className="w-8 h-8 rounded-md bg-dlu-navy-800 border border-sky-400/30 flex items-center justify-center shrink-0 shadow-sm text-sky-300">
          <FileText size={17} />
        </div>
        {!collapsed && (
          <div className="overflow-hidden leading-tight">
            <div className="font-bold text-xs tracking-wider text-white uppercase font-sans">
              Đại học Đà Lạt
            </div>
            <div className="text-[11px] text-slate-400 font-medium truncate">
              Phòng Công tác Sinh viên
            </div>
          </div>
        )}
      </div>

      {/* Nav List */}
      <nav className="flex-1 px-2.5 py-4 flex flex-col gap-1 overflow-y-auto">
        <div className="text-[10px] font-semibold text-slate-500 uppercase tracking-wider px-3 py-1">
          {!collapsed ? "Hồ sơ & Nghiệp vụ" : "•••"}
        </div>

        {allowedNav.map((item) => {
          const isActive =
            location.pathname === item.path ||
            (item.path !== "/" && location.pathname.startsWith(item.path));
          const Icon = item.icon;

          return (
            <Link
              key={item.path}
              to={item.path}
              title={collapsed ? item.label : undefined}
              className={`flex items-center gap-3 px-3 py-2 rounded-md text-xs font-medium transition-colors relative group ${
                isActive
                  ? "bg-white/10 text-white font-semibold border-l-2 border-sky-400 shadow-sm"
                  : "text-slate-400 hover:text-slate-100 hover:bg-white/5 border-l-2 border-transparent"
              }`}
            >
              <Icon
                size={17}
                className={`shrink-0 transition-colors ${
                  isActive ? "text-sky-400" : "text-slate-400 group-hover:text-slate-200"
                }`}
              />

              {!collapsed && (
                <span className="flex-1 truncate tracking-normal">
                  {item.label}
                </span>
              )}

              {!collapsed && item.badge && (
                <span className="text-[10px] font-bold px-1.5 py-0.5 rounded bg-sky-950/80 text-sky-300 border border-sky-800/60 leading-none">
                  {item.badge}
                </span>
              )}
            </Link>
          );
        })}
      </nav>

      {/* Footer System Info */}
      {!collapsed && (
        <div className="p-3 m-2.5 rounded-md bg-white/[0.03] border border-white/5 text-slate-400">
          <div className="text-[11px] font-semibold text-slate-300">
            Kho lưu trữ số CTSV
          </div>
          <div className="text-[10px] text-slate-500 mt-0.5">
            Trường Đại học Đà Lạt
          </div>
        </div>
      )}
    </aside>
  );
};
