"""
backend/app/routers/documents.py — Document API Endpoints (Advanced OCR & RBAC)

Bao gồm:
- GET /documents: Danh sách tài liệu (Phân quyền: STUDENT chỉ thấy của mình, STAFF/ADMIN thấy tất cả)
- POST /documents/upload: Upload và kích hoạt async OCR
- GET /documents/{id}: Chi tiết tài liệu, OCR text, metadata, job status
- PUT /documents/{id}/ocr-correction: Cán bộ CTSV hiệu chỉnh văn bản OCR (Side-by-Side Editor)
- POST /documents/{id}/extract-fields: Tự động bóc tách MSSV, Họ tên, Lý do vào metadata
- PUT /documents/{id}/metadata: Cập nhật thủ công metadata sinh viên
- PATCH /documents/{id}/approve: Phê duyệt hồ sơ (STAFF, ADMIN) + đóng dấu xác thực
- PATCH /documents/{id}/reject: Từ chối hồ sơ (STAFF, ADMIN)
- GET /documents/{id}/file-content: Lấy link/dữ liệu xem file gốc
- GET /documents/export/excel: Xuất danh sách hồ sơ ra file Excel (.xlsx / .csv)
- GET /documents/{id}/verification: Tra cứu mã QR xác thực điện tử
"""
import asyncio
import csv
from datetime import datetime, timezone
import hashlib
import io
import math
import os
import re
import urllib.parse
from uuid import UUID

from fastapi import APIRouter, Depends, File, Form, Query, Request, Response, UploadFile, status
from fastapi.responses import StreamingResponse
from loguru import logger
from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.config import settings
from app.core.constants import DEFAULT_OCR_ENGINE, OCR_ENGINES
from app.core.database import get_db
from app.core.dependencies import _resolve_user_from_token, get_current_user, get_current_user_optional, require_roles
from app.core.exceptions import (
    AppException,
    DocumentNotFoundException,
    FileTooLargeException,
    NotFoundException,
    UnsupportedFileTypeException,
    ValidationException,
)
from app.core.rate_limiter import limiter
from app.core.tickets import create_file_ticket, validate_and_consume_file_ticket
from app.models.audit_logs import AuditLog
from app.models.document_categories import DocumentCategory
from app.models.document_metadata import DocumentMetadata
from app.models.documents import Document
from app.models.ocr_results import OCRResult
from app.models.users import User
from app.schemas.documents import (
    AIExtractResponse,
    AIRefineRequest,
    AIRefineResponse,
    DocumentDetailResponse,
    DocumentListItem,
    DocumentListResponse,
    DocumentMetadataResponse,
    DocumentUploadResponse,
    FieldExtractionUpdateRequest,
    OCRCorrectionRequest,
    OCRResultResponse,
    TagSummaryItem,
    TagSummaryResponse,
    UpdateTagsRequest,
    VerificationResponse,
)
from app.services.ai_service import ai_service
from app.services.document_service import DocumentService
from app.services.extraction_service import extraction_service
from app.services.vietocr_service import vietocr_service
from app.services.search_index_service import search_index_service
from app.services.storage_service import storage_service
from app.services.tag_service import tag_service
from app.worker.tasks import async_process_ocr, process_ocr_task

router = APIRouter(prefix="/documents", tags=["documents"])


def _is_redis_available() -> bool:
    import socket
    try:
        sock = socket.create_connection((settings.redis_host, settings.redis_port), timeout=0.2)
        sock.close()
        return True
    except Exception:
        return False


def _sanitize_filename(name: str) -> str:
    """Loại bỏ ký tự nguy hiểm và path traversal khỏi tên file upload."""
    base = os.path.basename(name.replace("\\", "/"))
    sanitized = re.sub(r'[^a-zA-Z0-9._\-+ ()\[\]]', '_', base)
    return sanitized.strip() or "uploaded_document"


def _validate_magic_bytes(data: bytes, ext: str) -> bool:
    """
    Kiểm tra magic bytes thực tế của file: PDF, PNG, JPEG, TIFF.
    Ngăn chặn tấn công spoofing phần mở rộng file.
    """
    if len(data) < 4:
        return False
    if ext == "pdf":
        return data.startswith(b"%PDF")
    elif ext == "png":
        return data.startswith(b"\x89PNG\r\n\x1a\n") or data.startswith(b"\x89PNG")
    elif ext in ("jpg", "jpeg"):
        return data.startswith(b"\xff\xd8\xff")
    elif ext in ("tif", "tiff"):
        return data.startswith(b"II*\x00") or data.startswith(b"MM\x00*")
    return False


