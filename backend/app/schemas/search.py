"""
backend/app/schemas/search.py — Pydantic Schemas for Search API

Định nghĩa cấu trúc response cho full-text search, highlights, và thống kê tìm kiếm.
"""
from datetime import datetime
from typing import Any, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class SearchHit(BaseModel):
    """Một kết quả tìm kiếm khớp."""
    model_config = ConfigDict(from_attributes=True)

    document_id: UUID
    title: str
    content_snippet: str | None = None
    category_code: str | None = None
    category_name: str | None = None
    student_id: str | None = None
    student_name: str | None = None
    document_date: str | None = None
    document_number: str | None = None
    tags: list[str] = Field(default_factory=list)
    priority_score: int = 0
    ocr_status: str
    ocr_confidence: float | None = None
    score: float = Field(description="Điểm liên quan BM25 từ Elasticsearch")
    highlights: dict[str, list[str]] = Field(
        default_factory=dict,
        description="Các đoạn trích nổi bật khớp từ khóa (với thẻ <em>...</em>)",
    )
    created_at: datetime | None = None


class SearchResponse(BaseModel):
    """Response trả về cho GET /search."""
    model_config = ConfigDict(from_attributes=True)

    query: str
    total_hits: int
    page: int
    page_size: int
    total_pages: int
    took_ms: int
    results: list[SearchHit]
    facets: dict[str, Any] = Field(
        default_factory=dict,
        description="Thống kê đa diện (Faceted Aggregations) theo danh mục, trạng thái, thẻ nhãn và năm ban hành",
    )
    did_you_mean: str | None = Field(
        default=None,
        description="Gợi ý sửa lỗi chính tả khi từ khóa có thể bị gõ sai (Spelling correction)",
    )


class SimilarDocumentHit(BaseModel):
    """Một tài liệu có nội dung / biểu mẫu tương đồng."""
    model_config = ConfigDict(from_attributes=True)

    document_id: UUID
    title: str
    category_code: str | None = None
    category_name: str | None = None
    student_id: str | None = None
    student_name: str | None = None
    ocr_status: str
    ocr_confidence: float | None = None
    similarity_score: float
    content_snippet: str | None = None
    created_at: datetime | None = None


class SimilarDocumentsResponse(BaseModel):
    """Response trả về cho GET /search/documents/{document_id}/similar (More Like This)."""
    model_config = ConfigDict(from_attributes=True)

    source_document_id: UUID
    source_title: str
    total_similar: int
    took_ms: int
    similar_documents: list[SimilarDocumentHit]


class TimelineDataPoint(BaseModel):
    date: str
    count: int


class CategoryDataPoint(BaseModel):
    category_code: str
    count: int


class StatusDataPoint(BaseModel):
    status: str
    count: int


class ConfidenceStats(BaseModel):
    avg: float = 0.0
    min: float = 0.0
    max: float = 0.0
    count: int = 0


class SearchDashboardResponse(BaseModel):
    """Response trả về cho GET /search/analytics/dashboard."""
    model_config = ConfigDict(from_attributes=True)

    total_documents: int
    took_ms: int
    timeline: list[TimelineDataPoint]
    categories: list[CategoryDataPoint]
    statuses: list[StatusDataPoint]
    confidence_stats: ConfidenceStats


# ── Mục 1: Duplicate / Plagiarism Detection Schemas ───────────────────────────
class DuplicateCandidateHit(BaseModel):
    """Một hồ sơ có dấu hiệu trùng lặp / sao chép nội dung."""
    document_id: UUID
    title: str
    student_name: str | None = None
    student_id: str | None = None
    similarity_score: float
    is_same_student: bool = False
    verdict: str  # "IDENTICAL" (>=90%), "HIGH_SUSPECT" (>=75%), "MODERATE" (>=50%)
    reasons: list[str] = Field(default_factory=list)
    created_at: datetime | None = None


class DuplicateCheckResponse(BaseModel):
    """Kết quả kiểm tra gian lận / trùng lặp hồ sơ."""
    source_document_id: UUID
    source_title: str
    is_suspect_duplicate: bool
    risk_level: str  # "SAFE", "WARNING", "CRITICAL"
    max_similarity_score: float
    total_candidates_found: int
    candidates: list[DuplicateCandidateHit] = Field(default_factory=list)
    recommendation: str


