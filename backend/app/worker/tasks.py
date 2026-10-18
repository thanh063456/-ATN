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
from datetime import datetime
import time
from uuid import UUID

from loguru import logger
from sqlalchemy import select, update
from sqlalchemy.orm import selectinload

from app.core.config import settings
from app.core.database import AsyncSessionLocal
from app.models.audit_logs import AuditLog
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


async def _process_secondary_engine(doc_uuid: UUID, engine_name: str) -> None:
    """
    Xử lý OCR cho các engine phụ (TrOCR, Tesseract):
    - Đọc file từ storage.
    - Cập nhật hoặc chèn OCRResult với trạng thái PROCESSING.
    - Chạy suy luận nhận dạng văn bản.
    - Cập nhật OCRResult với văn bản nhận diện, confidence, thời gian xử lý, status=DONE.
    - KHÔNG ghi đè metadata, loại văn bản hoặc chỉ mục Elasticsearch của VietOCR.
    """
    logger.info("Starting secondary OCR engine {eng} for document_id={id}", eng=engine_name, id=doc_uuid)
    async with AsyncSessionLocal() as session:
        stmt = (
            select(OCRResult)
            .where(OCRResult.document_id == doc_uuid)
            .where(OCRResult.ocr_engine == engine_name)
            .where(OCRResult.is_latest == True)
        )
        res = await session.execute(stmt)
        record = res.scalars().first()

        if record:
            record.status = "PROCESSING"
        else:
            await session.execute(
                update(OCRResult)
                .where(OCRResult.document_id == doc_uuid)
                .where(OCRResult.ocr_engine == engine_name)
                .values(is_latest=False)
            )
            record = OCRResult(
                document_id=doc_uuid,
                ocr_engine=engine_name,
                status="PROCESSING",
                is_latest=True,
            )
            session.add(record)
        await session.commit()

        doc = await session.get(Document, doc_uuid)
        if not doc:
            logger.warning("Document {id} not found when running secondary OCR engine {eng}", id=doc_uuid, eng=engine_name)
            return

        minio_key = doc.minio_object_key
        file_type = doc.file_type

    file_bytes = await asyncio.to_thread(storage_service.get_file, minio_key)

    if engine_name == "trocr":
        service = trocr_service
        engine_version = getattr(trocr_service, "VERSION", "trocr-vi-finetuned")
    elif engine_name == "tesseract":
        from app.services.tesseract_service import tesseract_service
        service = tesseract_service
        engine_version = getattr(tesseract_service, "VERSION", "5.3.0")
    else:
        service = vietocr_service
        engine_version = getattr(vietocr_service, "VERSION", "vgg_transformer-2.0")

    ocr_scope = getattr(settings, "ocr_scope", "first_page")
    ocr_first_page_count = getattr(settings, "ocr_first_page_count", 1)
    target_pages = None
    if ocr_scope == "first_page":
        target_pages = list(range(ocr_first_page_count))

    t_start = time.perf_counter()
    ocr_failed = False
    ocr_err_msg = None
    status_val = "DONE"
    raw_text = ""
    processed_text = ""
    confidence = 0.0

    try:
        ocr_res = await asyncio.to_thread(
            service.extract_text_from_file, file_bytes, file_type, engine_name, target_pages
        )
        if isinstance(ocr_res, (list, tuple)) and len(ocr_res) >= 3:
            raw_text, processed_text, confidence = ocr_res[:3]
    except Exception as exc:
        exc_str = str(exc)
        if exc_str.startswith("LOW_QUALITY:"):
            ocr_failed = False
            ocr_err_msg = exc_str.replace("LOW_QUALITY:", "").strip()
            status_val = "LOW_QUALITY"
        else:
            ocr_failed = True
            ocr_err_msg = f"{type(exc).__name__}: {str(exc)}"
            status_val = "FAILED"
            logger.warning("Secondary OCR engine {eng} failed for doc {id}: {err}",
                           eng=engine_name, id=doc_uuid, err=ocr_err_msg)

    processing_time_ms = int(round((time.perf_counter() - t_start) * 1000))

    async with AsyncSessionLocal() as session:
        stmt = (
            select(OCRResult)
            .where(OCRResult.document_id == doc_uuid)
            .where(OCRResult.ocr_engine == engine_name)
            .where(OCRResult.is_latest == True)
        )
        res = await session.execute(stmt)
        record = res.scalars().first()

        if record:
            record.raw_text = raw_text if not ocr_failed else ""
            record.corrected_text = processed_text if not ocr_failed else ""
            record.confidence_score = confidence if not ocr_failed else 0.0
            record.ocr_engine_version = engine_version
            record.processing_time_ms = processing_time_ms
            record.status = status_val
            record.error_message = ocr_err_msg
        else:
            record = OCRResult(
                document_id=doc_uuid,
                ocr_engine=engine_name,
                ocr_engine_version=engine_version,
                raw_text=raw_text if not ocr_failed else "",
                corrected_text=processed_text if not ocr_failed else "",
                confidence_score=confidence if not ocr_failed else 0.0,
                processing_time_ms=processing_time_ms,
                status=status_val,
                error_message=ocr_err_msg,
                is_latest=True,
            )
            session.add(record)

        await session.commit()
    logger.info("Secondary OCR engine {eng} finished for doc {id} (status={st}, {ms}ms)",
                eng=engine_name, id=doc_uuid, st=status_val, ms=processing_time_ms)


