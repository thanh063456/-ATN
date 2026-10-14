"""
backend/tests/test_search.py — Elasticsearch Search API Tests

Tuân thủ AAA Pattern (Arrange - Act - Assert).
"""
import pytest
import httpx


@pytest.mark.asyncio
async def test_search_vietnamese_query(async_client: httpx.AsyncClient):
    """Kiểm tra tìm kiếm toàn văn tiếng Việt có dấu và không dấu."""
    # ── Arrange ───────────────────────────────────────────────────────────
    query = "học phí"

    # ── Act ───────────────────────────────────────────────────────────────
    response = await async_client.get("/api/v1/search", params={"q": query, "fuzzy": True})

    # ── Assert ────────────────────────────────────────────────────────────
    assert response.status_code == 200
    data = response.json()
    assert "total_hits" in data
    assert "results" in data
    assert data["query"] == query
    assert data["took_ms"] >= 0


@pytest.mark.asyncio
async def test_search_unaccented_query(async_client: httpx.AsyncClient):
    """Kiểm tra tìm kiếm không dấu (asciifolding: 'hoc phi' -> 'học phí')."""
    # ── Arrange ───────────────────────────────────────────────────────────
    query = "hoc phi"

    # ── Act ───────────────────────────────────────────────────────────────
    response = await async_client.get("/api/v1/search", params={"q": query})

    # ── Assert ────────────────────────────────────────────────────────────
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data["results"], list)


@pytest.mark.asyncio
async def test_search_with_facets(async_client: httpx.AsyncClient):
    """Kiểm tra phản hồi tìm kiếm trả về đầy đủ cấu trúc Faceted Aggregations."""
    # ── Arrange ───────────────────────────────────────────────────────────
    query = "học"

    # ── Act ───────────────────────────────────────────────────────────────
    response = await async_client.get("/api/v1/search", params={"q": query})

    # ── Assert ────────────────────────────────────────────────────────────
    assert response.status_code == 200
    data = response.json()
    assert "facets" in data
    facets = data["facets"]
    assert "categories" in facets
    assert "statuses" in facets
    assert "tags" in facets
    assert "years" in facets


@pytest.mark.asyncio
async def test_search_suggest_endpoint(async_client: httpx.AsyncClient):
    """Kiểm tra endpoint gợi ý từ khóa thời gian thực /search/suggest."""
    # ── Arrange ───────────────────────────────────────────────────────────
    prefix = "don"

    # ── Act ───────────────────────────────────────────────────────────────
    response = await async_client.get("/api/v1/search/suggest", params={"q": prefix, "limit": 5})

    # ── Assert ────────────────────────────────────────────────────────────
    assert response.status_code == 200
    data = response.json()
    assert data["query"] == prefix
    assert "suggestions" in data
    assert isinstance(data["suggestions"], list)


@pytest.mark.asyncio
async def test_search_hybrid_mode(async_client: httpx.AsyncClient):
    """Kiểm tra chế độ tìm kiếm kết hợp Hybrid Search (BM25 + kNN Dense Vector)."""
    # ── Arrange ───────────────────────────────────────────────────────────
    query = "miễn giảm học phí đối tượng chính sách"

    # ── Act ───────────────────────────────────────────────────────────────
    response = await async_client.get("/api/v1/search", params={"q": query, "hybrid": True})

    # ── Assert ────────────────────────────────────────────────────────────
    assert response.status_code == 200
    data = response.json()
    assert "results" in data
    assert data["took_ms"] >= 0


@pytest.mark.asyncio
async def test_search_sort_by(async_client: httpx.AsyncClient):
    """Kiểm tra tìm kiếm với tham số sắp xếp (newest, oldest, relevance)."""
    # ── Arrange ───────────────────────────────────────────────────────────
    query = "học"

    # ── Act & Assert (Newest) ─────────────────────────────────────────────
    res_newest = await async_client.get("/api/v1/search", params={"q": query, "sort_by": "newest"})
    assert res_newest.status_code == 200
    assert "results" in res_newest.json()

    # ── Act & Assert (Oldest) ─────────────────────────────────────────────
    res_oldest = await async_client.get("/api/v1/search", params={"q": query, "sort_by": "oldest"})
    assert res_oldest.status_code == 200
    assert "results" in res_oldest.json()


