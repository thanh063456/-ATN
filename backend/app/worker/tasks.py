"""
backend/app/worker/tasks.py — Celery Tasks for OCR Pipeline

Luồng xử lý chuẩn theo .ai/AGENTS.md:
1. Đánh dấu Job RUNNING và Document PROCESSING.
2. Lấy thông tin Document từ PostgreSQL -> nhận minio_object_key.
3. Đọc dữ liệu file nhị phân từ Supabase Storage qua storage_service.get_file(doc.minio_object_key).
4. Chạy tiền xử lý và gọi mô hình VietOCR qua ocr_service.
5. Trích xuất metadata (MSSV, Họ tên, Ngày, Số hiệu) tự động.
6. Lưu OCRResult vào PostgreSQL (is_latest=True, reset các bản ghi cũ về False).
7. Lưu/Cập nhật DocumentMetadata.
8. Cập nhật Document.ocr_status = "DONE", ProcessingJob.status = "SUCCESS".
9. Backend chủ động index sang Elasticsearch (search_index_service).
"""
import asyncio
from datetime import date, datetime
import time
from uuid import UUID

from loguru import logger
from sqlalchemy import select, update
from sqlalchemy.orm import selectinload

from app.core.config import settings
from app.core.database import AsyncSessionLocal
from app.models.document_metadata import DocumentMetadata
from app.models.documents import Document
from app.models.ocr_results import OCRResult
from app.models.processing_jobs import ProcessingJob
from app.services.ai_service import ai_service
from app.services.vietocr_service import vietocr_service
from app.services.trocr_service import trocr_service
from app.services.search_index_service import search_index_service
from app.services.storage_service import storage_service
from app.services.tag_service import tag_service
from app.worker.celery_app import celery_app


