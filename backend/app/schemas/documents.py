"""
backend/app/schemas/documents.py — Pydantic Schemas for Documents

Quy ước đặt tên theo .ai/CODING_RULES.md:
- <Entity>Create
- <Entity>Update
- <Entity>Response
- <Entity>DetailResponse
"""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


# ── Sub-schemas ──────────────────────────────────────────────────────────────
class OCRResultResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    document_id: UUID
    is_latest: bool
    raw_text: str | None = None
    corrected_text: str | None = None
    confidence_score: float | None = None
    ocr_engine: str
    ocr_engine_version: str | None = None
    page_texts: list[dict] | dict | None = None
    processing_time_ms: int | None = None
    status: str = "DONE"
    error_message: str | None = None
    is_corrected: bool = False
    corrected_by: UUID | None = None
    corrected_at: datetime | None = None
    created_at: datetime


class ProcessingJobResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    document_id: UUID
    celery_task_id: str | None = None
    status: str
    error_message: str | None = None
    retry_count: int
    ocr_progress: int = 0  # 0-100%
    started_at: datetime | None = None
    completed_at: datetime | None = None
    created_at: datetime


class DocumentMetadataResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    document_id: UUID
    student_id: str | None = None
    student_name: str | None = None
    document_date: datetime | None = None
    document_number: str | None = None
    tags: list[str] = Field(default_factory=list)
    priority_score: int = 0
    extra: dict | None = None


class OCRCorrectionRequest(BaseModel):
    """Payload gửi lên khi cán bộ hiệu chỉnh văn bản OCR."""

    corrected_text: str = Field(..., min_length=1, description="Nội dung văn bản sau khi hiệu chỉnh")
    engine: str | None = Field(default=None, description="Tên engine đang được hiệu chỉnh (vietocr, trocr, tesseract)")


class SetPublicRequest(BaseModel):
    """Payload cập nhật quyền công khai của tài liệu cho sinh viên."""

    is_public: bool = Field(
        ..., description="Trạng thái công khai của tài liệu (True: Cho phép sinh viên xem, False: Nội bộ CTSV)"
    )


class FieldExtractionUpdateRequest(BaseModel):
    """Payload cập nhật metadata bóc tách thông tin sinh viên."""

    student_id: str | None = None
    student_name: str | None = None
    document_number: str | None = None
    document_date: datetime | None = None
    tags: list[str] | None = None
    extra: dict | None = None


class UpdateTagsRequest(BaseModel):
    """Payload cập nhật danh sách nhãn (tags) của tài liệu."""

    tags: list[str] = Field(default_factory=list, description="Danh sách các nhãn gán cho tài liệu")


class TagSummaryItem(BaseModel):
    """Thống kê từng nhãn trong hệ thống."""

    tag: str
    count: int
    priority: int
    color: str
    category: str


class TagSummaryResponse(BaseModel):
    """Danh sách thống kê toàn bộ nhãn phục vụ thanh lọc 1-Click."""

    items: list[TagSummaryItem]
    total_tags: int


class AIRefineRequest(BaseModel):
    """Payload yêu cầu AI hiệu chỉnh chính tả & cấu trúc văn bản OCR."""

    text: str | None = Field(
        default=None, description="Văn bản OCR cần AI tinh chỉnh (nếu None sẽ lấy từ OCRResult mới nhất)"
    )


class AIRefineResponse(BaseModel):
    """Kết quả AI hiệu chỉnh văn bản."""

    original_text: str
    refined_text: str
    provider: str
    model: str
    success: bool
    message: str | None = None


class AIExtractResponse(BaseModel):
    """Kết quả AI trích xuất thông tin thông minh."""

    student_name: str | None = None
    student_id: str | None = None
    class_name: str | None = None
    faculty: str | None = None
    document_type: str | None = None
    document_number: str | None = None
    reason: str | None = None
    amount: str | None = None
    document_date: datetime | str | None = None
    tags: list[str] = Field(default_factory=list)
    priority_score: int = 0
    summary: str | None = None
    suggested_action: str | None = None
    provider: str = "rule_based"
    model: str = "regex"
    confidence_score: float = 0.9


class VerificationResponse(BaseModel):
    """Payload phản hồi khi quét mã QR xác thực hồ sơ."""

    is_valid: bool
    document_id: UUID
    title: str
    original_filename: str
    ocr_status: str
    student_name: str | None = None
    student_id: str | None = None
    approved_at: datetime | None = None
    approved_by_name: str | None = None
    approved_by_role: str | None = None
    approved_by_role_label: str | None = None
    verification_code: str
    qr_payload: str
    issued_by: str = "Trường Đại học Đà Lạt - Phòng Công tác Sinh viên (DocuCTSV)"


class ApprovalInfo(BaseModel):
    """Thông tin phê duyệt hoặc từ chối hồ sơ bởi Cán bộ CTSV / Quản trị viên."""

    status: str
    action: str = "APPROVE_DOCUMENT"
    approver_id: str | None = None
    approver_name: str | None = None
    approver_role: str | None = None  # "ADMIN" | "STAFF"
    approver_role_label: str | None = None  # "Quản trị viên (ADMIN)" | "Cán bộ Công tác Sinh viên (CTSV)"
    timestamp: datetime | None = None
    note: str | None = None


