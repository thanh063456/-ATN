"""
backend/app/routers/search.py — Full-Text Search API Endpoint

Cung cấp API tìm kiếm toàn văn, tìm kiếm mờ (fuzzy) và lọc đa chiều:
- Tìm kiếm trên Elasticsearch với bộ phân tích tiếng Việt (vietnamese_exact & vietnamese_ascii).
- Tự động Fallback tìm kiếm thông minh trên PostgreSQL nếu Elasticsearch chưa khởi động / chưa sync / không có kết quả.
- Tìm kiếm cả tiếng Việt có dấu và không dấu, tìm theo MSSV, Họ tên sinh viên, Tiêu đề và Nội dung văn bản OCR.
- Trích xuất highlight các đoạn văn bản khớp từ khóa.
- Ghi lịch sử truy vấn vào bảng `search_history` trong PostgreSQL.
"""
import math
import re
import time
import unicodedata
from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from loguru import logger
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.core.dependencies import get_current_user_optional
from app.core.elasticsearch import INDEX_NAME, get_es_client
from app.models.document_categories import DocumentCategory
from app.models.document_metadata import DocumentMetadata
from app.models.documents import Document
from app.models.ocr_results import OCRResult
from app.models.search_history import SearchHistory
from app.models.users import User
from app.schemas.search import SearchHit, SearchResponse

router = APIRouter(prefix="/search", tags=["search"])


def _strip_accents(text: str) -> str:
    """Chuyển đổi chuỗi tiếng Việt có dấu sang không dấu."""
    if not text:
        return ""
    text = text.replace("đ", "d").replace("Đ", "D")
    normalized = unicodedata.normalize("NFD", text)
    return "".join(c for c in normalized if unicodedata.category(c) != "Mn").lower()


def _extract_highlight_snippet(content: str, query: str, max_length: int = 200) -> tuple[str, list[str]]:
    """Tạo đoạn trích kèm thẻ <em> highlight cho từ khóa."""
    if not content or not query:
        return (content[:max_length] + "..." if content and len(content) > max_length else content or "", [])

    words = [w.strip() for w in query.split() if len(w.strip()) > 1]
    if not words:
        words = [query.strip()]

    # Tìm vị trí xuất hiện đầu tiên của từ khóa
    ascii_content = _strip_accents(content)
    first_idx = -1
    for word in words:
        idx = ascii_content.find(_strip_accents(word))
        if idx != -1 and (first_idx == -1 or idx < first_idx):
            first_idx = idx

    if first_idx == -1:
        snippet = content[:max_length] + ("..." if len(content) > max_length else "")
        return snippet, []

    start = max(0, first_idx - 60)
    end = min(len(content), start + max_length)
    raw_snippet = ("..." if start > 0 else "") + content[start:end] + ("..." if end < len(content) else "")

    # Đánh dấu highlight
    highlighted = raw_snippet
    matched_fragments = []
    for word in words:
        pattern = re.compile(re.escape(word), re.IGNORECASE)
        highlighted = pattern.sub(r"<em>\g<0></em>", highlighted)
        matched_fragments.append(word)

    return highlighted, matched_fragments


