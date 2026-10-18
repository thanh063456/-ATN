"""
backend/app/services/search_index_service.py — Elasticsearch Indexing Service

QUAN TRỌNG (theo .ai/AGENTS.md):
  - Backend chủ động index dữ liệu sang Elasticsearch sau khi OCR hoàn thành hoặc khi có chỉnh sửa.
  - PostgreSQL KHÔNG tự động trigger đẩy dữ liệu sang ES.
  - Elasticsearch không phải bản sao tức thời của PostgreSQL, mà là Search Engine chuyên dụng.
"""
from datetime import datetime
from typing import Any
from uuid import UUID

try:
    from loguru import logger
except ImportError:
    import logging
    logger = logging.getLogger("search_index_service")
logger: Any = logger

from app.core.elasticsearch import INDEX_NAME, get_es_client, is_es_available
from app.core.exceptions import SearchIndexException
from app.services.embedding_service import embedding_service


class SearchIndexService:
    """Service chịu trách nhiệm index, update, soft-delete dữ liệu trong Elasticsearch."""

    def __init__(self) -> None:
        self.index_name = INDEX_NAME

    async def index_document(
        self,
        document_id: UUID | str,
        title: str,
        content: str,
        category_code: str | None = None,
        category_name: str | None = None,
        student_id: str | None = None,
        student_name: str | None = None,
        document_date: str | None = None,
        document_number: str | None = None,
        uploaded_by: UUID | str | None = None,
        ocr_status: str = "DONE",
        ocr_confidence: float | None = None,
        tags: list[str] | None = None,
        priority_score: int | None = None,
        metadata_extra: dict | None = None,
        is_deleted: bool = False,
        created_at: datetime | None = None,
        updated_at: datetime | None = None,
    ) -> dict | None:
        """
        Index hoặc update toàn bộ document vào Elasticsearch.
        Được gọi bởi Backend sau khi OCR hoàn tất và lưu vào PostgreSQL.
        """
        if not is_es_available():
            logger.debug(f"Elasticsearch is offline, skipping indexing for doc {document_id}")
            return None
        es = get_es_client()
        doc_id_str = str(document_id)
        now_iso = datetime.now().isoformat()
        safe_title = title or ""
        safe_content = content or ""
        vec = await embedding_service.get_embedding(f"{safe_title} {safe_content[:400]}")

        body = {
            "document_id": doc_id_str,
            "title": title,
            "content": content,
            "category_code": category_code,
            "category_name": category_name,
            "student_id": student_id,
            "student_name": student_name,
            "document_date": document_date,
            "document_number": document_number,
            "uploaded_by": str(uploaded_by) if uploaded_by else None,
            "ocr_status": ocr_status,
            "ocr_confidence": ocr_confidence,
            "tags": tags or [],
            "priority_score": priority_score,
            "metadata_extra": metadata_extra or {},
            "title_suggest": title,
            "content_vector": vec,
            "is_deleted": is_deleted,
            "created_at": created_at.isoformat() if created_at else now_iso,
            "updated_at": updated_at.isoformat() if updated_at else now_iso,
        }

        try:
            response = await es.index(
                index=self.index_name,
                id=doc_id_str,
                document=body,
                refresh="wait_for",  # Đảm bảo có thể search thấy ngay
            )
            logger.info(f"Indexed document in Elasticsearch: id={doc_id_str}, result={response.get('result')}")
            return response
        except Exception as exc:
            logger.error(f"Failed to index document {doc_id_str} in Elasticsearch: {exc}")
            raise SearchIndexException(f"Lỗi khi index tài liệu {doc_id_str} vào Elasticsearch: {str(exc)}") from exc

    async def update_document_status(
        self,
        document_id: UUID | str,
        ocr_status: str,
        updated_at: datetime | None = None,
    ) -> None:
        """Cập nhật trạng thái duyệt hồ sơ (ocr_status) mà không ghi đè mất nội dung OCR đã index."""
        if not is_es_available():
            return
        es = get_es_client()
        doc_id_str = str(document_id)
        now_iso = (updated_at or datetime.now()).isoformat()

        try:
            await es.update(
                index=self.index_name,
                id=doc_id_str,
                doc={
                    "ocr_status": ocr_status.upper(),
                    "updated_at": now_iso,
                },
                doc_as_upsert=True,
                refresh="wait_for",
            )
            logger.info(f"Updated status in ES for {doc_id_str} to {ocr_status}")
        except Exception as exc:
            logger.warning(f"Failed to update status in ES for {doc_id_str}: {exc}")

    async def update_corrected_text(
        self,
        document_id: UUID | str,
        corrected_text: str,
        student_id: str | None = None,
        student_name: str | None = None,
        document_date: str | None = None,
        metadata_extra: dict | None = None,
    ) -> None:
        """Cập nhật nội dung sau khi người dùng sửa lỗi OCR kèm theo metadata trích xuất lại."""
        if not is_es_available():
            return
        es = get_es_client()
        doc_id_str = str(document_id)

        patch_doc: dict = {
            "content": corrected_text,
            "content_corrected": corrected_text,
            "updated_at": datetime.now().isoformat(),
        }
        if student_id:
            patch_doc["student_id"] = student_id
        if student_name:
            patch_doc["student_name"] = student_name
        if document_date:
            patch_doc["document_date"] = document_date
        if metadata_extra:
            patch_doc["metadata_extra"] = metadata_extra

        # Cập nhật lại vector ngữ nghĩa sau khi sửa lỗi chính tả
        try:
            vec = await embedding_service.get_embedding(corrected_text[:400])
            patch_doc["content_vector"] = vec
        except Exception as e_vec:
            logger.debug(f"Failed to calculate updated embedding vector: {e_vec}")

        try:
            await es.update(
                index=self.index_name,
                id=doc_id_str,
                doc=patch_doc,
                doc_as_upsert=True,
                refresh="wait_for",
            )
            logger.info(f"Updated corrected text and metadata in ES: id={doc_id_str}")
        except Exception as exc:
            logger.error(f"Failed to update corrected text in ES for {doc_id_str}: {exc}")

    async def update_metadata_and_tags(
        self,
        document_id: UUID | str,
        student_id: str | None = None,
        student_name: str | None = None,
        document_date: str | None = None,
        document_number: str | None = None,
        tags: list[str] | None = None,
        priority_score: int | None = None,
        metadata_extra: dict | None = None,
    ) -> None:
        """Đồng bộ metadata và thẻ nhãn (tags) sang Elasticsearch sau khi trích xuất hoặc chỉnh sửa."""
        if not is_es_available():
            return
        es = get_es_client()
        doc_id_str = str(document_id)

        patch_doc: dict = {"updated_at": datetime.now().isoformat()}
        if student_id is not None:
            patch_doc["student_id"] = student_id
        if student_name is not None:
            patch_doc["student_name"] = student_name
        if document_date is not None:
            patch_doc["document_date"] = document_date
        if document_number is not None:
            patch_doc["document_number"] = document_number
        if tags is not None:
            patch_doc["tags"] = tags
        if priority_score is not None:
            patch_doc["priority_score"] = priority_score
        if metadata_extra is not None:
            patch_doc["metadata_extra"] = metadata_extra

        try:
            await es.update(
                index=self.index_name,
                id=doc_id_str,
                doc=patch_doc,
                doc_as_upsert=True,
                refresh="wait_for",
            )
            logger.info(f"Synced metadata and tags in ES for doc {doc_id_str}")
        except Exception as exc:
            logger.warning(f"Failed to sync metadata/tags in ES for {doc_id_str}: {exc}")

    async def soft_delete_document(self, document_id: UUID | str) -> None:
        """Đánh dấu xóa mềm trong Elasticsearch (is_deleted = True)."""
        if not is_es_available():
            return
        es = get_es_client()
        doc_id_str = str(document_id)

        try:
            await es.update(
                index=self.index_name,
                id=doc_id_str,
                doc={"is_deleted": True, "updated_at": datetime.now().isoformat()},
                doc_as_upsert=True,
                refresh="wait_for",
            )
            logger.info(f"Soft deleted document in ES: id={doc_id_str}")
        except Exception as exc:
            logger.warning(f"Failed to soft delete in ES for {doc_id_str}: {exc}")

    async def hard_delete_document(self, document_id: UUID | str) -> None:
        """Xóa vĩnh viễn document khỏi Elasticsearch."""
        if not is_es_available():
            return
        es = get_es_client()
        doc_id_str = str(document_id)

        try:
            await es.delete(index=self.index_name, id=doc_id_str, refresh="wait_for")
            logger.info(f"Hard deleted document from ES: id={doc_id_str}")
        except Exception as exc:
            logger.warning(f"Failed to hard delete from ES for {doc_id_str}: {exc}")


# Singleton instance
search_index_service = SearchIndexService()
