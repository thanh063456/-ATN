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

function formatDisplayTitle(rawTitle: string): { mainTitle: string; code?: string } {
  if (!rawTitle) return { mainTitle: "Tài liệu không tên" };
  let clean = rawTitle.replace(/^[0-9]+_/, "");
  let codeMatch = clean.match(/^([0-9A-Za-z]+-[A-Za-zĐđ]+-[A-Za-zĐđ]+)/);
  let code = codeMatch ? codeMatch[1].replace(/-/g, "/") : undefined;
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

export const SearchPage: React.FC = () => {

  const { addToast } = useToastStore();
  const [searchParams, setSearchParams] = useSearchParams();

  const initialQuery = searchParams.get("q") || "";
  const initialPage = parseInt(searchParams.get("page") || "1", 10);

  const [query, setQuery] = useState(initialQuery);
  const [categoryCode, setCategoryCode] = useState(searchParams.get("category") || "");
  const [docTypeCode, setDocTypeCode] = useState(searchParams.get("doc_type") || "");
  const [tag, setTag] = useState(searchParams.get("tag") || "");
  const [ocrScope, setOcrScope] = useState(searchParams.get("ocr_scope") || "");
  const [ocrStatus, setOcrStatus] = useState(searchParams.get("status") || "");
  const [dateFrom, setDateFrom] = useState(searchParams.get("date_from") || "");
  const [dateTo, setDateTo] = useState(searchParams.get("date_to") || "");
  const [fuzzy, setFuzzy] = useState(true);
  const [showFilters, setShowFilters] = useState(false);

  const [searchResponse, setSearchResponse] = useState<SearchResponse | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [hasSearched, setHasSearched] = useState(false);
  const [currentPage, setCurrentPage] = useState(initialPage);

  const performSearch = async (
    searchQuery: string,
    pageNumber = 1,
    overrides?: {
      categoryCode?: string;
      docTypeCode?: string;
      tag?: string;
      ocrScope?: string;
      ocrStatus?: string;
      dateFrom?: string;
      dateTo?: string;
      fuzzy?: boolean;
    }
  ) => {
    const trimmed = searchQuery.trim();
    if (!trimmed) return;

    setIsLoading(true);
    setHasSearched(true);
    setCurrentPage(pageNumber);

    const activeCategoryCode = overrides?.categoryCode !== undefined ? overrides.categoryCode : categoryCode;
    const activeDocTypeCode = overrides?.docTypeCode !== undefined ? overrides.docTypeCode : docTypeCode;
    const activeTag = overrides?.tag !== undefined ? overrides.tag : tag;
    const activeOcrScope = overrides?.ocrScope !== undefined ? overrides.ocrScope : ocrScope;
    const activeOcrStatus = overrides?.ocrStatus !== undefined ? overrides.ocrStatus : ocrStatus;
    const activeDateFrom = overrides?.dateFrom !== undefined ? overrides.dateFrom : dateFrom;
    const activeDateTo = overrides?.dateTo !== undefined ? overrides.dateTo : dateTo;
    const activeFuzzy = overrides?.fuzzy !== undefined ? overrides.fuzzy : fuzzy;

    try {
      const res = await searchApi.search({
        q: trimmed,
        category_code: activeCategoryCode || undefined,
        doc_type_code: activeDocTypeCode || undefined,
        tag: activeTag || undefined,
        ocr_scope: activeOcrScope || undefined,
        ocr_status: activeOcrStatus || undefined,
        date_from: activeDateFrom || undefined,
        date_to: activeDateTo || undefined,
        fuzzy: activeFuzzy,
        page: pageNumber,
        page_size: 10,
      });
      setSearchResponse(res);

      // Đồng bộ URL params
      const newParams: Record<string, string> = { q: trimmed, page: String(pageNumber) };
      if (activeCategoryCode) newParams.category = activeCategoryCode;
      if (activeDocTypeCode) newParams.doc_type = activeDocTypeCode;
      if (activeTag) newParams.tag = activeTag;
      if (activeOcrScope) newParams.ocr_scope = activeOcrScope;
      if (activeOcrStatus) newParams.status = activeOcrStatus;
      if (activeDateFrom) newParams.date_from = activeDateFrom;
      if (activeDateTo) newParams.date_to = activeDateTo;
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
    setDocTypeCode("");
    setTag("");
    setOcrScope("");
    setOcrStatus("");
    setDateFrom("");
    setDateTo("");
    setFuzzy(true);
    if (query.trim()) {
      performSearch(query, 1, {
        categoryCode: "",
        docTypeCode: "",
        tag: "",
        ocrScope: "",
        ocrStatus: "",
        dateFrom: "",
        dateTo: "",
        fuzzy: true,
      });
    }
  };

  const activeFilterCount = [categoryCode, docTypeCode, tag, ocrScope, ocrStatus, dateFrom, dateTo].filter(Boolean).length;

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
              style={{
                borderColor: showFilters || activeFilterCount > 0 ? "var(--primary-500)" : undefined,
                color: activeFilterCount > 0 ? "var(--primary-700)" : undefined,
                backgroundColor: activeFilterCount > 0 ? "var(--primary-50)" : undefined,
              }}
            >
              Bộ lọc {activeFilterCount > 0 ? `(${activeFilterCount})` : ""} {showFilters ? "▲" : "▼"}
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
                Hình thức văn bản
              </label>
              <select
                value={docTypeCode || categoryCode}
                onChange={(e) => {
                  const val = e.target.value;
                  setDocTypeCode(val);
                  setCategoryCode(val);
                }}
                style={{ width: "100%", padding: "0.45rem", borderRadius: "var(--radius-sm)", border: "1px solid var(--border-color)", fontSize: "0.8125rem" }}
              >
                <option value="">-- Tất cả hình thức --</option>
                <option value="KE_HOACH">Kế hoạch (KE_HOACH)</option>
                <option value="THONG_BAO">Thông báo (THONG_BAO)</option>
                <option value="QUYET_DINH">Quyết định (QUYET_DINH)</option>
                <option value="DON_TU">Đơn từ (DON_TU)</option>
                <option value="HUONG_DAN">Hướng dẫn (HUONG_DAN)</option>
                <option value="BAO_CAO">Báo cáo (BAO_CAO)</option>
                <option value="CONG_VAN">Công văn (CONG_VAN)</option>
                <option value="BIEN_BAN">Biên bản (BIEN_BAN)</option>
                <option value="DANH_SACH">Danh sách (DANH_SACH)</option>
                <option value="DIEU_LE_QUY_CHE">Điều lệ / Quy chế (DIEU_LE_QUY_CHE)</option>
                <option value="KHAC">Khác (KHAC)</option>
              </select>
            </div>

            <div>
              <label style={{ display: "block", fontSize: "0.75rem", fontWeight: 600, color: "var(--gray-600)", marginBottom: "0.3rem" }}>
                Nhãn chủ đề AI (Tags)
              </label>
              <select
                value={tag}
                onChange={(e) => setTag(e.target.value)}
                style={{ width: "100%", padding: "0.45rem", borderRadius: "var(--radius-sm)", border: "1px solid var(--border-color)", fontSize: "0.8125rem" }}
              >
                <option value="">-- Tất cả chủ đề --</option>
                <option value="#DonTu">#Đơn từ / Thôi học / Bảo lưu</option>
                <option value="#MienGiamHocPhi">#Miễn giảm học phí</option>
                <option value="#HocPhi">#Học phí & Trợ cấp</option>
                <option value="#HocBong">#Học bổng sinh viên</option>
                <option value="#XuLyHocVu">#Xử lý học vụ</option>
                <option value="#XinThoiHoc">#Buộc thôi học / Nghỉ học</option>
                <option value="#KhenThuong">#Khen thưởng</option>
                <option value="#KyLuat">#Kỷ luật</option>
                <option value="#KhoiNghiep">#Khởi nghiệp đổi mới sáng tạo</option>
                <option value="#CuocThi">#Cuộc thi / Phong trào</option>
                <option value="#SinhHoatCongDan">#Sinh hoạt công dân</option>
                <option value="#NganhCNTT">#Ngành CNTT</option>
                <option value="#K46">#Khóa 46 (K46)</option>
                <option value="#K47">#Khóa 47 (K47)</option>
                <option value="#K48">#Khóa 48 (K48)</option>
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

            <div>
              <label style={{ display: "block", fontSize: "0.75rem", fontWeight: 600, color: "var(--gray-600)", marginBottom: "0.3rem" }}>
                Phạm vi quét OCR
              </label>
              <select
                value={ocrScope}
                onChange={(e) => setOcrScope(e.target.value)}
                style={{ width: "100%", padding: "0.45rem", borderRadius: "var(--radius-sm)", border: "1px solid var(--border-color)", fontSize: "0.8125rem" }}
              >
                <option value="">-- Tất cả phạm vi --</option>
                <option value="first_page">Mới OCR trang 1</option>
                <option value="full">Đã OCR toàn bộ</option>
              </select>
            </div>

            <div style={{ display: "flex", alignItems: "center", gap: "1rem", gridColumn: "1 / -1", marginTop: "0.5rem", flexWrap: "wrap" }}>
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

              <div style={{ display: "flex", gap: "0.5rem", marginLeft: "auto" }}>
                <Button
                  type="button"
                  variant="outline"
                  size="sm"
                  leftIcon={<RotateCcw size={13} />}
                  onClick={handleResetFilters}
                >
                  Đặt lại bộ lọc
                </Button>
                <Button
                  type="button"
                  variant="primary"
                  size="sm"
                  onClick={() => performSearch(query, 1)}
                >
                  Áp dụng bộ lọc
                </Button>
              </div>
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

          {/* Facets Chips */}
          {(() => {
            const rawFacets = searchResponse.facets?.doc_type_code || searchResponse.facets?.categories;
            if (!rawFacets) return null;

            const facetList: { code: string; count: number }[] = Array.isArray(rawFacets)
              ? rawFacets.map((item: any) => ({
                  code: typeof item === "object" ? (item.code || item.key || String(item)) : String(item),
                  count: typeof item === "object" ? (item.count ?? item.doc_count ?? 0) : 0,
                }))
              : Object.entries(rawFacets).map(([code, count]) => ({
                  code,
                  count: typeof count === "number" ? count : Number((count as any)?.count || 0),
                }));

            if (facetList.length === 0) return null;

            return (
              <div style={{ display: "flex", gap: "0.5rem", alignItems: "center", flexWrap: "wrap", padding: "0.25rem 0" }}>
                <span style={{ fontSize: "0.75rem", fontWeight: 600, color: "var(--gray-600)" }}>Lọc theo loại:</span>
                <button
                  type="button"
                  onClick={() => {
                    setDocTypeCode("");
                    setCategoryCode("");
                    performSearch(query, 1, { docTypeCode: "", categoryCode: "" });
                  }}
                  style={{
                    padding: "0.2rem 0.6rem",
                    borderRadius: "9999px",
                    fontSize: "0.75rem",
                    fontWeight: 600,
                    backgroundColor: (!docTypeCode && !categoryCode) ? "var(--primary-600)" : "var(--gray-100)",
                    color: (!docTypeCode && !categoryCode) ? "white" : "var(--gray-700)",
                    border: "1px solid var(--border-color)",
                    cursor: "pointer",
                  }}
                >
                  Tất cả ({searchResponse.total_hits})
                </button>
                {facetList.map(({ code, count }) => {
                  const isSelected = (docTypeCode === code || categoryCode === code);
                  return (
                    <button
                      key={code}
                      type="button"
                      onClick={() => {
                        const nextVal = isSelected ? "" : code;
                        setDocTypeCode(nextVal);
                        setCategoryCode(nextVal);
                        performSearch(query, 1, { docTypeCode: nextVal, categoryCode: nextVal });
                      }}
                      style={{
                        padding: "0.2rem 0.6rem",
                        borderRadius: "9999px",
                        fontSize: "0.75rem",
                        fontWeight: 600,
                        backgroundColor: isSelected ? "var(--primary-600)" : "var(--gray-100)",
                        color: isSelected ? "white" : "var(--gray-700)",
                        border: "1px solid var(--border-color)",
                        cursor: "pointer",
                      }}
                    >
                      {code} ({count})
                    </button>
                  );
                })}
              </div>
            );
          })()}

          {/* AI Tags Chips */}
          {(() => {
            const rawTags = searchResponse.facets?.tags;
            if (!rawTags || !Array.isArray(rawTags) || rawTags.length === 0) return null;
            const tagList = rawTags
              .map((item: any) => ({
                tag: typeof item === "object" ? (item.tag || item.key || String(item)) : String(item),
                count: typeof item === "object" ? (item.count ?? item.doc_count ?? 0) : 0,
              }))
              .filter((t) => t.tag && t.tag.trim());

            if (tagList.length === 0) return null;

            return (
              <div style={{ display: "flex", gap: "0.4rem", alignItems: "center", flexWrap: "wrap", padding: "0.15rem 0" }}>
                <span style={{ fontSize: "0.75rem", fontWeight: 600, color: "var(--gray-600)" }}>Chủ đề AI:</span>
                {tag && (
                  <button
                    type="button"
                    onClick={() => {
                      setTag("");
                      performSearch(query, 1, { tag: "" });
                    }}
                    style={{
                      padding: "0.2rem 0.6rem",
                      borderRadius: "9999px",
                      fontSize: "0.75rem",
                      fontWeight: 600,
                      backgroundColor: "#fef2f2",
                      color: "#b91c1c",
                      border: "1px dashed #f87171",
                      cursor: "pointer",
                    }}
                  >
                    Bỏ lọc chủ đề (x)
                  </button>
                )}
                {tagList.slice(0, 12).map(({ tag: t, count }) => {
                  const isSelected =
                    tag.toLowerCase() === t.toLowerCase() ||
                    tag.replace("#", "").toLowerCase() === t.replace("#", "").toLowerCase();
                  return (
                    <button
                      key={t}
                      type="button"
                      onClick={() => {
                        const nextTag = isSelected ? "" : t;
                        setTag(nextTag);
                        performSearch(query, 1, { tag: nextTag });
                      }}
                      style={{
                        padding: "0.2rem 0.55rem",
                        borderRadius: "9999px",
                        fontSize: "0.75rem",
                        fontWeight: isSelected ? 700 : 500,
                        backgroundColor: isSelected ? "#059669" : "#ecfdf5",
                        color: isSelected ? "white" : "#065f46",
                        border: `1px solid ${isSelected ? "#059669" : "#a7f3d0"}`,
                        cursor: "pointer",
                        display: "inline-flex",
                        alignItems: "center",
                        gap: "0.25rem",
                      }}
                    >
                      <span>{t}</span>
                      <span style={{ opacity: isSelected ? 1 : 0.7, fontSize: "0.7rem" }}>({count})</span>
                    </button>
                  );
                })}
              </div>
            );
          })()}

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
                      <div style={{ display: "flex", alignItems: "center", gap: "0.5rem", marginBottom: "0.35rem", flexWrap: "wrap" }}>
                        <OCRStatusBadge status={hit.ocr_status} />
                        {(hit.doc_type_name || hit.category_name) && (
                          <span style={{ fontSize: "0.75rem", color: "var(--primary-700)", backgroundColor: "var(--primary-50)", padding: "0.15rem 0.5rem", borderRadius: "4px", fontWeight: 600 }}>
                            {hit.doc_type_name || hit.category_name}
                          </span>
                        )}
                        {(hit.needs_review || hit.doc_type_code === "KHAC" || (hit.doc_type_confidence !== undefined && hit.doc_type_confidence < 0.6)) && (
                          <span
                            className="badge-needs-review"
                            style={{
                              fontSize: "0.75rem",
                              color: "#b91c1c",
                              backgroundColor: "#fee2e2",
                              padding: "0.15rem 0.5rem",
                              borderRadius: "4px",
                              fontWeight: 600,
                            }}
                          >
                            Cần kiểm tra
                          </span>
                        )}
                        {hit.ocr_scope === "first_page" && (hit.page_count ?? 1) > 1 && (
                          <span
                            className="badge-ocr-scope"
                            style={{
                              fontSize: "0.75rem",
                              color: "#b45309",
                              backgroundColor: "#fef3c7",
                              padding: "0.15rem 0.5rem",
                              borderRadius: "4px",
                              fontWeight: 600,
                            }}
                          >
                            Mới OCR trang 1: nội dung các trang sau chưa được tìm kiếm
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
                            <>
                              {formatDisplayTitle(hit.title).code && (
                                <span style={{ color: "var(--primary-600)", marginRight: "0.4rem", fontWeight: 800 }}>
                                  [{formatDisplayTitle(hit.title).code}]
                                </span>
                              )}
                              {formatDisplayTitle(hit.title).mainTitle}
                            </>
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

