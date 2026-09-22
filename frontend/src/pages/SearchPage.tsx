import React, { useState, useEffect } from "react";
import { Link, useSearchParams } from "react-router-dom";
import {
  Search,
  SlidersHorizontal,
  FileText,
  Calendar,
  User,
  GraduationCap,
  Sparkles,
  ArrowRight,
  Info,
  Clock,
  ChevronLeft,
  ChevronRight,
  RotateCcw,
} from "lucide-react";
import { Card } from "../components/common/Card";
import { Button } from "../components/common/Button";
import { OCRStatusBadge } from "../components/common/Badge";
import { searchApi, SearchResponse, SearchHit } from "../api/search";
import { useToastStore } from "../stores/useToastStore";

export const SearchPage: React.FC = () => {
  const { addToast } = useToastStore();
  const [searchParams, setSearchParams] = useSearchParams();

  const initialQuery = searchParams.get("q") || "";
  const initialPage = parseInt(searchParams.get("page") || "1", 10);

  const [query, setQuery] = useState(initialQuery);
  const [categoryCode, setCategoryCode] = useState(searchParams.get("category") || "");
  const [ocrStatus, setOcrStatus] = useState(searchParams.get("status") || "");
  const [dateFrom, setDateFrom] = useState(searchParams.get("date_from") || "");
  const [dateTo, setDateTo] = useState(searchParams.get("date_to") || "");
  const [fuzzy, setFuzzy] = useState(true);
  const [showFilters, setShowFilters] = useState(false);

  const [searchResponse, setSearchResponse] = useState<SearchResponse | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [hasSearched, setHasSearched] = useState(false);
  const [currentPage, setCurrentPage] = useState(initialPage);

  const performSearch = async (searchQuery: string, pageNumber = 1) => {
    const trimmed = searchQuery.trim();
    if (!trimmed) return;

    setIsLoading(true);
    setHasSearched(true);
    setCurrentPage(pageNumber);

    try {
      const res = await searchApi.search({
        q: trimmed,
        category_code: categoryCode || undefined,
        ocr_status: ocrStatus || undefined,
        date_from: dateFrom || undefined,
        date_to: dateTo || undefined,
        fuzzy: fuzzy,
        page: pageNumber,
        page_size: 10,
      });
      setSearchResponse(res);

      // Đồng bộ URL params
      const newParams: Record<string, string> = { q: trimmed, page: String(pageNumber) };
      if (categoryCode) newParams.category = categoryCode;
      if (ocrStatus) newParams.status = ocrStatus;
      if (dateFrom) newParams.date_from = dateFrom;
      if (dateTo) newParams.date_to = dateTo;
      setSearchParams(newParams, { replace: true });
    } catch (err: any) {
      addToast({
        type: "error",
        title: "Lỗi tìm kiếm",
        message: err.message || "Không thể thực hiện tra cứu",
      });
    } finally {
      setIsLoading(false);
    }
  };

  // Tự động tìm kiếm nếu URL có tham số q
  useEffect(() => {
    const qParam = searchParams.get("q");
    if (qParam && qParam !== query) {
      setQuery(qParam);
      performSearch(qParam, initialPage);
    } else if (qParam && !hasSearched) {
      performSearch(qParam, initialPage);
    }
  }, [searchParams]);

  const handleFormSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    performSearch(query, 1);
  };

  const handleResetFilters = () => {
    setCategoryCode("");
    setOcrStatus("");
    setDateFrom("");
    setDateTo("");
    setFuzzy(true);
    if (query.trim()) {
      performSearch(query, 1);
    }
  };

  const sampleQueries = [
    "miễn giảm học phí",
    "bảo lưu kết quả học tập",
    "xét học bổng kỳ 1",
    "20210678",
    "don xin nghi hoc",
    "Nguyễn Hoàng Nam",
  ];

  return (
    <div className="animate-fade-in" style={{ display: "flex", flexDirection: "column", gap: "1.5rem" }}>
      {/* Header */}
      <div>
        <h1 style={{ fontSize: "1.5rem", fontWeight: 800, color: "var(--gray-900)" }}>
          Tra cứu Toàn văn Tài liệu CTSV
        </h1>
        <p style={{ fontSize: "0.875rem", color: "var(--gray-500)", marginTop: "0.25rem" }}>
          Tìm kiếm thông minh trên Elasticsearch 8 & Cơ sở dữ liệu CTSV (hỗ trợ tìm có dấu, không dấu, MSSV, tên SV và bù đắp sai số OCR).
        </p>
      </div>

      {/* Main Search Bar Card */}
      <Card padding="md">
        <form onSubmit={handleFormSubmit}>
          <div style={{ display: "flex", gap: "0.75rem", alignItems: "center" }}>
            <div
              style={{
                flex: 1,
                display: "flex",
                alignItems: "center",
                gap: "0.75rem",
                padding: "0.5rem 1rem",
                borderRadius: "var(--radius-md)",
                border: "2px solid var(--primary-400)",
                backgroundColor: "#ffffff",
                boxShadow: "0 2px 4px rgba(99, 102, 241, 0.08)",
              }}
            >
              <Search size={20} color="var(--primary-600)" />
              <input
                type="text"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                placeholder="Nhập từ khóa, tiêu đề, họ tên SV hoặc MSSV (vd: 'học phí', '20210678', 'bảo lưu')..."
                style={{
                  width: "100%",
                  border: "none",
                  outline: "none",
                  fontSize: "0.9375rem",
                  fontWeight: 500,
                  color: "var(--gray-900)",
                }}
              />
            </div>

            <Button
              type="button"
              variant="outline"
              onClick={() => setShowFilters(!showFilters)}
              leftIcon={<SlidersHorizontal size={16} />}
              style={{ borderColor: showFilters ? "var(--primary-500)" : undefined }}
            >
              Bộ lọc {showFilters ? "▲" : "▼"}
            </Button>

            <Button
              type="submit"
              variant="primary"
              isLoading={isLoading}
              style={{ padding: "0.65rem 1.5rem" }}
            >
              Tìm kiếm
            </Button>
          </div>
        </form>

        {/* Quick Sample Queries */}
        <div style={{ display: "flex", alignItems: "center", gap: "0.5rem", marginTop: "1rem", flexWrap: "wrap" }}>
          <span style={{ fontSize: "0.75rem", color: "var(--gray-500)", fontWeight: 600 }}>Gợi ý nhanh:</span>
          {sampleQueries.map((item, idx) => (
            <button
              key={idx}
              type="button"
              onClick={() => {
                setQuery(item);
                performSearch(item, 1);
              }}
              style={{
                padding: "0.2rem 0.6rem",
                borderRadius: "9999px",
                backgroundColor: "var(--gray-100)",
                fontSize: "0.75rem",
                color: "var(--primary-700)",
                fontWeight: 500,
                border: "1px solid var(--border-color)",
                cursor: "pointer",
              }}
            >
              {item}
            </button>
          ))}
        </div>

        {/* Advanced Filters Panel */}
        {showFilters && (
          <div
            className="animate-fade-in"
            style={{
              marginTop: "1.25rem",
              paddingTop: "1.25rem",
              borderTop: "1px solid var(--border-color)",
              display: "grid",
              gridTemplateColumns: "repeat(auto-fit, minmax(200px, 1fr))",
              gap: "1rem",
            }}
          >
            <div>
              <label style={{ display: "block", fontSize: "0.75rem", fontWeight: 600, color: "var(--gray-600)", marginBottom: "0.3rem" }}>
                Loại danh mục
              </label>
              <select
                value={categoryCode}
                onChange={(e) => setCategoryCode(e.target.value)}
                style={{ width: "100%", padding: "0.45rem", borderRadius: "var(--radius-sm)", border: "1px solid var(--border-color)", fontSize: "0.8125rem" }}
              >
                <option value="">-- Tất cả danh mục --</option>
                <option value="DON_NGHI_HOC">Đơn nghỉ học / bảo lưu</option>
                <option value="GIAY_XAC_NHAN">Giấy xác nhận sinh viên</option>
                <option value="HOC_BONG">Hồ sơ xét học bổng</option>
                <option value="KHEN_THUONG">Khen thưởng - Kỷ luật</option>
                <option value="MIEN_GIAM_HOC_PHI">Miễn giảm học phí</option>
              </select>
            </div>

            <div>
              <label style={{ display: "block", fontSize: "0.75rem", fontWeight: 600, color: "var(--gray-600)", marginBottom: "0.3rem" }}>
                Trạng thái duyệt / OCR
              </label>
              <select
                value={ocrStatus}
                onChange={(e) => setOcrStatus(e.target.value)}
                style={{ width: "100%", padding: "0.45rem", borderRadius: "var(--radius-sm)", border: "1px solid var(--border-color)", fontSize: "0.8125rem" }}
              >
                <option value="">-- Tất cả trạng thái --</option>
                <option value="APPROVED">Đã phê duyệt (APPROVED)</option>
                <option value="DONE">OCR Hoàn thành (DONE)</option>
                <option value="PROCESSING">Đang xử lý (PROCESSING)</option>
                <option value="PENDING">Chờ xử lý (PENDING)</option>
              </select>
            </div>

            <div>
              <label style={{ display: "block", fontSize: "0.75rem", fontWeight: 600, color: "var(--gray-600)", marginBottom: "0.3rem" }}>
                Ngày upload từ
              </label>
              <input
                type="date"
                value={dateFrom}
                onChange={(e) => setDateFrom(e.target.value)}
                style={{ width: "100%", padding: "0.45rem", borderRadius: "var(--radius-sm)", border: "1px solid var(--border-color)", fontSize: "0.8125rem" }}
              />
            </div>

            <div>
              <label style={{ display: "block", fontSize: "0.75rem", fontWeight: 600, color: "var(--gray-600)", marginBottom: "0.3rem" }}>
                Ngày upload đến
              </label>
              <input
                type="date"
                value={dateTo}
                onChange={(e) => setDateTo(e.target.value)}
                style={{ width: "100%", padding: "0.45rem", borderRadius: "var(--radius-sm)", border: "1px solid var(--border-color)", fontSize: "0.8125rem" }}
              />
            </div>

            <div style={{ display: "flex", alignItems: "center", gap: "1rem", gridColumn: "1 / -1", marginTop: "0.5rem" }}>
              <div style={{ display: "flex", alignItems: "center", gap: "0.5rem" }}>
                <input
                  type="checkbox"
                  id="fuzzyToggle"
                  checked={fuzzy}
                  onChange={(e) => setFuzzy(e.target.checked)}
                  style={{ width: "16px", height: "16px", accentColor: "var(--primary-600)" }}
                />
                <label htmlFor="fuzzyToggle" style={{ fontSize: "0.8125rem", fontWeight: 600, color: "var(--gray-700)", cursor: "pointer" }}>
                  Tìm kiếm mờ (Fuzzy / Bù sai sót dấu tiếng Việt)
                </label>
              </div>

              <Button
                type="button"
                variant="outline"
                size="sm"
                leftIcon={<RotateCcw size={13} />}
                onClick={handleResetFilters}
                style={{ marginLeft: "auto" }}
              >
                Đặt lại bộ lọc
              </Button>
            </div>
          </div>
        )}
      </Card>

      {/* Search Results Area */}
      {hasSearched && searchResponse && (
        <div style={{ display: "flex", flexDirection: "column", gap: "1rem" }}>
          {/* Results Summary Bar */}
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", fontSize: "0.875rem", color: "var(--gray-600)" }}>
            <div>
              Tìm thấy <strong style={{ color: "var(--gray-900)" }}>{searchResponse.total_hits}</strong> kết quả cho từ khóa "<strong>{searchResponse.query}</strong>" ({searchResponse.took_ms} ms)
            </div>
            {searchResponse.total_pages > 1 && (
              <span style={{ fontSize: "0.8125rem", color: "var(--gray-500)" }}>
                Trang {searchResponse.page} / {searchResponse.total_pages}
              </span>
            )}
          </div>

          {searchResponse.results.length === 0 ? (
            /* Empty state */
            <Card padding="lg" style={{ textAlign: "center" }}>
              <div style={{ width: "48px", height: "48px", borderRadius: "50%", backgroundColor: "var(--gray-100)", display: "inline-flex", alignItems: "center", justifyContent: "center", marginBottom: "0.75rem" }}>
                <Info size={24} color="var(--gray-400)" />
              </div>
              <h3 style={{ fontSize: "1.1rem", fontWeight: 700, color: "var(--gray-800)" }}>
                Không tìm thấy tài liệu phù hợp
              </h3>
              <p style={{ fontSize: "0.8125rem", color: "var(--gray-500)", marginTop: "0.25rem", maxWidth: "450px", margin: "0.25rem auto" }}>
                Hãy thử kiểm tra lại chính tả, tìm từ khóa không dấu (vd: "hoc bong", "mien giam"), tìm theo MSSV, hoặc bỏ bớt các bộ lọc.
              </p>
            </Card>
          ) : (
            /* Results List */
            <>
              {searchResponse.results.map((hit: SearchHit) => (
                <Card key={hit.document_id} padding="md" hoverable>
                  <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", gap: "1rem" }}>
                    <div style={{ flex: 1 }}>
                      <div style={{ display: "flex", alignItems: "center", gap: "0.5rem", marginBottom: "0.35rem" }}>
                        <OCRStatusBadge status={hit.ocr_status} />
                        {hit.category_name && (
                          <span style={{ fontSize: "0.75rem", color: "var(--primary-700)", backgroundColor: "var(--primary-50)", padding: "0.15rem 0.5rem", borderRadius: "4px", fontWeight: 600 }}>
                            {hit.category_name}
                          </span>
                        )}
                        <span style={{ fontSize: "0.75rem", color: "var(--gray-400)", marginLeft: "auto" }}>
                          Độ phù hợp: {hit.score}
                        </span>
                      </div>

                      <h3 style={{ fontSize: "1.05rem", fontWeight: 700, color: "var(--gray-900)" }}>
                        <Link to={`/documents/${hit.document_id}`} style={{ color: "var(--primary-700)" }}>
                          {/* Title highlight if available */}
                          {hit.highlights?.title ? (
                            <span dangerouslySetInnerHTML={{ __html: hit.highlights.title[0] }} />
                          ) : (
                            hit.title
                          )}
                        </Link>
                      </h3>

                      {/* Metadata chips */}
                      <div style={{ display: "flex", gap: "1rem", marginTop: "0.35rem", fontSize: "0.75rem", color: "var(--gray-600)", flexWrap: "wrap" }}>
                        {hit.student_name && (
                          <span style={{ display: "flex", alignItems: "center", gap: "0.25rem" }}>
                            <User size={13} /> {hit.student_name}
                          </span>
                        )}
                        {hit.student_id && (
                          <span style={{ display: "flex", alignItems: "center", gap: "0.25rem" }}>
                            <GraduationCap size={13} /> MSSV: <strong>{hit.student_id}</strong>
                          </span>
                        )}
                        {hit.created_at && (
                          <span style={{ display: "flex", alignItems: "center", gap: "0.25rem" }}>
                            <Calendar size={13} /> {new Date(hit.created_at).toLocaleDateString("vi-VN")}
                          </span>
                        )}
                      </div>

                      {/* Snippet Highlight */}
                      {hit.content_snippet && (
                        <div
                          style={{
                            marginTop: "0.75rem",
                            padding: "0.6rem 0.85rem",
                            borderRadius: "var(--radius-sm)",
                            backgroundColor: "var(--gray-50)",
                            borderLeft: "3px solid var(--primary-500)",
                            fontSize: "0.8125rem",
                            color: "var(--gray-700)",
                            lineHeight: 1.5,
                          }}
                          dangerouslySetInnerHTML={{ __html: hit.content_snippet }}
                        />
                      )}
                    </div>

                    <Link to={`/documents/${hit.document_id}`} style={{ flexShrink: 0, marginTop: "0.5rem" }}>
                      <Button variant="outline" size="sm" rightIcon={<ArrowRight size={14} />}>
                        Xem chi tiết
                      </Button>
                    </Link>
                  </div>
                </Card>
              ))}

              {/* Pagination Controls */}
              {searchResponse.total_pages > 1 && (
                <div style={{ display: "flex", justifyContent: "center", alignItems: "center", gap: "0.5rem", marginTop: "1rem" }}>
                  <Button
                    variant="outline"
                    size="sm"
                    disabled={currentPage <= 1}
                    onClick={() => performSearch(query, currentPage - 1)}
                    leftIcon={<ChevronLeft size={14} />}
                  >
                    Trang trước
                  </Button>

                  {Array.from({ length: searchResponse.total_pages }, (_, i) => i + 1)
                    .filter((p) => p === 1 || p === searchResponse.total_pages || Math.abs(p - currentPage) <= 2)
                    .map((pageNum, idx, arr) => (
                      <React.Fragment key={pageNum}>
                        {idx > 0 && arr[idx - 1] !== pageNum - 1 && (
                          <span style={{ padding: "0 0.25rem", color: "var(--gray-400)" }}>...</span>
                        )}
                        <Button
                          variant={currentPage === pageNum ? "primary" : "outline"}
                          size="sm"
                          onClick={() => performSearch(query, pageNum)}
                          style={{ minWidth: "36px", padding: "0.4rem 0.6rem" }}
                        >
                          {pageNum}
                        </Button>
                      </React.Fragment>
                    ))}

                  <Button
                    variant="outline"
                    size="sm"
                    disabled={currentPage >= searchResponse.total_pages}
                    onClick={() => performSearch(query, currentPage + 1)}
                    rightIcon={<ChevronRight size={14} />}
                  >
                    Trang sau
                  </Button>
                </div>
              )}
            </>
          )}
        </div>
      )}
    </div>
  );
};

