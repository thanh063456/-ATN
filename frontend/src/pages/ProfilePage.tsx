import React, { useState, useEffect, useMemo } from "react";
import { Link } from "react-router-dom";
import {
  User,
  Mail,
  GraduationCap,
  ShieldCheck,
  FileText,
  Calendar,
  Clock,
  Search,
  CheckCircle2,
  Building2,
  ExternalLink,
  Save,
  RefreshCw,
  Award,
  Layers,
  FileSearch,
} from "lucide-react";
import { Card } from "../components/common/Card";
import { Button } from "../components/common/Button";
import { Badge, OCRStatusBadge } from "../components/common/Badge";
import { useAuthStore } from "../stores/useAuthStore";
import { useToastStore } from "../stores/useToastStore";
import { authApi } from "../api/auth";
import { documentsApi, DocumentListItem } from "../api/documents";

export const ProfilePage: React.FC = () => {
  const { user, updateProfile } = useAuthStore();
  const { addToast } = useToastStore();

  const [fullName, setFullName] = useState(user?.fullName || "");
  const [mssv, setMssv] = useState(user?.mssv || "");
  const [isSaving, setIsSaving] = useState(false);
  const [isLoadingDocs, setIsLoadingDocs] = useState(false);
  const [userDocs, setUserDocs] = useState<DocumentListItem[]>([]);
  const [searchDocTerm, setSearchDocTerm] = useState("");
  const [activeTab, setActiveTab] = useState<"DOCS" | "INFO">("DOCS");

  // Đồng bộ lại state khi user store cập nhật
  useEffect(() => {
    if (user) {
      setFullName(user.fullName || "");
      setMssv(user.mssv || "");
    }
  }, [user]);

  // Tải danh sách hồ sơ do người dùng tải lên hoặc gắn với MSSV này
  const fetchMyDocuments = async () => {
    setIsLoadingDocs(true);
    try {
      const res = await documentsApi.list({
        pageSize: 100,
      });
      // Lọc các hồ sơ do user này tải lên hoặc khớp MSSV
      const myItems = (res.items || []).filter((d) => {
        if (user?.id && d.uploaded_by === user.id) return true;
        if (user?.mssv && (d.student_id === user.mssv || d.uploader_mssv === user.mssv)) return true;
        if (user?.username && d.uploader_name?.toLowerCase().includes(user.username.toLowerCase())) return true;
        return false;
      });
      setUserDocs(myItems);
    } catch {
      // ignore
    } finally {
      setIsLoadingDocs(false);
    }
  };

  useEffect(() => {
    fetchMyDocuments();
  }, [user?.id, user?.mssv]);

  // Lưu thông tin cá nhân
  const handleSaveProfile = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!fullName.trim()) {
      addToast({ type: "error", title: "Lỗi", message: "Họ và tên không được để trống" });
      return;
    }

    setIsSaving(true);
    try {
      const updated = await authApi.updateProfile({
        full_name: fullName.trim(),
        mssv: mssv.trim() || undefined,
      });

      updateProfile({
        fullName: updated.full_name,
        mssv: updated.mssv,
      });

      addToast({
        type: "success",
        title: "Thành công",
        message: "Thông tin hồ sơ cá nhân đã được cập nhật.",
      });
    } catch (err: any) {
      addToast({
        type: "error",
        title: "Lỗi cập nhật",
        message: err.message || "Không thể cập nhật hồ sơ cá nhân",
      });
    } finally {
      setIsSaving(false);
    }
  };

  // Lọc và sắp xếp hồ sơ cá nhân theo thời gian thực upload (mới nhất lên đầu)
  const filteredDocs = useMemo(() => {
    return userDocs
      .filter((d) => {
        if (!searchDocTerm.trim()) return true;
        const q = searchDocTerm.toLowerCase().trim();
        return (
          d.title.toLowerCase().includes(q) ||
          (d.student_id && d.student_id.toLowerCase().includes(q)) ||
          (d.document_number && d.document_number.toLowerCase().includes(q)) ||
          (d.category_name && d.category_name.toLowerCase().includes(q))
        );
      })
      .sort((a, b) => {
        const tA = a.created_at ? new Date(a.created_at).getTime() : 0;
        const tB = b.created_at ? new Date(b.created_at).getTime() : 0;
        return tB - tA;
      });
  }, [userDocs, searchDocTerm]);

  // Thống kê nhanh
  const approvedDocsCount = userDocs.filter((d) => d.ocr_status === "APPROVED").length;
  const doneDocsCount = userDocs.filter((d) => d.ocr_status === "DONE" || d.ocr_status === "APPROVED").length;

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
        return "Quản trị viên Hệ thống (ADMIN)";
      case "STAFF":
        return "Cán bộ Phòng CTSV (STAFF)";
      default:
        return "Sinh viên Đại học Đà Lạt (STUDENT)";
    }
  };

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "1.5rem" }}>
      {/* 1. Header Profile Banner */}
      <Card
        padding="lg"
        style={{
          background: "linear-gradient(135deg, #1e3a8a 0%, #172554 100%)",
          color: "#ffffff",
          borderRadius: "var(--radius-lg)",
          boxShadow: "0 10px 25px -5px rgba(30, 58, 138, 0.3)",
        }}
      >
        <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", flexWrap: "wrap", gap: "1.5rem" }}>
          <div style={{ display: "flex", alignItems: "center", gap: "1.25rem" }}>
            <div
              style={{
                width: "72px",
                height: "72px",
                borderRadius: "50%",
                backgroundColor: "rgba(255, 255, 255, 0.15)",
                backdropFilter: "blur(8px)",
                color: "#93c5fd",
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                fontSize: "1.875rem",
                fontWeight: 700,
                border: "2px solid rgba(255, 255, 255, 0.3)",
                boxShadow: "0 4px 12px rgba(0, 0, 0, 0.15)",
              }}
            >
              {user?.fullName?.charAt(0) || "U"}
            </div>
            <div>
              <div style={{ display: "flex", alignItems: "center", gap: "0.6rem", flexWrap: "wrap" }}>
                <h1 style={{ fontSize: "1.5rem", fontWeight: 700, margin: 0, color: "#f8fafc" }}>
                  {user?.fullName || "Chưa đặt tên"}
                </h1>
                <Badge variant={getRoleBadgeVariant()}>{user?.role || "STUDENT"}</Badge>
              </div>
              <p style={{ margin: "0.25rem 0 0", fontSize: "0.875rem", color: "#bfdbfe", display: "flex", alignItems: "center", gap: "0.4rem" }}>
                <Building2 size={15} />
                <span>Trường Đại học Đà Lạt • Phòng Công tác Sinh viên (CTSV)</span>
              </p>
              <div style={{ display: "flex", gap: "1rem", marginTop: "0.5rem", flexWrap: "wrap", fontSize: "0.8125rem", color: "#e2e8f0" }}>
                <span style={{ display: "flex", alignItems: "center", gap: "0.35rem" }}>
                  <Mail size={14} color="#93c5fd" /> {user?.email}
                </span>
                {user?.mssv && (
                  <span style={{ display: "flex", alignItems: "center", gap: "0.35rem" }}>
                    <GraduationCap size={14} color="#93c5fd" /> MSSV: <strong>{user.mssv}</strong>
                  </span>
                )}
                <span style={{ display: "flex", alignItems: "center", gap: "0.35rem" }}>
                  <ShieldCheck size={14} color="#4ade80" /> Trạng thái: Đã xác thực
                </span>
              </div>
            </div>
          </div>

          {/* Quick link button to search by this MSSV/Name */}
          <div style={{ display: "flex", gap: "0.6rem" }}>
            <Link
              to={`/search?q=${encodeURIComponent(user?.mssv || user?.fullName || "")}`}
              style={{ textDecoration: "none" }}
            >
              <Button
                variant="outline"
                size="sm"
                leftIcon={<FileSearch size={15} />}
                style={{
                  backgroundColor: "rgba(255, 255, 255, 0.1)",
                  borderColor: "rgba(255, 255, 255, 0.3)",
                  color: "#ffffff",
                }}
              >
                Tra cứu hồ sơ liên quan
              </Button>
            </Link>
          </div>
        </div>
      </Card>

      {/* 2. Quick Stat Counters */}
      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))", gap: "1rem" }}>
        <Card padding="md">
          <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between" }}>
            <span style={{ fontSize: "0.75rem", fontWeight: 700, color: "var(--gray-500)", textTransform: "uppercase" }}>
              Hồ sơ đã tải lên
            </span>
            <div style={{ padding: "0.35rem", borderRadius: "0.375rem", backgroundColor: "#eff6ff", color: "#2563eb" }}>
              <Layers size={18} />
            </div>
          </div>
          <div style={{ fontSize: "1.75rem", fontWeight: 700, color: "var(--gray-900)", marginTop: "0.4rem" }}>
            {userDocs.length}
          </div>
          <span style={{ fontSize: "0.75rem", color: "var(--gray-500)" }}>Tổng tài liệu đã nạp vào kho</span>
        </Card>

        <Card padding="md">
          <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between" }}>
            <span style={{ fontSize: "0.75rem", fontWeight: 700, color: "var(--gray-500)", textTransform: "uppercase" }}>
              Đã nhận diện OCR
            </span>
            <div style={{ padding: "0.35rem", borderRadius: "0.375rem", backgroundColor: "#f0fdf4", color: "#16a34a" }}>
              <CheckCircle2 size={18} />
            </div>
          </div>
          <div style={{ fontSize: "1.75rem", fontWeight: 700, color: "#16a34a", marginTop: "0.4rem" }}>
            {doneDocsCount}
          </div>
          <span style={{ fontSize: "0.75rem", color: "var(--gray-500)" }}>Hoàn tất trích xuất toàn văn</span>
        </Card>

        <Card padding="md">
          <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between" }}>
            <span style={{ fontSize: "0.75rem", fontWeight: 700, color: "var(--gray-500)", textTransform: "uppercase" }}>
              Đã phê duyệt điện tử
            </span>
            <div style={{ padding: "0.35rem", borderRadius: "0.375rem", backgroundColor: "#fef3c7", color: "#d97706" }}>
              <Award size={18} />
            </div>
          </div>
          <div style={{ fontSize: "1.75rem", fontWeight: 700, color: "#d97706", marginTop: "0.4rem" }}>
            {approvedDocsCount}
          </div>
          <span style={{ fontSize: "0.75rem", color: "var(--gray-500)" }}>Đã ký số và cấp mã QR</span>
        </Card>
      </div>

      {/* 3. Navigation Tabs */}
      <div style={{ borderBottom: "1px solid var(--border-color)", display: "flex", gap: "1rem" }}>
        <button
          onClick={() => setActiveTab("DOCS")}
          style={{
            padding: "0.65rem 1rem",
            background: "none",
            border: "none",
            borderBottom: activeTab === "DOCS" ? "3px solid #1e3a8a" : "3px solid transparent",
            color: activeTab === "DOCS" ? "#1e3a8a" : "var(--gray-500)",
            fontWeight: activeTab === "DOCS" ? 700 : 500,
            fontSize: "0.875rem",
            cursor: "pointer",
            display: "flex",
            alignItems: "center",
            gap: "0.4rem",
          }}
        >
          <FileText size={16} />
          <span>Hồ sơ đã tải lên ({userDocs.length})</span>
        </button>

        <button
          onClick={() => setActiveTab("INFO")}
          style={{
            padding: "0.65rem 1rem",
            background: "none",
            border: "none",
            borderBottom: activeTab === "INFO" ? "3px solid #1e3a8a" : "3px solid transparent",
            color: activeTab === "INFO" ? "#1e3a8a" : "var(--gray-500)",
            fontWeight: activeTab === "INFO" ? 700 : 500,
            fontSize: "0.875rem",
            cursor: "pointer",
            display: "flex",
            alignItems: "center",
            gap: "0.4rem",
          }}
        >
          <User size={16} />
          <span>Thông tin tài khoản & Chỉnh sửa</span>
        </button>
      </div>

      {/* 4. Tab 1: Documents list */}
      {activeTab === "DOCS" && (
        <Card padding="none">
          <div
            style={{
              padding: "1rem 1.25rem",
              display: "flex",
              alignItems: "center",
              justifyContent: "space-between",
              borderBottom: "1px solid var(--border-color)",
              flexWrap: "wrap",
              gap: "0.75rem",
            }}
          >
            <div style={{ display: "flex", alignItems: "center", gap: "0.5rem", flex: 1, maxWidth: "420px" }}>
              <div
                style={{
                  display: "flex",
                  alignItems: "center",
                  gap: "0.5rem",
                  backgroundColor: "var(--gray-50)",
                  border: "1px solid var(--border-color)",
                  borderRadius: "var(--radius-md)",
                  padding: "0.4rem 0.75rem",
                  width: "100%",
                }}
              >
                <Search size={15} color="var(--gray-400)" />
                <input
                  type="text"
                  placeholder="Lọc hồ sơ theo tiêu đề, số hiệu, MSSV..."
                  value={searchDocTerm}
                  onChange={(e) => setSearchDocTerm(e.target.value)}
                  style={{
                    border: "none",
                    outline: "none",
                    backgroundColor: "transparent",
                    fontSize: "0.8125rem",
                    width: "100%",
                  }}
                />
              </div>
            </div>

            <Button
              variant="outline"
              size="sm"
              leftIcon={<RefreshCw size={14} className={isLoadingDocs ? "animate-spin" : ""} />}
              onClick={fetchMyDocuments}
            >
              Làm mới
            </Button>
          </div>

          <div style={{ overflowX: "auto" }}>
            <table style={{ width: "100%", borderCollapse: "collapse", textAlign: "left", fontSize: "0.8125rem" }}>
              <thead>
                <tr style={{ backgroundColor: "var(--gray-50)", borderBottom: "1px solid var(--border-color)", color: "var(--gray-600)", fontWeight: 700 }}>
                  <th style={{ padding: "0.75rem 1.25rem", width: "40%" }}>TIÊU ĐỀ & THÔNG TIN HỒ SƠ</th>
                  <th style={{ padding: "0.75rem 1rem", width: "15%" }}>DANH MỤC</th>
                  <th style={{ padding: "0.75rem 1rem", width: "15%" }}>TRẠNG THÁI OCR</th>
                  <th style={{ padding: "0.75rem 1rem", width: "20%" }}>THỜI GIAN THỰC UPLOAD</th>
                  <th style={{ padding: "0.75rem 1rem", width: "10%", textAlign: "right" }}>THAO TÁC</th>
                </tr>
              </thead>
              <tbody>
                {filteredDocs.length === 0 ? (
                  <tr>
                    <td colSpan={5} style={{ padding: "3rem 1rem", textAlign: "center", color: "var(--gray-400)" }}>
                      <FileText size={36} style={{ margin: "0 auto 0.5rem", opacity: 0.4 }} />
                      <p style={{ fontWeight: 500 }}>Chưa có hồ sơ nào phù hợp.</p>
                      <span style={{ fontSize: "0.75rem" }}>Các tài liệu do bạn tải lên sẽ hiển thị tại đây theo thời gian thực.</span>
                    </td>
                  </tr>
                ) : (
                  filteredDocs.map((doc) => (
                    <tr
                      key={doc.id}
                      style={{ borderBottom: "1px solid var(--border-light)", transition: "background-color 0.15s ease" }}
                      onMouseEnter={(e) => (e.currentTarget.style.backgroundColor = "rgba(243, 244, 246, 0.5)")}
                      onMouseLeave={(e) => (e.currentTarget.style.backgroundColor = "transparent")}
                    >
                      <td style={{ padding: "0.85rem 1.25rem" }}>
                        <div style={{ display: "flex", alignItems: "flex-start", gap: "0.6rem" }}>
                          <span
                            style={{
                              padding: "0.25rem 0.45rem",
                              borderRadius: "0.25rem",
                              backgroundColor: doc.file_type?.toLowerCase() === "pdf" ? "#fee2e2" : "#e0e7ff",
                              color: doc.file_type?.toLowerCase() === "pdf" ? "#dc2626" : "#4338ca",
                              fontWeight: 700,
                              fontSize: "0.6875rem",
                            }}
                          >
                            {doc.file_type || "PDF"}
                          </span>
                          <div>
                            <Link
                              to={`/documents/${doc.id}`}
                              style={{
                                color: "#1e3a8a",
                                fontWeight: 600,
                                textDecoration: "none",
                              }}
                            >
                              {doc.title}
                            </Link>
                            <div style={{ display: "flex", gap: "0.5rem", fontSize: "0.75rem", color: "var(--gray-500)", marginTop: "0.2rem" }}>
                              {doc.document_number && <span>Số: <strong>{doc.document_number}</strong></span>}
                              {doc.student_id && <span>MSSV: <strong>{doc.student_id}</strong></span>}
                              <span>{(doc.file_size_bytes / (1024 * 1024)).toFixed(2)} MB</span>
                            </div>
                          </div>
                        </div>
                      </td>
                      <td style={{ padding: "0.85rem 1rem", color: "var(--gray-700)" }}>
                        {doc.category_name || "Chưa phân loại"}
                      </td>
                      <td style={{ padding: "0.85rem 1rem" }}>
                        <OCRStatusBadge status={doc.ocr_status as any} />
                      </td>
                      <td style={{ padding: "0.85rem 1rem", color: "#1e3a8a", fontWeight: 600 }}>
                        <div style={{ display: "flex", alignItems: "center", gap: "0.35rem" }}>
                          <Clock size={13} color="var(--gray-400)" />
                          <span>
                            {new Date(doc.created_at).toLocaleTimeString("vi-VN", { hour: "2-digit", minute: "2-digit", second: "2-digit" })}{" "}
                            • {new Date(doc.created_at).toLocaleDateString("vi-VN")}
                          </span>
                        </div>
                      </td>
                      <td style={{ padding: "0.85rem 1rem", textAlign: "right" }}>
                        <Link to={`/documents/${doc.id}`} style={{ textDecoration: "none" }}>
                          <Button variant="outline" size="sm" rightIcon={<ExternalLink size={13} />}>
                            Xem
                          </Button>
                        </Link>
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </Card>
      )}

      {/* 5. Tab 2: Personal Information & Settings */}
      {activeTab === "INFO" && (
        <Card padding="lg" style={{ maxWidth: "680px" }}>
          <h2 style={{ fontSize: "1.1rem", fontWeight: 700, margin: "0 0 1.25rem", color: "var(--gray-900)" }}>
            Thông tin Hồ sơ Cá nhân
          </h2>
          <form onSubmit={handleSaveProfile} style={{ display: "flex", flexDirection: "column", gap: "1.2rem" }}>
            <div>
              <label style={{ display: "block", fontSize: "0.8125rem", fontWeight: 600, color: "var(--gray-700)", marginBottom: "0.35rem" }}>
                Họ và tên
              </label>
              <input
                type="text"
                value={fullName}
                onChange={(e) => setFullName(e.target.value)}
                required
                style={{
                  width: "100%",
                  padding: "0.6rem 0.85rem",
                  borderRadius: "var(--radius-md)",
                  border: "1px solid var(--border-color)",
                  fontSize: "0.875rem",
                  outline: "none",
                }}
              />
            </div>

            <div>
              <label style={{ display: "block", fontSize: "0.8125rem", fontWeight: 600, color: "var(--gray-700)", marginBottom: "0.35rem" }}>
                Mã số sinh viên (MSSV) / Mã cán bộ
              </label>
              <input
                type="text"
                value={mssv}
                onChange={(e) => setMssv(e.target.value)}
                placeholder="Ví dụ: 2212461 hoặc để trống nếu là cán bộ chung"
                style={{
                  width: "100%",
                  padding: "0.6rem 0.85rem",
                  borderRadius: "var(--radius-md)",
                  border: "1px solid var(--border-color)",
                  fontSize: "0.875rem",
                  outline: "none",
                }}
              />
              <span style={{ fontSize: "0.75rem", color: "var(--gray-500)", marginTop: "0.25rem", display: "block" }}>
                MSSV giúp hệ thống tự động liên kết các đơn từ, quyết định và hồ sơ khen thưởng / miễn giảm học phí của bạn.
              </span>
            </div>

            <div>
              <label style={{ display: "block", fontSize: "0.8125rem", fontWeight: 600, color: "var(--gray-700)", marginBottom: "0.35rem" }}>
                Địa chỉ Email nhà trường
              </label>
              <input
                type="email"
                value={user?.email || ""}
                disabled
                style={{
                  width: "100%",
                  padding: "0.6rem 0.85rem",
                  borderRadius: "var(--radius-md)",
                  border: "1px solid var(--border-color)",
                  backgroundColor: "var(--gray-100)",
                  color: "var(--gray-500)",
                  fontSize: "0.875rem",
                  cursor: "not-allowed",
                }}
              />
              <span style={{ fontSize: "0.75rem", color: "var(--gray-500)", marginTop: "0.25rem", display: "block" }}>
                Email định danh @dlu.edu.vn được xác thực cố định qua tài khoản nhà trường.
              </span>
            </div>

            <div>
              <label style={{ display: "block", fontSize: "0.8125rem", fontWeight: 600, color: "var(--gray-700)", marginBottom: "0.35rem" }}>
                Vai trò hệ thống
              </label>
              <div style={{ display: "flex", alignItems: "center", gap: "0.5rem" }}>
                <Badge variant={getRoleBadgeVariant()}>{user?.role || "STUDENT"}</Badge>
                <span style={{ fontSize: "0.8125rem", color: "var(--gray-600)" }}>{getRoleLabel()}</span>
              </div>
            </div>

            <div style={{ paddingTop: "0.75rem", borderTop: "1px solid var(--border-color)", display: "flex", justifyContent: "flex-end" }}>
              <Button variant="primary" size="md" type="submit" isLoading={isSaving} leftIcon={<Save size={16} />}>
                Lưu cập nhật
              </Button>
            </div>
          </form>
        </Card>
      )}
    </div>
  );
};