# ── Mục 2: SLA Tracking & Deadline Schemas ───────────────────────────────────
class SlaDocumentItem(BaseModel):
    """Hồ sơ kèm thông số tiến độ SLA."""
    document_id: UUID
    title: str
    category_name: str | None = None
    student_name: str | None = None
    status: str
    created_at: datetime
    waiting_days: float
    sla_status: str  # "OVERDUE" (>5d), "EXPIRING_SOON" (3-5d), "ON_TRACK" (<3d)
    sla_deadline_days: int = 5


class SlaSummaryResponse(BaseModel):
    """Báo cáo tổng quan tiến độ giải quyết hồ sơ (SLA) phòng CTSV."""
    total_pending: int
    overdue_count: int
    expiring_soon_count: int
    on_track_count: int
    compliance_rate: float  # Tỷ lệ hồ sơ đúng hạn (%)
    items: list[SlaDocumentItem] = Field(default_factory=list)


# ── Mục 3: Smart Search Alert Subscriptions Schemas ──────────────────────────
class AlertSubscriptionCreate(BaseModel):
    """Đăng ký từ khóa thông báo mới."""
    keyword: str
    category: str | None = None
    description: str | None = None


class AlertSubscriptionItem(BaseModel):
    """Thông tin một quy tắc theo dõi hồ sơ."""
    id: UUID
    user_id: UUID
    keyword: str
    category: str | None = None
    description: str | None = None
    is_active: bool = True
    created_at: datetime


class AlertSubscriptionListResponse(BaseModel):
    """Danh sách các từ khóa đang đăng ký theo dõi."""
    total: int
    items: list[AlertSubscriptionItem] = Field(default_factory=list)


class AlertMatchResponse(BaseModel):
    """Kết quả kiểm tra tài liệu mới khớp với các luật cảnh báo."""
    matched_alerts_count: int
    matched_keywords: list[str] = Field(default_factory=list)


# ── Chức năng 1: Student 360 Profile & Timeline Schemas ─────────────────────
class StudentTimelineEvent(BaseModel):
    """Một mốc sự kiện hồ sơ trong vòng đời học tập của sinh viên."""
    document_id: UUID
    title: str
    category_name: str | None = None
    category_code: str | None = None
    ocr_status: str
    created_at: datetime
    document_date: str | None = None
    summary_snippet: str | None = None


class StudentProfile360Response(BaseModel):
    """Hồ sơ tổng hợp 360 độ của sinh viên qua các năm học."""
    student_id: str
    student_name: str | None = None
    total_documents: int
    approved_documents: int
    pending_documents: int
    categories_breakdown: list[CategoryDataPoint] = Field(default_factory=list)
    timeline: list[StudentTimelineEvent] = Field(default_factory=list)


# ── Chức năng 3: Document Validity & Superseded Tracker Schemas ──────────────
class DocumentValidityResponse(BaseModel):
    """Thông tin hiệu lực pháp lý và văn bản thay thế."""
    document_id: UUID
    title: str
    is_effective: bool
    status_label: str  # "CÒN HIỆU LỰC" | "HẾT HIỆU LỰC (ĐÃ THAY THẾ)"
    effective_from: str | None = None
    effective_to: str | None = None
    superseded_by_id: UUID | None = None
    superseded_by_title: str | None = None
    warning_message: str | None = None


# ── Chức năng 4: Trending Topics & Significant Terms Schemas ────────────────
class TrendingTopicItem(BaseModel):
    """Một chủ đề / từ khóa đang tăng trưởng đột biến."""
    term: str
    frequency: int
    growth_rate: float  # Tỷ lệ tăng trưởng %
    sample_context: str | None = None


class TrendingTopicsResponse(BaseModel):
    """Báo cáo các điểm nóng và từ khóa phản ánh đột biến."""
    timeframe: str
    total_terms_analyzed: int
    trending_topics: list[TrendingTopicItem] = Field(default_factory=list)


