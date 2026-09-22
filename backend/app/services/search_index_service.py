"""
backend/app/services/search_index_service.py — Elasticsearch Indexing Service

QUAN TRỌNG (theo .ai/AGENTS.md):
  - Backend chủ động index dữ liệu sang Elasticsearch sau khi OCR hoàn thành hoặc khi có chỉnh sửa.
  - PostgreSQL KHÔNG tự động trigger đẩy dữ liệu sang ES.
  - Elasticsearch không phải bản sao tức thời của PostgreSQL, mà là Search Engine chuyên dụng.
"""
from datetime import datetime
from uuid import UUID

from loguru import logger

from app.core.config import settings
from app.core.elasticsearch import INDEX_NAME, get_es_client, is_es_available
from app.core.exceptions import SearchIndexException


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
        is_deleted: bool = False,
        created_at: datetime | None = None,
        updated_at: datetime | None = None,
    ) -> dict | None:
        """
        Index hoặc update toàn bộ document vào Elasticsearch.
        Được gọi bởi Backend sau khi OCR hoàn tất và lưu vào PostgreSQL.
        """
        if not is_es_available():
            logger.debug("Elasticsearch is offline, skipping indexing for doc {id}", id=document_id)
            return None
        es = get_es_client()
        doc_id_str = str(document_id)
        now_iso = datetime.now().isoformat()

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
            logger.info("Indexed document in Elasticsearch: id={id}, result={res}",
                        id=doc_id_str, res=response.get("result"))
            return response
        except Exception as exc:
            logger.error("Failed to index document {id} in Elasticsearch: {err}", id=doc_id_str, err=str(exc))
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
                refresh="wait_for",
            )
            logger.info("Updated status in ES for {id} to {status}", id=doc_id_str, status=ocr_status)
        except Exception as exc:
            logger.warning("Failed to update status in ES for {id}: {err}", id=doc_id_str, err=str(exc))

    async def update_corrected_text(
        self,
        document_id: UUID | str,
        corrected_text: str,
    ) -> None:
        """Cập nhật nội dung sau khi người dùng sửa lỗi OCR."""
        if not is_es_available():
            return
        es = get_es_client()
        doc_id_str = str(document_id)

        try:
            await es.update(
                index=self.index_name,
                id=doc_id_str,
                doc={
                    "content": corrected_text,
                    "content_corrected": corrected_text,
                    "updated_at": datetime.now().isoformat(),
                },
                refresh="wait_for",
            )
            logger.info("Updated corrected text in ES: id={id}", id=doc_id_str)
        except Exception as exc:
            logger.error("Failed to update corrected text in ES for {id}: {err}", id=doc_id_str, err=str(exc))

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
                refresh="wait_for",
            )
            logger.info("Soft deleted document in ES: id={id}", id=doc_id_str)
        except Exception as exc:
            logger.warning("Failed to soft delete in ES for {id}: {err}", id=doc_id_str, err=str(exc))

    async def hard_delete_document(self, document_id: UUID | str) -> None:
        """Xóa vĩnh viễn document khỏi Elasticsearch."""
        es = get_es_client()
        doc_id_str = str(document_id)

        try:
            await es.delete(index=self.index_name, id=doc_id_str, refresh="wait_for")
            logger.info("Hard deleted document from ES: id={id}", id=doc_id_str)
        except Exception as exc:
            logger.warning("Failed to hard delete from ES for {id}: {err}", id=doc_id_str, err=str(exc))


# Singleton instance
search_index_service = SearchIndexService()
