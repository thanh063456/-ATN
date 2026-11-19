import React, { useState } from "react";
import { Users, UserPlus, Shield, UserCheck, ToggleLeft, ToggleRight, Search, Edit2 } from "lucide-react";
import { Card } from "../components/common/Card";
import { Button } from "../components/common/Button";
import { Badge } from "../components/common/Badge";
import { useToastStore } from "../stores/useToastStore";

interface UserItem {
  id: string;
  username: string;
  fullName: string;
  email: string;
  role: "ADMIN" | "STAFF" | "STUDENT";
  isActive: boolean;
  lastLogin: string;
}

export const UserManagementPage: React.FC = () => {
  const { addToast } = useToastStore();
  const [search, setSearch] = useState("");
  const [showAddModal, setShowAddModal] = useState(false);

  // Form states for modal
  const [newUsername, setNewUsername] = useState("");
  const [newFullName, setNewFullName] = useState("");
  const [newEmail, setNewEmail] = useState("");
  const [newRole, setNewRole] = useState<"ADMIN" | "STAFF" | "STUDENT">("STAFF");

  const [users, setUsers] = useState<UserItem[]>([
    {
      id: "1",
      username: "admin_hethong",
      fullName: "Quản trị viên Hệ thống",
      email: "admin@student-ocr.edu.vn",
      role: "ADMIN",
      isActive: true,
      lastLogin: "27/08/2026 14:10",
    },
    {
      id: "2",
      username: "canbo_ctsv",
      fullName: "Nguyễn Văn Tuấn",
      email: "tuannv@hust.edu.vn",
      role: "STAFF",
      isActive: true,
      lastLogin: "27/08/2026 14:32",
    },
    {
      id: "3",
      username: "troly_hoso",
      fullName: "Lê Thị Hồng Nhung",
      email: "nhunglth@hust.edu.vn",
      role: "STAFF",
      isActive: true,
      lastLogin: "26/08/2026 17:05",
    },
    {
      id: "4",
      username: "20210678",
      fullName: "Nguyễn Hoàng Nam",
      email: "nam.nh210678@sis.hust.edu.vn",
      role: "STUDENT",
      isActive: true,
      lastLogin: "27/08/2026 10:15",
    },
  ]);

  const handleToggleStatus = (id: string) => {
    setUsers((prev) =>
      prev.map((u) => {
        if (u.id === id) {
          const next = !u.isActive;
          addToast({
            type: next ? "success" : "warning",
            title: next ? "Đã kích hoạt tài khoản" : "Đã vô hiệu hóa tài khoản",
            message: `Người dùng: ${u.username}`,
          });
          return { ...u, isActive: next };
        }
        return u;
      })
    );
  };

  const handleAddUser = (e: React.FormEvent) => {
    e.preventDefault();
    if (!newUsername || !newFullName || !newEmail) return;

    const newUser: UserItem = {
      id: Math.random().toString(),
      username: newUsername.trim(),
      fullName: newFullName.trim(),
      email: newEmail.trim(),
      role: newRole,
      isActive: true,
      lastLogin: "Chưa đăng nhập",
    };

    setUsers([newUser, ...users]);
    setShowAddModal(false);
    setNewUsername("");
    setNewFullName("");
    setNewEmail("");

    addToast({
      type: "success",
      title: "Thêm người dùng thành công",
      message: `Đã tạo tài khoản ${newUser.username} với vai trò ${newUser.role}.`,
    });
  };

  const filteredUsers = users.filter(
    (u) =>
      u.username.toLowerCase().includes(search.toLowerCase()) ||
      u.fullName.toLowerCase().includes(search.toLowerCase()) ||
      u.email.toLowerCase().includes(search.toLowerCase())
  );

  return (
    <div className="animate-fade-in" style={{ display: "flex", flexDirection: "column", gap: "1.5rem" }}>
      {/* Header */}
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
        <div>
          <h1 style={{ fontSize: "1.5rem", fontWeight: 800, color: "var(--gray-900)" }}>
            Quản trị Người dùng & Phân quyền
          </h1>
          <p style={{ fontSize: "0.875rem", color: "var(--gray-500)", marginTop: "0.25rem" }}>
            Quản lý tài khoản cán bộ phòng CTSV, giảng viên và sinh viên sử dụng hệ thống.
          </p>
        </div>
        <Button variant="primary" leftIcon={<UserPlus size={16} />} onClick={() => setShowAddModal(true)}>
          + Thêm người dùng
        </Button>
      </div>

      {/* Filter */}
      <Card padding="sm">
        <div style={{ position: "relative", maxWidth: "360px" }}>
          <Search size={16} color="var(--gray-400)" style={{ position: "absolute", left: "0.75rem", top: "50%", transform: "translateY(-50%)" }} />
          <input
            type="text"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Tìm theo username, họ tên hoặc email..."
            style={{ width: "100%", padding: "0.45rem 0.75rem 0.45rem 2.2rem", borderRadius: "var(--radius-sm)", border: "1px solid var(--border-color)", fontSize: "0.8125rem" }}
          />
        </div>
      </Card>

      {/* Users Table */}
      <Card padding="none">
        <div style={{ overflowX: "auto" }}>
          <table style={{ width: "100%", borderCollapse: "collapse", fontSize: "0.8125rem" }}>
            <thead>
              <tr style={{ backgroundColor: "var(--gray-50)", borderBottom: "1px solid var(--border-color)", color: "var(--gray-500)", fontWeight: 600, textAlign: "left" }}>
                <th style={{ padding: "0.85rem 1.25rem" }}>Tên đăng nhập</th>
                <th style={{ padding: "0.85rem 1rem" }}>Họ và tên</th>
                <th style={{ padding: "0.85rem 1rem" }}>Email</th>
                <th style={{ padding: "0.85rem 1rem" }}>Vai trò (Role)</th>
                <th style={{ padding: "0.85rem 1rem" }}>Trạng thái</th>
                <th style={{ padding: "0.85rem 1rem" }}>Lần đăng nhập cuối</th>
                <th style={{ padding: "0.85rem 1.25rem", textAlign: "right" }}>Thao tác</th>
              </tr>
            </thead>
            <tbody>
              {filteredUsers.map((u) => (
                <tr key={u.id} style={{ borderBottom: "1px solid var(--border-light)" }}>
                  <td style={{ padding: "0.85rem 1.25rem", fontWeight: 700, color: "var(--gray-900)" }}>
                    {u.username}
                  </td>
                  <td style={{ padding: "0.85rem 1rem", color: "var(--gray-800)" }}>
                    {u.fullName}
                  </td>
                  <td style={{ padding: "0.85rem 1rem", color: "var(--gray-500)" }}>
                    {u.email}
                  </td>
                  <td style={{ padding: "0.85rem 1rem" }}>
                    <Badge variant={u.role === "ADMIN" ? "primary" : u.role === "STAFF" ? "success" : "warning"}>
                      {u.role}
                    </Badge>
                  </td>
                  <td style={{ padding: "0.85rem 1rem" }}>
                    {u.isActive ? (
                      <span style={{ color: "#16a34a", fontWeight: 600 }}>Hoạt động</span>
                    ) : (
                      <span style={{ color: "#dc2626", fontWeight: 600 }}>Đã khóa</span>
                    )}
                  </td>
                  <td style={{ padding: "0.85rem 1rem", color: "var(--gray-400)", fontSize: "0.75rem" }}>
                    {u.lastLogin}
                  </td>
                  <td style={{ padding: "0.85rem 1.25rem", textAlign: "right" }}>
                    <Button
                      variant={u.isActive ? "outline" : "secondary"}
                      size="sm"
                      onClick={() => handleToggleStatus(u.id)}
                    >
                      {u.isActive ? "Khóa" : "Kích hoạt"}
                    </Button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Card>

      {/* Add User Modal */}
      {showAddModal && (
        <div
          style={{
            position: "fixed",
            top: 0,
            left: 0,
            right: 0,
            bottom: 0,
            backgroundColor: "rgba(15, 23, 42, 0.6)",
            backdropFilter: "blur(4px)",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            zIndex: 999,
            padding: "1.5rem",
          }}
        >
          <div
            className="animate-fade-in"
            style={{
              width: "100%",
              maxWidth: "480px",
              backgroundColor: "#ffffff",
              borderRadius: "var(--radius-xl)",
              boxShadow: "var(--shadow-xl)",
              padding: "2rem",
            }}
          >
            <h2 style={{ fontSize: "1.25rem", fontWeight: 700, color: "var(--gray-900)", marginBottom: "1.25rem" }}>
              Thêm người dùng mới
            </h2>

            <form onSubmit={handleAddUser} style={{ display: "flex", flexDirection: "column", gap: "1rem" }}>
              <div>
                <label style={{ display: "block", fontSize: "0.8125rem", fontWeight: 600, color: "var(--gray-700)", marginBottom: "0.3rem" }}>
                  Tên đăng nhập (Username)
                </label>
                <input
                  type="text"
                  required
                  value={newUsername}
                  onChange={(e) => setNewUsername(e.target.value)}
                  placeholder="vd: canbo_nguyenvanb"
                  style={{ width: "100%", padding: "0.55rem 0.85rem", borderRadius: "var(--radius-md)", border: "1px solid var(--border-color)", fontSize: "0.875rem" }}
                />
              </div>

              <div>
                <label style={{ display: "block", fontSize: "0.8125rem", fontWeight: 600, color: "var(--gray-700)", marginBottom: "0.3rem" }}>
                  Họ và tên đầy đủ
                </label>
                <input
                  type="text"
                  required
                  value={newFullName}
                  onChange={(e) => setNewFullName(e.target.value)}
                  placeholder="vd: Nguyễn Văn B"
                  style={{ width: "100%", padding: "0.55rem 0.85rem", borderRadius: "var(--radius-md)", border: "1px solid var(--border-color)", fontSize: "0.875rem" }}
                />
              </div>

              <div>
                <label style={{ display: "block", fontSize: "0.8125rem", fontWeight: 600, color: "var(--gray-700)", marginBottom: "0.3rem" }}>
                  Email
                </label>
                <input
                  type="email"
                  required
                  value={newEmail}
                  onChange={(e) => setNewEmail(e.target.value)}
                  placeholder="vd: bnv@hust.edu.vn"
                  style={{ width: "100%", padding: "0.55rem 0.85rem", borderRadius: "var(--radius-md)", border: "1px solid var(--border-color)", fontSize: "0.875rem" }}
                />
              </div>

              <div>
                <label style={{ display: "block", fontSize: "0.8125rem", fontWeight: 600, color: "var(--gray-700)", marginBottom: "0.3rem" }}>
                  Vai trò (Role)
                </label>
                <select
                  value={newRole}
                  onChange={(e) => setNewRole(e.target.value as any)}
                  style={{ width: "100%", padding: "0.55rem 0.85rem", borderRadius: "var(--radius-md)", border: "1px solid var(--border-color)", fontSize: "0.875rem" }}
                >
                  <option value="STAFF">Cán bộ CTSV (STAFF)</option>
                  <option value="ADMIN">Quản trị viên (ADMIN)</option>
                  <option value="STUDENT">Sinh viên (STUDENT)</option>
                </select>
              </div>

              <div style={{ display: "flex", justifyContent: "flex-end", gap: "0.75rem", marginTop: "1rem" }}>
                <Button type="button" variant="outline" onClick={() => setShowAddModal(false)}>
                  Hủy
                </Button>
                <Button type="submit" variant="primary">
                  Tạo tài khoản
                </Button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
