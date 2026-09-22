"""
backend/app/routers/search.py — Full-Text Search API Endpoint

Cung cấp API tìm kiếm toàn văn, tìm kiếm mờ (fuzzy) và lọc đa chiều:
- Tìm kiếm trên Elasticsearch với bộ phân tích tiếng Việt (vietnamese_exact & vietnamese_ascii).
- Tự động Fallback tìm kiếm thông minh trên PostgreSQL nếu Elasticsearch chưa khởi động / chưa sync / không có kết quả.
- Lọc Stopwords và đối sánh cụm từ (n-grams) để tránh false positives (vd: tìm "miễn giảm học phí" không bị lẫn với "kế hoạch khám sức khỏe" chỉ vì có từ "học").
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
from app.core.elasticsearch import INDEX_NAME, get_es_client, is_es_available
from app.models.document_categories import DocumentCategory
from app.models.document_metadata import DocumentMetadata
from app.models.documents import Document
from app.models.ocr_results import OCRResult
from app.models.search_history import SearchHistory
from app.models.users import User
from app.schemas.search import SearchHit, SearchResponse

router = APIRouter(prefix="/search", tags=["search"])

GENERIC_STOPWORDS_ASCII = {
    "hoc", "truong", "dai", "viet", "nam", "ngay", "thang", "nam", "so",
    "cong", "hoa", "xa", "hoi", "chu", "nghia", "doc", "lap", "tu", "do",
    "hanh", "phuc", "va", "cua", "cho", "ve", "cac", "tai", "theo", "duoc",
    "co", "trong", "da", "la", "sinh", "vien", "bo", "phong", "to", "chuc",
    "thong", "bao", "van", "ban", "ve"
}


def _strip_accents(text: str) -> str:
    """Chuyển đổi chuỗi tiếng Việt có dấu sang không dấu."""
    if not text:
        return ""
    text = text.replace("đ", "d").replace("Đ", "D")
    normalized = unicodedata.normalize("NFD", text)
    return "".join(c for c in normalized if unicodedata.category(c) != "Mn").lower().strip()


def _extract_highlight_snippet(content: str, target_terms: list[str], max_length: int = 220) -> tuple[str, list[str]]:
    """Tạo đoạn trích kèm thẻ <em> highlight cho các từ khóa/cụm từ quan trọng."""
    if not content:
        return ("", [])

    if not target_terms:
        snippet = content[:max_length] + ("..." if len(content) > max_length else "")
        return (snippet, [])

    ascii_content = _strip_accents(content)
    first_idx = -1
    best_term = ""

    # Ưu tiên tìm các cụm từ dài trước
    sorted_terms = sorted(target_terms, key=len, reverse=True)
    for term in sorted_terms:
        term_ascii = _strip_accents(term)
        idx = ascii_content.find(term_ascii)
        if idx != -1:
            first_idx = idx
            best_term = term
            break

    if first_idx == -1:
        snippet = content[:max_length] + ("..." if len(content) > max_length else "")
        return (snippet, [])

    start = max(0, first_idx - 50)
    end = min(len(content), start + max_length)
    raw_snippet = ("..." if start > 0 else "") + content[start:end] + ("..." if end < len(content) else "")

    # Đánh dấu highlight
    highlighted = raw_snippet
    matched_fragments = []
    for term in sorted_terms:
        if len(term.strip()) <= 1:
            continue
        pattern = re.compile(re.escape(term.strip()), re.IGNORECASE)
        if pattern.search(highlighted):
            highlighted = pattern.sub(r"<em>\g<0></em>", highlighted)
            matched_fragments.append(term.strip())

    return (highlighted, matched_fragments)


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

    # ── 1. Thử Tìm kiếm trên Elasticsearch (Nếu có kết nối) ────────────────────
    if is_es_available():
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
            logger.warning("Elasticsearch search failed: {err}, falling back to DB", err=str(exc))
            total_hits = 0
            results = []

    # ── 2. Fallback Tìm kiếm trên PostgreSQL nếu ES chưa chạy hoặc rỗng ────────
    if total_hits == 0 or len(results) == 0:
        q_ascii = _strip_accents(query_str)
        raw_words = [w.strip() for w in query_str.split() if w.strip()]
        raw_words_ascii = [_strip_accents(w) for w in raw_words]

        # Trích xuất các cụm từ con (bi-grams, tri-grams)
        sub_phrases: list[str] = []
        if len(raw_words) >= 2:
            sub_phrases.append(query_str)
            for i in range(len(raw_words) - 1):
                sub_phrases.append(f"{raw_words[i]} {raw_words[i+1]}")

        # Lọc các từ khóa quan trọng (không phải stopword thông dụng)
        important_words_ascii = [w for w in raw_words_ascii if w not in GENERIC_STOPWORDS_ASCII]
        if not important_words_ascii:
            # Nếu toàn bộ từ khóa nằm trong stopwords (vd: người dùng tìm đúng chữ "kế hoạch"), dùng lại từ gốc
            important_words_ascii = raw_words_ascii

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

        res_db = await db.execute(stmt)
        all_docs = res_db.scalars().all()

        matched_items: list[tuple[float, Document, str | None, dict[str, list[str]]]] = []

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

            title_ascii = _strip_accents(title)
            st_name_ascii = _strip_accents(st_name)
            st_id_ascii = _strip_accents(st_id)
            ocr_text_ascii = _strip_accents(ocr_text)

            score = 0.0
            matched_terms_for_highlight: list[str] = []
            highlights: dict[str, list[str]] = {}

            # 1. Khớp nguyên cụm từ đầy đủ (Exact Full Phrase)
            if q_ascii in title_ascii:
                score += 15.0
                matched_terms_for_highlight.append(query_str)
                highlights["title"] = [title]
            elif q_ascii in ocr_text_ascii:
                score += 10.0
                matched_terms_for_highlight.append(query_str)

            # 2. Khớp MSSV hoặc Tên sinh viên chính xác
            if st_id and (q_ascii in st_id_ascii or st_id_ascii in q_ascii):
                score += 12.0
                matched_terms_for_highlight.append(st_id)
                highlights["student_id"] = [st_id]
            if st_name and (q_ascii in st_name_ascii or any(w in st_name_ascii for w in important_words_ascii if len(w) >= 3)):
                score += 8.0
                matched_terms_for_highlight.append(st_name)
                highlights["student_name"] = [st_name]

            # 3. Khớp các cụm từ con (sub-phrases)
            for phrase in sub_phrases:
                p_ascii = _strip_accents(phrase)
                if p_ascii in title_ascii:
                    score += 6.0
                    matched_terms_for_highlight.append(phrase)
                if p_ascii in ocr_text_ascii:
                    score += 4.5
                    matched_terms_for_highlight.append(phrase)

            # 4. Khớp các từ khóa quan trọng (không phải stopword đơn lẻ)
            important_title_matches = sum(1 for w in important_words_ascii if w in title_ascii)
            important_ocr_matches = sum(1 for w in important_words_ascii if w in ocr_text_ascii)

            if important_title_matches > 0:
                score += important_title_matches * 3.0
                matched_terms_for_highlight.extend([w for w in raw_words if _strip_accents(w) in important_words_ascii])

            if important_ocr_matches >= len(important_words_ascii):
                # Khớp toàn bộ các từ quan trọng trong nội dung
                score += 5.0
                matched_terms_for_highlight.extend([w for w in raw_words if _strip_accents(w) in important_words_ascii])
            elif len(important_words_ascii) > 1 and important_ocr_matches >= 2:
                score += 3.0
                matched_terms_for_highlight.extend([w for w in raw_words if _strip_accents(w) in important_words_ascii])

            # ĐIỀU KIỆN QUYẾT ĐỊNH: Chỉ chấp nhận nếu có điểm khớp thực chất
            # (Loại bỏ triệt để trường hợp chỉ trùng 1 chữ stopword thông dụng như "học" hay "nam")
            has_genuine_match = (
                score >= 3.0 or
                (len(important_words_ascii) == 1 and important_ocr_matches >= 1)
            )

            if has_genuine_match and score > 0:
                target_terms = list(set(matched_terms_for_highlight)) if matched_terms_for_highlight else raw_words
                snippet, _ = _extract_highlight_snippet(ocr_text or title, target_terms)
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

