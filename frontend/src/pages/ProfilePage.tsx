import React, { useState, useEffect, useMemo } from "react";
import { Link } from "react-router-dom";
import {
  User,
  Mail,
  GraduationCap,
  ShieldCheck,
  FileText,
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

  useEffect(() => {
    if (user) {
      setFullName(user.fullName || "");
      setMssv(user.mssv || "");
    }
  }, [user]);

  const fetchMyDocuments = async () => {
    setIsLoadingDocs(true);
    try {
      const res = await documentsApi.list({
        pageSize: 100,
      });
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
    <div className="space-y-6 animate-fade-in">
      {/* 1. Header Profile Banner */}
      <div className="bg-[#0a192f] text-white p-5 sm:p-7 rounded-lg border border-slate-800 shadow-paper">
        <div className="flex items-center justify-between flex-wrap gap-5">
          <div className="flex items-center gap-4 sm:gap-5">
            <div className="w-16 h-16 sm:w-18 sm:h-18 rounded-full bg-dlu-navy-800 text-sky-300 border-2 border-sky-400/30 flex items-center justify-center text-2xl font-bold shadow-sm shrink-0">
              {user?.fullName?.charAt(0) || "U"}
            </div>
            <div>
              <div className="flex items-center gap-2.5 flex-wrap">
                <h1 className="text-xl sm:text-2xl font-bold text-white tracking-tight">
                  {user?.fullName || "Chưa đặt tên"}
                </h1>
                <Badge variant={getRoleBadgeVariant()}>{user?.role || "STUDENT"}</Badge>
              </div>
              <p className="text-slate-300 text-xs sm:text-sm mt-1 flex items-center gap-1.5">
                <Building2 size={14} className="text-sky-400" />
                <span>Trường Đại học Đà Lạt • Phòng Công tác Sinh viên (CTSV)</span>
              </p>
              <div className="flex gap-3 sm:gap-5 mt-2 flex-wrap text-xs text-slate-300">
                <span className="flex items-center gap-1.5">
                  <Mail size={13} className="text-sky-300" /> {user?.email}
                </span>
                {user?.mssv && (
                  <span className="flex items-center gap-1.5">
                    <GraduationCap size={13} className="text-sky-300" /> MSSV: <strong className="font-mono">{user.mssv}</strong>
                  </span>
                )}
                <span className="flex items-center gap-1.5 text-emerald-300">
                  <ShieldCheck size={13} /> Trạng thái: Đã xác thực
                </span>
              </div>
            </div>
          </div>

          <div className="flex gap-2">
            <Link to={`/search?q=${encodeURIComponent(user?.mssv || user?.fullName || "")}`}>
              <Button
                variant="outline"
                size="sm"
                leftIcon={<FileSearch size={14} />}
                className="border-slate-600 text-slate-200 hover:bg-white/10 hover:text-white"
              >
                Tra cứu hồ sơ liên quan
              </Button>
            </Link>
          </div>
        </div>
      </div>

      {/* 2. Quick Stat Counters */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <div className="bg-white p-4 rounded-lg border border-slate-200/90 shadow-paper border-l-4 border-l-dlu-navy-900">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-slate-500 uppercase tracking-wide">
              Hồ sơ đã tải lên
            </span>
            <div className="p-1.5 rounded-md bg-dlu-navy-50 text-dlu-navy-800">
              <Layers size={16} />
            </div>
          </div>
          <div className="text-2xl font-bold font-mono text-slate-900 mt-1">
            {userDocs.length}
          </div>
          <span className="text-[11px] text-slate-500 mt-0.5 block">Tổng tài liệu đã nạp vào kho</span>
        </div>

        <div className="bg-white p-4 rounded-lg border border-slate-200/90 shadow-paper border-l-4 border-l-emerald-600">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-slate-500 uppercase tracking-wide">
              Đã nhận diện OCR
            </span>
            <div className="p-1.5 rounded-md bg-emerald-50 text-emerald-700">
              <CheckCircle2 size={16} />
            </div>
          </div>
          <div className="text-2xl font-bold font-mono text-emerald-700 mt-1">
            {doneDocsCount}
          </div>
          <span className="text-[11px] text-slate-500 mt-0.5 block">Hoàn tất trích xuất toàn văn</span>
        </div>

        <div className="bg-white p-4 rounded-lg border border-slate-200/90 shadow-paper border-l-4 border-l-amber-500">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-slate-500 uppercase tracking-wide">
              Đã phê duyệt điện tử
            </span>
            <div className="p-1.5 rounded-md bg-amber-50 text-amber-700">
              <Award size={16} />
            </div>
          </div>
          <div className="text-2xl font-bold font-mono text-amber-600 mt-1">
            {approvedDocsCount}
          </div>
          <span className="text-[11px] text-slate-500 mt-0.5 block">Đã ký số và cấp mã QR</span>
        </div>
      </div>

      {/* 3. Navigation Tabs */}
      <div className="border-b border-slate-200 flex gap-4 text-xs sm:text-sm">
        <button
          onClick={() => setActiveTab("DOCS")}
          className={`pb-2.5 font-semibold flex items-center gap-1.5 transition-colors border-b-2 ${
            activeTab === "DOCS"
              ? "border-dlu-navy-900 text-dlu-navy-900"
              : "border-transparent text-slate-500 hover:text-slate-800"
          }`}
        >
          <FileText size={15} />
          <span>Hồ sơ đã tải lên ({userDocs.length})</span>
        </button>

        <button
          onClick={() => setActiveTab("INFO")}
          className={`pb-2.5 font-semibold flex items-center gap-1.5 transition-colors border-b-2 ${
            activeTab === "INFO"
              ? "border-dlu-navy-900 text-dlu-navy-900"
              : "border-transparent text-slate-500 hover:text-slate-800"
          }`}
        >
          <User size={15} />
          <span>Thông tin tài khoản & Chỉnh sửa</span>
        </button>
      </div>

      {/* 4. Tab 1: Documents list */}
      {activeTab === "DOCS" && (
        <Card padding="none">
          <div className="p-4 flex items-center justify-between border-b border-slate-200/80 flex-wrap gap-3">
            <div className="relative flex-1 max-w-md">
              <Search size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
              <input
                type="text"
                placeholder="Lọc hồ sơ theo tiêu đề, số hiệu, MSSV..."
                value={searchDocTerm}
                onChange={(e) => setSearchDocTerm(e.target.value)}
                className="w-full pl-9 pr-3 py-1.5 rounded-md border border-slate-200 bg-slate-50/70 text-xs text-slate-800 placeholder-slate-400 outline-none focus:bg-white focus:ring-1 focus:ring-dlu-navy-500"
              />
            </div>

            <Button
              variant="outline"
              size="sm"
              leftIcon={<RefreshCw size={13} className={isLoadingDocs ? "animate-spin" : ""} />}
              onClick={fetchMyDocuments}
            >
              Làm mới
            </Button>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead>
                <tr className="bg-slate-50/90 border-b border-slate-200/80 text-slate-500 font-semibold uppercase tracking-wider text-[11px]">
                  <th className="px-5 py-3">Tiêu đề & Thông tin hồ sơ</th>
                  <th className="px-4 py-3">Danh mục</th>
                  <th className="px-4 py-3">Trạng thái OCR</th>
                  <th className="px-4 py-3">Thời gian upload</th>
                  <th className="px-5 py-3 text-right">Thao tác</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {filteredDocs.length === 0 ? (
                  <tr>
                    <td colSpan={5} className="py-12 px-4 text-center text-slate-400">
                      <FileText size={32} className="mx-auto mb-2 opacity-40" />
                      <p className="font-semibold text-slate-700">Chưa có hồ sơ nào phù hợp.</p>
                      <span className="text-[11px] text-slate-400">Các tài liệu do bạn tải lên sẽ hiển thị tại đây theo thời gian thực.</span>
                    </td>
                  </tr>
                ) : (
                  filteredDocs.map((doc) => (
                    <tr key={doc.id} className="hover:bg-slate-50/80 transition-colors">
                      <td className="px-5 py-3.5">
                        <div className="flex items-start gap-2.5">
                          <span
                            className={`p-1.5 rounded text-[10px] font-bold leading-none shrink-0 mt-0.5 ${
                              doc.file_type?.toLowerCase() === "pdf"
                                ? "bg-rose-50 text-rose-700 border border-rose-200"
                                : "bg-indigo-50 text-indigo-700 border border-indigo-200"
                            }`}
                          >
                            {doc.file_type || "PDF"}
                          </span>
                          <div>
                            <Link
                              to={`/documents/${doc.id}`}
                              className="text-dlu-navy-900 font-semibold text-xs sm:text-sm hover:underline line-clamp-1"
                            >
                              {doc.title}
                            </Link>
                            <div className="flex items-center gap-2 text-[11px] text-slate-400 mt-0.5">
                              {doc.document_number && <span>Số: <strong className="text-slate-600">{doc.document_number}</strong></span>}
                              {doc.student_id && <span>MSSV: <strong className="font-mono text-slate-600">{doc.student_id}</strong></span>}
                              <span className="font-mono">{(doc.file_size_bytes / (1024 * 1024)).toFixed(2)} MB</span>
                            </div>
                          </div>
                        </div>
                      </td>
                      <td className="px-4 py-3.5 text-slate-600">
                        {doc.category_name || "Chưa phân loại"}
                      </td>
                      <td className="px-4 py-3.5">
                        <OCRStatusBadge status={doc.ocr_status as any} />
                      </td>
                      <td className="px-4 py-3.5 text-slate-500 font-mono text-[11px]">
                        <div className="flex items-center gap-1.5">
                          <Clock size={12} className="text-slate-400" />
                          <span>
                            {new Date(doc.created_at).toLocaleTimeString("vi-VN", { hour: "2-digit", minute: "2-digit" })} • {new Date(doc.created_at).toLocaleDateString("vi-VN")}
                          </span>
                        </div>
                      </td>
                      <td className="px-5 py-3.5 text-right">
                        <Link to={`/documents/${doc.id}`}>
                          <Button variant="outline" size="sm" rightIcon={<ExternalLink size={12} />}>
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
        <Card padding="md" className="max-w-xl">
          <h2 className="text-sm font-bold text-slate-900 mb-4 pb-2 border-b border-slate-100">
            Thông tin Hồ sơ Cá nhân
          </h2>
          <form onSubmit={handleSaveProfile} className="space-y-4">
            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">
                Họ và tên
              </label>
              <input
                type="text"
                value={fullName}
                onChange={(e) => setFullName(e.target.value)}
                required
                className="w-full px-3 py-2 rounded-md border border-slate-200 text-xs sm:text-sm bg-white text-slate-900 outline-none focus:ring-2 focus:ring-dlu-navy-500/20 focus:border-dlu-navy-600"
              />
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">
                Mã số sinh viên (MSSV) / Mã cán bộ
              </label>
              <input
                type="text"
                value={mssv}
                onChange={(e) => setMssv(e.target.value)}
                placeholder="Ví dụ: 2212461 hoặc để trống nếu là cán bộ chung"
                className="w-full px-3 py-2 rounded-md border border-slate-200 text-xs sm:text-sm bg-white text-slate-900 font-mono outline-none focus:ring-2 focus:ring-dlu-navy-500/20 focus:border-dlu-navy-600"
              />
              <span className="text-[11px] text-slate-400 mt-1 block">
                MSSV giúp hệ thống tự động liên kết các đơn từ, quyết định và hồ sơ khen thưởng / miễn giảm học phí của bạn.
              </span>
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">
                Địa chỉ Email nhà trường
              </label>
              <input
                type="email"
                value={user?.email || ""}
                disabled
                className="w-full px-3 py-2 rounded-md border border-slate-200 text-xs sm:text-sm bg-slate-100 text-slate-500 font-mono cursor-not-allowed"
              />
              <span className="text-[11px] text-slate-400 mt-1 block">
                Email định danh @dlu.edu.vn được xác thực cố định qua tài khoản nhà trường.
              </span>
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">
                Vai trò hệ thống
              </label>
              <div className="flex items-center gap-2">
                <Badge variant={getRoleBadgeVariant()}>{user?.role || "STUDENT"}</Badge>
                <span className="text-xs text-slate-600">{getRoleLabel()}</span>
              </div>
            </div>

            <div className="pt-3 border-t border-slate-100 flex justify-end">
              <Button variant="primary" size="md" type="submit" isLoading={isSaving} leftIcon={<Save size={15} />}>
                Lưu cập nhật
              </Button>
            </div>
          </form>
        </Card>
      )}
    </div>
  );
};