# ── Chức năng 6: Staff Performance Analytics Schemas ────────────────────────
class StaffPerformanceMetric(BaseModel):
    """Chỉ số đo lường hiệu suất xử lý hồ sơ của từng cán bộ CTSV."""
    staff_id: UUID | None = None
    staff_name: str
    total_processed: int
    approved_count: int
    rejected_count: int
    avg_processing_hours: float
    performance_score: float  # Điểm đánh giá năng suất (0 - 100)


class StaffPerformanceResponse(BaseModel):
    """Báo cáo đánh giá năng suất xử lý hồ sơ toàn phòng CTSV."""
    total_staff: int
    overall_avg_hours: float
    metrics: list[StaffPerformanceMetric] = Field(default_factory=list)


# ── Đề xuất Thực tế 1: IR Evaluation Benchmark Schemas ──────────────────────
class IRMetricQueryDetail(BaseModel):
    """Chi tiết kết quả đánh giá cho một truy vấn trong tập Ground Truth."""
    id: str
    type: str  # "EASY" | "HARD" | "NEGATIVE"
    query: str
    expected_count: int
    retrieved_count: int
    relevant_retrieved: int
    precision_at_5: float
    precision_at_10: float
    recall_at_10: float
    f1_score: float
    reciprocal_rank: float
    average_precision: float
    latency_ms: float


class IRTierMetricSummary(BaseModel):
    """Tổng hợp chỉ số theo phân tầng truy vấn (EASY, HARD, NEGATIVE)."""
    count: int
    precision_at_5: float
    precision_at_10: float
    recall_at_10: float
    f1_score: float
    map: float
    mrr: float


class IREvaluationBenchmarkResponse(BaseModel):
    """Báo cáo đánh giá thực nghiệm khoa học chất lượng truy hồi thông tin (IR)."""
    total_queries: int
    engine_evaluated: str
    precision_at_5: float
    precision_at_10: float
    recall_at_10: float
    f1_score: float
    mean_average_precision_map: float
    mean_reciprocal_rank_mrr: float
    negative_rejection_rate: float
    avg_latency_ms: float
    by_tier: dict[str, IRTierMetricSummary] = Field(default_factory=dict)
    query_details: list[IRMetricQueryDetail] = Field(default_factory=list)


# ── Đề xuất Thực tế 2: Cryptographic Verification Schemas ───────────────────
class DocumentVerificationCertificate(BaseModel):
    """Chứng thư điện tử xác thực tính toàn vẹn và chống làm giả văn bản CTSV."""
    is_valid: bool
    status: str  # "VALID" | "TAMPERED" | "NOT_FOUND"
    verification_code: str
    document_id: UUID | None = None
    title: str | None = None
    student_id: str | None = None
    student_name: str | None = None
    file_hash: str
    issued_at: datetime | None = None
    issuing_authority: str = "Phòng Công tác Sinh viên - Trường Đại học Đà Lạt"
    tamper_check_passed: bool
    qr_code_url: str | None = None
    verification_notes: str


# ── Đề xuất Thực tế 3: OCR Error-Tolerant Typo Search Schemas ───────────────
class OcrCorrectionSuggestion(BaseModel):
    """Đề xuất tự động sửa lỗi chính tả / lỗi OCR do nhận dạng chữ viết tay."""
    original_term: str
    corrected_term: str
    confidence: float
    reason: str


class OcrTolerantSearchRequest(BaseModel):
    """Yêu cầu tìm kiếm dung lỗi nhận dạng OCR."""
    query: str
    category_code: str | None = None
    page: int = 1
    page_size: int = 10


class OcrTolerantSearchResponse(BaseModel):
    """Kết quả tìm kiếm chịu lỗi OCR và sai số chữ viết tay."""
    query: str
    normalized_query: str
    suggested_corrections: list[OcrCorrectionSuggestion] = Field(default_factory=list)
    total: int
    results: list[SearchHit] = Field(default_factory=list)


# ── Đề xuất Thực tế 4: Spatial Bounding Box Search Schemas ──────────────────
class SpatialHighlightBox(BaseModel):
    """Tọa độ khung chữ nhật (Bounding Box) trên trang tài liệu phục vụ Side-by-Side Live Editor."""
    page: int
    box: list[float]  # [ymin, xmin, ymax, xmax] hoặc [x, y, width, height]
    matched_text: str
    confidence: float = 0.95


