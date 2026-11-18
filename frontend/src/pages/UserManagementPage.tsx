import React, { useEffect, useState } from "react";
import { UserPlus, Search, RefreshCw, Shield, Users, GraduationCap, Lock, CheckCircle2 } from "lucide-react";
import { Card } from "../components/common/Card";
import { Button } from "../components/common/Button";
import { Badge } from "../components/common/Badge";
import { authApi, UserAdminItem } from "../api/auth";
import { useToastStore } from "../stores/useToastStore";

export const UserManagementPage: React.FC = () => {
  const { addToast } = useToastStore();
  const [search, setSearch] = useState("");
  const [roleFilter, setRoleFilter] = useState<string>("ALL");
  const [showAddModal, setShowAddModal] = useState(false);
  const [isLoading, setIsLoading] = useState(true);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [togglingId, setTogglingId] = useState<string | null>(null);

  // Form states for modal
  const [newUsername, setNewUsername] = useState("");
  const [newFullName, setNewFullName] = useState("");
  const [newEmail, setNewEmail] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [newRole, setNewRole] = useState<"ADMIN" | "STAFF" | "STUDENT">("STAFF");
  const [newMssv, setNewMssv] = useState("");

  const [users, setUsers] = useState<UserAdminItem[]>([]);

  const loadUsers = async () => {
    setIsLoading(true);
    try {
      const data = await authApi.getAllUsers();
      setUsers(data);
    } catch (err: any) {
      addToast({
        type: "error",
        title: "Không thể tải danh sách người dùng",
        message: err?.response?.data?.message || err.message || "Vui lòng kiểm tra kết nối với Supabase.",
      });
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    loadUsers();
  }, []);

  const handleToggleStatus = async (id: string, currentStatus: boolean, username: string) => {
    setTogglingId(id);
    try {
      await authApi.toggleUserStatus(id);
      setUsers((prev) =>
        prev.map((u) => (u.id === id ? { ...u, isActive: !currentStatus } : u))
      );
      addToast({
        type: !currentStatus ? "success" : "warning",
        title: !currentStatus ? "Đã kích hoạt tài khoản" : "Đã vô hiệu hóa tài khoản",
        message: `Người dùng: ${username}`,
      });
    } catch (err: any) {
      addToast({
        type: "error",
        title: "Lỗi cập nhật trạng thái",
        message: err.response?.data?.message || err.message || "Không thể cập nhật trạng thái.",
      });
    } finally {
      setTogglingId(null);
    }
  };

  const handleAddUser = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newUsername || !newFullName || !newEmail) return;

    setIsSubmitting(true);
    try {
      const created = await authApi.createUserByAdmin({
        username: newUsername.trim(),
        full_name: newFullName.trim(),
        email: newEmail.trim().toLowerCase(),
        password: newPassword || "Dlu@123456",
        role: newRole,
        mssv: newMssv.trim() || undefined,
      });

      setUsers((prev) => [created, ...prev]);
      setShowAddModal(false);
      setNewUsername("");
      setNewFullName("");
      setNewEmail("");
      setNewPassword("");
      setNewMssv("");

      addToast({
        type: "success",
        title: "Thêm người dùng thành công",
        message: `Đã tạo tài khoản ${created.username} trên Supabase.`,
      });
    } catch (err: any) {
      addToast({
        type: "error",
        title: "Không thể tạo tài khoản",
        message: err.response?.data?.message || err.message || "Vui lòng kiểm tra lại thông tin.",
      });
    } finally {
      setIsSubmitting(false);
    }
  };

  const filteredUsers = users.filter((u) => {
    const matchesSearch =
      u.username.toLowerCase().includes(search.toLowerCase()) ||
      u.fullName.toLowerCase().includes(search.toLowerCase()) ||
      u.email.toLowerCase().includes(search.toLowerCase()) ||
      (u.mssv && u.mssv.toLowerCase().includes(search.toLowerCase()));

    const matchesRole = roleFilter === "ALL" || u.role === roleFilter;

    return matchesSearch && matchesRole;
  });

  const totalUsers = users.length;
  const adminCount = users.filter((u) => u.role === "ADMIN").length;
  const staffCount = users.filter((u) => u.role === "STAFF").length;
  const studentCount = users.filter((u) => u.role === "STUDENT").length;

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Header */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <div>
          <h1 className="text-xl sm:text-2xl font-bold text-slate-900 tracking-tight">
            Quản trị Người dùng & Phân quyền
          </h1>
          <p className="text-xs sm:text-sm text-slate-500 mt-1">
            Đồng bộ thời gian thực từ cơ sở dữ liệu Supabase: Quản lý tài khoản quản trị, cán bộ CTSV và sinh viên.
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={loadUsers}
            isLoading={isLoading}
            leftIcon={<RefreshCw size={14} className={isLoading ? "animate-spin" : ""} />}
          >
            Làm mới
          </Button>
          <Button variant="primary" size="sm" leftIcon={<UserPlus size={16} />} onClick={() => setShowAddModal(true)}>
            Thêm người dùng
          </Button>
        </div>
      </div>

      {/* KPI Stats Bar */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-3 sm:gap-4">
        <div className="bg-white p-4 rounded-lg border border-slate-200/90 border-l-4 border-l-dlu-navy-900 shadow-paper">
          <span className="text-[11px] font-bold text-slate-500 uppercase tracking-wider flex items-center gap-1.5">
            <Users size={13} className="text-dlu-navy-700" /> Tổng người dùng
          </span>
          <div className="text-2xl font-extrabold text-dlu-navy-900 mt-1">
            {isLoading ? "..." : totalUsers}
          </div>
          <span className="text-[11px] text-slate-500">Tài khoản trên hệ thống Supabase</span>
        </div>

        <div className="bg-white p-4 rounded-lg border border-slate-200/90 border-l-4 border-l-rose-600 shadow-paper">
          <span className="text-[11px] font-bold text-slate-500 uppercase tracking-wider flex items-center gap-1.5">
            <Shield size={13} className="text-rose-600" /> Quản trị viên (ADMIN)
          </span>
          <div className="text-2xl font-extrabold text-rose-700 mt-1">
            {isLoading ? "..." : adminCount}
          </div>
          <span className="text-[11px] text-slate-500">Toàn quyền cấu hình & duyệt</span>
        </div>

        <div className="bg-white p-4 rounded-lg border border-slate-200/90 border-l-4 border-l-amber-500 shadow-paper">
          <span className="text-[11px] font-bold text-slate-500 uppercase tracking-wider flex items-center gap-1.5">
            <Lock size={13} className="text-amber-600" /> Cán bộ CTSV (STAFF)
          </span>
          <div className="text-2xl font-extrabold text-amber-700 mt-1">
            {isLoading ? "..." : staffCount}
          </div>
          <span className="text-[11px] text-slate-500">Tiếp nhận & đối soát OCR</span>
        </div>

        <div className="bg-white p-4 rounded-lg border border-slate-200/90 border-l-4 border-l-sky-500 shadow-paper">
          <span className="text-[11px] font-bold text-slate-500 uppercase tracking-wider flex items-center gap-1.5">
            <GraduationCap size={13} className="text-sky-600" /> Sinh viên (STUDENT)
          </span>
          <div className="text-2xl font-extrabold text-sky-700 mt-1">
            {isLoading ? "..." : studentCount}
          </div>
          <span className="text-[11px] text-slate-500">Nộp đơn từ & tra cứu hồ sơ</span>
        </div>
      </div>

      {/* Filter Bar */}
      <Card padding="sm">
        <div className="flex flex-col sm:flex-row items-center justify-between gap-3">
          <div className="relative w-full sm:max-w-md">
            <Search size={15} className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
            <input
              type="text"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Tìm theo username, họ tên, email hoặc MSSV..."
              className="w-full pl-9 pr-3 py-1.5 rounded-md border border-slate-200 text-xs bg-slate-50/70 text-slate-900 placeholder-slate-400 focus:bg-white focus:ring-2 focus:ring-dlu-navy-500/20 focus:border-dlu-navy-600 outline-none"
            />
          </div>

          <div className="flex items-center gap-2 w-full sm:w-auto">
            <span className="text-xs text-slate-500 shrink-0 font-medium">Lọc theo vai trò:</span>
            <select
              value={roleFilter}
              onChange={(e) => setRoleFilter(e.target.value)}
              className="px-2.5 py-1.5 rounded-md border border-slate-200 text-xs bg-white text-slate-800 outline-none focus:ring-2 focus:ring-dlu-navy-500/20 focus:border-dlu-navy-600 font-medium"
            >
              <option value="ALL">Tất cả vai trò ({totalUsers})</option>
              <option value="ADMIN">Quản trị viên (ADMIN)</option>
              <option value="STAFF">Cán bộ CTSV (STAFF)</option>
              <option value="STUDENT">Sinh viên (STUDENT)</option>
            </select>
          </div>
        </div>
      </Card>

      {/* Users Table */}
      <Card padding="none">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs min-w-[900px]">
            <thead>
              <tr className="bg-slate-50/90 border-b border-slate-200/80 text-slate-500 font-semibold uppercase tracking-wider text-[11px] whitespace-nowrap">
                <th className="px-5 py-3.5">Tên đăng nhập</th>
                <th className="px-4 py-3.5">Họ và tên</th>
                <th className="px-4 py-3.5">Email</th>
                <th className="px-4 py-3.5">MSSV</th>
                <th className="px-4 py-3.5">Vai trò (Role)</th>
                <th className="px-4 py-3.5">Trạng thái</th>
                <th className="px-4 py-3.5">Lần đăng nhập cuối</th>
                <th className="px-5 py-3.5 text-right whitespace-nowrap">Thao tác</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {isLoading ? (
                <tr>
                  <td colSpan={8} className="py-12 text-center text-slate-400">
                    <RefreshCw className="animate-spin inline-block mr-2" size={18} />
                    Đang nạp danh sách tài khoản từ cơ sở dữ liệu Supabase...
                  </td>
                </tr>
              ) : filteredUsers.length === 0 ? (
                <tr>
                  <td colSpan={8} className="py-12 text-center text-slate-400">
                    Không tìm thấy tài khoản người dùng phù hợp.
                  </td>
                </tr>
              ) : (
                filteredUsers.map((u) => (
                  <tr key={u.id} className="hover:bg-slate-50/80 transition-colors">
                    <td className="px-5 py-3.5 font-bold font-mono text-slate-900">
                      {u.username}
                    </td>
                    <td className="px-4 py-3.5 font-medium text-slate-800">
                      {u.fullName}
                    </td>
                    <td className="px-4 py-3.5 text-slate-500 font-mono">
                      {u.email}
                    </td>
                    <td className="px-4 py-3.5 text-slate-600 font-mono">
                      {u.mssv || "—"}
                    </td>
                    <td className="px-4 py-3.5 whitespace-nowrap">
                      <Badge variant={u.role === "ADMIN" ? "danger" : u.role === "STAFF" ? "warning" : "info"}>
                        {u.role}
                      </Badge>
                    </td>
                    <td className="px-4 py-3.5 whitespace-nowrap">
                      {u.isActive ? (
                        <span className="text-emerald-700 font-semibold inline-flex items-center gap-1">
                          <span className="w-1.5 h-1.5 rounded-full bg-emerald-600" />
                          Hoạt động
                        </span>
                      ) : (
                        <span className="text-rose-700 font-semibold inline-flex items-center gap-1">
                          <span className="w-1.5 h-1.5 rounded-full bg-rose-600" />
                          Đã khóa
                        </span>
                      )}
                    </td>
                    <td className="px-4 py-3.5 text-slate-400 font-mono text-[11px] whitespace-nowrap">
                      {u.lastLogin}
                    </td>
                    <td className="px-5 py-3.5 text-right whitespace-nowrap">
                      <Button
                        variant={u.isActive ? "outline" : "secondary"}
                        size="sm"
                        isLoading={togglingId === u.id}
                        onClick={() => handleToggleStatus(u.id, u.isActive, u.username)}
                      >
                        {u.isActive ? "Khóa" : "Kích hoạt"}
                      </Button>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </Card>

      {/* Add User Modal */}
      {showAddModal && (
        <div className="fixed inset-0 bg-slate-900/50 backdrop-blur-xs flex items-center justify-center z-50 p-4 animate-fade-in">
          <div className="bg-white rounded-lg shadow-modal border border-slate-200/90 w-full max-w-md p-6">
            <h2 className="text-lg font-bold text-slate-900 mb-1">
              Thêm người dùng mới
            </h2>
            <p className="text-xs text-slate-500 mb-4">
              Tạo tài khoản và đồng bộ trực tiếp vào cơ sở dữ liệu Supabase.
            </p>

            <form onSubmit={handleAddUser} className="space-y-3.5">
              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">
                  Tên đăng nhập (Username) *
                </label>
                <input
                  type="text"
                  required
                  value={newUsername}
                  onChange={(e) => setNewUsername(e.target.value)}
                  placeholder="vd: canbo_tuannv hoặc 2212461"
                  className="w-full px-3 py-2 rounded-md border border-slate-200 text-xs sm:text-sm bg-white text-slate-900 outline-none focus:ring-2 focus:ring-dlu-navy-500/20 focus:border-dlu-navy-600"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">
                  Họ và tên đầy đủ *
                </label>
                <input
                  type="text"
                  required
                  value={newFullName}
                  onChange={(e) => setNewFullName(e.target.value)}
                  placeholder="vd: Nguyễn Văn Tuấn"
                  className="w-full px-3 py-2 rounded-md border border-slate-200 text-xs sm:text-sm bg-white text-slate-900 outline-none focus:ring-2 focus:ring-dlu-navy-500/20 focus:border-dlu-navy-600"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">
                  Email (@dlu.edu.vn) *
                </label>
                <input
                  type="email"
                  required
                  value={newEmail}
                  onChange={(e) => setNewEmail(e.target.value)}
                  placeholder="vd: tuannv@dlu.edu.vn"
                  className="w-full px-3 py-2 rounded-md border border-slate-200 text-xs sm:text-sm bg-white text-slate-900 outline-none focus:ring-2 focus:ring-dlu-navy-500/20 focus:border-dlu-navy-600"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">
                  Mật khẩu khởi tạo (Mặc định: Dlu@123456)
                </label>
                <input
                  type="password"
                  value={newPassword}
                  onChange={(e) => setNewPassword(e.target.value)}
                  placeholder="Để trống để dùng mật khẩu mặc định"
                  className="w-full px-3 py-2 rounded-md border border-slate-200 text-xs sm:text-sm bg-white text-slate-900 outline-none focus:ring-2 focus:ring-dlu-navy-500/20 focus:border-dlu-navy-600"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-semibold text-slate-700 mb-1">
                    Vai trò (Role)
                  </label>
                  <select
                    value={newRole}
                    onChange={(e) => setNewRole(e.target.value as any)}
                    className="w-full px-3 py-2 rounded-md border border-slate-200 text-xs sm:text-sm bg-white text-slate-900 outline-none focus:ring-2 focus:ring-dlu-navy-500/20 focus:border-dlu-navy-600"
                  >
                    <option value="STAFF">Cán bộ CTSV (STAFF)</option>
                    <option value="ADMIN">Quản trị viên (ADMIN)</option>
                    <option value="STUDENT">Sinh viên (STUDENT)</option>
                  </select>
                </div>

                <div>
                  <label className="block text-xs font-semibold text-slate-700 mb-1">
                    Mã số sinh viên (MSSV)
                  </label>
                  <input
                    type="text"
                    value={newMssv}
                    onChange={(e) => setNewMssv(e.target.value)}
                    placeholder="Chỉ dành cho STUDENT"
                    disabled={newRole !== "STUDENT"}
                    className="w-full px-3 py-2 rounded-md border border-slate-200 text-xs sm:text-sm bg-white text-slate-900 outline-none focus:ring-2 focus:ring-dlu-navy-500/20 focus:border-dlu-navy-600 disabled:bg-slate-100 disabled:text-slate-400"
                  />
                </div>
              </div>

              <div className="flex justify-end gap-2.5 pt-4 border-t border-slate-100">
                <Button type="button" variant="outline" onClick={() => setShowAddModal(false)} disabled={isSubmitting}>
                  Hủy
                </Button>
                <Button type="submit" variant="primary" isLoading={isSubmitting}>
                  Tạo tài khoản Supabase
                </Button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
