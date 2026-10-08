import argparse
import asyncio
import csv
import os
import sys
from datetime import datetime

# Thêm thư mục gốc backend vào sys.path để import app
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.database import AsyncSessionLocal
from app.core.config import settings
from app.models.documents import Document
from app.models.document_categories import DocumentCategory
from app.models.ocr_results import OCRResult
from app.services.doctype_service import doctype_service
from app.services.search_index_service import search_index_service
from app.core.elasticsearch import get_es_client, is_es_available
from loguru import logger
import json

async def undo_backfill(csv_path: str):
    logger.info(f"Reverting backfill from {csv_path}...")
    if not os.path.exists(csv_path):
        logger.error(f"CSV file {csv_path} not found.")
        return

    async with AsyncSessionLocal() as db:
        with open(csv_path, mode='r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                doc_id = row['document_id']
                old_category_id = row['old_category_id'] or None
                old_extra = row['old_extra_subset']
                
                doc = await db.get(Document, doc_id)
                if doc:
                    doc.category_id = old_category_id
                    if old_extra and doc.metadata_:
                        try:
                            old_extra_dict = json.loads(old_extra)
                            if not doc.metadata_.extra:
                                doc.metadata_.extra = {}
                            doc.metadata_.extra.update(old_extra_dict)
                        except Exception as e:
                            logger.error(f"Failed to parse old extra for {doc_id}: {e}")
                    logger.info(f"Reverted {doc_id}")
        await db.commit()
    logger.info("Undo completed.")

async def backfill_doctypes(apply: bool = False):
    logger.info("Starting backfill for legacy documents...")
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    work_dir = os.path.join(os.path.abspath(os.path.dirname(__file__)), "..", "..", "data_private", "work", "backfill")
    os.makedirs(work_dir, exist_ok=True)
    csv_path = os.path.join(work_dir, f"{timestamp}.csv")
    
    updated_docs = []
    
    async with AsyncSessionLocal() as db:
        stmt = select(Document).where(Document.is_deleted == False)
        result = await db.execute(stmt)
        documents = result.scalars().all()

        logger.info(f"Found {len(documents)} documents to evaluate.")

        for doc in documents:
            if doc.metadata_ and doc.metadata_.extra and doc.metadata_.extra.get("doc_type_source") == "manual":
                logger.info(f"Skipping {doc.id} - Source is manual.")
                continue

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
            
            doc_type_res = doctype_service.classify(text)
            
            cat_stmt = select(DocumentCategory).where(DocumentCategory.code == doc_type_res.code)
            cat_res = await db.execute(cat_stmt)
            category = cat_res.scalars().first()
            
            if not category:
                logger.warning(f"Category code {doc_type_res.code} not found in DB.")
                continue
            
            old_category_id = str(doc.category_id) if doc.category_id else ""
            old_extra_subset = {}
            if doc.metadata_ and doc.metadata_.extra:
                old_extra_subset = {
                    "document_type": doc.metadata_.extra.get("document_type"),
                    "confidence": doc.metadata_.extra.get("confidence"),
                    "doc_type_source": doc.metadata_.extra.get("doc_type_source")
                }
                
            updated_docs.append({
                "document_id": str(doc.id),
                "old_category_id": old_category_id,
                "old_extra_subset": json.dumps(old_extra_subset),
                "new_category_id": str(category.id),
                "new_category_code": category.code
            })
            
            if apply:
                doc.category_id = category.id
                if doc.metadata_:
                    if not doc.metadata_.extra:
                        doc.metadata_.extra = {}
                    doc.metadata_.extra["document_type"] = category.name
                    doc.metadata_.extra["confidence"] = doc_type_res.confidence
                    doc.metadata_.extra["doc_type_source"] = "auto"
                
                logger.info(f"Classified {doc.id} as {category.code} (Confidence: {doc_type_res.confidence})")
            else:
                logger.info(f"[DRY RUN] Would classify {doc.id} as {category.code}")
                
        if apply and updated_docs:
            await db.commit()
            
            with open(csv_path, mode='w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=["document_id", "old_category_id", "old_extra_subset", "new_category_id", "new_category_code"])
                writer.writeheader()
                writer.writerows(updated_docs)
            logger.info(f"Wrote audit log to {csv_path}")
            
            if is_es_available():
                es = get_es_client()
                logger.info("Updating Elasticsearch index...")
                for item in updated_docs:
                    try:
                        await es.update(
                            index=search_index_service.index_name,
                            id=item["document_id"],
                            doc={
                                "category_code": item["new_category_code"],
                            },
                            ignore=404
                        )
                    except Exception as e:
                        logger.error(f"Error updating ES for doc {item['document_id']}: {e}")
                            
    if not apply:
        logger.info("Dry run completed. Use --apply to save changes.")
    else:
        logger.info("Backfill applied.")

def main():
    parser = argparse.ArgumentParser(description="Backfill document types")
    parser.add_argument("--apply", action="store_true", help="Apply changes (default is dry-run)")
    parser.add_argument("--undo", type=str, help="Path to CSV file to undo")
    parser.add_argument("--i-know-this-is-production", action="store_true", help="Allow running on production DB")
    
    args = parser.parse_args()
    
    if "sqlite" not in settings.database_url and not args.i_know_this_is_production:
        logger.error("Cowardly refusing to run on non-SQLite database without --i-know-this-is-production flag.")
        sys.exit(1)
        
    if args.undo:
        asyncio.run(undo_backfill(args.undo))
    else:
        asyncio.run(backfill_doctypes(apply=args.apply))

if __name__ == "__main__":
    main()
