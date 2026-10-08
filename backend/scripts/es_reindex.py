import asyncio
import os
import sys
import argparse

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from sqlalchemy import select
from loguru import logger
from app.core.database import AsyncSessionLocal
from app.models.documents import Document
from app.models.document_categories import DocumentCategory
from app.models.ocr_results import OCRResult
from app.core.elasticsearch import get_es_client, is_es_available, INDEX_NAME

async def reindex_es(apply: bool = False, batch_size: int = 100):
    if not is_es_available():
        logger.error("Elasticsearch is not available.")
        return
        
    es = get_es_client()
    
    async with AsyncSessionLocal() as db:
        stmt = select(Document).where(Document.is_deleted == False)
        res = await db.execute(stmt)
        docs = res.scalars().all()
        
        logger.info(f"Found {len(docs)} documents to reindex.")
        
        for i in range(0, len(docs), batch_size):
            batch = docs[i:i+batch_size]
            actions = []
            
            for doc in batch:
                cat_code = None
                cat_name = None
                if doc.category_id:
                    cat_stmt = select(DocumentCategory).where(DocumentCategory.id == doc.category_id)
                    cat_res = await db.execute(cat_stmt)
                    cat = cat_res.scalars().first()
                    if cat:
                        cat_code = cat.code
                        cat_name = cat.name
                        
                ocr_stmt = select(OCRResult).where(OCRResult.document_id == doc.id, OCRResult.is_latest == True)
                ocr_res = await db.execute(ocr_stmt)
                ocr = ocr_res.scalars().first()
                
                content = ocr.raw_text if ocr else ""
                
                body = {
                    "document_id": str(doc.id),
                    "title": doc.original_filename,
                    "content": content,
                    "category_code": cat_code,
                    "category_name": cat_name,
                    "document_date": doc.created_at.isoformat(),
                    "document_number": None,
                    "document_type": cat_code,
                    "document_subtype": None,
                    "uploaded_by": str(doc.uploader_id) if doc.uploader_id else None,
                    "ocr_status": doc.processing_status,
                    "ocr_confidence": 0.0,
                    "is_deleted": doc.is_deleted,
                    "created_at": doc.created_at.isoformat() if doc.created_at else None,
                    "updated_at": doc.updated_at.isoformat() if doc.updated_at else None,
                    
                    "doc_type_code": cat_code,
                    "doc_type_name": cat_name,
                    "doc_group": None,
                    "doc_subtype": None,
                    "doc_type_confidence": None,
                    "doc_type_source": "auto",
                    "subject": None,
                    "issuing_unit": None,
                    "ocr_scope": "first_page",
                    "page_count": 1,
                    "pages_ocr": 1,
                    "needs_review": False
                }
                
                if doc.metadata_ and doc.metadata_.extra:
                    body["doc_type_confidence"] = doc.metadata_.extra.get("confidence")
                    body["doc_type_source"] = doc.metadata_.extra.get("doc_type_source", "auto")
                
                if apply:
                    try:
                        await es.index(index=INDEX_NAME, id=str(doc.id), document=body)
                    except Exception as e:
                        logger.error(f"Error indexing doc {doc.id}: {e}")
                        
            if apply:
                logger.info(f"Indexed batch {i//batch_size + 1} ({len(batch)} docs).")
            else:
                logger.info(f"[DRY RUN] Would index batch {i//batch_size + 1} ({len(batch)} docs).")

def main():
    parser = argparse.ArgumentParser(description="Reindex ES from Postgres without re-OCR")
    parser.add_argument("--apply", action="store_true", help="Apply changes")
    parser.add_argument("--batch-size", type=int, default=100, help="Batch size")
    args = parser.parse_args()
    
    asyncio.run(reindex_es(apply=args.apply, batch_size=args.batch_size))

if __name__ == "__main__":
    main()
