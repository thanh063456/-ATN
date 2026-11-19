#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
scripts/retag_existing_documents.py — Cập nhật lại nhãn AI thông minh đa chiều cho toàn bộ tài liệu đã có trong CSDL
"""

import sys
import asyncio
from pathlib import Path

# Add backend directory to sys.path
backend_path = Path(__file__).resolve().parent.parent / "backend"
sys.path.insert(0, str(backend_path))

from loguru import logger
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.core.database import AsyncSessionLocal
from app.models import Document, DocumentMetadata
from app.models.ocr_results import OCRResult
from app.services.tag_service import tag_service
from app.services.search_index_service import search_index_service


async def retag_all():
    logger.info("Đang quét CSDL để cập nhật lại hệ thống nhãn theo chủ đề chi tiết...")
    async with AsyncSessionLocal() as session:
        stmt = (
            select(Document)
            .options(
                selectinload(Document.metadata_),
                selectinload(Document.ocr_results),
            )
        )
        res = await session.execute(stmt)
        docs = res.scalars().all()
        logger.info(f"Tìm thấy {len(docs)} tài liệu trong CSDL.")

        updated_count = 0
        for doc in docs:
            # Lấy nội dung text OCR tốt nhất
            ocr = next((r for r in doc.ocr_results if r.ocr_engine == "vietocr"), None)
            if not ocr and doc.ocr_results:
                ocr = doc.ocr_results[0]
            ocr_text = (ocr.corrected_text or ocr.raw_text or "") if ocr else ""

            meta_obj = doc.metadata_
            extra = dict(meta_obj.extra or {}) if meta_obj else {}

            metadata_dict = {
                "student_id": meta_obj.student_id if meta_obj else None,
                "student_name": meta_obj.student_name if meta_obj else None,
                "document_number": meta_obj.document_number if meta_obj else None,
                "trich_yeu": extra.get("trich_yeu"),
                "title": doc.title,
                "faculty": extra.get("faculty"),
                "class_name": extra.get("class_name"),
            }

            # Tự động gán nhãn lại theo bộ phân loại mới
            new_tags = tag_service.generate_auto_tags(
                text=ocr_text,
                metadata=metadata_dict,
                confidence_score=ocr.confidence_score if ocr else 0.85,
            )
            new_priority = tag_service.calculate_priority_score(new_tags)

            old_tags = extra.get("tags") or []
            if set(old_tags) != set(new_tags):
                extra["tags"] = new_tags
                extra["priority_score"] = new_priority
                if meta_obj:
                    meta_obj.extra = extra
                logger.info(f"[{doc.original_filename}] Tags cũ: {old_tags} -> Tags mới: {new_tags}")
                updated_count += 1

                # Lập chỉ mục lại ES
                try:
                    await search_index_service.index_document(
                        document_id=str(doc.id),
                        title=doc.title,
                        raw_text=ocr_text,
                        processed_text=ocr_text,
                        student_name=meta_obj.student_name if meta_obj else None,
                        student_id=meta_obj.student_id if meta_obj else None,
                        class_name=extra.get("class_name"),
                        faculty=extra.get("faculty"),
                        tags=new_tags,
                        ocr_status=doc.ocr_status,
                        confidence_score=ocr.confidence_score if ocr else 0.85,
                        metadata_extra=extra,
                    )
                except Exception as e:
                    logger.debug(f"ES index skip: {e}")

        await session.commit()
        logger.info(f"✅ Hoàn tất! Đã cập nhật nhãn cho {updated_count}/{len(docs)} tài liệu.")


if __name__ == "__main__":
    asyncio.run(retag_all())
