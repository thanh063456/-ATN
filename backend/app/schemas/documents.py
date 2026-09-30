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
    extra: dict | None = None


class OCRCorrectionRequest(BaseModel):
    """Payload gửi lên khi cán bộ hiệu chỉnh văn bản OCR."""
    corrected_text: str = Field(..., min_length=1, description="Nội dung văn bản sau khi hiệu chỉnh")


class FieldExtractionUpdateRequest(BaseModel):
    """Payload cập nhật metadata bóc tách thông tin sinh viên."""
    student_id: str | None = None
    student_name: str | None = None
    document_number: str | None = None
    document_date: datetime | None = None
    extra: dict | None = None


class AIRefineRequest(BaseModel):
    """Payload yêu cầu AI hiệu chỉnh chính tả & cấu trúc văn bản OCR."""
    text: str | None = Field(default=None, description="Văn bản OCR cần AI tinh chỉnh (nếu None sẽ lấy từ OCRResult mới nhất)")


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
    reason: str | None = None
    amount: str | None = None
    document_date: datetime | str | None = None
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
    verification_code: str
    qr_payload: str
    issued_by: str = "Trường Đại học Đà Lạt - Phòng Công tác Sinh viên (DocuCTSV)"


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
    ocr_progress: int = 0  # 0-100% tiến độ OCR thực tế


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
    processing_job: ProcessingJobResponse | None = None
    metadata_: DocumentMetadataResponse | None = Field(default=None, alias="metadata")
