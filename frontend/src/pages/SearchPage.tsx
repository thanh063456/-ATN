import React, { useState, useEffect } from "react";
import { Link, useSearchParams } from "react-router-dom";
import {
  Search,
  SlidersHorizontal,
  FileText,
  Calendar,
  User,
  GraduationCap,
  ArrowRight,
  Info,
  Clock,
  ChevronLeft,
  ChevronRight,
  RotateCcw,
  CheckCircle2,
  AlertTriangle,
  HelpCircle,
  FileCheck,
  AlertOctagon,
  ShieldCheck,
  ShieldAlert,
  Download,
  X,
  Layers,
  GitBranch,
  Scan,
  BarChart3,
  CopyCheck,
  Building2,
  TrendingUp,
  Tag,
  History,
  Cpu,
} from "lucide-react";
import { Card } from "../components/common/Card";
import { Button } from "../components/common/Button";
import { OCRStatusBadge } from "../components/common/Badge";
import {
  searchApi,
  SearchResponse,
  SearchHit,
  SuggestItem,
  FaqAnswerResponse,
  PolicyAuditResponse,
  CrossDocumentFraudResponse,
  PercolateRoutingResponse,
  CtsvMultiDimensionalAnalyticsResponse,
  SpatialHighlightResponse,
  DuplicateCheckResponse,
  DocumentAutoTagsResponse,
  DocumentAuditTrailResponse,
  HybridRrfHit,
  HybridRrfSearchResponse,
} from "../api/search";
import { useToastStore } from "../stores/useToastStore";
import { useAuthStore } from "../stores/useAuthStore";

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

// Chuyển đổi một kết quả HybridRrfHit sang SearchHit để tái sử dụng toàn bộ modals công cụ
function convertHybridHitToSearchHit(h: HybridRrfHit): SearchHit {
  return {
    document_id: h.document_id,
    title: h.title,
    category_name: h.category_name,
    doc_type_name: h.category_name,
    student_name: h.student_name,
    student_id: h.student_id,
    content_snippet: h.content_snippet,
    score: Number(h.rrf_score.toFixed(5)),
    highlights: {},
    ocr_status: "DONE",
    ocr_scope: "full",
    tags: [],
  };
}

