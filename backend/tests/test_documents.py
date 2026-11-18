"""
backend/tests/test_documents.py — Documents Management & Approval Tests

Tuân thủ AAA Pattern (Arrange - Act - Assert).
"""

import httpx
import pytest


@pytest.mark.asyncio
async def test_upload_document_success(async_client: httpx.AsyncClient, staff_token: str):
    """Kiểm tra upload tài liệu PDF hợp lệ -> 202 Accepted + lưu MinIO."""
    # ── Arrange ───────────────────────────────────────────────────────────
    pdf_content = b"%PDF-1.4 Unit test document\nEm ten la: Tran Van An\nMSSV: 20221234"
    files = {"file": ("test_don_xin_hoc_bong.pdf", pdf_content, "application/pdf")}
    data = {"title": "Đơn xin học bổng - Trần Văn An"}
    headers = {"Authorization": f"Bearer {staff_token}"}

    # ── Act ───────────────────────────────────────────────────────────────
    response = await async_client.post("/api/v1/documents/upload", data=data, files=files, headers=headers)

    # ── Assert ────────────────────────────────────────────────────────────
    assert response.status_code == 202
    res_data = response.json()
    assert "id" in res_data
    assert res_data["title"] == "Đơn xin học bổng - Trần Văn An"
    assert res_data["ocr_status"] == "PENDING"
    assert "documents/" in res_data["minio_object_key"]


@pytest.mark.asyncio
async def test_upload_unsupported_file_type(async_client: httpx.AsyncClient, staff_token: str):
    """Kiểm tra từ chối upload định dạng file không hỗ trợ (.exe) -> 400 Bad Request."""
    # ── Arrange ───────────────────────────────────────────────────────────
    bad_content = b"MZ executable binary payload"
    files = {"file": ("malicious_program.exe", bad_content, "application/octet-stream")}
    data = {"title": "File không hợp lệ"}
    headers = {"Authorization": f"Bearer {staff_token}"}

    # ── Act ───────────────────────────────────────────────────────────────
    response = await async_client.post("/api/v1/documents/upload", data=data, files=files, headers=headers)

    # ── Assert ────────────────────────────────────────────────────────────
    assert response.status_code == 400
    assert "exe" in response.json()["detail"]


@pytest.mark.asyncio
async def test_approve_document(async_client: httpx.AsyncClient, staff_token: str):
    """Kiểm tra cán bộ CTSV phê duyệt hồ sơ -> trạng thái APPROVED."""
    # ── Arrange ───────────────────────────────────────────────────────────
    # 1. Tạo document trước
    pdf_content = b"%PDF-1.4 Test approval document"
    files = {"file": ("don_phe_duyet.pdf", pdf_content, "application/pdf")}
    headers = {"Authorization": f"Bearer {staff_token}"}
    up_res = await async_client.post(
        "/api/v1/documents/upload", data={"title": "Đơn cần phê duyệt"}, files=files, headers=headers
    )
    doc_id = up_res.json()["id"]

    # ── Act ───────────────────────────────────────────────────────────────
    app_res = await async_client.patch(f"/api/v1/documents/{doc_id}/approve", headers=headers)

    # ── Assert ────────────────────────────────────────────────────────────
    assert app_res.status_code == 200
    res_json = app_res.json()
    assert res_json["ocr_status"] == "APPROVED"
    assert "approval_info" in res_json
    if res_json["approval_info"]:
        assert res_json["approval_info"]["status"] == "APPROVED"
        assert res_json["approval_info"]["approver_role"] in ("ADMIN", "STAFF")


@pytest.mark.asyncio
async def test_get_document_notifications(async_client: httpx.AsyncClient, staff_token: str):
    """Kiểm tra API lấy danh sách thông báo xét duyệt hồ sơ."""
    headers = {"Authorization": f"Bearer {staff_token}"}
    response = await async_client.get("/api/v1/documents/notifications?limit=10", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert "total" in data
    assert "unread_count" in data
    assert isinstance(data["items"], list)
