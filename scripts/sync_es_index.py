"""
scripts/sync_es_index.py — Bulk Reindex Dữ liệu từ PostgreSQL sang Elasticsearch

Công cụ quản trị đồng bộ toàn bộ tài liệu hồ sơ sinh viên từ PostgreSQL sang Elasticsearch 8.
Hỗ trợ:
- Lập chỉ mục hàng loạt (Bulk Indexing) với tốc độ cao.
- Tùy chọn xóa và tạo lại Index (--recreate).
- Tùy chọn kích thước lô (--batch-size).
- Báo cáo chi tiết số lượng tài liệu đã đồng bộ và độ trễ.

Sử dụng:
    python scripts/sync_es_index.py [--recreate] [--batch-size 100]
"""
import argparse
import asyncio
import os
import sys
import time
from typing import Any

# Đảm bảo UTF-8 cho Windows console
if sys.platform == "win32":
    getattr(sys.stdout, "reconfigure", lambda **kw: None)(encoding="utf-8")
    getattr(sys.stderr, "reconfigure", lambda **kw: None)(encoding="utf-8")

# Thêm thư mục gốc và backend vào sys.path
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BACKEND_DIR = os.path.join(BASE_DIR, "backend")
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

try:
    from elasticsearch import AsyncElasticsearch
    from elasticsearch.helpers import async_bulk
except ImportError:
    AsyncElasticsearch: Any = None
    async_bulk: Any = None

try:
    from loguru import logger
except ImportError:
    import logging
    logger = logging.getLogger("sync_es_index")
logger: Any = logger
from sqlalchemy import select
from sqlalchemy.orm import selectinload

try:
    from app.core.config import settings
    from app.core.database import AsyncSessionLocal
    from app.core.elasticsearch import INDEX_MAPPINGS, INDEX_NAME, INDEX_SETTINGS, get_es_client, is_es_available
    from app.models.documents import Document
    from app.models.ocr_results import OCRResult
    from app.services.embedding_service import embedding_service
except ImportError:
    from backend.app.core.config import settings
    from backend.app.core.database import AsyncSessionLocal
    from backend.app.core.elasticsearch import INDEX_MAPPINGS, INDEX_NAME, INDEX_SETTINGS, get_es_client, is_es_available
    from backend.app.models.documents import Document
    from backend.app.models.ocr_results import OCRResult
    from backend.app.services.embedding_service import embedding_service