class DocumentNotificationItem(BaseModel):
    """Thông báo về trạng thái xét duyệt và nộp hồ sơ."""

    id: str
    document_id: UUID
    document_title: str
    action: str  # "APPROVE_DOCUMENT" | "REJECT_DOCUMENT" | "UPLOAD"
    status: str  # "APPROVED" | "REJECTED" | "PENDING" | "PROCESSING" | "DONE"
    actor_id: str | None = None
    actor_name: str
    actor_role: str
    actor_role_label: str
    message: str
    created_at: datetime
    is_read: bool = False


class DocumentNotificationsResponse(BaseModel):
    """Danh sách thông báo kèm số lượng chưa đọc."""

    items: list[DocumentNotificationItem] = Field(default_factory=list)
    total: int = 0
    unread_count: int = 0


# ── Main Document Schemas ────────────────────────────────────────────────────
class DocumentUploadResponse(BaseModel):
    """Response trả về ngay sau khi upload (202 Accepted)."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    title: str
    original_filename: str
    file_type: str
    file_size_bytes: int
    ocr_status: str
    minio_object_key: str
    job_id: UUID | None = None
    celery_task_id: str | None = None
    message: str = "Tài liệu đã được tải lên và đưa vào hàng đợi OCR."
    created_at: datetime


class DocumentResponse(BaseModel):
    """Thông tin cơ bản của Document."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    title: str
    original_filename: str
    file_type: str
    file_size_bytes: int
    page_count: int | None = None
    category_id: UUID | None = None
    uploaded_by: UUID | None = None
    ocr_status: str
    minio_object_key: str | None = None
    is_public: bool = False
    is_deleted: bool = False
    created_at: datetime
    updated_at: datetime


class DocumentListItem(DocumentResponse):
    """Thông tin item trong danh sách tài liệu."""

    uploader_name: str | None = None
    uploader_mssv: str | None = None
    category_name: str | None = None
    category_code: str | None = None
    confidence_score: float | None = None
    ocr_confidence: float | None = None
    student_id: str | None = None
    student_name: str | None = None
    document_number: str | None = None
    tags: list[str] = Field(default_factory=list)
    priority_score: int = 0
    ocr_progress: int = 0  # 0-100% tiến độ OCR thực tế
    approval_info: ApprovalInfo | None = None


class DocumentListResponse(BaseModel):
    """Danh sách tài liệu có phân trang."""

    items: list[DocumentListItem]
    total: int
    page: int
    page_size: int
    total_pages: int


class DocumentDetailResponse(DocumentResponse):
    """Thông tin chi tiết tài liệu kèm kết quả OCR mới nhất và trạng thái Job."""

    ocr_result: OCRResultResponse | None = None
    all_ocr_results: list[OCRResultResponse] = Field(default_factory=list)
    processing_job: ProcessingJobResponse | None = None
    metadata_: DocumentMetadataResponse | None = Field(default=None, alias="metadata")
    tags: list[str] = Field(default_factory=list)
    priority_score: int = 0
    file_url: str | None = None
    approval_info: ApprovalInfo | None = None


class TypeOverrideReq(BaseModel):
    category_code: str = Field(..., description="Mã loại tài liệu (category code)")


# ── Stamp & Table Extraction Schemas ─────────────────────────────────────────
class DetectedStampSchema(BaseModel):
    bbox: tuple[int, int, int, int]
    confidence: float
    area: float
    aspect_ratio: float
    image_base64: str = ""
    is_circular: bool = False


class StampDetectionResponse(BaseModel):
    document_id: UUID
    has_stamp: bool
    stamps: list[DetectedStampSchema] = Field(default_factory=list)
    cleaned_image_base64: str = ""
    red_pixel_ratio: float = 0.0


class TableCellSchema(BaseModel):
    row_idx: int
    col_idx: int
    bbox: tuple[int, int, int, int]
    text: str = ""


class ExtractedTableSchema(BaseModel):
    table_idx: int
    page_num: int = 1
    bbox: tuple[int, int, int, int]
    headers: list[str] = Field(default_factory=list)
    rows: list[list[str]] = Field(default_factory=list)
    cells: list[TableCellSchema] = Field(default_factory=list)
    row_count: int = 0
    col_count: int = 0
    markdown: str = ""
    html: str = ""


class TableExtractionResponse(BaseModel):
    document_id: UUID
    has_table: bool
    tables: list[ExtractedTableSchema] = Field(default_factory=list)
    total_tables: int = 0
    total_cells: int = 0


class CategoryItemResponse(BaseModel):
    id: str
    name: str
    code: str
    description: str | None = None
    is_active: bool = True
    doc_count: int = 0


class CreateCategoryRequest(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    code: str = Field(..., min_length=2, max_length=50)
    description: str | None = None

