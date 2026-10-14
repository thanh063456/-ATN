"""
backend/app/schemas/search.py — Pydantic Schemas for Search API

Định nghĩa cấu trúc response cho full-text search, highlights, và thống kê tìm kiếm.
"""
from datetime import datetime
from typing import Any
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