@router.get(
    "",
    response_model=DocumentListResponse,
    summary="Lấy danh sách tài liệu (Phân quyền theo vai trò & Lọc đa chiều theo Tag)",
)
async def list_documents(
    page: int = Query(1, ge=1, description="Trang hiện tại"),
    page_size: int = Query(10, ge=1, le=100, description="Số mục trên mỗi trang"),
    ocr_status: str | None = Query(None, description="Lọc theo trạng thái OCR"),
    category_id: UUID | None = Query(None, description="Lọc theo danh mục"),
    tag: str | None = Query(None, description="Lọc theo thẻ nhãn phân loại (vd: #K44, #MienGiamHocPhi, #HoNgheo)"),
    search: str | None = Query(None, description="Tìm kiếm theo tiêu đề, tên file, MSSV, số hiệu"),
    token: str | None = Query(None, description="JWT Access Token"),
    current_user: User | None = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_db),
) -> DocumentListResponse:
    if not current_user and token:
        current_user = await _resolve_user_from_token(token, db)

    stmt = (
        select(Document)
        .where(Document.is_deleted == False)
        .options(
            selectinload(Document.uploader),
            selectinload(Document.category),
            selectinload(Document.ocr_results),
            selectinload(Document.metadata_),
            selectinload(Document.processing_jobs),
        )
    )

    # RBAC Filtering
    if current_user:
        role_name = current_user.role.name if current_user.role else "STUDENT"
        if role_name == "STUDENT":
            stmt = stmt.where(
                (Document.uploaded_by == current_user.id) |
                (Document.uploaded_by == None) |
                (Document.ocr_status == "APPROVED")
            )
    else:
        stmt = stmt.where(Document.ocr_status == "APPROVED")

    if ocr_status:
        stmt = stmt.where(Document.ocr_status == ocr_status.upper())
    if category_id:
        stmt = stmt.where(Document.category_id == category_id)
    if search:
        search_pattern = f"%{search.strip()}%"
        stmt = stmt.outerjoin(Document.metadata_).outerjoin(Document.ocr_results).outerjoin(Document.uploader)
        stmt = stmt.where(
            Document.title.ilike(search_pattern) |
            Document.original_filename.ilike(search_pattern) |
            DocumentMetadata.student_id.ilike(search_pattern) |
            DocumentMetadata.student_name.ilike(search_pattern) |
            DocumentMetadata.document_number.ilike(search_pattern) |
            User.mssv.ilike(search_pattern) |
            User.full_name.ilike(search_pattern) |
            OCRResult.raw_text.ilike(search_pattern) |
            OCRResult.corrected_text.ilike(search_pattern)
        ).distinct()

    count_stmt = select(func.count()).select_from(stmt.subquery())
    total_res = await db.execute(count_stmt)
    total = total_res.scalar_one() or 0

    offset = (page - 1) * page_size
    stmt = stmt.order_by(Document.created_at.desc()).offset(offset).limit(page_size)
    res = await db.execute(stmt)
    docs = res.scalars().all()

    items: list[DocumentListItem] = []
    target_tag = tag.strip().lower() if tag else None

    for doc in docs:
        confidence = None
        raw_or_corr_text = ""
        is_corrected = False
        for ocr in doc.ocr_results:
            if ocr.is_latest:
                if ocr.confidence_score is not None:
                    confidence = float(ocr.confidence_score)
                raw_or_corr_text = ocr.corrected_text or ocr.raw_text or ""
                is_corrected = ocr.is_corrected
                break

        # Ưu tiên lấy student_name & mssv từ metadata bóc tách
        uploader_name = doc.uploader.full_name if doc.uploader else None
        uploader_mssv = doc.uploader.mssv if doc.uploader else None
        doc_num = None
        doc_tags: list[str] = []

        if doc.metadata_:
            if doc.metadata_.student_name:
                uploader_name = doc.metadata_.student_name
            if doc.metadata_.student_id:
                uploader_mssv = doc.metadata_.student_id
            doc_num = doc.metadata_.document_number
            extra_dict = doc.metadata_.extra or {}
            saved_tags = extra_dict.get("tags")
            if saved_tags and isinstance(saved_tags, list):
                doc_tags = tag_service.sort_tags_by_priority(saved_tags)
            elif raw_or_corr_text:
                doc_tags = tag_service.generate_auto_tags(
                    text=raw_or_corr_text,
                    metadata={
                        "student_id": uploader_mssv,
                        "student_name": uploader_name,
                        "extra": extra_dict,
                    },
                    ocr_status=doc.ocr_status,
                    is_corrected=is_corrected,
                    confidence_score=confidence,
                )
        elif raw_or_corr_text:
            doc_tags = tag_service.generate_auto_tags(
                text=raw_or_corr_text,
                metadata={},
                ocr_status=doc.ocr_status,
            )

        # Lọc theo tag nếu được yêu cầu
        if target_tag:
            tag_matches = any(
                target_tag == t.lower() or target_tag == t.lstrip("#").lower()
                for t in doc_tags
            )
            if not tag_matches:
                continue

        # Lấy ocr_progress từ ProcessingJob gần nhất
        ocr_progress = 0
        if doc.ocr_status in ("DONE", "APPROVED"):
            ocr_progress = 100
        elif doc.ocr_status == "FAILED":
            ocr_progress = 0
        elif doc.processing_jobs:
            latest_job = max(doc.processing_jobs, key=lambda j: j.created_at, default=None)
            if latest_job:
                ocr_progress = getattr(latest_job, "ocr_progress", 0) or 0

        priority_score = tag_service.calculate_priority_score(doc_tags)

        items.append(
            DocumentListItem(
                id=doc.id,
                title=doc.title,
                original_filename=doc.original_filename,
                file_type=doc.file_type,
                file_size_bytes=doc.file_size_bytes,
                page_count=doc.page_count,
                category_id=doc.category_id,
                category_name=doc.category.name if doc.category else None,
                category_code=doc.category.code if doc.category else None,
                uploaded_by=doc.uploaded_by,
                ocr_status=doc.ocr_status,
                minio_object_key=doc.minio_object_key,
                is_deleted=doc.is_deleted,
                ocr_confidence=confidence,
                confidence_score=confidence,
                student_id=uploader_mssv,
                student_name=uploader_name,
                uploader_mssv=uploader_mssv,
                uploader_name=uploader_name,
                document_number=doc_num,
                tags=doc_tags,
                priority_score=priority_score,
                ocr_progress=ocr_progress,
                created_at=doc.created_at,
                updated_at=doc.updated_at,
            )
        )

    total_pages = math.ceil(total / page_size) if total > 0 else 0
    return DocumentListResponse(
        total=len(items) if target_tag else total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
        items=items,
    )


@router.get(
    "/categories",
    summary="Lấy danh sách các danh mục tài liệu hành chính CTSV",
)
async def list_categories(
    db: AsyncSession = Depends(get_db),
):
    stmt = select(DocumentCategory).order_by(DocumentCategory.sort_order.asc())
    res = await db.execute(stmt)
    cats = res.scalars().all()
    return [{"id": c.id, "name": c.name, "code": c.code, "description": c.description} for c in cats]


