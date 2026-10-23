import { apiClient } from "./client";

export interface SearchHit {
  document_id: string;
  title: string;
  content_snippet?: string;
  category_code?: string;
  category_name?: string;
  doc_type_code?: string;
  doc_type_name?: string;
  doc_group?: string;
  doc_subtype?: string;
  doc_type_confidence?: number;
  doc_type_source?: string;
  subject?: string;
  issuing_unit?: string;
  ocr_scope?: string;
  page_count?: number;
  pages_ocr?: number;
  needs_review?: boolean;
  student_id?: string;
  student_name?: string;
  document_date?: string;
  document_number?: string;
  ocr_status: string;
  ocr_confidence?: number;
  score: number;
  highlights: Record<string, string[]>;
  tags?: string[];
  created_at?: string;
}

export interface FacetItem {
  code?: string;
  category?: string;
  status?: string;
  tag?: string;
  year?: string;
  count: number;
}

export interface SearchResponse {
  query: string;
  total_hits: number;
  page: number;
  page_size: number;
  total_pages: number;
  took_ms: number;
  facets?: {
    categories?: FacetItem[];
    statuses?: FacetItem[];
    tags?: FacetItem[];
    years?: FacetItem[];
    doc_type_code?: FacetItem[];
    doc_group?: FacetItem[];
    [key: string]: any;
  };
  results: SearchHit[];
}

export interface SuggestItem {
  type: string;
  text: string;
  document_id?: string;
  category_code?: string;
}

export interface SuggestResponse {
  query: string;
  suggestions: SuggestItem[];
}

export interface SearchParams {
  q?: string;
  category_code?: string;
  doc_type_code?: string;
  doc_group?: string;
  tag?: string;
  ocr_scope?: string;
  ocr_status?: string;
  date_from?: string;
  date_to?: string;
  fuzzy?: boolean;
  page?: number;
  page_size?: number;
}

// ── 5 Tính năng đề xuất mới ──────────────────────────────────────────────────
export interface RequiredFormItem {
  form_code: string;
  form_name: string;
  download_url: string;
  guide?: string;
}

export interface FaqAnswerResponse {
  query: string;
  matched_article: string;
  regulation_title: string;
  summary_answer: string;
  detail_content: string;
  confidence_score: number;
  required_forms: RequiredFormItem[];
  related_articles: string[];
}

export interface PolicyCriteriaCheck {
  rule_code: string;
  title: string;
  passed: boolean;
  detail: string;
  evidence_snippet?: string;
}

export interface PolicyAuditResponse {
  document_id: string;
  policy_name: string;
  policy_code: string;
  status: "ELIGIBLE" | "INCOMPLETE" | "INELIGIBLE";
  score: number;
  criteria_checks: PolicyCriteriaCheck[];
  missing_documents: string[];
  recommendation: string;
  audited_at: string;
}

export interface CollisionDetail {
  collision_type: string;
  serial_number: string;
  conflicting_document_id: string;
  conflicting_student_id?: string;
  conflicting_student_name?: string;
  detail: string;
}

export interface CrossDocumentFraudResponse {
  document_id: string;
  student_id?: string;
  risk_level: "SAFE" | "WARNING" | "CRITICAL";
  tamper_score: number;
  detected_collisions: CollisionDetail[];
  conclusion: string;
  audited_at: string;
}

export interface TableSearchRequest {
  student_id?: string;
  student_name?: string;
  class_name?: string;
  min_gpa?: number;
  min_drl?: number;
  scholarship_tier?: string;
  page?: number;
  page_size?: number;
}

export interface TableRowHit {
  document_id: string;
  document_title: string;
  decision_number?: string;
  page: number;
  mssv: string;
  student_name: string;
  class_name?: string;
  gpa?: number;
  drl?: number;
  scholarship_tier?: string;
  amount?: string;
}

export interface TableSearchResponse {
  total_hits: number;
  page: number;
  page_size: number;
  rows: TableRowHit[];
  took_ms: number;
}

export interface PiiAccessRecord {
  id: string;
  timestamp: string;
  user_id: string;
  user_email: string;
  action: string;
  document_id: string;
  student_id?: string;
  accessed_fields: string[];
}

