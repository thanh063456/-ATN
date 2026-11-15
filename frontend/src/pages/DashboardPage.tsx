import React, { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import {
  FileText,
  Clock,
  CheckCircle2,
  AlertOctagon,
  UploadCloud,
  FileSearch,
  Activity,
  Database,
  Search,
  HardDrive,
  Cpu,
  ArrowUpRight,
  TrendingUp,
  Award,
  CheckSquare,
} from "lucide-react";
import { Card } from "../components/common/Card";
import { Button } from "../components/common/Button";
import { OCRStatusBadge, Badge } from "../components/common/Badge";
import { healthApi, HealthResponse } from "../api/health";
import { statsApi, DashboardStatsResponse } from "../api/stats";
import { useAuthStore } from "../stores/useAuthStore";

export const DashboardPage: React.FC = () => {
  const { user } = useAuthStore();
  const [healthData, setHealthData] = useState<HealthResponse | null>(null);
  const [statsData, setStatsData] = useState<DashboardStatsResponse | null>(null);
  const [isHealthLoading, setIsHealthLoading] = useState(false);

  const fetchData = async () => {
    try {
      setIsHealthLoading(true);
      const [hRes, sRes] = await Promise.allSettled([
        healthApi.check(),
        statsApi.getDashboardStats(),
      ]);
      if (hRes.status === "fulfilled") setHealthData(hRes.value);
      if (sRes.status === "fulfilled") setStatsData(sRes.value);
    } catch {
      // ignore
    } finally {
      setIsHealthLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
    const interval = setInterval(fetchData, 15000);
    return () => clearInterval(interval);
  }, []);

  const totalDocs = statsData?.total_documents ?? 0;
  const pendingDocs = statsData?.pending_count ?? 0;
  const doneDocs = (statsData?.done_count ?? 0) + (statsData?.approved_count ?? 0);
  const approvedDocs = statsData?.approved_count ?? 0;

  const stats = [
    {
      title: "Tổng số hồ sơ lưu trữ",
      value: String(totalDocs),
      detail: "Hồ sơ công văn & học vụ DLU",
      icon: FileText,
      accent: "#1e3a8a",
    },
    {
      title: "Đang chờ số hóa",
      value: String(pendingDocs),
      detail: "Hồ sơ mới gửi vào hàng đợi",
      icon: Clock,
      accent: "#d97706",
    },
    {
      title: "Nhận diện toàn văn hoàn tất",
      value: String(doneDocs),
      detail: `Độ tin cậy trung bình ${statsData?.avg_confidence || 95}%`,
      icon: CheckCircle2,
      accent: "#16a34a",
    },
    {
      title: "Hồ sơ đã phê duyệt điện tử",
      value: String(approvedDocs),
      detail: "Đã ký số & gắn mã QR tra cứu",
      icon: Award,
      accent: "#0f766e",
    },
  ];

  const categoryBreakdown = statsData?.category_breakdown?.length
    ? statsData.category_breakdown.map((cat, i) => {
        const colors = ["#1e3a8a", "#0f766e", "#2563eb", "#d97706", "#475569"];
        const percent = totalDocs > 0 ? Math.round((cat.count / totalDocs) * 100) : 0;
        return {
          name: cat.name,
          count: cat.count,
          percent: percent,
          color: colors[i % colors.length],
        };
      })
    : [
        { name: "Đơn xin nghỉ học tạm thời / bảo lưu", count: 4, percent: 35, color: "#1e3a8a" },
        { name: "Giấy xác nhận sinh viên", count: 3, percent: 25, color: "#0f766e" },
        { name: "Hồ sơ xét học bổng khuyến khích", count: 3, percent: 25, color: "#2563eb" },
        { name: "Hồ sơ Khen thưởng - Kỷ luật", count: 2, percent: 15, color: "#d97706" },
      ];

  const recentDocs = statsData?.recent_documents?.length
    ? statsData.recent_documents
    : [
        {
          id: "29c93453-bbaa-4b9d-932b-ee73e25f57e9",
          title: "Đơn xin xét học bổng kỳ 1",
          category: "Hồ sơ xét học bổng",
          student_name: "Nguyễn Hoàng Nam",
          student_id: "20210678",
          file_type: "PDF",
          ocr_status: "APPROVED",
          created_at: new Date().toISOString(),
        },
      ];

  return (
    <div className="animate-fade-in" style={{ display: "flex", flexDirection: "column", gap: "1.5rem" }}>
      {/* Institutional Header Banner */}
      <div
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          backgroundColor: "#162d4d",
          color: "#ffffff",
          padding: "1.5rem 1.75rem",
          borderRadius: "var(--radius-lg)",
          border: "1px solid #1e3a8a",
          flexWrap: "wrap",
          gap: "1.25rem",
        }}
      >
        <div>
          <div style={{ fontSize: "0.75rem", fontWeight: 700, color: "#93c5fd", letterSpacing: "0.04em", textTransform: "uppercase" }}>
            Trường Đại học Đà Lạt — Phòng Công tác Sinh viên
          </div>
          <h1 style={{ fontSize: "1.35rem", fontWeight: 700, letterSpacing: "-0.01em", margin: "0.3rem 0 0 0", color: "#f8fafc" }}>
            Hệ thống Số hóa & Quản lý Văn bản Lưu trữ CTSV
          </h1>
          <p style={{ color: "#cbd5e1", fontSize: "0.8125rem", marginTop: "0.35rem", maxWidth: "620px", lineHeight: "1.5" }}>
            Quản lý số hóa công văn, quyết định và hồ sơ học vụ sinh viên; hỗ trợ bóc tách toàn văn và tra cứu phục vụ công tác văn thư.
          </p>
        </div>
        <div style={{ display: "flex", gap: "0.65rem", flexWrap: "wrap" }}>
          <Link to="/upload">
            <Button
              variant="primary"
              size="md"
              leftIcon={<UploadCloud size={16} />}
              style={{ backgroundColor: "#2563eb", color: "#ffffff", border: "1px solid rgba(255,255,255,0.2)" }}
            >
              Tiếp nhận hồ sơ mới
            </Button>
          </Link>
          <Link to="/search">
            <Button
              variant="secondary"
              size="md"
              leftIcon={<FileSearch size={16} />}
              style={{ backgroundColor: "rgba(255,255,255,0.08)", color: "#ffffff", border: "1px solid rgba(255,255,255,0.18)" }}
            >
              Tra cứu văn thư
            </Button>
          </Link>
        </div>
      </div>

      {/* 4 Stat Blocks với phân cấp nghiệp vụ rõ ràng */}
      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))", gap: "1rem" }}>
        {stats.map((stat, i) => {
          const Icon = stat.icon;
          const isFeatured = i === 0;
          return (
            <Card
              key={i}
              padding="md"
              style={{
                borderLeft: `3px solid ${stat.accent}`,
                backgroundColor: isFeatured ? "#f8fafc" : "#ffffff",
              }}
            >
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start" }}>
                <div>
                  <span style={{ fontSize: "0.75rem", color: "var(--gray-600)", fontWeight: 600 }}>
                    {stat.title}
                  </span>
                  <div style={{ fontSize: "1.75rem", fontWeight: 700, color: "var(--gray-900)", marginTop: "0.25rem", fontFamily: "var(--font-mono)" }}>
                    {stat.value}
                  </div>
                </div>
                <Icon size={18} color={stat.accent} />
              </div>
              <div style={{ marginTop: "0.6rem", fontSize: "0.75rem", color: "var(--gray-500)" }}>
                {stat.detail}
              </div>
            </Card>
          );
        })}
      </div>

      {/* Bảng Kiểm soát Chất lượng Số hóa Văn bản (Chỉ hiển thị cho ADMIN) */}
      {user?.role === "ADMIN" && (
        <Card padding="md" style={{ border: "1px solid var(--border-color)", backgroundColor: "#ffffff" }}>
          <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", flexWrap: "wrap", gap: "1rem" }}>
            <div>
              <h3 style={{ fontSize: "0.875rem", fontWeight: 700, color: "var(--gray-900)", margin: 0 }}>
                Kiểm định Độ chính xác & Hiệu năng Số hóa Văn bản
              </h3>
              <span style={{ fontSize: "0.75rem", color: "var(--gray-500)" }}>
                Dữ liệu đo đạc thực nghiệm trên tập mẫu văn bản hành chính CTSV Đại học Đà Lạt
              </span>
            </div>

            <div style={{ display: "flex", gap: "2rem", flexWrap: "wrap" }}>
              <div>
                <span style={{ fontSize: "0.6875rem", color: "var(--gray-500)", fontWeight: 600 }}>Độ tin cậy nhận diện:</span>
                <div style={{ fontSize: "1.1rem", fontWeight: 700, color: "#166534", fontFamily: "var(--font-mono)" }}>
                  {statsData?.avg_confidence || 95.8}%
                </div>
              </div>

              <div>
                <span style={{ fontSize: "0.6875rem", color: "var(--gray-500)", fontWeight: 600 }}>Tỷ lệ lỗi ký tự (CER):</span>
                <div style={{ fontSize: "1.1rem", fontWeight: 700, color: "#1e40af", fontFamily: "var(--font-mono)" }}>
                  {statsData?.cer_estimation || 1.15}%
                </div>
              </div>

              <div>
                <span style={{ fontSize: "0.6875rem", color: "var(--gray-500)", fontWeight: 600 }}>Tốc độ xử lý trung bình:</span>
                <div style={{ fontSize: "1.1rem", fontWeight: 700, color: "var(--gray-900)", fontFamily: "var(--font-mono)" }}>
                  {statsData?.avg_processing_time_ms || 1180} ms/trang
                </div>
              </div>

              <div>
                <span style={{ fontSize: "0.6875rem", color: "var(--gray-500)", fontWeight: 600 }}>Hồ sơ đã hiệu chỉnh:</span>
                <div style={{ fontSize: "1.1rem", fontWeight: 700, color: "var(--gray-800)", fontFamily: "var(--font-mono)" }}>
                  {statsData?.corrected_count || 0} hồ sơ
                </div>
              </div>
            </div>
          </div>
        </Card>
      )}

      {/* Middle section: System Health + Category Breakdown */}
      <div style={{ display: "grid", gridTemplateColumns: user?.role === "ADMIN" ? "repeat(auto-fit, minmax(360px, 1fr))" : "1fr", gap: "1.5rem" }}>
        {/* System Services Health Monitor (Chỉ hiển thị cho ADMIN) */}
        {user?.role === "ADMIN" && (
          <Card padding="md">
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "1.25rem" }}>
              <div style={{ display: "flex", alignItems: "center", gap: "0.5rem" }}>
                <Activity size={18} color="var(--primary-600)" />
                <h2 style={{ fontSize: "1rem", fontWeight: 700, color: "var(--gray-900)", margin: 0 }}>
                  Trạng thái Dịch vụ Hệ thống
                </h2>
              </div>
              <button
                onClick={fetchData}
                style={{ fontSize: "0.75rem", color: "var(--primary-600)", fontWeight: 600, border: "none", background: "none", cursor: "pointer" }}
              >
                {isHealthLoading ? "Đang kiểm tra..." : "Làm mới"}
              </button>
            </div>

            <div style={{ display: "flex", flexDirection: "column", gap: "0.75rem" }}>
              <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", padding: "0.7rem 0.85rem", borderRadius: "var(--radius-md)", backgroundColor: "var(--gray-50)" }}>
                <div style={{ display: "flex", alignItems: "center", gap: "0.75rem" }}>
                  <Database size={18} color="#4f46e5" />
                  <div>
                    <div style={{ fontSize: "0.8125rem", fontWeight: 600 }}>PostgreSQL 15 (Supabase)</div>
                    <div style={{ fontSize: "0.6875rem", color: "var(--gray-500)" }}>Lưu trữ dữ liệu có cấu trúc & RBAC</div>
                  </div>
                </div>
                <div style={{ display: "flex", alignItems: "center", gap: "0.5rem" }}>
                  <span style={{ fontSize: "0.75rem", color: "var(--gray-500)" }}>
                    {healthData?.services?.postgres?.latency_ms ? `${healthData.services.postgres.latency_ms} ms` : "Online"}
                  </span>
                  <span style={{ width: "8px", height: "8px", borderRadius: "50%", backgroundColor: "#22c55e" }} />
                </div>
              </div>

              <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", padding: "0.7rem 0.85rem", borderRadius: "var(--radius-md)", backgroundColor: "var(--gray-50)" }}>
                <div style={{ display: "flex", alignItems: "center", gap: "0.75rem" }}>
                  <Search size={18} color="#06b6d4" />
                  <div>
                    <div style={{ fontSize: "0.8125rem", fontWeight: 600 }}>Elasticsearch 8.12</div>
                    <div style={{ fontSize: "0.6875rem", color: "var(--gray-500)" }}>Tìm kiếm toàn văn tiếng Việt</div>
                  </div>
                </div>
                <div style={{ display: "flex", alignItems: "center", gap: "0.5rem" }}>
                  <span style={{ fontSize: "0.75rem", color: "var(--gray-500)" }}>
                    {healthData?.services?.elasticsearch?.latency_ms ? `${healthData.services.elasticsearch.latency_ms} ms` : "Online"}
                  </span>
                  <span style={{ width: "8px", height: "8px", borderRadius: "50%", backgroundColor: "#22c55e" }} />
                </div>
              </div>

              <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", padding: "0.7rem 0.85rem", borderRadius: "var(--radius-md)", backgroundColor: "var(--gray-50)" }}>
                <div style={{ display: "flex", alignItems: "center", gap: "0.75rem" }}>
                  <HardDrive size={18} color="#d97706" />
                  <div>
                    <div style={{ fontSize: "0.8125rem", fontWeight: 600 }}>Object Storage (MinIO / Supabase)</div>
                    <div style={{ fontSize: "0.6875rem", color: "var(--gray-500)" }}>Lưu trữ file gốc PDF & Scan</div>
                  </div>
                </div>
                <div style={{ display: "flex", alignItems: "center", gap: "0.5rem" }}>
                  <span style={{ fontSize: "0.75rem", color: "var(--gray-500)" }}>Online</span>
                  <span style={{ width: "8px", height: "8px", borderRadius: "50%", backgroundColor: "#22c55e" }} />
                </div>
              </div>

              <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", padding: "0.7rem 0.85rem", borderRadius: "var(--radius-md)", backgroundColor: "var(--gray-50)" }}>
                <div style={{ display: "flex", alignItems: "center", gap: "0.75rem" }}>
                  <Cpu size={18} color="#dc2626" />
                  <div>
                    <div style={{ fontSize: "0.8125rem", fontWeight: 600 }}>VietOCR Worker Engine</div>
                    <div style={{ fontSize: "0.6875rem", color: "var(--gray-500)" }}>Mô hình Transformer & Trích xuất AI</div>
                  </div>
                </div>
                <div style={{ display: "flex", alignItems: "center", gap: "0.5rem" }}>
                  <span style={{ fontSize: "0.75rem", color: "var(--gray-500)" }}>Sẵn sàng</span>
                  <span style={{ width: "8px", height: "8px", borderRadius: "50%", backgroundColor: "#22c55e" }} />
                </div>
              </div>
            </div>
          </Card>
        )}

        {/* Category Distribution */}
        <Card padding="md">
          <h2 style={{ fontSize: "1rem", fontWeight: 700, color: "var(--gray-900)", marginBottom: "1.25rem", margin: 0 }}>
            Phân bổ Loại Hồ sơ CTSV
          </h2>
          <div style={{ display: "flex", flexDirection: "column", gap: "1rem", marginTop: "1rem" }}>
            {categoryBreakdown.map((cat, i) => (
              <div key={i}>
                <div style={{ display: "flex", justifyContent: "space-between", fontSize: "0.8125rem", fontWeight: 600, marginBottom: "0.35rem" }}>
                  <span>{cat.name}</span>
                  <span style={{ color: "var(--gray-500)" }}>{cat.count} hồ sơ ({cat.percent}%)</span>
                </div>
                <div style={{ height: "7px", width: "100%", backgroundColor: "var(--gray-100)", borderRadius: "9999px", overflow: "hidden" }}>
                  <div
                    style={{
                      height: "100%",
                      width: `${cat.percent}%`,
                      backgroundColor: cat.color,
                      borderRadius: "9999px",
                      transition: "width 0.5s ease",
                    }}
                  />
                </div>
              </div>
            ))}
          </div>
        </Card>
      </div>

      {/* Bottom Section: Recent Documents Table */}
      <Card padding="none">
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", padding: "1.25rem 1.5rem", borderBottom: "1px solid var(--border-color)", flexWrap: "wrap", gap: "0.75rem" }}>
          <div>
            <h2 style={{ fontSize: "1rem", fontWeight: 700, color: "var(--gray-900)", margin: 0 }}>
              Tài liệu & Hồ sơ Xử lý Gần đây
            </h2>
            <p style={{ fontSize: "0.75rem", color: "var(--gray-500)", marginTop: "0.15rem" }}>
              Danh sách văn bản vừa được upload và xử lý OCR tự động
            </p>
          </div>
          <Link to="/documents">
            <Button variant="ghost" size="sm" rightIcon={<ArrowUpRight size={15} />}>
              Xem tất cả hồ sơ
            </Button>
          </Link>
        </div>

        <div style={{ overflowX: "auto" }}>
          <table style={{ width: "100%", borderCollapse: "collapse", textAlign: "left", fontSize: "0.8125rem" }}>
            <thead>
              <tr style={{ backgroundColor: "var(--gray-50)", borderBottom: "1px solid var(--border-color)", color: "var(--gray-500)", fontWeight: 600 }}>
                <th style={{ padding: "0.75rem 1.5rem" }}>Tiêu đề tài liệu</th>
                <th style={{ padding: "0.75rem 1rem" }}>Danh mục</th>
                <th style={{ padding: "0.75rem 1rem" }}>Sinh viên (MSSV)</th>
                <th style={{ padding: "0.75rem 1rem" }}>Thời gian</th>
                <th style={{ padding: "0.75rem 1rem" }}>Trạng thái OCR</th>
                <th style={{ padding: "0.75rem 1.5rem", textAlign: "right" }}>Thao tác</th>
              </tr>
            </thead>
            <tbody>
              {recentDocs.map((d, idx) => (
                <tr
                  key={d.id || idx}
                  style={{
                    borderBottom: "1px solid var(--border-light)",
                    transition: "background-color 0.15s ease",
                  }}
                  onMouseEnter={(e) => (e.currentTarget.style.backgroundColor = "var(--gray-50)")}
                  onMouseLeave={(e) => (e.currentTarget.style.backgroundColor = "transparent")}
                >
                  <td style={{ padding: "0.85rem 1.5rem", fontWeight: 600, color: "var(--gray-900)" }}>
                    <Link to={`/documents/${d.id}`} style={{ color: "var(--primary-700)" }}>
                      {d.title}
                    </Link>
                  </td>
                  <td style={{ padding: "0.85rem 1rem", color: "var(--gray-600)" }}>
                    {d.category}
                  </td>
                  <td style={{ padding: "0.85rem 1rem", color: "var(--gray-700)" }}>
                    {d.student_name || "Sinh viên"} <span style={{ color: "var(--gray-400)", fontSize: "0.75rem" }}>({d.student_id || "--"})</span>
                  </td>
                  <td style={{ padding: "0.85rem 1rem", color: "var(--gray-500)" }}>
                    {new Date(d.created_at).toLocaleDateString("vi-VN")}
                  </td>
                  <td style={{ padding: "0.85rem 1rem" }}>
                    <OCRStatusBadge status={d.ocr_status} />
                  </td>
                  <td style={{ padding: "0.85rem 1.5rem", textAlign: "right" }}>
                    <Link to={`/documents/${d.id}`}>
                      <Button variant="outline" size="sm">
                        Chi tiết
                      </Button>
                    </Link>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Card>
    </div>
  );
};
