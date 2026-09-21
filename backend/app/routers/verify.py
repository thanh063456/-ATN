"""
backend/app/routers/verify.py — Public Document Verification Endpoint

Cho phép quét mã QR hoặc truy cập đường link xác minh công khai để kiểm tra tính hợp lệ
của văn bản/hồ sơ sinh viên đã được Phòng Công tác Sinh viên (DLU) phê duyệt.
"""
from datetime import datetime
import hashlib
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.models.documents import Document
from app.schemas.documents import VerificationResponse

router = APIRouter(prefix="/verify", tags=["verify"])


@router.get(
    "/{document_id}",
    response_model=VerificationResponse,
    summary="Xác thực hồ sơ sinh viên công khai qua mã QR",
)
async def public_verify_document(
    document_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> VerificationResponse:
    """Kiểm tra và trả về chứng chỉ xác thực điện tử công khai của tài liệu."""
    stmt = (
        select(Document)
        .where(Document.id == document_id, Document.is_deleted == False)
        .options(selectinload(Document.uploader), selectinload(Document.metadata_))
    )
    res = await db.execute(stmt)
    doc = res.scalars().first()

    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Không tìm thấy hồ sơ hoặc hồ sơ không tồn tại trên hệ thống DLU.",
        )

    is_approved = doc.ocr_status == "APPROVED"
    student_name = (
        doc.metadata_.student_name
        if doc.metadata_ and doc.metadata_.student_name
        else (doc.uploader.full_name if doc.uploader else "Sinh viên")
    )
    student_id = (
        doc.metadata_.student_id
        if doc.metadata_ and doc.metadata_.student_id
        else (doc.uploader.mssv if doc.uploader else None)
    )

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
        issued_by="Trường Đại học Đà Lạt - Phòng Công tác Sinh viên (DocuCTSV)",
    )