export interface PiiAnomalyItem {
  alert_id: string;
  severity: "LOW" | "MEDIUM" | "HIGH" | "CRITICAL";
  user_id: string;
  user_email: string;
  description: string;
  access_count: number;
  time_window: string;
  created_at: string;
}

export interface PiiAuditSummaryResponse {
  total_pii_accesses: number;
  unique_documents_accessed: number;
  top_accessors: { user_id: string; email: string; access_count: number }[];
  anomalies: PiiAnomalyItem[];
  recent_accesses: PiiAccessRecord[];
}

// ── Đề tài CTSV: Percolator Reverse Document Routing ──
export interface PercolateRuleMatch {
  rule_id: string;
  policy_name: string;
  category_target: string;
  target_department: string;
  routing_action: string;
  confidence: number;
  description: string;
  required_checklist: string[];
}

export interface PercolateRoutingResponse {
  document_id: string;
  document_title: string;
  matched_rules_count: number;
  primary_route: string;
  assigned_department: string;
  priority: "URGENT" | "HIGH" | "NORMAL";
  matched_policies: PercolateRuleMatch[];
  routing_timestamp: string;
}

// ── Đề tài CTSV: Multi-faceted CTSV Analytics Aggregations ──
export interface FacultyBreakdownItem {
  faculty_code: string;
  faculty_name: string;
  total_applications: number;
  approved_count: number;
  pending_count: number;
  rejected_count: number;
  budget_disbursed: number;
}

export interface PolicyDistributionItem {
  policy_code: string;
  policy_name: string;
  count: number;
  percentage: number;
}

export interface CtsvMultiDimensionalAnalyticsResponse {
  total_student_documents: number;
  total_active_students: number;
  total_budget_allocated: number;
  avg_processing_sla_days: number;
  faculty_breakdown: FacultyBreakdownItem[];
  policy_distribution: PolicyDistributionItem[];
  monthly_application_trend: { month: string; applications: number; approved: number }[];
}

// ── Đề tài CTSV: Spatial Highlighting Bounding Boxes ──
export interface SpatialHighlightBox {
  page: number;
  box: [number, number, number, number]; // [ymin, xmin, ymax, xmax]
  matched_text: string;
  confidence?: number;
}

export interface SpatialHighlightResponse {
  document_id: string;
  keyword: string;
  total_occurrences: number;
  highlights: SpatialHighlightBox[];
}

// ── Đề tài CTSV: OCR Error-Tolerant Search & Suggester ──
export interface OcrCorrectionSuggestion {
  original_term: string;
  corrected_term: string;
  confidence: number;
  reason: string;
}

export interface OcrTolerantSearchRequest {
  query: string;
  category_code?: string;
  page?: number;
  page_size?: number;
}

export interface OcrTolerantSearchResponse {
  query: string;
  normalized_query: string;
  suggested_corrections: OcrCorrectionSuggestion[];
  total: number;
  page: number;
  page_size: number;
  results: SearchHit[];
}

// ── Đề tài CTSV: Cross-Document More-Like-This Duplicate Checker ──
export interface DuplicateCandidateHit {
  document_id: string;
  title: string;
  student_id?: string;
  student_name?: string;
  similarity_score: number;
  matched_terms: string[];
  content_snippet?: string;
  created_at?: string;
}

export interface DuplicateCheckResponse {
  document_id: string;
  is_suspect_duplicate: boolean;
  risk_level: "SAFE" | "WARNING" | "CRITICAL";
  max_similarity_score: number;
  recommendation: string;
  candidates: DuplicateCandidateHit[];
}

// ── Đề tài CTSV Đợt 2: Types ──
export interface OcrQualityBucket {
  range_label: string;
  min_score: number;
  max_score: number;
  doc_count: number;
  percentage: number;
  action_needed: string;
}

export interface OcrQualityDistributionResponse {
  total_scanned_documents: number;
  avg_confidence: number;
  excellent_count: number;
  good_count: number;
  review_needed_count: number;
  poor_count: number;
  skewed_count: number;
  distribution: OcrQualityBucket[];
}

export interface OcrReviewQueueItem {
  document_id: string;
  title: string;
  document_number?: string;
  student_name?: string;
  student_id?: string;
  ocr_confidence: number;
  skew_angle: number;
  unclear_words_count: number;
  urgency: "URGENT" | "HIGH" | "NORMAL";
  created_at: string;
}

