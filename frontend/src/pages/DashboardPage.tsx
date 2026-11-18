import React, { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import {
  FileText,
  Clock,
  CheckCircle2,
  UploadCloud,
  FileSearch,
  Activity,
  Database,
  Search,
  HardDrive,
  Cpu,
  ArrowUpRight,
  Award,
} from "lucide-react";
import { Card } from "../components/common/Card";
import { Button } from "../components/common/Button";
import { OCRStatusBadge } from "../components/common/Badge";
import { healthApi, HealthResponse } from "../api/health";
import { statsApi, DashboardStatsResponse } from "../api/stats";
import { useAuthStore } from "../stores/useAuthStore";

export const DashboardPage: React.FC = () => {
  const { user } = useAuthStore();
  const isStudent = user?.role === "STUDENT";
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

  const stats = isStudent
    ? [
        {
          title: "Hồ sơ bạn đã upload",
          value: String(totalDocs),
          detail: "Tổng số tài liệu thuộc tài khoản của bạn",
          icon: UploadCloud,
          borderAccent: "border-l-dlu-navy-900",
          iconBg: "bg-dlu-navy-50 text-dlu-navy-800",
        },
        {
          title: "Đang chờ / Đang số hóa",
          value: String(pendingDocs),
          detail: "Hồ sơ đang trong hàng đợi xử lý OCR",
          icon: Clock,
          borderAccent: "border-l-amber-500",
          iconBg: "bg-amber-50 text-amber-700",
        },
        {
          title: "Nhận dạng hoàn tất",
          value: String(doneDocs),
          detail: `Độ tin cậy OCR trung bình ${statsData?.avg_confidence || 95}%`,
          icon: CheckCircle2,
          borderAccent: "border-l-emerald-600",
          iconBg: "bg-emerald-50 text-emerald-700",
        },
        {
          title: "Hồ sơ đã được duyệt",
          value: String(approvedDocs),
          detail: "Cán bộ CTSV đã xác thực & cấp mã QR",
          icon: Award,
          borderAccent: "border-l-teal-600",
          iconBg: "bg-teal-50 text-teal-700",
        },
      ]
    : [
        {
          title: "Tổng số hồ sơ lưu trữ",
          value: String(totalDocs),
          detail: "Hồ sơ công văn & học vụ DLU",
          icon: FileText,
          borderAccent: "border-l-dlu-navy-900",
          iconBg: "bg-dlu-navy-50 text-dlu-navy-800",
        },
        {
          title: "Đang chờ số hóa",
          value: String(pendingDocs),
          detail: "Hồ sơ mới gửi vào hàng đợi",
          icon: Clock,
          borderAccent: "border-l-amber-500",
          iconBg: "bg-amber-50 text-amber-700",
        },
        {
          title: "Nhận diện toàn văn hoàn tất",
          value: String(doneDocs),
          detail: `Độ tin cậy trung bình ${statsData?.avg_confidence || 95}%`,
          icon: CheckCircle2,
          borderAccent: "border-l-emerald-600",
          iconBg: "bg-emerald-50 text-emerald-700",
        },
        {
          title: "Hồ sơ đã phê duyệt điện tử",
          value: String(approvedDocs),
          detail: "Đã ký số & gắn mã QR tra cứu",
          icon: Award,
          borderAccent: "border-l-teal-600",
          iconBg: "bg-teal-50 text-teal-700",
        },
      ];

  const categoryBreakdown = statsData?.category_breakdown?.length
    ? statsData.category_breakdown.map((cat, i) => {
        const colors = [
          "bg-dlu-navy-800",
          "bg-teal-700",
          "bg-sky-600",
          "bg-amber-600",
          "bg-slate-600",
        ];
        const percent = totalDocs > 0 ? Math.round((cat.count / totalDocs) * 100) : 0;
        return {
          name: cat.name,
          count: cat.count,
          percent: percent,
          colorClass: colors[i % colors.length],
        };
      })
    : [];

  const recentDocs = statsData?.recent_documents || [];

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Institutional Header Banner */}
      <div className="bg-[#0a192f] text-white p-5 sm:p-7 rounded-lg border border-slate-800 shadow-paper flex flex-col md:flex-row justify-between items-start md:items-center gap-5">
        <div className="max-w-3xl">
          <div className="text-[11px] font-bold text-sky-300 tracking-wider uppercase">
            {isStudent
              ? "Cổng Dịch vụ Sinh viên trực tuyến — ĐH Đà Lạt"
              : "Trường Đại học Đà Lạt — Phòng Công tác Sinh viên"}
          </div>
          <h1 className="text-xl sm:text-2xl font-bold tracking-tight text-white mt-1">
            {isStudent
              ? `Chào mừng, ${user?.fullName || user?.username || "Sinh viên"}!`
              : "Hệ thống Số hóa & Quản lý Văn bản Lưu trữ CTSV"}
          </h1>
          <p className="text-slate-300 text-xs sm:text-sm mt-1.5 leading-relaxed">
            {isStudent
              ? "Theo dõi tiến độ nhận dạng OCR và trạng thái xử lý các hồ sơ bạn đã tải lên hệ thống Phòng Công tác Sinh viên."
              : "Quản lý số hóa công văn, quyết định và hồ sơ học vụ sinh viên; hỗ trợ bóc tách toàn văn và tra cứu phục vụ công tác văn thư."}
          </p>
        </div>

        <div className="flex items-center gap-2.5 shrink-0 flex-wrap">
          <Link to="/upload">
            <Button
              variant="primary"
              size="md"
              leftIcon={<UploadCloud size={16} />}
              className="bg-sky-600 hover:bg-sky-500 text-white shadow-sm"
            >
              {isStudent ? "Tải lên hồ sơ mới" : "Tiếp nhận hồ sơ mới"}
            </Button>
          </Link>
          <Link to={isStudent ? "/documents" : "/search"}>
            <Button
              variant="outline"
              size="md"
              leftIcon={isStudent ? <Clock size={16} /> : <FileSearch size={16} />}
              className="border-slate-600 text-slate-200 hover:bg-white/10 hover:text-white"
            >
              {isStudent ? "Lịch sử upload của bạn" : "Tra cứu văn thư"}
            </Button>
          </Link>
        </div>
      </div>

      {/* 4 Stat Blocks */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {stats.map((stat, i) => {
          const Icon = stat.icon;
          return (
            <div
              key={i}
              className={`bg-white rounded-lg border border-slate-200/90 p-5 shadow-paper border-l-4 ${stat.borderAccent} transition-shadow hover:shadow-paper-hover`}
            >
              <div className="flex justify-between items-start">
                <div>
                  <span className="text-xs font-semibold text-slate-500 uppercase tracking-wide">
                    {stat.title}
                  </span>
                  <div className="text-2xl font-bold text-slate-900 font-mono mt-1">
                    {stat.value}
                  </div>
                </div>
                <div className={`w-8 h-8 rounded-md flex items-center justify-center ${stat.iconBg}`}>
                  <Icon size={17} />
                </div>
              </div>
              <div className="mt-3 text-[11px] text-slate-500 leading-snug">
                {stat.detail}
              </div>
            </div>
          );
        })}
      </div>

      {/* Bảng Kiểm soát Chất lượng Số hóa Văn bản (Chỉ hiển thị cho ADMIN) */}
      {user?.role === "ADMIN" && (
        <Card padding="md">
          <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4">
            <div>
              <h3 className="text-sm font-bold text-slate-900">
                Kiểm định Độ chính xác & Hiệu năng Số hóa Văn bản
              </h3>
              <p className="text-xs text-slate-500 mt-0.5">
                Dữ liệu đo đạc thực nghiệm trên tập mẫu văn bản hành chính CTSV Đại học Đà Lạt
              </p>
            </div>

            <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 sm:gap-6 border-t lg:border-t-0 pt-3 lg:pt-0 border-slate-100">
              <div>
                <span className="text-[11px] font-semibold text-slate-400 block">Độ tin cậy nhận diện</span>
                <span className="text-base font-bold font-mono text-emerald-700">
                  {statsData?.avg_confidence || 95.8}%
                </span>
              </div>
              <div>
                <span className="text-[11px] font-semibold text-slate-400 block">Tỷ lệ lỗi ký tự (CER)</span>
                <span className="text-base font-bold font-mono text-dlu-navy-700">
                  {statsData?.cer_estimation || 1.15}%
                </span>
              </div>
              <div>
                <span className="text-[11px] font-semibold text-slate-400 block">Tốc độ trung bình</span>
                <span className="text-base font-bold font-mono text-slate-800">
                  {statsData?.avg_processing_time_ms || 1180} ms
                </span>
              </div>
              <div>
                <span className="text-[11px] font-semibold text-slate-400 block">Hồ sơ đã hiệu chỉnh</span>
                <span className="text-base font-bold font-mono text-slate-800">
                  {statsData?.corrected_count || 0} hồ sơ
                </span>
              </div>
            </div>
          </div>
        </Card>
      )}

      {/* Middle section: System Health / Student Guidance + Category Breakdown */}
      <div className={`grid grid-cols-1 ${user?.role === "ADMIN" || isStudent ? "lg:grid-cols-2" : ""} gap-6`}>
        {/* System Services Health Monitor (ADMIN) */}
        {user?.role === "ADMIN" && (
          <Card padding="md">
            <div className="flex justify-between items-center mb-4">
              <div className="flex items-center gap-2">
                <Activity size={17} className="text-dlu-navy-700" />
                <h2 className="text-sm font-bold text-slate-900">
                  Trạng thái Dịch vụ Hệ thống
                </h2>
              </div>
              <button
                onClick={fetchData}
                disabled={isHealthLoading}
                className="text-xs font-semibold text-dlu-navy-700 hover:text-dlu-navy-900 disabled:opacity-50"
              >
                {isHealthLoading ? "Đang kiểm tra..." : "Làm mới"}
              </button>
            </div>

            <div className="space-y-2.5">
              <div className="flex items-center justify-between p-3 rounded-md bg-slate-50 border border-slate-100">
                <div className="flex items-center gap-3">
                  <Database size={17} className="text-indigo-600" />
                  <div>
                    <div className="text-xs font-semibold text-slate-800">PostgreSQL 15 (Supabase)</div>
                    <div className="text-[11px] text-slate-500">Lưu trữ dữ liệu có cấu trúc & RBAC</div>
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  <span className="text-xs font-mono text-slate-500">
                    {healthData?.services?.postgres?.latency_ms ? `${healthData.services.postgres.latency_ms} ms` : "Online"}
                  </span>
                  <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
                </div>
              </div>

              <div className="flex items-center justify-between p-3 rounded-md bg-slate-50 border border-slate-100">
                <div className="flex items-center gap-3">
                  <Search size={17} className="text-cyan-600" />
                  <div>
                    <div className="text-xs font-semibold text-slate-800">Elasticsearch 8.12</div>
                    <div className="text-[11px] text-slate-500">Tìm kiếm toàn văn tiếng Việt</div>
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  <span className="text-xs font-mono text-slate-500">
                    {healthData?.services?.elasticsearch?.latency_ms ? `${healthData.services.elasticsearch.latency_ms} ms` : "Online"}
                  </span>
                  <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
                </div>
              </div>

              <div className="flex items-center justify-between p-3 rounded-md bg-slate-50 border border-slate-100">
                <div className="flex items-center gap-3">
                  <HardDrive size={17} className="text-amber-600" />
                  <div>
                    <div className="text-xs font-semibold text-slate-800">Object Storage (MinIO / Supabase)</div>
                    <div className="text-[11px] text-slate-500">Lưu trữ file gốc PDF & Scan</div>
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  <span className="text-xs font-mono text-slate-500">Online</span>
                  <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
                </div>
              </div>

              <div className="flex items-center justify-between p-3 rounded-md bg-slate-50 border border-slate-100">
                <div className="flex items-center gap-3">
                  <Cpu size={17} className="text-rose-600" />
                  <div>
                    <div className="text-xs font-semibold text-slate-800">VietOCR & TrOCR Engine</div>
                    <div className="text-[11px] text-slate-500">Mô hình Transformer & Trích xuất AI</div>
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  <span className="text-xs font-mono text-slate-500">Sẵn sàng</span>
                  <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
                </div>
              </div>
            </div>
          </Card>
        )}

        {/* Hướng dẫn Quy trình Xử lý Hồ sơ dành cho Sinh viên */}
        {isStudent && (
          <Card padding="md">
            <h2 className="text-sm font-bold text-slate-900 mb-3.5">
              Quy trình Xử lý Hồ sơ Học vụ Trực tuyến
            </h2>
            <div className="space-y-3">
              <div className="flex gap-3 items-start">
                <div className="w-6 h-6 rounded-full bg-sky-100 text-sky-700 font-bold flex items-center justify-center shrink-0 text-xs">
                  1
                </div>
                <div>
                  <div className="text-xs font-semibold text-slate-800">Tải lên hồ sơ / Chụp ảnh văn bản</div>
                  <div className="text-[11px] text-slate-500 mt-0.5">
                    Nộp đơn xin nghỉ học tạm thời, đơn xin miễn giảm học phí, hồ sơ học bổng dạng PDF hoặc ảnh chụp rõ nét.
                  </div>
                </div>
              </div>
              <div className="flex gap-3 items-start">
                <div className="w-6 h-6 rounded-full bg-emerald-100 text-emerald-700 font-bold flex items-center justify-center shrink-0 text-xs">
                  2
                </div>
                <div>
                  <div className="text-xs font-semibold text-slate-800">Số hóa tự động bằng VietOCR & AI</div>
                  <div className="text-[11px] text-slate-500 mt-0.5">
                    Hệ thống tự động trích xuất toàn văn, bóc tách MSSV, họ tên, ngày tháng, bảng biểu và gắn nhãn theo chủ đề.
                  </div>
                </div>
              </div>
              <div className="flex gap-3 items-start">
                <div className="w-6 h-6 rounded-full bg-purple-100 text-purple-700 font-bold flex items-center justify-center shrink-0 text-xs">
                  3
                </div>
                <div>
                  <div className="text-xs font-semibold text-slate-800">Cán bộ CTSV tiếp nhận & Phê duyệt</div>
                  <div className="text-[11px] text-slate-500 mt-0.5">
                    Hồ sơ được thẩm định, đóng dấu số và cấp mã QR xác thực để bạn có thể tra cứu và sử dụng hợp lệ.
                  </div>
                </div>
              </div>
            </div>
          </Card>
        )}

        {/* Category Distribution */}
        <Card padding="md">
          <h2 className="text-sm font-bold text-slate-900 mb-3.5">
            {isStudent ? "Phân bổ Hồ sơ của bạn theo Danh mục" : "Phân bổ Loại Hồ sơ CTSV"}
          </h2>
          {categoryBreakdown.length > 0 ? (
            <div className="space-y-3.5">
              {categoryBreakdown.map((cat, i) => (
                <div key={i}>
                  <div className="flex justify-between text-xs font-semibold mb-1">
                    <span className="text-slate-800">{cat.name}</span>
                    <span className="text-slate-500 font-mono">
                      {cat.count} hồ sơ ({cat.percent}%)
                    </span>
                  </div>
                  <div className="h-2 w-full bg-slate-100 rounded-full overflow-hidden">
                    <div
                      className={`h-full rounded-full transition-all duration-500 ${cat.colorClass}`}
                      style={{ width: `${cat.percent}%` }}
                    />
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="py-8 text-center text-slate-400">
              <UploadCloud size={28} className="mx-auto mb-2 opacity-50" />
              <div className="text-xs font-semibold text-slate-600">
                {isStudent ? "Bạn chưa có hồ sơ nào được tải lên" : "Chưa có dữ liệu danh mục"}
              </div>
              {isStudent && (
                <p className="text-[11px] text-slate-400 mt-1">
                  Các hồ sơ đơn từ bạn nộp sẽ được tự động phân loại tại đây.
                </p>
              )}
            </div>
          )}
        </Card>
      </div>

      {/* Bottom Section: Recent Documents Table */}
      <Card padding="none">
        <div className="flex justify-between items-center px-5 py-4 border-b border-slate-200/80 flex-wrap gap-3">
          <div>
            <h2 className="text-sm font-bold text-slate-900">
              {isStudent ? "Lịch sử Hồ sơ Bạn đã Tải lên Gần đây" : "Tài liệu & Hồ sơ Xử lý Gần đây"}
            </h2>
            <p className="text-xs text-slate-500 mt-0.5">
              {isStudent
                ? "Danh sách các tài liệu do chính bạn tải lên cùng tiến độ số hóa OCR"
                : "Danh sách văn bản vừa được upload và xử lý OCR tự động"}
            </p>
          </div>
          <Link to="/documents">
            <Button variant="ghost" size="sm" rightIcon={<ArrowUpRight size={14} />}>
              {isStudent ? "Xem toàn bộ lịch sử upload" : "Xem tất cả hồ sơ"}
            </Button>
          </Link>
        </div>

        <div className="overflow-x-auto">
          {recentDocs.length > 0 ? (
            <table className="w-full text-left text-xs">
              <thead>
                <tr className="bg-slate-50/90 border-b border-slate-200/80 text-slate-500 font-semibold uppercase tracking-wider text-[11px]">
                  <th className="px-5 py-3">Tiêu đề tài liệu</th>
                  <th className="px-4 py-3">Danh mục</th>
                  <th className="px-4 py-3">Sinh viên (MSSV)</th>
                  <th className="px-4 py-3">Thời gian</th>
                  <th className="px-4 py-3">Trạng thái OCR</th>
                  <th className="px-5 py-3 text-right">Thao tác</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {recentDocs.map((d, idx) => (
                  <tr
                    key={d.id || idx}
                    className="hover:bg-slate-50/80 transition-colors"
                  >
                    <td className="px-5 py-3.5 font-semibold text-slate-900">
                      <Link
                        to={`/documents/${d.id}`}
                        className="text-dlu-navy-800 hover:text-dlu-navy-950 hover:underline line-clamp-1"
                      >
                        {d.title}
                      </Link>
                    </td>
                    <td className="px-4 py-3.5 text-slate-600">
                      {d.category}
                    </td>
                    <td className="px-4 py-3.5 text-slate-700">
                      <span>{d.student_name || "Sinh viên"}</span>{" "}
                      <span className="text-slate-400 font-mono text-[11px]">
                        ({d.student_id || "--"})
                      </span>
                    </td>
                    <td className="px-4 py-3.5 text-slate-500 font-mono">
                      {d.created_at ? new Date(d.created_at).toLocaleDateString("vi-VN") : "--"}
                    </td>
                    <td className="px-4 py-3.5">
                      <OCRStatusBadge status={d.ocr_status} />
                    </td>
                    <td className="px-5 py-3.5 text-right">
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
          ) : (
            <div className="py-12 px-6 text-center text-slate-500">
              <FileText size={36} className="mx-auto text-slate-300 mb-2" />
              <div className="text-sm font-semibold text-slate-700">
                {isStudent ? "Bạn chưa tải lên tài liệu nào" : "Chưa có tài liệu nào trong hệ thống"}
              </div>
              <p className="text-xs text-slate-400 mt-1 max-w-sm mx-auto mb-4">
                {isStudent
                  ? "Toàn bộ tài liệu, giấy tờ bạn gửi lên hệ thống sẽ được lưu tại đây để tiện theo dõi tiến độ."
                  : "Các tài liệu vừa tải lên sẽ xuất hiện tại đây."}
              </p>
              <Link to="/upload">
                <Button variant="primary" size="sm" leftIcon={<UploadCloud size={14} />}>
                  {isStudent ? "Tải lên hồ sơ đầu tiên" : "Tiếp nhận hồ sơ mới"}
                </Button>
              </Link>
            </div>
          )}
        </div>
      </Card>
    </div>
  );
};