async def async_process_ocr(document_id: str, task_id: str | None = None, engine: str | None = None) -> dict:
    """Coroutine thực thi toàn bộ logic OCR, Metadata Extraction và Elasticsearch indexing."""
    doc_uuid = UUID(document_id)
    now = datetime.now()
    logger.info(f"Starting async OCR processing for document_id={document_id}")

    if engine and engine != "vietocr":
        await _process_secondary_engine(doc_uuid, engine)
        return {
            "status": "SUCCESS",
            "document_id": document_id,
            "engine": engine,
        }

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
            page_count = None

            try:
                ocr_res = await asyncio.to_thread(
                    service.extract_text_from_file, file_bytes, doc.file_type, target_engine
                )
                if isinstance(ocr_res, (list, tuple)):
                    if len(ocr_res) >= 3:
                        raw_text, processed_text, confidence = ocr_res[:3]
                    if len(ocr_res) >= 4 and isinstance(ocr_res[3], int):
                        page_count = ocr_res[3]
                else:
                    raise ValueError(f"Unexpected return format from extract_text_from_file: {type(ocr_res)}")
            except Exception as exc:
                ocr_failed = True
                ocr_err_msg = f"{type(exc).__name__}: {str(exc)}"
                logger.exception(f"OCR execution failed for engine {target_engine} on document {doc_uuid}: {ocr_err_msg}")

            processing_time_ms = round((time.perf_counter() - t_ocr_start) * 1000)

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
            doc_update_values = {"ocr_status": "DONE", "updated_at": now}
            if page_count and page_count > 0:
                doc_update_values["page_count"] = page_count

            await session.execute(
                update(Document)
                .where(Document.id == doc_uuid)
                .values(**doc_update_values)
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
                    student_id=final_student_id or meta_dict.get("student_id"),
                    student_name=final_student_name or meta_dict.get("student_name"),
                    document_date=doc_date.isoformat() if doc_date else meta_dict.get("document_date"),
                    document_number=final_doc_no or meta_dict.get("document_number"),
                    uploaded_by=doc.uploaded_by,
                    ocr_status="DONE",
                    ocr_confidence=confidence,
                    tags=auto_tags,
                    priority_score=priority_score,
                    metadata_extra=extra_data,
                    is_deleted=doc.is_deleted,
                    created_at=doc.created_at,
                    updated_at=doc.updated_at,
                )
                logger.info(f"Indexed document {document_id} into Elasticsearch successfully (with tags and metadata)")
            except Exception as es_err:
                logger.warning(f"Elasticsearch indexing failed: {es_err}")

            logger.info(f"OCR task completed successfully for document_id={document_id}")
            return {
                "status": "SUCCESS",
                "document_id": document_id,
                "task_id": task_id,
                "confidence": confidence,
                "student_id": meta_dict.get("student_id"),
                "student_name": meta_dict.get("student_name"),
            }

        except Exception as exc:
            logger.error(f"OCR task failed for document_id={document_id}: {exc}")
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


