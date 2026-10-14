"""
scripts/backup_restore_es.py — Elasticsearch Index Backup & Restore CLI

Cung cấp công cụ sao lưu và phục hồi chỉ mục Elasticsearch:
- Sao lưu toàn bộ Mapping, Settings và Documents ra file JSON nén Gzip.
- Phục hồi chỉ mục tức thời từ bản sao lưu mà không cần truy vấn lại PostgreSQL.
- Phục vụ kiểm thử, di chuyển môi trường (Development -> Production/Defense demo).

Cách sử dụng:
    # Sao lưu index
    python scripts/backup_restore_es.py --backup

    # Phục hồi index từ bản sao lưu
    python scripts/backup_restore_es.py --restore dataset/backups/es_backup_documents_YYYYMMDD_HHMMSS.json.gz
"""
import argparse
import asyncio
import gzip
import json
import os
import sys
import time
from datetime import datetime
from typing import Any

if sys.platform == "win32":
    getattr(sys.stdout, "reconfigure", lambda **kw: None)(encoding="utf-8")
    getattr(sys.stderr, "reconfigure", lambda **kw: None)(encoding="utf-8")

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BACKEND_DIR = os.path.join(BASE_DIR, "backend")
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

try:
    from elasticsearch import AsyncElasticsearch
    from elasticsearch.helpers import async_bulk, async_scan
except ImportError:
    AsyncElasticsearch: Any = None
    async_bulk: Any = None
    async_scan: Any = None

try:
    from loguru import logger
except ImportError:
    import logging
    logger = logging.getLogger("backup_restore_es")
logger: Any = logger

try:
    from app.core.config import settings
    from app.core.elasticsearch import (
        INDEX_MAPPINGS,
        INDEX_NAME,
        INDEX_SETTINGS,
        get_es_client,
        is_es_available,
    )
except ImportError:
    from backend.app.core.config import settings
    from backend.app.core.elasticsearch import (
        INDEX_MAPPINGS,
        INDEX_NAME,
        INDEX_SETTINGS,
        get_es_client,
        is_es_available,
    )


BACKUP_DIR = os.path.join(BASE_DIR, "dataset", "backups")


async def backup_elasticsearch_index(output_file: str | None = None) -> dict[str, Any]:
    """Sao lưu toàn bộ mapping và documents từ Elasticsearch ra file gzip."""
    t0 = time.perf_counter()
    if not is_es_available():
        logger.error(f"Elasticsearch tại {settings.es_url} hiện không khả dụng.")
        return {"status": "ERROR", "message": "Elasticsearch is offline"}

    os.makedirs(BACKUP_DIR, exist_ok=True)
    if not output_file:
        timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = os.path.join(BACKUP_DIR, f"es_backup_{INDEX_NAME}_{timestamp_str}.json.gz")

    es = get_es_client()
    exists = await es.indices.exists(index=INDEX_NAME)
    if not exists:
        logger.warning(f"Index '{INDEX_NAME}' chưa tồn tại trong Elasticsearch.")
        return {"status": "ERROR", "message": f"Index {INDEX_NAME} does not exist"}

    logger.info(f"Bắt đầu sao lưu index '{INDEX_NAME}'...")

    # Lấy mapping và settings hiện tại
    mapping_res = await es.indices.get_mapping(index=INDEX_NAME)
    settings_res = await es.indices.get_settings(index=INDEX_NAME)

    documents: list[dict[str, Any]] = []
    # Quét toàn bộ documents bằng async_scan (scroll)
    async for doc in async_scan(es, index=INDEX_NAME, query={"query": {"match_all": {}}}):
        documents.append({
            "_id": doc["_id"],
            "_source": doc["_source"],
        })

    backup_payload = {
        "version": "1.0",
        "created_at": datetime.now().isoformat(),
        "index_name": INDEX_NAME,
        "total_documents": len(documents),
        "settings": settings_res.get(INDEX_NAME, {}).get("settings", {}),
        "mappings": mapping_res.get(INDEX_NAME, {}).get("mappings", {}),
        "documents": documents,
    }

    # Ghi nén gzip
    with gzip.open(output_file, "wt", encoding="utf-8") as f_out:
        json.dump(backup_payload, f_out, ensure_ascii=False)

    file_size_kb = round(os.path.getsize(output_file) / 1024, 2)
    elapsed = round(time.perf_counter() - t0, 2)

    logger.info(
        f"SAO LƯU THÀNH CÔNG: {len(documents)} tài liệu -> {output_file} "
        f"({file_size_kb} KB) trong {elapsed}s."
    )

    return {
        "status": "SUCCESS",
        "output_file": output_file,
        "total_documents": len(documents),
        "file_size_kb": file_size_kb,
        "elapsed_seconds": elapsed,
    }