@pytest.mark.asyncio
async def test_search_trending_keywords(async_client: httpx.AsyncClient):
    """Kiểm tra endpoint top từ khóa phổ biến /search/trending."""
    # ── Act ───────────────────────────────────────────────────────────────
    response = await async_client.get("/api/v1/search/trending", params={"limit": 5})

    # ── Assert ────────────────────────────────────────────────────────────
    assert response.status_code == 200
    data = response.json()
    assert "trending" in data
    assert isinstance(data["trending"], list)
    if data["trending"]:
        item = data["trending"][0]
        assert "keyword" in item
        assert "count" in item


@pytest.mark.asyncio
async def test_search_stats_endpoint_requires_auth(async_client: httpx.AsyncClient):
    """Kiểm tra endpoint /search/stats yêu cầu phân quyền STAFF/ADMIN."""
    # ── Act ───────────────────────────────────────────────────────────────
    response = await async_client.get("/api/v1/search/stats")

    # ── Assert ────────────────────────────────────────────────────────────
    assert response.status_code in (401, 403)


@pytest.mark.asyncio
async def test_search_with_quick_time_range(async_client: httpx.AsyncClient):
    """Kiểm tra tìm kiếm với bộ lọc mốc thời gian nhanh (7d, this_year)."""
    # ── Act ───────────────────────────────────────────────────────────────
    res_7d = await async_client.get("/api/v1/search", params={"q": "học", "time_range": "7d"})
    assert res_7d.status_code == 200
    assert "results" in res_7d.json()

    res_year = await async_client.get("/api/v1/search", params={"q": "học", "time_range": "this_year"})
    assert res_year.status_code == 200
    assert "results" in res_year.json()


@pytest.mark.asyncio
async def test_search_export_requires_auth(async_client: httpx.AsyncClient):
    """Kiểm tra endpoint xuất CSV /search/export yêu cầu phân quyền STAFF/ADMIN."""
    # ── Act ───────────────────────────────────────────────────────────────
    response = await async_client.get("/api/v1/search/export", params={"q": "học phí"})

    # ── Assert ────────────────────────────────────────────────────────────
    assert response.status_code in (401, 403)


@pytest.mark.asyncio
async def test_search_with_confidence_range(async_client: httpx.AsyncClient):
    """Kiểm tra tìm kiếm kết hợp bộ lọc kiểm toán OCR min_confidence và max_confidence."""
    # ── Act ───────────────────────────────────────────────────────────────
    res = await async_client.get(
        "/api/v1/search",
        params={"q": "học phí", "min_confidence": 0.5, "max_confidence": 0.99},
    )

    # ── Assert ────────────────────────────────────────────────────────────
    assert res.status_code == 200
    data = res.json()
    assert "results" in data
    assert isinstance(data["results"], list)


@pytest.mark.asyncio
async def test_search_similar_documents(async_client: httpx.AsyncClient, staff_token: str):
    """Kiểm tra tìm kiếm tài liệu tương đồng More Like This (MLT)."""
    # ── Arrange: Upload một tài liệu mẫu ─────────────────────────────────
    pdf_content = b"%PDF-1.4 Don xin mien giam hoc phi ky 1 nam hoc 2026"
    files = {"file": ("don_mghp_sample.pdf", pdf_content, "application/pdf")}
    headers = {"Authorization": f"Bearer {staff_token}"}
    up_res = await async_client.post("/api/v1/documents/upload", files=files, headers=headers)
    assert up_res.status_code in (200, 201, 202)
    doc_id = up_res.json()["id"]

    # ── Act: Gọi API /similar ─────────────────────────────────────────────
    sim_res = await async_client.get(f"/api/v1/search/documents/{doc_id}/similar", headers=headers)

    # ── Assert ────────────────────────────────────────────────────────────
    assert sim_res.status_code == 200
    sim_data = sim_res.json()
    assert "source_document_id" in sim_data
    assert "similar_documents" in sim_data
    assert isinstance(sim_data["similar_documents"], list)


