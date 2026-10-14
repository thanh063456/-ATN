"""
backend/app/core/elasticsearch.py — Elasticsearch Client & Index Setup

Cấu hình Elasticsearch client và khởi tạo index "documents" với Custom Vietnamese Analyzer:
- vietnamese_exact: Giữ nguyên dấu tiếng Việt để tìm kiếm chính xác.
- vietnamese_ascii: Tokenizer + lowercase + asciifolding để tìm kiếm không dấu (vd: "don xin nghi hoc" -> "Đơn xin nghỉ học").

Ref: .ai/research/Elasticsearch.md, .ai/research/VietnameseSearch.md, ADR-005
"""
import socket
import time
from typing import Any
from urllib.parse import urlparse

try:
    from elasticsearch import AsyncElasticsearch
except ImportError:
    AsyncElasticsearch: Any = None

try:
    from loguru import logger
except ImportError:
    import logging
    logger = logging.getLogger("elasticsearch")
logger: Any = logger
from app.core.config import settings

# ── Elasticsearch Async Client & Availability Cache ───────────────────────────
_es_client: Any | None = None
_es_availability_cache: tuple[bool, float] = (False, 0.0)
_ES_CACHE_TTL_SECONDS: float = 3.0


def is_es_available(force_refresh: bool = False) -> bool:
    """
    Kiểm tra nhanh kết nối TCP tới Elasticsearch trong 300ms (IPv4 localhost an toàn).
    Sử dụng TTL cache 3s để tránh nghẽn socket timeout khi ES offline dưới tải đồng thời cao.
    """
    global _es_availability_cache
    if AsyncElasticsearch is None:
        return False

    now = time.monotonic()
    if not force_refresh and (now - _es_availability_cache[1] < _ES_CACHE_TTL_SECONDS):
        return _es_availability_cache[0]

    try:
        parsed = urlparse(settings.es_url)
        host = parsed.hostname or "127.0.0.1"
        if host == "localhost":
            host = "127.0.0.1"  # Tránh trễ phân giải IPv6 ::1 trên Windows
        port = parsed.port or 9200
        sock = socket.create_connection((host, port), timeout=0.3)
        sock.close()
        _es_availability_cache = (True, now)
        return True
    except Exception:
        _es_availability_cache = (False, now)
        return False


def get_es_client() -> Any:
    """Singleton getter cho AsyncElasticsearch client."""
    global _es_client
    if AsyncElasticsearch is None:
        raise RuntimeError("Thư viện 'elasticsearch' chưa được cài đặt trong môi trường Python.")
    if _es_client is None:
        auth = (settings.es_username, settings.es_password) if settings.es_password else None
        _es_client = AsyncElasticsearch(
            hosts=[settings.es_url],
            basic_auth=auth,
            request_timeout=2.0,
            max_retries=1,
            retry_on_timeout=False,
        )
    return _es_client


async def close_es_client() -> None:
    """Đóng kết nối AsyncElasticsearch client khi shutdown ứng dụng."""
    global _es_client
    if _es_client is not None:
        try:
            await _es_client.close()
            logger.info("Elasticsearch client connections closed cleanly.")
        except Exception as exc:
            logger.debug(f"Error closing Elasticsearch client: {exc}")
        finally:
            _es_client = None



# ── Index Definition & Mapping ────────────────────────────────────────────────
INDEX_NAME = settings.es_index_documents