async def async_process_all_ocr_engines(document_id: str, task_id: str | None = None) -> dict:
    """
    Quy trình tự động quét toàn bộ 3 OCR engine (VietOCR, TrOCR, Tesseract) tuần tự khi upload:
    1. Đặt placeholder PENDING cho trocr và tesseract (UI lập tức hiển thị trạng thái chờ quét).
    2. Chạy VietOCR (engine chính): trích xuất text, metadata, AI smart fields, auto-tags, phân loại, Elasticsearch.
    3. Chạy TrOCR (fine-tuned transformer): nhận dạng văn bản và lưu OCRResult (status='DONE').
    4. Chạy Tesseract (LSTM baseline): nhận dạng văn bản và lưu OCRResult (status='DONE').
    """
    doc_uuid = UUID(document_id)
    logger.info("Starting ALL OCR engines pipeline for document_id={doc_id}", doc_id=document_id)

    # 1. Đặt placeholder PENDING cho trocr và tesseract
    async with AsyncSessionLocal() as session:
        try:
            await session.execute(
                update(OCRResult)
                .where(OCRResult.document_id == doc_uuid)
                .where(OCRResult.ocr_engine.in_(["trocr", "tesseract"]))
                .values(is_latest=False)
            )
            from app.services.tesseract_service import tesseract_service
            session.add(OCRResult(
                document_id=doc_uuid,
                ocr_engine="trocr",
                ocr_engine_version=getattr(trocr_service, "VERSION", "trocr-vi-finetuned"),
                status="PENDING",
                is_latest=True,
            ))
            session.add(OCRResult(
                document_id=doc_uuid,
                ocr_engine="tesseract",
                ocr_engine_version=getattr(tesseract_service, "VERSION", "5.3.0"),
                status="PENDING",
                is_latest=True,
            ))
            await session.commit()
        except Exception as exc:
            logger.warning("Failed to initialize pending OCRResult records: {err}", err=str(exc))

    # 2. Chạy engine chính: VietOCR
    logger.info("Pipeline Step 1/3: Running VietOCR for document_id={id}", id=document_id)
    vietocr_res = await async_process_ocr(document_id, task_id=task_id, engine="vietocr")

    # 3. Chạy TrOCR
    logger.info("Pipeline Step 2/3: Running TrOCR for document_id={id}", id=document_id)
    try:
        await _process_secondary_engine(doc_uuid, "trocr")
    except Exception as exc:
        logger.error("Secondary engine trocr failed on doc {id}: {err}", id=document_id, err=str(exc))

    # 4. Chạy Tesseract
    logger.info("Pipeline Step 3/3: Running Tesseract for document_id={id}", id=document_id)
    try:
        await _process_secondary_engine(doc_uuid, "tesseract")
    except Exception as exc:
        logger.error("Secondary engine tesseract failed on doc {id}: {err}", id=document_id, err=str(exc))

    logger.info("ALL OCR engines pipeline completed successfully for document_id={id}", id=document_id)
    return {
        "status": "SUCCESS",
        "document_id": document_id,
        "vietocr": vietocr_res,
    }


@celery_app.task(bind=True, name="tasks.process_all_ocr", max_retries=2, default_retry_delay=10)
def process_all_ocr_task(self, document_id: str) -> dict:
    try:
        return asyncio.run(async_process_all_ocr_engines(document_id, task_id=self.request.id))
    except Exception as exc:
        raise self.retry(exc=exc)