@pytest.mark.asyncio
async def test_search_dashboard_analytics(async_client: httpx.AsyncClient, staff_token: str):
    """Kiểm tra API Dashboard Analytics trả về thống kê đa chiều."""
    # ── 1. Kiểm tra chặn người dùng chưa xác thực ──────────────────────────
    unauth_res = await async_client.get("/api/v1/search/analytics/dashboard")
    assert unauth_res.status_code in (401, 403)

    # ── 2. Kiểm tra truy xuất thành công với quyền STAFF ───────────────────
    headers = {"Authorization": f"Bearer {staff_token}"}
    auth_res = await async_client.get("/api/v1/search/analytics/dashboard", headers=headers)
    assert auth_res.status_code == 200
    data = auth_res.json()

    assert "total_documents" in data
    assert "timeline" in data
    assert "categories" in data
    assert "statuses" in data
    assert "confidence_stats" in data
    assert isinstance(data["timeline"], list)
    assert isinstance(data["categories"], list)
    assert isinstance(data["statuses"], list)
    assert "avg" in data["confidence_stats"]


@pytest.mark.asyncio
async def test_duplicate_check_endpoint(async_client: httpx.AsyncClient, staff_token: str):
    """Kiểm tra API phát hiện trùng lặp hồ sơ và nghi vấn gian lận (Duplicate Check)."""
    # ── 1. Upload một tài liệu mẫu ─────────────────────────────────────────
    pdf_content = b"%PDF-1.4 Don xin ho tro chi phi hoc tap sinh vien kho khan 2026"
    files = {"file": ("don_hotro_check.pdf", pdf_content, "application/pdf")}
    headers = {"Authorization": f"Bearer {staff_token}"}
    up_res = await async_client.post("/api/v1/documents/upload", files=files, headers=headers)
    assert up_res.status_code in (200, 201, 202)
    doc_id = up_res.json()["id"]

    # ── 2. Gọi API kiểm tra trùng lặp ──────────────────────────────────────
    dup_res = await async_client.get(f"/api/v1/search/documents/{doc_id}/duplicate-check", headers=headers)
    assert dup_res.status_code == 200
    data = dup_res.json()

    assert "is_suspect_duplicate" in data
    assert "risk_level" in data
    assert data["risk_level"] in ("SAFE", "WARNING", "CRITICAL")
    assert "max_similarity_score" in data
    assert "recommendation" in data
    assert "candidates" in data
    assert isinstance(data["candidates"], list)


@pytest.mark.asyncio
async def test_sla_summary_endpoint(async_client: httpx.AsyncClient, staff_token: str):
    """Kiểm tra API báo cáo tiến độ và hạn chót xử lý hồ sơ (SLA Tracking)."""
    # ── 1. Kiểm tra chặn truy cập khi chưa đăng nhập ──────────────────────
    unauth_res = await async_client.get("/api/v1/search/sla/summary")
    assert unauth_res.status_code in (401, 403)

    # ── 2. Kiểm tra truy xuất thành công với quyền STAFF ───────────────────
    headers = {"Authorization": f"Bearer {staff_token}"}
    sla_res = await async_client.get("/api/v1/search/sla/summary", headers=headers)
    assert sla_res.status_code == 200
    data = sla_res.json()

    assert "total_pending" in data
    assert "overdue_count" in data
    assert "expiring_soon_count" in data
    assert "on_track_count" in data
    assert "compliance_rate" in data
    assert "items" in data
    assert isinstance(data["items"], list)
    assert isinstance(data["compliance_rate"], (int, float))