INDEX_SETTINGS: dict[str, Any] = {
    "number_of_shards": 1,
    "number_of_replicas": 0,
    "analysis": {
        "filter": {
            # Từ điển từ đồng nghĩa & viết tắt hành chính ĐH Đà Lạt & Phòng CTSV
            # Bao gồm cả dạng có dấu và không dấu để tối ưu tìm kiếm hai chiều
            "synonym_ctsv": {
                "type": "synonym_graph",
                "synonyms": [
                    "dlu, dhdl, đhđl, đại học đà lạt, dai hoc da lat",
                    "ctsv, công tác sinh viên, phòng công tác sinh viên, cong tac sinh vien, phong cong tac sinh vien",
                    "mghp, miễn giảm học phí, mien giam hoc phi",
                    "kkht, học bổng khuyến khích, học bổng khuyến khích học tập, hoc bong khuyen khich, hoc bong khuyen khich hoc tap",
                    "bảo lưu, nghỉ học tạm thời, tạm dừng học tập, bao luu, nghi hoc tam thoi, tam dung hoc tap",
                    "thôi học, xin rút hồ sơ, buộc thôi học, thoi hoc, xin rut ho so, buoc thoi hoc",
                    "bhyt, bhxh, bảo hiểm y tế, bao hiem y te",
                    "mssv, mã sinh viên, mã số sinh viên, ma sinh vien, ma so sinh vien",
                    "gvcn, giáo viên chủ nhiệm, giảng viên chủ nhiệm, giao vien chu nhiem, giang vien chu nhiem",
                    "nckh, nghiên cứu khoa học, nghien cuu khoa hoc",
                    "ctxh, công tác xã hội, cong tac xa hoi",
                    "drl, điểm rèn luyện, diem ren luyen",
                ],
            },
        },
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
            # 3. Search analyzer có dấu kèm từ đồng nghĩa
            "vietnamese_search_synonym": {
                "type": "custom",
                "tokenizer": "standard",
                "filter": ["lowercase", "synonym_ctsv", "trim"],
            },
            # 4. Search analyzer không dấu kèm từ đồng nghĩa (synonym trước rồi mới asciifolding)
            "vietnamese_search_synonym_ascii": {
                "type": "custom",
                "tokenizer": "standard",
                "filter": ["lowercase", "synonym_ctsv", "asciifolding", "trim"],
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
            "search_analyzer": "vietnamese_search_synonym",
            "fields": {
                "ascii": {
                    "type": "text",
                    "analyzer": "vietnamese_ascii",
                    "search_analyzer": "vietnamese_search_synonym_ascii",
                },
                "keyword": {"type": "keyword", "ignore_above": 256},
            },
        },
        "content": {
            "type": "text",
            "analyzer": "vietnamese_exact",
            "search_analyzer": "vietnamese_search_synonym",
            "term_vector": "with_positions_offsets",
            "fields": {
                "ascii": {
                    "type": "text",
                    "analyzer": "vietnamese_ascii",
                    "search_analyzer": "vietnamese_search_synonym_ascii",
                    "term_vector": "with_positions_offsets",
                },
            },
        },
        "content_corrected": {
            "type": "text",
            "analyzer": "vietnamese_exact",
            "search_analyzer": "vietnamese_search_synonym",
            "term_vector": "with_positions_offsets",
            "fields": {
                "ascii": {
                    "type": "text",
                    "analyzer": "vietnamese_ascii",
                    "search_analyzer": "vietnamese_search_synonym_ascii",
                    "term_vector": "with_positions_offsets",
                },
            },
        },
        "category_code": {"type": "keyword"},
        "category_name": {
            "type": "text",
            "analyzer": "vietnamese_exact",
            "search_analyzer": "vietnamese_search_synonym",
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
        "tags": {"type": "keyword"},
        "priority_score": {"type": "integer"},
        "metadata_extra": {"type": "object", "dynamic": True},
        "title_suggest": {"type": "search_as_you_type"},
        "content_vector": {
            "type": "dense_vector",
            "dims": 768,
            "index": True,
            "similarity": "cosine",
        },
    }
}


async def init_elasticsearch_index() -> None:
    """
    Kiểm tra và khởi tạo Elasticsearch index với mapping và custom analyzer.
    Được gọi khi ứng dụng FastAPI startup.
    """
    if not is_es_available():
        logger.info(
            f"Elasticsearch is offline ({settings.es_host}:{settings.es_port}). "
            "Search service will operate seamlessly via PostgreSQL fallback mode."
        )
        return

    es = get_es_client()
    try:
        exists = await es.indices.exists(index=INDEX_NAME)
        if not exists:
            logger.info(f"Elasticsearch index '{INDEX_NAME}' does not exist. Creating...")
            await es.indices.create(
                index=INDEX_NAME,
                settings=INDEX_SETTINGS,
                mappings=INDEX_MAPPINGS,
            )
            logger.info(f"Successfully created Elasticsearch index '{INDEX_NAME}' with Vietnamese analyzers.")
        else:
            try:
                await es.indices.put_mapping(index=INDEX_NAME, properties=INDEX_MAPPINGS["properties"])
                logger.info(f"Elasticsearch index '{INDEX_NAME}' already exists. Synced mappings.")
            except Exception as map_err:
                logger.warning(
                    f"Elasticsearch index '{INDEX_NAME}' exists but mapping sync was partial ({map_err}). "
                    "Run 'make es-reindex' to fully recreate index with new analyzers."
                )
    except Exception as exc:
        logger.warning(
            f"Could not connect to Elasticsearch index '{INDEX_NAME}': {exc}. Full-text search will use PostgreSQL fallback."
        )