async def sync_all_documents(recreate: bool = False, batch_size: int = 100, include_deleted: bool = False) -> dict[str, Any]:
    """Đồng bộ toàn bộ tài liệu từ PostgreSQL sang Elasticsearch."""
    t0 = time.perf_counter()

    if not is_es_available():
        logger.error(f"Elasticsearch tại {settings.es_url} hiện không khả dụng. Vui lòng kiểm tra container/dịch vụ.")
        return {"status": "ERROR", "message": "Elasticsearch is offline"}

    es = get_es_client()

    # 1. Tùy chọn xóa và tạo lại Index sạch
    if recreate:
        logger.info(f"Đang xóa index cũ '{INDEX_NAME}' để tạo lại từ đầu...")
        try:
            if await es.indices.exists(index=INDEX_NAME):
                await es.indices.delete(index=INDEX_NAME)
                logger.info(f"Đã xóa index '{INDEX_NAME}'.")
            await es.indices.create(
                index=INDEX_NAME,
                settings=INDEX_SETTINGS,
                mappings=INDEX_MAPPINGS,
            )
            logger.info(f"Đã khởi tạo lại index '{INDEX_NAME}' với mapping và custom analyzer mới nhất.")
        except Exception as exc:
            logger.error(f"Lỗi khi tạo lại index: {exc}")
            return {"status": "ERROR", "message": str(exc)}
    else:
        # Đảm bảo index đã tồn tại và cập nhật mapping mới nhất
        try:
            exists = await es.indices.exists(index=INDEX_NAME)
            if not exists:
                await es.indices.create(
                    index=INDEX_NAME,
                    settings=INDEX_SETTINGS,
                    mappings=INDEX_MAPPINGS,
                )
                logger.info(f"Tạo mới index '{INDEX_NAME}'.")
            else:
                await es.indices.put_mapping(index=INDEX_NAME, properties=INDEX_MAPPINGS["properties"])
                logger.info(f"Đã cập nhật mapping mới nhất cho index '{INDEX_NAME}'.")
        except Exception as exc:
            logger.warning(f"Lỗi kiểm tra mapping: {exc}")

    # 2. Đọc dữ liệu từ PostgreSQL
    logger.info("Đang nạp danh sách tài liệu từ cơ sở dữ liệu PostgreSQL...")
    async with AsyncSessionLocal() as session:
        stmt = (
            select(Document)
            .options(
                selectinload(Document.category),
                selectinload(Document.metadata_),
                selectinload(Document.uploader),
                selectinload(Document.ocr_results),
            )
        )
        if not include_deleted:
            stmt = stmt.where(Document.is_deleted == False)

        result = await session.execute(stmt)
        documents = result.scalars().all()

    total_docs = len(documents)
    logger.info(f"Tìm thấy {total_docs} tài liệu cần đồng bộ từ PostgreSQL.")

    if total_docs == 0:
        return {
            "status": "SUCCESS",
            "total_documents": 0,
            "indexed_count": 0,
            "elapsed_seconds": round(time.perf_counter() - t0, 2),
        }

    # 3. Chuẩn bị bulk payload
    actions = []
    for doc in documents:
        # Lấy văn bản OCR mới nhất
        ocr_text = ""
        confidence = None
        for ocr in doc.ocr_results:
            if ocr.is_latest:
                ocr_text = ocr.corrected_text or ocr.raw_text or ""
                confidence = float(ocr.confidence_score) if ocr.confidence_score is not None else None
                break
        if not ocr_text and doc.ocr_results:
            ocr_text = doc.ocr_results[0].corrected_text or doc.ocr_results[0].raw_text or ""
            if doc.ocr_results[0].confidence_score is not None:
                confidence = float(doc.ocr_results[0].confidence_score)

        st_name = (
            doc.metadata_.student_name
            if doc.metadata_ and doc.metadata_.student_name
            else (doc.uploader.full_name if doc.uploader else None)
        )
        st_id = (
            doc.metadata_.student_id
            if doc.metadata_ and doc.metadata_.student_id
            else (doc.uploader.mssv if doc.uploader else None)
        )
        doc_num = doc.metadata_.document_number if doc.metadata_ else None
        doc_date = doc.metadata_.document_date.isoformat() if doc.metadata_ and doc.metadata_.document_date else None

        extra_data = (doc.metadata_.extra or {}) if doc.metadata_ and doc.metadata_.extra else {}
        tags = extra_data.get("tags", [])
        priority_score = extra_data.get("priority_score", 0)

        vec = await embedding_service.get_embedding(f"{doc.title or ''} {ocr_text[:400]}")

        action = {
            "_index": INDEX_NAME,
            "_id": str(doc.id),
            "_source": {
                "document_id": str(doc.id),
                "title": doc.title or doc.original_filename,
                "content": ocr_text,
                "content_corrected": ocr_text,
                "category_code": doc.category.code if doc.category else None,
                "category_name": doc.category.name if doc.category else None,
                "student_id": st_id,
                "student_name": st_name,
                "document_date": doc_date,
                "document_number": doc_num,
                "uploaded_by": str(doc.uploaded_by) if doc.uploaded_by else None,
                "ocr_status": doc.ocr_status or "DONE",
                "ocr_confidence": confidence,
                "tags": tags,
                "priority_score": priority_score,
                "metadata_extra": extra_data,
                "title_suggest": doc.title or doc.original_filename,
                "content_vector": vec,
                "is_deleted": doc.is_deleted,
                "created_at": doc.created_at.isoformat() if doc.created_at else None,
                "updated_at": doc.updated_at.isoformat() if doc.updated_at else None,
            },
        }
        actions.append(action)

    # 4. Thực thi bulk indexing theo lô
    success_count = 0
    failed_count = 0

    for i in range(0, len(actions), batch_size):
        chunk = actions[i : i + batch_size]
        try:
            ok, failed = await async_bulk(es, chunk, refresh=False, stats_only=True)
            success_count += ok
            failed_count += failed if isinstance(failed, int) else (len(failed) if isinstance(failed, list) else 0)
            logger.info(f"Đã lập chỉ mục {success_count}/{total_docs} tài liệu...")
        except Exception as exc:
            logger.error(f"Lỗi khi bulk index lô {i}-{i+batch_size}: {exc}")
            failed_count += len(chunk)

    # Làm tươi index để tìm kiếm thấy ngay
    await es.indices.refresh(index=INDEX_NAME)

    # Kiểm tra số lượng thực tế trong index
    count_res = await es.count(index=INDEX_NAME)
    actual_es_count = count_res.get("count", 0)

    elapsed = round(time.perf_counter() - t0, 2)
    logger.info(
        f"ĐỒNG BỘ HOÀN TẤT trong {elapsed}s: "
        f"Thành công {success_count}/{total_docs} tài liệu. "
        f"Tổng tài liệu trong ES index: {actual_es_count}."
    )

    return {
        "status": "SUCCESS",
        "total_db_documents": total_docs,
        "indexed_count": success_count,
        "failed_count": failed_count,
        "actual_es_index_count": actual_es_count,
        "elapsed_seconds": elapsed,
    }


def main():
    parser = argparse.ArgumentParser(description="Đồng bộ dữ liệu từ PostgreSQL sang Elasticsearch")
    parser.add_argument("--recreate", action="store_true", help="Xóa index cũ và tạo lại toàn bộ mapping sạch")
    parser.add_argument("--batch-size", type=int, default=100, help="Kích thước lô khi bulk index (mặc định: 100)")
    parser.add_argument("--include-deleted", action="store_true", help="Bao gồm cả tài liệu đã xóa mềm")

    args = parser.parse_args()

    asyncio.run(
        sync_all_documents(
            recreate=args.recreate,
            batch_size=args.batch_size,
            include_deleted=args.include_deleted,
        )
    )


if __name__ == "__main__":
    main()