export interface OcrReviewQueueResponse {
  total_items: number;
  page: number;
  page_size: number;
  items: OcrReviewQueueItem[];
}

export interface AutoTagItem {
  tag: string;
  category: string;
  significance_score: number;
  matched_keyword: string;
  evidence_snippet: string;
}

export interface DocumentAutoTagsResponse {
  document_id: string;
  document_title: string;
  total_tags: number;
  tags: AutoTagItem[];
  suggested_policy_category: string;
  extracted_entities: Record<string, string[]>;
}

export interface GeoAreaVerifyRequest {
  student_id?: string;
  address_raw: string;
  commune?: string;
  district?: string;
  province?: string;
}

export interface GeoAreaVerifyResponse {
  is_priority_area: boolean;
  area_category: "KHU_VUC_III" | "KHU_VUC_II" | "KHU_VUC_I" | "KHONG_THUOC_DIEN";
  matched_commune: string;
  matched_district: string;
  matched_province: string;
  tuition_reduction_rate: number;
  subsidy_amount_monthly: number;
  distance_to_dlu_km: number;
  legal_reference: string;
  notes: string;
}

export interface GraphNode {
  id: string;
  label: string;
  type: string;
  group: string;
  properties?: Record<string, any>;
}

export interface GraphEdge {
  source: string;
  target: string;
  relationship: string;
  weight: number;
}

export interface DropoutRiskAssessment {
  risk_level: "SAFE" | "LOW" | "MEDIUM" | "HIGH" | "CRITICAL";
  risk_score: number;
  primary_reason: string;
  action_recommendation: string;
  risk_factors: { factor_code: string; severity: string; description: string }[];
}

export interface StudentEntityGraphResponse {
  student_id: string;
  student_name: string;
  faculty: string;
  total_documents_connected: number;
  nodes: GraphNode[];
  edges: GraphEdge[];
  dropout_risk: DropoutRiskAssessment;
}

export interface FieldDiffItem {
  field_name: string;
  original_ocr_value: any;
  curated_value: any;
  is_changed: boolean;
}

export interface DocumentRevisionItem {
  revision_number: number;
  editor_name: string;
  editor_role: string;
  edited_at: string;
  change_summary: string;
  diffs: FieldDiffItem[];
}

export interface DocumentAuditTrailResponse {
  document_id: string;
  title: string;
  current_version: number;
  total_revisions: number;
  has_tamper_warning: boolean;
  revisions: DocumentRevisionItem[];
}

export interface CreateWatcherRequest {
  name: string;
  query_text: string;
  category_code?: string;
  min_priority?: string;
}

export interface WatcherItem {
  watcher_id: string;
  name: string;
  query_text: string;
  category_code?: string;
  created_at: string;
  is_active: boolean;
  matches_count_last_24h: number;
  last_triggered_at?: string;
}

export interface WatcherTriggeredEvent {
  event_id: string;
  watcher_id: string;
  watcher_name: string;
  document_id: string;
  document_title: string;
  student_name?: string;
  student_id?: string;
  match_reason: string;
  triggered_at: string;
  priority: string;
}

export interface WatcherListResponse {
  total_watchers: number;
  watchers: WatcherItem[];
}

