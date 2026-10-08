import asyncio
import os
import sys

# Thêm thư mục gốc backend vào sys.path để import app
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.database import AsyncSessionLocal
from app.models.documents import Document
from app.models.document_categories import DocumentCategory
from app.models.ocr_results import OCRResult
from app.services.doctype_service import doctype_service
from app.services.search_index_service import search_index_service
from app.core.elasticsearch import get_es_client, is_es_available
from loguru import logger

async def backfill_doctypes():
    logger.info("Starting backfill for legacy documents...")
    async with AsyncSessionLocal() as db:
        # Lấy tất cả documents chưa có phân loại hoặc phân loại không xác định
        # Để test hoặc backfill tất cả, ta query tất cả:
        stmt = select(Document).where(Document.is_deleted == False)
        result = await db.execute(stmt)
        documents = result.scalars().all()

        logger.info(f"Found {len(documents)} documents to evaluate.")

        for doc in documents:
            # Lấy text OCR trang 1
            ocr_stmt = select(OCRResult).where(
                OCRResult.document_id == doc.id,
                OCRResult.is_latest == True
            )
            ocr_res = await db.execute(ocr_stmt)
            ocr = ocr_res.scalars().first()
            
            if not ocr or not ocr.raw_text:
                logger.info(f"Skipping {doc.id} - No OCR text found.")
                continue
                
            text = ocr.raw_text
            
            # Phân loại
            doc_type_res = doctype_service.classify(text)
            
            cat_stmt = select(DocumentCategory).where(DocumentCategory.code == doc_type_res.code)
            cat_res = await db.execute(cat_stmt)
            category = cat_res.scalars().first()
            
            if not category:
                logger.error(f"Category code {doc_type_res.code} not found in DB.")
                continue
                
            # Cập nhật DB
            doc.category_id = category.id
            if doc.metadata_:
                if not doc.metadata_.extra:
                    doc.metadata_.extra = {}
                doc.metadata_.extra["document_type"] = category.name
                doc.metadata_.extra["confidence"] = doc_type_res.confidence
            
            logger.info(f"Classified {doc.id} as {category.code} (Confidence: {doc_type_res.confidence})")
            
        await db.commit()
        
        # Đồng bộ ES
        if is_es_available():
            es = get_es_client()
            logger.info("Updating Elasticsearch index...")
            for doc in documents:
                if doc.category_id:
                    cat_stmt = select(DocumentCategory).where(DocumentCategory.id == doc.category_id)
                    cat_res = await db.execute(cat_stmt)
                    cat = cat_res.scalars().first()
                    if cat:
                        try:
                            await es.update(
                                index=search_index_service.index_name,
                                id=str(doc.id),
                                doc={
                                    "category_code": cat.code,
                                    "category_name": cat.name,
                                    "document_type": cat.code
                                },
                                ignore=404
                            )
                        except Exception as e:
                            logger.error(f"Error updating ES for doc {doc.id}: {e}")
                            
    logger.info("Backfill completed.")

if __name__ == "__main__":
    asyncio.run(backfill_doctypes())