class SpatialHighlightResponse(BaseModel):
    """Danh sách tọa độ xuất hiện của từ khóa trên file PDF/Ảnh scan gốc."""
    document_id: UUID
    keyword: str
    total_occurrences: int
    highlights: list[SpatialHighlightBox] = Field(default_factory=list)


# ── Đề xuất Thực tế Mới 1: Natural Language FAQ & Regulation Q&A ──────────────
class RequiredFormItem(BaseModel):
    """Biểu mẫu đính kèm cần nộp tương ứng với quy chế."""
    form_code: str
    form_name: str
    download_url: str
    guide: str | None = None


class FaqAnswerResponse(BaseModel):
    """Phản hồi câu trả lời hỏi đáp quy chế đào tạo & CTSV bằng ngôn ngữ tự nhiên."""
    query: str
    matched_article: str
    regulation_title: str
    summary_answer: str
    detail_content: str
    confidence_score: float
    required_forms: list[RequiredFormItem] = Field(default_factory=list)
    related_articles: list[str] = Field(default_factory=list)


# ── Đề xuất Thực tế Mới 2: Policy Eligibility Auto-Audit ──────────────────────
class PolicyCriteriaCheck(BaseModel):
    """Từng tiêu chí kiểm tra theo quy định chính sách của Nhà nước/Nhà trường."""
    rule_code: str
    title: str
    passed: bool
    detail: str
    evidence_snippet: str | None = None


class PolicyAuditResponse(BaseModel):
    """Kết quả tự động đối soát và thẩm định điều kiện hồ sơ CTSV."""
    document_id: UUID
    policy_name: str
    policy_code: str
    status: str  # ELIGIBLE | INCOMPLETE | INELIGIBLE
    score: float
    criteria_checks: list[PolicyCriteriaCheck] = Field(default_factory=list)
    missing_documents: list[str] = Field(default_factory=list)
    recommendation: str
    audited_at: str


# ── Đề xuất Thực tế Mới 3: Cross-Document Anti-Fraud & Collision Detection ───
class CollisionDetail(BaseModel):
    """Chi tiết xung đột hoặc trùng lặp mã chứng từ giữa các hồ sơ."""
    collision_type: str  # SERIAL_NUMBER_DUPLICATION | RECEIPT_REUSE | SIGNATURE_CONFLICT
    serial_number: str
    conflicting_document_id: str
    conflicting_student_id: str | None = None
    conflicting_student_name: str | None = None
    detail: str


class CrossDocumentFraudResponse(BaseModel):
    """Kết quả phân tích gian lận, tái sử dụng giấy tờ hoặc trùng lặp con dấu/số hiệu."""
    document_id: UUID
    student_id: str | None = None
    risk_level: str  # SAFE | WARNING | CRITICAL
    tamper_score: float
    detected_collisions: list[CollisionDetail] = Field(default_factory=list)
    conclusion: str
    audited_at: str


# ── Đề xuất Thực tế Mới 4: Nested Table Structured Search ────────────────────
class TableSearchRequest(BaseModel):
    """Yêu cầu tìm kiếm dòng bảng biểu cấu trúc trong các văn bản đa trang."""
    student_id: str | None = None
    student_name: str | None = None
    class_name: str | None = None
    min_gpa: float | None = None
    min_drl: int | None = None
    scholarship_tier: str | None = None
    page: int = 1
    page_size: int = 10


class TableRowHit(BaseModel):
    """Một dòng dữ liệu trích xuất từ bảng scan trong quyết định/danh sách."""
    document_id: UUID
    document_title: str
    decision_number: str | None = None
    page: int = 1
    mssv: str
    student_name: str
    class_name: str | None = None
    gpa: float | None = None
    drl: int | None = None
    scholarship_tier: str | None = None
    amount: str | None = None


class TableSearchResponse(BaseModel):
    """Kết quả tìm kiếm bảng biểu cấu trúc."""
    total_hits: int
    page: int
    page_size: int
    rows: list[TableRowHit] = Field(default_factory=list)
    took_ms: int = 0


