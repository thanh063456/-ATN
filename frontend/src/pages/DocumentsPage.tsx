import React, { useState, useEffect } from "react";
import { Link } from "react-router-dom";
import {
  FileText,
  Filter,
  UploadCloud,
  CheckCircle2,
  Clock,
  Eye,
  CheckSquare,
  Search,
  RefreshCw,
  XCircle,
  Camera,
  FileCheck,
  AlertCircle,
  ShieldCheck,
  Sparkles,
} from "lucide-react";
import { Card } from "../components/common/Card";
import { Button } from "../components/common/Button";
import { OCRStatusBadge, Badge } from "../components/common/Badge";
import { CameraCaptureModal } from "../components/common/CameraCaptureModal";
import { useAuthStore } from "../stores/useAuthStore";
import { useToastStore } from "../stores/useToastStore";
import { documentsApi, DocumentListItem } from "../api/documents";

// Helper hàm làm đẹp tiêu đề văn bản hành chính
function formatDisplayTitle(rawTitle: string): { mainTitle: string; code?: string } {
  if (!rawTitle) return { mainTitle: "Tài liệu không tên" };
  
  // Loại bỏ tiền tố 0_, 1_, 2_
  let clean = rawTitle.replace(/^[0-9]+_/, "");
  
  // Trích xuất số hiệu công văn nếu có (vd: 1436-KH-ĐHĐL, 1353-KH-ĐHĐL)
  let codeMatch = clean.match(/^([0-9A-Za-z]+-[A-Za-zĐđ]+-[A-Za-zĐđ]+)/);
  let code = codeMatch ? codeMatch[1].replace(/-/g, "/") : undefined;
  
  if (codeMatch) {
    clean = clean.replace(codeMatch[0], "").replace(/^[_\s-]+/, "");
  }
  
  // Thay thế dấu gạch dưới thành dấu cách
  clean = clean.replace(/_/g, " ").trim();
  
  // Bỏ phần đuôi mở rộng file nếu có
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
  const [isLoading, setIsLoading] = useState(false);
  const [isCameraOpen, setIsCameraOpen] = useState(false);
  const [docs, setDocs] = useState<DocumentListItem[]>([]);

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

  const fetchDocuments = async () => {
    setIsLoading(true);
    try {
      const res = await documentsApi.list({
        search: searchFilter || undefined,
        ocrStatus: statusFilter !== "ALL" ? statusFilter : undefined,
      });
      setDocs(res.items || []);
    } catch (err: any) {
      console.warn("Could not fetch from backend:", err);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchDocuments();
  }, [statusFilter]);

  // Real-time polling nếu có tài liệu đang xử lý OCR (PROCESSING hoặc PENDING)
  useEffect(() => {
    const hasProcessing = docs.some((d) => d.ocr_status === "PROCESSING" || d.ocr_status === "PENDING");
    if (!hasProcessing) return;

    const interval = setInterval(() => {
      fetchDocuments();
    }, 3000);

    return () => clearInterval(interval);
  }, [docs, statusFilter]);

  const handleApprove = async (id: string, e: React.MouseEvent) => {
    e.stopPropagation();
    try {
      await documentsApi.approve(id);
      addToast({
        type: "success",
        title: "Đã phê duyệt hồ sơ",
        message: "Hồ sơ đã được đánh dấu APPROVED và xác thực điện tử",
      });
      fetchDocuments();
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
      fetchDocuments();
    } catch (err: any) {
      addToast({
        type: "error",
        title: "Lỗi",
        message: err.message || "Không thể từ chối hồ sơ này",
      });
    }
  };

  const filteredDocs = docs.filter((doc) => {
    const uploaderName = doc.uploader_name || doc.student_name || "";
    const uploaderMssv = doc.uploader_mssv || doc.student_id || "";
    const matchSearch =
      !searchFilter ||
      doc.title.toLowerCase().includes(searchFilter.toLowerCase()) ||
      (uploaderName && uploaderName.toLowerCase().includes(searchFilter.toLowerCase())) ||
      (uploaderMssv && uploaderMssv.includes(searchFilter));

    const isApproved = doc.ocr_status === "APPROVED";
    const matchApproval =
      approvalFilter === "ALL" ||
      (approvalFilter === "APPROVED" && isApproved) ||
      (approvalFilter === "PENDING" && !isApproved);

    return matchSearch && matchApproval;
  });

  // KPI tóm tắt số liệu
  const totalCount = docs.length;
  const pendingCount = docs.filter((d) => d.ocr_status !== "APPROVED" && d.ocr_status !== "REJECTED").length;
  const approvedCount = docs.filter((d) => d.ocr_status === "APPROVED").length;
  const avgConfidence = docs.length > 0
    ? Math.round(docs.reduce((acc, cur) => acc + (cur.ocr_confidence ?? cur.confidence_score ?? 0.95), 0) / docs.length * 100)
    : 98;

  return (
    <div className="animate-fade-in" style={{ display: "flex", flexDirection: "column", gap: "1.25rem", width: "100%" }}>
      {/* Top Header */}
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", flexWrap: "wrap", gap: "1rem" }}>
        <div>
          <div style={{ display: "flex", alignItems: "center", gap: "0.75rem" }}>
            <h1 style={{ fontSize: "1.5rem", fontWeight: 800, color: "var(--gray-900)", letterSpacing: "-0.02em" }}>
              {isStaffOrAdmin ? "Quản lý & Phê duyệt Hồ sơ CTSV" : "Hồ sơ của tôi"}
            </h1>
            <Badge variant={user?.role === "ADMIN" ? "danger" : user?.role === "STAFF" ? "warning" : "info"}>
              {user?.role || "STUDENT"}
            </Badge>
          </div>
          <p style={{ fontSize: "0.875rem", color: "var(--gray-500)", marginTop: "0.25rem" }}>
            {isStaffOrAdmin
              ? "Trợ lý CTSV kiểm tra kết quả nhận dạng OCR, chỉnh sửa thông tin metadata và phê duyệt văn bản số."
              : "Theo dõi tiến độ nhận diện OCR và kết quả phê duyệt các hồ sơ, đơn từ của bạn."}
          </p>
        </div>

        <div style={{ display: "flex", gap: "0.625rem", flexWrap: "wrap", alignItems: "center" }}>
          {isStaffOrAdmin && (
            <a
              href={documentsApi.exportExcelUrl(statusFilter)}
              download
              target="_blank"
              rel="noreferrer"
              style={{ textDecoration: "none" }}
            >
              <Button variant="outline" size="sm" leftIcon={<FileText size={14} color="#16a34a" />}>
                Xuất Excel (.csv)
              </Button>
            </a>
          )}
          <Button
            variant="outline"
            size="sm"
            onClick={() => setIsCameraOpen(true)}
            leftIcon={<Camera size={15} color="#6366f1" />}
          >
            Chụp ảnh hồ sơ
          </Button>
          <Link to="/upload" style={{ textDecoration: "none" }}>
            <Button variant="primary" size="sm" leftIcon={<UploadCloud size={15} />}>
              Upload hồ sơ mới
            </Button>
          </Link>
        </div>
      </div>

      {/* Mini KPI Dashboard Cards */}
      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(200px, 1fr))", gap: "1rem" }}>
        <div style={{
          backgroundColor: "#fff",
          padding: "1rem 1.25rem",
          borderRadius: "0.75rem",
          border: "1px solid var(--border-color)",
          boxShadow: "0 1px 3px rgba(0,0,0,0.04)",
          display: "flex",
          alignItems: "center",
          gap: "1rem"
        }}>
          <div style={{ width: "42px", height: "42px", borderRadius: "0.5rem", backgroundColor: "var(--primary-50)", display: "flex", alignItems: "center", justifyContent: "center", color: "var(--primary-600)" }}>
            <FileText size={22} />
          </div>
          <div>
            <div style={{ fontSize: "0.75rem", fontWeight: 600, color: "var(--gray-500)", textTransform: "uppercase" }}>Tổng số hồ sơ</div>
            <div style={{ fontSize: "1.375rem", fontWeight: 800, color: "var(--gray-900)" }}>{totalCount}</div>
          </div>
        </div>

        <div style={{
          backgroundColor: "#fff",
          padding: "1rem 1.25rem",
          borderRadius: "0.75rem",
          border: "1px solid var(--border-color)",
          boxShadow: "0 1px 3px rgba(0,0,0,0.04)",
          display: "flex",
          alignItems: "center",
          gap: "1rem"
        }}>
          <div style={{ width: "42px", height: "42px", borderRadius: "0.5rem", backgroundColor: "#fef3c7", display: "flex", alignItems: "center", justifyContent: "center", color: "#d97706" }}>
            <Clock size={22} />
          </div>
          <div>
            <div style={{ fontSize: "0.75rem", fontWeight: 600, color: "var(--gray-500)", textTransform: "uppercase" }}>Chờ phê duyệt</div>
            <div style={{ fontSize: "1.375rem", fontWeight: 800, color: "#d97706" }}>{pendingCount}</div>
          </div>
        </div>

        <div style={{
          backgroundColor: "#fff",
          padding: "1rem 1.25rem",
          borderRadius: "0.75rem",
          border: "1px solid var(--border-color)",
          boxShadow: "0 1px 3px rgba(0,0,0,0.04)",
          display: "flex",
          alignItems: "center",
          gap: "1rem"
        }}>
          <div style={{ width: "42px", height: "42px", borderRadius: "0.5rem", backgroundColor: "#dcfce7", display: "flex", alignItems: "center", justifyContent: "center", color: "#16a34a" }}>
            <CheckCircle2 size={22} />
          </div>
          <div>
            <div style={{ fontSize: "0.75rem", fontWeight: 600, color: "var(--gray-500)", textTransform: "uppercase" }}>Đã phê duyệt</div>
            <div style={{ fontSize: "1.375rem", fontWeight: 800, color: "#16a34a" }}>{approvedCount}</div>
          </div>
        </div>

        <div style={{
          backgroundColor: "#fff",
          padding: "1rem 1.25rem",
          borderRadius: "0.75rem",
          border: "1px solid var(--border-color)",
          boxShadow: "0 1px 3px rgba(0,0,0,0.04)",
          display: "flex",
          alignItems: "center",
          gap: "1rem"
        }}>
          <div style={{ width: "42px", height: "42px", borderRadius: "0.5rem", backgroundColor: "#ede9fe", display: "flex", alignItems: "center", justifyContent: "center", color: "#7c3aed" }}>
            <Sparkles size={22} />
          </div>
          <div>
            <div style={{ fontSize: "0.75rem", fontWeight: 600, color: "var(--gray-500)", textTransform: "uppercase" }}>Số hóa hoàn tất</div>
            <div style={{ fontSize: "1.375rem", fontWeight: 800, color: "#7c3aed" }}>{documents.filter(d => d.ocr_status === "DONE" || d.ocr_status === "APPROVED").length}</div>
          </div>
        </div>
      </div>

      {/* Filter & Search Bar */}
      <Card padding="sm">
        <div style={{ display: "flex", gap: "1rem", flexWrap: "wrap", alignItems: "center", justifyContent: "space-between" }}>
          <div style={{ flex: "1 1 320px", position: "relative" }}>
            <Search size={16} color="var(--gray-400)" style={{ position: "absolute", left: "0.85rem", top: "50%", transform: "translateY(-50%)" }} />
            <input
              type="text"
              value={searchFilter}
              onChange={(e) => setSearchFilter(e.target.value)}
              placeholder="Tìm theo tên hồ sơ, số hiệu công văn, họ tên hoặc MSSV..."
              style={{
                width: "100%",
                padding: "0.55rem 0.85rem 0.55rem 2.4rem",
                borderRadius: "0.5rem",
                border: "1px solid var(--border-color)",
                fontSize: "0.875rem",
                backgroundColor: "var(--gray-50)",
                transition: "all 0.2s ease",
              }}
            />
          </div>

          <div style={{ display: "flex", gap: "0.75rem", alignItems: "center", flexWrap: "wrap" }}>
            <div style={{ display: "flex", gap: "0.5rem", alignItems: "center" }}>
              <span style={{ fontSize: "0.8125rem", fontWeight: 600, color: "var(--gray-600)" }}>Trạng thái OCR:</span>
              <select
                value={statusFilter}
                onChange={(e) => setStatusFilter(e.target.value)}
                style={{
                  padding: "0.45rem 0.75rem",
                  borderRadius: "0.5rem",
                  border: "1px solid var(--border-color)",
                  fontSize: "0.8125rem",
                  backgroundColor: "#fff",
                  fontWeight: 500,
                  cursor: "pointer",
                }}
              >
                <option value="ALL">Tất cả trạng thái</option>
                <option value="APPROVED">Đã duyệt (APPROVED)</option>
                <option value="DONE">OCR Xong (DONE)</option>
                <option value="PROCESSING">Đang xử lý</option>
                <option value="PENDING">Chờ xử lý</option>
                <option value="REJECTED">Từ chối (REJECTED)</option>
              </select>
            </div>

            <div style={{ display: "flex", gap: "0.5rem", alignItems: "center" }}>
              <span style={{ fontSize: "0.8125rem", fontWeight: 600, color: "var(--gray-600)" }}>Phê duyệt:</span>
              <select
                value={approvalFilter}
                onChange={(e) => setApprovalFilter(e.target.value)}
                style={{
                  padding: "0.45rem 0.75rem",
                  borderRadius: "0.5rem",
                  border: "1px solid var(--border-color)",
                  fontSize: "0.8125rem",
                  backgroundColor: "#fff",
                  fontWeight: 500,
                  cursor: "pointer",
                }}
              >
                <option value="ALL">Tất cả</option>
                <option value="APPROVED">Đã phê duyệt</option>
                <option value="PENDING">Chưa phê duyệt</option>
              </select>
            </div>

            <Button
              variant="outline"
              size="sm"
              onClick={fetchDocuments}
              leftIcon={<RefreshCw size={14} className={isLoading ? "animate-spin" : ""} />}
            >
              Làm mới
            </Button>
          </div>
        </div>
      </Card>

      {/* Main Documents Table */}
      <Card padding="none">
        <div style={{ width: "100%", overflowX: "auto" }}>
          <table style={{ width: "100%", borderCollapse: "collapse", tableLayout: "auto", minWidth: "900px" }}>
            <thead>
              <tr style={{
                backgroundColor: "var(--gray-50)",
                borderBottom: "1px solid var(--border-color)",
                color: "var(--gray-600)",
                fontSize: "0.8125rem",
                fontWeight: 700,
                textAlign: "left",
                letterSpacing: "0.02em"
              }}>
                <th style={{ padding: "0.85rem 1.25rem", width: "32%" }}>TIÊU ĐỀ & THÔNG TIN HỒ SƠ</th>
                <th style={{ padding: "0.85rem 1rem", width: "18%" }}>NGƯỜI NỘP / MSSV</th>
                <th style={{ padding: "0.85rem 1rem", width: "14%" }}>DANH MỤC</th>
                <th style={{ padding: "0.85rem 1rem", width: "12%" }}>TIẾN ĐỘ OCR</th>
                <th style={{ padding: "0.85rem 0.75rem", width: "10%" }}>PHÊ DUYỆT</th>
                <th style={{ padding: "0.85rem 1.25rem", width: "14%", textAlign: "right" }}>THAO TÁC</th>
              </tr>
            </thead>
            <tbody>
              {filteredDocs.length === 0 ? (
                <tr>
                  <td colSpan={6} style={{ padding: "3.5rem 1rem", textAlign: "center", color: "var(--gray-400)" }}>
                    <FileText size={40} style={{ margin: "0 auto 0.75rem", opacity: 0.4 }} />
                    <p style={{ fontSize: "0.9375rem", fontWeight: 500 }}>Không tìm thấy hồ sơ nào phù hợp.</p>
                    <p style={{ fontSize: "0.8125rem", color: "var(--gray-400)", marginTop: "0.25rem" }}>Thử thay đổi bộ lọc hoặc tải lên hồ sơ mới.</p>
                  </td>
                </tr>
              ) : (
                filteredDocs.map((doc) => {
                  const isApproved = doc.ocr_status === "APPROVED";
                  const isRejected = doc.ocr_status === "REJECTED";
                  const { mainTitle, code } = formatDisplayTitle(doc.title);

                  return (
                    <tr
                      key={doc.id}
                      style={{
                        borderBottom: "1px solid var(--border-light)",
                        transition: "background-color 0.15s ease",
                      }}
                      onMouseEnter={(e) => (e.currentTarget.style.backgroundColor = "rgba(243, 244, 246, 0.6)")}
                      onMouseLeave={(e) => (e.currentTarget.style.backgroundColor = "transparent")}
                    >
                      {/* Tiêu đề & Thông tin file */}
                      <td style={{ padding: "1rem 1.25rem" }}>
                        <div style={{ display: "flex", alignItems: "flex-start", gap: "0.625rem" }}>
                          <div style={{
                            padding: "0.4rem",
                            borderRadius: "0.375rem",
                            backgroundColor: doc.file_type?.toLowerCase() === "pdf" ? "#fee2e2" : "#e0e7ff",
                            color: doc.file_type?.toLowerCase() === "pdf" ? "#dc2626" : "#4338ca",
                            fontWeight: 700,
                            fontSize: "0.6875rem",
                            lineHeight: 1,
                            flexShrink: 0,
                            marginTop: "0.15rem"
                          }}>
                            {doc.file_type || "PDF"}
                          </div>
                          <div>
                            <Link
                              to={`/documents/${doc.id}`}
                              style={{
                                color: "var(--primary-700)",
                                fontWeight: 600,
                                fontSize: "0.875rem",
                                textDecoration: "none",
                                display: "-webkit-box",
                                WebkitLineClamp: 2,
                                WebkitBoxOrient: "vertical",
                                overflow: "hidden",
                                lineHeight: "1.35",
                              }}
                            >
                              {mainTitle}
                            </Link>
                            <div style={{ display: "flex", alignItems: "center", gap: "0.5rem", fontSize: "0.75rem", color: "var(--gray-400)", marginTop: "0.25rem" }}>
                              {code && <span style={{ color: "var(--primary-600)", fontWeight: 600 }}>{code}</span>}
                              {code && <span>•</span>}
                              <span>{(doc.file_size_bytes / (1024 * 1024)).toFixed(2)} MB</span>
                              <span>•</span>
                              <span>{new Date(doc.created_at).toLocaleDateString("vi-VN")}</span>
                            </div>
                          </div>
                        </div>
                      </td>

                      {/* Người nộp / MSSV */}
                      <td style={{ padding: "1rem 1rem", verticalAlign: "middle" }}>
                        <div style={{ fontWeight: 600, color: "var(--gray-800)", fontSize: "0.8125rem" }}>
                          {doc.student_name || doc.uploader_name || "Cán bộ CTSV (Đại học Đà Lạt)"}
                        </div>
                        <div style={{ fontSize: "0.75rem", color: "var(--gray-400)", marginTop: "0.15rem" }}>
                          {doc.student_id || doc.uploader_mssv ? (
                            <span style={{ backgroundColor: "var(--gray-100)", padding: "0.1rem 0.35rem", borderRadius: "0.25rem", fontFamily: "monospace" }}>
                              MSSV: {doc.student_id || doc.uploader_mssv}
                            </span>
                          ) : (
                            <span style={{ color: "var(--gray-400)" }}>Trường Đại học Đà Lạt</span>
                          )}
                        </div>
                      </td>

                      {/* Danh mục */}
                      <td style={{ padding: "1rem 1rem", verticalAlign: "middle", color: "var(--gray-700)", fontSize: "0.8125rem" }}>
                        <span style={{
                          display: "inline-block",
                          padding: "0.2rem 0.5rem",
                          borderRadius: "0.375rem",
                          backgroundColor: "var(--gray-100)",
                          fontWeight: 500,
                          fontSize: "0.75rem",
                          color: "var(--gray-700)"
                        }}>
                          {doc.category_name || "Chưa phân loại"}
                        </span>
                      </td>

                      {/* Trạng thái OCR */}
                      <td style={{ padding: "1rem 1rem", verticalAlign: "middle" }}>
                        <OCRStatusBadge status={doc.ocr_status as any} />
                      </td>

                      {/* Trạng thái Phê duyệt */}
                      <td style={{ padding: "1rem 0.75rem", verticalAlign: "middle" }}>
                        {isApproved ? (
                          <Badge variant="success" dot>Đã duyệt</Badge>
                        ) : isRejected ? (
                          <Badge variant="danger" dot>Từ chối</Badge>
                        ) : (
                          <Badge variant="warning" dot>Chờ duyệt</Badge>
                        )}
                      </td>

                      {/* Hành động */}
                      <td style={{ padding: "1rem 1.25rem", verticalAlign: "middle", textAlign: "right" }}>
                        <div style={{ display: "inline-flex", gap: "0.35rem", alignItems: "center", justifyContent: "flex-end" }}>
                          <Link to={`/documents/${doc.id}`} style={{ textDecoration: "none" }}>
                            <Button variant="outline" size="sm" leftIcon={<Eye size={13} />}>
                              Chi tiết
                            </Button>
                          </Link>

                          {isStaffOrAdmin && (
                            <>
                              {!isApproved && (
                                <Button
                                  variant="primary"
                                  size="sm"
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