async def restore_elasticsearch_index(input_file: str) -> dict[str, Any]:
    """Phục hồi index Elasticsearch từ file gzip backup."""
    t0 = time.perf_counter()
    if not is_es_available():
        logger.error(f"Elasticsearch tại {settings.es_url} hiện không khả dụng.")
        return {"status": "ERROR", "message": "Elasticsearch is offline"}

    if not os.path.exists(input_file):
        logger.error(f"File sao lưu không tồn tại: {input_file}")
        return {"status": "ERROR", "message": f"File {input_file} not found"}

    es = get_es_client()
    logger.info(f"Đang đọc dữ liệu sao lưu từ {input_file}...")

    with gzip.open(input_file, "rt", encoding="utf-8") as f_in:
        backup_data = json.load(f_in)

    target_index = INDEX_NAME
    docs_to_restore = backup_data.get("documents", [])
    total_docs = len(docs_to_restore)

    # 1. Tái tạo index sạch với settings và mappings mới nhất
    if await es.indices.exists(index=target_index):
        logger.info(f"Xóa index cũ '{target_index}'...")
        await es.indices.delete(index=target_index)

    logger.info(f"Khởi tạo lại index '{target_index}'...")
    await es.indices.create(
        index=target_index,
        settings=INDEX_SETTINGS,
        mappings=INDEX_MAPPINGS,
    )

    # 2. Chuẩn bị bulk actions
    actions = []
    for item in docs_to_restore:
        actions.append({
            "_index": target_index,
            "_id": item["_id"],
            "_source": item["_source"],
        })

    # 3. Nạp hàng loạt
    success_count = 0
    failed_count = 0
    batch_size = 200

    for i in range(0, len(actions), batch_size):
        chunk = actions[i : i + batch_size]
        try:
            ok, failed = await async_bulk(es, chunk, refresh=False, stats_only=True)
            success_count += ok
            failed_count += failed if isinstance(failed, int) else len(failed)
            logger.info(f"Đã phục hồi {success_count}/{total_docs} tài liệu...")
        except Exception as exc:
            logger.error(f"Lỗi phục hồi lô {i}-{i+batch_size}: {exc}")
            failed_count += len(chunk)

    await es.indices.refresh(index=target_index)
    count_res = await es.count(index=target_index)
    actual_count = count_res.get("count", 0)
    elapsed = round(time.perf_counter() - t0, 2)

    logger.info(
        f"PHỤC HỒI HOÀN TẤT: Thành công {success_count}/{total_docs} tài liệu "
        f"vào index '{target_index}' ({actual_count} hiện hữu) trong {elapsed}s."
    )

    return {
        "status": "SUCCESS",
        "input_file": input_file,
        "restored_count": success_count,
        "failed_count": failed_count,
        "actual_index_count": actual_count,
        "elapsed_seconds": elapsed,
    }


def main():
    parser = argparse.ArgumentParser(description="Elasticsearch Index Backup & Restore Tool")
    parser.add_argument("--backup", action="store_true", help="Sao lưu index ra file gzip")
    parser.add_argument("--restore", type=str, help="Đường dẫn file .json.gz để phục hồi")
    parser.add_argument("--output", type=str, default=None, help="Tùy chọn file đích khi sao lưu")

    args = parser.parse_args()

    if args.backup:
        asyncio.run(backup_elasticsearch_index(output_file=args.output))
    elif args.restore:
        asyncio.run(restore_elasticsearch_index(input_file=args.restore))
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