# ── Đề xuất Thực tế Mới 5: PII Security Audit & Anomaly SIEM ─────────────────
class PiiAccessRecord(BaseModel):
    """Nhật ký truy xuất thông tin cá nhân nhạy cảm của sinh viên."""
    id: str
    timestamp: str
    user_id: str
    user_email: str
    action: str
    document_id: str
    student_id: str | None = None
    accessed_fields: list[str] = Field(default_factory=list)


class PiiAnomalyItem(BaseModel):
    """Cảnh báo truy cập bất thường dữ liệu sinh viên."""
    alert_id: str
    severity: str  # LOW | MEDIUM | HIGH | CRITICAL
    user_id: str
    user_email: str
    description: str
    access_count: int
    time_window: str
    created_at: str


class PiiAuditSummaryResponse(BaseModel):
    """Báo cáo tổng hợp giám sát an toàn thông tin PII theo Nghị định 13/2023/NĐ-CP."""
    total_pii_accesses: int
    unique_documents_accessed: int
    top_accessors: list[dict[str, Any]] = Field(default_factory=list)
    anomalies: list[PiiAnomalyItem] = Field(default_factory=list)
    recent_accesses: list[PiiAccessRecord] = Field(default_factory=list)


# ── Đề tài CTSV: Percolator Reverse Document Routing ──────────────────────────
class PercolateRuleMatch(BaseModel):
    """Từng quy tắc chính sách CTSV mà văn bản scan đã kích hoạt."""
    rule_id: str
    policy_name: str
    category_target: str
    target_department: str
    routing_action: str
    confidence: float
    description: str
    required_checklist: list[str] = Field(default_factory=list)


class PercolateRoutingResponse(BaseModel):
    """Kết quả phân luồng tự động văn bản bằng Elasticsearch Percolator."""
    document_id: UUID
    document_title: str
    matched_rules_count: int
    primary_route: str
    assigned_department: str
    priority: str  # URGENT | HIGH | NORMAL
    matched_policies: list[PercolateRuleMatch] = Field(default_factory=list)
    routing_timestamp: str


# ── Đề tài CTSV: Multi-faceted CTSV Analytics Aggregations ───────────────────
class FacultyBreakdownItem(BaseModel):
    """Thống kê hồ sơ sinh viên theo từng Khoa chuyên môn."""
    faculty_code: str
    faculty_name: str
    total_applications: int
    approved_count: int
    pending_count: int
    rejected_count: int
    budget_disbursed: float


class PolicyDistributionItem(BaseModel):
    """Phân bổ các diện chính sách sinh viên."""
    policy_code: str
    policy_name: str
    count: int
    percentage: float


class CtsvMultiDimensionalAnalyticsResponse(BaseModel):
    """Báo cáo tổng hợp đa chiều về tình hình chính sách sinh viên toàn trường."""
    total_student_documents: int
    total_active_students: int
    total_budget_allocated: float
    avg_processing_sla_days: float
    faculty_breakdown: list[FacultyBreakdownItem] = Field(default_factory=list)
    policy_distribution: list[PolicyDistributionItem] = Field(default_factory=list)
    monthly_application_trend: list[dict[str, Any]] = Field(default_factory=list)


# ── Đề tài CTSV Đợt 2: 1. OCR Quality & Review Queue ────────────────────────
class OcrQualityBucket(BaseModel):
    """Phân khúc dải chất lượng OCR."""
    range_label: str
    min_score: float
    max_score: float
    doc_count: int
    percentage: float
    action_needed: str


class OcrQualityDistributionResponse(BaseModel):
    """Báo cáo tổng hợp phân bổ chất lượng nhận dạng scan OCR toàn hệ thống."""
    total_scanned_documents: int
    avg_confidence: float
    excellent_count: int      # >= 90%
    good_count: int           # 75% - 89%
    review_needed_count: int  # 60% - 74%
    poor_count: int           # < 60%
    skewed_count: int
    distribution: list[OcrQualityBucket] = Field(default_factory=list)


class OcrReviewQueueItem(BaseModel):
    """Văn bản trong hàng đợi kiểm duyệt & hiệu đính thủ công (Human-in-the-Loop)."""
    document_id: UUID
    title: str
    document_number: Optional[str] = None
    student_name: Optional[str] = None
    student_id: Optional[str] = None
    ocr_confidence: float
    skew_angle: float
    unclear_words_count: int
    urgency: str  # URGENT | HIGH | NORMAL
    created_at: str


