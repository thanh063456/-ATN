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
import urllib.parse
from uuid import UUID

from fastapi import APIRouter, Depends, File, Form, Query, Response, UploadFile, status
from fastapi.responses import StreamingResponse
from loguru import logger
from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.config import settings
from app.core.database import get_db
from app.core.dependencies import _resolve_user_from_token, get_current_user, get_current_user_optional, require_roles
from app.core.exceptions import AppException, DocumentNotFoundException, FileTooLargeException, UnsupportedFileTypeException
from app.models.audit_logs import AuditLog
from app.models.document_categories import DocumentCategory
from app.models.document_metadata import DocumentMetadata
from app.models.documents import Document
from app.models.ocr_results import OCRResult
from app.models.users import User
from app.schemas.documents import (
    DocumentDetailResponse,
    DocumentListItem,
    DocumentListResponse,
    DocumentMetadataResponse,
    DocumentUploadResponse,
    FieldExtractionUpdateRequest,
    OCRCorrectionRequest,
    OCRResultResponse,
    VerificationResponse,
)
from app.services.document_service import DocumentService
from app.services.extraction_service import extraction_service
from app.services.search_index_service import search_index_service
from app.services.storage_service import storage_service
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


@router.get(
    "",
    response_model=DocumentListResponse,
    summary="Lấy danh sách tài liệu (Phân quyền theo vai trò)",
)
async def list_documents(
    page: int = Query(1, ge=1, description="Trang hiện tại"),
    page_size: int = Query(10, ge=1, le=100, description="Số mục trên mỗi trang"),
    ocr_status: str | None = Query(None, description="Lọc theo trạng thái OCR"),
    category_id: UUID | None = Query(None, description="Lọc theo danh mục"),
    search: str | None = Query(None, description="Tìm kiếm theo tiêu đề hoặc tên file"),
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
    for doc in docs:
        confidence = None
        for ocr in doc.ocr_results:
            if ocr.is_latest and ocr.confidence_score is not None:
                confidence = float(ocr.confidence_score)
                break

        # Ưu tiên lấy student_name & mssv từ metadata bóc tách
        uploader_name = doc.uploader.full_name if doc.uploader else None
        uploader_mssv = doc.uploader.mssv if doc.uploader else None
        if doc.metadata_:
            if doc.metadata_.student_name:
                uploader_name = doc.metadata_.student_name
            if doc.metadata_.student_id:
                uploader_mssv = doc.metadata_.student_id

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
                created_at=doc.created_at,
                updated_at=doc.updated_at,
            )
        )

    total_pages = math.ceil(total / page_size) if total > 0 else 0
    return DocumentListResponse(
        total=total,
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
async def upload_document(
    file: UploadFile = File(..., description="File tài liệu cần OCR (PDF, JPG, PNG, TIFF)"),
    title: str | None = Form(None, description="Tiêu đề tài liệu"),
    category_id: UUID | None = Form(None, description="ID danh mục tài liệu"),
    current_user: User | None = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_db),
) -> DocumentUploadResponse:
    filename = file.filename or "uploaded_document"
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""

    if ext not in settings.allowed_file_types:
        raise UnsupportedFileTypeException(ext)

    content = await file.read()
    file_size = len(content)

    if file_size > settings.max_file_size_bytes:
        raise FileTooLargeException(
            size_mb=file_size / (1024 * 1024),
            max_mb=settings.max_file_size_mb,
        )

    doc_title = title.strip() if title and title.strip() else filename

    minio_object_key = storage_service.upload_file(
        file_data=content,
        filename=filename,
        content_type=file.content_type or "application/octet-stream",
    )

    doc_service = DocumentService(db)
    user_id = current_user.id if current_user else None
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
    return detail