@router.get(
    "/export/excel",
    summary="Xuất danh sách hồ sơ sinh viên ra file CSV / Excel",
)
async def export_documents_excel(
    ocr_status: str | None = Query(None),
    category_id: UUID | None = Query(None),
    current_user: User = Depends(require_roles(["ADMIN", "STAFF"])),
    db: AsyncSession = Depends(get_db),
):
    """Xuất toàn bộ danh sách hồ sơ kèm thông tin sinh viên, mã số, điểm tin cậy ra file CSV."""
    stmt = (
        select(Document)
        .where(Document.is_deleted == False)
        .options(
            selectinload(Document.uploader),
            selectinload(Document.category),
            selectinload(Document.ocr_results),
            selectinload(Document.metadata_),
        )
        .order_by(Document.created_at.desc())
    )
    if ocr_status:
        stmt = stmt.where(Document.ocr_status == ocr_status.upper())
    if category_id:
        stmt = stmt.where(Document.category_id == category_id)

    res = await db.execute(stmt)
    docs = res.scalars().all()

    output = io.StringIO()
    # Write UTF-8 BOM để Excel hiển thị đúng tiếng Việt không bị lỗi font
    output.write("\ufeff")
    writer = csv.writer(output)
    writer.writerow([
        "Mã hồ sơ",
        "Tiêu đề hồ sơ",
        "Tên file gốc",
        "MSSV",
        "Họ và tên sinh viên",
        "Danh mục",
        "Trạng thái OCR",
        "Độ tin cậy OCR (%)",
        "Thời gian tải lên",
    ])

    for d in docs:
        conf = ""
        for o in d.ocr_results:
            if o.is_latest and o.confidence_score is not None:
                conf = f"{float(o.confidence_score) * 100:.1f}%"
                break

        mssv = (d.metadata_.student_id if d.metadata_ and d.metadata_.student_id else (d.uploader.mssv if d.uploader else "")) or ""
        name = (d.metadata_.student_name if d.metadata_ and d.metadata_.student_name else (d.uploader.full_name if d.uploader else "")) or ""
        cat = d.category.name if d.category else "Chưa phân loại"

        writer.writerow([
            str(d.id),
            d.title,
            d.original_filename,
            mssv,
            name,
            cat,
            d.ocr_status,
            conf,
            d.created_at.strftime("%d/%m/%Y %H:%M:%S") if d.created_at else "",
        ])

    csv_data = output.getvalue().encode("utf-8-sig")
    filename = f"Danh_sach_ho_so_CTSV_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}.csv"
    encoded_filename = urllib.parse.quote(filename)

    return Response(
        content=csv_data,
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": f"attachment; filename*=UTF-8''{encoded_filename}"},
    )