class OcrReviewQueueResponse(BaseModel):
    """Danh sách hàng đợi hiệu đính văn bản chất lượng kém."""
    total_items: int
    page: int
    page_size: int
    items: list[OcrReviewQueueItem] = Field(default_factory=list)


# ── Đề tài CTSV Đợt 2: 2. Auto-Tagging & Entity Extraction (significant_text) 
class AutoTagItem(BaseModel):
    """Thẻ nhãn tự động trích xuất từ văn cảnh bằng thuật toán significant_text."""
    tag: str
    category: str
    significance_score: float
    matched_keyword: str
    evidence_snippet: str


class DocumentAutoTagsResponse(BaseModel):
    """Kết quả tự động gán nhãn chính sách & thực thể cho tài liệu OCR."""
    document_id: UUID
    document_title: str
    total_tags: int
    tags: list[AutoTagItem] = Field(default_factory=list)
    suggested_policy_category: str
    extracted_entities: dict[str, list[str]] = Field(default_factory=dict)


# ── Đề tài CTSV Đợt 2: 3. Geo-Distance & Area Verification (NĐ 81/2021) ───────
class GeoAreaVerifyRequest(BaseModel):
    """Yêu cầu thẩm định địa giới thường trú hưởng chính sách NĐ 81/2021."""
    student_id: Optional[str] = None
    address_raw: str
    commune: Optional[str] = None
    district: Optional[str] = None
    province: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None


class GeoAreaVerifyResponse(BaseModel):
    """Kết quả thẩm định địa giới ưu tiên theo tọa độ & Nghị định 81."""
    is_priority_area: bool
    area_category: str  # KHU_VUC_III | KHU_VUC_II | KHU_VUC_I | KHONG_THUOC_DIEN
    matched_commune: str
    matched_district: str
    matched_province: str
    tuition_reduction_rate: int  # 100 | 70 | 50 | 0
    subsidy_amount_monthly: float
    distance_to_dlu_km: float
    legal_reference: str
    notes: str


# ── Đề tài CTSV Đợt 2: 4. Entity Graph & Dropout Risk (Adjacency Matrix) ─────
class GraphNode(BaseModel):
    """Nút thực thể trong đồ thị liên kết sinh viên - giấy tờ."""
    id: str
    label: str
    type: str  # STUDENT | FACULTY | POLICY | DOCUMENT | WARNING | AWARD
    group: str
    properties: dict[str, Any] = Field(default_factory=dict)


class GraphEdge(BaseModel):
    """Cạnh quan hệ giữa các thực thể."""
    source: str
    target: str
    relationship: str
    weight: float = 1.0


class DropoutRiskFactor(BaseModel):
    """Từng chỉ báo rủi ro học vụ / thôi học."""
    factor_code: str
    severity: str  # CRITICAL | HIGH | MEDIUM | LOW
    description: str
    evidence_document_id: Optional[str] = None


class DropoutRiskAssessment(BaseModel):
    """Đánh giá toàn diện nguy cơ thôi học của sinh viên."""
    risk_level: str  # SAFE | LOW | MEDIUM | HIGH | CRITICAL
    risk_score: float  # Thang điểm 0 - 100
    primary_reason: str
    action_recommendation: str
    risk_factors: list[DropoutRiskFactor] = Field(default_factory=list)


class StudentEntityGraphResponse(BaseModel):
    """Đồ thị thực thể 360 độ và phân tích rủi ro học vụ của sinh viên."""
    student_id: str
    student_name: str
    faculty: str
    total_documents_connected: int
    nodes: list[GraphNode] = Field(default_factory=list)
    edges: list[GraphEdge] = Field(default_factory=list)
    dropout_risk: DropoutRiskAssessment


# ── Đề tài CTSV Đợt 2: 5. Audit Trail & Searchable Diffs ─────────────────────
class FieldDiffItem(BaseModel):
    """So sánh thay đổi từng trường giữa bản OCR thô và bản hiệu đính."""
    field_name: str
    original_ocr_value: Any
    curated_value: Any
    is_changed: bool


