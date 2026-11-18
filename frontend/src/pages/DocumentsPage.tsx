import React, { useState, useEffect, useMemo } from "react";
import { Link } from "react-router-dom";
import {
  FileText,
  Filter,
  UploadCloud,
  Eye,
  CheckSquare,
  Search,
  RefreshCw,
  XCircle,
  Camera,
  ChevronLeft,
  ChevronRight,
  ChevronsLeft,
  ChevronsRight,
  Globe,
  Lock,
} from "lucide-react";
import { Card } from "../components/common/Card";
import { Button } from "../components/common/Button";
import { Badge } from "../components/common/Badge";
import { CameraCaptureModal } from "../components/common/CameraCaptureModal";
import { useAuthStore } from "../stores/useAuthStore";
import { useToastStore } from "../stores/useToastStore";
import { documentsApi, DocumentListItem } from "../api/documents";
import { statsApi, DashboardStatsResponse } from "../api/stats";

// Helper hàm làm đẹp tiêu đề văn bản hành chính
function formatDisplayTitle(rawTitle: string): { mainTitle: string; code?: string } {
  if (!rawTitle) return { mainTitle: "Tài liệu không tên" };

  let clean = rawTitle.replace(/^[0-9]+_/, "");
  const codeMatch = clean.match(/^([0-9A-Za-z]+-[A-Za-zĐđ]+-[A-Za-zĐđ]+)/);
  const code = codeMatch ? codeMatch[1].replace(/-/g, "/") : undefined;

  if (codeMatch) {
    clean = clean.replace(codeMatch[0], "").replace(/^[_\s-]+/, "");
  }

  clean = clean.replace(/_/g, " ").trim();
  clean = clean.replace(/\.(pdf|jpg|jpeg|png|tiff)$/i, "");

  if (!clean && code) {
    clean = `Văn bản số ${code}`;
  }

  return { mainTitle: clean || rawTitle, code };
}

