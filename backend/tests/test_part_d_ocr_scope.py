import pytest
from httpx import AsyncClient
from uuid import uuid4
from sqlalchemy import select
from app.core.database import AsyncSessionLocal
from app.models.documents import Document
from app.models.document_categories import DocumentCategory
from app.models.document_metadata import DocumentMetadata
from app.models.audit_logs import AuditLog
from app.models.users import User


@pytest.mark.asyncio
async def test_ocr_full_rbac(async_client: AsyncClient, student_token: str, staff_token: str):
    async with AsyncSessionLocal() as session:
        user = (await session.execute(select(User))).scalars().first()
        cat = (await session.execute(select(DocumentCategory))).scalars().first()
        doc_id = uuid4()
        doc = Document(
            id=doc_id,
            title="Tài liệu kiểm tra RBAC",
            original_filename="sample.pdf",
            minio_object_key=f"test/{doc_id}.pdf",
            file_type="pdf",
            file_size_bytes=1024,
            page_count=3,
            category_id=cat.id if cat else None,
            uploaded_by=user.id,
            ocr_status="DONE",
        )
        session.add(doc)
        meta = DocumentMetadata(document_id=doc_id, extra={"ocr_scope": "first_page", "pages_ocr": 1})
        session.add(meta)
        await session.commit()

    # 1. Student should get 403 Forbidden
    res_student = await async_client.post(
        f"/api/v1/documents/{doc_id}/ocr-full",
        headers={"Authorization": f"Bearer {student_token}"},
    )
    assert res_student.status_code == 403

    # 2. Staff should succeed (200 OK)
    res_staff = await async_client.post(
        f"/api/v1/documents/{doc_id}/ocr-full",
        headers={"Authorization": f"Bearer {staff_token}"},
    )
    assert res_staff.status_code == 200
    assert "PROCESSING" in res_staff.json()["status"]

    # 3. Check AuditLog entry for TRIGGER_OCR_FULL
    async with AsyncSessionLocal() as session:
        log = (
            await session.execute(
                select(AuditLog).where(
                    AuditLog.resource_id == doc_id, AuditLog.action == "TRIGGER_OCR_FULL"
                )
            )
        ).scalars().first()
        assert log is not None
        assert "Kích hoạt" in log.detail.get("message", "")


@pytest.mark.asyncio
async def test_ocr_full_status(async_client: AsyncClient, staff_token: str):
    doc_id = uuid4()
    async with AsyncSessionLocal() as session:
        user = (await session.execute(select(User))).scalars().first()
        cat = (await session.execute(select(DocumentCategory))).scalars().first()
        doc = Document(
            id=doc_id,
            title="Tài liệu kiểm tra status",
            original_filename="sample_status.pdf",
            minio_object_key=f"test/{doc_id}.pdf",
            file_type="pdf",
            file_size_bytes=1024,
            page_count=5,
            category_id=cat.id if cat else None,
            uploaded_by=user.id,
            ocr_status="DONE",
        )
        session.add(doc)
        meta = DocumentMetadata(document_id=doc_id, extra={"ocr_scope": "first_page", "pages_ocr": 1})
        session.add(meta)
        await session.commit()

    res = await async_client.get(
        f"/api/v1/documents/{doc_id}/ocr-full/status",
        headers={"Authorization": f"Bearer {staff_token}"},
    )
    assert res.status_code == 200
    data = res.json()
    assert data["ocr_scope"] == "first_page"
    assert data["pages_ocr"] == 1
    assert data["page_count"] == 5


@pytest.mark.asyncio
async def test_override_document_type(async_client: AsyncClient, student_token: str, staff_token: str):
    doc_id = uuid4()
    async with AsyncSessionLocal() as session:
        user = (await session.execute(select(User))).scalars().first()
        categories = (await session.execute(select(DocumentCategory))).scalars().all()
        cat1 = categories[0]
        cat2 = categories[1] if len(categories) > 1 else categories[0]
        doc = Document(
            id=doc_id,
            title="Tài liệu thử nghiệm override",
            original_filename="override.pdf",
            minio_object_key=f"test/{doc_id}.pdf",
            file_type="pdf",
            file_size_bytes=1024,
            page_count=2,
            category_id=cat1.id,
            uploaded_by=user.id,
            ocr_status="DONE",
        )
        session.add(doc)
        meta = DocumentMetadata(
            document_id=doc_id,
            extra={"ocr_scope": "first_page", "doc_type_source": "auto"},
        )
        session.add(meta)
        await session.commit()
        cat2_code = cat2.code

    # 1. Student should get 403 Forbidden
    res_student = await async_client.patch(
        f"/api/v1/documents/{doc_id}/type",
        json={"category_code": cat2_code},
        headers={"Authorization": f"Bearer {student_token}"},
    )
    assert res_student.status_code == 403

    # 2. Staff succeeds and returns "Sửa loại văn bản thành công"
    res_staff = await async_client.patch(
        f"/api/v1/documents/{doc_id}/type",
        json={"category_code": cat2_code},
        headers={"Authorization": f"Bearer {staff_token}"},
    )
    assert res_staff.status_code == 200
    assert "Sửa loại văn bản thành công" in res_staff.json()["message"]

    # 3. Verify doc_type_source is set to "manual" so auto-classification won't overwrite
    async with AsyncSessionLocal() as session:
        updated_doc = await session.get(Document, doc_id)
        assert updated_doc.category_id == cat2.id
        updated_meta = (
            await session.execute(
                select(DocumentMetadata).where(DocumentMetadata.document_id == doc_id)
            )
        ).scalars().first()
        assert updated_meta.extra.get("doc_type_source") == "manual"
        assert updated_meta.extra.get("source") == "manual"

        # 4. Verify audit log entry
        log = (
            await session.execute(
                select(AuditLog).where(
                    AuditLog.resource_id == doc_id, AuditLog.action == "OVERRIDE_TYPE"
                )
            )
        ).scalars().first()
        assert log is not None
        assert cat2_code in log.detail.get("new_type", "")