class DocumentRevisionItem(BaseModel):
    """Phiên bản lịch sử chỉnh sửa tài liệu."""
    revision_number: int
    editor_name: str
    editor_role: str
    edited_at: str
    change_summary: str
    diffs: list[FieldDiffItem] = Field(default_factory=list)


class DocumentAuditTrailResponse(BaseModel):
    """Toàn bộ nhật ký kiểm toán và so sánh diffs của văn bản."""
    document_id: UUID
    title: str
    current_version: int
    total_revisions: int
    has_tamper_warning: bool
    revisions: list[DocumentRevisionItem] = Field(default_factory=list)


# ── Đề tài CTSV Đợt 2: 6. Smart Watchers & Real-Time Alerting Engine ─────────
class CreateWatcherRequest(BaseModel):
    """Tạo bộ giám sát chỉ mục tự động cho cán bộ CTSV."""
    name: str
    query_text: str
    category_code: Optional[str] = None
    faculty_code: Optional[str] = None
    min_priority: str = "NORMAL"
    notify_email: Optional[str] = None


class WatcherItem(BaseModel):
    """Bộ giám sát đang hoạt động trong hệ thống."""
    watcher_id: str
    name: str
    query_text: str
    category_code: Optional[str] = None
    created_at: str
    is_active: bool
    matches_count_last_24h: int
    last_triggered_at: Optional[str] = None


class WatcherTriggeredEvent(BaseModel):
    """Sự kiện văn bản mới kích hoạt điều kiện Watcher."""
    event_id: str
    watcher_id: str
    watcher_name: str
    document_id: UUID
    document_title: str
    student_name: Optional[str] = None
    student_id: Optional[str] = None
    match_reason: str
    triggered_at: str
    priority: str


class WatcherListResponse(BaseModel):
    """Danh sách các Watchers đang chạy."""
    total_watchers: int
    watchers: list[WatcherItem] = Field(default_factory=list)


# ── Đề tài CTSV Đợt 3: 1. Hybrid Search (BM25 + kNN Reciprocal Rank Fusion) ──────
class HybridRrfRequest(BaseModel):
    """Yêu cầu tìm kiếm lai Hybrid Search kết hợp BM25 & kNN Dense Vector."""
    query: str
    limit: int = Field(default=10, ge=1, le=50)
    rank_constant_k: int = Field(default=20, ge=1, le=100, description="Hằng số làm mịn k trong công thức RRF (thường là 20 hoặc 60)")
    category_code: Optional[str] = None
    min_confidence: Optional[float] = None


class HybridRrfHit(BaseModel):
    """Kết quả tài liệu sau khi dung hòa thứ hạng bằng RRF."""
    document_id: UUID
    title: str
    category_name: str
    student_name: Optional[str] = None
    student_id: Optional[str] = None
    bm25_rank: Optional[int] = None
    knn_rank: Optional[int] = None
    bm25_score: Optional[float] = None
    knn_score: Optional[float] = None
    rrf_score: float
    match_type: str = Field(description="HYBRID_BOTH | KEYWORD_ONLY | SEMANTIC_ONLY")
    content_snippet: Optional[str] = None
    explanation: str


class HybridRrfSearchResponse(BaseModel):
    """Báo cáo so sánh và xếp hạng tìm kiếm lai RRF (ES 8.9+)."""
    query: str
    rank_constant_k: int
    total_results: int
    results: list[HybridRrfHit] = Field(default_factory=list)
    metrics: dict[str, Any] = Field(default_factory=dict)


# ── Đề tài CTSV Đợt 3: 5. Kibana Canvas Dashboard ────────────────────────────
class KibanaCanvasWorkpadPreview(BaseModel):
    """Cấu trúc dữ liệu trực quan hóa Canvas Workpad phục vụ trình chiếu điều hành."""
    title: str
    version: str
    executive_kpis: dict[str, Any]
    faculty_budget_distribution: list[dict[str, Any]]
    policy_share_metrics: list[dict[str, Any]]
    ocr_quality_gauge: dict[str, Any]
    canvas_elements_count: int
    download_ndjson_url: str





