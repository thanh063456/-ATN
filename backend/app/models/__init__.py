"""backend/app/models/__init__.py — export tất cả models để Alembic autogenerate thấy."""
from app.models.roles import Role
from app.models.users import User
from app.models.document_categories import DocumentCategory
from app.models.documents import Document
from app.models.ocr_results import OCRResult
from app.models.document_metadata import DocumentMetadata
from app.models.processing_jobs import ProcessingJob
from app.models.search_history import SearchHistory
from app.models.audit_logs import AuditLog

__all__ = [
    "Role",
    "User",
    "DocumentCategory",
    "Document",
    "OCRResult",
    "DocumentMetadata",
    "ProcessingJob",
    "SearchHistory",
    "AuditLog",
]
