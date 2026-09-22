"""
backend/app/core/elasticsearch.py — Elasticsearch Client & Index Setup

Cấu hình Elasticsearch client và khởi tạo index "documents" với Custom Vietnamese Analyzer:
- vietnamese_exact: Giữ nguyên dấu tiếng Việt để tìm kiếm chính xác.
- vietnamese_ascii: Tokenizer + lowercase + asciifolding để tìm kiếm không dấu (vd: "don xin nghi hoc" -> "Đơn xin nghỉ học").

Ref: .ai/research/Elasticsearch.md, .ai/research/VietnameseSearch.md, ADR-005
"""
from typing import Any
from elasticsearch import AsyncElasticsearch
from loguru import logger

from app.core.config import settings

import socket
from urllib.parse import urlparse

# ── Elasticsearch Async Client ────────────────────────────────────────────────
_es_client: AsyncElasticsearch | None = None


def is_es_available() -> bool:
    """Kiểm tra nhanh kết nối TCP tới Elasticsearch trong 150ms."""
    try:
        parsed = urlparse(settings.es_url)
        host = parsed.hostname or "127.0.0.1"
        port = parsed.port or 9200
        sock = socket.create_connection((host, port), timeout=0.15)
        sock.close()
        return True
    except Exception:
        return False


def get_es_client() -> AsyncElasticsearch:
    """Singleton getter cho AsyncElasticsearch client."""
    global _es_client
    if _es_client is None:
        auth = (settings.es_username, settings.es_password) if settings.es_password else None
        _es_client = AsyncElasticsearch(
            hosts=[settings.es_url],
            basic_auth=auth,
            request_timeout=1.5,
            max_retries=1,
            retry_on_timeout=False,
        )
    return _es_client



# ── Index Definition & Mapping ────────────────────────────────────────────────
INDEX_NAME = settings.es_index_documents

INDEX_SETTINGS: dict[str, Any] = {
    "number_of_shards": 1,
    "number_of_replicas": 0,
    "analysis": {
        "analyzer": {
            # 1. Tìm chính xác có dấu tiếng Việt
            "vietnamese_exact": {
                "type": "custom",
                "tokenizer": "standard",
                "filter": ["lowercase", "trim"],
            },
            # 2. Tìm không dấu / chấp nhận lỗi OCR dấu tiếng Việt
            "vietnamese_ascii": {
                "type": "custom",
                "tokenizer": "standard",
                "filter": ["lowercase", "asciifolding", "trim"],
            },
        },
    },
}

INDEX_MAPPINGS: dict[str, Any] = {
    "properties": {
        "document_id": {"type": "keyword"},
        "title": {
            "type": "text",
            "analyzer": "vietnamese_exact",
            "fields": {
                "ascii": {
                    "type": "text",
                    "analyzer": "vietnamese_ascii",
                },
                "keyword": {"type": "keyword", "ignore_above": 256},
            },
        },
        "content": {
            "type": "text",
            "analyzer": "vietnamese_exact",
            "term_vector": "with_positions_offsets",
            "fields": {
                "ascii": {
                    "type": "text",
                    "analyzer": "vietnamese_ascii",
                    "term_vector": "with_positions_offsets",
                },
            },
        },
        "content_corrected": {
            "type": "text",
            "analyzer": "vietnamese_exact",
            "fields": {
                "ascii": {
                    "type": "text",
                    "analyzer": "vietnamese_ascii",
                },
            },
        },
        "category_code": {"type": "keyword"},
        "category_name": {
            "type": "text",
            "analyzer": "vietnamese_exact",
            "fields": {
                "keyword": {"type": "keyword"},
            },
        },
        "student_id": {"type": "keyword"},
        "student_name": {
            "type": "text",
            "analyzer": "vietnamese_exact",
            "fields": {
                "ascii": {
                    "type": "text",
                    "analyzer": "vietnamese_ascii",
                },
                "keyword": {"type": "keyword"},
            },
        },
        "document_date": {
            "type": "date",
            "format": "yyyy-MM-dd||strict_date_optional_time||epoch_millis",
            "ignore_malformed": True,
        },
        "document_number": {"type": "keyword"},
        "uploaded_by": {"type": "keyword"},
        "ocr_status": {"type": "keyword"},
        "ocr_confidence": {"type": "float"},
        "is_deleted": {"type": "boolean"},
        "created_at": {"type": "date"},
        "updated_at": {"type": "date"},
    }
}


async def init_elasticsearch_index() -> None:
    """
    Kiểm tra và khởi tạo Elasticsearch index với mapping và custom analyzer.
    Được gọi khi ứng dụng FastAPI startup.
    """
    if not is_es_available():
        logger.info(
            "Elasticsearch is offline ({host}:{port}). Search service will operate seamlessly via PostgreSQL fallback mode.",
            host=settings.es_host,
            port=settings.es_port,
        )
        return

    es = get_es_client()
    try:
        exists = await es.indices.exists(index=INDEX_NAME)
        if not exists:
            logger.info("Elasticsearch index '{idx}' does not exist. Creating...", idx=INDEX_NAME)
            await es.indices.create(
                index=INDEX_NAME,
                settings=INDEX_SETTINGS,
                mappings=INDEX_MAPPINGS,
            )
            logger.info("Successfully created Elasticsearch index '{idx}' with Vietnamese analyzers.", idx=INDEX_NAME)
        else:
            logger.info("Elasticsearch index '{idx}' already exists.", idx=INDEX_NAME)
    except Exception as exc:
        logger.warning(
            "Could not connect to Elasticsearch index '{idx}': {err}. Full-text search will use PostgreSQL fallback.",
            idx=INDEX_NAME,
            err=str(exc),
        )