export const searchApi = {
  // 1. Full-text search
  search: async (params: SearchParams): Promise<SearchResponse> => {
    const res = await apiClient.get<SearchResponse>("/search", { params });
    return res.data;
  },

  // 2. Autocomplete suggestions
  suggest: async (q: string, limit = 6): Promise<SuggestResponse> => {
    const res = await apiClient.get<SuggestResponse>("/search/suggest", {
      params: { q, limit },
    });
    return res.data;
  },

  // 3. Trending keywords
  trending: async (): Promise<string[]> => {
    const res = await apiClient.get<{ keywords: string[] }>("/search/trending");
    return res.data.keywords;
  },

  // 4. Natural Language FAQ & Regulation Q&A
  askFaq: async (q: string): Promise<FaqAnswerResponse> => {
    const res = await apiClient.get<FaqAnswerResponse>("/search/faq/ask", {
      params: { q },
    });
    return res.data;
  },

  // 5. Policy Eligibility Auto-Audit
  auditPolicy: async (
    documentId: string,
    policyCode = "NGHI_DINH_81"
  ): Promise<PolicyAuditResponse> => {
    const res = await apiClient.get<PolicyAuditResponse>(
      `/search/documents/${documentId}/policy-audit`,
      { params: { policy_code: policyCode } }
    );
    return res.data;
  },

  // 6. Cross-Document Anti-Fraud & Collision Detection
  auditFraud: async (
    documentId?: string,
    studentId?: string
  ): Promise<CrossDocumentFraudResponse> => {
    const res = await apiClient.get<CrossDocumentFraudResponse>(
      "/search/fraud-detection/audit",
      { params: { document_id: documentId, student_id: studentId } }
    );
    return res.data;
  },

  // 7. Nested Table Structured Search
  queryTables: async (
    params: TableSearchRequest
  ): Promise<TableSearchResponse> => {
    const res = await apiClient.post<TableSearchResponse>(
      "/search/tables/query",
      params
    );
    return res.data;
  },

  // 8. PII Security Audit & Anomaly SIEM
  getPiiAuditSummary: async (
    windowMinutes = 60
  ): Promise<PiiAuditSummaryResponse> => {
    const res = await apiClient.get<PiiAuditSummaryResponse>(
      "/search/security/pii-audit-summary",
      { params: { window_minutes: windowMinutes } }
    );
    return res.data;
  },

  // 9. Percolator Reverse Document Routing
  getPercolateRouting: async (
    documentId: string
  ): Promise<PercolateRoutingResponse> => {
    const res = await apiClient.get<PercolateRoutingResponse>(
      `/search/documents/${documentId}/percolate-routing`
    );
    return res.data;
  },

  // 10. Multi-faceted CTSV Analytics Aggregations
  getCtsvBreakdown: async (): Promise<CtsvMultiDimensionalAnalyticsResponse> => {
    const res = await apiClient.get<CtsvMultiDimensionalAnalyticsResponse>(
      "/search/analytics/ctsv-breakdown"
    );
    return res.data;
  },

  // 11. Spatial Highlighting Bounding Boxes
  getSpatialHighlights: async (
    documentId: string,
    q: string
  ): Promise<SpatialHighlightResponse> => {
    const res = await apiClient.get<SpatialHighlightResponse>(
      `/search/documents/${documentId}/spatial-highlights`,
      { params: { q } }
    );
    return res.data;
  },

  // 12. OCR Error-Tolerant Search
  searchOcrTolerant: async (
    payload: OcrTolerantSearchRequest
  ): Promise<OcrTolerantSearchResponse> => {
    const res = await apiClient.post<OcrTolerantSearchResponse>(
      "/search/ocr-tolerant",
      payload
    );
    return res.data;
  },

  // 13. More-Like-This Duplicate Check
  checkDuplicates: async (
    documentId: string
  ): Promise<DuplicateCheckResponse> => {
    const res = await apiClient.get<DuplicateCheckResponse>(
      `/search/documents/${documentId}/duplicate-check`
    );
    return res.data;
  },

  // 14. OCR Quality Distribution
  getOcrQualityDistribution: async (): Promise<OcrQualityDistributionResponse> => {
    const res = await apiClient.get<OcrQualityDistributionResponse>(
      "/search/analytics/ocr-quality"
    );
    return res.data;
  },

  // 15. OCR Review Queue (Human-in-the-Loop)
  getOcrReviewQueue: async (params?: {
    page?: number;
    pageSize?: number;
    maxConfidence?: number;
  }): Promise<OcrReviewQueueResponse> => {
    const res = await apiClient.get<OcrReviewQueueResponse>(
      "/search/ocr-quality/review-queue",
      {
        params: {
          page: params?.page || 1,
          page_size: params?.pageSize || 10,
          max_confidence: params?.maxConfidence ?? 0.75,
        },
      }
    );
    return res.data;
  },

  // 16. Auto-Tagging & Entity Extraction (significant_text)
  getDocumentAutoTags: async (documentId: string): Promise<DocumentAutoTagsResponse> => {
    const res = await apiClient.post<DocumentAutoTagsResponse>(
      `/search/documents/${documentId}/auto-tags`
    );
    return res.data;
  },

  // 17. Geo-Distance Area Verify (NĐ 81/2021)
  verifyGeoPriorityArea: async (
    payload: GeoAreaVerifyRequest
  ): Promise<GeoAreaVerifyResponse> => {
    const res = await apiClient.post<GeoAreaVerifyResponse>(
      "/search/geo/verify-priority-area",
      payload
    );
    return res.data;
  },

  // 18. Student Entity Graph & Dropout Risk
  getStudentEntityGraph: async (
    studentId: string
  ): Promise<StudentEntityGraphResponse> => {
    const res = await apiClient.get<StudentEntityGraphResponse>(
      `/search/students/${studentId}/entity-graph`
    );
    return res.data;
  },

  // 19. Document Audit Trail & Diffs
  getDocumentAuditTrail: async (
    documentId: string
  ): Promise<DocumentAuditTrailResponse> => {
    const res = await apiClient.get<DocumentAuditTrailResponse>(
      `/search/documents/${documentId}/audit-trail`
    );
    return res.data;
  },

  // 20. Watchers (Real-Time Alerting Engine)
  getWatchers: async (): Promise<WatcherListResponse> => {
    const res = await apiClient.get<WatcherListResponse>("/search/watchers");
    return res.data;
  },

  createWatcher: async (payload: CreateWatcherRequest): Promise<WatcherItem> => {
    const res = await apiClient.post<WatcherItem>("/search/watchers", payload);
    return res.data;
  },

  getWatcherTriggeredEvents: async (
    watcherId: string
  ): Promise<WatcherTriggeredEvent[]> => {
    const res = await apiClient.get<WatcherTriggeredEvent[]>(
      `/search/watchers/${watcherId}/triggered-events`
    );
    return res.data;
  },

  // 21. Hybrid Search (BM25 + kNN RRF)
  searchHybridRrf: async (
    payload: HybridRrfRequest
  ): Promise<HybridRrfSearchResponse> => {
    const res = await apiClient.post<HybridRrfSearchResponse>(
      "/search/hybrid-rrf",
      payload
    );
    return res.data;
  },

  // 22. Kibana Canvas Workpad Preview
  getKibanaCanvasPreview: async (): Promise<KibanaCanvasWorkpadPreview> => {
    const res = await apiClient.get<KibanaCanvasWorkpadPreview>(
      "/search/kibana/canvas-preview"
    );
    return res.data;
  },

  // 23. Kibana Saved Objects Download URL
  getKibanaDashboardDownloadUrl: (): string => {
    return "/api/v1/search/kibana/export-dashboard";
  },
};

