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
  CheckCircle2,
  AlertTriangle,
  ShieldAlert,
  Table as TableIcon,
  HelpCircle,
  FileCheck,
  Download,
  AlertOctagon,
  ShieldCheck,
  X,
  Shield,
  Layers,
  Award,
  GitBranch,
  Scan,
  BarChart3,
  Zap,
  CopyCheck,
  Building2,
  TrendingUp,
  CheckSquare,
  Tag,
  History,
  MapPin,
  Activity,
  Bell,
  FileCode,
  Cpu,
  PieChart,
  ExternalLink,
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
  TableSearchResponse,
  PiiAuditSummaryResponse,
  PercolateRoutingResponse,
  CtsvMultiDimensionalAnalyticsResponse,
  SpatialHighlightResponse,
  OcrTolerantSearchResponse,
  DuplicateCheckResponse,
  OcrQualityDistributionResponse,
  OcrReviewQueueResponse,
  DocumentAutoTagsResponse,
  GeoAreaVerifyResponse,
  StudentEntityGraphResponse,
  DocumentAuditTrailResponse,
  WatcherItem,
  WatcherTriggeredEvent,
  HybridRrfHit,
  HybridRrfSearchResponse,
  KibanaCanvasWorkpadPreview,
} from "../api/search";
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

  // Autocomplete / Search-As-You-Type
  const [suggestions, setSuggestions] = useState<SuggestItem[]>([]);
  const [showSuggestions, setShowSuggestions] = useState(false);
  const searchContainerRef = React.useRef<HTMLDivElement>(null);

  const [searchResponse, setSearchResponse] = useState<SearchResponse | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [hasSearched, setHasSearched] = useState(false);
  const [currentPage, setCurrentPage] = useState(initialPage);

  // ── Navigation View Tabs ──────────────────────────────────────────────────
  const [activeTab, setActiveTab] = useState<
    | "fulltext"
    | "hybrid_rrf"
    | "faq"
    | "tables"
    | "pii"
    | "ctsv_analytics"
    | "ocr_tolerant"
    | "ocr_quality"
    | "realtime_watchers"
  >("fulltext");

  // ── Đề xuất 1: Hybrid Search (BM25 + kNN Reciprocal Rank Fusion) ──────────
  const [hybridInput, setHybridInput] = useState("nghị định 81 miễn giảm học phí sv nghèo khó khăn");
  const [hybridConstantK, setHybridConstantK] = useState(20);
  const [hybridData, setHybridData] = useState<HybridRrfSearchResponse | null>(null);
  const [isHybridLoading, setIsHybridLoading] = useState(false);

  // ── Đề xuất 5: Kibana Canvas Dashboard & Workpad Preview ──────────────────
  const [kibanaPreviewData, setKibanaPreviewData] = useState<KibanaCanvasWorkpadPreview | null>(null);
  const [isKibanaLoading, setIsKibanaLoading] = useState(false);

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

  // ── Feature 4: Nested Table Structured Search ─────────────────────────────
  const [tableStudentId, setTableStudentId] = useState("");
  const [tableStudentName, setTableStudentName] = useState("");
  const [tableMinGpa, setTableMinGpa] = useState<string>("");
  const [tableMinDrl, setTableMinDrl] = useState<string>("");
  const [tableTier, setTableTier] = useState("");
  const [tableResult, setTableResult] = useState<TableSearchResponse | null>(null);
  const [isTableLoading, setIsTableLoading] = useState(false);

  // ── Feature 5: PII SIEM Security ──────────────────────────────────────────
  const [piiWindow, setPiiWindow] = useState(60);
  const [piiData, setPiiData] = useState<PiiAuditSummaryResponse | null>(null);
  const [isPiiLoading, setIsPiiLoading] = useState(false);

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

  // ── Đề tài CTSV - Feature 4: OCR Error-Tolerant Search Tab ─────────────────
  const [ocrTolerantInput, setOcrTolerantInput] = useState("don xin hb kkht sv 2O21");
  const [ocrTolerantData, setOcrTolerantData] = useState<OcrTolerantSearchResponse | null>(null);
  const [isOcrTolerantLoading, setIsOcrTolerantLoading] = useState(false);

  // ── Đề tài CTSV - Feature 5: Cross-Document MLT Duplicate Modal ────────────
  const [duplicateModalDoc, setDuplicateModalDoc] = useState<SearchHit | null>(null);
  const [duplicateData, setDuplicateData] = useState<DuplicateCheckResponse | null>(null);
  const [isDuplicateLoading, setIsDuplicateLoading] = useState(false);

  // ── Đề tài CTSV Nâng cao 1: OCR Quality & Review Queue ────────────────────
  const [ocrQualityData, setOcrQualityData] = useState<OcrQualityDistributionResponse | null>(null);
  const [isQualityLoading, setIsQualityLoading] = useState(false);
  const [reviewQueueData, setReviewQueueData] = useState<OcrReviewQueueResponse | null>(null);
  const [isQueueLoading, setIsQueueLoading] = useState(false);

  // ── Đề tài CTSV Nâng cao 2: Auto-Tagging Modal (significant_text) ─────────
  const [autoTagsModalDoc, setAutoTagsModalDoc] = useState<SearchHit | null>(null);
  const [autoTagsData, setAutoTagsData] = useState<DocumentAutoTagsResponse | null>(null);
  const [isAutoTagsLoading, setIsAutoTagsLoading] = useState(false);

  // ── Đề tài CTSV Nâng cao 3 & 6: Geo-Verify NĐ 81 & Watchers ────────────────
  const [geoAddressInput, setGeoAddressInput] = useState("Thôn Đạ Tro, Xã Đạ Chais, Huyện Lạc Dương, Tỉnh Lâm Đồng");
  const [geoVerifyResult, setGeoVerifyResult] = useState<GeoAreaVerifyResponse | null>(null);
  const [isGeoLoading, setIsGeoLoading] = useState(false);
  const [watchersList, setWatchersList] = useState<WatcherItem[]>([]);
  const [triggeredEvents, setTriggeredEvents] = useState<WatcherTriggeredEvent[]>([]);
  const [isWatchersLoading, setIsWatchersLoading] = useState(false);

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

  const handleQueryTables = async () => {
    setIsTableLoading(true);
    try {
      const gpaNum = tableMinGpa ? parseFloat(tableMinGpa) : undefined;
      const drlNum = tableMinDrl ? parseInt(tableMinDrl, 10) : undefined;
      const data = await searchApi.queryTables({
        student_id: tableStudentId.trim() || undefined,
        student_name: tableStudentName.trim() || undefined,
        min_gpa: isNaN(gpaNum as number) ? undefined : gpaNum,
        min_drl: isNaN(drlNum as number) ? undefined : drlNum,
        scholarship_tier: tableTier || undefined,
        page: 1,
        page_size: 20,
      });
      setTableResult(data);
    } catch (err: any) {
      addToast({
        type: "error",
        title: "Lỗi bảng biểu",
        message: "Lỗi truy vấn bảng biểu cấu trúc",
      });
    } finally {
      setIsTableLoading(false);
    }
  };

  const handleLoadPiiAudit = async (windowMinutes = piiWindow) => {
    setIsPiiLoading(true);
    try {
      const data = await searchApi.getPiiAuditSummary(windowMinutes);
      setPiiData(data);
    } catch (err: any) {
      addToast({
        type: "error",
        title: "Lỗi PII Audit",
        message: "Lỗi tải báo cáo an toàn PII",
      });
    } finally {
      setIsPiiLoading(false);
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

  const handleSearchOcrTolerant = async (text: string) => {
    if (!text.trim()) return;
    setIsOcrTolerantLoading(true);
    try {
      const data = await searchApi.searchOcrTolerant({ query: text.trim() });
      setOcrTolerantData(data);
    } catch (err: any) {
      addToast({
        type: "error",
        title: "Lỗi tìm kiếm OCR",
        message: "Lỗi tìm kiếm chịu lỗi nhận dạng OCR",
      });
    } finally {
      setIsOcrTolerantLoading(false);
    }
  };

  const handleLoadOcrQuality = async () => {
    setIsQualityLoading(true);
    setIsQueueLoading(true);
    try {
      const [dist, queue] = await Promise.all([
        searchApi.getOcrQualityDistribution(),
        searchApi.getOcrReviewQueue({ page: 1, pageSize: 10, maxConfidence: 0.75 }),
      ]);
      setOcrQualityData(dist);
      setReviewQueueData(queue);
    } catch (err: any) {
      addToast({
        type: "error",
        title: "Lỗi chất lượng OCR",
        message: "Không thể tải báo cáo phân bổ chất lượng nhận dạng OCR",
      });
    } finally {
      setIsQualityLoading(false);
      setIsQueueLoading(false);
    }
  };

  const handleVerifyGeoArea = async (address: string) => {
    if (!address.trim()) return;
    setIsGeoLoading(true);
    try {
      const res = await searchApi.verifyGeoPriorityArea({ address_raw: address });
      setGeoVerifyResult(res);
    } catch (err: any) {
      addToast({
        type: "error",
        title: "Lỗi thẩm định địa giới",
        message: "Không thể thẩm định địa giới ưu tiên",
      });
    } finally {
      setIsGeoLoading(false);
    }
  };

  const handleLoadWatchers = async () => {
    setIsWatchersLoading(true);
    try {
      const data = await searchApi.getWatchers();
      setWatchersList(data.watchers || []);
      if (data.watchers && data.watchers.length > 0) {
        const evts = await searchApi.getWatcherTriggeredEvents(data.watchers[0].watcher_id);
        setTriggeredEvents(evts);
      }
    } catch (err: any) {
      addToast({
        type: "error",
        title: "Lỗi bộ theo dõi",
        message: "Không thể tải danh sách bộ theo dõi Watchers",
      });
    } finally {
      setIsWatchersLoading(false);
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

  // ── Đề xuất 5: Handler Tải Dữ liệu Kibana Canvas Workpad ─────────────────
  const handleLoadKibanaCanvas = async () => {
    setIsKibanaLoading(true);
    try {
      const data = await searchApi.getKibanaCanvasPreview();
      setKibanaPreviewData(data);
    } catch (err: any) {
      addToast({
        type: "error",
        title: "Lỗi tải Canvas Workpad",
        message: err?.response?.data?.detail || "Không thể tải dữ liệu Kibana Canvas",
      });
    } finally {
      setIsKibanaLoading(false);
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
          <h1 style={{ fontSize: "1.5rem", fontWeight: 800, color: "var(--gray-900)" }}>
            Tra cứu & Thẩm định Hồ sơ CTSV Thông minh
          </h1>
          <p style={{ fontSize: "0.875rem", color: "var(--gray-500)", marginTop: "0.25rem" }}>
            Hệ sinh thái tìm kiếm thông minh Elasticsearch 8 & OCR CSDL: Tra cứu toàn văn, Tìm kiếm Lai RRF, Thống kê CTSV, Hỏi đáp pháp quy & Giám sát an toàn PII.
          </p>
        </div>
      </div>

      {/* View Switcher Tabs - 2 Balanced Suites (Zero Overflow, Zero Cutoff) */}
      <div
        style={{
          display: "flex",
          flexDirection: "column",
          gap: "0.6rem",
          backgroundColor: "#f8fafc",
          border: "1px solid var(--gray-200)",
          borderRadius: "0.875rem",
          padding: "0.65rem",
          boxShadow: "0 1px 3px rgba(0,0,0,0.04)",
        }}
      >
        {/* SUITE 1: CÔNG NGHỆ TRA CỨU & AI TÌM KIẾM THÔNG MINH */}
        <div>
          <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: "0.35rem", padding: "0 0.25rem" }}>
            <span style={{ fontSize: "0.6875rem", fontWeight: 800, color: "#1e40af", textTransform: "uppercase", letterSpacing: "0.05em", display: "flex", alignItems: "center", gap: "0.35rem" }}>
              <Search size={12} /> NHÓM 1: CÔNG NGHỆ TRA CỨU & AI TÌM KIẾM THÔNG MINH
            </span>
            <span style={{ fontSize: "0.6875rem", color: "var(--gray-500)", fontWeight: 600 }}>Elasticsearch 8.9+ Core</span>
          </div>

          <div
            style={{
              display: "grid",
              gridTemplateColumns: "repeat(auto-fit, minmax(170px, 1fr))",
              gap: "0.4rem",
            }}
          >
            {/* 1. fulltext */}
            <button
              type="button"
              onClick={() => setActiveTab("fulltext")}
              style={{
                display: "inline-flex",
                alignItems: "center",
                justifyContent: "center",
                gap: "0.4rem",
                padding: "0.55rem 0.65rem",
                borderRadius: "0.5rem",
                border: activeTab === "fulltext" ? "1px solid #2563eb" : "1px solid var(--gray-200)",
                backgroundColor: activeTab === "fulltext" ? "var(--primary-600)" : "#ffffff",
                color: activeTab === "fulltext" ? "#ffffff" : "var(--gray-700)",
                fontWeight: activeTab === "fulltext" ? 700 : 600,
                fontSize: "0.8125rem",
                cursor: "pointer",
                transition: "all 0.15s ease",
                boxShadow: activeTab === "fulltext" ? "0 2px 4px rgba(37,99,235,0.25)" : "none",
              }}
            >
              <Search size={14} style={{ flexShrink: 0 }} />
              <span>Tra cứu Toàn văn</span>
            </button>

            {/* 2. hybrid_rrf */}
            <button
              type="button"
              onClick={() => {
                setActiveTab("hybrid_rrf");
                if (!hybridData) handleSearchHybridRrf(hybridInput);
              }}
              style={{
                display: "inline-flex",
                alignItems: "center",
                justifyContent: "center",
                gap: "0.4rem",
                padding: "0.55rem 0.65rem",
                borderRadius: "0.5rem",
                border: activeTab === "hybrid_rrf" ? "1px solid #4f46e5" : "1px solid #c7d2fe",
                backgroundColor: activeTab === "hybrid_rrf" ? "#4f46e5" : "#ffffff",
                color: activeTab === "hybrid_rrf" ? "#ffffff" : "#3730a3",
                fontWeight: activeTab === "hybrid_rrf" ? 700 : 600,
                fontSize: "0.8125rem",
                cursor: "pointer",
                transition: "all 0.15s ease",
                boxShadow: activeTab === "hybrid_rrf" ? "0 2px 4px rgba(79,70,229,0.3)" : "none",
              }}
            >
              <Cpu size={14} style={{ flexShrink: 0 }} />
              <span>Tìm kiếm Lai RRF</span>
              <span style={{ fontSize: "0.625rem", backgroundColor: activeTab === "hybrid_rrf" ? "rgba(255,255,255,0.25)" : "#e0e7ff", color: activeTab === "hybrid_rrf" ? "#fff" : "#3730a3", padding: "0.1rem 0.35rem", borderRadius: "9999px", fontWeight: 700 }}>
                ES 8.9+
              </span>
            </button>

            {/* 3. ocr_tolerant */}
            <button
              type="button"
              onClick={() => {
                setActiveTab("ocr_tolerant");
                if (!ocrTolerantData) handleSearchOcrTolerant(ocrTolerantInput);
              }}
              style={{
                display: "inline-flex",
                alignItems: "center",
                justifyContent: "center",
                gap: "0.4rem",
                padding: "0.55rem 0.65rem",
                borderRadius: "0.5rem",
                border: activeTab === "ocr_tolerant" ? "1px solid #2563eb" : "1px solid var(--gray-200)",
                backgroundColor: activeTab === "ocr_tolerant" ? "var(--primary-600)" : "#ffffff",
                color: activeTab === "ocr_tolerant" ? "#ffffff" : "var(--gray-700)",
                fontWeight: activeTab === "ocr_tolerant" ? 700 : 600,
                fontSize: "0.8125rem",
                cursor: "pointer",
                transition: "all 0.15s ease",
                boxShadow: activeTab === "ocr_tolerant" ? "0 2px 4px rgba(37,99,235,0.25)" : "none",
              }}
            >
              <Zap size={14} style={{ flexShrink: 0 }} />
              <span>Bù lỗi OCR</span>
              <span style={{ fontSize: "0.625rem", backgroundColor: activeTab === "ocr_tolerant" ? "rgba(255,255,255,0.25)" : "#e0e7ff", color: activeTab === "ocr_tolerant" ? "#fff" : "#3730a3", padding: "0.1rem 0.35rem", borderRadius: "9999px", fontWeight: 700 }}>
                Fuzzy
              </span>
            </button>

            {/* 4. tables */}
            <button
              type="button"
              onClick={() => {
                setActiveTab("tables");
                if (!tableResult) handleQueryTables();
              }}
              style={{
                display: "inline-flex",
                alignItems: "center",
                justifyContent: "center",
                gap: "0.4rem",
                padding: "0.55rem 0.65rem",
                borderRadius: "0.5rem",
                border: activeTab === "tables" ? "1px solid #2563eb" : "1px solid var(--gray-200)",
                backgroundColor: activeTab === "tables" ? "var(--primary-600)" : "#ffffff",
                color: activeTab === "tables" ? "#ffffff" : "var(--gray-700)",
                fontWeight: activeTab === "tables" ? 700 : 600,
                fontSize: "0.8125rem",
                cursor: "pointer",
                transition: "all 0.15s ease",
                boxShadow: activeTab === "tables" ? "0 2px 4px rgba(37,99,235,0.25)" : "none",
              }}
            >
              <TableIcon size={14} style={{ flexShrink: 0 }} />
              <span>Bảng Quyết định</span>
              <span style={{ fontSize: "0.625rem", backgroundColor: activeTab === "tables" ? "rgba(255,255,255,0.25)" : "#dbeafe", color: activeTab === "tables" ? "#fff" : "#1e40af", padding: "0.1rem 0.35rem", borderRadius: "9999px", fontWeight: 700 }}>
                Nested
              </span>
            </button>

            {/* 5. faq */}
            <button
              type="button"
              onClick={() => setActiveTab("faq")}
              style={{
                display: "inline-flex",
                alignItems: "center",
                justifyContent: "center",
                gap: "0.4rem",
                padding: "0.55rem 0.65rem",
                borderRadius: "0.5rem",
                border: activeTab === "faq" ? "1px solid #2563eb" : "1px solid var(--gray-200)",
                backgroundColor: activeTab === "faq" ? "var(--primary-600)" : "#ffffff",
                color: activeTab === "faq" ? "#ffffff" : "var(--gray-700)",
                fontWeight: activeTab === "faq" ? 700 : 600,
                fontSize: "0.8125rem",
                cursor: "pointer",
                transition: "all 0.15s ease",
                boxShadow: activeTab === "faq" ? "0 2px 4px rgba(37,99,235,0.25)" : "none",
              }}
            >
              <HelpCircle size={14} style={{ flexShrink: 0 }} />
              <span>Hỏi đáp Quy chế</span>
              <span style={{ fontSize: "0.625rem", backgroundColor: activeTab === "faq" ? "rgba(255,255,255,0.25)" : "#fef3c7", color: activeTab === "faq" ? "#fff" : "#92400e", padding: "0.1rem 0.35rem", borderRadius: "9999px", fontWeight: 700 }}>
                Trợ lý
              </span>
            </button>
          </div>
        </div>

        {/* Subtle Divider */}
        <div style={{ height: "1px", backgroundColor: "#e2e8f0" }} />

        {/* SUITE 2: BÁO CÁO THỐNG KÊ & QUẢN TRỊ CTSV */}
        <div>
          <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: "0.35rem", padding: "0 0.25rem" }}>
            <span style={{ fontSize: "0.6875rem", fontWeight: 800, color: "#0f766e", textTransform: "uppercase", letterSpacing: "0.05em", display: "flex", alignItems: "center", gap: "0.35rem" }}>
              <BarChart3 size={12} /> NHÓM 2: BÁO CÁO THỐNG KÊ & QUẢN TRỊ CTSV
            </span>
            <span style={{ fontSize: "0.6875rem", color: "#0f766e", fontWeight: 700 }}>Nghiệp vụ CTSV ĐH Đà Lạt</span>
          </div>

          <div
            style={{
              display: "grid",
              gridTemplateColumns: "repeat(auto-fit, minmax(170px, 1fr))",
              gap: "0.4rem",
            }}
          >

            {/* 7. ctsv_analytics */}
            <button
              type="button"
              onClick={() => {
                setActiveTab("ctsv_analytics");
                if (!ctsvBreakdown) handleLoadCtsvBreakdown();
              }}
              style={{
                display: "inline-flex",
                alignItems: "center",
                justifyContent: "center",
                gap: "0.4rem",
                padding: "0.55rem 0.65rem",
                borderRadius: "0.5rem",
                border: activeTab === "ctsv_analytics" ? "1px solid #2563eb" : "1px solid var(--gray-200)",
                backgroundColor: activeTab === "ctsv_analytics" ? "var(--primary-600)" : "#ffffff",
                color: activeTab === "ctsv_analytics" ? "#ffffff" : "var(--gray-700)",
                fontWeight: activeTab === "ctsv_analytics" ? 700 : 600,
                fontSize: "0.8125rem",
                cursor: "pointer",
                transition: "all 0.15s ease",
                boxShadow: activeTab === "ctsv_analytics" ? "0 2px 4px rgba(37,99,235,0.25)" : "none",
              }}
            >
              <BarChart3 size={14} style={{ flexShrink: 0 }} />
              <span>Thống kê CTSV</span>
              <span style={{ fontSize: "0.625rem", backgroundColor: activeTab === "ctsv_analytics" ? "rgba(255,255,255,0.25)" : "#fef3c7", color: activeTab === "ctsv_analytics" ? "#fff" : "#92400e", padding: "0.1rem 0.35rem", borderRadius: "9999px", fontWeight: 700 }}>
                Aggs
              </span>
            </button>

            {/* 8. ocr_quality */}
            <button
              type="button"
              onClick={() => {
                setActiveTab("ocr_quality");
                if (!ocrQualityData) handleLoadOcrQuality();
              }}
              style={{
                display: "inline-flex",
                alignItems: "center",
                justifyContent: "center",
                gap: "0.4rem",
                padding: "0.55rem 0.65rem",
                borderRadius: "0.5rem",
                border: activeTab === "ocr_quality" ? "1px solid #16a34a" : "1px solid var(--gray-200)",
                backgroundColor: activeTab === "ocr_quality" ? "#16a34a" : "#ffffff",
                color: activeTab === "ocr_quality" ? "#ffffff" : "var(--gray-700)",
                fontWeight: activeTab === "ocr_quality" ? 700 : 600,
                fontSize: "0.8125rem",
                cursor: "pointer",
                transition: "all 0.15s ease",
                boxShadow: activeTab === "ocr_quality" ? "0 2px 4px rgba(22,163,74,0.25)" : "none",
              }}
            >
              <Activity size={14} style={{ flexShrink: 0 }} />
              <span>Chất lượng OCR</span>
              <span style={{ fontSize: "0.625rem", backgroundColor: activeTab === "ocr_quality" ? "rgba(255,255,255,0.25)" : "#ecfdf5", color: activeTab === "ocr_quality" ? "#fff" : "#047857", padding: "0.1rem 0.35rem", borderRadius: "9999px", fontWeight: 700 }}>
                Queue
              </span>
            </button>

            {/* 9. pii */}
            <button
              type="button"
              onClick={() => {
                setActiveTab("pii");
                if (!piiData) handleLoadPiiAudit();
              }}
              style={{
                display: "inline-flex",
                alignItems: "center",
                justifyContent: "center",
                gap: "0.4rem",
                padding: "0.55rem 0.65rem",
                borderRadius: "0.5rem",
                border: activeTab === "pii" ? "1px solid #dc2626" : "1px solid var(--gray-200)",
                backgroundColor: activeTab === "pii" ? "#dc2626" : "#ffffff",
                color: activeTab === "pii" ? "#ffffff" : "var(--gray-700)",
                fontWeight: activeTab === "pii" ? 700 : 600,
                fontSize: "0.8125rem",
                cursor: "pointer",
                transition: "all 0.15s ease",
                boxShadow: activeTab === "pii" ? "0 2px 4px rgba(220,38,38,0.25)" : "none",
              }}
            >
              <ShieldAlert size={14} style={{ flexShrink: 0 }} />
              <span>Giám sát PII</span>
              <span style={{ fontSize: "0.625rem", backgroundColor: activeTab === "pii" ? "rgba(255,255,255,0.25)" : "#fee2e2", color: activeTab === "pii" ? "#fff" : "#991b1b", padding: "0.1rem 0.35rem", borderRadius: "9999px", fontWeight: 700 }}>
                NĐ 13
              </span>
            </button>

            {/* 10. realtime_watchers */}
            <button
              type="button"
              onClick={() => {
                setActiveTab("realtime_watchers");
                if (watchersList.length === 0) {
                  handleLoadWatchers();
                  handleVerifyGeoArea(geoAddressInput);
                }
              }}
              style={{
                display: "inline-flex",
                alignItems: "center",
                justifyContent: "center",
                gap: "0.4rem",
                padding: "0.55rem 0.65rem",
                borderRadius: "0.5rem",
                border: activeTab === "realtime_watchers" ? "1px solid #2563eb" : "1px solid var(--gray-200)",
                backgroundColor: activeTab === "realtime_watchers" ? "var(--primary-600)" : "#ffffff",
                color: activeTab === "realtime_watchers" ? "#ffffff" : "var(--gray-700)",
                fontWeight: activeTab === "realtime_watchers" ? 700 : 600,
                fontSize: "0.8125rem",
                cursor: "pointer",
                transition: "all 0.15s ease",
                boxShadow: activeTab === "realtime_watchers" ? "0 2px 4px rgba(37,99,235,0.25)" : "none",
              }}
            >
              <Bell size={14} style={{ flexShrink: 0 }} />
              <span>Cảnh báo Watchers</span>
              <span style={{ fontSize: "0.625rem", backgroundColor: activeTab === "realtime_watchers" ? "rgba(255,255,255,0.25)" : "#e0e7ff", color: activeTab === "realtime_watchers" ? "#fff" : "#1e40af", padding: "0.1rem 0.35rem", borderRadius: "9999px", fontWeight: 700 }}>
                Alerts
              </span>
            </button>
          </div>
        </div>
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
              {searchResponse.query ? (
                <>
                  Tìm thấy <strong style={{ color: "var(--gray-900)" }}>{searchResponse.total_hits}</strong> kết quả cho từ khóa "<strong>{searchResponse.query}</strong>" ({searchResponse.took_ms} ms)
                </>
              ) : (
                <>
                  Hiển thị <strong style={{ color: "var(--gray-900)" }}>{searchResponse.total_hits}</strong> văn bản và hồ sơ CTSV mới nhất ({searchResponse.took_ms} ms)
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
                      <span style={{ fontSize: "0.75rem", color: "var(--gray-400)" }}>
                        Độ phù hợp: <strong style={{ color: "var(--gray-600)" }}>{hit.score}</strong>
                      </span>
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
                        <User size={14} style={{ color: "var(--gray-400)" }} /> {hit.student_name}
                      </span>
                    )}
                    {hit.student_id && (
                      <span style={{ display: "flex", alignItems: "center", gap: "0.35rem" }}>
                        <GraduationCap size={14} style={{ color: "var(--gray-400)" }} /> MSSV: <strong style={{ color: "var(--gray-800)" }}>{hit.student_id}</strong>
                      </span>
                    )}
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

                  {/* 5. Card Bottom Action Bar: Dedicated, balanced, grouped actions */}
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
              background: "linear-gradient(135deg, #1e1b4b 0%, #312e81 50%, #4338ca 100%)",
              color: "#ffffff",
              borderRadius: "var(--radius-lg)",
            }}
          >
            <div style={{ maxWidth: "800px" }}>
              <div style={{ display: "inline-flex", alignItems: "center", gap: "0.5rem", padding: "0.25rem 0.75rem", borderRadius: "9999px", backgroundColor: "rgba(255,255,255,0.15)", fontSize: "0.75rem", fontWeight: 700, marginBottom: "0.75rem" }}>
                <Sparkles size={14} color="#facc15" />
                TRỢ LÝ PHÁP QUY & QUY CHẾ CTSV ĐẠI HỌC ĐÀ LẠT
              </div>
              <h2 style={{ fontSize: "1.6rem", fontWeight: 800, marginBottom: "0.5rem" }}>
                Hỏi đáp Quy chế bằng Ngôn ngữ Tự nhiên
              </h2>
              <p style={{ fontSize: "0.9375rem", color: "#c7d2fe", lineHeight: 1.6, marginBottom: "1.25rem" }}>
                Đặt bất kỳ câu hỏi nào về điều kiện xét học bổng, chính sách miễn giảm học phí theo Nghị định 81, điểm rèn luyện hoặc thủ tục tạm hoãn nghĩa vụ quân sự. Hệ thống tự động trích dẫn chính xác Điều/Khoản và cung cấp biểu mẫu hành chính tương ứng.
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
                  leftIcon={<Sparkles size={16} />}
                  style={{ backgroundColor: "#f59e0b", color: "#1e1b4b", fontWeight: 700, border: "none" }}
                >
                  Hỏi đáp Quy chế
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
      {/* FEATURE 4 TAB: NESTED TABLE STRUCTURED SEARCH                        */}
      {/* ==================================================================== */}
      {activeTab === "tables" && (
        <div style={{ display: "flex", flexDirection: "column", gap: "1.25rem" }}>
          {/* Filter Card */}
          <Card padding="md">
            <div style={{ marginBottom: "0.75rem" }}>
              <h3 style={{ fontSize: "1.1rem", fontWeight: 700, color: "var(--gray-900)" }}>
                Tra cứu Bảng biểu Quyết định & Phụ lục Học bổng Đa trang
              </h3>
              <p style={{ fontSize: "0.8125rem", color: "var(--gray-500)", marginTop: "0.15rem" }}>
                Tìm kiếm trực tiếp từng dòng dữ liệu trong phụ lục scan quyết định khen thưởng, miễn giảm học phí và học bổng KKHT.
              </p>
            </div>

            <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(180px, 1fr))", gap: "0.75rem", alignItems: "flex-end" }}>
              <div>
                <label style={{ fontSize: "0.75rem", fontWeight: 600, color: "var(--gray-700)", display: "block", marginBottom: "0.25rem" }}>
                  Mã số SV (MSSV)
                </label>
                <input
                  type="text"
                  value={tableStudentId}
                  onChange={(e) => setTableStudentId(e.target.value)}
                  placeholder="vd: 2112345..."
                  style={{ width: "100%", padding: "0.45rem 0.65rem", borderRadius: "var(--radius-sm)", border: "1px solid var(--border-color)", fontSize: "0.8125rem" }}
                />
              </div>

              <div>
                <label style={{ fontSize: "0.75rem", fontWeight: 600, color: "var(--gray-700)", display: "block", marginBottom: "0.25rem" }}>
                  Họ và tên
                </label>
                <input
                  type="text"
                  value={tableStudentName}
                  onChange={(e) => setTableStudentName(e.target.value)}
                  placeholder="vd: Nguyễn Văn..."
                  style={{ width: "100%", padding: "0.45rem 0.65rem", borderRadius: "var(--radius-sm)", border: "1px solid var(--border-color)", fontSize: "0.8125rem" }}
                />
              </div>

              <div>
                <label style={{ fontSize: "0.75rem", fontWeight: 600, color: "var(--gray-700)", display: "block", marginBottom: "0.25rem" }}>
                  GPA Tối thiểu
                </label>
                <select
                  value={tableMinGpa}
                  onChange={(e) => setTableMinGpa(e.target.value)}
                  style={{ width: "100%", padding: "0.45rem 0.65rem", borderRadius: "var(--radius-sm)", border: "1px solid var(--border-color)", fontSize: "0.8125rem" }}
                >
                  <option value="">Tất cả khoảng điểm</option>
                  <option value="2.5">Từ 2.50 trở lên (Khá)</option>
                  <option value="3.2">Từ 3.20 trở lên (Giỏi)</option>
                  <option value="3.6">Từ 3.60 trở lên (Xuất sắc)</option>
                </select>
              </div>

              <div>
                <label style={{ fontSize: "0.75rem", fontWeight: 600, color: "var(--gray-700)", display: "block", marginBottom: "0.25rem" }}>
                  Điểm Rèn luyện Tối thiểu
                </label>
                <select
                  value={tableMinDrl}
                  onChange={(e) => setTableMinDrl(e.target.value)}
                  style={{ width: "100%", padding: "0.45rem 0.65rem", borderRadius: "var(--radius-sm)", border: "1px solid var(--border-color)", fontSize: "0.8125rem" }}
                >
                  <option value="">Tất cả ĐRL</option>
                  <option value="65">Từ 65 điểm trở lên (Khá)</option>
                  <option value="80">Từ 80 điểm trở lên (Tốt)</option>
                  <option value="90">Từ 90 điểm trở lên (Xuất sắc)</option>
                </select>
              </div>

              <div>
                <label style={{ fontSize: "0.75rem", fontWeight: 600, color: "var(--gray-700)", display: "block", marginBottom: "0.25rem" }}>
                  Khung học bổng
                </label>
                <select
                  value={tableTier}
                  onChange={(e) => setTableTier(e.target.value)}
                  style={{ width: "100%", padding: "0.45rem 0.65rem", borderRadius: "var(--radius-sm)", border: "1px solid var(--border-color)", fontSize: "0.8125rem" }}
                >
                  <option value="">Tất cả loại học bổng</option>
                  <option value="Xuất sắc">Loại Xuất sắc</option>
                  <option value="Giỏi">Loại Giỏi</option>
                  <option value="Khá">Loại Khá</option>
                </select>
              </div>

              <Button
                type="button"
                variant="primary"
                isLoading={isTableLoading}
                leftIcon={<TableIcon size={15} />}
                onClick={handleQueryTables}
                style={{ height: "35px" }}
              >
                Truy vấn Bảng
              </Button>
            </div>
          </Card>

          {/* Results Table Card */}
          <Card padding="md">
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "0.75rem" }}>
              <span style={{ fontSize: "0.875rem", fontWeight: 700, color: "var(--gray-800)" }}>
                Kết quả tìm kiếm bảng biểu:{" "}
                <strong style={{ color: "var(--primary-600)" }}>{tableResult?.total_hits ?? 0}</strong> dòng ({tableResult?.took_ms ?? 0} ms)
              </span>
            </div>

            <div style={{ overflowX: "auto" }}>
              <table style={{ width: "100%", borderCollapse: "collapse", fontSize: "0.8125rem" }}>
                <thead>
                  <tr style={{ backgroundColor: "var(--gray-50)", borderBottom: "2px solid var(--border-color)", textAlign: "left" }}>
                    <th style={{ padding: "0.6rem 0.75rem", color: "var(--gray-700)", fontWeight: 700 }}>Trang</th>
                    <th style={{ padding: "0.6rem 0.75rem", color: "var(--gray-700)", fontWeight: 700 }}>Số Quyết định / Văn bản</th>
                    <th style={{ padding: "0.6rem 0.75rem", color: "var(--gray-700)", fontWeight: 700 }}>MSSV</th>
                    <th style={{ padding: "0.6rem 0.75rem", color: "var(--gray-700)", fontWeight: 700 }}>Họ và tên</th>
                    <th style={{ padding: "0.6rem 0.75rem", color: "var(--gray-700)", fontWeight: 700 }}>Lớp</th>
                    <th style={{ padding: "0.6rem 0.75rem", color: "var(--gray-700)", fontWeight: 700 }}>GPA</th>
                    <th style={{ padding: "0.6rem 0.75rem", color: "var(--gray-700)", fontWeight: 700 }}>ĐRL</th>
                    <th style={{ padding: "0.6rem 0.75rem", color: "var(--gray-700)", fontWeight: 700 }}>Khung học bổng</th>
                    <th style={{ padding: "0.6rem 0.75rem", color: "var(--gray-700)", fontWeight: 700 }}>Mức tiền thưởng</th>
                    <th style={{ padding: "0.6rem 0.75rem", color: "var(--gray-700)", fontWeight: 700 }}>Hồ sơ gốc</th>
                  </tr>
                </thead>
                <tbody>
                  {!tableResult || tableResult.rows.length === 0 ? (
                    <tr>
                      <td colSpan={10} style={{ padding: "2rem", textAlign: "center", color: "var(--gray-400)" }}>
                        Không có dòng dữ liệu bảng biểu nào khớp với tiêu chí tìm kiếm.
                      </td>
                    </tr>
                  ) : (
                    tableResult.rows.map((row, idx) => (
                      <tr
                        key={idx}
                        style={{
                          borderBottom: "1px solid var(--gray-100)",
                          backgroundColor: idx % 2 === 0 ? "#ffffff" : "var(--gray-50)",
                        }}
                      >
                        <td style={{ padding: "0.6rem 0.75rem", fontWeight: 600 }}>Trang {row.page}</td>
                        <td style={{ padding: "0.6rem 0.75rem", color: "var(--gray-800)", maxWidth: "200px", overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }} title={row.document_title}>
                          {row.decision_number || formatDisplayTitle(row.document_title).code || row.document_title}
                        </td>
                        <td style={{ padding: "0.6rem 0.75rem", fontWeight: 700, color: "var(--primary-700)" }}>{row.mssv}</td>
                        <td style={{ padding: "0.6rem 0.75rem", fontWeight: 600, color: "var(--gray-900)" }}>{row.student_name}</td>
                        <td style={{ padding: "0.6rem 0.75rem", color: "var(--gray-600)" }}>{row.class_name || "CTK45"}</td>
                        <td style={{ padding: "0.6rem 0.75rem", fontWeight: 700, color: (row.gpa ?? 0) >= 3.6 ? "#15803d" : "#0284c7" }}>
                          {row.gpa?.toFixed(2) ?? "N/A"}
                        </td>
                        <td style={{ padding: "0.6rem 0.75rem", fontWeight: 600 }}>{row.drl ?? "N/A"}</td>
                        <td style={{ padding: "0.6rem 0.75rem" }}>
                          <span
                            style={{
                              padding: "0.2rem 0.5rem",
                              borderRadius: "4px",
                              fontSize: "0.75rem",
                              fontWeight: 700,
                              backgroundColor: row.scholarship_tier?.includes("Xuất sắc") ? "#ede9fe" : "#e0f2fe",
                              color: row.scholarship_tier?.includes("Xuất sắc") ? "#6d28d9" : "#0369a1",
                            }}
                          >
                            {row.scholarship_tier || "Đạt chuẩn"}
                          </span>
                        </td>
                        <td style={{ padding: "0.6rem 0.75rem", fontWeight: 700, color: "#b45309" }}>{row.amount || "Theo quy định"}</td>
                        <td style={{ padding: "0.6rem 0.75rem" }}>
                          <Link to={`/documents/${row.document_id}`} style={{ textDecoration: "none" }}>
                            <Button variant="ghost" size="sm" style={{ padding: "0.2rem 0.4rem", fontSize: "0.75rem" }}>
                              Xem file
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
        </div>
      )}

      {/* ==================================================================== */}
      {/* FEATURE 5 TAB: PII SECURITY AUDIT & ANOMALY SIEM                     */}
      {/* ==================================================================== */}
      {activeTab === "pii" && (
        <div style={{ display: "flex", flexDirection: "column", gap: "1.25rem" }}>
          {/* Header Controls */}
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", flexWrap: "wrap", gap: "0.75rem" }}>
            <div>
              <h3 style={{ fontSize: "1.2rem", fontWeight: 800, color: "var(--gray-900)" }}>
                Giám sát An toàn Thông tin Cá nhân Sinh viên (Nghị định 13/2023/NĐ-CP SIEM)
              </h3>
              <p style={{ fontSize: "0.8125rem", color: "var(--gray-500)", marginTop: "0.15rem" }}>
                Giám sát việc truy xuất số CCCD, tài khoản ngân hàng, thông tin sổ hộ nghèo; phát hiện tải hàng loạt và truy cập ngoài giờ.
              </p>
            </div>

            <div style={{ display: "flex", gap: "0.5rem", alignItems: "center" }}>
              <span style={{ fontSize: "0.75rem", fontWeight: 600, color: "var(--gray-600)" }}>Cửa sổ giám sát:</span>
              <select
                value={piiWindow}
                onChange={(e) => {
                  const val = parseInt(e.target.value, 10);
                  setPiiWindow(val);
                  handleLoadPiiAudit(val);
                }}
                style={{ padding: "0.4rem 0.75rem", borderRadius: "var(--radius-sm)", border: "1px solid var(--border-color)", fontSize: "0.8125rem", fontWeight: 600 }}
              >
                <option value={30}>30 phút qua</option>
                <option value={60}>60 phút qua (1 giờ)</option>
                <option value={180}>3 giờ qua</option>
                <option value={1440}>24 giờ qua (1 ngày)</option>
              </select>
              <Button variant="outline" size="sm" onClick={() => handleLoadPiiAudit(piiWindow)} leftIcon={<RotateCcw size={14} />}>
                Làm mới
              </Button>
            </div>
          </div>

          {/* Metric KPIs */}
          <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))", gap: "1rem" }}>
            <Card padding="md" style={{ borderLeft: "4px solid #3b82f6" }}>
              <span style={{ fontSize: "0.75rem", fontWeight: 600, color: "var(--gray-500)" }}>TỔNG LƯỢT TRUY XUẤT PII</span>
              <div style={{ fontSize: "1.75rem", fontWeight: 800, color: "var(--gray-900)", marginTop: "0.25rem" }}>
                {piiData?.total_pii_accesses ?? 12}
              </div>
              <span style={{ fontSize: "0.75rem", color: "#2563eb", fontWeight: 600 }}>Theo dõi tức thời</span>
            </Card>

            <Card padding="md" style={{ borderLeft: "4px solid #10b981" }}>
              <span style={{ fontSize: "0.75rem", fontWeight: 600, color: "var(--gray-500)" }}>HỒ SƠ SINH VIÊN ĐÃ MỞ</span>
              <div style={{ fontSize: "1.75rem", fontWeight: 800, color: "var(--gray-900)", marginTop: "0.25rem" }}>
                {piiData?.unique_documents_accessed ?? 5}
              </div>
              <span style={{ fontSize: "0.75rem", color: "#059669", fontWeight: 600 }}>Hồ sơ chính sách, học bổng</span>
            </Card>

            <Card padding="md" style={{ borderLeft: "4px solid #ef4444" }}>
              <span style={{ fontSize: "0.75rem", fontWeight: 600, color: "var(--gray-500)" }}>CẢNH BÁO BẤT THƯỜNG</span>
              <div style={{ fontSize: "1.75rem", fontWeight: 800, color: "#dc2626", marginTop: "0.25rem" }}>
                {piiData?.anomalies.length ?? 0}
              </div>
              <span style={{ fontSize: "0.75rem", color: "#dc2626", fontWeight: 600 }}>Cần thẩm tra an ninh</span>
            </Card>

            <Card padding="md" style={{ borderLeft: "4px solid #8b5cf6" }}>
              <span style={{ fontSize: "0.75rem", fontWeight: 600, color: "var(--gray-500)" }}>TUÂN THỦ NGHỊ ĐỊNH 13</span>
              <div style={{ fontSize: "1.75rem", fontWeight: 800, color: "#7c3aed", marginTop: "0.25rem" }}>
                100%
              </div>
              <span style={{ fontSize: "0.75rem", color: "#7c3aed", fontWeight: 600 }}>Đã mã hóa và ghi nhật ký</span>
            </Card>
          </div>

          {/* Anomaly Alerts List */}
          {piiData && piiData.anomalies.length > 0 && (
            <Card padding="md" style={{ border: "1px solid #fecaca", backgroundColor: "#fff5f5" }}>
              <div style={{ display: "flex", alignItems: "center", gap: "0.5rem", marginBottom: "0.75rem" }}>
                <AlertTriangle size={18} color="#dc2626" />
                <h4 style={{ fontSize: "0.9375rem", fontWeight: 700, color: "#991b1b" }}>
                  Phát hiện Cảnh báo Hành vi Bất thường (Anomalies Alert):
                </h4>
              </div>
              <div style={{ display: "flex", flexDirection: "column", gap: "0.6rem" }}>
                {piiData.anomalies.map((alt) => (
                  <div
                    key={alt.alert_id}
                    style={{
                      padding: "0.75rem 1rem",
                      borderRadius: "var(--radius-sm)",
                      backgroundColor: "#ffffff",
                      border: "1px solid #fee2e2",
                      display: "flex",
                      justifyContent: "space-between",
                      alignItems: "center",
                      gap: "1rem",
                    }}
                  >
                    <div>
                      <div style={{ display: "flex", alignItems: "center", gap: "0.5rem" }}>
                        <span
                          style={{
                            padding: "0.15rem 0.45rem",
                            borderRadius: "4px",
                            fontSize: "0.6875rem",
                            fontWeight: 700,
                            backgroundColor: alt.severity === "CRITICAL" ? "#dc2626" : alt.severity === "HIGH" ? "#f97316" : "#eab308",
                            color: "#ffffff",
                          }}
                        >
                          {alt.severity}
                        </span>
                        <strong style={{ fontSize: "0.8125rem", color: "var(--gray-900)" }}>{alt.alert_id}</strong>
                        <span style={{ fontSize: "0.75rem", color: "var(--gray-500)" }}>Tài khoản: {alt.user_email}</span>
                      </div>
                      <p style={{ fontSize: "0.8125rem", color: "var(--gray-700)", marginTop: "0.25rem" }}>
                        {alt.description}
                      </p>
                    </div>
                    <span style={{ fontSize: "0.75rem", color: "var(--gray-400)", whiteSpace: "nowrap" }}>{alt.created_at}</span>
                  </div>
                ))}
              </div>
            </Card>
          )}

          {/* Recent Access Stream */}
          <Card padding="md">
            <h4 style={{ fontSize: "0.9375rem", fontWeight: 700, color: "var(--gray-900)", marginBottom: "0.75rem" }}>
              Nhật ký Truy xuất Dữ liệu Nhạy cảm Thời gian thực (Audit Trail)
            </h4>
            <div style={{ overflowX: "auto" }}>
              <table style={{ width: "100%", borderCollapse: "collapse", fontSize: "0.8125rem" }}>
                <thead>
                  <tr style={{ backgroundColor: "var(--gray-50)", borderBottom: "1px solid var(--border-color)", textAlign: "left" }}>
                    <th style={{ padding: "0.6rem 0.75rem", color: "var(--gray-700)", fontWeight: 700 }}>Thời gian</th>
                    <th style={{ padding: "0.6rem 0.75rem", color: "var(--gray-700)", fontWeight: 700 }}>Tài khoản Cán bộ</th>
                    <th style={{ padding: "0.6rem 0.75rem", color: "var(--gray-700)", fontWeight: 700 }}>Hành động</th>
                    <th style={{ padding: "0.6rem 0.75rem", color: "var(--gray-700)", fontWeight: 700 }}>Mã Hồ sơ</th>
                    <th style={{ padding: "0.6rem 0.75rem", color: "var(--gray-700)", fontWeight: 700 }}>Trường PII đã đọc/tải</th>
                  </tr>
                </thead>
                <tbody>
                  {!piiData || piiData.recent_accesses.length === 0 ? (
                    <tr>
                      <td colSpan={5} style={{ padding: "1.5rem", textAlign: "center", color: "var(--gray-400)" }}>
                        Chưa có nhật ký truy xuất PII trong cửa sổ thời gian này.
                      </td>
                    </tr>
                  ) : (
                    piiData.recent_accesses.map((acc) => (
                      <tr key={acc.id} style={{ borderBottom: "1px solid var(--gray-100)" }}>
                        <td style={{ padding: "0.6rem 0.75rem", color: "var(--gray-600)" }}>{acc.timestamp}</td>
                        <td style={{ padding: "0.6rem 0.75rem", fontWeight: 600, color: "var(--gray-900)" }}>{acc.user_email}</td>
                        <td style={{ padding: "0.6rem 0.75rem" }}>
                          <span
                            style={{
                              padding: "0.15rem 0.45rem",
                              borderRadius: "4px",
                              fontSize: "0.6875rem",
                              fontWeight: 700,
                              backgroundColor: acc.action === "EXPORT" ? "#fef3c7" : acc.action === "DOWNLOAD" ? "#e0f2fe" : "#f3f4f6",
                              color: acc.action === "EXPORT" ? "#b45309" : acc.action === "DOWNLOAD" ? "#0284c7" : "#4b5563",
                            }}
                          >
                            {acc.action}
                          </span>
                        </td>
                        <td style={{ padding: "0.6rem 0.75rem", fontFamily: "monospace", fontSize: "0.75rem", color: "var(--primary-700)" }}>
                          {acc.document_id.slice(0, 8)}...
                        </td>
                        <td style={{ padding: "0.6rem 0.75rem" }}>
                          <div style={{ display: "flex", gap: "0.35rem", flexWrap: "wrap" }}>
                            {acc.accessed_fields.map((fld, fIdx) => (
                              <span key={fIdx} style={{ fontSize: "0.6875rem", backgroundColor: "#fef2f2", color: "#991b1b", border: "1px solid #fecaca", padding: "0.1rem 0.4rem", borderRadius: "3px" }}>
                                {fld}
                              </span>
                            ))}
                          </div>
                        </td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>
          </Card>
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
                Khai phá dữ liệu tổng hợp đa tầng của Elasticsearch 8: Phân tích cơ cấu chính sách, phân bổ hồ sơ theo từng Khoa, tiến độ giải ngân ngân sách và cam kết chất lượng SLA.
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
                  <span style={{ fontSize: "0.75rem", fontWeight: 700, color: "var(--gray-500)", textTransform: "uppercase" }}>Tổng Ngân sách Cấp bù</span>
                  <div style={{ fontSize: "1.75rem", fontWeight: 800, color: "#b45309", marginTop: "0.25rem" }}>
                    {(ctsvBreakdown.total_budget_allocated / 1000000000).toFixed(2)} tỷ VNĐ
                  </div>
                  <span style={{ fontSize: "0.75rem", color: "var(--gray-600)" }}>Nghị định 81, KKHT & Trợ cấp XH</span>
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
                          <th style={{ padding: "0.5rem 0.6rem", color: "var(--gray-700)", textAlign: "right" }}>Kinh phí (VNĐ)</th>
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
                              <td style={{ padding: "0.55rem 0.6rem", textAlign: "right", fontFamily: "monospace", fontWeight: 700 }}>
                                {f.budget_disbursed.toLocaleString()}
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
      {/* TAB 6: TRA CỨU BÙ LỖI OCR & TỪ VIẾT TẮT CTSV (FUZZY & N-GRAM)         */}
      {/* ==================================================================== */}
      {activeTab === "ocr_tolerant" && (
        <div style={{ display: "flex", flexDirection: "column", gap: "1.25rem" }}>
          <Card padding="md">
            <div>
              <h3 style={{ fontSize: "1.15rem", fontWeight: 800, color: "var(--gray-900)" }}>
                Tra cứu Bao dung Lỗi OCR & Mở rộng Từ viết tắt Tiếng Việt
              </h3>
              <p style={{ fontSize: "0.8125rem", color: "var(--gray-500)", marginTop: "0.2rem" }}>
                Khắc phục triệt để sai sót của bản scan OCR: Tự động sửa nhầm lẫn ký tự số/chữ (0/O, 1/l), phục hồi dấu tiếng Việt mờ nhòe và mở rộng từ viết tắt hồ sơ CTSV (hb, kkht, mghp, tcxh, drl, ktx).
              </p>
            </div>

            {/* Input Form */}
            <div style={{ display: "flex", gap: "0.5rem", marginTop: "1rem" }}>
              <input
                type="text"
                value={ocrTolerantInput}
                onChange={(e) => setOcrTolerantInput(e.target.value)}
                onKeyDown={(e) => e.key === "Enter" && handleSearchOcrTolerant(ocrTolerantInput)}
                placeholder="Nhập từ khóa có lỗi OCR hoặc viết tắt (vd: don xin hb kkht sv 2O21)..."
                style={{
                  flex: 1,
                  padding: "0.6rem 0.85rem",
                  borderRadius: "var(--radius-md)",
                  border: "2px solid var(--primary-400)",
                  fontSize: "0.875rem",
                }}
              />
              <Button
                type="button"
                variant="primary"
                leftIcon={<Zap size={16} className={isOcrTolerantLoading ? "animate-spin" : ""} />}
                onClick={() => handleSearchOcrTolerant(ocrTolerantInput)}
                disabled={isOcrTolerantLoading}
              >
                {isOcrTolerantLoading ? "Đang xử lý..." : "Tra cứu Bù lỗi OCR"}
              </Button>
            </div>

            {/* Suggestion Chips */}
            <div style={{ display: "flex", alignItems: "center", gap: "0.4rem", marginTop: "0.75rem", flexWrap: "wrap" }}>
              <span style={{ fontSize: "0.75rem", color: "var(--gray-500)" }}>Gợi ý mẫu thử:</span>
              {[
                "don xin hb kkht sv 2O21",
                "mghp mien giam hp sv",
                "tro cap xh tcxh dlu",
                "sinh hoat ktx noi tru sv",
              ].map((chip, idx) => (
                <button
                  key={idx}
                  type="button"
                  onClick={() => {
                    setOcrTolerantInput(chip);
                    handleSearchOcrTolerant(chip);
                  }}
                  style={{
                    padding: "0.2rem 0.5rem",
                    borderRadius: "9999px",
                    border: "1px solid var(--primary-200)",
                    backgroundColor: "#eef2ff",
                    color: "var(--primary-700)",
                    fontSize: "0.75rem",
                    cursor: "pointer",
                  }}
                >
                  {chip}
                </button>
              ))}
            </div>
          </Card>

          {/* Normalization & Results */}
          {ocrTolerantData && (
            <div style={{ display: "flex", flexDirection: "column", gap: "1rem" }}>
              {/* Normalization Banner */}
              <div
                style={{
                  padding: "1rem 1.25rem",
                  borderRadius: "var(--radius-md)",
                  backgroundColor: "#f0fdf4",
                  border: "1px solid #bbf7d0",
                  display: "flex",
                  flexDirection: "column",
                  gap: "0.5rem",
                }}
              >
                <div style={{ display: "flex", alignItems: "center", gap: "0.5rem" }}>
                  <CheckCircle2 size={18} color="#16a34a" />
                  <span style={{ fontSize: "0.8125rem", fontWeight: 700, color: "#166534" }}>
                    KẾT QUẢ NẮN CHỈNH & PHỤC HỒI NGỮ NGHĨA ELASTICSEARCH:
                  </span>
                </div>
                <div style={{ fontSize: "0.875rem", color: "var(--gray-800)" }}>
                  Truy vấn gốc: <code style={{ backgroundColor: "#fee2e2", color: "#991b1b", padding: "0.15rem 0.4rem", borderRadius: "3px" }}>{ocrTolerantData.query}</code>
                  {" ➔ "}
                  Truy vấn nắn chỉnh: <strong style={{ color: "#15803d" }}>"{ocrTolerantData.normalized_query}"</strong>
                </div>

                {/* Badges for each corrected term */}
                {ocrTolerantData.suggested_corrections.length > 0 && (
                  <div style={{ display: "flex", gap: "0.5rem", flexWrap: "wrap", marginTop: "0.25rem" }}>
                    {ocrTolerantData.suggested_corrections.map((sc, scIdx) => (
                      <span
                        key={scIdx}
                        style={{
                          fontSize: "0.75rem",
                          padding: "0.2rem 0.6rem",
                          borderRadius: "4px",
                          backgroundColor: "#dcfce7",
                          color: "#166534",
                          border: "1px solid #86efac",
                        }}
                      >
                        <strong>{sc.original_term}</strong> ➔ <em>{sc.corrected_term}</em> ({sc.reason})
                      </span>
                    ))}
                  </div>
                )}
              </div>

              {/* Matched Hits */}
              <div>
                <h4 style={{ fontSize: "0.9375rem", fontWeight: 700, color: "var(--gray-900)", marginBottom: "0.75rem" }}>
                  Tài liệu Khớp sau khi Bù lỗi OCR ({ocrTolerantData.total} kết quả):
                </h4>
                {ocrTolerantData.results.length === 0 ? (
                  <Card padding="md">
                    <p style={{ textAlign: "center", color: "var(--gray-500)", margin: 0 }}>
                      Không tìm thấy văn bản phù hợp sau khi nắn chỉnh truy vấn.
                    </p>
                  </Card>
                ) : (
                  <div style={{ display: "flex", flexDirection: "column", gap: "0.75rem" }}>
                    {ocrTolerantData.results.map((hit) => (
                      <Card key={hit.document_id} padding="md">
                        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", gap: "1rem" }}>
                          <div style={{ flex: 1 }}>
                            <h4 style={{ fontSize: "1rem", fontWeight: 700, color: "var(--gray-900)", margin: 0 }}>
                              <Link to={`/documents/${hit.document_id}`} style={{ color: "var(--primary-700)", textDecoration: "none" }}>
                                {formatDisplayTitle(hit.title).mainTitle}
                              </Link>
                            </h4>
                            <div style={{ display: "flex", gap: "1rem", fontSize: "0.75rem", color: "var(--gray-500)", marginTop: "0.3rem" }}>
                              {hit.student_name && <span>Họ tên: {hit.student_name}</span>}
                              {hit.student_id && <span>MSSV: {hit.student_id}</span>}
                              <span>Điểm liên quan BM25: <strong>{hit.score.toFixed(2)}</strong></span>
                            </div>
                            {hit.content_snippet && (
                              <div
                                style={{
                                  marginTop: "0.5rem",
                                  padding: "0.5rem 0.75rem",
                                  backgroundColor: "var(--gray-50)",
                                  borderRadius: "4px",
                                  fontSize: "0.8125rem",
                                  color: "var(--gray-700)",
                                  lineHeight: 1.5,
                                }}
                                dangerouslySetInnerHTML={{ __html: hit.content_snippet }}
                              />
                            )}
                          </div>
                          <Link to={`/documents/${hit.document_id}`}>
                            <Button variant="outline" size="sm" rightIcon={<ArrowRight size={14} />}>
                              Xem chi tiết
                            </Button>
                          </Link>
                        </div>
                      </Card>
                    ))}
                  </div>
                )}
              </div>
            </div>
          )}
        </div>
      )}

      {/* ==================================================================== */}
      {/* TAB 7: CHẤT LƯỢNG SCAN OCR & HÀNG ĐỢI HIỆU ĐÍNH (HUMAN-IN-THE-LOOP)  */}
      {/* ==================================================================== */}
      {activeTab === "ocr_quality" && (
        <div style={{ display: "flex", flexDirection: "column", gap: "1.25rem" }}>
          {/* Header Card */}
          <Card padding="md">
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", flexWrap: "wrap", gap: "1rem" }}>
              <div style={{ display: "flex", alignItems: "center", gap: "0.75rem" }}>
                <div style={{ padding: "0.6rem", borderRadius: "var(--radius-md)", backgroundColor: "#ecfdf5", color: "#059669" }}>
                  <Activity size={24} />
                </div>
                <div>
                  <h3 style={{ fontSize: "1.125rem", fontWeight: 700, color: "var(--gray-900)", margin: 0 }}>
                    Kiểm định Chất lượng Nhận dạng OCR & Hàng đợi Hiệu đính
                  </h3>
                  <p style={{ fontSize: "0.8125rem", color: "var(--gray-500)", margin: 0, marginTop: "0.2rem" }}>
                    Phân tích điểm số tin cậy (Confidence Score), phát hiện văn bản scan xiên/mờ và điều hướng vào hàng đợi rà soát Human-in-the-Loop.
                  </p>
                </div>
              </div>
              <Button
                type="button"
                variant="outline"
                size="sm"
                leftIcon={<RotateCcw size={14} />}
                onClick={handleLoadOcrQuality}
                disabled={isQualityLoading}
              >
                {isQualityLoading ? "Đang tải dữ liệu..." : "Cập nhật Thống kê"}
              </Button>
            </div>
          </Card>

          {/* 4 KPI Cards */}
          {ocrQualityData && (
            <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(210px, 1fr))", gap: "1rem" }}>
              <div style={{ padding: "1rem", borderRadius: "var(--radius-md)", backgroundColor: "#f0fdf4", border: "1px solid #bbf7d0" }}>
                <span style={{ fontSize: "0.75rem", fontWeight: 700, color: "#166534", textTransform: "uppercase" }}>TỔNG BẢN SCAN ĐÃ SỐ HÓA</span>
                <div style={{ fontSize: "1.75rem", fontWeight: 800, color: "#15803d", marginTop: "0.25rem" }}>
                  {ocrQualityData.total_scanned_documents.toLocaleString()}
                </div>
                <span style={{ fontSize: "0.75rem", color: "#166534" }}>Tài liệu trong kho lưu trữ</span>
              </div>
              <div style={{ padding: "1rem", borderRadius: "var(--radius-md)", backgroundColor: "#eff6ff", border: "1px solid #bfdbfe" }}>
                <span style={{ fontSize: "0.75rem", fontWeight: 700, color: "#1e40af", textTransform: "uppercase" }}>ĐỘ TIN CẬY TRUNG BÌNH</span>
                <div style={{ fontSize: "1.75rem", fontWeight: 800, color: "#2563eb", marginTop: "0.25rem" }}>
                  {Math.round(ocrQualityData.avg_confidence * 100)}%
                </div>
                <span style={{ fontSize: "0.75rem", color: "#1e40af" }}>Chất lượng nhận dạng tiếng Việt</span>
              </div>
              <div style={{ padding: "1rem", borderRadius: "var(--radius-md)", backgroundColor: "#fef3c7", border: "1px solid #fde68a" }}>
                <span style={{ fontSize: "0.75rem", fontWeight: 700, color: "#92400e", textTransform: "uppercase" }}>CẦN HIỆU ĐÍNH THỦ CÔNG</span>
                <div style={{ fontSize: "1.75rem", fontWeight: 800, color: "#d97706", marginTop: "0.25rem" }}>
                  {ocrQualityData.review_needed_count + ocrQualityData.poor_count}
                </div>
                <span style={{ fontSize: "0.75rem", color: "#92400e" }}>Bản scan có độ tin cậy &lt; 75%</span>
              </div>
              <div style={{ padding: "1rem", borderRadius: "var(--radius-md)", backgroundColor: "#fdf2f8", border: "1px solid #fbcfe8" }}>
                <span style={{ fontSize: "0.75rem", fontWeight: 700, color: "#9d174d", textTransform: "uppercase" }}>BẢN SCAN XIÊN GÓC</span>
                <div style={{ fontSize: "1.75rem", fontWeight: 800, color: "#db2777", marginTop: "0.25rem" }}>
                  {ocrQualityData.skewed_count}
                </div>
                <span style={{ fontSize: "0.75rem", color: "#9d174d" }}>Góc nghiêng &gt; 2.0 độ cần nắn chỉnh</span>
              </div>
            </div>
          )}

          {/* Distribution Ranges */}
          {ocrQualityData && (
            <Card padding="md">
              <h4 style={{ fontSize: "0.9375rem", fontWeight: 700, color: "var(--gray-900)", marginBottom: "0.75rem" }}>
                Phân bổ Dải Độ tin cậy OCR (Range Aggregations):
              </h4>
              <div style={{ display: "flex", flexDirection: "column", gap: "0.75rem" }}>
                {ocrQualityData.distribution.map((b, bIdx) => (
                  <div key={bIdx}>
                    <div style={{ display: "flex", justifyContent: "space-between", fontSize: "0.8125rem", marginBottom: "0.25rem" }}>
                      <span style={{ fontWeight: 600, color: "var(--gray-800)" }}>{b.range_label}</span>
                      <span style={{ color: "var(--gray-500)" }}>
                        <strong>{b.doc_count}</strong> tài liệu ({b.percentage}%) — <em>{b.action_needed}</em>
                      </span>
                    </div>
                    <div style={{ height: "8px", borderRadius: "4px", backgroundColor: "#e2e8f0", overflow: "hidden" }}>
                      <div
                        style={{
                          height: "100%",
                          width: `${Math.min(b.percentage, 100)}%`,
                          backgroundColor: bIdx === 0 ? "#10b981" : bIdx === 1 ? "#3b82f6" : bIdx === 2 ? "#f59e0b" : "#ef4444",
                          borderRadius: "4px",
                          transition: "width 0.4s ease",
                        }}
                      />
                    </div>
                  </div>
                ))}
              </div>
            </Card>
          )}

          {/* Review Queue Table */}
          {reviewQueueData && (
            <Card padding="md">
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "0.75rem" }}>
                <h4 style={{ fontSize: "0.9375rem", fontWeight: 700, color: "var(--gray-900)", margin: 0 }}>
                  Hàng đợi Rà soát & Hiệu đính Thủ công ({reviewQueueData.total_items} tài liệu):
                </h4>
                <span style={{ fontSize: "0.75rem", color: "var(--gray-500)" }}>
                  Ưu tiên xử lý tài liệu mức khẩn cấp (URGENT / HIGH)
                </span>
              </div>
              <div style={{ overflowX: "auto" }}>
                <table style={{ width: "100%", borderCollapse: "collapse", fontSize: "0.8125rem" }}>
                  <thead>
                    <tr style={{ backgroundColor: "#f8fafc", borderBottom: "2px solid #e2e8f0", textAlign: "left" }}>
                      <th style={{ padding: "0.6rem 0.75rem", fontWeight: 700, color: "var(--gray-700)" }}>Văn bản & Số hiệu</th>
                      <th style={{ padding: "0.6rem 0.75rem", fontWeight: 700, color: "var(--gray-700)" }}>Sinh viên nộp</th>
                      <th style={{ padding: "0.6rem 0.75rem", fontWeight: 700, color: "var(--gray-700)" }}>Độ tin cậy OCR</th>
                      <th style={{ padding: "0.6rem 0.75rem", fontWeight: 700, color: "var(--gray-700)" }}>Góc nghiêng</th>
                      <th style={{ padding: "0.6rem 0.75rem", fontWeight: 700, color: "var(--gray-700)" }}>Từ mờ/nghi vấn</th>
                      <th style={{ padding: "0.6rem 0.75rem", fontWeight: 700, color: "var(--gray-700)" }}>Mức khẩn</th>
                      <th style={{ padding: "0.6rem 0.75rem", fontWeight: 700, color: "var(--gray-700)" }}>Hành động</th>
                    </tr>
                  </thead>
                  <tbody>
                    {reviewQueueData.items.map((item, idx) => (
                      <tr key={idx} style={{ borderBottom: "1px solid #f1f5f9" }}>
                        <td style={{ padding: "0.6rem 0.75rem" }}>
                          <div style={{ fontWeight: 600, color: "var(--gray-900)" }}>{item.title}</div>
                          <div style={{ fontSize: "0.75rem", color: "var(--gray-500)" }}>{item.document_number || "Chưa có số"}</div>
                        </td>
                        <td style={{ padding: "0.6rem 0.75rem" }}>
                          <div style={{ fontWeight: 600, color: "var(--gray-800)" }}>{item.student_name || "N/A"}</div>
                          <div style={{ fontSize: "0.75rem", color: "var(--gray-500)" }}>MSSV: {item.student_id || "N/A"}</div>
                        </td>
                        <td style={{ padding: "0.6rem 0.75rem" }}>
                          <span style={{ fontWeight: 700, color: item.ocr_confidence < 0.65 ? "#dc2626" : "#d97706" }}>
                            {Math.round(item.ocr_confidence * 100)}%
                          </span>
                        </td>
                        <td style={{ padding: "0.6rem 0.75rem", color: "var(--gray-600)" }}>
                          {item.skew_angle}°
                        </td>
                        <td style={{ padding: "0.6rem 0.75rem", color: "var(--gray-600)" }}>
                          {item.unclear_words_count} từ
                        </td>
                        <td style={{ padding: "0.6rem 0.75rem" }}>
                          <span
                            style={{
                              fontSize: "0.6875rem",
                              fontWeight: 700,
                              padding: "0.15rem 0.45rem",
                              borderRadius: "9999px",
                              backgroundColor: item.urgency === "URGENT" ? "#fee2e2" : item.urgency === "HIGH" ? "#fef3c7" : "#e0e7ff",
                              color: item.urgency === "URGENT" ? "#991b1b" : item.urgency === "HIGH" ? "#92400e" : "#3730a3",
                            }}
                          >
                            {item.urgency}
                          </span>
                        </td>
                        <td style={{ padding: "0.6rem 0.75rem" }}>
                          <Link to={`/documents/${item.document_id}`}>
                            <Button variant="outline" size="sm">
                              Hiệu đính
                            </Button>
                          </Link>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </Card>
          )}
        </div>
      )}

      {/* ==================================================================== */}
      {/* TAB 8: GIÁM SÁT THỜI GIAN THỰC (WATCHERS & ĐỊA LÝ NGHỊ ĐỊNH 81)       */}
      {/* ==================================================================== */}
      {activeTab === "realtime_watchers" && (
        <div style={{ display: "flex", flexDirection: "column", gap: "1.25rem" }}>
          {/* Sub-Card 1: Thẩm định Địa lý Xã ĐBKK NĐ 81/2021 */}
          <Card padding="md">
            <div style={{ display: "flex", alignItems: "center", gap: "0.75rem", marginBottom: "1rem" }}>
              <div style={{ padding: "0.6rem", borderRadius: "var(--radius-md)", backgroundColor: "#f3e8ff", color: "#7c3aed" }}>
                <MapPin size={24} />
              </div>
              <div>
                <h3 style={{ fontSize: "1.125rem", fontWeight: 700, color: "var(--gray-900)", margin: 0 }}>
                  Thẩm định Địa giới Thường trú theo Nghị định 81/2021 & QĐ 861/QĐ-TTg
                </h3>
                <p style={{ fontSize: "0.8125rem", color: "var(--gray-500)", margin: 0, marginTop: "0.2rem" }}>
                  Ứng dụng Elasticsearch Geo-search đối chiếu địa chỉ sinh viên với danh mục xã Khu vực III (Đặc biệt khó khăn) tại Lâm Đồng & Tây Nguyên.
                </p>
              </div>
            </div>

            <div style={{ display: "flex", gap: "0.5rem", flexWrap: "wrap", marginBottom: "0.75rem" }}>
              <span style={{ fontSize: "0.75rem", fontWeight: 600, color: "var(--gray-600)", alignSelf: "center" }}>Địa chỉ mẫu kiểm thử:</span>
              {[
                "Thôn Đạ Tro, Xã Đạ Chais, Huyện Lạc Dương, Tỉnh Lâm Đồng",
                "Xã Liêng S'rônh, Huyện Đam Rông, Tỉnh Lâm Đồng",
                "Xã Tân Thượng, Huyện Di Linh, Tỉnh Lâm Đồng",
                "Số 01 Phù Đổng Thiên Vương, Phường 8, TP Đà Lạt",
              ].map((sampleAddr, sIdx) => (
                <button
                  key={sIdx}
                  type="button"
                  onClick={() => {
                    setGeoAddressInput(sampleAddr);
                    handleVerifyGeoArea(sampleAddr);
                  }}
                  style={{
                    padding: "0.25rem 0.6rem",
                    borderRadius: "9999px",
                    fontSize: "0.75rem",
                    border: "1px solid #d8b4fe",
                    backgroundColor: "#faf5ff",
                    color: "#6b21a8",
                    cursor: "pointer",
                  }}
                >
                  {sampleAddr.split(",")[1]?.trim() || sampleAddr.slice(0, 20)}
                </button>
              ))}
            </div>

            <div style={{ display: "flex", gap: "0.75rem" }}>
              <input
                type="text"
                value={geoAddressInput}
                onChange={(e) => setGeoAddressInput(e.target.value)}
                placeholder="Nhập địa chỉ ghi trên CCCD/Hộ khẩu sinh viên..."
                style={{
                  flex: 1,
                  padding: "0.6rem 0.9rem",
                  borderRadius: "var(--radius-md)",
                  border: "1px solid var(--border-color)",
                  fontSize: "0.875rem",
                }}
              />
              <Button
                type="button"
                variant="primary"
                onClick={() => handleVerifyGeoArea(geoAddressInput)}
                disabled={isGeoLoading}
              >
                {isGeoLoading ? "Đang thẩm định..." : "Thẩm định Ngay"}
              </Button>
            </div>

            {geoVerifyResult && (
              <div
                style={{
                  marginTop: "1rem",
                  padding: "1rem",
                  borderRadius: "var(--radius-md)",
                  backgroundColor: geoVerifyResult.is_priority_area ? "#f0fdf4" : "#f8fafc",
                  border: `1px solid ${geoVerifyResult.is_priority_area ? "#86efac" : "#cbd5e1"}`,
                }}
              >
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "0.5rem" }}>
                  <span style={{ fontSize: "0.75rem", fontWeight: 700, color: geoVerifyResult.is_priority_area ? "#15803d" : "#475569" }}>
                    KẾT QUẢ THẨM ĐỊNH: {geoVerifyResult.area_category}
                  </span>
                  <span style={{ fontSize: "0.8125rem", fontWeight: 700, color: geoVerifyResult.tuition_reduction_rate > 0 ? "#15803d" : "#64748b" }}>
                    {geoVerifyResult.tuition_reduction_rate > 0 ? `GIẢM ${geoVerifyResult.tuition_reduction_rate}% HỌC PHÍ` : "KHÔNG THUỘC DIỆN MIỄN GIẢM"}
                  </span>
                </div>
                <div style={{ fontSize: "0.875rem", color: "var(--gray-900)", fontWeight: 600 }}>
                  Địa phương đối soát: {geoVerifyResult.matched_commune}, {geoVerifyResult.matched_district}, {geoVerifyResult.matched_province} (Cách trường ~{geoVerifyResult.distance_to_dlu_km} km)
                </div>
                {geoVerifyResult.subsidy_amount_monthly > 0 && (
                  <div style={{ fontSize: "0.8125rem", color: "#166534", marginTop: "0.25rem" }}>
                    Trợ cấp chi phí học tập hàng tháng: <strong>{geoVerifyResult.subsidy_amount_monthly.toLocaleString()} VNĐ/tháng</strong>
                  </div>
                )}
                <div style={{ fontSize: "0.75rem", color: "var(--gray-500)", marginTop: "0.35rem" }}>
                  Căn cứ pháp lý: <em>{geoVerifyResult.legal_reference}</em> — {geoVerifyResult.notes}
                </div>
              </div>
            )}
          </Card>

          {/* Sub-Card 2: Watchers & Triggered Events */}
          <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(360px, 1fr))", gap: "1rem" }}>
            <Card padding="md">
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "0.75rem" }}>
                <h4 style={{ fontSize: "0.9375rem", fontWeight: 700, color: "var(--gray-900)", margin: 0 }}>
                  Bộ giám sát Chỉ mục Đang hoạt động ({watchersList.length}):
                </h4>
                <span style={{ fontSize: "0.6875rem", fontWeight: 700, color: "#15803d", backgroundColor: "#dcfce7", padding: "0.15rem 0.4rem", borderRadius: "9999px" }}>
                  Live Active
                </span>
              </div>
              <div style={{ display: "flex", flexDirection: "column", gap: "0.6rem" }}>
                {watchersList.map((w, wIdx) => (
                  <div
                    key={wIdx}
                    style={{
                      padding: "0.65rem 0.85rem",
                      borderRadius: "var(--radius-sm)",
                      backgroundColor: "#f8fafc",
                      border: "1px solid var(--border-color)",
                    }}
                  >
                    <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                      <span style={{ fontWeight: 700, fontSize: "0.8125rem", color: "var(--gray-900)" }}>{w.name}</span>
                      <span style={{ fontSize: "0.6875rem", fontWeight: 700, color: "#2563eb", backgroundColor: "#dbeafe", padding: "0.1rem 0.35rem", borderRadius: "4px" }}>
                        +{w.matches_count_last_24h} hôm nay
                      </span>
                    </div>
                    <div style={{ fontSize: "0.75rem", color: "var(--gray-600)", marginTop: "0.2rem" }}>
                      Điều kiện DSL: <code style={{ backgroundColor: "#e2e8f0", padding: "0.1rem 0.3rem", borderRadius: "3px" }}>{w.query_text}</code>
                    </div>
                    <div style={{ fontSize: "0.6875rem", color: "var(--gray-400)", marginTop: "0.25rem" }}>
                      Kích hoạt gần nhất: {w.last_triggered_at ? new Date(w.last_triggered_at).toLocaleString("vi-VN") : "Chưa kích hoạt"}
                    </div>
                  </div>
                ))}
              </div>
            </Card>

            <Card padding="md">
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "0.75rem" }}>
                <h4 style={{ fontSize: "0.9375rem", fontWeight: 700, color: "var(--gray-900)", margin: 0 }}>
                  Sự kiện Kích hoạt Thời gian thực (Real-Time Feed):
                </h4>
                <span style={{ fontSize: "0.6875rem", fontWeight: 700, color: "#b91c1c", backgroundColor: "#fee2e2", padding: "0.15rem 0.4rem", borderRadius: "9999px" }}>
                  Live Alerts
                </span>
              </div>
              <div style={{ display: "flex", flexDirection: "column", gap: "0.6rem" }}>
                {triggeredEvents.map((evt, eIdx) => (
                  <div
                    key={eIdx}
                    style={{
                      padding: "0.65rem 0.85rem",
                      borderRadius: "var(--radius-sm)",
                      backgroundColor: evt.priority === "URGENT" ? "#fff1f2" : "#fefce8",
                      border: `1px solid ${evt.priority === "URGENT" ? "#fecdd3" : "#fef08a"}`,
                    }}
                  >
                    <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                      <span style={{ fontWeight: 700, fontSize: "0.8125rem", color: evt.priority === "URGENT" ? "#9f1239" : "#854d0e" }}>
                        {evt.document_title}
                      </span>
                      <span style={{ fontSize: "0.6875rem", fontWeight: 700, color: "#ffffff", backgroundColor: evt.priority === "URGENT" ? "#e11d48" : "#ca8a04", padding: "0.1rem 0.35rem", borderRadius: "4px" }}>
                        {evt.priority}
                      </span>
                    </div>
                    <div style={{ fontSize: "0.75rem", color: "var(--gray-700)", marginTop: "0.2rem" }}>
                      Sinh viên: <strong>{evt.student_name}</strong> (MSSV: {evt.student_id})
                    </div>
                    <div style={{ fontSize: "0.75rem", color: "var(--gray-600)", marginTop: "0.15rem" }}>
                      {evt.match_reason}
                    </div>
                    <div style={{ fontSize: "0.6875rem", color: "var(--gray-400)", marginTop: "0.25rem" }}>
                      Thời điểm: {new Date(evt.triggered_at).toLocaleTimeString("vi-VN")}
                    </div>
                  </div>
                ))}
              </div>
            </Card>
          </div>
        </div>
      )}

      {/* ==================================================================== */}
      {/* TAB: TÌM KIẾM LAI RRF (BM25 + kNN RECIPROCAL RANK FUSION - ES 8.9+)  */}
      {/* ==================================================================== */}
      {activeTab === "hybrid_rrf" && (
        <div style={{ display: "flex", flexDirection: "column", gap: "1.25rem" }}>
          {/* Header & Concept Explanation */}
          <Card padding="md" style={{ background: "linear-gradient(135deg, #f8fafc 0%, #eff6ff 100%)", border: "1px solid #bfdbfe" }}>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", flexWrap: "wrap", gap: "1rem" }}>
              <div style={{ maxWidth: "800px" }}>
                <div style={{ display: "flex", alignItems: "center", gap: "0.5rem", marginBottom: "0.4rem" }}>
                  <div style={{ backgroundColor: "#2563eb", color: "#ffffff", padding: "0.3rem", borderRadius: "0.5rem", display: "flex", alignItems: "center", justifyContent: "center" }}>
                    <Cpu size={20} />
                  </div>
                  <h3 style={{ fontSize: "1.2rem", fontWeight: 800, color: "var(--gray-900)", margin: 0 }}>
                    Tìm kiếm Lai Đa Tầng RRF (Reciprocal Rank Fusion — BM25 & kNN Dense Vector)
                  </h3>
                  <span style={{ fontSize: "0.6875rem", fontWeight: 700, backgroundColor: "#dbeafe", color: "#1d4ed8", padding: "0.2rem 0.5rem", borderRadius: "9999px" }}>
                    Elasticsearch 8.9+ Native
                  </span>
                </div>
                <p style={{ fontSize: "0.8125rem", color: "var(--gray-600)", lineHeight: 1.5, margin: 0 }}>
                  Thuật toán RRF giải quyết triệt để sự mất cân xứng độ lớn điểm số giữa <strong>BM25 (điểm số không chặn trên)</strong> và <strong>Vector kNN Cosine (trong khoảng 0 đến 1)</strong>. 
                  RRF xếp hạng độc lập hai phương thức và dung hòa dựa trên vị trí thứ tự: 
                  <code style={{ marginLeft: "0.35rem", padding: "0.15rem 0.45rem", backgroundColor: "#ffffff", borderRadius: "4px", border: "1px solid #bfdbfe", fontWeight: 700, color: "#1e40af" }}>
                    RRF(d) = Σ 1 / (k + rank_m(d))
                  </code>
                </p>
              </div>

              {/* Formula & Parameter Quick Info */}
              <div style={{ display: "flex", flexDirection: "column", gap: "0.35rem", backgroundColor: "#ffffff", padding: "0.6rem 0.85rem", borderRadius: "var(--radius-md)", border: "1px solid #e2e8f0" }}>
                <div style={{ fontSize: "0.75rem", color: "var(--gray-500)", fontWeight: 600 }}>HẰNG SỐ LÀM MỊN (RANK CONSTANT):</div>
                <div style={{ display: "flex", alignItems: "center", gap: "0.5rem" }}>
                  {[
                    { label: "k = 20 (Khuyến nghị ES 8.9)", val: 20 },
                    { label: "k = 60 (Cormack 2009)", val: 60 },
                  ].map((preset) => (
                    <button
                      key={preset.val}
                      type="button"
                      onClick={() => {
                        setHybridConstantK(preset.val);
                        handleSearchHybridRrf(hybridInput, preset.val);
                      }}
                      style={{
                        padding: "0.25rem 0.55rem",
                        borderRadius: "4px",
                        fontSize: "0.75rem",
                        fontWeight: hybridConstantK === preset.val ? 700 : 500,
                        backgroundColor: hybridConstantK === preset.val ? "#2563eb" : "#f1f5f9",
                        color: hybridConstantK === preset.val ? "#ffffff" : "var(--gray-700)",
                        border: "none",
                        cursor: "pointer",
                      }}
                    >
                      {preset.label}
                    </button>
                  ))}
                </div>
              </div>
            </div>

            {/* Input Search Box */}
            <div style={{ display: "flex", gap: "0.5rem", marginTop: "1rem" }}>
              <div style={{ position: "relative", flex: 1 }}>
                <Search size={18} style={{ position: "absolute", left: "0.85rem", top: "50%", transform: "translateY(-50%)", color: "var(--gray-400)" }} />
                <input
                  type="text"
                  value={hybridInput}
                  onChange={(e) => setHybridInput(e.target.value)}
                  onKeyDown={(e) => e.key === "Enter" && handleSearchHybridRrf(hybridInput)}
                  placeholder="Nhập câu truy vấn ngữ nghĩa hoặc từ khóa chính xác (vd: nghị định 81 miễn giảm học phí sv nghèo khó khăn)..."
                  style={{
                    width: "100%",
                    padding: "0.65rem 1rem 0.65rem 2.5rem",
                    borderRadius: "var(--radius-md)",
                    border: "2px solid #3b82f6",
                    fontSize: "0.875rem",
                    backgroundColor: "#ffffff",
                    boxShadow: "0 2px 4px rgba(59, 130, 246, 0.1)",
                  }}
                />
              </div>
              <Button
                type="button"
                variant="primary"
                leftIcon={<Zap size={16} className={isHybridLoading ? "animate-spin" : ""} />}
                onClick={() => handleSearchHybridRrf(hybridInput)}
                disabled={isHybridLoading}
                style={{ padding: "0 1.25rem", whiteSpace: "nowrap" }}
              >
                {isHybridLoading ? "Đang dung hòa RRF..." : "Tìm kiếm Lai RRF"}
              </Button>
            </div>

            {/* Suggested Scenarios */}
            <div style={{ display: "flex", alignItems: "center", gap: "0.4rem", marginTop: "0.75rem", flexWrap: "wrap" }}>
              <span style={{ fontSize: "0.75rem", color: "var(--gray-500)", fontWeight: 600 }}>Kịch bản thực nghiệm:</span>
              {[
                "nghị định 81 miễn giảm học phí sv nghèo khó khăn",
                "học bổng khuyến khích học tập dlu kỳ 1",
                "đơn xin tạm hoãn thi kết thúc học phần vì sức khỏe",
                "hỗ trợ sinh viên mồ côi dân tộc thiểu số ký túc xá",
              ].map((querySample, sIdx) => (
                <button
                  key={sIdx}
                  type="button"
                  onClick={() => {
                    setHybridInput(querySample);
                    handleSearchHybridRrf(querySample);
                  }}
                  style={{
                    padding: "0.2rem 0.55rem",
                    borderRadius: "9999px",
                    border: "1px solid #bfdbfe",
                    backgroundColor: "#eff6ff",
                    color: "#1e40af",
                    fontSize: "0.75rem",
                    cursor: "pointer",
                  }}
                >
                  {querySample}
                </button>
              ))}
            </div>
          </Card>

          {/* Execution Metrics Panel */}
          {hybridData && (
            <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(200px, 1fr))", gap: "0.75rem" }}>
              <Card padding="sm" style={{ borderLeft: "4px solid #2563eb", backgroundColor: "#f8fafc" }}>
                <span style={{ fontSize: "0.6875rem", fontWeight: 700, color: "var(--gray-500)", textTransform: "uppercase" }}>Động cơ tìm kiếm</span>
                <div style={{ fontSize: "0.9375rem", fontWeight: 800, color: "#1e40af", marginTop: "0.15rem" }}>
                  {hybridData.metrics?.engine || "Elasticsearch 8.9+ RRF"}
                </div>
                <span style={{ fontSize: "0.6875rem", color: "var(--gray-500)" }}>Thời gian: {hybridData.metrics?.execution_time_ms ?? 12} ms</span>
              </Card>

              <Card padding="sm" style={{ borderLeft: "4px solid #16a34a", backgroundColor: "#f8fafc" }}>
                <span style={{ fontSize: "0.6875rem", fontWeight: 700, color: "var(--gray-500)", textTransform: "uppercase" }}>Khớp Kép (Hybrid Both)</span>
                <div style={{ fontSize: "1.25rem", fontWeight: 800, color: "#15803d", marginTop: "0.15rem" }}>
                  {hybridData.metrics?.both_count ?? hybridData.results.filter(r => r.match_type === "HYBRID_BOTH").length}
                </div>
                <span style={{ fontSize: "0.6875rem", color: "#166534" }}>Đạt thứ hạng cao nhất nhờ cộng hưởng</span>
              </Card>

              <Card padding="sm" style={{ borderLeft: "4px solid #0284c7", backgroundColor: "#f8fafc" }}>
                <span style={{ fontSize: "0.6875rem", fontWeight: 700, color: "var(--gray-500)", textTransform: "uppercase" }}>Chỉ Khớp Từ Khóa (BM25)</span>
                <div style={{ fontSize: "1.25rem", fontWeight: 800, color: "#0369a1", marginTop: "0.15rem" }}>
                  {hybridData.metrics?.keyword_only_count ?? hybridData.results.filter(r => r.match_type === "KEYWORD_ONLY").length}
                </div>
                <span style={{ fontSize: "0.6875rem", color: "#0284c7" }}>Khớp chính xác số hiệu, điều khoản</span>
              </Card>

              <Card padding="sm" style={{ borderLeft: "4px solid #9333ea", backgroundColor: "#f8fafc" }}>
                <span style={{ fontSize: "0.6875rem", fontWeight: 700, color: "var(--gray-500)", textTransform: "uppercase" }}>Chỉ Khớp Ngữ Nghĩa (kNN)</span>
                <div style={{ fontSize: "1.25rem", fontWeight: 800, color: "#7e22ce", marginTop: "0.15rem" }}>
                  {hybridData.metrics?.semantic_only_count ?? hybridData.results.filter(r => r.match_type === "SEMANTIC_ONLY").length}
                </div>
                <span style={{ fontSize: "0.6875rem", color: "#9333ea" }}>Tìm ra tài liệu đồng nghĩa, cách diễn đạt khác</span>
              </Card>
            </div>
          )}

          {/* Results List */}
          {isHybridLoading && !hybridData ? (
            <Card padding="lg">
              <div style={{ padding: "3rem", textAlign: "center", color: "var(--gray-500)" }}>
                <Clock className="animate-spin" size={32} style={{ margin: "0 auto 0.75rem", color: "var(--primary-600)" }} />
                <span>Đang xếp hạng song song BM25 và kNN vector 768 chiều qua RRF...</span>
              </div>
            </Card>
          ) : hybridData && hybridData.results.length > 0 ? (
            <div style={{ display: "flex", flexDirection: "column", gap: "0.85rem" }}>
              {hybridData.results.map((hit, hIdx) => {
                const titleInfo = formatDisplayTitle(hit.title);
                const isBoth = hit.match_type === "HYBRID_BOTH";
                const isBm25 = hit.match_type === "KEYWORD_ONLY";
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
                          <span
                            style={{
                              padding: "0.2rem 0.6rem",
                              borderRadius: "9999px",
                              fontSize: "0.6875rem",
                              fontWeight: 800,
                              backgroundColor: isBoth ? "#dcfce7" : isBm25 ? "#dbeafe" : "#f3e8ff",
                              color: isBoth ? "#166534" : isBm25 ? "#1e40af" : "#6b21a8",
                              display: "inline-flex",
                              alignItems: "center",
                              gap: "0.3rem",
                            }}
                          >
                            {isBoth ? <Sparkles size={12} /> : isBm25 ? <Search size={12} /> : <Cpu size={12} />}
                            {isBoth ? "⚡ KHỚP KÉP (HYBRID BOTH)" : isBm25 ? "🔍 TỪ KHÓA CHÍNH XÁC (BM25)" : "🧠 NGỮ NGHĨA VECTOR (kNN)"}
                          </span>
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

                        {(hit.student_name || hit.student_id) && (
                          <div style={{ fontSize: "0.8125rem", color: "var(--gray-600)", marginTop: "0.25rem", display: "flex", alignItems: "center", gap: "0.75rem" }}>
                            <span>Sinh viên: <strong>{hit.student_name || "N/A"}</strong></span>
                            <span>MSSV: <code style={{ color: "var(--primary-700)", fontWeight: 700 }}>{hit.student_id || "N/A"}</code></span>
                          </div>
                        )}

                        {hit.content_snippet && (
                          <p style={{ fontSize: "0.8125rem", color: "var(--gray-600)", marginTop: "0.4rem", lineHeight: 1.5 }}>
                            {hit.content_snippet}
                          </p>
                        )}
                      </div>

                      {/* Rank & RRF Score Badges Box */}
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
                      </div>
                    </div>
                  </Card>
                );
              })}
            </div>
          ) : hybridData ? (
            <Card padding="lg">
              <div style={{ textAlign: "center", padding: "2rem", color: "var(--gray-500)" }}>
                Không tìm thấy tài liệu phù hợp với truy vấn lai RRF. Vui lòng thử từ khóa khác.
              </div>
            </Card>
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