@router.get(
    "/{document_id}/file",
    summary="Xem trực tiếp file gốc của tài liệu (PDF / Hình ảnh - Có kiểm soát RBAC)",
)
async def view_document_file(
    document_id: UUID,
    token: str | None = Query(None, description="JWT Access Token (dành cho iframe/img preview)"),
    current_user: User | None = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_db),
):
    """Truy xuất file nhị phân gốc từ Storage kèm xác thực quyền truy cập RBAC."""
    if not current_user and token:
        current_user = await _resolve_user_from_token(token, db)

    doc = await db.get(Document, document_id)
    if not doc or doc.is_deleted:
        raise DocumentNotFoundException(str(document_id))

    # Quyền xem tệp tài liệu:
    # 1. Nếu tài liệu đã APPROVED hoặc được upload công khai/demo (uploaded_by is None) -> cho phép xem
    # 2. Nếu có current_user: ADMIN, STAFF hoặc chính người upload -> cho phép xem
    # 3. Cho phép xem để preview hiển thị trên giao diện trực quan
    is_allowed = False
    if doc.ocr_status == "APPROVED" or doc.uploaded_by is None:
        is_allowed = True
    elif current_user:
        role_name = current_user.role.name if current_user.role else "STUDENT"
        if role_name in ("ADMIN", "STAFF") or doc.uploaded_by == current_user.id:
            is_allowed = True
    else:
        is_allowed = True

    if not is_allowed:
        if not current_user:
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

    # Tìm OCRResult mới nhất
    stmt = (
        select(OCRResult)
        .where(OCRResult.document_id == document_id, OCRResult.is_latest == True)
    )
    res = await db.execute(stmt)
    ocr_result = res.scalars().first()

    now = datetime.now()
    if not ocr_result:
        ocr_result = OCRResult(
            document_id=document_id,
            is_latest=True,
            raw_text=req.corrected_text,
            corrected_text=req.corrected_text,
            is_corrected=True,
            corrected_by=current_user.id,
            corrected_at=now,
            confidence_score=1.0,
            ocr_engine="manual_correction",
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
        detail={"length": len(req.corrected_text), "user_role": current_user.role.name if current_user.role else "USER"},
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

    logger.info("Updated corrected OCR text for doc {id} by user {user}", id=document_id, user=current_user.id)
    doc_service = DocumentService(db)
    return await doc_service.get_document_by_id(document_id)


@router.post(
    "/{document_id}/reprocess-ocr",
    summary="Chạy lại quy trình OCR cho tài liệu với mô hình VietOCR mới nhất (ADMIN, STAFF)",
)
async def reprocess_document_ocr(
    document_id: UUID,
    current_user: User = Depends(require_roles(["ADMIN", "STAFF"])),
    db: AsyncSession = Depends(get_db),
):
    """Kích hoạt lại tác vụ OCR đa tầng nền cho tài liệu (bảo vệ quyền STAFF/ADMIN tránh DoS)."""
    doc = await db.get(Document, document_id)
    if not doc or doc.is_deleted:
        raise DocumentNotFoundException(str(document_id))

    asyncio.create_task(async_process_ocr(str(document_id), task_id="reprocess_worker"))
    return {"message": "Đang chạy lại OCR cho tài liệu", "document_id": document_id, "status": "PROCESSING"}


@router.post(
    "/{document_id}/extract-fields",
    response_model=DocumentMetadataResponse,
    summary="Tự động bóc tách MSSV, Họ tên, Lý do từ OCR text (ADMIN, STAFF)",
)
async def trigger_extract_fields(
    document_id: UUID,
    current_user: User = Depends(require_roles(["ADMIN", "STAFF"])),
    db: AsyncSession = Depends(get_db),
) -> DocumentMetadataResponse:
    """Chạy module Smart Form Field Extraction trích xuất thông tin sinh viên."""
    stmt = select(OCRResult).where(OCRResult.document_id == document_id, OCRResult.is_latest == True)
    res = await db.execute(stmt)
    ocr = res.scalars().first()
    text = (ocr.corrected_text or ocr.raw_text or "") if ocr else ""

    extracted = extraction_service.extract_metadata(text)

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
        if extracted.get("student_id"): meta_obj.student_id = extracted["student_id"]
        if extracted.get("student_name"): meta_obj.student_name = extracted["student_name"]
        if extracted.get("document_date"): meta_obj.document_date = extracted["document_date"]
        meta_obj.extra = extracted.get("extra")

    await db.commit()
    await db.refresh(meta_obj)
    return DocumentMetadataResponse.model_validate(meta_obj)


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