@pytest.mark.asyncio
async def test_smart_search_alerts_lifecycle(async_client: httpx.AsyncClient, staff_token: str):
    """Kiểm tra vòng đời đăng ký thông báo thông minh (Smart Alert Subscription & Matching)."""
    headers = {"Authorization": f"Bearer {staff_token}"}

    # ── 1. Tạo subscription theo dõi từ khóa ──────────────────────────────
    payload = {
        "keyword": "Học bổng Hessen",
        "category": "HOC_BONG",
        "description": "Theo dõi học bổng du học CHLB Đức",
    }
    create_res = await async_client.post("/api/v1/search/alerts", json=payload, headers=headers)
    assert create_res.status_code == 201
    alert_data = create_res.json()
    assert alert_data["keyword"] == "Học bổng Hessen"
    alert_id = alert_data["id"]

    # ── 2. Lấy danh sách alert ─────────────────────────────────────────────
    list_res = await async_client.get("/api/v1/search/alerts", headers=headers)
    assert list_res.status_code == 200
    list_data = list_res.json()
    assert list_data["total"] >= 1
    assert any(a["id"] == alert_id for a in list_data["items"])

    # ── 3. So khớp tài liệu mới (Percolate matching) ───────────────────────
    match_res = await async_client.post(
        "/api/v1/search/alerts/match-new",
        params={"title": "Thông báo xét tuyển Học bổng Hessen năm học 2026", "content": "Chi tiết tiêu chuẩn xét tuyển..."},
        headers=headers,
    )
    assert match_res.status_code == 200
    match_data = match_res.json()
    assert match_data["matched_alerts_count"] >= 1
    assert "Học bổng Hessen" in match_data["matched_keywords"]

    # ── 4. Xóa subscription ────────────────────────────────────────────────
    del_res = await async_client.delete(f"/api/v1/search/alerts/{alert_id}", headers=headers)
    assert del_res.status_code == 204


@pytest.mark.asyncio
async def test_pii_masking_for_students(async_client: httpx.AsyncClient, student_token: str, staff_token: str):
    """Kiểm tra che mờ dữ liệu cá nhân nhạy cảm (PII Masking) theo Nghị định 13."""
    # ── 1. Upload tài liệu có chứa thông tin nhạy cảm ───────────────────────
    raw_content = b"%PDF-1.4 Ho so sinh vien Nguyen Van A, CCCD: 068199001234, SDT: 0987654321, email: nguyen.a@gmail.com"
    files = {"file": ("don_pii_sample.pdf", raw_content, "application/pdf")}
    staff_headers = {"Authorization": f"Bearer {staff_token}"}
    student_headers = {"Authorization": f"Bearer {student_token}"}

    up_res = await async_client.post("/api/v1/documents/upload", files=files, headers=staff_headers)
    assert up_res.status_code in (200, 201, 202)
    doc_id = up_res.json()["id"]

    # Duyệt để sinh viên thấy
    await async_client.post(f"/api/v1/documents/{doc_id}/approve", headers=staff_headers)

    # ── 2. Sinh viên tìm kiếm -> Phải được che mờ PII ──────────────────────
    s_res = await async_client.get("/api/v1/search?q=Nguyen", headers=student_headers)
    assert s_res.status_code == 200
    s_data = s_res.json()
    for hit in s_data["results"]:
        snippet = hit.get("content_snippet") or ""
        # Không được để lộ nguyên vẹn số CCCD hoặc SĐT
        assert "068199001234" not in snippet
        assert "0987654321" not in snippet

    # ── 3. Cán bộ tìm kiếm -> Xem được dữ liệu gốc để đối soát ─────────────
    c_res = await async_client.get("/api/v1/search?q=Nguyen", headers=staff_headers)
    assert c_res.status_code == 200


@pytest.mark.asyncio
async def test_student_profile_360_endpoint(async_client: httpx.AsyncClient, staff_token: str):
    """Kiểm tra API Hồ sơ Sinh viên 360 độ và dòng thời gian."""
    headers = {"Authorization": f"Bearer {staff_token}"}
    res = await async_client.get("/api/v1/search/student-profile/2210001", headers=headers)
    assert res.status_code == 200
    data = res.json()

    assert "student_id" in data
    assert data["student_id"] == "2210001"
    assert "total_documents" in data
    assert "approved_documents" in data
    assert "pending_documents" in data
    assert "timeline" in data
    assert isinstance(data["timeline"], list)
    assert "categories_breakdown" in data
    assert isinstance(data["categories_breakdown"], list)