@router.get(
    "",
    response_model=SearchResponse,
    summary="Tìm kiếm toàn văn tài liệu trên Elasticsearch & PostgreSQL Fallback",
)
async def search_documents(
    q: str = Query(..., min_length=1, description="Từ khóa tìm kiếm (tiếng Việt có dấu hoặc không dấu)"),
    category_code: str | None = Query(None, description="Lọc theo mã danh mục (vd: DON_NGHI_HOC)"),
    ocr_status: str | None = Query(None, description="Lọc theo trạng thái OCR (vd: DONE, APPROVED)"),
    date_from: str | None = Query(None, description="Ngày tạo từ (định dạng YYYY-MM-DD)"),
    date_to: str | None = Query(None, description="Ngày tạo đến (định dạng YYYY-MM-DD)"),
    fuzzy: bool = Query(True, description="Bật tìm kiếm mờ (Fuzzy matching) để bù đắp sai sót OCR / chính tả"),
    page: int = Query(1, ge=1, description="Số trang (bắt đầu từ 1)"),
    page_size: int = Query(10, ge=1, le=100, description="Số kết quả mỗi trang"),
    current_user: User | None = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_db),
) -> SearchResponse:
    """
    Tìm kiếm toàn văn tài liệu với:
    - Phân quyền RBAC: STUDENT/Vãng lai chỉ tìm hồ sơ của mình hoặc đã APPROVED; STAFF/ADMIN tìm toàn bộ.
    - Đa trường: tiêu đề, nội dung OCR, tên sinh viên, MSSV, số hiệu công văn.
    - Tìm tiếng Việt có dấu và không dấu thông minh.
    - Fallback tự động sang PostgreSQL khi Elasticsearch rỗng hoặc chưa sync.
    """
    t0 = time.monotonic()
    query_str = q.strip()
    from_offset = (page - 1) * page_size
    role_name = current_user.role.name if current_user and current_user.role else "STUDENT"

    results: list[SearchHit] = []
    total_hits = 0
    used_es = False

    # ── 1. Thử Tìm kiếm trên Elasticsearch ────────────────────────────────────
    try:
        es = get_es_client()
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
            "category_name^1.5",
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

        filter_clause: list[dict[str, Any]] = [
            {"term": {"is_deleted": False}}
        ]

        if role_name == "STUDENT":
            user_id_str = str(current_user.id) if current_user else ""
            filter_clause.append({
                "bool": {
                    "should": [
                        {"term": {"uploaded_by": user_id_str}} if user_id_str else {"term": {"ocr_status": "APPROVED"}},
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

        es_res = await es.search(index=INDEX_NAME, body=body)
        total_hits = es_res["hits"]["total"]["value"]
        hits_raw = es_res["hits"]["hits"]

        if total_hits > 0:
            used_es = True
            for hit in hits_raw:
                source = hit["_source"]
                highlights = hit.get("highlight", {})

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
    except Exception as exc:
        logger.warning("Elasticsearch query notice (falling back to DB search): {err}", err=str(exc))
        total_hits = 0
        results = []

    # ── 2. Fallback Tìm kiếm trên PostgreSQL nếu ES không có kết quả ───────────
    if total_hits == 0 or len(results) == 0:
        logger.info("Executing PostgreSQL fallback search for query: '{q}'", q=query_str)
        q_ascii = _strip_accents(query_str)
        search_pattern = f"%{query_str}%"

        stmt = (
            select(Document)
            .where(Document.is_deleted == False)
            .options(
                selectinload(Document.uploader),
                selectinload(Document.category),
                selectinload(Document.ocr_results),
                selectinload(Document.metadata_),
            )
        )

        # RBAC Filter
        if role_name == "STUDENT":
            if current_user:
                stmt = stmt.where(
                    (Document.uploaded_by == current_user.id) |
                    (Document.uploaded_by == None) |
                    (Document.ocr_status == "APPROVED")
                )
            else:
                stmt = stmt.where(Document.ocr_status == "APPROVED")

        if category_code:
            stmt = stmt.join(Document.category).where(DocumentCategory.code == category_code)
        if ocr_status:
            stmt = stmt.where(Document.ocr_status == ocr_status.upper())
        if date_from:
            stmt = stmt.where(Document.created_at >= date_from)
        if date_to:
            stmt = stmt.where(Document.created_at <= f"{date_to} 23:59:59")

        # Lấy tất cả tài liệu khả dụng để đối soát toàn văn & không dấu
        res_db = await db.execute(stmt)
        all_docs = res_db.scalars().all()

        matched_items: list[tuple[float, Document, str | None, dict[str, list[str]]]] = []

        query_terms = [t.strip().lower() for t in query_str.split() if t.strip()]
        query_terms_ascii = [t.strip().lower() for t in q_ascii.split() if t.strip()]

        for doc in all_docs:
            ocr_text = ""
            for ocr in doc.ocr_results:
                if ocr.is_latest:
                    ocr_text = ocr.corrected_text or ocr.raw_text or ""
                    break
            if not ocr_text and doc.ocr_results:
                ocr_text = doc.ocr_results[0].corrected_text or doc.ocr_results[0].raw_text or ""

            st_name = (doc.metadata_.student_name if doc.metadata_ and doc.metadata_.student_name else (doc.uploader.full_name if doc.uploader else "")) or ""
            st_id = (doc.metadata_.student_id if doc.metadata_ and doc.metadata_.student_id else (doc.uploader.mssv if doc.uploader else "")) or ""
            doc_num = (doc.metadata_.document_number if doc.metadata_ else "") or ""
            cat_name = doc.category.name if doc.category else ""
            title = doc.title or ""

            full_searchable = f"{title} {st_name} {st_id} {doc_num} {cat_name} {ocr_text}"
            full_searchable_ascii = _strip_accents(full_searchable)

            # Tính điểm liên quan BM25 giả lập
            score = 0.0
            highlights: dict[str, list[str]] = {}

            # Kiểm tra khớp chính xác tiêu đề
            if query_str.lower() in title.lower() or q_ascii in _strip_accents(title):
                score += 5.0
                highlights["title"] = [title]
            
            # Kiểm tra khớp MSSV
            if st_id and (query_str.lower() in st_id.lower() or q_ascii in st_id.lower()):
                score += 6.0
                highlights["student_id"] = [st_id]

            # Kiểm tra khớp Tên sinh viên
            if st_name and (query_str.lower() in st_name.lower() or q_ascii in _strip_accents(st_name)):
                score += 4.5
                highlights["student_name"] = [st_name]

            # Kiểm tra khớp Số hiệu / Danh mục
            if doc_num and query_str.lower() in doc_num.lower():
                score += 3.0
            if cat_name and (query_str.lower() in cat_name.lower() or q_ascii in _strip_accents(cat_name)):
                score += 2.0

            # Kiểm tra khớp nội dung OCR
            if ocr_text:
                if query_str.lower() in ocr_text.lower() or q_ascii in _strip_accents(ocr_text):
                    score += 3.5
                else:
                    # Kiểm tra khớp từng từ
                    term_match_count = sum(1 for term in query_terms_ascii if term in full_searchable_ascii)
                    if term_match_count > 0:
                        score += (term_match_count / max(len(query_terms_ascii), 1)) * 2.0

            if score > 0:
                snippet, _ = _extract_highlight_snippet(ocr_text or title, query_str)
                matched_items.append((score, doc, snippet, highlights))

        # Sắp xếp theo score giảm dần
        matched_items.sort(key=lambda x: x[0], reverse=True)
        total_hits = len(matched_items)

        # Cắt phân trang
        paged_items = matched_items[from_offset:from_offset + page_size]

        for score, doc, snippet, hls in paged_items:
            confidence = None
            for ocr in doc.ocr_results:
                if ocr.is_latest and ocr.confidence_score is not None:
                    confidence = float(ocr.confidence_score)
                    break

            st_name = (doc.metadata_.student_name if doc.metadata_ and doc.metadata_.student_name else (doc.uploader.full_name if doc.uploader else None))
            st_id = (doc.metadata_.student_id if doc.metadata_ and doc.metadata_.student_id else (doc.uploader.mssv if doc.uploader else None))

            results.append(
                SearchHit(
                    document_id=doc.id,
                    title=doc.title,
                    content_snippet=snippet,
                    category_code=doc.category.code if doc.category else None,
                    category_name=doc.category.name if doc.category else None,
                    student_id=st_id,
                    student_name=st_name,
                    document_date=doc.metadata_.document_date.isoformat() if doc.metadata_ and doc.metadata_.document_date else None,
                    document_number=doc.metadata_.document_number if doc.metadata_ else None,
                    ocr_status=doc.ocr_status,
                    ocr_confidence=confidence,
                    score=round(score, 3),
                    highlights=hls,
                    created_at=doc.created_at,
                )
            )

    total_pages = math.ceil(total_hits / page_size) if total_hits > 0 else 0
    took_ms = int((time.monotonic() - t0) * 1000)

    # ── 3. Ghi Lịch Sử Tìm Kiếm vào PostgreSQL ─────────────────────────────────
    if current_user:
        try:
            filters_dict = {
                "category_code": category_code,
                "ocr_status": ocr_status,
                "date_from": date_from,
                "date_to": date_to,
                "fuzzy": fuzzy,
                "engine": "elasticsearch" if used_es else "postgresql_fallback",
            }
            active_filters = {k: v for k, v in filters_dict.items() if v is not None}

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