// ── Đề tài CTSV Đợt 3: 1. Hybrid Search (BM25 + kNN Reciprocal Rank Fusion) ──
export interface HybridRrfRequest {
  query: string;
  limit?: number;
  rank_constant_k?: number;
  category_code?: string;
  min_confidence?: number;
}

export interface HybridRrfHit {
  document_id: string;
  title: string;
  category_name: string;
  student_name?: string;
  student_id?: string;
  bm25_rank?: number;
  knn_rank?: number;
  bm25_score?: number;
  knn_score?: number;
  rrf_score: number;
  match_type: "HYBRID_BOTH" | "KEYWORD_ONLY" | "SEMANTIC_ONLY" | string;
  content_snippet?: string;
  explanation: string;
}

export interface HybridRrfSearchResponse {
  query: string;
  rank_constant_k: number;
  total_results: number;
  results: HybridRrfHit[];
  metrics: {
    engine?: string;
    execution_time_ms?: number;
    both_count?: number;
    keyword_only_count?: number;
    semantic_only_count?: number;
    formula?: string;
    [key: string]: any;
  };
}

// ── Đề tài CTSV Đợt 3: 5. Kibana Canvas Dashboard & Workpad Preview ───────────
export interface KibanaCanvasWorkpadPreview {
  title: string;
  version: string;
  executive_kpis: {
    total_documents: number;
    active_beneficiaries: number;
    total_budget_disbursed: string;
    sla_avg_days: number;
    compliance_rate: string;
    [key: string]: any;
  };
  faculty_budget_distribution: Array<{
    faculty: string;
    budget: number;
    apps: number;
  }>;
  policy_share_metrics: Array<{
    policy: string;
    percentage: number;
    count: number;
  }>;
  ocr_quality_gauge: {
    avg_confidence: number;
    excellent_rate: string;
    manual_review_queue_size: number;
    status: string;
  };
  canvas_elements_count: number;
  download_ndjson_url: string;
}