async def async_process_ocr(document_id: str, task_id: str | None = None, engine: str | None = None) -> dict:
    """Coroutine thực thi toàn bộ logic OCR, Metadata Extraction và Elasticsearch indexing."""
    doc_uuid = UUID(document_id)
    now = datetime.now()
    logger.info("Starting async OCR processing for document_id={doc_id}", doc_id=document_id)

    async def _set_progress(session, progress: int) -> None:
        """Cập nhật tiến độ OCR (0-100%) vào ProcessingJob và commit ngay."""
        try:
            await session.execute(
                update(ProcessingJob)
                .where(ProcessingJob.document_id == doc_uuid)
                .values(ocr_progress=progress)
            )
            await session.commit()
        except Exception:
            pass  # Không để lỗi progress làm hỏng luồng chính

    async with AsyncSessionLocal() as session:
        try:
            # ── 1. Đánh dấu RUNNING & PROCESSING (progress: 10%) ──────────────
            await session.execute(
                update(Document)
                .where(Document.id == doc_uuid)
                .values(ocr_status="PROCESSING", updated_at=now)
            )
            await session.execute(
                update(ProcessingJob)
                .where(ProcessingJob.document_id == doc_uuid)
                .values(status="RUNNING", started_at=now, ocr_progress=10)
            )
            await session.commit()

            # ── 2. Lấy Document từ DB (progress: 20%) ─────────────────────────
            await _set_progress(session, 20)
            stmt = (
                select(Document)
                .where(Document.id == doc_uuid)
                .options(selectinload(Document.category), selectinload(Document.metadata_))
            )
            res = await session.execute(stmt)
            doc = res.scalars().first()
            if not doc:
                raise ValueError(f"Document {document_id} không tồn tại trong database")

            # ── 3. Đọc file từ Supabase Storage (progress: 35%) ───────────────
            await _set_progress(session, 35)
            file_bytes = await asyncio.to_thread(storage_service.get_file, doc.minio_object_key)
            logger.info("Retrieved file from Supabase Storage: key={key}, bytes={len}",
                        key=doc.minio_object_key, len=len(file_bytes))

            # ── 4. Chạy OCR (progress: 45% → 85% sau khi xong) ───────────
            await _set_progress(session, 45)

            target_engine = engine or "vietocr"
            if target_engine == "trocr":
                service = trocr_service
                engine_version = getattr(trocr_service, "VERSION", "trocr-base-printed")
            elif target_engine == "tesseract":
                from app.services.tesseract_service import tesseract_service
                service = tesseract_service
                engine_version = getattr(tesseract_service, "VERSION", "5.3.0")
            else:
                target_engine = "vietocr"
                service = vietocr_service
                engine_version = getattr(vietocr_service, "VERSION", "vgg_transformer-2.0")

            t_ocr_start = time.perf_counter()
            ocr_failed = False
            ocr_err_msg = None
            raw_text = ""
            processed_text = ""
            confidence = 0.0

            try:
                raw_text, processed_text, confidence = await asyncio.to_thread(
                    service.extract_text_from_file, file_bytes, doc.file_type, target_engine
                )
            except Exception as exc:
                ocr_failed = True
                ocr_err_msg = f"{type(exc).__name__}: {str(exc)}"
                logger.exception("OCR execution failed for engine {eng} on document {id}: {err}",
                             eng=target_engine, id=doc_uuid, err=ocr_err_msg)

            processing_time_ms = int(round((time.perf_counter() - t_ocr_start) * 1000))

            # Reset is_latest=False CHỈ cho các bản ghi của cùng engine này trên document này
            await session.execute(
                update(OCRResult)
                .where(OCRResult.document_id == doc_uuid)
                .where(OCRResult.ocr_engine == target_engine)
                .values(is_latest=False)
            )

            ocr_result = OCRResult(
                document_id=doc_uuid,
                is_latest=True,
                raw_text=raw_text if not ocr_failed else "",
                corrected_text=processed_text if not ocr_failed else "",
                confidence_score=confidence if not ocr_failed else 0.0,
                ocr_engine=target_engine,
                ocr_engine_version=engine_version,
                processing_time_ms=processing_time_ms,
                status="FAILED" if ocr_failed else "DONE",
                error_message=ocr_err_msg,
                is_corrected=False,
            )
            session.add(ocr_result)

            if ocr_failed and (not engine or engine == "vietocr"):
                # Nếu engine mặc định (VietOCR) thất bại khi upload, raise để đánh dấu Job/Document FAILED
                raise RuntimeError(f"OCR mặc định ({target_engine}) thất bại: {ocr_err_msg}")

            await _set_progress(session, 85)

            # ── 5. Trích xuất Metadata & AI Smart Fields (dùng processed_text) ──
            await _set_progress(session, 90)
            # Dùng processed_text (đã qua post-process) để cải thiện độ chính xác metadata
            meta_text = processed_text if processed_text else raw_text
            meta_dict = await asyncio.to_thread(vietocr_service.extract_metadata, meta_text)
            
            try:
                ai_fields = await ai_service.extract_smart_fields(raw_text)
            except Exception as ai_err:
                logger.warning("AI smart fields extraction error: {err}", err=str(ai_err))
                ai_fields = {}

            # Hợp nhất thông tin AI bóc tách và Metadata chuẩn
            final_student_id = ai_fields.get("student_id") or meta_dict.get("student_id")
            final_student_name = ai_fields.get("student_name") or meta_dict.get("student_name")
            final_doc_no = ai_fields.get("document_number") or meta_dict.get("document_number")
            auto_tags = ai_fields.get("tags") or tag_service.generate_auto_tags(raw_text, metadata=meta_dict)
            priority_score = ai_fields.get("priority_score") or tag_service.calculate_priority_score(auto_tags)

            # ── 6. Lưu / Cập nhật DocumentMetadata ────────────────────────────
            doc_date = None
            date_str = ai_fields.get("document_date") or meta_dict.get("document_date")
            if date_str:
                try:
                    doc_date = datetime.strptime(str(date_str)[:10], "%Y-%m-%d").date()
                except Exception:
                    pass

            extra_data = {
                "tags": auto_tags,
                "priority_score": priority_score,
                "faculty": ai_fields.get("faculty"),
                "class_name": ai_fields.get("class_name"),
                "document_type": ai_fields.get("document_type"),
                "ai_summary": ai_fields.get("summary"),
            }

            if doc.metadata_:
                doc.metadata_.student_id = final_student_id or doc.metadata_.student_id
                doc.metadata_.student_name = final_student_name or doc.metadata_.student_name
                doc.metadata_.document_date = doc_date or doc.metadata_.document_date
                doc.metadata_.document_number = final_doc_no or doc.metadata_.document_number
                doc.metadata_.extra = {**(doc.metadata_.extra or {}), **extra_data}
                doc.metadata_.updated_at = now
            else:
                new_meta = DocumentMetadata(
                    document_id=doc_uuid,
                    student_id=final_student_id,
                    student_name=final_student_name,
                    document_date=doc_date,
                    document_number=final_doc_no,
                    extra=extra_data,
                    created_at=now,
                    updated_at=now,
                )
                session.add(new_meta)

            # ── 8. Cập nhật Document và Job hoàn thành (progress: 100%) ────────
            await session.execute(
                update(Document)
                .where(Document.id == doc_uuid)
                .values(ocr_status="DONE", updated_at=now)
            )
            await session.execute(
                update(ProcessingJob)
                .where(ProcessingJob.document_id == doc_uuid)
                .values(status="SUCCESS", completed_at=now, ocr_progress=100)
            )
            await session.commit()

            # ── 9. Backend chủ động index sang Elasticsearch ───────────────────
            try:
                await search_index_service.index_document(
                    document_id=doc.id,
                    title=doc.title,
                    content=raw_text,
                    category_code=doc.category.code if doc.category else meta_dict.get("detected_category"),
                    category_name=doc.category.name if doc.category else None,
                    student_id=meta_dict.get("student_id"),
                    student_name=meta_dict.get("student_name"),
                    document_date=meta_dict.get("document_date"),
                    document_number=meta_dict.get("document_number"),
                    uploaded_by=doc.uploaded_by,
                    ocr_status="DONE",
                    ocr_confidence=confidence,
                    is_deleted=doc.is_deleted,
                    created_at=doc.created_at,
                    updated_at=doc.updated_at,
                )
                logger.info("Indexed document {id} into Elasticsearch successfully", id=document_id)
            except Exception as es_err:
                logger.warning("Elasticsearch indexing failed: {err}", err=str(es_err))

            logger.info("OCR task completed successfully for document_id={id}", id=document_id)
            return {
                "status": "SUCCESS",
                "document_id": document_id,
                "task_id": task_id,
                "confidence": confidence,
                "student_id": meta_dict.get("student_id"),
                "student_name": meta_dict.get("student_name"),
            }

        except Exception as exc:
            logger.error("OCR task failed for document_id={id}: {err}", id=document_id, err=str(exc))
            await session.execute(
                update(Document)
                .where(Document.id == doc_uuid)
                .values(ocr_status="FAILED", updated_at=datetime.now())
            )
            await session.execute(
                update(ProcessingJob)
                .where(ProcessingJob.document_id == doc_uuid)
                .values(status="FAILED", error_message=str(exc), completed_at=datetime.now())
            )
            await session.commit()
            raise exc


@celery_app.task(bind=True, name="tasks.process_ocr", max_retries=3, default_retry_delay=10)
def process_ocr_task(self, document_id: str) -> dict:
    """Celery task entry point."""
    try:
        return asyncio.run(async_process_ocr(document_id, task_id=self.request.id))
    except Exception as exc:
        raise self.retry(exc=exc)