@pytest.mark.asyncio
async def test_document_validity_endpoint(async_client: httpx.AsyncClient, staff_token: str):
    """Kiểm tra API cảnh báo hiệu lực văn bản và biểu mẫu thay thế."""
    # Upload 1 tài liệu
    pdf_content = b"%PDF-1.4 Bieu mau don xin xac nhan sinh vien mau cu nam 2023"
    files = {"file": ("don_xn_mau_cu.pdf", pdf_content, "application/pdf")}
    headers = {"Authorization": f"Bearer {staff_token}"}
    up_res = await async_client.post("/api/v1/documents/upload", files=files, headers=headers)
    assert up_res.status_code in (200, 201, 202)
    doc_id = up_res.json()["id"]

    val_res = await async_client.get(f"/api/v1/search/documents/{doc_id}/validity")
    assert val_res.status_code == 200
    data = val_res.json()

    assert "document_id" in data
    assert "is_effective" in data
    assert "status_label" in data
    assert isinstance(data["is_effective"], bool)


@pytest.mark.asyncio
async def test_trending_topics_endpoint(async_client: httpx.AsyncClient, staff_token: str):
    """Kiểm tra API phân tích điểm nóng dư luận sinh viên (Significant Terms)."""
    headers = {"Authorization": f"Bearer {staff_token}"}
    res = await async_client.get("/api/v1/search/analytics/trending-topics", headers=headers)
    assert res.status_code == 200
    data = res.json()

    assert "timeframe" in data
    assert "total_terms_analyzed" in data
    assert "trending_topics" in data
    assert isinstance(data["trending_topics"], list)
    assert len(data["trending_topics"]) > 0
    assert "term" in data["trending_topics"][0]
    assert "growth_rate" in data["trending_topics"][0]


@pytest.mark.asyncio
async def test_staff_performance_endpoint(async_client: httpx.AsyncClient, staff_token: str):
    """Kiểm tra API đánh giá hiệu suất xử lý hồ sơ của Cán bộ CTSV."""
    headers = {"Authorization": f"Bearer {staff_token}"}
    res = await async_client.get("/api/v1/search/analytics/staff-performance", headers=headers)
    assert res.status_code == 200
    data = res.json()

    assert "total_staff" in data
    assert "overall_avg_hours" in data
    assert "metrics" in data
    assert isinstance(data["metrics"], list)
    if data["metrics"]:
        first = data["metrics"][0]
        assert "staff_name" in first
        assert "total_processed" in first
        assert "performance_score" in first


@pytest.mark.asyncio
async def test_ir_evaluation_benchmark_endpoint(async_client: httpx.AsyncClient):
    """Kiểm tra API đánh giá thực nghiệm khoa học chất lượng tìm kiếm IR Benchmark."""
    # Test GET với max_queries=5 để chạy nhanh
    res = await async_client.get("/api/v1/search/evaluation/benchmark", params={"include_details": True, "max_queries": 5})
    assert res.status_code == 200
    data = res.json()

    assert "total_queries" in data
    assert data["total_queries"] > 0
    assert "precision_at_5" in data
    assert "precision_at_10" in data
    assert "recall_at_10" in data
    assert "mean_average_precision_map" in data
    assert "mean_reciprocal_rank_mrr" in data
    assert "negative_rejection_rate" in data
    assert "avg_latency_ms" in data
    assert "engine_evaluated" in data
    assert "query_details" in data
    assert len(data["query_details"]) > 0

    first_q = data["query_details"][0]
    assert "id" in first_q
    assert "query" in first_q
    assert "precision_at_5" in first_q
    assert "latency_ms" in first_q

    # Test POST endpoint
    post_res = await async_client.post("/api/v1/search/evaluation/benchmark", params={"max_queries": 2})
    assert post_res.status_code == 200