export const DocumentsPage: React.FC = () => {
  const { user } = useAuthStore();
  const { addToast } = useToastStore();

  const isStaffOrAdmin = user?.role === "ADMIN" || user?.role === "STAFF";

  const [searchFilter, setSearchFilter] = useState("");
  const [statusFilter, setStatusFilter] = useState("ALL");
  const [approvalFilter, setApprovalFilter] = useState("ALL");
  const [selectedTag, setSelectedTag] = useState("ALL");
  const [tagSummary, setTagSummary] = useState<{ tag: string; count: number; priority: number; color: string; category: string }[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [isCameraOpen, setIsCameraOpen] = useState(false);
  const [publicFilter, setPublicFilter] = useState<"ALL" | "PUBLIC" | "PRIVATE">("ALL");
  const [togglingPublicId, setTogglingPublicId] = useState<string | null>(null);
  const [docs, setDocs] = useState<DocumentListItem[]>([]);

  // Phân trang & Thống kê
  const [currentPage, setCurrentPage] = useState(1);
  const [pageSize, setPageSize] = useState(20);
  const [totalItems, setTotalItems] = useState(0);
  const [totalPages, setTotalPages] = useState(1);
  const [systemStats, setSystemStats] = useState<DashboardStatsResponse | null>(null);

  const handleCameraCapture = async (file: File) => {
    setIsLoading(true);
    try {
      const title = file.name.replace(/\.[^/.]+$/, "");
      await documentsApi.upload(file, title);
      addToast({
        type: "success",
        title: "Đã tải lên ảnh chụp tài liệu",
        message: "Hệ thống đang tiến hành nhận dạng OCR.",
      });
      await fetchDocuments();
    } catch (err: any) {
      addToast({
        type: "error",
        title: "Lỗi tải lên",
        message: err.message || "Không thể tải lên ảnh chụp",
      });
    } finally {
      setIsLoading(false);
    }
  };

  const fetchTags = async () => {
    try {
      const res = await documentsApi.getTagsSummary();
      setTagSummary(res.items || []);
    } catch (err) {
      console.warn("Could not fetch tags summary:", err);
    }
  };

  const fetchDashboardStats = async () => {
    try {
      const stats = await statsApi.getDashboardStats();
      setSystemStats(stats);
    } catch (err) {
      console.warn("Could not fetch dashboard stats:", err);
    }
  };

  const isInitialSearchMount = React.useRef(true);

  const fetchDocuments = async (page = currentPage, size = pageSize, refreshMeta = false) => {
    setIsLoading(true);
    try {
      const res = await documentsApi.list({
        search: searchFilter.trim() || undefined,
        ocrStatus: statusFilter !== "ALL" ? statusFilter : undefined,
        approvalStatus: approvalFilter !== "ALL" ? approvalFilter : undefined,
        tag: selectedTag !== "ALL" ? selectedTag : undefined,
        page: page,
        pageSize: size,
        onlyMyUploads: !isStaffOrAdmin ? true : undefined,
      });
      setDocs(res.items || []);
      setTotalItems(res.total || 0);
      setTotalPages(res.total_pages || 1);
      if (refreshMeta || !systemStats) {
        fetchTags();
        fetchDashboardStats();
      }
    } catch (err: any) {
      console.warn("Could not fetch from backend:", err);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    setCurrentPage(1);
    fetchDocuments(1, pageSize, true);
  }, [statusFilter, approvalFilter, selectedTag, pageSize]);

  useEffect(() => {
    if (isInitialSearchMount.current) {
      isInitialSearchMount.current = false;
      return;
    }
    const timer = setTimeout(() => {
      setCurrentPage(1);
      fetchDocuments(1, pageSize);
    }, 350);
    return () => clearTimeout(timer);
  }, [searchFilter]);

  useEffect(() => {
    const hasProcessing = docs.some((d) => d.ocr_status === "PROCESSING" || d.ocr_status === "PENDING");
    if (!hasProcessing) return;

    const interval = setInterval(() => {
      fetchDocuments(currentPage, pageSize);
    }, 3000);

    return () => clearInterval(interval);
  }, [docs, currentPage, pageSize]);

  const handlePageChange = (newPage: number) => {
    if (newPage < 1 || newPage > totalPages || newPage === currentPage) return;
    setCurrentPage(newPage);
    fetchDocuments(newPage, pageSize, false);
    window.scrollTo({ top: 0, behavior: "smooth" });
  };

  const getPageNumbers = () => {
    const pages: number[] = [];
    if (totalPages <= 7) {
      for (let i = 1; i <= totalPages; i++) pages.push(i);
    } else {
      if (currentPage <= 4) {
        for (let i = 1; i <= 5; i++) pages.push(i);
        pages.push(-1);
        pages.push(totalPages);
      } else if (currentPage >= totalPages - 3) {
        pages.push(1);
        pages.push(-1);
        for (let i = totalPages - 4; i <= totalPages; i++) pages.push(i);
      } else {
        pages.push(1);
        pages.push(-1);
        pages.push(currentPage - 1);
        pages.push(currentPage);
        pages.push(currentPage + 1);
        pages.push(-1);
        pages.push(totalPages);
      }
    }
    return pages;
  };

  const handleApprove = async (id: string, e: React.MouseEvent) => {
    e.stopPropagation();
    try {
      await documentsApi.approve(id);
      addToast({
        type: "success",
        title: "Đã phê duyệt hồ sơ",
        message: "Hồ sơ đã được đánh dấu APPROVED và xác thực điện tử",
      });
      fetchDocuments(currentPage, pageSize, true);
    } catch (err: any) {
      addToast({
        type: "error",
        title: "Lỗi phê duyệt",
        message: err.message || "Không thể phê duyệt hồ sơ này",
      });
    }
  };

  const handleReject = async (id: string, e: React.MouseEvent) => {
    e.stopPropagation();
    try {
      await documentsApi.reject(id);
      addToast({
        type: "info",
        title: "Đã từ chối hồ sơ",
        message: "Trạng thái đã chuyển sang REJECTED",
      });
      fetchDocuments(currentPage, pageSize, true);
    } catch (err: any) {
      addToast({
        type: "error",
        title: "Lỗi",
        message: err.message || "Không thể từ chối hồ sơ này",
      });
    }
  };

  const handleTogglePublic = async (id: string, isPublic: boolean, e: React.MouseEvent) => {
    e.stopPropagation();
    setTogglingPublicId(id);
    try {
      await documentsApi.setPublic(id, isPublic);
      addToast({
        type: "success",
        title: isPublic ? "Đã mở quyền công khai" : "Đã chuyển sang nội bộ",
        message: isPublic
          ? "Sinh viên hiện đã có thể tra cứu và xem tài liệu này."
          : "Tài liệu đã được thu hồi quyền công khai, chỉ Cán bộ và Quản trị viên mới xem được.",
      });
      setDocs((prev) => prev.map((d) => (d.id === id ? { ...d, is_public: isPublic } : d)));
    } catch (err: any) {
      addToast({
        type: "error",
        title: "Lỗi cập nhật quyền",
        message: err.message || "Không thể thay đổi quyền truy cập tài liệu.",
      });
    } finally {
      setTogglingPublicId(null);
    }
  };

  const displayDocs = useMemo(() => {
    return docs
      .filter((doc) => {
        if (publicFilter === "PUBLIC" && !doc.is_public) return false;
        if (publicFilter === "PRIVATE" && doc.is_public) return false;
        return true;
      })
      .sort((a, b) => {
        const timeA = a.created_at ? new Date(a.created_at).getTime() : 0;
        const timeB = b.created_at ? new Date(b.created_at).getTime() : 0;
        return timeB - timeA;
      });
  }, [docs, publicFilter]);

  const isFiltered = Boolean(searchFilter || statusFilter !== "ALL" || approvalFilter !== "ALL" || selectedTag !== "ALL");

  const totalCount = isFiltered ? totalItems : (systemStats?.total_documents ?? totalItems);
  const pendingCount = isFiltered
    ? docs.filter((d) => d.ocr_status !== "APPROVED" && d.ocr_status !== "REJECTED").length
    : (systemStats ? Math.max(0, systemStats.total_documents - systemStats.approved_count - systemStats.rejected_count) : totalItems);
  const approvedCount = isFiltered
    ? docs.filter((d) => d.ocr_status === "APPROVED").length
    : (systemStats?.approved_count ?? 0);
  const digitizedCount = isFiltered
    ? docs.filter((d) => d.ocr_status === "DONE" || d.ocr_status === "APPROVED").length
    : (systemStats ? (systemStats.done_count + systemStats.approved_count) : totalItems);

  const getTagBadgeClass = (tag: string) => {
    const t = tag.toUpperCase();
    if (t.startsWith("#SO_") || /^#[0-9]/.test(t)) {
      return "bg-rose-50 text-rose-700 border-rose-200 hover:bg-rose-100";
    }
    if (["#THONGBAO", "#KEHOACH", "#QUYETDINH", "#HUONGDAN", "#TOTRINH", "#BAOCAO", "#CONGVAN", "#GIAYMOI", "#BIENBAN", "#DANHSACH", "#DONTU"].includes(t)) {
      return "bg-amber-50 text-amber-800 border-amber-200 hover:bg-amber-100";
    }
    if (t.startsWith("#NGANH")) {
      return "bg-emerald-50 text-emerald-800 border-emerald-200 hover:bg-emerald-100";
    }
    if (t.startsWith("#KHOA") && !/^#K[0-9]{2}/.test(t)) {
      return "bg-indigo-50 text-indigo-700 border-indigo-200 hover:bg-indigo-100";
    }
    if (/^#K[0-9]{2}/.test(t)) {
      return "bg-purple-50 text-purple-700 border-purple-200 hover:bg-purple-100";
    }
    return "bg-teal-50 text-teal-800 border-teal-200 hover:bg-teal-100";
  };

  return (
    <div className="space-y-5 animate-fade-in w-full">
      {/* Top Header */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <div>
          <div className="flex items-center gap-2.5">
            <h1 className="text-xl sm:text-2xl font-bold text-slate-900 tracking-tight">
              {isStaffOrAdmin ? "Quản lý & Phê duyệt Hồ sơ CTSV" : "Lịch sử Upload Hồ sơ của bạn"}
            </h1>
            <Badge variant={user?.role === "ADMIN" ? "danger" : user?.role === "STAFF" ? "warning" : "info"}>
              {user?.role === "STUDENT" ? "SINH VIÊN" : (user?.role || "STUDENT")}
            </Badge>
          </div>
          <p className="text-xs sm:text-sm text-slate-500 mt-1">
            {isStaffOrAdmin
              ? "Trợ lý CTSV kiểm tra kết quả nhận dạng OCR, phân loại nhãn thông minh và phê duyệt văn bản số."
              : "Danh sách toàn bộ các tài liệu do tài khoản của bạn tải lên, tình trạng nhận dạng OCR và kết quả xử lý của Cán bộ CTSV."}
          </p>
        </div>

        {/* Nút thao tác nhanh */}
        <div className="flex items-center gap-2 flex-wrap">
          <Button
            variant="outline"
            size="sm"
            onClick={() => setIsCameraOpen(true)}
            leftIcon={<Camera size={14} className="text-dlu-navy-700" />}
          >
            Chụp ảnh hồ sơ
          </Button>
          <Link to="/upload">
            <Button variant="primary" size="sm" leftIcon={<UploadCloud size={14} />}>
              {isStaffOrAdmin ? "Tiếp nhận hồ sơ" : "Tải lên hồ sơ mới"}
            </Button>
          </Link>
        </div>
      </div>

      {/* Chỉ số hồ sơ nghiệp vụ */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-3 sm:gap-4">
        <div className="bg-white p-4 rounded-lg border border-slate-200/90 border-l-4 border-l-dlu-navy-900 shadow-paper">
          <div className="text-xs font-semibold text-slate-500 uppercase tracking-wide">
            {isStaffOrAdmin ? "Tổng số hồ sơ" : "Hồ sơ bạn đã upload"}
          </div>
          <div className="text-xl sm:text-2xl font-bold text-slate-900 font-mono mt-1">
            {totalCount}
          </div>
        </div>

        <div className="bg-white p-4 rounded-lg border border-slate-200/90 border-l-4 border-l-amber-500 shadow-paper">
          <div className="text-xs font-semibold text-slate-500 uppercase tracking-wide">
            {isStaffOrAdmin ? "Chờ phê duyệt" : "Đang chờ duyệt"}
          </div>
          <div className="text-xl sm:text-2xl font-bold text-amber-600 font-mono mt-1">
            {pendingCount}
          </div>
        </div>

        <div className="bg-white p-4 rounded-lg border border-slate-200/90 border-l-4 border-l-emerald-600 shadow-paper">
          <div className="text-xs font-semibold text-slate-500 uppercase tracking-wide">
            {isStaffOrAdmin ? "Đã phê duyệt" : "Đã được phê duyệt"}
          </div>
          <div className="text-xl sm:text-2xl font-bold text-emerald-600 font-mono mt-1">
            {approvedCount}
          </div>
        </div>

        <div className="bg-white p-4 rounded-lg border border-slate-200/90 border-l-4 border-l-sky-600 shadow-paper">
          <div className="text-xs font-semibold text-slate-500 uppercase tracking-wide">
            {isStaffOrAdmin ? "Số hóa hoàn tất" : "Đã nhận dạng OCR"}
          </div>
          <div className="text-xl sm:text-2xl font-bold text-sky-700 font-mono mt-1">
            {digitizedCount}
          </div>
        </div>
      </div>

      {/* Filter & Search Bar + 1-Click Smart Tag Cloud */}
      <Card padding="sm">
        <div className="space-y-3">
          <div className="flex flex-col lg:flex-row gap-3 items-stretch lg:items-center justify-between">
            {/* Search Input */}
            <div className="relative flex-1">
              <Search size={15} className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
              <input
                type="text"
                value={searchFilter}
                onChange={(e) => setSearchFilter(e.target.value)}
                placeholder={
                  isStaffOrAdmin
                    ? "Tìm theo tên hồ sơ, số hiệu văn bản (1353/KH...), họ tên hoặc MSSV..."
                    : "Tìm trong lịch sử upload theo tên hồ sơ, số hiệu, từ khóa..."
                }
                className="w-full pl-9 pr-3 py-2 rounded-md border border-slate-200 bg-slate-50/70 text-xs sm:text-sm text-slate-900 placeholder-slate-400 focus:bg-white focus:ring-2 focus:ring-dlu-navy-500/20 focus:border-dlu-navy-600 outline-none transition-all"
              />
            </div>

            {/* Filter Dropdowns */}
            <div className="flex items-center gap-2 flex-wrap">
              <div className="flex items-center gap-1.5">
                <span className="text-xs font-semibold text-slate-600">Trạng thái:</span>
                <select
                  value={statusFilter}
                  onChange={(e) => setStatusFilter(e.target.value)}
                  className="px-2.5 py-1.5 rounded-md border border-slate-200 text-xs bg-white text-slate-800 font-medium cursor-pointer outline-none focus:ring-2 focus:ring-dlu-navy-500/20 focus:border-dlu-navy-600"
                >
                  <option value="ALL">Tất cả trạng thái</option>
                  <option value="APPROVED">Đã duyệt (APPROVED)</option>
                  <option value="DONE">OCR Xong (DONE)</option>
                  <option value="PROCESSING">Đang xử lý</option>
                  <option value="PENDING">Chờ xử lý</option>
                  <option value="FAILED">Thất bại (FAILED)</option>
                </select>
              </div>

              <div className="flex items-center gap-1.5">
                <span className="text-xs font-semibold text-slate-600">Phê duyệt:</span>
                <select
                  value={approvalFilter}
                  onChange={(e) => setApprovalFilter(e.target.value)}
                  className="px-2.5 py-1.5 rounded-md border border-slate-200 text-xs bg-white text-slate-800 font-medium cursor-pointer outline-none focus:ring-2 focus:ring-dlu-navy-500/20 focus:border-dlu-navy-600"
                >
                  <option value="ALL">Tất cả</option>
                  <option value="APPROVED">Đã phê duyệt</option>
                  <option value="PENDING">Chưa phê duyệt</option>
                </select>
              </div>

              {isStaffOrAdmin && (
                <div className="flex items-center gap-1.5">
                  <span className="text-xs font-semibold text-slate-600">Quyền xem:</span>
                  <select
                    value={publicFilter}
                    onChange={(e) => setPublicFilter(e.target.value as any)}
                    className="px-2.5 py-1.5 rounded-md border border-slate-200 text-xs bg-white text-slate-800 font-medium cursor-pointer outline-none focus:ring-2 focus:ring-dlu-navy-500/20 focus:border-dlu-navy-600"
                  >
                    <option value="ALL">Tất cả quyền</option>
                    <option value="PUBLIC">🌐 Công khai (Public)</option>
                    <option value="PRIVATE">🔒 Nội bộ (Riêng tư)</option>
                  </select>
                </div>
              )}

              <Button
                variant="outline"
                size="sm"
                onClick={() => fetchDocuments(currentPage, pageSize)}
                leftIcon={<RefreshCw size={13} className={isLoading ? "animate-spin" : ""} />}
              >
                Làm mới
              </Button>
            </div>
          </div>

          {/* 🏷️ 1-Click Smart Tag Cloud Filter */}
          <div className="flex items-center gap-1.5 flex-wrap pt-2.5 border-t border-slate-100 text-xs">
            <span className="font-bold text-slate-500 flex items-center gap-1 mr-1 text-[11px]">
              <Filter size={12} className="text-dlu-navy-700" />
              Lọc theo Nhãn AI:
            </span>

            <button
              onClick={() => setSelectedTag("ALL")}
              className={`px-2.5 py-0.5 rounded-full text-xs font-semibold border transition-all ${
                selectedTag === "ALL"
                  ? "bg-dlu-navy-900 text-white border-dlu-navy-900 shadow-xs"
                  : "bg-white text-slate-700 border-slate-200 hover:bg-slate-50"
              }`}
            >
              Tất cả nhãn
            </button>

            {tagSummary.slice(0, 10).map((tItem) => {
              const isSelected = selectedTag.toLowerCase() === tItem.tag.toLowerCase();
              const badgeClass = getTagBadgeClass(tItem.tag);

              return (
                <button
                  key={tItem.tag}
                  onClick={() => setSelectedTag(isSelected ? "ALL" : tItem.tag)}
                  className={`inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-medium border transition-all ${
                    isSelected
                      ? "bg-dlu-navy-900 text-white border-dlu-navy-900 shadow-xs"
                      : badgeClass
                  }`}
                  title={`Ưu tiên: ${tItem.priority} điểm - Danh mục: ${tItem.category}`}
                >
                  <span>{tItem.tag}</span>
                  <span className={`text-[10px] font-mono px-1 rounded-full ${isSelected ? "bg-white/20 text-white" : "bg-black/5"}`}>
                    {tItem.count}
                  </span>
                </button>
              );
            })}
          </div>
        </div>
      </Card>

      {/* Main Documents Table */}
      <Card padding="none">
        <div className="w-full overflow-x-auto">
          <table className="w-full text-left text-xs min-w-[960px]">
            <thead>
              <tr className="bg-slate-50/90 border-b border-slate-200/80 text-slate-500 font-semibold uppercase tracking-wider text-[11px] whitespace-nowrap">
                <th className="px-5 py-3.5">Tiêu đề & Thông tin hồ sơ</th>
                <th className="px-4 py-3.5 whitespace-nowrap">Người nộp / MSSV</th>
                <th className="px-4 py-3.5 whitespace-nowrap">Danh mục</th>
                {isStaffOrAdmin && <th className="px-4 py-3.5 whitespace-nowrap">Tiến độ OCR</th>}
                {isStaffOrAdmin && <th className="px-3 py-3.5 whitespace-nowrap">Quyền xem</th>}
                <th className="px-3 py-3.5 whitespace-nowrap">Phê duyệt</th>
                <th className="px-5 py-3.5 text-right whitespace-nowrap min-w-[210px]">Thao tác</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {displayDocs.length === 0 ? (
                <tr>
                  <td colSpan={isStaffOrAdmin ? 7 : 5} className="py-14 px-4 text-center text-slate-400">
                    <UploadCloud size={40} className="mx-auto text-slate-300 mb-2 opacity-60" />
                    <p className="text-sm font-semibold text-slate-800">
                      {isFiltered
                        ? "Không tìm thấy hồ sơ nào khớp với bộ lọc."
                        : isStaffOrAdmin
                        ? "Không có hồ sơ nào trong hệ thống."
                        : "Bạn chưa tải lên hồ sơ nào"}
                    </p>
                    <p className="text-xs text-slate-400 mt-1 max-w-sm mx-auto mb-4">
                      {isFiltered
                        ? "Thử xóa từ khóa tìm kiếm hoặc bỏ chọn các điều kiện lọc."
                        : isStaffOrAdmin
                        ? "Các hồ sơ vừa được tải lên sẽ hiển thị tại đây."
                        : "Toàn bộ tài liệu, giấy tờ bạn gửi lên hệ thống sẽ được lưu tại đây để tiện theo dõi tiến độ."}
                    </p>
                    {!isStaffOrAdmin && !isFiltered && (
                      <Link to="/upload">
                        <Button variant="primary" size="sm" leftIcon={<UploadCloud size={14} />}>
                          Tải lên hồ sơ mới ngay
                        </Button>
                      </Link>
                    )}
                  </td>
                </tr>
              ) : (
                displayDocs.map((doc) => {
                  const isApproved = doc.ocr_status === "APPROVED";
                  const isRejected = doc.ocr_status === "REJECTED";
                  const { mainTitle, code } = formatDisplayTitle(doc.title);

                  return (
                    <tr
                      key={doc.id}
                      className="hover:bg-slate-50/80 transition-colors"
                    >
                      {/* Tiêu đề & Thông tin file */}
                      <td className="px-5 py-3.5 max-w-md">
                        <div className="flex items-start gap-2.5">
                          <div
                            className={`p-1.5 rounded font-bold text-[10px] leading-none shrink-0 mt-0.5 ${
                              doc.file_type?.toLowerCase() === "pdf"
                                ? "bg-rose-50 text-rose-700 border border-rose-200"
                                : "bg-indigo-50 text-indigo-700 border border-indigo-200"
                            }`}
                          >
                            {doc.file_type || "PDF"}
                          </div>
                          <div>
                            <Link
                              to={`/documents/${doc.id}`}
                              className="text-dlu-navy-900 font-semibold text-xs sm:text-sm hover:underline line-clamp-2 leading-snug"
                            >
                              {mainTitle}
                            </Link>

                            <div className="flex items-center gap-2 text-[11px] text-slate-400 mt-1 flex-wrap">
                              {doc.document_number ? (
                                <span className="bg-sky-50 text-sky-800 font-bold px-1.5 py-0.2 rounded border border-sky-200 text-[10px]">
                                  Số: {doc.document_number}
                                </span>
                              ) : code ? (
                                <span className="text-dlu-navy-700 font-semibold">{code}</span>
                              ) : null}

                              {doc.category_code === "KHAC" && (
                                <span className="bg-rose-50 text-rose-700 font-bold px-1.5 py-0.2 rounded border border-rose-200 text-[10px]">
                                  Cần kiểm tra
                                </span>
                              )}

                              <span className="font-mono">
                                {(doc.file_size_bytes / (1024 * 1024)).toFixed(2)} MB
                              </span>
                              <span>•</span>
                              <span
                                className="text-dlu-navy-900 font-medium"
                                title={`Thời gian upload: ${new Date(doc.created_at).toLocaleString("vi-VN")}`}
                              >
                                {new Date(doc.created_at).toLocaleTimeString("vi-VN", {
                                  hour: "2-digit",
                                  minute: "2-digit",
                                })} • {new Date(doc.created_at).toLocaleDateString("vi-VN")}
                              </span>
                            </div>

                            {/* Badges danh sách nhãn AI */}
                            {doc.tags && doc.tags.length > 0 && (
                              <div className="flex gap-1 flex-wrap mt-1.5">
                                {doc.tags.slice(0, 3).map((t) => (
                                  <button
                                    key={t}
                                    onClick={(e) => {
                                      e.preventDefault();
                                      e.stopPropagation();
                                      setSelectedTag(t);
                                    }}
                                    className={`text-[10px] font-semibold px-1.5 py-0.5 rounded border transition-colors ${getTagBadgeClass(
                                      t
                                    )}`}
                                    title={`Lọc tài liệu theo nhãn ${t}`}
                                  >
                                    {t}
                                  </button>
                                ))}
                                {doc.tags.length > 3 && (
                                  <span className="text-[10px] text-slate-400 self-center">
                                    +{doc.tags.length - 3}
                                  </span>
                                )}
                              </div>
                            )}
                          </div>
                        </div>
                      </td>

                      {/* Người nộp / MSSV */}
                      <td className="px-4 py-3.5 align-middle">
                        <div className="font-semibold text-slate-800 text-xs">
                          {doc.student_name || doc.uploader_name || "Cán bộ CTSV (Đại học Đà Lạt)"}
                        </div>
                        <div className="text-[11px] text-slate-400 mt-0.5">
                          {doc.student_id || doc.uploader_mssv ? (
                            <span className="bg-slate-100 px-1.5 py-0.5 rounded font-mono text-slate-700">
                              MSSV: {doc.student_id || doc.uploader_mssv}
                            </span>
                          ) : (
                            <span>Trường Đại học Đà Lạt</span>
                          )}
                        </div>
                      </td>

                      {/* Danh mục */}
                      <td className="px-4 py-3.5 align-middle">
                        <span className="inline-block px-2 py-0.5 rounded bg-slate-100 font-medium text-[11px] text-slate-700 border border-slate-200">
                          {doc.category_name || "Chưa phân loại"}
                        </span>
                      </td>

                      {/* Tiến độ OCR */}
                      {isStaffOrAdmin && (
                        <td className="px-4 py-3.5 align-middle min-w-[130px]">
                          {(() => {
                            const status = doc.ocr_status;
                            const rawProgress = doc.ocr_progress ?? 0;
                            const progress =
                              status === "DONE" || status === "APPROVED"
                                ? 100
                                : status === "FAILED"
                                ? 0
                                : status === "PENDING"
                                ? Math.max(rawProgress, 5)
                                : rawProgress;

                            const isDone = status === "DONE" || status === "APPROVED";
                            const isFailed = status === "FAILED";

                            return (
                              <div className="space-y-1">
                                <div className="flex justify-between items-center text-[11px]">
                                  <span
                                    className={`font-semibold ${
                                      isDone
                                        ? "text-emerald-700"
                                        : isFailed
                                        ? "text-rose-700"
                                        : "text-dlu-navy-700"
                                    }`}
                                  >
                                    {isDone
                                      ? "Hoàn thành"
                                      : isFailed
                                      ? "Thất bại"
                                      : status === "PENDING"
                                      ? "Chờ xử lý"
                                      : "Đang OCR..."}
                                  </span>
                                  <span className="font-mono font-bold text-slate-600">
                                    {progress}%
                                  </span>
                                </div>
                                <div className="w-full h-1.5 bg-slate-100 rounded-full overflow-hidden">
                                  <div
                                    className={`h-full rounded-full transition-all duration-300 ${
                                      isDone
                                        ? "bg-emerald-600"
                                        : isFailed
                                        ? "bg-rose-600"
                                        : "bg-dlu-navy-700"
                                    }`}
                                    style={{ width: `${progress}%` }}
                                  />
                                </div>
                              </div>
                            );
                          })()}
                        </td>
                      )}

                      {/* Quyền xem Public / Nội bộ */}
                      {isStaffOrAdmin && (
                        <td className="px-3 py-3.5 align-middle">
                          <button
                            onClick={(e) => handleTogglePublic(doc.id, !doc.is_public, e)}
                            disabled={togglingPublicId === doc.id}
                            className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-bold border transition-all ${
                              doc.is_public
                                ? "bg-emerald-50 text-emerald-800 border-emerald-300 hover:bg-emerald-100"
                                : "bg-amber-50 text-amber-800 border-amber-300 hover:bg-amber-100"
                            }`}
                            title={
                              doc.is_public
                                ? "Tài liệu đang CÔNG KHAI cho Sinh viên. Nhấp để khóa thành Nội bộ"
                                : "Tài liệu đang NỘI BỘ. Nhấp để mở quyền cho Sinh viên xem"
                            }
                          >
                            {doc.is_public ? (
                              <>
                                <Globe size={11} className="text-emerald-700" />
                                <span>Công khai</span>
                              </>
                            ) : (
                              <>
                                <Lock size={11} className="text-amber-700" />
                                <span>Nội bộ</span>
                              </>
                            )}
                          </button>
                        </td>
                      )}

                      {/* Trạng thái Phê duyệt */}
                      <td className="px-3 py-3.5 align-middle whitespace-nowrap">
                        {isApproved ? (
                          <div className="inline-flex flex-col items-start">
                            <Badge variant="success" dot size="sm">Đã duyệt</Badge>
                            {doc.approval_info?.approver_role && (
                              <div
                                className={`text-[10px] font-semibold mt-0.5 ${
                                  doc.approval_info.approver_role === "ADMIN"
                                    ? "text-rose-700"
                                    : "text-sky-700"
                                }`}
                                title={`Phê duyệt bởi: ${
                                  doc.approval_info.approver_name ||
                                  doc.approval_info.approver_role_label
                                }`}
                              >
                                {doc.approval_info.approver_role === "ADMIN" ? "Admin" : "CTSV"}
                              </div>
                            )}
                          </div>
                        ) : isRejected ? (
                          <div className="inline-flex flex-col items-start">
                            <Badge variant="danger" dot size="sm">Từ chối</Badge>
                            {doc.approval_info?.approver_role && (
                              <div className="text-[10px] font-semibold text-rose-800 mt-0.5">
                                {doc.approval_info.approver_role === "ADMIN" ? "Admin" : "CTSV"}
                              </div>
                            )}
                          </div>
                        ) : (
                          <Badge variant="warning" dot size="sm">Chờ duyệt</Badge>
                        )}
                      </td>

                      {/* Hành động */}
                      <td className="px-5 py-3.5 align-middle text-right whitespace-nowrap min-w-[280px]">
                        <div className="inline-flex gap-1.5 items-center justify-end flex-nowrap">
                          <Link to={`/documents/${doc.id}`} className="shrink-0 inline-flex">
                            <Button variant="outline" size="sm" className="shrink-0" leftIcon={<Eye size={13} />}>
                              Chi tiết
                            </Button>
                          </Link>

                          {isStaffOrAdmin && (
                            <>
                              {!isApproved && (
                                <Button
                                  variant="primary"
                                  size="sm"
                                  className="shrink-0"
                                  onClick={(e) => handleApprove(doc.id, e)}
                                  leftIcon={<CheckSquare size={13} />}
                                >
                                  Duyệt
                                </Button>
                              )}
                              {!isRejected && (
                                <Button
                                  variant="danger"
                                  size="sm"
                                  className="shrink-0"
                                  onClick={(e) => handleReject(doc.id, e)}
                                  leftIcon={<XCircle size={13} />}
                                >
                                  Từ chối
                                </Button>
                              )}
                            </>
                          )}
                        </div>
                      </td>
                    </tr>
                  );
                })
              )}
            </tbody>
          </table>
        </div>

        {/* Pagination & Display Controls */}
        <div className="flex justify-between items-center flex-wrap gap-4 px-5 py-3.5 border-t border-slate-200/80 bg-white">
          <div className="flex items-center gap-3 sm:gap-5 flex-wrap text-xs text-slate-500">
            <span>
              Hiển thị <strong className="text-slate-900 font-mono">{totalItems > 0 ? (currentPage - 1) * pageSize + 1 : 0}</strong> - <strong className="text-slate-900 font-mono">{Math.min(currentPage * pageSize, totalItems)}</strong> trong tổng số <strong className="text-dlu-navy-900 font-mono">{totalItems}</strong> hồ sơ
            </span>

            <div className="flex items-center gap-1.5">
              <span>Số mục / trang:</span>
              <select
                value={pageSize}
                onChange={(e) => {
                  const newSize = Number(e.target.value);
                  setPageSize(newSize);
                  setCurrentPage(1);
                }}
                className="px-2 py-1 text-xs rounded border border-slate-200 bg-slate-50 text-slate-800 font-medium cursor-pointer outline-none focus:ring-1 focus:ring-dlu-navy-500"
              >
                <option value={20}>20 hồ sơ</option>
                <option value={50}>50 hồ sơ</option>
                <option value={100}>100 hồ sơ</option>
                <option value={200}>Tất cả ({totalItems})</option>
              </select>
            </div>
          </div>

          {/* Page Navigation Buttons */}
          <div className="flex items-center gap-1">
            <button
              onClick={() => handlePageChange(1)}
              disabled={currentPage <= 1 || isLoading}
              title="Về trang đầu"
              className="p-1.5 rounded border border-slate-200 bg-white text-slate-600 hover:bg-slate-50 disabled:opacity-40 disabled:cursor-not-allowed text-xs transition-colors"
            >
              <ChevronsLeft size={13} />
            </button>

            <button
              onClick={() => handlePageChange(currentPage - 1)}
              disabled={currentPage <= 1 || isLoading}
              title="Trang trước"
              className="inline-flex items-center gap-1 px-2.5 py-1 rounded border border-slate-200 bg-white text-slate-700 hover:bg-slate-50 disabled:opacity-40 disabled:cursor-not-allowed text-xs font-medium transition-colors"
            >
              <ChevronLeft size={13} />
              Trước
            </button>

            {getPageNumbers().map((p, idx) => {
              if (p === -1) {
                return (
                  <span key={`ellipsis-${idx}`} className="px-1 text-slate-400 text-xs">
                    ...
                  </span>
                );
              }
              const isActive = p === currentPage;
              return (
                <button
                  key={`page-${p}`}
                  onClick={() => handlePageChange(p)}
                  disabled={isLoading}
                  className={`w-7 h-7 inline-flex items-center justify-center rounded text-xs font-mono font-semibold transition-all ${
                    isActive
                      ? "bg-dlu-navy-900 text-white shadow-xs"
                      : "border border-slate-200 bg-white text-slate-700 hover:bg-slate-50"
                  }`}
                >
                  {p}
                </button>
              );
            })}

            <button
              onClick={() => handlePageChange(currentPage + 1)}
              disabled={currentPage >= totalPages || isLoading}
              title="Trang sau"
              className="inline-flex items-center gap-1 px-2.5 py-1 rounded border border-slate-200 bg-white text-slate-700 hover:bg-slate-50 disabled:opacity-40 disabled:cursor-not-allowed text-xs font-medium transition-colors"
            >
              Sau
              <ChevronRight size={13} />
            </button>

            <button
              onClick={() => handlePageChange(totalPages)}
              disabled={currentPage >= totalPages || isLoading}
              title="Đến trang cuối"
              className="p-1.5 rounded border border-slate-200 bg-white text-slate-600 hover:bg-slate-50 disabled:opacity-40 disabled:cursor-not-allowed text-xs transition-colors"
            >
              <ChevronsRight size={13} />
            </button>
          </div>
        </div>
      </Card>

      {/* Camera Capture Modal */}
      <CameraCaptureModal
        isOpen={isCameraOpen}
        onClose={() => setIsCameraOpen(false)}
        onCapture={handleCameraCapture}
      />
    </div>
  );
};
