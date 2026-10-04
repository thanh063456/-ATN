"""
backend/app/services/document_service.py — Document Business Logic

Thực thi logic nghiệp vụ cho tài liệu:
- Tạo Document record và ProcessingJob trong PostgreSQL
- Truy vấn chi tiết tài liệu kèm kết quả OCR mới nhất (is_latest=True)
- Xử lý soft delete và phân quyền cơ bản

Tuân thủ .ai/CODING_RULES.md:
- Service layer chỉ raise custom exception (AppException).
- Không import trực tiếp HTTPException.
"""
from datetime import datetime
from uuid import UUID

from loguru import logger
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.exceptions import DocumentNotFoundException
from app.models.documents import Document, OCR_STATUS_PENDING
from app.models.ocr_results import OCRResult
from app.models.processing_jobs import ProcessingJob, JOB_STATUS_PENDING
from app.models.roles import Role
from app.models.users import User
from app.schemas.documents import (
    DocumentDetailResponse,
    DocumentMetadataResponse,
    DocumentUploadResponse,
    OCRResultResponse,
    ProcessingJobResponse,
)


class DocumentService:
    """Service xử lý nghiệp vụ tài liệu và hàng đợi xử lý."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_or_create_default_user(self) -> User:
        """
        Lấy hoặc tạo tài khoản mặc định (system admin) cho quá trình dev/upload
        khi chưa có JWT token từ client.
        """
        result = await self.db.execute(select(User).limit(1))
        user = result.scalars().first()
        if user:
            return user

        # Tạo Role ADMIN nếu chưa có
        role_result = await self.db.execute(select(Role).where(Role.name == "ADMIN"))
        role = role_result.scalars().first()
        if not role:
            role = Role(name="ADMIN", description="Quản trị viên hệ thống")
            self.db.add(role)
            await self.db.flush()

        # Tạo User admin mặc định
        user = User(
            username="admin",
            email="admin@student-ocr.edu.vn",
            hashed_password="$2b$12$dummyhashedpasswordforinitialsystemdevelopment",
            full_name="Quản trị viên Hệ thống",
            role_id=role.id,
            is_active=True,
        )
        self.db.add(user)
        await self.db.commit()
        await self.db.refresh(user)
        logger.info("Created default system user: id={id}, username={username}", id=user.id, username=user.username)
        return user

    async def create_document(
        self,
        title: str,
        original_filename: str,
        file_type: str,
        file_size_bytes: int,
        minio_object_key: str,
        uploaded_by: UUID | None = None,
        category_id: UUID | None = None,
    ) -> tuple[Document, ProcessingJob]:
        """
        Tạo Document record và ProcessingJob tương ứng trong PostgreSQL.
        Trạng thái ban đầu: Document.ocr_status = PENDING, ProcessingJob.status = PENDING.
        """
        if uploaded_by is None:
            default_user = await self.get_or_create_default_user()
            uploaded_by = default_user.id

        now = datetime.now()

        # 1. Tạo Document
        document = Document(
            title=title,
            original_filename=original_filename,
            file_type=file_type.upper(),
            file_size_bytes=file_size_bytes,
            minio_object_key=minio_object_key,
            category_id=category_id,
            uploaded_by=uploaded_by,
            ocr_status=OCR_STATUS_PENDING,
            is_deleted=False,
            created_at=now,
            updated_at=now,
        )
        self.db.add(document)
        await self.db.flush()  # Sinh document.id

        # 2. Tạo ProcessingJob liên kết
        job = ProcessingJob(
            document_id=document.id,
            status=JOB_STATUS_PENDING,
            retry_count=0,
            created_at=now,
        )
        self.db.add(job)
        await self.db.commit()
        await self.db.refresh(document)
        await self.db.refresh(job)

        logger.info("Created Document (id={doc_id}) and ProcessingJob (id={job_id})",
                    doc_id=document.id, job_id=job.id)
        return document, job

    async def update_job_celery_task_id(self, job_id: UUID, celery_task_id: str) -> None:
        """Cập nhật Celery task ID vào ProcessingJob sau khi dispatch task."""
        job = await self.db.get(ProcessingJob, job_id)
        if job:
            job.celery_task_id = celery_task_id
            await self.db.commit()

    async def get_document_by_id(self, document_id: UUID) -> DocumentDetailResponse:
        """
        Lấy thông tin chi tiết tài liệu kèm:
        - Kết quả OCR mới nhất (is_latest=True)
        - Trạng thái ProcessingJob gần nhất
        - Metadata (nếu có)
        """
        # Query Document
        stmt = (
            select(Document)
            .where(Document.id == document_id, Document.is_deleted == False)
            .options(
                selectinload(Document.ocr_results),
                selectinload(Document.processing_jobs),
                selectinload(Document.metadata_),
            )
        )
        result = await self.db.execute(stmt)
        document = result.scalars().first()

        if not document:
            raise DocumentNotFoundException(str(document_id))

        # Tìm OCR result mới nhất theo từng engine (is_latest == True)
        engine_latest_map: dict[str, OCRResultResponse] = {}
        for ocr in document.ocr_results:
            if ocr.is_latest:
                engine_latest_map[ocr.ocr_engine] = OCRResultResponse.model_validate(ocr)

        all_ocr_results = list(engine_latest_map.values())

        # ocr_result chính: ưu tiên 'vietocr' mới nhất cho backward compatibility
        latest_ocr = engine_latest_map.get("vietocr")
        if not latest_ocr and all_ocr_results:
            latest_ocr = all_ocr_results[0]

        # Tìm ProcessingJob mới nhất
        latest_job = None
        if document.processing_jobs:
            sorted_jobs = sorted(document.processing_jobs, key=lambda j: j.created_at, reverse=True)
            latest_job = ProcessingJobResponse.model_validate(sorted_jobs[0])

        # Metadata & Tags
        meta_response = None
        doc_tags: list[str] = []
        doc_priority: int = 0
        from app.services.tag_service import tag_service

        raw_or_corr_text = ""
        if latest_ocr:
            raw_or_corr_text = latest_ocr.corrected_text or latest_ocr.raw_text or ""

        if document.metadata_:
            extra_dict = document.metadata_.extra or {}
            saved_tags = extra_dict.get("tags")
            if saved_tags and isinstance(saved_tags, list):
                doc_tags = tag_service.sort_tags_by_priority(saved_tags)
            elif raw_or_corr_text:
                doc_tags = tag_service.generate_auto_tags(
                    text=raw_or_corr_text,
                    metadata={
                        "student_id": document.metadata_.student_id,
                        "student_name": document.metadata_.student_name,
                        "extra": extra_dict,
                    },
                    ocr_status=document.ocr_status,
                    is_corrected=latest_ocr.is_corrected if latest_ocr else False,
                    confidence_score=latest_ocr.confidence_score if latest_ocr else None,
                )
            doc_priority = tag_service.calculate_priority_score(doc_tags)
            meta_response = DocumentMetadataResponse(
                id=document.metadata_.id,
                document_id=document.metadata_.document_id,
                student_id=document.metadata_.student_id,
                student_name=document.metadata_.student_name,
                document_date=document.metadata_.document_date,
                document_number=document.metadata_.document_number,
                tags=doc_tags,
                priority_score=doc_priority,
                extra=document.metadata_.extra,
            )
        elif raw_or_corr_text:
            doc_tags = tag_service.generate_auto_tags(
                text=raw_or_corr_text,
                metadata={},
                ocr_status=document.ocr_status,
            )
            doc_priority = tag_service.calculate_priority_score(doc_tags)

        return DocumentDetailResponse(
            id=document.id,
            title=document.title,
            original_filename=document.original_filename,
            file_type=document.file_type,
            file_size_bytes=document.file_size_bytes,
            page_count=document.page_count,
            category_id=document.category_id,
            uploaded_by=document.uploaded_by,
            ocr_status=document.ocr_status,
            minio_object_key=document.minio_object_key,
            is_deleted=document.is_deleted,
            created_at=document.created_at,
            updated_at=document.updated_at,
            ocr_result=latest_ocr,
            all_ocr_results=all_ocr_results,
            processing_job=latest_job,
            metadata=meta_response,
            tags=doc_tags,
            priority_score=doc_priority,
        )