@pytest.mark.asyncio
async def test_document_verification_endpoint(async_client: httpx.AsyncClient):
    """Kiểm tra API xác thực chứng thư điện tử & chống làm giả QR / SHA-256."""
    # 1. Lấy một tài liệu thực tế từ hệ thống
    search_res = await async_client.get("/api/v1/search", params={"q": "sinh viên", "page_size": 1})
    assert search_res.status_code == 200
    search_data = search_res.json()

    if search_data.get("results"):
        valid_doc_id = search_data["results"][0]["document_id"]
        res = await async_client.get(f"/api/v1/search/verify/{valid_doc_id}")
        assert res.status_code == 200
        data = res.json()

        assert "is_valid" in data
        assert "status" in data
        assert "verification_code" in data
        assert "file_hash" in data
        assert len(data["file_hash"]) == 64  # SHA-256 hex string
        assert "tamper_check_passed" in data
        assert "issuing_authority" in data
        assert "Đại học Đà Lạt" in data["issuing_authority"]

    # 2. Kiểm tra với mã giả mạo không tồn tại
    fake_code = "CTSV-DLU-FAKE9999"
    res_fake = await async_client.get(f"/api/v1/search/verify/{fake_code}")
    assert res_fake.status_code == 200
    fake_data = res_fake.json()
    assert fake_data["is_valid"] is False
    assert fake_data["status"] == "NOT_FOUND"
    assert fake_data["tamper_check_passed"] is False


@pytest.mark.asyncio
async def test_ocr_error_tolerant_search_endpoint(async_client: httpx.AsyncClient):
    """Kiểm tra API tìm kiếm chịu lỗi nhận dạng OCR chữ viết tay & lỗi chính tả."""
    # Truy vấn có từ viết tắt đặc thù và nhầm lẫn OCR
    payload = {
        "query": "don xin hb kkht sv 2O21",
        "page": 1,
        "page_size": 5,
    }
    res = await async_client.post("/api/v1/search/ocr-tolerant", json=payload)
    assert res.status_code == 200
    data = res.json()

    assert "query" in data
    assert "normalized_query" in data
    assert "suggested_corrections" in data
    assert isinstance(data["suggested_corrections"], list)
    assert len(data["suggested_corrections"]) > 0

    # Phải phát hiện được từ viết tắt hb hoặc kkht hoặc nhầm lẫn 2O21 -> 2021
    reasons = [c["reason"] for c in data["suggested_corrections"]]
    assert any("học bổng" in r or "202" in r or "viết tắt" in r for r in reasons)
    assert "results" in data
    assert "total" in data


@pytest.mark.asyncio
async def test_spatial_highlight_locations_endpoint(async_client: httpx.AsyncClient):
    """Kiểm tra API trích xuất tọa độ Bounding Box cho Side-by-Side Live Editor."""
    # 1. Lấy một tài liệu có sẵn
    search_res = await async_client.get("/api/v1/search", params={"q": "sinh viên", "page_size": 1})
    assert search_res.status_code == 200
    search_data = search_res.json()

    if search_data.get("results"):
        doc_id = search_data["results"][0]["document_id"]
        res = await async_client.get(
            f"/api/v1/search/documents/{doc_id}/spatial-highlights",
            params={"q": "sinh viên"},
        )
        assert res.status_code == 200
        data = res.json()

        assert "document_id" in data
        assert "keyword" in data
        assert "total_occurrences" in data
        assert "highlights" in data
        assert isinstance(data["highlights"], list)

        if data["highlights"]:
            box_item = data["highlights"][0]
            assert "page" in box_item
            assert "box" in box_item
            assert len(box_item["box"]) == 4  # [ymin, xmin, ymax, xmax]
            assert "matched_text" in box_item

    # 2. Kiểm tra với tài liệu không tồn tại -> 404
    fake_uuid = "00000000-0000-0000-0000-000000000000"
    res_404 = await async_client.get(
        f"/api/v1/search/documents/{fake_uuid}/spatial-highlights",
        params={"q": "test"},
    )
    assert res_404.status_code == 404




