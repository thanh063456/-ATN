"""
backend/tests/test_rbac_security.py — Negative & RBAC Security Automated Tests

Kiểm thử xác minh các lỗ hổng bảo mật và phân quyền đã được khắc phục hoàn toàn:
1. Chống bypass mật khẩu (No backdoor fallback)
2. Chặn truy cập file gốc trái phép (File viewing RBAC)
3. Chặn tìm kiếm toàn văn khi chưa xác thực (Search RBAC)
4. Chặn quyền gọi tác vụ nặng / duyệt hồ sơ trái thẩm quyền (Reprocess & Approve RBAC)
5. Bảo vệ dữ liệu riêng tư trên cổng xác thực công khai (Privacy-Preserving Verification)
"""
import uuid
import pytest
import httpx
from app.core.security import verify_password, get_password_hash


def test_password_verify_no_backdoor_fallback():
    """Kiểm tra không còn backdoor password fallback khi hash bị lỗi/giả mạo."""
    # Hash sai định dạng hoặc không tồn tại
    assert verify_password("password123", "$2b$12$dummyinvalidhash") is False
    assert verify_password("admin123", "$2b$12$dummyinvalidhash") is False
    assert verify_password("random_pass", "") is False

    # Hash bcrypt thật hợp lệ
    valid_hash = get_password_hash("CorrectPassword@123")
    assert verify_password("CorrectPassword@123", valid_hash) is True
    assert verify_password("WrongPassword@123", valid_hash) is False


@pytest.mark.asyncio
async def test_unauthenticated_file_download_rejected(async_client: httpx.AsyncClient):
    """Kiểm tra xem file gốc không có Authorization header -> 401 Unauthorized."""
    random_doc_id = str(uuid.uuid4())
    response = await async_client.get(f"/api/v1/documents/{random_doc_id}/file")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_unauthenticated_search_rejected(async_client: httpx.AsyncClient):
    """Kiểm tra tìm kiếm /search không có token -> 401 Unauthorized."""
    response = await async_client.get("/api/v1/search?q=sinhvien")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_student_cannot_trigger_reprocess_ocr(async_client: httpx.AsyncClient, student_token: str):
    """Kiểm tra sinh viên (STUDENT) không thể kích hoạt lại OCR -> 403 Forbidden."""
    random_doc_id = str(uuid.uuid4())
    headers = {"Authorization": f"Bearer {student_token}"}
    response = await async_client.post(f"/api/v1/documents/{random_doc_id}/reprocess-ocr", headers=headers)
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_student_cannot_approve_document(async_client: httpx.AsyncClient, student_token: str):
    """Kiểm tra sinh viên (STUDENT) không thể tự phê duyệt hồ sơ -> 403 Forbidden."""
    random_doc_id = str(uuid.uuid4())
    headers = {"Authorization": f"Bearer {student_token}"}
    response = await async_client.patch(f"/api/v1/documents/{random_doc_id}/approve", headers=headers)
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_public_verify_endpoint_exists(async_client: httpx.AsyncClient):
    """Kiểm tra endpoint /verify/{id} hoạt động công khai không bắt login, trả 404 cho doc không tồn tại."""
    random_doc_id = str(uuid.uuid4())
    response = await async_client.get(f"/api/v1/verify/{random_doc_id}")
    assert response.status_code == 404
