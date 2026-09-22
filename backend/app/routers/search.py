"""
backend/app/routers/search.py — Full-Text Search API Endpoint

Cung cấp API tìm kiếm toàn văn, tìm kiếm mờ (fuzzy) và lọc đa chiều trên Elasticsearch:
- Tìm kiếm cả tiếng Việt có dấu và không dấu (nhờ custom analyzer asciifolding).
- Highlight các đoạn văn bản khớp từ khóa.
- Ghi lịch sử truy vấn vào bảng `search_history` trong PostgreSQL.

Ref: .ai/research/Elasticsearch.md, .ai/research/VietnameseSearch.md, .ai/design/Database.md §2.8
"""
import math
import time
from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.core.elasticsearch import INDEX_NAME, get_es_client
from app.models.search_history import SearchHistory
from app.models.users import User
from app.schemas.search import SearchHit, SearchResponse

router = APIRouter(prefix="/search", tags=["search"])


@router.get(
    "",
    response_model=SearchResponse,
    summary="Tìm kiếm toàn văn tài liệu trên Elasticsearch (RBAC)",
)
async def search_documents(
    q: str = Query(..., min_length=1, description="Từ khóa tìm kiếm (tiếng Việt có dấu hoặc không dấu)"),
    category_code: str | None = Query(None, description="Lọc theo mã danh mục (vd: DON_NGHI_HOC)"),
    ocr_status: str | None = Query(None, description="Lọc theo trạng thái OCR (vd: DONE, PENDING)"),
    date_from: str | None = Query(None, description="Ngày tạo từ (định dạng YYYY-MM-DD)"),
    date_to: str | None = Query(None, description="Ngày tạo đến (định dạng YYYY-MM-DD)"),
    fuzzy: bool = Query(True, description="Bật tìm kiếm mờ (Fuzzy matching) để bù đắp sai sót OCR / chính tả"),
    page: int = Query(1, ge=1, description="Số trang (bắt đầu từ 1)"),
    page_size: int = Query(10, ge=1, le=100, description="Số kết quả mỗi trang"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> SearchResponse:
    """
    Tìm kiếm toàn văn tài liệu trên Elasticsearch với:
    - Phân quyền RBAC: STUDENT chỉ tìm kiếm hồ sơ của mình hoặc hồ sơ đã APPROVED; STAFF/ADMIN tìm kiếm toàn bộ.
    - Tìm kiếm đa trường: tiêu đề, nội dung OCR, tên sinh viên, MSSV, số hiệu.
    - Tìm không dấu / có dấu thông minh.
    - Trích xuất highlight các đoạn khớp.
    - Tự động ghi nhận lịch sử tìm kiếm vào Database.
    """
    t0 = time.monotonic()
    es = get_es_client()

    query_str = q.strip()
    from_offset = (page - 1) * page_size

    # ── 1. Xây dựng Elasticsearch Query ────────────────────────────────────────
    search_fields = [
        "title^3",
        "title.ascii^2",
        "content^2",
        "content.ascii^1.5",
        "content_corrected^2",
        "content_corrected.ascii^1.5",
        "student_name^2.5",
        "student_name.ascii^2",
        "student_id^3",
        "document_number^2",
    ]

    must_clause: list[dict[str, Any]] = [
        {
            "multi_match": {
                "query": query_str,
                "fields": search_fields,
                "type": "best_fields",
                "fuzziness": "AUTO" if fuzzy else "0",
                "prefix_length": 2 if fuzzy else 0,
            }
        }
    ]

    # Filters (không ảnh hưởng score BM25)
    filter_clause: list[dict[str, Any]] = [
        {"term": {"is_deleted": False}}
    ]

    # RBAC Filter
    role_name = current_user.role.name if current_user.role else "STUDENT"
    if role_name == "STUDENT":
        # Sinh viên chỉ thấy tài liệu do chính mình upload hoặc tài liệu đã được duyệt (APPROVED)
        filter_clause.append({
            "bool": {
                "should": [
                    {"term": {"uploaded_by": str(current_user.id)}},
                    {"term": {"ocr_status": "APPROVED"}},
                ],
                "minimum_should_match": 1,
            }
        })

    if category_code:
        filter_clause.append({"term": {"category_code": category_code}})
    if ocr_status:
        filter_clause.append({"term": {"ocr_status": ocr_status.upper()}})
    if date_from or date_to:
        range_query: dict[str, Any] = {}
        if date_from:
            range_query["gte"] = date_from
        if date_to:
            range_query["lte"] = date_to
        filter_clause.append({"range": {"created_at": range_query}})

    body: dict[str, Any] = {
        "from": from_offset,
        "size": page_size,
        "track_total_hits": True,
        "query": {
            "bool": {
                "must": must_clause,
                "filter": filter_clause,
            }
        },
        "highlight": {
            "pre_tags": ["<em>"],
            "post_tags": ["</em>"],
            "fields": {
                "content": {"fragment_size": 150, "number_of_fragments": 3},
                "content.ascii": {"fragment_size": 150, "number_of_fragments": 3},
                "title": {"number_of_fragments": 0},
                "student_name": {"number_of_fragments": 0},
            },
        },
    }

    # ── 2. Thực thi Search ────────────────────────────────────────────────────
    try:
        es_res = await es.search(index=INDEX_NAME, body=body)
    except Exception as exc:
        logger.error("Elasticsearch query error: {err}", err=str(exc))
        # Nếu index chưa tồn tại hoặc lỗi khác, trả về danh sách rỗng
        es_res = {"hits": {"total": {"value": 0}, "hits": []}, "took": 0}

    total_hits = es_res["hits"]["total"]["value"]
    hits_raw = es_res["hits"]["hits"]
    took_ms = es_res.get("took", int((time.monotonic() - t0) * 1000))

    # ── 3. Parse Kết Quả ──────────────────────────────────────────────────────
    results: list[SearchHit] = []
    for hit in hits_raw:
        source = hit["_source"]
        highlights = hit.get("highlight", {})

        # Lấy snippet từ content hoặc content.ascii highlight
        snippet = None
        if "content" in highlights and highlights["content"]:
            snippet = "... ".join(highlights["content"])
        elif "content.ascii" in highlights and highlights["content.ascii"]:
            snippet = "... ".join(highlights["content.ascii"])
        elif source.get("content"):
            snippet = source["content"][:200] + "..." if len(source["content"]) > 200 else source["content"]

        doc_id_val = source.get("document_id") or hit.get("_id")
        results.append(
            SearchHit(
                document_id=UUID(doc_id_val),
                title=source.get("title", ""),
                content_snippet=snippet,
                category_code=source.get("category_code"),
                category_name=source.get("category_name"),
                student_id=source.get("student_id"),
                student_name=source.get("student_name"),
                document_date=source.get("document_date"),
                document_number=source.get("document_number"),
                ocr_status=source.get("ocr_status", "DONE"),
                ocr_confidence=source.get("ocr_confidence"),
                score=round(float(hit.get("_score") or 0.0), 3),
                highlights=highlights,
                created_at=source.get("created_at"),
            )
        )

    total_pages = math.ceil(total_hits / page_size) if total_hits > 0 else 0

    # ── 4. Ghi Lịch Sử Tìm Kiếm vào PostgreSQL ─────────────────────────────────
    filters_dict = {
        "category_code": category_code,
        "ocr_status": ocr_status,
        "date_from": date_from,
        "date_to": date_to,
        "fuzzy": fuzzy,
    }
    # Lọc bỏ các key None
    active_filters = {k: v for k, v in filters_dict.items() if v is not None}

    try:
        history_entry = SearchHistory(
            user_id=current_user.id,
            keyword=query_str,
            filter=active_filters if active_filters else None,
            result_count=total_hits,
        )
        db.add(history_entry)
        await db.commit()
    except Exception as exc:
        logger.warning("Failed to log search history: {err}", err=str(exc))

    return SearchResponse(
        query=query_str,
        total_hits=total_hits,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
        took_ms=took_ms,
        results=results,
    )
