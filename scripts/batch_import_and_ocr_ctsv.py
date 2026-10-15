#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
scripts/batch_import_and_ocr_ctsv.py — Nhập và OCR toàn bộ tài liệu PDF từ CTSV_output

Tính năng:
1. Quét toàn bộ 105 tệp PDF và thư mục con trong CTSV_output.
2. Đọc metadata.json đi kèm để lấy trích yếu, số ký hiệu, ngày tạo, đơn vị ban hành.
3. Chạy VietOCR toàn bộ tất cả các trang (full pages) cho từng tài liệu.
4. Tự động phân loại tài liệu (DocTypeService), sinh auto-tags và trích xuất thực thể.
5. Lưu trữ CSDL PostgreSQL (Supabase/SQLite), Storage và lập chỉ mục Elasticsearch.
6. Cơ chế Resume: Bỏ qua các tài liệu đã OCR hoàn thành (status=DONE), có thể tạm dừng và tiếp tục an toàn.
"""

import os
import sys
import glob
import json
import time
import uuid
import asyncio
import argparse
from pathlib import Path
from datetime import datetime

# UTF-8 stdout configuration for Windows
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')

# Add backend directory to sys.path
backend_path = Path(__file__).resolve().parent.parent / "backend"
sys.path.insert(0, str(backend_path))

import fitz  # PyMuPDF
from loguru import logger
from sqlalchemy import select, update
from sqlalchemy.orm import selectinload

from app.core.database import AsyncSessionLocal, init_db
from app.models import Document, DocumentCategory, DocumentMetadata, ProcessingJob
from app.models.ocr_results import OCRResult
from app.models.users import User
from app.services.storage_service import storage_service
from app.services.vietocr_service import vietocr_service
from app.services.tag_service import tag_service
from app.services.doctype_service import DocTypeService
from app.services.search_index_service import search_index_service


def find_pdf_entries(base_dir: Path) -> list[dict]:
    """
    Quét thư mục base_dir, thu thập danh sách tất cả các file PDF cùng metadata.json tương ứng.
    """
    entries = []
    seen_files = set()

    for item in sorted(base_dir.iterdir()):
        if item.is_dir():
            # Check for metadata.json in this directory
            meta_file = item / "metadata.json"
            meta_json = {}
            if meta_file.exists():
                try:
                    with open(meta_file, "r", encoding="utf-8") as f:
                        meta_json = json.load(f)
                except Exception as e:
                    logger.warning(f"Could not read {meta_file}: {e}")

            pdfs = list(item.glob("*.pdf")) + list(item.glob("*.PDF"))
            for p in sorted(pdfs):
                real_p = p.resolve()
                if real_p in seen_files:
                    continue
                seen_files.add(real_p)

                entries.append({
                    "pdf_path": p,
                    "folder_name": item.name,
                    "metadata_json": meta_json,
                })
        elif item.is_file() and item.suffix.lower() == ".pdf":
            real_p = item.resolve()
            if real_p in seen_files:
                continue
            seen_files.add(real_p)
            entries.append({
                "pdf_path": item,
                "folder_name": "",
                "metadata_json": {},
            })

    return entries


async def process_single_pdf(
    entry: dict,
    staff_user: User,
    cat_map: dict[str, DocumentCategory],
    doctype_service: DocTypeService,
    force_reprocess: bool = False,
) -> dict:
    """
    Xử lý OCR và nạp 1 file PDF vào hệ thống.
    """
    pdf_path: Path = entry["pdf_path"]
    meta_json: dict = entry["metadata_json"]
    filename = pdf_path.name
    now = datetime.now()

    # 1. Đọc số trang
    try:
        pdf_doc = fitz.open(str(pdf_path))
        page_count = len(pdf_doc)
        pdf_doc.close()
    except Exception as e:
        logger.error(f"Cannot read PDF {filename}: {e}")
        return {"status": "ERROR", "filename": filename, "error": str(e)}

    # 2. Xác định tiêu đề (cắt ngắn tối đa 490 ký tự để phù hợp giới hạn cột DB String(500))
    trich_yeu = meta_json.get("trich_yeu")
    if trich_yeu and trich_yeu.strip():
        clean_trich_yeu = " ".join(trich_yeu.strip().split())
        title = clean_trich_yeu[:490]
    else:
        title = pdf_path.stem[:490]

    # 3. Kiểm tra xem tài liệu đã có trong CSDL chưa
    async with AsyncSessionLocal() as session:
        stmt = (
            select(Document)
            .where(Document.original_filename == filename)
            .options(selectinload(Document.ocr_results), selectinload(Document.metadata_))
        )
        res = await session.execute(stmt)
        existing_doc = res.scalars().first()

        if existing_doc and not force_reprocess:
            # Nếu tài liệu đã DONE và có OCRResult thì bỏ qua
            has_done_ocr = any(o.is_latest and o.status == "DONE" for o in existing_doc.ocr_results)
            if existing_doc.ocr_status == "DONE" and has_done_ocr:
                logger.info(f"⏭️ Skipping already processed: {filename} (ID: {existing_doc.id})")
                return {"status": "SKIPPED", "filename": filename, "id": str(existing_doc.id)}

    # 4. Đọc nội dung file nhị phân
    with open(pdf_path, "rb") as f:
        file_bytes = f.read()
    file_size_bytes = len(file_bytes)

    # 5. Lưu vào Storage (Supabase + Local Cache)
    try:
        minio_object_key = storage_service.upload_file(
            file_data=file_bytes,
            filename=filename,
            content_type="application/pdf",
        )
    except Exception as st_err:
        logger.warning(f"Storage upload note for {filename}: {st_err}")
        minio_object_key = f"documents/{uuid.uuid4()}_{filename}"

    # 6. Chạy VietOCR toàn bộ tất cả các trang
    t_ocr_start = time.perf_counter()
    logger.info(f"🔍 Running VietOCR for {filename} ({page_count} trang)...")
    try:
        raw_text, processed_text, confidence, _ = await asyncio.to_thread(
            vietocr_service.extract_text_from_file, file_bytes, "pdf", "vietocr", list(range(page_count))
        )
    except Exception as ocr_err:
        logger.error(f"VietOCR failed for {filename}: {ocr_err}")
        raw_text = ""
        processed_text = ""
        confidence = 0.0

    ocr_duration_ms = int(round((time.perf_counter() - t_ocr_start) * 1000))

    # 7. Phân loại loại văn bản và trích xuất thực thể
    text_for_analysis = processed_text if processed_text else raw_text
    doc_type_res = doctype_service.classify(text_for_analysis, page_count=page_count)

    # Lấy category_id tương ứng
    matched_cat = cat_map.get(doc_type_res.code)
    category_id = matched_cat.id if matched_cat else None

    # Trích xuất metadata từ OCR hoặc metadata.json
    extracted_meta = vietocr_service.extract_metadata(text_for_analysis)
    doc_number = meta_json.get("so_ky_hieu") or extracted_meta.get("document_number") or doc_type_res.document_number
    if doc_number:
        doc_number = str(doc_number).strip()[:95]

    doc_date = None
    created_str = meta_json.get("created")
    if created_str:
        try:
            doc_date = datetime.fromisoformat(created_str.replace("Z", "+00:00")).date()
        except Exception:
            pass
    if not doc_date and extracted_meta.get("document_date"):
        try:
            doc_date = datetime.strptime(str(extracted_meta["document_date"])[:10], "%Y-%m-%d").date()
        except Exception:
            pass

    student_id = extracted_meta.get("student_id")
    student_name = extracted_meta.get("student_name")

    auto_tags = tag_service.generate_auto_tags(
        text=text_for_analysis,
        metadata={
            "student_id": student_id,
            "student_name": student_name,
            "document_number": doc_number,
            "trich_yeu": meta_json.get("trich_yeu"),
            "title": title,
        },
        confidence_score=confidence,
    )
    priority_score = tag_service.calculate_priority_score(auto_tags)

    extra_data = {
        "tags": auto_tags,
        "priority_score": priority_score,
        "ocr_scope": "full",
        "pages_ocr": page_count,
        "doc_type_code": doc_type_res.code,
        "doc_type_name": doc_type_res.name,
        "doc_group": doc_type_res.group,
        "doc_subtype": doc_type_res.subtype,
        "doc_type_confidence": doc_type_res.confidence,
        "doc_type_source": doc_type_res.source,
        "issuing_unit": meta_json.get("ten_don_vi") or doc_type_res.issuing_unit,
        "sender": meta_json.get("ten_nguoi_gui"),
    }

    # 8. Lưu CSDL
    async with AsyncSessionLocal() as session:
        # Kiểm tra lại document
        stmt = select(Document).where(Document.original_filename == filename)
        res = await session.execute(stmt)
        doc = res.scalars().first()

        if not doc:
            doc_id = uuid.uuid4()
            doc = Document(
                id=doc_id,
                title=title,
                original_filename=filename,
                file_type="pdf",
                file_size_bytes=file_size_bytes,
                page_count=page_count,
                minio_object_key=minio_object_key,
                uploaded_by=staff_user.id,
                category_id=category_id,
                ocr_status="DONE",
                is_public=True,
                created_at=now,
                updated_at=now,
            )
            session.add(doc)
            await session.flush()

            # Job record
            job = ProcessingJob(
                document_id=doc.id,
                status="SUCCESS",
                ocr_progress=100,
                started_at=now,
                completed_at=now,
            )
            session.add(job)
        else:
            doc.title = title
            doc.page_count = page_count
            doc.minio_object_key = minio_object_key
            doc.category_id = category_id or doc.category_id
            doc.ocr_status = "DONE"
            doc.is_public = True
            doc.updated_at = now

        # Cập nhật hoặc tạo OCRResult
        await session.execute(
            update(OCRResult)
            .where(OCRResult.document_id == doc.id)
            .where(OCRResult.ocr_engine == "vietocr")
            .values(is_latest=False)
        )
        ocr_rec = OCRResult(
            document_id=doc.id,
            is_latest=True,
            raw_text=raw_text,
            corrected_text=processed_text,
            confidence_score=confidence,
            ocr_engine="vietocr",
            ocr_engine_version=getattr(vietocr_service, "VERSION", "vgg_transformer-2.0"),
            processing_time_ms=ocr_duration_ms,
            status="DONE" if raw_text else "FAILED",
        )
        session.add(ocr_rec)

        # Cập nhật hoặc tạo DocumentMetadata
        stmt_meta = select(DocumentMetadata).where(DocumentMetadata.document_id == doc.id)
        res_meta = await session.execute(stmt_meta)
        meta_rec = res_meta.scalars().first()

        if meta_rec:
            meta_rec.document_number = doc_number or meta_rec.document_number
            meta_rec.document_date = doc_date or meta_rec.document_date
            meta_rec.student_id = student_id or meta_rec.student_id
            meta_rec.student_name = student_name or meta_rec.student_name
            meta_rec.extra = {**(meta_rec.extra or {}), **extra_data}
            meta_rec.updated_at = now
        else:
            meta_rec = DocumentMetadata(
                document_id=doc.id,
                document_number=doc_number,
                document_date=doc_date,
                student_id=student_id,
                student_name=student_name,
                extra=extra_data,
                created_at=now,
                updated_at=now,
            )
            session.add(meta_rec)

        await session.commit()
        doc_id_val = doc.id

    # 9. Lập chỉ mục Elasticsearch
    try:
        cat_name = matched_cat.name if matched_cat else None
        cat_code = matched_cat.code if matched_cat else doc_type_res.code
        await search_index_service.index_document(
            document_id=doc_id_val,
            title=title,
            content=raw_text,
            category_code=cat_code,
            category_name=cat_name,
            student_id=student_id,
            student_name=student_name,
            document_date=doc_date.isoformat() if doc_date else None,
            document_number=doc_number,
            uploaded_by=staff_user.id,
            ocr_status="DONE",
            ocr_confidence=confidence,
            tags=auto_tags,
            priority_score=priority_score,
            metadata_extra=extra_data,
            is_deleted=False,
            created_at=now,
            updated_at=now,
        )
        logger.info(f"✅ Indexed {filename} into Elasticsearch.")
    except Exception as es_err:
        logger.warning(f"ES index notice for {filename}: {es_err}")

    try:
        import torch
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
    except Exception:
        pass

    logger.info(f"✨ Successfully processed {filename} in {ocr_duration_ms}ms (Conf: {confidence:.2f})")
    return {
        "status": "SUCCESS",
        "filename": filename,
        "id": str(doc_id_val),
        "pages": page_count,
        "duration_ms": ocr_duration_ms,
        "confidence": confidence,
    }


async def main():
    parser = argparse.ArgumentParser(description="Batch import and OCR all PDFs in CTSV_output")
    parser.add_argument(
        "--input", "-i",
        type=str,
        default=r"d:\Đồ án tốt nghiệp\CTSV_output",
        help="Thư mục CTSV_output"
    )
    parser.add_argument(
        "--limit", "-l",
        type=int,
        default=0,
        help="Giới hạn số file xử lý (0 = không giới hạn)"
    )
    parser.add_argument(
        "--force", "-f",
        action="store_true",
        help="Xử lý lại kể cả khi đã có trong DB"
    )
    args = parser.parse_args()

    input_dir = Path(args.input)
    if not input_dir.exists():
        logger.error(f"Thư mục không tồn tại: {input_dir}")
        return

    logger.info("Initializing database...")
    await init_db()

    # Lấy tài khoản cán bộ CTSV làm người tải lên mặc định
    async with AsyncSessionLocal() as session:
        user_res = await session.execute(
            select(User).where(User.username.in_(["canbo_ctsv", "admin_hethong"]))
        )
        staff_user = user_res.scalars().first()
        if not staff_user:
            staff_user = (await session.execute(select(User))).scalars().first()

        cat_res = await session.execute(select(DocumentCategory))
        categories = cat_res.scalars().all()
        cat_map = {c.code: c for c in categories}

    doctype_service = DocTypeService()

    entries = find_pdf_entries(input_dir)
    total_found = len(entries)
    logger.info(f"📂 Tìm thấy {total_found} tệp PDF trong {input_dir}")

    if args.limit > 0:
        entries = entries[:args.limit]
        logger.info(f"Áp dụng giới hạn xử lý: {len(entries)} tệp.")

    processed_count = 0
    skipped_count = 0
    error_count = 0
    t_start_all = time.time()

    for idx, entry in enumerate(entries, start=1):
        filename = entry["pdf_path"].name
        logger.info(f"\n=======================================================")
        logger.info(f"[{idx}/{len(entries)}] Bắt đầu xử lý: {filename}")
        logger.info(f"=======================================================")

        try:
            res = await process_single_pdf(
                entry=entry,
                staff_user=staff_user,
                cat_map=cat_map,
                doctype_service=doctype_service,
                force_reprocess=args.force,
            )
            if res["status"] == "SUCCESS":
                processed_count += 1
            elif res["status"] == "SKIPPED":
                skipped_count += 1
            else:
                error_count += 1
        except Exception as e:
            logger.exception(f"Lỗi khi xử lý {filename}: {e}")
            error_count += 1

    elapsed = time.time() - t_start_all
    logger.info("\n🎉 =======================================================")
    logger.info(f"HOÀN TẤT QUÁ TRÌNH OCR BATCH CTSV_OUTPUT")
    logger.info(f"- Tổng số file: {len(entries)}")
    logger.info(f"- Đã xử lý mới: {processed_count}")
    logger.info(f"- Đã bỏ qua (đã có sẵn): {skipped_count}")
    logger.info(f"- Lỗi: {error_count}")
    logger.info(f"- Thời gian thực hiện: {elapsed:.1f}s ({elapsed/60:.2f} phút)")
    logger.info("=======================================================")


if __name__ == "__main__":
    asyncio.run(main())