async def async_process_ocr_full(document_id: str, task_id: str | None = None) -> dict:
    """Stage 2 OCR: Process remaining pages."""
    doc_uuid = UUID(document_id)
    now = datetime.now()
    logger.info("Starting FULL OCR processing for document_id={doc_id}", doc_id=document_id)

    async with AsyncSessionLocal() as session:
        try:
            stmt = select(Document).where(Document.id == doc_uuid).options(selectinload(Document.category), selectinload(Document.metadata_))
            res = await session.execute(stmt)
            doc = res.scalars().first()
            if not doc:
                raise ValueError(f"Document {document_id} không tồn tại")

            if doc.metadata_ and doc.metadata_.extra and doc.metadata_.extra.get("ocr_scope") == "full":
                logger.info(f"Document {document_id} is already fully OCRed. Skipping.")
                return {"status": "SUCCESS", "message": "Document already fully OCRed", "document_id": document_id}

            ocr_first_page_count = getattr(settings, "ocr_first_page_count", 1)
            page_count = doc.page_count or 1
            if page_count <= ocr_first_page_count:
                if doc.metadata_:
                    if not doc.metadata_.extra:
                        doc.metadata_.extra = {}
                    doc.metadata_.extra["ocr_scope"] = "full"
                    doc.metadata_.extra["pages_ocr"] = page_count
                    await session.commit()
                return {"status": "SUCCESS", "message": "No remaining pages to OCR", "document_id": document_id}

            remaining_pages = list(range(ocr_first_page_count, page_count))

            # Set status to PROCESSING
            await session.execute(update(Document).where(Document.id == doc_uuid).values(ocr_status="PROCESSING", updated_at=now))
            await session.commit()

            # Read file
            file_bytes = await asyncio.to_thread(storage_service.get_file, doc.minio_object_key)

            # Extract remaining pages with exact per-page markers
            target_engine = getattr(settings, "ocr_engine", "vietocr")
            service = vietocr_service

            per_page_raw = []
            per_page_proc = []
            conf_list = []
            for p_idx in remaining_pages:
                page_res = await asyncio.to_thread(
                    service.extract_text_from_file, file_bytes, doc.file_type, target_engine, [p_idx]
                )
                raw_p = page_res[0] if isinstance(page_res, (list, tuple)) and len(page_res) > 0 else ""
                proc_p = page_res[1] if isinstance(page_res, (list, tuple)) and len(page_res) > 1 else ""
                conf_p = page_res[2] if isinstance(page_res, (list, tuple)) and len(page_res) > 2 else 0.8
                per_page_raw.append(f"--- Trang {p_idx + 1} ---\n{raw_p}")
                per_page_proc.append(f"--- Trang {p_idx + 1} ---\n{proc_p}")
                conf_list.append(conf_p)

            raw_text = "\n\n".join(per_page_raw)
            processed_text = "\n\n".join(per_page_proc)
            confidence = sum(conf_list) / len(conf_list) if conf_list else 0.8

            # Get latest OCR result
            ocr_res = await session.execute(select(OCRResult).where(OCRResult.document_id == doc_uuid, OCRResult.is_latest == True))
            latest_ocr = ocr_res.scalars().first()

            if latest_ocr:
                new_raw = latest_ocr.raw_text + "\n\n" + raw_text
                new_proc = latest_ocr.corrected_text + "\n\n" + processed_text
                
                # Update existing or create new
                latest_ocr.is_latest = False
                
                new_ocr = OCRResult(
                    document_id=doc_uuid,
                    is_latest=True,
                    raw_text=new_raw,
                    corrected_text=new_proc,
                    confidence_score=(latest_ocr.confidence_score + confidence) / 2,
                    ocr_engine=latest_ocr.ocr_engine,
                    ocr_engine_version=latest_ocr.ocr_engine_version,
                    status="DONE",
                    is_corrected=latest_ocr.is_corrected,
                )
                session.add(new_ocr)
            else:
                new_raw = raw_text
                new_proc = processed_text

            if doc.metadata_:
                if not doc.metadata_.extra:
                    doc.metadata_.extra = {}
                doc.metadata_.extra["ocr_scope"] = "full"
                doc.metadata_.extra["pages_ocr"] = page_count

            # Trích xuất trước khi commit để tránh lỗi lazy loading
            doc_id_val = doc.id
            doc_title_val = doc.title
            doc_uploaded_by_val = doc.uploaded_by
            doc_is_deleted_val = doc.is_deleted
            doc_created_at_val = doc.created_at
            cat_code = doc.category.code if doc.category else None
            cat_name = doc.category.name if doc.category else None
            meta_student_id = doc.metadata_.student_id if doc.metadata_ else None
            meta_student_name = doc.metadata_.student_name if doc.metadata_ else None
            meta_doc_date = doc.metadata_.document_date.isoformat() if doc.metadata_ and doc.metadata_.document_date else None
            meta_doc_no = doc.metadata_.document_number if doc.metadata_ else None
            meta_subtype = doc.metadata_.extra.get("document_subtype") if doc.metadata_ and doc.metadata_.extra else None

            await session.execute(update(Document).where(Document.id == doc_uuid).values(ocr_status="DONE", updated_at=now))
            await session.commit()

            # Audit log for full OCR
            audit_full = AuditLog(
                user_id=doc_uploaded_by_val,
                action="OCR_FULL_COMPLETED",
                resource_type="document",
                resource_id=doc_uuid,
                detail={
                    "engine": target_engine,
                    "pages_extracted": len(remaining_pages),
                    "page_count": page_count,
                },
                created_at=now,
            )
            session.add(audit_full)
            await session.commit()

            # Re-index
            try:
                await search_index_service.index_document(
                    document_id=doc_id_val,
                    title=doc_title_val,
                    content=new_raw,
                    category_code=cat_code,
                    category_name=cat_name,
                    student_id=meta_student_id,
                    student_name=meta_student_name,
                    document_date=meta_doc_date,
                    document_number=meta_doc_no,
                    uploaded_by=doc_uploaded_by_val,
                    ocr_status="DONE",
                    ocr_confidence=(latest_ocr.confidence_score + confidence) / 2 if latest_ocr else confidence,
                    is_deleted=doc_is_deleted_val,
                    created_at=doc_created_at_val,
                    updated_at=now,
                    document_type=cat_code,
                    document_subtype=meta_subtype,
                )
            except Exception as es_err:
                logger.warning("ES indexing failed: {err}", err=str(es_err))

            return {"status": "SUCCESS", "document_id": document_id}

        except Exception as exc:
            logger.error("OCR FULL task failed for document_id={id}: {err}", id=document_id, err=str(exc))
            await session.execute(update(Document).where(Document.id == doc_uuid).values(ocr_status="FAILED", updated_at=datetime.now()))
            await session.commit()
            raise exc

@celery_app.task(bind=True, name="tasks.process_ocr_full", max_retries=3, default_retry_delay=10)
def process_ocr_full_task(self, document_id: str) -> dict:
    try:
        return asyncio.run(async_process_ocr_full(document_id, task_id=self.request.id))
    except Exception as exc:
        raise self.retry(exc=exc)