@router.post(
    "/upload",
    response_model=DocumentUploadResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Upload tài liệu mới và đưa vào hàng đợi OCR",
)
@limiter.limit("20/minute")
async def upload_document(
    request: Request,
    file: UploadFile = File(..., description="File tài liệu cần OCR (PDF, JPG, PNG, TIFF)"),
    title: str | None = Form(None, description="Tiêu đề tài liệu"),
    category_id: UUID | None = Form(None, description="ID danh mục tài liệu"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> DocumentUploadResponse:
    raw_filename = file.filename or "uploaded_document"
    filename = _sanitize_filename(raw_filename)
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""

    if ext not in settings.allowed_file_types:
        raise UnsupportedFileTypeException(ext)

    # Đọc file theo chunk và dừng sớm nếu vượt max_file_size_bytes
    CHUNK_SIZE = 1024 * 1024  # 1MB
    chunks = []
    total_size = 0
    while True:
        chunk = await file.read(CHUNK_SIZE)
        if not chunk:
            break
        total_size += len(chunk)
        if total_size > settings.max_file_size_bytes:
            raise FileTooLargeException(
                size_mb=total_size / (1024 * 1024),
                max_mb=settings.max_file_size_mb,
            )
        chunks.append(chunk)

    content = b"".join(chunks)
    file_size = total_size

    # Kiểm tra magic bytes
    if not _validate_magic_bytes(content, ext):
        raise AppException(
            message=f"Định dạng nội dung file không hợp lệ (magic bytes không khớp với .{ext})",
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    doc_title = title.strip() if title and title.strip() else filename

    minio_object_key = storage_service.upload_file(
        file_data=content,
        filename=filename,
        content_type=file.content_type or "application/octet-stream",
    )

    doc_service = DocumentService(db)
    user_id = current_user.id
    document, job = await doc_service.create_document(
        title=doc_title,
        original_filename=filename,
        file_type=ext,
        file_size_bytes=file_size,
        minio_object_key=minio_object_key,
        uploaded_by=user_id,
        category_id=category_id,
    )

    celery_task_id = None
    # Khởi chạy tác vụ OCR nền
    asyncio.create_task(async_process_ocr(str(document.id), task_id="async_worker"))

    return DocumentUploadResponse(
        id=document.id,
        title=document.title,
        original_filename=document.original_filename,
        file_type=document.file_type,
        file_size_bytes=document.file_size_bytes,
        ocr_status=document.ocr_status,
        minio_object_key=document.minio_object_key,
        job_id=job.id,
        celery_task_id=celery_task_id,
        created_at=document.created_at,
    )


@router.get(
    "/{document_id}",
    response_model=DocumentDetailResponse,
    summary="Lấy chi tiết tài liệu và trạng thái xử lý OCR",
)
async def get_document(
    document_id: UUID,
    token: str | None = Query(None, description="JWT Access Token"),
    current_user: User | None = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_db),
) -> DocumentDetailResponse:
    if not current_user and token:
        current_user = await _resolve_user_from_token(token, db)

    doc_service = DocumentService(db)
    detail = await doc_service.get_document_by_id(document_id)

    if current_user:
        role_name = current_user.role.name if current_user.role else "STUDENT"
        if (
            role_name == "STUDENT"
            and detail.uploaded_by is not None
            and detail.uploaded_by != current_user.id
            and detail.ocr_status != "APPROVED"
        ):
            raise AppException(
                message="Bạn không có quyền truy cập hồ sơ này",
                status_code=status.HTTP_403_FORBIDDEN,
            )

        # Cấp signed URL hoặc file ticket ngắn hạn cho preview
        try:
            signed = storage_service.get_signed_url(detail.minio_object_key, expires_in=180)
            if signed:
                detail.file_url = signed
            else:
                ticket = create_file_ticket(str(detail.id), str(current_user.id), ttl_seconds=180)
                detail.file_url = f"/api/v1/documents/{detail.id}/file?ticket={ticket}"
        except Exception as exc:
            logger.debug("Could not generate pre-signed file URL: {err}", err=str(exc))
    return detail


@router.post(
    "/{document_id}/file-url",
    summary="Cấp signed URL ngắn hạn (TTL 60-300s) hoặc file ticket dùng 1 lần",
)
async def get_document_file_url(
    document_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Tạo signed URL hoặc file ticket dùng 1 lần để xem file tài liệu."""
    doc = await db.get(Document, document_id)
    if not doc or doc.is_deleted:
        raise DocumentNotFoundException(str(document_id))

    role_name = current_user.role.name if current_user.role else "STUDENT"
    is_allowed = False
    if doc.ocr_status == "APPROVED" and getattr(doc, "is_public", False):
        is_allowed = True
    elif role_name in ("ADMIN", "STAFF") or (doc.uploaded_by is not None and doc.uploaded_by == current_user.id):
        is_allowed = True

    if not is_allowed:
        raise AppException("Bạn không có quyền truy cập tệp tài liệu này", status_code=status.HTTP_403_FORBIDDEN)

    signed = storage_service.get_signed_url(doc.minio_object_key, expires_in=180)
    ticket = create_file_ticket(str(doc.id), str(current_user.id), ttl_seconds=180)
    ticket_url = f"/api/v1/documents/{doc.id}/file?ticket={ticket}"
    return {
        "file_url": signed or ticket_url,
        "signed_url": signed,
        "ticket": ticket,
        "ticket_url": ticket_url,
        "expires_in": 180,
    }


@router.api_route(
    "/{document_id}/file",
    methods=["GET", "HEAD"],
    summary="Xem trực tiếp file gốc của tài liệu (PDF / Hình ảnh - Có kiểm soát RBAC)",
)
async def view_document_file(
    document_id: UUID,
    ticket: str | None = Query(None, description="Single-use file ticket ngắn hạn"),
    current_user: User | None = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_db),
):
    """Truy xuất file nhị phân gốc từ Storage kèm xác thực quyền truy cập RBAC."""
    doc = await db.get(Document, document_id)
    if not doc or doc.is_deleted:
        raise DocumentNotFoundException(str(document_id))

    # Quyền xem tệp tài liệu (P0 Rule 9):
    # 1. Vé dùng một lần (ticket) hợp lệ và chưa hết hạn (TTL 60-300s)
    # 2. Hoặc tài liệu APPROVED và được đánh dấu public
    # 3. Hoặc người dùng đăng nhập là ADMIN/STAFF hoặc chính người upload
    # Lưu ý: Tài liệu uploaded_by is None KHÔNG được mặc định công khai.
    is_allowed = False
    if ticket and validate_and_consume_file_ticket(ticket, str(document_id)):
        is_allowed = True
    elif doc.ocr_status == "APPROVED" and getattr(doc, "is_public", False):
        is_allowed = True
    elif current_user:
        role_name = current_user.role.name if current_user.role else "STUDENT"
        if role_name in ("ADMIN", "STAFF") or (doc.uploaded_by is not None and doc.uploaded_by == current_user.id):
            is_allowed = True

    if not is_allowed:
        if not current_user and not ticket:
            raise AppException(
                message="Vui lòng đăng nhập để thực hiện thao tác này",
                status_code=status.HTTP_401_UNAUTHORIZED,
            )
        raise AppException(
            message="Bạn không có quyền xem tệp tài liệu này",
            status_code=status.HTTP_403_FORBIDDEN,
        )

    file_bytes = await asyncio.to_thread(storage_service.get_file, doc.minio_object_key)
    if not file_bytes:
        raise AppException(message="Không tìm thấy file trên hệ thống lưu trữ", status_code=404)

    ext = doc.file_type.lower().replace(".", "")
    media_types = {
        "pdf": "application/pdf",
        "png": "image/png",
        "jpg": "image/jpeg",
        "jpeg": "image/jpeg",
        "webp": "image/webp",
        "tiff": "image/tiff",
    }
    media_type = media_types.get(ext, "application/octet-stream")

    encoded_filename = urllib.parse.quote(doc.original_filename or f"document.{ext}")
    return Response(
        content=file_bytes,
        media_type=media_type,
        headers={"Content-Disposition": f"inline; filename*=UTF-8''{encoded_filename}"},
    )


@router.put(
    "/{document_id}/ocr-correction",
    response_model=DocumentDetailResponse,
    summary="Cán bộ CTSV hiệu chỉnh văn bản OCR (Side-by-Side Live Editor)",
)
async def correct_ocr_text(
    document_id: UUID,
    req: OCRCorrectionRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> DocumentDetailResponse:
    """
    Lưu văn bản sau khi cán bộ CTSV đối chiếu và chỉnh sửa sai sót OCR.
    Tự động kích hoạt lại Smart Extraction và cập nhật chỉ mục Elasticsearch.
    """
    doc = await db.get(Document, document_id)
    if not doc or doc.is_deleted:
        raise DocumentNotFoundException(str(document_id))

    target_engine = req.engine or "vietocr"
    if target_engine not in OCR_ENGINES and target_engine != "manual_correction":
        raise ValidationException(
            f"Engine '{target_engine}' không hợp lệ. Các engine hợp lệ: {', '.join(OCR_ENGINES)}",
            status_code=422,
        )

    # Tìm OCRResult mới nhất của engine này
    stmt = (
        select(OCRResult)
        .where(
            OCRResult.document_id == document_id,
            OCRResult.ocr_engine == target_engine,
            OCRResult.is_latest == True,
        )
    )
    res = await db.execute(stmt)
    ocr_result = res.scalars().first()

    now = datetime.now()
    if not ocr_result:
        # Nếu chưa có kết quả cho engine này, tìm bất kỳ bản ghi is_latest nào làm base hoặc tạo mới
        ocr_result = OCRResult(
            document_id=document_id,
            is_latest=True,
            raw_text=req.corrected_text,
            corrected_text=req.corrected_text,
            is_corrected=True,
            corrected_by=current_user.id,
            corrected_at=now,
            confidence_score=1.0,
            ocr_engine=target_engine,
            status="DONE",
        )
        db.add(ocr_result)
    else:
        ocr_result.corrected_text = req.corrected_text
        ocr_result.is_corrected = True
        ocr_result.corrected_by = current_user.id
        ocr_result.corrected_at = now
        ocr_result.updated_at = now

    # Bóc tách lại thông tin từ văn bản đã sửa
    extracted = extraction_service.extract_metadata(req.corrected_text)
    stmt_meta = select(DocumentMetadata).where(DocumentMetadata.document_id == document_id)
    meta_res = await db.execute(stmt_meta)
    meta_obj = meta_res.scalars().first()

    if not meta_obj:
        meta_obj = DocumentMetadata(
            document_id=document_id,
            student_id=extracted.get("student_id"),
            student_name=extracted.get("student_name"),
            document_date=extracted.get("document_date"),
            extra=extracted.get("extra"),
        )
        db.add(meta_obj)
    else:
        if extracted.get("student_id"):
            meta_obj.student_id = extracted["student_id"]
        if extracted.get("student_name"):
            meta_obj.student_name = extracted["student_name"]
        if extracted.get("document_date"):
            meta_obj.document_date = extracted["document_date"]
        if extracted.get("extra"):
            merged_extra = meta_obj.extra or {}
            merged_extra.update(extracted["extra"])
            meta_obj.extra = merged_extra

    # Ghi Audit Log
    audit = AuditLog(
        user_id=current_user.id,
        action="CORRECT_OCR_TEXT",
        resource_type="document",
        resource_id=document_id,
        detail={
            "length": len(req.corrected_text),
            "engine": target_engine,
            "user_role": current_user.role.name if current_user.role else "USER",
        },
        created_at=now,
    )
    db.add(audit)
    await db.commit()

    # Cập nhật Elasticsearch
    try:
        await search_index_service.update_corrected_text(
            document_id=doc.id,
            corrected_text=req.corrected_text,
        )
    except Exception as exc:
        logger.warning("Failed to update corrected text in ES: {err}", err=str(exc))

    logger.info("Updated corrected OCR text for doc {id} (engine={eng}) by user {user}",
                id=document_id, eng=target_engine, user=current_user.id)
    doc_service = DocumentService(db)
    return await doc_service.get_document_by_id(document_id)


@router.post(
    "/{document_id}/reprocess-ocr",
    summary="Chạy lại quy trình OCR cho tài liệu theo engine (ADMIN, STAFF)",
)
async def reprocess_document_ocr(
    document_id: UUID,
    engine: str | None = Query(None, description="vietocr, trocr, hoặc tesseract"),
    current_user: User = Depends(require_roles(["ADMIN", "STAFF"])),
    db: AsyncSession = Depends(get_db),
):
    """Kích hoạt lại tác vụ OCR nền cho một engine cụ thể (hoặc mặc định vietocr)."""
    if engine is not None and engine not in OCR_ENGINES:
        raise ValidationException(
            f"Engine '{engine}' không hợp lệ. Các engine được hỗ trợ: {', '.join(OCR_ENGINES)}",
            status_code=422,
        )

    doc = await db.get(Document, document_id)
    if not doc or doc.is_deleted:
        raise DocumentNotFoundException(str(document_id))

    target_engine = engine or DEFAULT_OCR_ENGINE
    asyncio.create_task(async_process_ocr(str(document_id), task_id="reprocess_worker", engine=target_engine))
    return {
        "message": f"Đang chạy lại OCR ({target_engine}) cho tài liệu",
        "document_id": document_id,
        "status": "PROCESSING",
        "engine": target_engine,
    }


@router.get(
    "/{document_id}/ocr-results/{engine}",
    response_model=OCRResultResponse,
    summary="Lấy kết quả OCR mới nhất của một engine cụ thể (404 nếu chưa từng chạy)",
)
async def get_document_ocr_result_by_engine(
    document_id: UUID,
    engine: str,
    current_user: User | None = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_db),
) -> OCRResultResponse:
    """Trả về kết quả OCR của riêng 1 engine (vietocr | trocr | tesseract)."""
    if engine not in OCR_ENGINES:
        raise ValidationException(
            f"Engine '{engine}' không hợp lệ. Các engine được hỗ trợ: {', '.join(OCR_ENGINES)}",
            status_code=422,
        )

    doc = await db.get(Document, document_id)
    if not doc or doc.is_deleted:
        raise DocumentNotFoundException(str(document_id))

    stmt = (
        select(OCRResult)
        .where(
            OCRResult.document_id == document_id,
            OCRResult.ocr_engine == engine,
            OCRResult.is_latest == True,
        )
    )
    res = await db.execute(stmt)
    ocr = res.scalars().first()
    if not ocr:
        raise NotFoundException(f"kết quả OCR của engine '{engine}' cho tài liệu", str(document_id))

    return OCRResultResponse.model_validate(ocr)


@router.post(
    "/{document_id}/compare-models",
    summary="Thực nghiệm so sánh đa mô hình (VietOCR vs Microsoft TrOCR vs Tesseract) trên cùng tài liệu",
)
async def compare_document_ocr_models(
    document_id: UUID,
    current_user: User = Depends(require_roles(["ADMIN", "STAFF"])),
    db: AsyncSession = Depends(get_db),
):
    """
    Thực hiện so sánh đối chứng song song 3 mô hình OCR:
    - VietOCR (Seq2Seq Transformer - Fine-tuned)
    - Microsoft TrOCR (Vision Transformer)
    - Tesseract 5 (LSTM Baseline)
    """
    doc = await db.get(Document, document_id)
    if not doc or doc.is_deleted:
        raise DocumentNotFoundException(str(document_id))

    file_bytes = await asyncio.to_thread(storage_service.get_file, doc.minio_object_key)
    if not file_bytes:
        raise AppException(message="Không tìm thấy file trên hệ thống lưu trữ", status_code=404)

    results = await asyncio.to_thread(vietocr_service.compare_ocr_engines, file_bytes, doc.file_type)
    return {
        "document_id": document_id,
        "filename": doc.original_filename,
        "comparison": results,
    }


@router.get(
    "/tags/summary",
    response_model=TagSummaryResponse,
    summary="Lấy danh sách thống kê toàn bộ thẻ nhãn (Tags) phục vụ thanh lọc 1-Click",
)
async def get_tags_summary(
    current_user: User | None = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_db),
) -> TagSummaryResponse:
    """
    Thống kê tần suất xuất hiện của tất cả các nhãn trong hệ thống,
    kèm phân cấp mức độ ưu tiên và màu sắc trực quan (Red, Amber, Blue, Purple, Gray).
    """
    stmt = (
        select(Document)
        .where(Document.is_deleted == False)
        .options(
            selectinload(Document.metadata_),
            selectinload(Document.ocr_results),
        )
    )
    res = await db.execute(stmt)
    docs = res.scalars().all()

    tag_counts: dict[str, int] = {}
    for doc in docs:
        doc_tags: list[str] = []
        raw_text = ""
        for ocr in doc.ocr_results:
            if ocr.is_latest:
                raw_text = ocr.corrected_text or ocr.raw_text or ""
                break

        if doc.metadata_ and doc.metadata_.extra and "tags" in doc.metadata_.extra:
            saved = doc.metadata_.extra.get("tags")
            if isinstance(saved, list):
                doc_tags = saved
        elif raw_text:
            doc_tags = tag_service.generate_auto_tags(
                text=raw_text,
                metadata={
                    "student_id": doc.metadata_.student_id if doc.metadata_ else None,
                    "student_name": doc.metadata_.student_name if doc.metadata_ else None,
                },
                ocr_status=doc.ocr_status,
            )

        for t in set(doc_tags):
            if t:
                tag_counts[t] = tag_counts.get(t, 0) + 1

    items: list[TagSummaryItem] = []
    for tag, count in tag_counts.items():
        prio = tag_service.get_tag_priority(tag)
        color = tag_service.get_tag_color(tag)
        category = "Ưu tiên" if prio >= 90 else ("Chính sách" if prio >= 70 else ("Định danh" if prio >= 30 else "Thủ tục"))
        items.append(
            TagSummaryItem(
                tag=tag,
                count=count,
                priority=prio,
                color=color,
                category=category,
            )
        )

    # Sắp xếp theo thứ tự ưu tiên từ cao đến thấp, sau đó theo số lượng
    items.sort(key=lambda x: (x.priority, x.count), reverse=True)

    return TagSummaryResponse(
        items=items,
        total_tags=len(items),
    )


@router.put(
    "/{document_id}/tags",
    response_model=DocumentDetailResponse,
    summary="Cập nhật danh sách thẻ nhãn (Tags) cho tài liệu (ADMIN, STAFF)",
)
async def update_document_tags(
    document_id: UUID,
    req: UpdateTagsRequest,
    current_user: User = Depends(require_roles(["ADMIN", "STAFF"])),
    db: AsyncSession = Depends(get_db),
) -> DocumentDetailResponse:
    """Cán bộ CTSV tùy chỉnh, thêm bớt nhãn gán cho tài liệu."""
    doc = await db.get(Document, document_id)
    if not doc or doc.is_deleted:
        raise DocumentNotFoundException(str(document_id))

    stmt_meta = select(DocumentMetadata).where(DocumentMetadata.document_id == document_id)
    meta_res = await db.execute(stmt_meta)
    meta_obj = meta_res.scalars().first()

    clean_tags = [t.strip() if t.strip().startswith("#") else f"#{t.strip()}" for t in req.tags if t and t.strip()]
    sorted_tags = tag_service.sort_tags_by_priority(clean_tags)

    if not meta_obj:
        meta_obj = DocumentMetadata(
            document_id=document_id,
            extra={"tags": sorted_tags},
        )
        db.add(meta_obj)
    else:
        extra_dict = dict(meta_obj.extra or {})
        extra_dict["tags"] = sorted_tags
        meta_obj.extra = extra_dict

    # Ghi Audit Log
    now = datetime.now()
    audit = AuditLog(
        user_id=current_user.id,
        action="UPDATE_TAGS",
        resource_type="document",
        resource_id=document_id,
        detail={"tags": sorted_tags, "user_role": current_user.role.name if current_user.role else "USER"},
        created_at=now,
    )
    db.add(audit)
    await db.commit()

    logger.info("Updated tags for doc {id}: {tags}", id=document_id, tags=sorted_tags)
    doc_service = DocumentService(db)
    return await doc_service.get_document_by_id(document_id)


@router.post(
    "/{document_id}/auto-tag",
    response_model=DocumentDetailResponse,
    summary="Kích hoạt AI tự động gán nhãn lại theo thứ tự ưu tiên (ADMIN, STAFF)",
)
async def auto_tag_document(
    document_id: UUID,
    current_user: User = Depends(require_roles(["ADMIN", "STAFF"])),
    db: AsyncSession = Depends(get_db),
) -> DocumentDetailResponse:
    """
    AI phân tích lại toàn bộ nội dung văn bản OCR và metadata hiện tại để tự động sinh bộ nhãn chuẩn hóa.
    Tuyệt đối không tự sinh số hiệu.
    """
    doc = await db.get(Document, document_id)
    if not doc or doc.is_deleted:
        raise DocumentNotFoundException(str(document_id))

    stmt = select(OCRResult).where(OCRResult.document_id == document_id, OCRResult.is_latest == True)
    res = await db.execute(stmt)
    ocr = res.scalars().first()
    text = (ocr.corrected_text or ocr.raw_text or "") if ocr else ""

    stmt_meta = select(DocumentMetadata).where(DocumentMetadata.document_id == document_id)
    meta_res = await db.execute(stmt_meta)
    meta_obj = meta_res.scalars().first()

    metadata_dict = {
        "student_id": meta_obj.student_id if meta_obj else None,
        "student_name": meta_obj.student_name if meta_obj else None,
        "extra": meta_obj.extra if meta_obj else {},
    }

    auto_tags = tag_service.generate_auto_tags(
        text=text,
        metadata=metadata_dict,
        ocr_status=doc.ocr_status,
        is_corrected=ocr.is_corrected if ocr else False,
        confidence_score=ocr.confidence_score if ocr else None,
    )

    if not meta_obj:
        meta_obj = DocumentMetadata(
            document_id=document_id,
            extra={"tags": auto_tags},
        )
        db.add(meta_obj)
    else:
        extra_dict = dict(meta_obj.extra or {})
        extra_dict["tags"] = auto_tags
        meta_obj.extra = extra_dict

    await db.commit()
    logger.info("Auto-tagged doc {id} with {count} tags", id=document_id, count=len(auto_tags))
    doc_service = DocumentService(db)
    return await doc_service.get_document_by_id(document_id)


@router.post(
    "/{document_id}/extract-fields",
    response_model=DocumentMetadataResponse,
    summary="Tự động bóc tách MSSV, Họ tên, Lý do, Số hiệu từ OCR text (ADMIN, STAFF)",
)
async def trigger_extract_fields(
    document_id: UUID,
    current_user: User = Depends(require_roles(["ADMIN", "STAFF"])),
    db: AsyncSession = Depends(get_db),
) -> DocumentMetadataResponse:
    """Chạy module Smart Form Field Extraction trích xuất thông tin sinh viên và số hiệu thực tế."""
    stmt = select(OCRResult).where(OCRResult.document_id == document_id, OCRResult.is_latest == True)
    res = await db.execute(stmt)
    ocr = res.scalars().first()
    text = (ocr.corrected_text or ocr.raw_text or "") if ocr else ""

    extracted = extraction_service.extract_metadata(text)

    # Tự động gán nhãn
    auto_tags = tag_service.generate_auto_tags(
        text=text,
        metadata=extracted,
        confidence_score=0.85,
    )
    extra_payload = dict(extracted.get("extra") or {})
    extra_payload["tags"] = auto_tags

    stmt_meta = select(DocumentMetadata).where(DocumentMetadata.document_id == document_id)
    meta_res = await db.execute(stmt_meta)
    meta_obj = meta_res.scalars().first()

    if not meta_obj:
        meta_obj = DocumentMetadata(
            document_id=document_id,
            student_id=extracted.get("student_id"),
            student_name=extracted.get("student_name"),
            document_date=extracted.get("document_date"),
            document_number=extracted.get("document_number"),
            extra=extra_payload,
        )
        db.add(meta_obj)
    else:
        if extracted.get("student_id"): meta_obj.student_id = extracted["student_id"]
        if extracted.get("student_name"): meta_obj.student_name = extracted["student_name"]
        if extracted.get("document_date"): meta_obj.document_date = extracted["document_date"]
        if extracted.get("document_number"): meta_obj.document_number = extracted["document_number"]
        current_extra = dict(meta_obj.extra or {})
        current_extra.update(extra_payload)
        meta_obj.extra = current_extra

    await db.commit()
    await db.refresh(meta_obj)
    return DocumentMetadataResponse(
        id=meta_obj.id,
        document_id=meta_obj.document_id,
        student_id=meta_obj.student_id,
        student_name=meta_obj.student_name,
        document_date=meta_obj.document_date,
        document_number=meta_obj.document_number,
        tags=auto_tags,
        priority_score=tag_service.calculate_priority_score(auto_tags),
        extra=meta_obj.extra,
    )


@router.post(
    "/{document_id}/ai-refine",
    response_model=AIRefineResponse,
    summary="Dùng AI (Gemini / OpenAI / Ollama) sửa lỗi chính tả và chuẩn hóa văn bản OCR",
)
async def ai_refine_document_text(
    document_id: UUID,
    req: AIRefineRequest | None = None,
    current_user: User = Depends(require_roles(["ADMIN", "STAFF"])),
    db: AsyncSession = Depends(get_db),
) -> AIRefineResponse:
    """
    Sử dụng mô hình ngôn ngữ lớn để sửa lỗi chính tả OCR, giữ nguyên bố cục hành chính.
    """
    doc = await db.get(Document, document_id)
    if not doc or doc.is_deleted:
        raise DocumentNotFoundException(str(document_id))

    input_text = req.text if (req and req.text) else None
    if not input_text:
        stmt = select(OCRResult).where(OCRResult.document_id == document_id, OCRResult.is_latest == True)
        res = await db.execute(stmt)
        ocr = res.scalars().first()
        input_text = (ocr.corrected_text or ocr.raw_text or "") if ocr else ""

    result = await ai_service.refine_ocr_text(input_text)
    return AIRefineResponse(
        original_text=result.get("original_text", input_text),
        refined_text=result.get("refined_text", input_text),
        provider=result.get("provider", "none"),
        model=result.get("model", "none"),
        success=result.get("success", False),
        message=result.get("message"),
    )


@router.post(
    "/{document_id}/ai-extract",
    response_model=AIExtractResponse,
    summary="Dùng AI trích xuất thực thể thông minh (MSSV, Họ tên, Lớp, Khoa, Lý do, Số tiền, Tóm tắt, Nhãn)",
)
async def ai_extract_document_fields(
    document_id: UUID,
    current_user: User = Depends(require_roles(["ADMIN", "STAFF"])),
    db: AsyncSession = Depends(get_db),
) -> AIExtractResponse:
    """
    Sử dụng AI phân tích ngữ cảnh, bóc tách thực thể sinh viên vào metadata và tự động gán nhãn ưu tiên.
    """
    doc = await db.get(Document, document_id)
    if not doc or doc.is_deleted:
        raise DocumentNotFoundException(str(document_id))

    stmt = select(OCRResult).where(OCRResult.document_id == document_id, OCRResult.is_latest == True)
    res = await db.execute(stmt)
    ocr = res.scalars().first()
    text = (ocr.corrected_text or ocr.raw_text or "") if ocr else ""

    extracted = await ai_service.extract_smart_fields(text)
    auto_tags = extracted.get("tags") or []

    # Cập nhật vào DB metadata
    stmt_meta = select(DocumentMetadata).where(DocumentMetadata.document_id == document_id)
    meta_res = await db.execute(stmt_meta)
    meta_obj = meta_res.scalars().first()

    extra_data = {
        "class_name": extracted.get("class_name"),
        "faculty": extracted.get("faculty"),
        "document_type": extracted.get("document_type"),
        "reason": extracted.get("reason"),
        "amount": extracted.get("amount"),
        "summary": extracted.get("summary"),
        "suggested_action": extracted.get("suggested_action"),
        "ai_provider": extracted.get("provider"),
        "ai_model": extracted.get("model"),
        "tags": auto_tags,
    }

    parsed_date = None
    if extracted.get("document_date"):
        try:
            if isinstance(extracted["document_date"], str):
                parsed_date = datetime.fromisoformat(extracted["document_date"])
            elif isinstance(extracted["document_date"], datetime):
                parsed_date = extracted["document_date"]
        except Exception:
            pass

    if not meta_obj:
        meta_obj = DocumentMetadata(
            document_id=document_id,
            student_id=extracted.get("student_id"),
            student_name=extracted.get("student_name"),
            document_date=parsed_date,
            document_number=extracted.get("document_number"),
            extra=extra_data,
        )
        db.add(meta_obj)
    else:
        if extracted.get("student_id"):
            meta_obj.student_id = extracted["student_id"]
        if extracted.get("student_name"):
            meta_obj.student_name = extracted["student_name"]
        if extracted.get("document_number"):
            meta_obj.document_number = extracted["document_number"]
        if parsed_date:
            meta_obj.document_date = parsed_date
        current_extra = dict(meta_obj.extra or {})
        current_extra.update(extra_data)
        meta_obj.extra = current_extra

    await db.commit()
    await db.refresh(meta_obj)

    return AIExtractResponse(
        student_name=extracted.get("student_name"),
        student_id=extracted.get("student_id"),
        class_name=extracted.get("class_name"),
        faculty=extracted.get("faculty"),
        document_type=extracted.get("document_type"),
        document_number=extracted.get("document_number"),
        reason=extracted.get("reason"),
        amount=extracted.get("amount"),
        document_date=extracted.get("document_date"),
        tags=auto_tags,
        priority_score=tag_service.calculate_priority_score(auto_tags),
        summary=extracted.get("summary"),
        suggested_action=extracted.get("suggested_action"),
        provider=extracted.get("provider", "rule_based"),
        model=extracted.get("model", "regex"),
        confidence_score=extracted.get("confidence_score", 0.9),
    )


@router.get(
    "/{document_id}/verification",
    response_model=VerificationResponse,
    summary="Tra cứu mã QR xác thực hồ sơ điện tử",
)
async def get_document_verification(
    document_id: UUID,
    current_user: User | None = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_db),
) -> VerificationResponse:
    """Lấy thông tin xác thực điện tử công khai và mã băm chứng chỉ."""
    stmt = (
        select(Document)
        .where(Document.id == document_id, Document.is_deleted == False)
        .options(selectinload(Document.uploader), selectinload(Document.metadata_))
    )
    res = await db.execute(stmt)
    doc = res.scalars().first()

    if not doc:
        raise DocumentNotFoundException(str(document_id))

    is_approved = doc.ocr_status == "APPROVED"
    raw_name = doc.metadata_.student_name if doc.metadata_ and doc.metadata_.student_name else (doc.uploader.full_name if doc.uploader else "Sinh viên")
    raw_mssv = doc.metadata_.student_id if doc.metadata_ and doc.metadata_.student_id else (doc.uploader.mssv if doc.uploader else None)

    # Bảo vệ quyền riêng tư nếu người tra cứu không phải chủ tài liệu hoặc cán bộ
    is_privileged = False
    if current_user:
        role_name = current_user.role.name if current_user.role else "STUDENT"
        if role_name in ("ADMIN", "STAFF") or doc.uploaded_by == current_user.id:
            is_privileged = True

    if is_privileged:
        student_name = raw_name
        student_id = raw_mssv
    else:
        # Ẩn danh một phần thông tin cá nhân (Privacy-Preserving Verification)
        if raw_name and len(raw_name) > 3:
            parts = raw_name.split()
            student_name = " ".join([p[0] + "***" for p in parts])
        else:
            student_name = "*** (Đã bảo mật)"
        student_id = f"***{raw_mssv[-3:]}" if raw_mssv and len(raw_mssv) >= 3 else "***"

    # Sinh mã băm xác thực SHA-256
    raw_signature = f"DLU_CTSV_{doc.id}_{doc.title}_{doc.ocr_status}_{doc.created_at.isoformat()}"
    verification_code = hashlib.sha256(raw_signature.encode()).hexdigest()[:16].upper()

    qr_payload = f"https://dlu.edu.vn/verify/{doc.id}?code={verification_code}"

    return VerificationResponse(
        is_valid=is_approved,
        document_id=doc.id,
        title=doc.title,
        original_filename=doc.original_filename,
        ocr_status=doc.ocr_status,
        student_name=student_name,
        student_id=student_id,
        approved_at=doc.updated_at if is_approved else None,
        approved_by_name="Phòng Công tác Sinh viên (DLU)",
        verification_code=verification_code,
        qr_payload=qr_payload,
    )


@router.patch(
    "/{document_id}/approve",
    response_model=DocumentDetailResponse,
    summary="Cán bộ CTSV / Quản trị viên phê duyệt hồ sơ",
)
async def approve_document(
    document_id: UUID,
    current_user: User = Depends(require_roles(["ADMIN", "STAFF"])),
    db: AsyncSession = Depends(get_db),
) -> DocumentDetailResponse:
    doc = await db.get(Document, document_id)
    if not doc or doc.is_deleted:
        raise DocumentNotFoundException(str(document_id))

    old_status = doc.ocr_status
    now = datetime.now()
    doc.ocr_status = "APPROVED"
    doc.updated_at = now

    audit = AuditLog(
        user_id=current_user.id,
        action="APPROVE_DOCUMENT",
        resource_type="document",
        resource_id=document_id,
        detail={"old_status": old_status, "new_status": "APPROVED", "title": doc.title},
        created_at=now,
    )
    db.add(audit)
    await db.commit()

    # Cập nhật trạng thái ES (Partial update - không xóa nội dung content)
    try:
        await search_index_service.update_document_status(
            document_id=doc.id,
            ocr_status="APPROVED",
            updated_at=now,
        )
    except Exception as exc:
        logger.warning("Failed to update status in ES: {err}", err=str(exc))

    logger.info("Approved document {id} by user {user}", id=document_id, user=current_user.id)
    doc_service = DocumentService(db)
    return await doc_service.get_document_by_id(document_id)


@router.patch(
    "/{document_id}/reject",
    response_model=DocumentDetailResponse,
    summary="Cán bộ CTSV / Quản trị viên từ chối hồ sơ",
)
async def reject_document(
    document_id: UUID,
    current_user: User = Depends(require_roles(["ADMIN", "STAFF"])),
    db: AsyncSession = Depends(get_db),
) -> DocumentDetailResponse:
    doc = await db.get(Document, document_id)
    if not doc or doc.is_deleted:
        raise DocumentNotFoundException(str(document_id))

    old_status = doc.ocr_status
    now = datetime.now()
    doc.ocr_status = "REJECTED"
    doc.updated_at = now

    audit = AuditLog(
        user_id=current_user.id,
        action="REJECT_DOCUMENT",
        resource_type="document",
        resource_id=document_id,
        detail={"old_status": old_status, "new_status": "REJECTED", "title": doc.title},
        created_at=now,
    )

    db.add(audit)
    await db.commit()

    # Cập nhật trạng thái ES (Partial update)
    try:
        await search_index_service.update_document_status(
            document_id=doc.id,
            ocr_status="REJECTED",
            updated_at=now,
        )
    except Exception as exc:
        logger.warning("Failed to update status in ES: {err}", err=str(exc))

    logger.info("Rejected document {id} by user {user}", id=document_id, user=current_user.id)
    doc_service = DocumentService(db)
    return await doc_service.get_document_by_id(document_id)