export const SearchPage: React.FC = () => {
  const { user } = useAuthStore();
  const isAdmin = user?.role === "ADMIN";
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

  // Autocomplete / Search-As-You-Type
  const [suggestions, setSuggestions] = useState<SuggestItem[]>([]);
  const [showSuggestions, setShowSuggestions] = useState(false);
  const searchContainerRef = React.useRef<HTMLDivElement>(null);

  const [searchResponse, setSearchResponse] = useState<SearchResponse | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [hasSearched, setHasSearched] = useState(false);
  const [currentPage, setCurrentPage] = useState(initialPage);

  // ── Navigation View Tabs (Rút gọn còn 3 tab chính tinh gọn) ──────────────
  const [activeTab, setActiveTab] = useState<
    | "fulltext"
    | "faq"
    | "ctsv_analytics"
  >("fulltext");

  // ── Tìm kiếm Lai RRF (BM25 + kNN Reciprocal Rank Fusion) tích hợp ─────────
  const [isHybridMode, setIsHybridMode] = useState(true);
  const [hybridConstantK, setHybridConstantK] = useState(20);
  const [hybridData, setHybridData] = useState<HybridRrfSearchResponse | null>(null);
  const [isHybridLoading, setIsHybridLoading] = useState(false);

  // ── Modal 1: Policy Audit Modal ───────────────────────────────────────────
  const [policyModalDoc, setPolicyModalDoc] = useState<SearchHit | null>(null);
  const [policyCode, setPolicyCode] = useState<string>("NGHI_DINH_81");
  const [policyAuditData, setPolicyAuditData] = useState<PolicyAuditResponse | null>(null);
  const [isAuditingPolicy, setIsAuditingPolicy] = useState(false);

  // ── Modal 2: Cross-Document Anti-Fraud Audit Modal ────────────────────────
  const [fraudModalDoc, setFraudModalDoc] = useState<SearchHit | null>(null);
  const [fraudAuditData, setFraudAuditData] = useState<CrossDocumentFraudResponse | null>(null);
  const [isAuditingFraud, setIsAuditingFraud] = useState(false);

  // ── Feature 1: FAQ Regulation Q&A ─────────────────────────────────────────
  const [faqInput, setFaqInput] = useState("");
  const [faqData, setFaqData] = useState<FaqAnswerResponse | null>(null);
  const [isFaqLoading, setIsFaqLoading] = useState(false);

  // ── Đề tài CTSV - Feature 1: Percolator Reverse Routing Modal ──────────────
  const [percolateModalDoc, setPercolateModalDoc] = useState<SearchHit | null>(null);
  const [percolateData, setPercolateData] = useState<PercolateRoutingResponse | null>(null);
  const [isPercolateLoading, setIsPercolateLoading] = useState(false);

  // ── Đề tài CTSV - Feature 2: Spatial Highlighting Bounding Box Modal ──────
  const [spatialModalDoc, setSpatialModalDoc] = useState<SearchHit | null>(null);
  const [spatialKeyword, setSpatialKeyword] = useState<string>("");
  const [spatialData, setSpatialData] = useState<SpatialHighlightResponse | null>(null);
  const [isSpatialLoading, setIsSpatialLoading] = useState(false);

  // ── Đề tài CTSV - Feature 3: Multi-Faceted CTSV Analytics Tab ─────────────
  const [ctsvBreakdown, setCtsvBreakdown] = useState<CtsvMultiDimensionalAnalyticsResponse | null>(null);
  const [isBreakdownLoading, setIsBreakdownLoading] = useState(false);

  // ── Đề tài CTSV - Feature 5: Cross-Document MLT Duplicate Modal ────────────
  const [duplicateModalDoc, setDuplicateModalDoc] = useState<SearchHit | null>(null);
  const [duplicateData, setDuplicateData] = useState<DuplicateCheckResponse | null>(null);
  const [isDuplicateLoading, setIsDuplicateLoading] = useState(false);

  // ── Đề tài CTSV Nâng cao 2: Auto-Tagging Modal (significant_text) ─────────
  const [autoTagsModalDoc, setAutoTagsModalDoc] = useState<SearchHit | null>(null);
  const [autoTagsData, setAutoTagsData] = useState<DocumentAutoTagsResponse | null>(null);
  const [isAutoTagsLoading, setIsAutoTagsLoading] = useState(false);

  // ── Đề tài CTSV Nâng cao 5: Audit Trail & Diffs Modal ─────────────────────
  const [auditTrailModalDoc, setAuditTrailModalDoc] = useState<SearchHit | null>(null);
  const [auditTrailData, setAuditTrailData] = useState<DocumentAuditTrailResponse | null>(null);
  const [isAuditTrailLoading, setIsAuditTrailLoading] = useState(false);

  // Handlers
  const handleOpenPolicyAudit = async (doc: SearchHit, code = policyCode) => {
    setPolicyModalDoc(doc);
    setPolicyCode(code);
    setIsAuditingPolicy(true);
    try {
      const data = await searchApi.auditPolicy(doc.document_id, code);
      setPolicyAuditData(data);
    } catch (err: any) {
      addToast({
        type: "error",
        title: "Lỗi thẩm định",
        message: err?.response?.data?.detail || "Không thể thực hiện thẩm định hồ sơ",
      });
    } finally {
      setIsAuditingPolicy(false);
    }
  };

  const handleOpenFraudAudit = async (doc: SearchHit) => {
    setFraudModalDoc(doc);
    setIsAuditingFraud(true);
    try {
      const data = await searchApi.auditFraud(doc.document_id, doc.student_id);
      setFraudAuditData(data);
    } catch (err: any) {
      addToast({
        type: "error",
        title: "Lỗi đối soát",
        message: err?.response?.data?.detail || "Không thể kiểm tra xung đột chứng từ",
      });
    } finally {
      setIsAuditingFraud(false);
    }
  };

  const handleAskFaq = async (questionText: string) => {
    if (!questionText.trim()) return;
    setIsFaqLoading(true);
    try {
      const data = await searchApi.askFaq(questionText.trim());
      setFaqData(data);
    } catch (err: any) {
      addToast({
        type: "error",
        title: "Lỗi trợ lý quy chế",
        message: "Không thể kết nối trợ lý quy chế lúc này",
      });
    } finally {
      setIsFaqLoading(false);
    }
  };

  const handleOpenPercolateRouting = async (doc: SearchHit) => {
    setPercolateModalDoc(doc);
    setIsPercolateLoading(true);
    try {
      const data = await searchApi.getPercolateRouting(doc.document_id);
      setPercolateData(data);
    } catch (err: any) {
      addToast({
        type: "error",
        title: "Lỗi phân luồng",
        message: err?.response?.data?.detail || "Không thể thực hiện phân luồng Percolator",
      });
    } finally {
      setIsPercolateLoading(false);
    }
  };

  const handleOpenSpatialHighlights = async (doc: SearchHit, kw?: string) => {
    setSpatialModalDoc(doc);
    const targetKw = kw || query || doc.title.split(" ")[0] || "sinh viên";
    setSpatialKeyword(targetKw);
    setIsSpatialLoading(true);
    try {
      const data = await searchApi.getSpatialHighlights(doc.document_id, targetKw);
      setSpatialData(data);
    } catch (err: any) {
      addToast({
        type: "error",
        title: "Lỗi tọa độ",
        message: err?.response?.data?.detail || "Không thể trích xuất tọa độ Bounding Box",
      });
    } finally {
      setIsSpatialLoading(false);
    }
  };

  const handleOpenDuplicateCheck = async (doc: SearchHit) => {
    setDuplicateModalDoc(doc);
    setIsDuplicateLoading(true);
    try {
      const data = await searchApi.checkDuplicates(doc.document_id);
      setDuplicateData(data);
    } catch (err: any) {
      addToast({
        type: "error",
        title: "Lỗi trùng lặp",
        message: err?.response?.data?.detail || "Không thể kiểm tra trùng lặp More-Like-This",
      });
    } finally {
      setIsDuplicateLoading(false);
    }
  };

  const handleLoadCtsvBreakdown = async () => {
    setIsBreakdownLoading(true);
    try {
      const data = await searchApi.getCtsvBreakdown();
      setCtsvBreakdown(data);
    } catch (err: any) {
      addToast({
        type: "error",
        title: "Lỗi thống kê",
        message: "Không thể tải báo cáo đa chiều CTSV",
      });
    } finally {
      setIsBreakdownLoading(false);
    }
  };

  const handleOpenAutoTags = async (doc: SearchHit) => {
    setAutoTagsModalDoc(doc);
    setIsAutoTagsLoading(true);
    try {
      const data = await searchApi.getDocumentAutoTags(doc.document_id);
      setAutoTagsData(data);
    } catch (err: any) {
      addToast({
        type: "error",
        title: "Lỗi trích xuất thực thể",
        message: "Không thể trích xuất thẻ nhãn significant_text",
      });
    } finally {
      setIsAutoTagsLoading(false);
    }
  };

  const handleOpenAuditTrail = async (doc: SearchHit) => {
    setAuditTrailModalDoc(doc);
    setIsAuditTrailLoading(true);
    try {
      const data = await searchApi.getDocumentAuditTrail(doc.document_id);
      setAuditTrailData(data);
    } catch (err: any) {
      addToast({
        type: "error",
        title: "Lỗi kiểm toán phiên bản",
        message: "Không thể truy xuất nhật ký Diffs",
      });
    } finally {
      setIsAuditTrailLoading(false);
    }
  };

  // ── Đề xuất 1: Handler Tìm kiếm Lai RRF ──────────────────────────────────
  const handleSearchHybridRrf = async (queryText: string, kVal = hybridConstantK) => {
    if (!queryText.trim()) return;
    setIsHybridLoading(true);
    try {
      const data = await searchApi.searchHybridRrf({
        query: queryText.trim(),
        limit: 10,
        rank_constant_k: kVal,
      });
      setHybridData(data);
    } catch (err: any) {
      addToast({
        type: "error",
        title: "Lỗi tìm kiếm Lai RRF",
        message: err?.response?.data?.detail || "Không thể thực hiện tìm kiếm lai",
      });
    } finally {
      setIsHybridLoading(false);
    }
  };


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

    setIsLoading(true);
    setHasSearched(true);
    setCurrentPage(pageNumber);
    setShowSuggestions(false);

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
      const newParams: Record<string, string> = { page: String(pageNumber) };
      if (trimmed) newParams.q = trimmed;
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

  // Tự động tải danh sách tài liệu mới nhất khi vừa vào trang
  useEffect(() => {
    const qParam = searchParams.get("q") || "";
    setQuery(qParam);
    performSearch(qParam, initialPage);
  }, []);

  // Debounced Autocomplete khi người dùng đang gõ
  useEffect(() => {
    const trimmed = query.trim();
    if (trimmed.length < 2) {
      setSuggestions([]);
      setShowSuggestions(false);
      return;
    }

    const timer = setTimeout(async () => {
      try {
        const res = await searchApi.suggest(trimmed, 6);
        setSuggestions(res.suggestions || []);
        setShowSuggestions((res.suggestions || []).length > 0);
      } catch {
        setSuggestions([]);
        setShowSuggestions(false);
      }
    }, 200);

    return () => clearTimeout(timer);
  }, [query]);

  // Đóng gợi ý khi click ra ngoài ô tìm kiếm
  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (searchContainerRef.current && !searchContainerRef.current.contains(e.target as Node)) {
        setShowSuggestions(false);
      }
    };
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  const handleFormSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    performSearch(query, 1);
    if (isHybridMode && query.trim()) {
      handleSearchHybridRrf(query.trim(), hybridConstantK);
    } else {
      setHybridData(null);
    }
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
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", flexWrap: "wrap", gap: "1rem" }}>
        <div>
          <h1 style={{ fontSize: "1.35rem", fontWeight: 700, color: "var(--gray-900)" }}>
            Tra cứu Văn bản & Hồ sơ Công tác Sinh viên
          </h1>
          <p style={{ fontSize: "0.8125rem", color: "var(--gray-500)", marginTop: "0.2rem" }}>
            Tìm kiếm theo số hiệu văn bản (vd: 1395/KH-ĐHĐL), họ tên, mã số sinh viên hoặc nội dung toàn văn.
          </p>
        </div>
      </div>

      {/* ── Modern Streamlined 3-Tab Navigation Bar ── */}
      <div
        style={{
          display: "flex",
          alignItems: "center",
          gap: "0.5rem",
          backgroundColor: "#ffffff",
          border: "1px solid var(--border-color)",
          borderRadius: "0.875rem",
          padding: "0.45rem",
          boxShadow: "0 1px 3px rgba(0,0,0,0.04)",
        }}
      >
        {/* Tab 1: Tra cứu & Tìm kiếm Lai RRF */}
        <button
          type="button"
          onClick={() => setActiveTab("fulltext")}
          style={{
            flex: 1,
            display: "inline-flex",
            alignItems: "center",
            justifyContent: "center",
            gap: "0.5rem",
            padding: "0.65rem 1rem",
            borderRadius: "0.6rem",
            border: activeTab === "fulltext" ? "1px solid #2563eb" : "1px solid transparent",
            backgroundColor: activeTab === "fulltext" ? "var(--primary-600)" : "transparent",
            color: activeTab === "fulltext" ? "#ffffff" : "var(--gray-700)",
            fontWeight: activeTab === "fulltext" ? 700 : 600,
            fontSize: "0.875rem",
            cursor: "pointer",
            transition: "all 0.15s ease",
            boxShadow: activeTab === "fulltext" ? "0 2px 4px rgba(37,99,235,0.25)" : "none",
          }}
        >
          <Search size={16} />
          <span>Tra cứu Toàn văn & Tìm kiếm Lai (Hybrid RRF)</span>
          <span
            style={{
              fontSize: "0.6875rem",
              backgroundColor: activeTab === "fulltext" ? "rgba(255,255,255,0.25)" : "#eff6ff",
              color: activeTab === "fulltext" ? "#fff" : "#1e40af",
              padding: "0.15rem 0.5rem",
              borderRadius: "9999px",
              fontWeight: 700,
            }}
          >
            ES 8.9+ / Vector
          </span>
        </button>

        {/* Tab 2: Hỏi đáp Quy chế (FAQ AI) */}
        <button
          type="button"
          onClick={() => setActiveTab("faq")}
          style={{
            flex: 1,
            display: "inline-flex",
            alignItems: "center",
            justifyContent: "center",
            gap: "0.5rem",
            padding: "0.65rem 1rem",
            borderRadius: "0.6rem",
            border: activeTab === "faq" ? "1px solid #2563eb" : "1px solid transparent",
            backgroundColor: activeTab === "faq" ? "var(--primary-600)" : "transparent",
            color: activeTab === "faq" ? "#ffffff" : "var(--gray-700)",
            fontWeight: activeTab === "faq" ? 700 : 600,
            fontSize: "0.875rem",
            cursor: "pointer",
            transition: "all 0.15s ease",
            boxShadow: activeTab === "faq" ? "0 2px 4px rgba(37,99,235,0.25)" : "none",
          }}
        >
          <HelpCircle size={16} />
          <span>Hỏi đáp Quy chế CTSV</span>
          <span
            style={{
              fontSize: "0.6875rem",
              backgroundColor: activeTab === "faq" ? "rgba(255,255,255,0.25)" : "#fef3c7",
              color: activeTab === "faq" ? "#fff" : "#92400e",
              padding: "0.15rem 0.5rem",
              borderRadius: "9999px",
              fontWeight: 700,
            }}
          >
            Trợ lý AI
          </span>
        </button>

        {/* Tab 3: Thống kê CTSV */}
        <button
          type="button"
          onClick={() => {
            setActiveTab("ctsv_analytics");
            if (!ctsvBreakdown) handleLoadCtsvBreakdown();
          }}
          style={{
            flex: 1,
            display: "inline-flex",
            alignItems: "center",
            justifyContent: "center",
            gap: "0.5rem",
            padding: "0.65rem 1rem",
            borderRadius: "0.6rem",
            border: activeTab === "ctsv_analytics" ? "1px solid #2563eb" : "1px solid transparent",
            backgroundColor: activeTab === "ctsv_analytics" ? "var(--primary-600)" : "transparent",
            color: activeTab === "ctsv_analytics" ? "#ffffff" : "var(--gray-700)",
            fontWeight: activeTab === "ctsv_analytics" ? 700 : 600,
            fontSize: "0.875rem",
            cursor: "pointer",
            transition: "all 0.15s ease",
            boxShadow: activeTab === "ctsv_analytics" ? "0 2px 4px rgba(37,99,235,0.25)" : "none",
          }}
        >
          <BarChart3 size={16} />
          <span>Thống kê CTSV theo Khoa</span>
          <span
            style={{
              fontSize: "0.6875rem",
              backgroundColor: activeTab === "ctsv_analytics" ? "rgba(255,255,255,0.25)" : "#ecfdf5",
              color: activeTab === "ctsv_analytics" ? "#fff" : "#047857",
              padding: "0.15rem 0.5rem",
              borderRadius: "9999px",
              fontWeight: 700,
            }}
          >
            Aggregations
          </span>
        </button>
      </div>

      {activeTab === "fulltext" && (
        <>
          {/* Main Search Bar Card */}
          <Card padding="md">
            <form onSubmit={handleFormSubmit}>
              <div style={{ display: "flex", gap: "0.75rem", alignItems: "center" }}>
                <div
                  ref={searchContainerRef}
                  style={{
                flex: 1,
                position: "relative",
              }}
            >
              <div
                style={{
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
                  onChange={(e) => {
                    setQuery(e.target.value);
                    setShowSuggestions(true);
                  }}
                  onFocus={() => {
                    if (suggestions.length > 0) setShowSuggestions(true);
                  }}
                  placeholder="Tìm theo từ khóa, tiêu đề, mã số sinh viên (MSSV) hoặc tên người upload (vd: '2212461', 'canbo_ctsv', 'bảo lưu')..."
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

              {/* Floating Autocomplete Suggestions */}
              {showSuggestions && suggestions.length > 0 && (
                <div
                  style={{
                    position: "absolute",
                    top: "calc(100% + 6px)",
                    left: 0,
                    right: 0,
                    zIndex: 50,
                    backgroundColor: "#ffffff",
                    borderRadius: "var(--radius-md)",
                    border: "1px solid var(--border-color)",
                    boxShadow: "0 10px 25px -5px rgba(0, 0, 0, 0.12), 0 8px 10px -6px rgba(0, 0, 0, 0.08)",
                    overflow: "hidden",
                  }}
                >
                  <div
                    style={{
                      padding: "0.4rem 0.85rem",
                      fontSize: "0.6875rem",
                      fontWeight: 700,
                      color: "var(--gray-400)",
                      textTransform: "uppercase",
                      letterSpacing: "0.05em",
                      backgroundColor: "var(--gray-50)",
                    }}
                  >
                    Gợi ý văn bản khớp từ khóa
                  </div>
                  {suggestions.map((item, idx) => (
                    <div
                      key={idx}
                      onClick={() => {
                        setQuery(item.text);
                        setShowSuggestions(false);
                        performSearch(item.text, 1);
                        if (isHybridMode) {
                          handleSearchHybridRrf(item.text, hybridConstantK);
                        }
                      }}
                      style={{
                        padding: "0.65rem 0.85rem",
                        display: "flex",
                        alignItems: "center",
                        gap: "0.6rem",
                        cursor: "pointer",
                        borderTop: "1px solid var(--gray-100)",
                        transition: "background-color 0.15s ease",
                      }}
                      onMouseEnter={(e) => (e.currentTarget.style.backgroundColor = "var(--primary-50)")}
                      onMouseLeave={(e) => (e.currentTarget.style.backgroundColor = "transparent")}
                    >
                      <FileText size={15} color="var(--primary-600)" />
                      <span
                        style={{
                          fontSize: "0.875rem",
                          color: "var(--gray-800)",
                          fontWeight: 500,
                          flex: 1,
                          overflow: "hidden",
                          textOverflow: "ellipsis",
                          whiteSpace: "nowrap",
                        }}
                      >
                        {item.text}
                      </span>
                      <ArrowRight size={13} color="var(--gray-400)" />
                    </div>
                  ))}
                </div>
              )}
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

        {/* Hybrid RRF Mode Switcher & Parameters (Chỉ hiển thị cho Quản trị viên ADMIN để đánh giá IR thực nghiệm) */}
        {isAdmin && (
          <div
            style={{
              display: "flex",
              alignItems: "center",
              justifyContent: "space-between",
              flexWrap: "wrap",
              gap: "0.75rem",
              marginTop: "1rem",
              padding: "0.6rem 0.85rem",
              backgroundColor: isHybridMode ? "#f5f3ff" : "#f8fafc",
              border: isHybridMode ? "1px solid #c7d2fe" : "1px solid var(--border-color)",
              borderRadius: "var(--radius-md)",
              transition: "all 0.2s ease",
            }}
          >
            <div style={{ display: "flex", alignItems: "center", gap: "0.6rem" }}>
              <label
                style={{
                  display: "inline-flex",
                  alignItems: "center",
                  gap: "0.45rem",
                  fontSize: "0.8125rem",
                  fontWeight: 700,
                  color: isHybridMode ? "#4338ca" : "var(--gray-700)",
                  cursor: "pointer",
                }}
              >
                <input
                  type="checkbox"
                  checked={isHybridMode}
                  onChange={(e) => {
                    const enabled = e.target.checked;
                    setIsHybridMode(enabled);
                    if (enabled && query.trim()) {
                      handleSearchHybridRrf(query.trim(), hybridConstantK);
                    }
                  }}
                  style={{ width: "16px", height: "16px", cursor: "pointer", accentColor: "#4f46e5" }}
                />
                <Cpu size={16} color={isHybridMode ? "#4f46e5" : "var(--gray-500)"} />
                <span>Chế độ Tìm kiếm Lai RRF (BM25 + kNN Vector Ngữ nghĩa 768 chiều)</span>
              </label>
              <span
                style={{
                  fontSize: "0.625rem",
                  fontWeight: 700,
                  backgroundColor: isHybridMode ? "#4f46e5" : "#e2e8f0",
                  color: isHybridMode ? "#ffffff" : "var(--gray-600)",
                  padding: "0.15rem 0.45rem",
                  borderRadius: "9999px",
                }}
              >
                Elasticsearch 8.9+
              </span>
            </div>

            {isHybridMode && (
              <div style={{ display: "flex", alignItems: "center", gap: "0.4rem" }}>
                <span style={{ fontSize: "0.75rem", color: "var(--gray-600)", fontWeight: 600 }}>Hằng số RRF (k):</span>
                {[
                  { label: "k = 20 (Chuẩn ES 8.9)", val: 20 },
                  { label: "k = 60 (Cormack)", val: 60 },
                ].map((preset) => (
                  <button
                    key={preset.val}
                    type="button"
                    onClick={() => {
                      setHybridConstantK(preset.val);
                      if (query.trim()) handleSearchHybridRrf(query.trim(), preset.val);
                    }}
                    style={{
                      padding: "0.2rem 0.5rem",
                      borderRadius: "4px",
                      fontSize: "0.75rem",
                      fontWeight: hybridConstantK === preset.val ? 700 : 500,
                      backgroundColor: hybridConstantK === preset.val ? "#4f46e5" : "#ffffff",
                      color: hybridConstantK === preset.val ? "#ffffff" : "var(--gray-700)",
                      border: "1px solid",
                      borderColor: hybridConstantK === preset.val ? "#4f46e5" : "var(--border-color)",
                      cursor: "pointer",
                    }}
                  >
                    {preset.label}
                  </button>
                ))}
              </div>
            )}
          </div>
        )}

        {/* Quick Sample Queries */}
        <div style={{ display: "flex", alignItems: "center", gap: "0.5rem", marginTop: "0.75rem", flexWrap: "wrap" }}>
          <span style={{ fontSize: "0.75rem", color: "var(--gray-500)", fontWeight: 600 }}>Gợi ý mẫu:</span>
          {[
            "nghị định 81 miễn giảm học phí sv nghèo khó khăn",
            "học bổng khuyến khích học tập dlu kỳ 1",
            "đơn xin tạm hoãn thi kết thúc học phần vì sức khỏe",
            "học phí",
            "20210678",
            "bảo lưu",
          ].map((item, idx) => (
            <button
              key={idx}
              type="button"
              onClick={() => {
                setQuery(item);
                performSearch(item, 1);
                if (isHybridMode) {
                  handleSearchHybridRrf(item, hybridConstantK);
                }
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
          {/* Hybrid RRF Loading State */}
          {isHybridLoading && !hybridData && (
            <Card padding="md">
              <div style={{ padding: "1.75rem", textAlign: "center", color: "var(--gray-500)" }}>
                <Clock className="animate-spin" size={26} style={{ margin: "0 auto 0.5rem", color: "var(--primary-600)" }} />
                <div style={{ fontWeight: 600, color: "var(--gray-700)" }}>Đang xếp hạng song song BM25 và kNN vector 768 chiều qua RRF (k = {hybridConstantK})...</div>
                <span style={{ fontSize: "0.75rem", color: "var(--gray-500)" }}>Thuật toán Reciprocal Rank Fusion kết hợp độ chính xác từ khóa và chiều sâu ngữ nghĩa</span>
              </div>
            </Card>
          )}

          {/* Hybrid RRF Ranked Results */}
          {isHybridMode && hybridData && hybridData.results.length > 0 && (
            <div style={{ display: "flex", flexDirection: "column", gap: "0.85rem", marginBottom: "0.5rem" }}>
              {/* Hybrid Header & Metrics */}
              {isAdmin ? (
                <div
                  style={{
                    display: "flex",
                    justifyContent: "space-between",
                    alignItems: "center",
                    flexWrap: "wrap",
                    gap: "0.75rem",
                    padding: "0.75rem 1rem",
                    backgroundColor: "#eff6ff",
                    borderRadius: "var(--radius-md)",
                    border: "1px solid #bfdbfe",
                  }}
                >
                  <div style={{ display: "flex", alignItems: "center", gap: "0.5rem" }}>
                    <Layers size={18} color="#1d4ed8" />
                    <span style={{ fontWeight: 700, fontSize: "0.9375rem", color: "#1e3a8a" }}>
                      Kết quả Xếp hạng Lai RRF (Dense Vector 768d + BM25 Lexical)
                    </span>
                    <span style={{ fontSize: "0.75rem", color: "#64748b" }}>
                      ({hybridData.results.length} tài liệu tối ưu nhất, k = {hybridData.rank_constant_k})
                    </span>
                  </div>

                  <div style={{ display: "flex", alignItems: "center", gap: "0.5rem", flexWrap: "wrap" }}>
                    <span style={{ fontSize: "0.75rem", fontWeight: 700, padding: "0.2rem 0.55rem", borderRadius: "9999px", backgroundColor: "#dcfce7", color: "#166534" }}>
                      Khớp kép: {hybridData.metrics?.both_count ?? hybridData.results.filter(r => r.match_type === "HYBRID_BOTH").length}
                    </span>
                    <span style={{ fontSize: "0.75rem", fontWeight: 700, padding: "0.2rem 0.55rem", borderRadius: "9999px", backgroundColor: "#dbeafe", color: "#1e40af" }}>
                      BM25 từ khóa: {hybridData.metrics?.keyword_only_count ?? hybridData.results.filter(r => r.match_type === "KEYWORD_ONLY").length}
                    </span>
                    <span style={{ fontSize: "0.75rem", fontWeight: 700, padding: "0.2rem 0.55rem", borderRadius: "9999px", backgroundColor: "#f1f5f9", color: "#334155" }}>
                      kNN Ngữ nghĩa: {hybridData.metrics?.semantic_only_count ?? hybridData.results.filter(r => r.match_type === "SEMANTIC_ONLY").length}
                    </span>
                  </div>
                </div>
              ) : (
                <div
                  style={{
                    display: "flex",
                    alignItems: "center",
                    gap: "0.5rem",
                    padding: "0.6rem 0.85rem",
                    backgroundColor: "#f8fafc",
                    borderRadius: "var(--radius-md)",
                    border: "1px solid var(--border-color)",
                  }}
                >
                  <CheckCircle2 size={16} color="var(--primary-600)" />
                  <span style={{ fontWeight: 600, fontSize: "0.875rem", color: "var(--gray-800)" }}>
                    Kết quả tìm kiếm phù hợp nhất ({hybridData.results.length} tài liệu)
                  </span>
                </div>
              )}

              {/* Hybrid Hits Cards */}
              {hybridData.results.map((hit, hIdx) => {
                const titleInfo = formatDisplayTitle(hit.title);
                const isBoth = hit.match_type === "HYBRID_BOTH";
                const isBm25 = hit.match_type === "KEYWORD_ONLY";
                const searchHitEquivalent = convertHybridHitToSearchHit(hit);

                return (
                  <Card
                    key={hit.document_id || hIdx}
                    padding="md"
                    style={{
                      borderLeft: isBoth ? "5px solid #16a34a" : isBm25 ? "5px solid #2563eb" : "5px solid #9333ea",
                      backgroundColor: isBoth ? "#fcfdfc" : "#ffffff",
                      transition: "box-shadow 0.2s ease",
                    }}
                  >
                    <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", gap: "1rem", flexWrap: "wrap" }}>
                      <div style={{ flex: 1, minWidth: "280px" }}>
                        <div style={{ display: "flex", alignItems: "center", gap: "0.5rem", flexWrap: "wrap", marginBottom: "0.3rem" }}>
                          {isAdmin && (
                            <span
                              style={{
                                padding: "0.2rem 0.6rem",
                                borderRadius: "9999px",
                                fontSize: "0.6875rem",
                                fontWeight: 700,
                                backgroundColor: isBoth ? "#dcfce7" : isBm25 ? "#dbeafe" : "#f1f5f9",
                                color: isBoth ? "#166534" : isBm25 ? "#1e40af" : "#334155",
                                display: "inline-flex",
                                alignItems: "center",
                                gap: "0.3rem",
                              }}
                            >
                              {isBoth ? <CheckCircle2 size={12} /> : isBm25 ? <Search size={12} /> : <Cpu size={12} />}
                              {isBoth ? "KHỚP KÉP (HYBRID)" : isBm25 ? "TỪ KHÓA CHÍNH XÁC (BM25)" : "NGỮ NGHĨA VECTOR (kNN)"}
                            </span>
                          )}
                          <span style={{ fontSize: "0.75rem", color: "var(--gray-500)", backgroundColor: "var(--gray-100)", padding: "0.15rem 0.45rem", borderRadius: "4px" }}>
                            {hit.category_name}
                          </span>
                          {titleInfo.code && (
                            <span style={{ fontSize: "0.75rem", fontFamily: "monospace", color: "#1d4ed8", backgroundColor: "#eff6ff", padding: "0.15rem 0.45rem", borderRadius: "4px", fontWeight: 700 }}>
                              Số: {titleInfo.code}
                            </span>
                          )}
                        </div>

                        <Link
                          to={`/documents/${hit.document_id}`}
                          style={{
                            fontSize: "1.05rem",
                            fontWeight: 700,
                            color: "var(--primary-700)",
                            textDecoration: "none",
                            lineHeight: 1.4,
                            display: "block",
                          }}
                        >
                          {titleInfo.mainTitle}
                        </Link>

                        <div style={{ fontSize: "0.8125rem", color: "var(--gray-600)", marginTop: "0.25rem", display: "flex", alignItems: "center", gap: "0.75rem", flexWrap: "wrap" }}>
                          {(hit.student_name || hit.student_id) && (
                            <>
                              <span>Sinh viên: <strong>{hit.student_name || "N/A"}</strong></span>
                              <span>MSSV: <code style={{ color: "var(--primary-700)", fontWeight: 700, backgroundColor: "#eff6ff", padding: "0.1rem 0.35rem", borderRadius: "3px" }}>{hit.student_id || "N/A"}</code></span>
                            </>
                          )}
                          <span style={{ color: "var(--gray-400)" }}>•</span>
                          <span>Người upload: <strong style={{ color: "#1e3a8a" }}>{hit.uploader_name || "Cán bộ CTSV"}</strong></span>
                        </div>

                        {hit.content_snippet && (
                          <p style={{ fontSize: "0.8125rem", color: "var(--gray-600)", marginTop: "0.4rem", lineHeight: 1.5 }}>
                            {hit.content_snippet}
                          </p>
                        )}
                      </div>

                      {/* Rank & RRF Score Badges Box (Chỉ hiển thị cho Admin; Sinh viên & Cán bộ chỉ xem nút chi tiết) */}
                      {isAdmin ? (
                        <div
                          style={{
                            display: "flex",
                            flexDirection: "column",
                            alignItems: "flex-end",
                            gap: "0.4rem",
                            backgroundColor: "#f8fafc",
                            padding: "0.6rem 0.85rem",
                            borderRadius: "var(--radius-md)",
                            border: "1px solid #e2e8f0",
                            minWidth: "210px",
                          }}
                        >
                          <div style={{ display: "flex", alignItems: "baseline", gap: "0.4rem" }}>
                            <span style={{ fontSize: "0.6875rem", fontWeight: 700, color: "var(--gray-500)", textTransform: "uppercase" }}>Điểm RRF:</span>
                            <span style={{ fontSize: "1.15rem", fontWeight: 900, color: "#1d4ed8", fontFamily: "monospace" }}>
                              {hit.rrf_score.toFixed(5)}
                            </span>
                          </div>

                          <div style={{ display: "flex", gap: "0.5rem", fontSize: "0.75rem" }}>
                            <span style={{ color: hit.bm25_rank ? "#1e40af" : "var(--gray-400)", backgroundColor: hit.bm25_rank ? "#dbeafe" : "#f1f5f9", padding: "0.15rem 0.4rem", borderRadius: "3px" }}>
                              BM25: {hit.bm25_rank ? `#${hit.bm25_rank}` : "Không khớp"}
                            </span>
                            <span style={{ color: hit.knn_rank ? "#6b21a8" : "var(--gray-400)", backgroundColor: hit.knn_rank ? "#f3e8ff" : "#f1f5f9", padding: "0.15rem 0.4rem", borderRadius: "3px" }}>
                              kNN: {hit.knn_rank ? `#${hit.knn_rank}` : "Không khớp"}
                            </span>
                          </div>

                          <div style={{ fontSize: "0.6875rem", color: "var(--gray-500)", textAlign: "right", marginTop: "0.15rem" }}>
                            {hit.explanation}
                          </div>

                          <Link to={`/documents/${hit.document_id}`} style={{ marginTop: "0.25rem" }}>
                            <Button variant="outline" size="sm" rightIcon={<ArrowRight size={13} />} style={{ fontSize: "0.75rem", padding: "0.2rem 0.55rem", height: "26px" }}>
                              Xem chi tiết
                            </Button>
                          </Link>
                        </div>
                      ) : (
                        <div style={{ display: "flex", alignItems: "center" }}>
                          <Link to={`/documents/${hit.document_id}`}>
                            <Button variant="outline" size="sm" rightIcon={<ArrowRight size={13} />} style={{ fontSize: "0.75rem", padding: "0.25rem 0.65rem", height: "28px" }}>
                              Xem chi tiết
                            </Button>
                          </Link>
                        </div>
                      )}
                    </div>

                    {/* Action Buttons for Hybrid Hit (Chỉ hiển thị cho Admin khi đánh giá các công cụ chuyên sâu) */}
                    {isAdmin && (
                      <div
                        style={{
                          display: "flex",
                          alignItems: "center",
                          justifyContent: "space-between",
                          marginTop: "0.75rem",
                          paddingTop: "0.65rem",
                          borderTop: "1px solid var(--gray-100)",
                          flexWrap: "wrap",
                          gap: "0.4rem",
                        }}
                      >
                        <div style={{ display: "flex", alignItems: "center", gap: "0.35rem", flexWrap: "wrap" }}>
                          <span style={{ fontSize: "0.6875rem", fontWeight: 700, color: "var(--gray-400)", textTransform: "uppercase" }}>
                            Công cụ:
                          </span>
                          <Button
                            type="button"
                            variant="outline"
                            size="sm"
                            leftIcon={<GitBranch size={12} color="#4f46e5" />}
                            onClick={() => handleOpenPercolateRouting(searchHitEquivalent)}
                            style={{ fontSize: "0.7rem", padding: "0.2rem 0.5rem", height: "26px", backgroundColor: "#eef2ff", borderColor: "#c7d2fe", color: "#3730a3" }}
                          >
                            Phân luồng Percolator
                          </Button>
                          <Button
                            type="button"
                            variant="outline"
                            size="sm"
                            leftIcon={<Scan size={12} color="#0284c7" />}
                            onClick={() => handleOpenSpatialHighlights(searchHitEquivalent)}
                            style={{ fontSize: "0.7rem", padding: "0.2rem 0.5rem", height: "26px", backgroundColor: "#f0f9ff", borderColor: "#bae6fd", color: "#0369a1" }}
                          >
                            Tọa độ Scan OCR
                          </Button>
                          <Button
                            type="button"
                            variant="outline"
                            size="sm"
                            leftIcon={<CopyCheck size={12} color="#be123c" />}
                            onClick={() => handleOpenDuplicateCheck(searchHitEquivalent)}
                            style={{ fontSize: "0.7rem", padding: "0.2rem 0.5rem", height: "26px", backgroundColor: "#fff1f2", borderColor: "#fecdd3", color: "#9f1239" }}
                          >
                            Trùng lặp MLT
                          </Button>
                          <Button
                            type="button"
                            variant="outline"
                            size="sm"
                            leftIcon={<Tag size={12} color="#059669" />}
                            onClick={() => handleOpenAutoTags(searchHitEquivalent)}
                            style={{ fontSize: "0.7rem", padding: "0.2rem 0.5rem", height: "26px", backgroundColor: "#ecfdf5", borderColor: "#a7f3d0", color: "#065f46" }}
                          >
                            Gán nhãn Tags
                          </Button>
                          <Button
                            type="button"
                            variant="outline"
                            size="sm"
                            leftIcon={<History size={12} color="#7c3aed" />}
                            onClick={() => handleOpenAuditTrail(searchHitEquivalent)}
                            style={{ fontSize: "0.7rem", padding: "0.2rem 0.5rem", height: "26px", backgroundColor: "#f5f3ff", borderColor: "#ddd6fe", color: "#5b21b6" }}
                          >
                            Nhật ký Diffs
                          </Button>
                        </div>

                        <div style={{ display: "flex", alignItems: "center", gap: "0.35rem" }}>
                          <Button
                            type="button"
                            variant="outline"
                            size="sm"
                            leftIcon={<FileCheck size={12} color="#059669" />}
                            onClick={() => handleOpenPolicyAudit(searchHitEquivalent, "NGHI_DINH_81")}
                            style={{ fontSize: "0.7rem", padding: "0.2rem 0.5rem", height: "26px", backgroundColor: "#f0fdf4", borderColor: "#a7f3d0", color: "#065f46" }}
                          >
                            Thẩm định NĐ 81
                          </Button>
                          <Button
                            type="button"
                            variant="outline"
                            size="sm"
                            leftIcon={<ShieldCheck size={12} color="#d97706" />}
                            onClick={() => handleOpenFraudAudit(searchHitEquivalent)}
                            style={{ fontSize: "0.7rem", padding: "0.2rem 0.5rem", height: "26px", backgroundColor: "#fffbeb", borderColor: "#fde68a", color: "#92400e" }}
                          >
                            Đối soát Gian lận
                          </Button>
                        </div>
                      </div>
                    )}
                  </Card>
                );
              })}
            </div>
          )}

          {/* Section title for full catalog when hybrid results are present */}
          {isHybridMode && hybridData && hybridData.results.length > 0 && (
            <div style={{ display: "flex", alignItems: "center", gap: "0.5rem", margin: "0.5rem 0 0.25rem", borderTop: "2px dashed var(--gray-200)", paddingTop: "1rem" }}>
              <FileText size={16} color="var(--primary-600)" />
              <span style={{ fontSize: "0.875rem", fontWeight: 700, color: "var(--gray-800)" }}>
                {isAdmin
                  ? `Toàn bộ Danh mục Văn bản Khớp Từ khóa & Bộ lọc Phân loại (${searchResponse.total_hits} tài liệu)`
                  : `Danh sách tất cả văn bản phù hợp (${searchResponse.total_hits} tài liệu)`}
              </span>
            </div>
          )}

          {/* Results Summary Bar */}
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", fontSize: "0.875rem", color: "var(--gray-600)" }}>
            <div>
              {searchResponse.query ? (
                <>
                  Tìm thấy <strong style={{ color: "var(--gray-900)" }}>{searchResponse.total_hits}</strong> kết quả cho từ khóa "<strong>{searchResponse.query}</strong>" {isAdmin && `(${searchResponse.took_ms} ms)`}
                </>
              ) : (
                <>
                  Hiển thị <strong style={{ color: "var(--gray-900)" }}>{searchResponse.total_hits}</strong> văn bản và hồ sơ CTSV mới nhất {isAdmin && `(${searchResponse.took_ms} ms)`}
                </>
              )}
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
                <Card key={hit.document_id} padding="md" hoverable style={{ border: "1px solid var(--gray-200)", borderRadius: "var(--radius-lg)" }}>
                  {/* 1. Card Top Bar: Badges + Relevance Score + Quick View */}
                  <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "0.5rem", flexWrap: "wrap", gap: "0.5rem" }}>
                    <div style={{ display: "flex", alignItems: "center", gap: "0.45rem", flexWrap: "wrap" }}>
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
                          Mới OCR trang 1
                        </span>
                      )}
                    </div>

                    <div style={{ display: "flex", alignItems: "center", gap: "0.75rem" }}>
                      {isAdmin && (
                        <span style={{ fontSize: "0.75rem", color: "var(--gray-400)" }}>
                          Độ phù hợp: <strong style={{ color: "var(--gray-600)" }}>{hit.score}</strong>
                        </span>
                      )}
                      <Link to={`/documents/${hit.document_id}`}>
                        <Button variant="outline" size="sm" rightIcon={<ArrowRight size={13} />} style={{ fontSize: "0.75rem", padding: "0.25rem 0.65rem", height: "28px" }}>
                          Xem chi tiết
                        </Button>
                      </Link>
                    </div>
                  </div>

                  {/* 2. Document Title (Full Width) */}
                  <h3 style={{ fontSize: "1.05rem", fontWeight: 700, color: "var(--gray-900)", lineHeight: 1.4, margin: "0.2rem 0" }}>
                    <Link to={`/documents/${hit.document_id}`} style={{ color: "var(--primary-700)", textDecoration: "none" }}>
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

                  {/* 3. Metadata row */}
                  <div style={{ display: "flex", gap: "1.25rem", marginTop: "0.35rem", fontSize: "0.8125rem", color: "var(--gray-600)", flexWrap: "wrap", alignItems: "center" }}>
                    {hit.student_name && (
                      <span style={{ display: "flex", alignItems: "center", gap: "0.35rem" }}>
                        <User size={14} style={{ color: "var(--gray-400)" }} /> Sinh viên: <strong>{hit.student_name}</strong>
                      </span>
                    )}
                    {hit.student_id && (
                      <span style={{ display: "flex", alignItems: "center", gap: "0.35rem" }}>
                        <GraduationCap size={14} style={{ color: "var(--gray-400)" }} /> MSSV: <strong style={{ color: "var(--gray-800)" }}>{hit.student_id}</strong>
                      </span>
                    )}
                    <span style={{ display: "flex", alignItems: "center", gap: "0.35rem" }}>
                      <User size={14} style={{ color: "#2563eb" }} /> Người upload: <strong style={{ color: "#1e3a8a" }}>{hit.uploader_name || "Cán bộ CTSV"}</strong>
                    </span>
                    {hit.created_at && (
                      <span style={{ display: "flex", alignItems: "center", gap: "0.35rem" }}>
                        <Calendar size={14} style={{ color: "var(--gray-400)" }} /> {new Date(hit.created_at).toLocaleDateString("vi-VN")}
                      </span>
                    )}
                  </div>

                  {/* 4. Snippet Highlight (if available) */}
                  {hit.content_snippet && (
                    <div
                      style={{
                        marginTop: "0.65rem",
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

                  {/* 5. Card Bottom Action Bar: Dedicated, balanced, grouped actions (Chỉ hiển thị cho Admin) */}
                  {isAdmin && (
                    <div
                    style={{
                      display: "flex",
                      alignItems: "center",
                      justifyContent: "space-between",
                      marginTop: "0.85rem",
                      paddingTop: "0.75rem",
                      borderTop: "1px solid var(--gray-100)",
                      flexWrap: "wrap",
                      gap: "0.5rem",
                    }}
                  >
                    <div style={{ display: "flex", alignItems: "center", gap: "0.4rem", flexWrap: "wrap" }}>
                      <span style={{ fontSize: "0.7rem", fontWeight: 700, color: "var(--gray-400)", textTransform: "uppercase", letterSpacing: "0.03em", marginRight: "0.2rem" }}>
                        Công cụ ES 8:
                      </span>
                      <Button
                        type="button"
                        variant="outline"
                        size="sm"
                        leftIcon={<GitBranch size={13} color="#4f46e5" />}
                        onClick={() => handleOpenPercolateRouting(hit)}
                        style={{ fontSize: "0.75rem", padding: "0.25rem 0.6rem", borderColor: "#c7d2fe", color: "#3730a3", backgroundColor: "#eef2ff", height: "30px" }}
                        title="Đánh giá so khớp tự động với tập luật Percolator chính sách CTSV"
                      >
                        Phân luồng Percolator
                      </Button>
                      <Button
                        type="button"
                        variant="outline"
                        size="sm"
                        leftIcon={<Scan size={13} color="#0284c7" />}
                        onClick={() => handleOpenSpatialHighlights(hit)}
                        style={{ fontSize: "0.75rem", padding: "0.25rem 0.6rem", borderColor: "#bae6fd", color: "#0369a1", backgroundColor: "#f0f9ff", height: "30px" }}
                        title="Xem tọa độ Bounding Box của từ khóa trên văn bản scan gốc"
                      >
                        Tọa độ Scan OCR
                      </Button>
                      <Button
                        type="button"
                        variant="outline"
                        size="sm"
                        leftIcon={<CopyCheck size={13} color="#be123c" />}
                        onClick={() => handleOpenDuplicateCheck(hit)}
                        style={{ fontSize: "0.75rem", padding: "0.25rem 0.6rem", borderColor: "#fecdd3", color: "#9f1239", backgroundColor: "#fff1f2", height: "30px" }}
                        title="So soát trùng lặp văn bản bằng Elasticsearch More-Like-This"
                      >
                        Trùng lặp MLT
                      </Button>
                      <Button
                        type="button"
                        variant="outline"
                        size="sm"
                        leftIcon={<Tag size={13} color="#059669" />}
                        onClick={() => handleOpenAutoTags(hit)}
                        style={{ fontSize: "0.75rem", padding: "0.25rem 0.6rem", borderColor: "#a7f3d0", color: "#065f46", backgroundColor: "#ecfdf5", height: "30px" }}
                        title="Tự động trích xuất thẻ nhãn chính sách & thực thể bằng significant_text"
                      >
                        Gán nhãn Tags
                      </Button>
                      <Button
                        type="button"
                        variant="outline"
                        size="sm"
                        leftIcon={<History size={13} color="#7c3aed" />}
                        onClick={() => handleOpenAuditTrail(hit)}
                        style={{ fontSize: "0.75rem", padding: "0.25rem 0.6rem", borderColor: "#ddd6fe", color: "#5b21b6", backgroundColor: "#f5f3ff", height: "30px" }}
                        title="Xem lịch sử kiểm toán phiên bản & so sánh Diffs sửa đổi"
                      >
                        Nhật ký Diffs
                      </Button>
                    </div>

                    <div style={{ display: "flex", alignItems: "center", gap: "0.4rem", flexWrap: "wrap" }}>
                      <Button
                        type="button"
                        variant="outline"
                        size="sm"
                        leftIcon={<FileCheck size={13} color="#059669" />}
                        onClick={() => handleOpenPolicyAudit(hit, "NGHI_DINH_81")}
                        style={{ fontSize: "0.75rem", padding: "0.25rem 0.6rem", borderColor: "#a7f3d0", color: "#065f46", backgroundColor: "#f0fdf4", height: "30px" }}
                        title="Đối soát tự động điều kiện theo Nghị định 81, Học bổng KKHT..."
                      >
                        Thẩm định NĐ 81
                      </Button>
                      <Button
                        type="button"
                        variant="outline"
                        size="sm"
                        leftIcon={<ShieldCheck size={13} color="#d97706" />}
                        onClick={() => handleOpenFraudAudit(hit)}
                        style={{ fontSize: "0.75rem", padding: "0.25rem 0.6rem", borderColor: "#fde68a", color: "#92400e", backgroundColor: "#fffbeb", height: "30px" }}
                        title="Quét trùng lặp số hiệu sổ hộ nghèo, biên lai, tái sử dụng hồ sơ..."
                      >
                        Đối soát Gian lận
                      </Button>
                    </div>
                  </div>
                  )}
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
      </>
      )}

      {/* ==================================================================== */}
      {/* FEATURE 1 TAB: TRỢ LÝ HỎI ĐÁP QUY CHẾ CTSV (NLP FAQ)                */}
      {/* ==================================================================== */}
      {activeTab === "faq" && (
        <div style={{ display: "flex", flexDirection: "column", gap: "1.25rem" }}>
          {/* Banner Card */}
          <Card
            padding="lg"
            style={{
              backgroundColor: "#0e1e33",
              border: "1px solid #1e3a8a",
              color: "#ffffff",
              borderRadius: "var(--radius-lg)",
            }}
          >
            <div style={{ maxWidth: "800px" }}>
              <div style={{ display: "inline-flex", alignItems: "center", gap: "0.5rem", padding: "0.25rem 0.75rem", borderRadius: "9999px", backgroundColor: "rgba(255,255,255,0.1)", fontSize: "0.75rem", fontWeight: 600, marginBottom: "0.75rem", color: "#93c5fd" }}>
                <HelpCircle size={14} color="#60a5fa" />
                HỖ TRỢ PHÁP QUY & QUY CHẾ CTSV ĐẠI HỌC ĐÀ LẠT
              </div>
              <h2 style={{ fontSize: "1.4rem", fontWeight: 700, marginBottom: "0.5rem" }}>
                Tra cứu Quy chế & Thủ tục Hành chính
              </h2>
              <p style={{ fontSize: "0.875rem", color: "#94a3b8", lineHeight: 1.6, marginBottom: "1.25rem" }}>
                Đặt câu hỏi về điều kiện xét học bổng, chính sách miễn giảm học phí theo Nghị định 81, điểm rèn luyện hoặc thủ tục tạm hoãn nghĩa vụ quân sự. Hệ thống tự động trích dẫn chính xác Điều/Khoản và cung cấp biểu mẫu hành chính tương ứng.
              </p>

              {/* Input Form */}
              <form
                onSubmit={(e) => {
                  e.preventDefault();
                  handleAskFaq(faqInput);
                }}
                style={{ display: "flex", gap: "0.5rem" }}
              >
                <input
                  type="text"
                  value={faqInput}
                  onChange={(e) => setFaqInput(e.target.value)}
                  placeholder="Nhập câu hỏi (vd: Bị điểm F thể dục có được xét học bổng không?)..."
                  style={{
                    flex: 1,
                    padding: "0.75rem 1rem",
                    borderRadius: "var(--radius-md)",
                    border: "none",
                    outline: "none",
                    fontSize: "0.9375rem",
                    fontWeight: 500,
                    color: "var(--gray-900)",
                    backgroundColor: "#ffffff",
                  }}
                />
                <Button
                  type="submit"
                  variant="primary"
                  isLoading={isFaqLoading}
                  leftIcon={<Search size={16} />}
                  style={{ backgroundColor: "#1e40af", color: "#ffffff", fontWeight: 600, border: "none" }}
                >
                  Tra cứu Quy chế
                </Button>
              </form>
            </div>

            {/* Quick Questions Prompts */}
            <div style={{ marginTop: "1.25rem", borderTop: "1px solid rgba(255,255,255,0.15)", paddingTop: "1rem" }}>
              <span style={{ fontSize: "0.75rem", color: "#a5b4fc", fontWeight: 600, display: "block", marginBottom: "0.5rem" }}>
                CÂU HỎI THƯỜNG GẶP CỦA SINH VIÊN (BẤM ĐỂ HỎI NHANH):
              </span>
              <div style={{ display: "flex", flexWrap: "wrap", gap: "0.5rem" }}>
                {[
                  "Bị điểm F môn thể dục có được xét học bổng không?",
                  "Hồ sơ miễn giảm học phí cho sinh viên hộ nghèo gồm giấy tờ gì?",
                  "Điểm rèn luyện bao nhiêu thì được loại Tốt và Xuất sắc?",
                  "Xin giấy xác nhận sinh viên tạm hoãn nghĩa vụ quân sự ở đâu?",
                  "Đối tượng sinh viên nào được ưu tiên ở Ký túc xá?",
                ].map((qText) => (
                  <button
                    key={qText}
                    type="button"
                    onClick={() => {
                      setFaqInput(qText);
                      handleAskFaq(qText);
                    }}
                    style={{
                      padding: "0.35rem 0.75rem",
                      borderRadius: "9999px",
                      backgroundColor: "rgba(255, 255, 255, 0.12)",
                      border: "1px solid rgba(255, 255, 255, 0.2)",
                      color: "#ffffff",
                      fontSize: "0.8125rem",
                      cursor: "pointer",
                      transition: "all 0.15s ease",
                    }}
                    onMouseEnter={(e) => (e.currentTarget.style.backgroundColor = "rgba(255, 255, 255, 0.25)")}
                    onMouseLeave={(e) => (e.currentTarget.style.backgroundColor = "rgba(255, 255, 255, 0.12)")}
                  >
                    {qText}
                  </button>
                ))}
              </div>
            </div>
          </Card>

          {/* Answer Card */}
          {faqData && (
            <Card padding="lg" style={{ borderLeft: "4px solid var(--primary-600)" }}>
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", gap: "1rem", flexWrap: "wrap", marginBottom: "0.75rem" }}>
                <div>
                  <span style={{ fontSize: "0.75rem", fontWeight: 700, color: "var(--primary-700)", textTransform: "uppercase", letterSpacing: "0.05em" }}>
                    Căn cứ pháp lý: {faqData.matched_article}
                  </span>
                  <h3 style={{ fontSize: "1.25rem", fontWeight: 800, color: "var(--gray-900)", marginTop: "0.25rem" }}>
                    {faqData.regulation_title}
                  </h3>
                </div>
                <div style={{ display: "inline-flex", alignItems: "center", gap: "0.4rem", padding: "0.3rem 0.7rem", borderRadius: "9999px", backgroundColor: "#ecfdf5", color: "#065f46", fontSize: "0.75rem", fontWeight: 700 }}>
                  <CheckCircle2 size={14} /> Độ tin cậy: {Math.round(faqData.confidence_score * 100)}%
                </div>
              </div>

              {/* Tóm tắt câu trả lời */}
              <div style={{ backgroundColor: "#f0fdf4", border: "1px solid #bbf7d0", borderRadius: "var(--radius-md)", padding: "1rem", marginBottom: "1rem" }}>
                <div style={{ fontSize: "0.75rem", fontWeight: 700, color: "#166534", marginBottom: "0.35rem" }}>
                  TÓM TẮT TRẢ LỜI CHO SINH VIÊN:
                </div>
                <p style={{ fontSize: "0.9375rem", color: "#14532d", fontWeight: 600, lineHeight: 1.6 }}>
                  {faqData.summary_answer}
                </p>
              </div>

              {/* Trích dẫn chi tiết */}
              <div style={{ backgroundColor: "var(--gray-50)", borderRadius: "var(--radius-md)", padding: "1rem", marginBottom: "1.25rem" }}>
                <div style={{ fontSize: "0.75rem", fontWeight: 700, color: "var(--gray-600)", marginBottom: "0.35rem" }}>
                  NỘI DUNG QUY ĐỊNH CHI TIẾT:
                </div>
                <p style={{ fontSize: "0.875rem", color: "var(--gray-700)", lineHeight: 1.7, whiteSpace: "pre-line" }}>
                  {faqData.detail_content}
                </p>
              </div>

              {/* Biểu mẫu đính kèm */}
              {faqData.required_forms && faqData.required_forms.length > 0 && (
                <div style={{ marginTop: "1rem" }}>
                  <div style={{ fontSize: "0.8125rem", fontWeight: 700, color: "var(--gray-800)", marginBottom: "0.6rem" }}>
                    BIỂU MẪU HÀNH CHÍNH LIÊN QUAN (TẢI VỀ NỘP PHÒNG CTSV):
                  </div>
                  <div style={{ display: "flex", flexDirection: "column", gap: "0.5rem" }}>
                    {faqData.required_forms.map((f) => (
                      <div
                        key={f.form_code}
                        style={{
                          display: "flex",
                          justifyContent: "space-between",
                          alignItems: "center",
                          padding: "0.75rem 1rem",
                          borderRadius: "var(--radius-md)",
                          backgroundColor: "#ffffff",
                          border: "1px solid var(--border-color)",
                          boxShadow: "0 1px 3px rgba(0,0,0,0.05)",
                        }}
                      >
                        <div style={{ display: "flex", alignItems: "center", gap: "0.75rem" }}>
                          <div style={{ width: "36px", height: "36px", borderRadius: "8px", backgroundColor: "var(--primary-50)", display: "flex", alignItems: "center", justifyContent: "center" }}>
                            <FileText size={18} color="var(--primary-600)" />
                          </div>
                          <div>
                            <span style={{ fontSize: "0.75rem", fontWeight: 700, color: "var(--primary-700)" }}>
                              {f.form_code}
                            </span>
                            <div style={{ fontSize: "0.875rem", fontWeight: 600, color: "var(--gray-900)" }}>
                              {f.form_name}
                            </div>
                            {f.guide && (
                              <div style={{ fontSize: "0.75rem", color: "var(--gray-500)", marginTop: "0.15rem" }}>
                                {f.guide}
                              </div>
                            )}
                          </div>
                        </div>

                        <a
                          href={f.download_url}
                          target="_blank"
                          rel="noopener noreferrer"
                          style={{ textDecoration: "none" }}
                        >
                          <Button variant="outline" size="sm" leftIcon={<Download size={14} />}>
                            Tải biểu mẫu
                          </Button>
                        </a>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Điều khoản liên quan */}
              {faqData.related_articles && faqData.related_articles.length > 0 && (
                <div style={{ marginTop: "1rem", paddingTop: "0.75rem", borderTop: "1px solid var(--gray-200)", display: "flex", gap: "0.5rem", alignItems: "center", flexWrap: "wrap" }}>
                  <span style={{ fontSize: "0.75rem", fontWeight: 600, color: "var(--gray-500)" }}>Điều khoản liên quan:</span>
                  {faqData.related_articles.map((art, idx) => (
                    <span key={idx} style={{ fontSize: "0.75rem", backgroundColor: "var(--gray-100)", color: "var(--gray-700)", padding: "0.2rem 0.5rem", borderRadius: "4px" }}>
                      {art}
                    </span>
                  ))}
                </div>
              )}
            </Card>
          )}
        </div>
      )}

      {/* ==================================================================== */}
      {/* TAB 5: BÁO CÁO ĐA CHIỀU CTSV (MULTI-LEVEL AGGREGATIONS)              */}
      {/* ==================================================================== */}
      {activeTab === "ctsv_analytics" && (
        <div style={{ display: "flex", flexDirection: "column", gap: "1.25rem" }}>
          {/* Header & Refresh */}
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", flexWrap: "wrap", gap: "0.75rem" }}>
            <div>
              <h3 style={{ fontSize: "1.15rem", fontWeight: 800, color: "var(--gray-900)" }}>
                Thống kê Đa chiều CTSV Toàn trường (Multi-level Aggregations)
              </h3>
              <p style={{ fontSize: "0.8125rem", color: "var(--gray-500)", marginTop: "0.2rem" }}>
                Khai phá dữ liệu tổng hợp đa tầng của Elasticsearch 8: Phân tích cơ cấu chính sách, phân bổ hồ sơ theo từng Khoa, tiến độ phê duyệt hồ sơ và cam kết chất lượng SLA.
              </p>
            </div>
            <div style={{ display: "flex", alignItems: "center", gap: "0.5rem" }}>
              <Button
                type="button"
                variant="outline"
                size="sm"
                leftIcon={<RotateCcw size={14} className={isBreakdownLoading ? "animate-spin" : ""} />}
                onClick={() => handleLoadCtsvBreakdown()}
                disabled={isBreakdownLoading}
              >
                Làm mới dữ liệu Aggs
              </Button>
            </div>
          </div>

          {isBreakdownLoading && !ctsvBreakdown ? (
            <Card padding="lg">
              <div style={{ padding: "3rem", textAlign: "center", color: "var(--gray-500)" }}>
                <Clock className="animate-spin" size={32} style={{ margin: "0 auto 0.75rem", color: "var(--primary-600)" }} />
                <span>Đang thực thi các câu truy vấn Aggregations đa tầng trên Elasticsearch 8...</span>
              </div>
            </Card>
          ) : ctsvBreakdown ? (
            <>
              {/* 4 KPI Summary Cards */}
              <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))", gap: "1rem" }}>
                <Card padding="md" style={{ borderLeft: "4px solid var(--primary-600)", backgroundColor: "#f8fafc" }}>
                  <span style={{ fontSize: "0.75rem", fontWeight: 700, color: "var(--gray-500)", textTransform: "uppercase" }}>Tổng Hồ sơ Chính sách</span>
                  <div style={{ fontSize: "1.75rem", fontWeight: 800, color: "var(--primary-700)", marginTop: "0.25rem" }}>
                    {ctsvBreakdown.total_student_documents.toLocaleString()}
                  </div>
                  <span style={{ fontSize: "0.75rem", color: "var(--gray-600)" }}>Toàn bộ đơn từ scan đã lập chỉ mục</span>
                </Card>

                <Card padding="md" style={{ borderLeft: "4px solid #16a34a", backgroundColor: "#f8fafc" }}>
                  <span style={{ fontSize: "0.75rem", fontWeight: 700, color: "var(--gray-500)", textTransform: "uppercase" }}>Sinh viên Thụ hưởng</span>
                  <div style={{ fontSize: "1.75rem", fontWeight: 800, color: "#16a34a", marginTop: "0.25rem" }}>
                    {ctsvBreakdown.total_active_students.toLocaleString()}
                  </div>
                  <span style={{ fontSize: "0.75rem", color: "var(--gray-600)" }}>Sinh viên diện chính sách / học bổng</span>
                </Card>

                <Card padding="md" style={{ borderLeft: "4px solid #d97706", backgroundColor: "#f8fafc" }}>
                  <span style={{ fontSize: "0.75rem", fontWeight: 700, color: "var(--gray-500)", textTransform: "uppercase" }}>Tỷ lệ Đã Phê duyệt</span>
                  <div style={{ fontSize: "1.75rem", fontWeight: 800, color: "#b45309", marginTop: "0.25rem" }}>
                    {ctsvBreakdown.total_student_documents > 0
                      ? `${Math.round((ctsvBreakdown.faculty_breakdown.reduce((acc, f) => acc + f.approved_count, 0) / Math.max(ctsvBreakdown.total_student_documents, 1)) * 100)}%`
                      : "100%"}
                  </div>
                  <span style={{ fontSize: "0.75rem", color: "var(--gray-600)" }}>Tiến độ thẩm định chính sách toàn trường</span>
                </Card>

                <Card padding="md" style={{ borderLeft: "4px solid #0284c7", backgroundColor: "#f8fafc" }}>
                  <span style={{ fontSize: "0.75rem", fontWeight: 700, color: "var(--gray-500)", textTransform: "uppercase" }}>Thời gian Xử lý Trung bình</span>
                  <div style={{ fontSize: "1.75rem", fontWeight: 800, color: "#0284c7", marginTop: "0.25rem" }}>
                    {ctsvBreakdown.avg_processing_sla_days} ngày
                  </div>
                  <span style={{ fontSize: "0.75rem", color: "#16a34a", fontWeight: 600 }}>Đạt chuẩn SLA (&lt; 3.0 ngày)</span>
                </Card>
              </div>

              {/* Main Grid: Faculty Breakdown & Policy Distribution */}
              <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(360px, 1fr))", gap: "1rem" }}>
                {/* Faculty Breakdown Table */}
                <Card padding="md" style={{ gridColumn: "span 1" }}>
                  <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "0.75rem" }}>
                    <h4 style={{ fontSize: "0.9375rem", fontWeight: 700, color: "var(--gray-900)", display: "flex", alignItems: "center", gap: "0.4rem" }}>
                      <Building2 size={16} color="var(--primary-600)" />
                      Phân bổ Hồ sơ theo Khoa Chuyên môn
                    </h4>
                    <span style={{ fontSize: "0.75rem", color: "var(--gray-500)" }}>
                      {ctsvBreakdown.faculty_breakdown.length} Khoa
                    </span>
                  </div>

                  <div style={{ overflowX: "auto" }}>
                    <table style={{ width: "100%", borderCollapse: "collapse", fontSize: "0.8125rem" }}>
                      <thead>
                        <tr style={{ backgroundColor: "var(--gray-50)", borderBottom: "1px solid var(--border-color)", textAlign: "left" }}>
                          <th style={{ padding: "0.5rem 0.6rem", color: "var(--gray-700)" }}>Khoa</th>
                          <th style={{ padding: "0.5rem 0.6rem", color: "var(--gray-700)", textAlign: "center" }}>Tổng đơn</th>
                          <th style={{ padding: "0.5rem 0.6rem", color: "var(--gray-700)", textAlign: "center" }}>Đã duyệt</th>
                          <th style={{ padding: "0.5rem 0.6rem", color: "var(--gray-700)", textAlign: "center" }}>Chờ duyệt</th>
                          <th style={{ padding: "0.5rem 0.6rem", color: "var(--gray-700)", textAlign: "right" }}>Tỷ lệ duyệt</th>
                        </tr>
                      </thead>
                      <tbody>
                        {ctsvBreakdown.faculty_breakdown.map((f, idx) => {
                          const rate = Math.round((f.approved_count / f.total_applications) * 100);
                          return (
                            <tr key={idx} style={{ borderBottom: "1px solid var(--gray-100)" }}>
                              <td style={{ padding: "0.55rem 0.6rem" }}>
                                <div style={{ fontWeight: 600, color: "var(--gray-900)" }}>{f.faculty_name}</div>
                                <div style={{ width: "100%", backgroundColor: "var(--gray-100)", height: "4px", borderRadius: "2px", marginTop: "3px" }}>
                                  <div style={{ width: `${rate}%`, backgroundColor: rate >= 80 ? "#16a34a" : "#d97706", height: "100%", borderRadius: "2px" }} />
                                </div>
                              </td>
                              <td style={{ padding: "0.55rem 0.6rem", textAlign: "center", fontWeight: 700 }}>{f.total_applications}</td>
                              <td style={{ padding: "0.55rem 0.6rem", textAlign: "center", color: "#16a34a", fontWeight: 700 }}>{f.approved_count}</td>
                              <td style={{ padding: "0.55rem 0.6rem", textAlign: "center", color: "#d97706" }}>{f.pending_count}</td>
                              <td style={{ padding: "0.55rem 0.6rem", textAlign: "right" }}>
                                <span style={{
                                  fontSize: "0.75rem",
                                  fontWeight: 700,
                                  backgroundColor: rate >= 80 ? "#dcfce7" : "#fef3c7",
                                  color: rate >= 80 ? "#16a34a" : "#d97706",
                                  padding: "0.15rem 0.45rem",
                                  borderRadius: "9999px"
                                }}>
                                  {rate}%
                                </span>
                              </td>
                            </tr>
                          );
                        })}
                      </tbody>
                    </table>
                  </div>
                </Card>

                {/* Policy Distribution & Monthly Trend */}
                <div style={{ display: "flex", flexDirection: "column", gap: "1rem" }}>
                  <Card padding="md">
                    <h4 style={{ fontSize: "0.9375rem", fontWeight: 700, color: "var(--gray-900)", marginBottom: "0.75rem", display: "flex", alignItems: "center", gap: "0.4rem" }}>
                      <Layers size={16} color="#d97706" />
                      Cơ cấu Danh mục Chính sách Sinh viên
                    </h4>
                    <div style={{ display: "flex", flexDirection: "column", gap: "0.6rem" }}>
                      {ctsvBreakdown.policy_distribution.map((pol, idx) => (
                        <div key={idx} style={{ padding: "0.55rem 0.75rem", borderRadius: "var(--radius-sm)", backgroundColor: "var(--gray-50)", border: "1px solid var(--gray-200)" }}>
                          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                            <span style={{ fontSize: "0.8125rem", fontWeight: 600, color: "var(--gray-900)" }}>{pol.policy_name}</span>
                            <span style={{ fontSize: "0.75rem", fontWeight: 800, color: "var(--primary-700)" }}>{pol.percentage}%</span>
                          </div>
                          <div style={{ width: "100%", backgroundColor: "var(--gray-200)", height: "6px", borderRadius: "3px", marginTop: "4px" }}>
                            <div style={{ width: `${pol.percentage}%`, backgroundColor: idx === 0 ? "var(--primary-600)" : idx === 1 ? "#16a34a" : idx === 2 ? "#d97706" : "#0284c7", height: "100%", borderRadius: "3px" }} />
                          </div>
                          <div style={{ fontSize: "0.6875rem", color: "var(--gray-500)", marginTop: "3px", textAlign: "right" }}>
                            {pol.count} hồ sơ thụ hưởng
                          </div>
                        </div>
                      ))}
                    </div>
                  </Card>

                  {/* Monthly Application Trend */}
                  <Card padding="md">
                    <h4 style={{ fontSize: "0.9375rem", fontWeight: 700, color: "var(--gray-900)", marginBottom: "0.75rem", display: "flex", alignItems: "center", gap: "0.4rem" }}>
                      <TrendingUp size={16} color="#16a34a" />
                      Tiến độ Nộp Hồ sơ Theo Tháng (Date Histogram)
                    </h4>
                    <div style={{ display: "grid", gridTemplateColumns: `repeat(${ctsvBreakdown.monthly_application_trend.length}, 1fr)`, gap: "0.5rem", alignItems: "flex-end", height: "130px", paddingTop: "1rem" }}>
                      {ctsvBreakdown.monthly_application_trend.map((m, idx) => {
                        const maxVal = Math.max(...ctsvBreakdown.monthly_application_trend.map((item) => item.applications));
                        const heightPct = Math.round((m.applications / maxVal) * 100);
                        return (
                          <div key={idx} style={{ display: "flex", flexDirection: "column", alignItems: "center", height: "100%", justifyContent: "flex-end" }}>
                            <span style={{ fontSize: "0.6875rem", fontWeight: 700, color: "var(--primary-700)", marginBottom: "2px" }}>{m.applications}</span>
                            <div
                              style={{
                                width: "70%",
                                height: `${heightPct}%`,
                                backgroundColor: "var(--primary-500)",
                                borderRadius: "4px 4px 0 0",
                                transition: "height 0.3s ease",
                              }}
                              title={`${m.month}: ${m.applications} đơn (${m.approved} đã duyệt)`}
                            />
                            <span style={{ fontSize: "0.625rem", color: "var(--gray-500)", marginTop: "4px" }}>{m.month.slice(5)}</span>
                          </div>
                        );
                      })}
                    </div>
                  </Card>
                </div>
              </div>
            </>
          ) : null}
        </div>
      )}



      {/* ==================================================================== */}
      {/* MODAL 1: THẨM ĐỊNH CHÍNH SÁCH TỰ ĐỘNG (POLICY AUTO-AUDIT)            */}
      {/* ==================================================================== */}
      {policyModalDoc && (
        <div
          style={{
            position: "fixed",
            inset: 0,
            backgroundColor: "rgba(0, 0, 0, 0.55)",
            backdropFilter: "blur(3px)",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            zIndex: 100,
            padding: "1rem",
          }}
          onClick={() => setPolicyModalDoc(null)}
        >
          <div
            style={{
              backgroundColor: "#ffffff",
              borderRadius: "var(--radius-lg)",
              maxWidth: "750px",
              width: "100%",
              maxHeight: "90vh",
              overflowY: "auto",
              boxShadow: "0 25px 50px -12px rgba(0, 0, 0, 0.25)",
              padding: "1.5rem",
            }}
            onClick={(e) => e.stopPropagation()}
          >
            {/* Modal Header */}
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: "1rem" }}>
              <div>
                <span style={{ fontSize: "0.75rem", fontWeight: 700, color: "var(--primary-600)", textTransform: "uppercase" }}>
                  ĐỐI SOÁT & THẨM ĐỊNH ĐIỀU KIỆN PHÁP LÝ TỰ ĐỘNG
                </span>
                <h3 style={{ fontSize: "1.25rem", fontWeight: 800, color: "var(--gray-900)", marginTop: "0.2rem" }}>
                  {formatDisplayTitle(policyModalDoc.title).mainTitle}
                </h3>
                <span style={{ fontSize: "0.75rem", color: "var(--gray-500)" }}>
                  MSSV: {policyModalDoc.student_id || "N/A"} | Sinh viên: {policyModalDoc.student_name || "N/A"}
                </span>
              </div>
              <button
                type="button"
                onClick={() => setPolicyModalDoc(null)}
                style={{ border: "none", background: "none", cursor: "pointer", padding: "0.25rem" }}
              >
                <X size={20} color="var(--gray-400)" />
              </button>
            </div>

            {/* Policy Selector */}
            <div style={{ display: "flex", gap: "0.5rem", marginBottom: "1.25rem", flexWrap: "wrap" }}>
              {[
                { code: "NGHI_DINH_81", label: "Nghị định 81/2021 (Miễn giảm học phí)" },
                { code: "HOC_BONG_KKHT", label: "Quy chế Học bổng KKHT (QĐ 688)" },
                { code: "TRO_CAP_XAH_HOI", label: "Trợ cấp Xã hội (QĐ 1121)" },
              ].map((p) => (
                <button
                  key={p.code}
                  type="button"
                  onClick={() => handleOpenPolicyAudit(policyModalDoc, p.code)}
                  style={{
                    padding: "0.4rem 0.8rem",
                    borderRadius: "9999px",
                    fontSize: "0.75rem",
                    fontWeight: policyCode === p.code ? 700 : 500,
                    backgroundColor: policyCode === p.code ? "var(--primary-600)" : "var(--gray-100)",
                    color: policyCode === p.code ? "#ffffff" : "var(--gray-700)",
                    border: "none",
                    cursor: "pointer",
                  }}
                >
                  {p.label}
                </button>
              ))}
            </div>

            {/* Audit Content */}
            {isAuditingPolicy ? (
              <div style={{ padding: "3rem", textAlign: "center", color: "var(--gray-500)" }}>
                <Clock className="animate-spin" size={28} style={{ margin: "0 auto 0.5rem" }} />
                <span>Đang phân tích OCR và đối chiếu quy chế...</span>
              </div>
            ) : policyAuditData ? (
              <div style={{ display: "flex", flexDirection: "column", gap: "1rem" }}>
                {/* Overall Status Banner */}
                <div
                  style={{
                    padding: "1rem",
                    borderRadius: "var(--radius-md)",
                    backgroundColor: policyAuditData.status === "ELIGIBLE" ? "#f0fdf4" : policyAuditData.status === "INCOMPLETE" ? "#fffbeb" : "#fef2f2",
                    border: `1px solid ${policyAuditData.status === "ELIGIBLE" ? "#bbf7d0" : policyAuditData.status === "INCOMPLETE" ? "#fde68a" : "#fecaca"}`,
                    display: "flex",
                    alignItems: "center",
                    gap: "1rem",
                  }}
                >
                  {policyAuditData.status === "ELIGIBLE" ? (
                    <CheckCircle2 size={32} color="#16a34a" />
                  ) : policyAuditData.status === "INCOMPLETE" ? (
                    <AlertTriangle size={32} color="#d97706" />
                  ) : (
                    <AlertOctagon size={32} color="#dc2626" />
                  )}
                  <div>
                    <span style={{ fontSize: "0.75rem", fontWeight: 700, textTransform: "uppercase", color: policyAuditData.status === "ELIGIBLE" ? "#166534" : policyAuditData.status === "INCOMPLETE" ? "#92400e" : "#991b1b" }}>
                      KẾT QUẢ THẨM ĐỊNH TỰ ĐỘNG
                    </span>
                    <div style={{ fontSize: "1.1rem", fontWeight: 800, color: policyAuditData.status === "ELIGIBLE" ? "#15803d" : policyAuditData.status === "INCOMPLETE" ? "#b45309" : "#b91c1c" }}>
                      {policyAuditData.status === "ELIGIBLE" ? "HỒ SƠ HỢP LỆ — ĐỦ ĐIỀU KIỆN PHÊ DUYỆT" : policyAuditData.status === "INCOMPLETE" ? "HỒ SƠ CẦN BỔ SUNG MINH CHỨNG" : "HỒ SƠ KHÔNG ĐỦ ĐIỀU KIỆN"}
                    </div>
                    <p style={{ fontSize: "0.8125rem", color: "var(--gray-700)", marginTop: "0.2rem" }}>
                      {policyAuditData.recommendation}
                    </p>
                  </div>
                </div>

                {/* Criteria Checks Checklist */}
                <div>
                  <span style={{ fontSize: "0.75rem", fontWeight: 700, color: "var(--gray-700)", textTransform: "uppercase", display: "block", marginBottom: "0.5rem" }}>
                    CÁC TIÊU CHÍ PHÁP LÝ ĐÃ KIỂM TRA ({policyAuditData.criteria_checks.filter(c => c.passed).length}/{policyAuditData.criteria_checks.length} ĐẠT):
                  </span>
                  <div style={{ display: "flex", flexDirection: "column", gap: "0.5rem" }}>
                    {policyAuditData.criteria_checks.map((crit) => (
                      <div
                        key={crit.rule_code}
                        style={{
                          padding: "0.75rem",
                          borderRadius: "var(--radius-sm)",
                          backgroundColor: crit.passed ? "#f8fafc" : "#fff1f2",
                          border: `1px solid ${crit.passed ? "#e2e8f0" : "#fecdd3"}`,
                          display: "flex",
                          alignItems: "flex-start",
                          gap: "0.75rem",
                        }}
                      >
                        {crit.passed ? <CheckCircle2 size={18} color="#16a34a" style={{ marginTop: "2px", flexShrink: 0 }} /> : <AlertOctagon size={18} color="#e11d48" style={{ marginTop: "2px", flexShrink: 0 }} />}
                        <div style={{ flex: 1 }}>
                          <div style={{ display: "flex", justifyContent: "space-between" }}>
                            <strong style={{ fontSize: "0.8125rem", color: "var(--gray-900)" }}>{crit.title}</strong>
                            <span style={{ fontSize: "0.6875rem", fontWeight: 700, color: crit.passed ? "#16a34a" : "#e11d48" }}>
                              {crit.passed ? "ĐẠT CHUẨN" : "CHƯA ĐẠT"}
                            </span>
                          </div>
                          <p style={{ fontSize: "0.75rem", color: "var(--gray-600)", marginTop: "0.2rem" }}>
                            {crit.detail}
                          </p>
                          {crit.evidence_snippet && (
                            <div style={{ marginTop: "0.3rem", fontSize: "0.6875rem", color: "var(--primary-700)", backgroundColor: "rgba(99, 102, 241, 0.08)", padding: "0.2rem 0.5rem", borderRadius: "3px", fontFamily: "monospace" }}>
                              Trích xuất OCR: {crit.evidence_snippet}
                            </div>
                          )}
                        </div>
                      </div>
                    ))}
                  </div>
                </div>

                {/* Missing Documents notice */}
                {policyAuditData.missing_documents && policyAuditData.missing_documents.length > 0 && (
                  <div style={{ padding: "0.75rem 1rem", backgroundColor: "#fffbeb", borderRadius: "var(--radius-sm)", border: "1px solid #fde68a" }}>
                    <span style={{ fontSize: "0.75rem", fontWeight: 700, color: "#92400e", display: "block", marginBottom: "0.25rem" }}>
                      GIẤY TỜ YÊU CẦU SINH VIÊN BỔ SUNG:
                    </span>
                    <ul style={{ margin: 0, paddingLeft: "1.25rem", fontSize: "0.8125rem", color: "#78350f" }}>
                      {policyAuditData.missing_documents.map((md, idx) => (
                        <li key={idx}>{md}</li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>
            ) : null}

            {/* Modal Footer */}
            <div style={{ marginTop: "1.5rem", display: "flex", justifyContent: "flex-end" }}>
              <Button variant="outline" size="sm" onClick={() => setPolicyModalDoc(null)}>
                Đóng đối soát
              </Button>
            </div>
          </div>
        </div>
      )}

      {/* ==================================================================== */}
      {/* MODAL 2: ĐỐI SOÁT GIAN LẬN & TRÙNG LẶP (ANTI-FRAUD)                 */}
      {/* ==================================================================== */}
      {fraudModalDoc && (
        <div
          style={{
            position: "fixed",
            inset: 0,
            backgroundColor: "rgba(0, 0, 0, 0.55)",
            backdropFilter: "blur(3px)",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            zIndex: 100,
            padding: "1rem",
          }}
          onClick={() => setFraudModalDoc(null)}
        >
          <div
            style={{
              backgroundColor: "#ffffff",
              borderRadius: "var(--radius-lg)",
              maxWidth: "750px",
              width: "100%",
              maxHeight: "90vh",
              overflowY: "auto",
              boxShadow: "0 25px 50px -12px rgba(0, 0, 0, 0.25)",
              padding: "1.5rem",
            }}
            onClick={(e) => e.stopPropagation()}
          >
            {/* Modal Header */}
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: "1rem" }}>
              <div>
                <span style={{ fontSize: "0.75rem", fontWeight: 700, color: "#d97706", textTransform: "uppercase" }}>
                  PHÂN TÍCH ĐỐI SOÁT CHÉO & CHỐNG GIAN LẬN CHỨNG TỪ (ANTI-FRAUD)
                </span>
                <h3 style={{ fontSize: "1.25rem", fontWeight: 800, color: "var(--gray-900)", marginTop: "0.2rem" }}>
                  {formatDisplayTitle(fraudModalDoc.title).mainTitle}
                </h3>
                <span style={{ fontSize: "0.75rem", color: "var(--gray-500)" }}>
                  MSSV: {fraudModalDoc.student_id || "N/A"} | Sinh viên: {fraudModalDoc.student_name || "N/A"}
                </span>
              </div>
              <button
                type="button"
                onClick={() => setFraudModalDoc(null)}
                style={{ border: "none", background: "none", cursor: "pointer", padding: "0.25rem" }}
              >
                <X size={20} color="var(--gray-400)" />
              </button>
            </div>

            {isAuditingFraud ? (
              <div style={{ padding: "3rem", textAlign: "center", color: "var(--gray-500)" }}>
                <Clock className="animate-spin" size={28} style={{ margin: "0 auto 0.5rem" }} />
                <span>Đang quét đối soát chéo toàn bộ cơ sở dữ liệu chứng từ...</span>
              </div>
            ) : fraudAuditData ? (
              <div style={{ display: "flex", flexDirection: "column", gap: "1rem" }}>
                {/* Risk Level Banner */}
                <div
                  style={{
                    padding: "1rem",
                    borderRadius: "var(--radius-md)",
                    backgroundColor: fraudAuditData.risk_level === "SAFE" ? "#f0fdf4" : fraudAuditData.risk_level === "WARNING" ? "#fffbeb" : "#fef2f2",
                    border: `1px solid ${fraudAuditData.risk_level === "SAFE" ? "#bbf7d0" : fraudAuditData.risk_level === "WARNING" ? "#fde68a" : "#fecaca"}`,
                    display: "flex",
                    alignItems: "center",
                    gap: "1rem",
                  }}
                >
                  {fraudAuditData.risk_level === "SAFE" ? (
                    <ShieldCheck size={32} color="#16a34a" />
                  ) : fraudAuditData.risk_level === "WARNING" ? (
                    <AlertTriangle size={32} color="#d97706" />
                  ) : (
                    <ShieldAlert size={32} color="#dc2626" />
                  )}
                  <div>
                    <span style={{ fontSize: "0.75rem", fontWeight: 700, textTransform: "uppercase", color: fraudAuditData.risk_level === "SAFE" ? "#166534" : fraudAuditData.risk_level === "WARNING" ? "#92400e" : "#991b1b" }}>
                      MỨC ĐỘ RỦI RO: {fraudAuditData.risk_level} (Chỉ số nghi vấn: {Math.round(fraudAuditData.tamper_score * 100)}%)
                    </span>
                    <div style={{ fontSize: "1.05rem", fontWeight: 800, color: fraudAuditData.risk_level === "SAFE" ? "#15803d" : fraudAuditData.risk_level === "WARNING" ? "#b45309" : "#b91c1c" }}>
                      {fraudAuditData.conclusion}
                    </div>
                  </div>
                </div>

                {/* Collisions list */}
                <div>
                  <span style={{ fontSize: "0.75rem", fontWeight: 700, color: "var(--gray-700)", textTransform: "uppercase", display: "block", marginBottom: "0.5rem" }}>
                    XUNG ĐỘT PHÁT HIỆN ĐƯỢC ({fraudAuditData.detected_collisions.length} TRƯỜNG HỢP):
                  </span>
                  {fraudAuditData.detected_collisions.length === 0 ? (
                    <div style={{ padding: "1.25rem", backgroundColor: "var(--gray-50)", borderRadius: "var(--radius-sm)", textAlign: "center", color: "var(--gray-500)", fontSize: "0.8125rem" }}>
                      Không phát hiện trùng lặp số hiệu sổ hộ nghèo, mã biên lai hay thông tin CCCD giữa các sinh viên.
                    </div>
                  ) : (
                    <div style={{ display: "flex", flexDirection: "column", gap: "0.5rem" }}>
                      {fraudAuditData.detected_collisions.map((col, idx) => (
                        <div
                          key={idx}
                          style={{
                            padding: "0.75rem 1rem",
                            borderRadius: "var(--radius-sm)",
                            backgroundColor: "#fff1f2",
                            border: "1px solid #fecdd3",
                          }}
                        >
                          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                            <span style={{ fontSize: "0.75rem", fontWeight: 700, color: "#be123c" }}>
                              {col.collision_type}
                            </span>
                            <span style={{ fontSize: "0.75rem", color: "var(--gray-500)" }}>
                              Mã số: <strong>{col.serial_number}</strong>
                            </span>
                          </div>
                          <p style={{ fontSize: "0.8125rem", color: "var(--gray-800)", marginTop: "0.25rem" }}>
                            {col.detail}
                          </p>
                          <div style={{ marginTop: "0.35rem", fontSize: "0.75rem", color: "var(--gray-600)" }}>
                            Hồ sơ xung đột: <Link to={`/documents/${col.conflicting_document_id}`} style={{ color: "var(--primary-600)" }}>Mở hồ sơ đối chiếu</Link>
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              </div>
            ) : null}

            {/* Modal Footer */}
            <div style={{ marginTop: "1.5rem", display: "flex", justifyContent: "flex-end" }}>
              <Button variant="outline" size="sm" onClick={() => setFraudModalDoc(null)}>
                Đóng đối soát
              </Button>
            </div>
          </div>
        </div>
      )}

      {/* ==================================================================== */}
      {/* MODAL 3: PHÂN LUỒNG HỒ SƠ PERCOLATOR (REVERSE ROUTING)               */}
      {/* ==================================================================== */}
      {percolateModalDoc && (
        <div
          style={{
            position: "fixed",
            inset: 0,
            backgroundColor: "rgba(0, 0, 0, 0.55)",
            backdropFilter: "blur(3px)",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            zIndex: 100,
            padding: "1rem",
          }}
          onClick={() => setPercolateModalDoc(null)}
        >
          <div
            style={{
              backgroundColor: "#ffffff",
              borderRadius: "var(--radius-lg)",
              maxWidth: "750px",
              width: "100%",
              maxHeight: "90vh",
              overflowY: "auto",
              boxShadow: "0 25px 50px -12px rgba(0, 0, 0, 0.25)",
              padding: "1.5rem",
            }}
            onClick={(e) => e.stopPropagation()}
          >
            {/* Header */}
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: "1rem" }}>
              <div>
                <span style={{ fontSize: "0.75rem", fontWeight: 700, color: "var(--primary-600)", textTransform: "uppercase", display: "flex", alignItems: "center", gap: "0.35rem" }}>
                  <GitBranch size={15} /> PHÂN LUỒNG TỰ ĐỘNG BẰNG ELASTICSEARCH PERCOLATOR (REVERSE SEARCH)
                </span>
                <h3 style={{ fontSize: "1.25rem", fontWeight: 800, color: "var(--gray-900)", marginTop: "0.2rem" }}>
                  {formatDisplayTitle(percolateModalDoc.title).mainTitle}
                </h3>
                <span style={{ fontSize: "0.75rem", color: "var(--gray-500)" }}>
                  MSSV: {percolateModalDoc.student_id || "N/A"} | Sinh viên: {percolateModalDoc.student_name || "N/A"}
                </span>
              </div>
              <button
                type="button"
                onClick={() => setPercolateModalDoc(null)}
                style={{ border: "none", background: "none", cursor: "pointer", padding: "0.25rem" }}
              >
                <X size={20} color="var(--gray-400)" />
              </button>
            </div>

            {isPercolateLoading ? (
              <div style={{ padding: "3rem", textAlign: "center", color: "var(--gray-500)" }}>
                <Clock className="animate-spin" size={28} style={{ margin: "0 auto 0.5rem", color: "var(--primary-600)" }} />
                <span>Đang chạy Percolator query so khớp tài liệu với tập quy tắc chính sách CTSV...</span>
              </div>
            ) : percolateData ? (
              <div style={{ display: "flex", flexDirection: "column", gap: "1rem" }}>
                {/* Routing Result Banner */}
                <div
                  style={{
                    padding: "1rem",
                    borderRadius: "var(--radius-md)",
                    backgroundColor: percolateData.priority === "URGENT" ? "#fef2f2" : percolateData.priority === "HIGH" ? "#fffbeb" : "#f0fdf4",
                    border: `1px solid ${percolateData.priority === "URGENT" ? "#fecaca" : percolateData.priority === "HIGH" ? "#fde68a" : "#bbf7d0"}`,
                    display: "flex",
                    alignItems: "center",
                    gap: "1rem",
                  }}
                >
                  <Building2 size={32} color={percolateData.priority === "URGENT" ? "#dc2626" : percolateData.priority === "HIGH" ? "#d97706" : "#16a34a"} />
                  <div>
                    <div style={{ display: "flex", alignItems: "center", gap: "0.5rem" }}>
                      <span
                        style={{
                          fontSize: "0.6875rem",
                          fontWeight: 800,
                          padding: "0.15rem 0.45rem",
                          borderRadius: "4px",
                          backgroundColor: percolateData.priority === "URGENT" ? "#dc2626" : percolateData.priority === "HIGH" ? "#d97706" : "#16a34a",
                          color: "#ffffff",
                        }}
                      >
                        ƯU TIÊN: {percolateData.priority}
                      </span>
                      <span style={{ fontSize: "0.75rem", color: "var(--gray-600)" }}>
                        {percolateData.routing_timestamp}
                      </span>
                    </div>
                    <div style={{ fontSize: "1.1rem", fontWeight: 800, color: "var(--gray-900)", marginTop: "0.25rem" }}>
                      Bộ phận tiếp nhận: {percolateData.assigned_department}
                    </div>
                    <p style={{ fontSize: "0.8125rem", color: "var(--gray-700)", marginTop: "0.15rem", margin: 0 }}>
                      Tuyến xử lý chính: <strong>{percolateData.primary_route}</strong>
                    </p>
                  </div>
                </div>

                {/* Matched Policies List */}
                <div>
                  <span style={{ fontSize: "0.75rem", fontWeight: 700, color: "var(--gray-700)", textTransform: "uppercase", display: "block", marginBottom: "0.5rem" }}>
                    CÁC QUY TẮC PERCOLATOR ĐÃ KÍCH HOẠT ({percolateData.matched_rules_count} LUẬT KHỚP):
                  </span>
                  <div style={{ display: "flex", flexDirection: "column", gap: "0.6rem" }}>
                    {percolateData.matched_policies.map((p, pIdx) => (
                      <div
                        key={pIdx}
                        style={{
                          padding: "0.85rem",
                          borderRadius: "var(--radius-sm)",
                          backgroundColor: "#f8fafc",
                          border: "1px solid var(--border-color)",
                        }}
                      >
                        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                          <span style={{ fontSize: "0.875rem", fontWeight: 700, color: "var(--primary-700)" }}>
                            {p.policy_name}
                          </span>
                          <span style={{ fontSize: "0.75rem", fontWeight: 700, color: "#16a34a" }}>
                            Độ khớp Percolate: {Math.round(p.confidence * 100)}%
                          </span>
                        </div>
                        <p style={{ fontSize: "0.8125rem", color: "var(--gray-700)", marginTop: "0.25rem" }}>
                          {p.description}
                        </p>
                        <div style={{ marginTop: "0.35rem", fontSize: "0.75rem", color: "var(--gray-600)" }}>
                          Hành động tự động: <strong>{p.routing_action}</strong>
                        </div>
                        {p.required_checklist && p.required_checklist.length > 0 && (
                          <div style={{ marginTop: "0.5rem", padding: "0.45rem 0.65rem", backgroundColor: "#ffffff", borderRadius: "4px", border: "1px solid var(--gray-200)" }}>
                            <span style={{ fontSize: "0.6875rem", fontWeight: 700, color: "var(--gray-600)", textTransform: "uppercase", display: "block", marginBottom: "0.25rem" }}>
                              Hồ sơ kiểm tra đối chiếu (Checklist):
                            </span>
                            <ul style={{ margin: 0, paddingLeft: "1.2rem", fontSize: "0.75rem", color: "var(--gray-700)" }}>
                              {p.required_checklist.map((chk, cIdx) => (
                                <li key={cIdx}>{chk}</li>
                              ))}
                            </ul>
                          </div>
                        )}
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            ) : null}

            {/* Modal Footer */}
            <div style={{ marginTop: "1.5rem", display: "flex", justifyContent: "flex-end" }}>
              <Button variant="outline" size="sm" onClick={() => setPercolateModalDoc(null)}>
                Đóng phân luồng
              </Button>
            </div>
          </div>
        </div>
      )}

      {/* ==================================================================== */}
      {/* MODAL 4: TỌA ĐỘ SPATIAL BOUNDING BOX TRÊN FILE SCAN GỐC            */}
      {/* ==================================================================== */}
      {spatialModalDoc && (
        <div
          style={{
            position: "fixed",
            inset: 0,
            backgroundColor: "rgba(0, 0, 0, 0.55)",
            backdropFilter: "blur(3px)",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            zIndex: 100,
            padding: "1rem",
          }}
          onClick={() => setSpatialModalDoc(null)}
        >
          <div
            style={{
              backgroundColor: "#ffffff",
              borderRadius: "var(--radius-lg)",
              maxWidth: "800px",
              width: "100%",
              maxHeight: "92vh",
              overflowY: "auto",
              boxShadow: "0 25px 50px -12px rgba(0, 0, 0, 0.25)",
              padding: "1.5rem",
            }}
            onClick={(e) => e.stopPropagation()}
          >
            {/* Header */}
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: "1rem" }}>
              <div>
                <span style={{ fontSize: "0.75rem", fontWeight: 700, color: "#0284c7", textTransform: "uppercase", display: "flex", alignItems: "center", gap: "0.35rem" }}>
                  <Scan size={15} /> TRÍCH XUẤT TỌA ĐỘ BOUNDING BOX TỪ KHÓA TRÊN FILE SCAN GỐC
                </span>
                <h3 style={{ fontSize: "1.25rem", fontWeight: 800, color: "var(--gray-900)", marginTop: "0.2rem" }}>
                  {formatDisplayTitle(spatialModalDoc.title).mainTitle}
                </h3>
              </div>
              <button
                type="button"
                onClick={() => setSpatialModalDoc(null)}
                style={{ border: "none", background: "none", cursor: "pointer", padding: "0.25rem" }}
              >
                <X size={20} color="var(--gray-400)" />
              </button>
            </div>

            {/* Keyword search input */}
            <div style={{ display: "flex", gap: "0.5rem", marginBottom: "1rem" }}>
              <input
                type="text"
                value={spatialKeyword}
                onChange={(e) => setSpatialKeyword(e.target.value)}
                onKeyDown={(e) => e.key === "Enter" && handleOpenSpatialHighlights(spatialModalDoc, spatialKeyword)}
                placeholder="Nhập từ khóa cần định vị tọa độ (vd: sinh viên, học bổng, con dấu, mssv)..."
                style={{
                  flex: 1,
                  padding: "0.5rem 0.75rem",
                  borderRadius: "var(--radius-sm)",
                  border: "1px solid var(--border-color)",
                  fontSize: "0.875rem",
                }}
              />
              <Button
                type="button"
                variant="primary"
                size="sm"
                onClick={() => handleOpenSpatialHighlights(spatialModalDoc, spatialKeyword)}
                disabled={isSpatialLoading}
              >
                Định vị Bounding Box
              </Button>
            </div>

            {isSpatialLoading ? (
              <div style={{ padding: "3rem", textAlign: "center", color: "var(--gray-500)" }}>
                <Clock className="animate-spin" size={28} style={{ margin: "0 auto 0.5rem", color: "#0284c7" }} />
                <span>Đang trích xuất tọa độ không gian [ymin, xmin, ymax, xmax] từ Elasticsearch...</span>
              </div>
            ) : spatialData ? (
              <div style={{ display: "flex", flexDirection: "column", gap: "1rem" }}>
                {/* Occurrences Counter */}
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", padding: "0.6rem 0.85rem", backgroundColor: "#f0f9ff", borderRadius: "var(--radius-sm)", border: "1px solid #bae6fd" }}>
                  <span style={{ fontSize: "0.8125rem", color: "#0369a1" }}>
                    Từ khóa: <strong>"{spatialData.keyword}"</strong>
                  </span>
                  <span style={{ fontSize: "0.8125rem", fontWeight: 700, color: "#0284c7" }}>
                    Tìm thấy {spatialData.total_occurrences} vị trí trên trang tài liệu
                  </span>
                </div>

                {/* Visual Document Canvas Simulation */}
                <div
                  style={{
                    position: "relative",
                    width: "100%",
                    height: "320px",
                    backgroundColor: "#fefefe",
                    borderRadius: "var(--radius-sm)",
                    border: "2px dashed #cbd5e1",
                    overflow: "hidden",
                    display: "flex",
                    flexDirection: "column",
                    padding: "1rem",
                    boxShadow: "inset 0 2px 4px rgba(0,0,0,0.02)",
                  }}
                >
                  <div style={{ fontSize: "0.6875rem", color: "var(--gray-400)", marginBottom: "0.5rem", display: "flex", justifyContent: "space-between" }}>
                    <span>TRANG MÔ PHỎNG VĂN BẢN SCAN (Trang 1/1)</span>
                    <span>Tọa độ hệ [0, 0] đến [800, 600]</span>
                  </div>

                  {/* Render simulated line placeholders */}
                  <div style={{ display: "flex", flexDirection: "column", gap: "8px", opacity: 0.35 }}>
                    {[...Array(9)].map((_, i) => (
                      <div key={i} style={{ height: "6px", backgroundColor: "#94a3b8", borderRadius: "3px", width: i % 2 === 0 ? "90%" : "75%" }} />
                    ))}
                  </div>

                  {/* Render Interactive Bounding Boxes */}
                  {spatialData.highlights.map((h, hIdx) => {
                    const top = Math.min(Math.max(h.box[0] * 0.5, 30), 260);
                    const left = Math.min(Math.max(h.box[1] * 0.7, 20), 550);
                    const width = Math.max((h.box[3] - h.box[1]) * 1.1, 80);
                    const height = 24;

                    return (
                      <div
                        key={hIdx}
                        style={{
                          position: "absolute",
                          top: `${top}px`,
                          left: `${left}px`,
                          width: `${width}px`,
                          height: `${height}px`,
                          backgroundColor: "rgba(250, 204, 21, 0.35)",
                          border: "2px solid #eab308",
                          borderRadius: "3px",
                          boxShadow: "0 0 10px rgba(234, 179, 8, 0.6)",
                          display: "flex",
                          alignItems: "center",
                          justifyContent: "center",
                          fontSize: "0.75rem",
                          fontWeight: 700,
                          color: "#854d0e",
                          cursor: "pointer",
                          animation: "pulse 2s infinite",
                        }}
                        title={`Tọa độ [${h.box.join(", ")}] - Khớp: "${h.matched_text}"`}
                      >
                        {h.matched_text}
                      </div>
                    );
                  })}
                </div>

                {/* Coordinate Coordinates Table */}
                <div>
                  <span style={{ fontSize: "0.75rem", fontWeight: 700, color: "var(--gray-700)", textTransform: "uppercase", display: "block", marginBottom: "0.5rem" }}>
                    DANH SÁCH TỌA ĐỘ PIXEL BẬC CAO:
                  </span>
                  <div style={{ overflowX: "auto" }}>
                    <table style={{ width: "100%", borderCollapse: "collapse", fontSize: "0.75rem" }}>
                      <thead>
                        <tr style={{ backgroundColor: "var(--gray-50)", borderBottom: "1px solid var(--border-color)", textAlign: "left" }}>
                          <th style={{ padding: "0.45rem 0.6rem" }}>STT</th>
                          <th style={{ padding: "0.45rem 0.6rem" }}>Trang</th>
                          <th style={{ padding: "0.45rem 0.6rem" }}>Từ khóa trích xuất</th>
                          <th style={{ padding: "0.45rem 0.6rem" }}>Hộp bao [ymin, xmin, ymax, xmax]</th>
                          <th style={{ padding: "0.45rem 0.6rem", textAlign: "right" }}>Độ tin cậy OCR</th>
                        </tr>
                      </thead>
                      <tbody>
                        {spatialData.highlights.map((h, idx) => (
                          <tr key={idx} style={{ borderBottom: "1px solid var(--gray-100)" }}>
                            <td style={{ padding: "0.45rem 0.6rem", fontWeight: 700 }}>#{idx + 1}</td>
                            <td style={{ padding: "0.45rem 0.6rem" }}>Trang {h.page}</td>
                            <td style={{ padding: "0.45rem 0.6rem", fontWeight: 600, color: "var(--primary-700)" }}>{h.matched_text}</td>
                            <td style={{ padding: "0.45rem 0.6rem", fontFamily: "monospace", color: "#b45309" }}>[{h.box.join(", ")}]</td>
                            <td style={{ padding: "0.45rem 0.6rem", textAlign: "right", color: "#16a34a", fontWeight: 700 }}>{Math.round((h.confidence || 0.95) * 100)}%</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              </div>
            ) : null}

            {/* Modal Footer */}
            <div style={{ marginTop: "1.5rem", display: "flex", justifyContent: "flex-end" }}>
              <Button variant="outline" size="sm" onClick={() => setSpatialModalDoc(null)}>
                Đóng bản đồ tọa độ
              </Button>
            </div>
          </div>
        </div>
      )}

      {/* ==================================================================== */}
      {/* MODAL 5: ĐỐI SOÁT TRÙNG LẶP MORE-LIKE-THIS (MLT DUPLICATE CHECK)       */}
      {/* ==================================================================== */}
      {duplicateModalDoc && (
        <div
          style={{
            position: "fixed",
            inset: 0,
            backgroundColor: "rgba(0, 0, 0, 0.55)",
            backdropFilter: "blur(3px)",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            zIndex: 100,
            padding: "1rem",
          }}
          onClick={() => setDuplicateModalDoc(null)}
        >
          <div
            style={{
              backgroundColor: "#ffffff",
              borderRadius: "var(--radius-lg)",
              maxWidth: "750px",
              width: "100%",
              maxHeight: "90vh",
              overflowY: "auto",
              boxShadow: "0 25px 50px -12px rgba(0, 0, 0, 0.25)",
              padding: "1.5rem",
            }}
            onClick={(e) => e.stopPropagation()}
          >
            {/* Header */}
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: "1rem" }}>
              <div>
                <span style={{ fontSize: "0.75rem", fontWeight: 700, color: "#be123c", textTransform: "uppercase", display: "flex", alignItems: "center", gap: "0.35rem" }}>
                  <CopyCheck size={15} /> ĐỐI SOÁT TRÙNG LẶP HỒ SƠ BẰNG ELASTICSEARCH MORE-LIKE-THIS (MLT)
                </span>
                <h3 style={{ fontSize: "1.25rem", fontWeight: 800, color: "var(--gray-900)", marginTop: "0.2rem" }}>
                  {formatDisplayTitle(duplicateModalDoc.title).mainTitle}
                </h3>
                <span style={{ fontSize: "0.75rem", color: "var(--gray-500)" }}>
                  MSSV: {duplicateModalDoc.student_id || "N/A"} | Sinh viên: {duplicateModalDoc.student_name || "N/A"}
                </span>
              </div>
              <button
                type="button"
                onClick={() => setDuplicateModalDoc(null)}
                style={{ border: "none", background: "none", cursor: "pointer", padding: "0.25rem" }}
              >
                <X size={20} color="var(--gray-400)" />
              </button>
            </div>

            {isDuplicateLoading ? (
              <div style={{ padding: "3rem", textAlign: "center", color: "var(--gray-500)" }}>
                <Clock className="animate-spin" size={28} style={{ margin: "0 auto 0.5rem", color: "#be123c" }} />
                <span>Đang trích xuất TF-IDF và quét tương đồng More-Like-This trên toàn trường...</span>
              </div>
            ) : duplicateData ? (
              <div style={{ display: "flex", flexDirection: "column", gap: "1rem" }}>
                {/* Risk Banner */}
                <div
                  style={{
                    padding: "1rem",
                    borderRadius: "var(--radius-md)",
                    backgroundColor: duplicateData.risk_level === "SAFE" ? "#f0fdf4" : duplicateData.risk_level === "WARNING" ? "#fffbeb" : "#fef2f2",
                    border: `1px solid ${duplicateData.risk_level === "SAFE" ? "#bbf7d0" : duplicateData.risk_level === "WARNING" ? "#fde68a" : "#fecaca"}`,
                    display: "flex",
                    alignItems: "center",
                    gap: "1rem",
                  }}
                >
                  {duplicateData.risk_level === "SAFE" ? (
                    <CheckCircle2 size={32} color="#16a34a" />
                  ) : duplicateData.risk_level === "WARNING" ? (
                    <AlertTriangle size={32} color="#d97706" />
                  ) : (
                    <ShieldAlert size={32} color="#dc2626" />
                  )}
                  <div>
                    <span style={{ fontSize: "0.75rem", fontWeight: 700, textTransform: "uppercase", color: duplicateData.risk_level === "SAFE" ? "#166534" : duplicateData.risk_level === "WARNING" ? "#92400e" : "#991b1b" }}>
                      MỨC ĐỘ TRÙNG LẶP: {duplicateData.risk_level} (Độ tương đồng cao nhất: {Math.round(duplicateData.max_similarity_score * 100)}%)
                    </span>
                    <div style={{ fontSize: "1.05rem", fontWeight: 800, color: duplicateData.risk_level === "SAFE" ? "#15803d" : duplicateData.risk_level === "WARNING" ? "#b45309" : "#b91c1c" }}>
                      {duplicateData.is_suspect_duplicate ? "PHÁT HIỆN HỒ SƠ CÓ DẤU HIỆU TRÙNG LẶP / SAO CHÉP" : "HỒ SƠ ĐỘC LẬP — KHÔNG CÓ DẤU HIỆU TRÙNG LẶP"}
                    </div>
                    <p style={{ fontSize: "0.8125rem", color: "var(--gray-700)", marginTop: "0.2rem", margin: 0 }}>
                      Khuyến nghị xử lý: {duplicateData.recommendation}
                    </p>
                  </div>
                </div>

                {/* Candidate Duplicates List */}
                <div>
                  <span style={{ fontSize: "0.75rem", fontWeight: 700, color: "var(--gray-700)", textTransform: "uppercase", display: "block", marginBottom: "0.5rem" }}>
                    CÁC ỨNG VIÊN CÓ NỘI DUNG TƯƠNG ĐỒNG ({duplicateData.candidates.length} VĂN BẢN):
                  </span>
                  {duplicateData.candidates.length === 0 ? (
                    <div style={{ padding: "1.25rem", backgroundColor: "var(--gray-50)", borderRadius: "var(--radius-sm)", textAlign: "center", color: "var(--gray-500)", fontSize: "0.8125rem" }}>
                      Không phát hiện văn bản nào có nội dung trùng lặp trong kho lưu trữ.
                    </div>
                  ) : (
                    <div style={{ display: "flex", flexDirection: "column", gap: "0.5rem" }}>
                      {duplicateData.candidates.map((cand, idx) => (
                        <div
                          key={idx}
                          style={{
                            padding: "0.75rem 1rem",
                            borderRadius: "var(--radius-sm)",
                            backgroundColor: "#f8fafc",
                            border: "1px solid var(--border-color)",
                          }}
                        >
                          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                            <span style={{ fontSize: "0.875rem", fontWeight: 700, color: "var(--gray-900)" }}>
                              {cand.title}
                            </span>
                            <span style={{ fontSize: "0.75rem", fontWeight: 700, color: cand.similarity_score >= 0.8 ? "#dc2626" : "#d97706" }}>
                              Tương đồng: {Math.round(cand.similarity_score * 100)}%
                            </span>
                          </div>
                          <div style={{ fontSize: "0.75rem", color: "var(--gray-500)", marginTop: "0.2rem" }}>
                            Sinh viên: <strong>{cand.student_name || "N/A"}</strong> | MSSV: <strong>{cand.student_id || "N/A"}</strong>
                          </div>
                          {cand.content_snippet && (
                            <p style={{ fontSize: "0.75rem", color: "var(--gray-700)", marginTop: "0.3rem", backgroundColor: "#ffffff", padding: "0.4rem 0.6rem", borderRadius: "3px", border: "1px solid var(--gray-200)" }}>
                              {cand.content_snippet}
                            </p>
                          )}
                          <div style={{ marginTop: "0.35rem", fontSize: "0.75rem" }}>
                            <Link to={`/documents/${cand.document_id}`} style={{ color: "var(--primary-600)", textDecoration: "none", fontWeight: 600 }}>
                              Mở hồ sơ đối chiếu chi tiết ➔
                            </Link>
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              </div>
            ) : null}

            {/* Modal Footer */}
            <div style={{ marginTop: "1.5rem", display: "flex", justifyContent: "flex-end" }}>
              <Button variant="outline" size="sm" onClick={() => setDuplicateModalDoc(null)}>
                Đóng đối soát trùng lặp
              </Button>
            </div>
          </div>
        </div>
      )}

      {/* ==================================================================== */}
      {/* MODAL 6: TRÍCH XUẤT THỰC THỂ & GÁN NHÃN SIGNIFICANT_TEXT             */}
      {/* ==================================================================== */}
      {autoTagsModalDoc && (
        <div
          style={{
            position: "fixed",
            inset: 0,
            backgroundColor: "rgba(0, 0, 0, 0.55)",
            backdropFilter: "blur(3px)",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            zIndex: 100,
            padding: "1rem",
          }}
        >
          <div
            style={{
              backgroundColor: "#ffffff",
              borderRadius: "var(--radius-lg)",
              maxWidth: "760px",
              width: "100%",
              maxHeight: "90vh",
              overflowY: "auto",
              boxShadow: "var(--shadow-xl)",
              padding: "1.75rem",
              border: "1px solid var(--border-color)",
            }}
          >
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: "1rem", borderBottom: "1px solid var(--gray-200)", paddingBottom: "0.75rem" }}>
              <div style={{ display: "flex", alignItems: "center", gap: "0.6rem" }}>
                <div style={{ padding: "0.45rem", borderRadius: "var(--radius-sm)", backgroundColor: "#ecfdf5", color: "#059669" }}>
                  <Tag size={20} />
                </div>
                <div>
                  <h3 style={{ fontSize: "1.125rem", fontWeight: 700, color: "var(--gray-900)", margin: 0 }}>
                    Trích xuất Thực thể & Gán nhãn Tự động (significant_text)
                  </h3>
                  <span style={{ fontSize: "0.75rem", color: "var(--gray-500)" }}>
                    Phân tích toàn văn OCR bằng thuật toán tần suất nổi bật so với kho lưu trữ
                  </span>
                </div>
              </div>
              <button
                type="button"
                onClick={() => setAutoTagsModalDoc(null)}
                style={{ border: "none", background: "none", cursor: "pointer", color: "var(--gray-400)" }}
              >
                <X size={20} />
              </button>
            </div>

            {isAutoTagsLoading ? (
              <div style={{ padding: "2.5rem 0", textAlign: "center", color: "var(--gray-500)", fontSize: "0.875rem" }}>
                <div style={{ display: "inline-block", animation: "spin 1s linear infinite", marginBottom: "0.5rem" }}>⌛</div>
                <div>Đang chạy thuật toán trích xuất significant_text...</div>
              </div>
            ) : autoTagsData ? (
              <div style={{ display: "flex", flexDirection: "column", gap: "1.25rem" }}>
                <div style={{ padding: "0.85rem", borderRadius: "var(--radius-sm)", backgroundColor: "#f0fdf4", border: "1px solid #bbf7d0" }}>
                  <div style={{ fontSize: "0.75rem", fontWeight: 700, color: "#166534", textTransform: "uppercase" }}>
                    DIỆN CHÍNH SÁCH DỰ BÁO:
                  </div>
                  <div style={{ fontSize: "1rem", fontWeight: 800, color: "#15803d", marginTop: "0.2rem" }}>
                    {autoTagsData.suggested_policy_category}
                  </div>
                </div>

                {/* Tags List */}
                <div>
                  <span style={{ fontSize: "0.75rem", fontWeight: 700, color: "var(--gray-700)", textTransform: "uppercase", display: "block", marginBottom: "0.5rem" }}>
                    CÁC THẺ NHÃN ĐÃ GÁN TỰ ĐỘNG ({autoTagsData.total_tags}):
                  </span>
                  <div style={{ display: "flex", flexDirection: "column", gap: "0.6rem" }}>
                    {autoTagsData.tags.map((t, idx) => (
                      <div key={idx} style={{ padding: "0.75rem", borderRadius: "var(--radius-sm)", backgroundColor: "#f8fafc", border: "1px solid #e2e8f0" }}>
                        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                          <span style={{ fontWeight: 700, color: "#065f46", fontSize: "0.875rem", backgroundColor: "#ecfdf5", padding: "0.15rem 0.5rem", borderRadius: "4px" }}>
                            #{t.tag}
                          </span>
                          <span style={{ fontSize: "0.75rem", fontWeight: 700, color: "#059669" }}>
                            Điểm nổi bật: {Math.round(t.significance_score * 100)}%
                          </span>
                        </div>
                        <div style={{ fontSize: "0.75rem", color: "var(--gray-500)", marginTop: "0.3rem" }}>
                          Nhóm thực thể: <strong>{t.category}</strong> | Khớp từ khóa: <em>"{t.matched_keyword}"</em>
                        </div>
                        <div style={{ fontSize: "0.75rem", color: "var(--gray-700)", marginTop: "0.3rem", fontStyle: "italic", backgroundColor: "#ffffff", padding: "0.4rem 0.6rem", borderRadius: "3px", border: "1px solid #f1f5f9" }}>
                          {t.evidence_snippet}
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            ) : null}

            <div style={{ marginTop: "1.5rem", display: "flex", justifyContent: "flex-end" }}>
              <Button variant="outline" size="sm" onClick={() => setAutoTagsModalDoc(null)}>
                Đóng
              </Button>
            </div>
          </div>
        </div>
      )}

      {/* ==================================================================== */}
      {/* MODAL 7: NHẬT KÝ KIỂM TOÁN PHIÊN BẢN & SO SÁNH DIFFS SỬA ĐỔI         */}
      {/* ==================================================================== */}
      {auditTrailModalDoc && (
        <div
          style={{
            position: "fixed",
            inset: 0,
            backgroundColor: "rgba(0, 0, 0, 0.55)",
            backdropFilter: "blur(3px)",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            zIndex: 100,
            padding: "1rem",
          }}
        >
          <div
            style={{
              backgroundColor: "#ffffff",
              borderRadius: "var(--radius-lg)",
              maxWidth: "850px",
              width: "100%",
              maxHeight: "90vh",
              overflowY: "auto",
              boxShadow: "var(--shadow-xl)",
              padding: "1.75rem",
              border: "1px solid var(--border-color)",
            }}
          >
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: "1rem", borderBottom: "1px solid var(--gray-200)", paddingBottom: "0.75rem" }}>
              <div style={{ display: "flex", alignItems: "center", gap: "0.6rem" }}>
                <div style={{ padding: "0.45rem", borderRadius: "var(--radius-sm)", backgroundColor: "#f5f3ff", color: "#7c3aed" }}>
                  <History size={20} />
                </div>
                <div>
                  <h3 style={{ fontSize: "1.125rem", fontWeight: 700, color: "var(--gray-900)", margin: 0 }}>
                    Nhật ký Kiểm toán Phiên bản & So sánh Diffs (Audit Trail)
                  </h3>
                  <span style={{ fontSize: "0.75rem", color: "var(--gray-500)" }}>
                    Lập chỉ mục lịch sử chỉnh sửa giữa bản OCR thô và bản cán bộ hiệu đính
                  </span>
                </div>
              </div>
              <button
                type="button"
                onClick={() => setAuditTrailModalDoc(null)}
                style={{ border: "none", background: "none", cursor: "pointer", color: "var(--gray-400)" }}
              >
                <X size={20} />
              </button>
            </div>

            {isAuditTrailLoading ? (
              <div style={{ padding: "2.5rem 0", textAlign: "center", color: "var(--gray-500)", fontSize: "0.875rem" }}>
                <div style={{ display: "inline-block", animation: "spin 1s linear infinite", marginBottom: "0.5rem" }}>⌛</div>
                <div>Đang truy xuất lịch sử phiên bản từ Elasticsearch...</div>
              </div>
            ) : auditTrailData ? (
              <div style={{ display: "flex", flexDirection: "column", gap: "1.25rem" }}>
                <div style={{ padding: "0.85rem", borderRadius: "var(--radius-sm)", backgroundColor: "#faf5ff", border: "1px solid #e9d5ff", display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                  <div>
                    <span style={{ fontSize: "0.75rem", fontWeight: 700, color: "#6b21a8", textTransform: "uppercase" }}>TÀI LIỆU:</span>
                    <div style={{ fontSize: "0.9375rem", fontWeight: 800, color: "#581c87" }}>{auditTrailData.title}</div>
                  </div>
                  <span style={{ fontSize: "0.8125rem", fontWeight: 700, color: "#6b21a8", backgroundColor: "#f3e8ff", padding: "0.2rem 0.6rem", borderRadius: "9999px" }}>
                    Phiên bản hiện hành: v{auditTrailData.current_version}
                  </span>
                </div>

                {/* Revisions list */}
                <div style={{ display: "flex", flexDirection: "column", gap: "1rem" }}>
                  {auditTrailData.revisions.map((rev) => (
                    <div key={rev.revision_number} style={{ padding: "1rem", borderRadius: "var(--radius-sm)", backgroundColor: "#f8fafc", border: "1px solid #e2e8f0" }}>
                      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "0.5rem" }}>
                        <span style={{ fontWeight: 800, fontSize: "0.875rem", color: "var(--gray-900)" }}>
                          Phiên bản #{rev.revision_number} — {rev.change_summary}
                        </span>
                        <span style={{ fontSize: "0.75rem", color: "var(--gray-500)" }}>
                          {new Date(rev.edited_at).toLocaleString("vi-VN")}
                        </span>
                      </div>
                      <div style={{ fontSize: "0.75rem", color: "var(--gray-600)", marginBottom: "0.75rem" }}>
                        Thực hiện bởi: <strong>{rev.editor_name}</strong> (Vai trò: {rev.editor_role})
                      </div>

                      {/* Diffs Table */}
                      <table style={{ width: "100%", borderCollapse: "collapse", fontSize: "0.75rem" }}>
                        <thead>
                          <tr style={{ backgroundColor: "#e2e8f0", textAlign: "left" }}>
                            <th style={{ padding: "0.4rem 0.6rem" }}>Trường thông tin</th>
                            <th style={{ padding: "0.4rem 0.6rem" }}>Bản OCR thô (Scan gốc)</th>
                            <th style={{ padding: "0.4rem 0.6rem" }}>Bản sau hiệu đính</th>
                            <th style={{ padding: "0.4rem 0.6rem", textAlign: "center" }}>Trạng thái</th>
                          </tr>
                        </thead>
                        <tbody>
                          {rev.diffs.map((d, dIdx) => (
                            <tr key={dIdx} style={{ borderBottom: "1px solid #f1f5f9" }}>
                              <td style={{ padding: "0.4rem 0.6rem", fontWeight: 700 }}>{d.field_name}</td>
                              <td style={{ padding: "0.4rem 0.6rem", color: "#dc2626", backgroundColor: d.is_changed ? "#fef2f2" : "transparent" }}>
                                {String(d.original_ocr_value)}
                              </td>
                              <td style={{ padding: "0.4rem 0.6rem", color: "#16a34a", fontWeight: 600, backgroundColor: d.is_changed ? "#f0fdf4" : "transparent" }}>
                                {String(d.curated_value)}
                              </td>
                              <td style={{ padding: "0.4rem 0.6rem", textAlign: "center" }}>
                                <span
                                  style={{
                                    fontSize: "0.6875rem",
                                    fontWeight: 700,
                                    padding: "0.1rem 0.4rem",
                                    borderRadius: "3px",
                                    backgroundColor: d.is_changed ? "#fef3c7" : "#e2e8f0",
                                    color: d.is_changed ? "#92400e" : "#475569",
                                  }}
                                >
                                  {d.is_changed ? "Đã sửa" : "Khớp 100%"}
                                </span>
                              </td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  ))}
                </div>
              </div>
            ) : null}

            <div style={{ marginTop: "1.5rem", display: "flex", justifyContent: "flex-end" }}>
              <Button variant="outline" size="sm" onClick={() => setAuditTrailModalDoc(null)}>
                Đóng
              </Button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};


