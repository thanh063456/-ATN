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


# ==============================================================================
# TESTS CHO 5 TÍNH NĂNG ĐỀ XUẤT MỚI
# ==============================================================================

@pytest.mark.asyncio
async def test_faq_ask_endpoint(async_client: httpx.AsyncClient):
    """Kiểm tra Endpoint Hỏi đáp Quy chế CTSV bằng ngôn ngữ tự nhiên (NLP FAQ)."""
    # 1. Hỏi về học bổng và điểm F thể dục
    res1 = await async_client.get(
        "/api/v1/search/faq/ask",
        params={"q": "Bị điểm F môn thể dục có được xét học bổng không?"},
    )
    assert res1.status_code == 200
    data1 = res1.json()
    assert "matched_article" in data1
    assert "summary_answer" in data1
    assert "required_forms" in data1
    assert data1["confidence_score"] >= 0.8
    assert "688" in data1["matched_article"] or "Quy chế" in data1["regulation_title"]
    assert any("BM-01-HBKK" in f["form_code"] for f in data1["required_forms"])

    # 2. Hỏi về miễn giảm học phí hộ nghèo
    res2 = await async_client.get(
        "/api/v1/search/faq/ask",
        params={"q": "Hồ sơ miễn giảm học phí cho sinh viên hộ nghèo gồm giấy tờ gì?"},
    )
    assert res2.status_code == 200
    data2 = res2.json()
    assert "81/2021" in data2["matched_article"] or "học phí" in data2["regulation_title"]
    assert any("BM-02-MGHP" in f["form_code"] for f in data2["required_forms"])


@pytest.mark.asyncio
async def test_policy_auto_audit_endpoint(async_client: httpx.AsyncClient):
    """Kiểm tra Endpoint Thẩm định Hồ sơ Chính sách Tự động (Policy Auto-Audit)."""
    # 1. Tìm tài liệu có sẵn
    search_res = await async_client.get("/api/v1/search", params={"q": "sinh viên", "page_size": 1})
    assert search_res.status_code == 200
    hits = search_res.json().get("results", [])

    if hits:
        doc_id = hits[0]["document_id"]
        # Audit theo Nghị định 81
        res = await async_client.get(
            f"/api/v1/search/documents/{doc_id}/policy-audit",
            params={"policy_code": "NGHI_DINH_81"},
        )
        assert res.status_code == 200
        data = res.json()
        assert data["policy_code"] == "NGHI_DINH_81"
        assert data["status"] in ("ELIGIBLE", "INCOMPLETE", "INELIGIBLE")
        assert len(data["criteria_checks"]) >= 3
        assert "score" in data
        assert "recommendation" in data

        # Audit theo Học bổng KKHT
        res_hb = await async_client.get(
            f"/api/v1/search/documents/{doc_id}/policy-audit",
            params={"policy_code": "HOC_BONG_KKHT"},
        )
        assert res_hb.status_code == 200
        assert res_hb.json()["policy_code"] == "HOC_BONG_KKHT"

    # Kiểm tra 404
    fake_uuid = "00000000-0000-0000-0000-000000000000"
    res_404 = await async_client.get(f"/api/v1/search/documents/{fake_uuid}/policy-audit")
    assert res_404.status_code == 404


@pytest.mark.asyncio
async def test_cross_document_fraud_detection_endpoint(async_client: httpx.AsyncClient):
    """Kiểm tra Endpoint Phát hiện Xung đột & Gian lận Liên văn bản (Anti-Fraud)."""
    res = await async_client.get("/api/v1/search/fraud-detection/audit")
    assert res.status_code == 200
    data = res.json()
    assert "risk_level" in data
    assert data["risk_level"] in ("SAFE", "WARNING", "CRITICAL")
    assert "tamper_score" in data
    assert isinstance(data["detected_collisions"], list)
    assert "conclusion" in data
    assert "audited_at" in data


@pytest.mark.asyncio
async def test_structured_tables_query_endpoint(async_client: httpx.AsyncClient):
    """Kiểm tra Endpoint Tìm kiếm Bảng biểu Cấu trúc (Nested Table Search)."""
    # 1. Tìm theo điều kiện điểm GPA và điểm rèn luyện
    body = {
        "min_gpa": 3.2,
        "min_drl": 80,
        "page": 1,
        "page_size": 10,
    }
    res = await async_client.post("/api/v1/search/tables/query", json=body)
    assert res.status_code == 200
    data = res.json()
    assert "total_hits" in data
    assert "rows" in data
    assert isinstance(data["rows"], list)
    assert data["page"] == 1
    assert data["page_size"] == 10

    if data["rows"]:
        row = data["rows"][0]
        assert "mssv" in row
        assert "student_name" in row
        if row.get("gpa") is not None:
            assert row["gpa"] >= 3.2

    # 2. Tìm theo MSSV cụ thể
    body_mssv = {"student_id": "2112345"}
    res_mssv = await async_client.post("/api/v1/search/tables/query", json=body_mssv)
    assert res_mssv.status_code == 200
    data_mssv = res_mssv.json()
    assert "rows" in data_mssv


@pytest.mark.asyncio
async def test_pii_security_audit_summary_endpoint(async_client: httpx.AsyncClient):
    """Kiểm tra Endpoint Giám sát An toàn Thông tin PII & SIEM."""
    res = await async_client.get("/api/v1/search/security/pii-audit-summary", params={"window_minutes": 60})
    assert res.status_code == 200
    data = res.json()
    assert "total_pii_accesses" in data
    assert "unique_documents_accessed" in data
    assert "top_accessors" in data
    assert isinstance(data["top_accessors"], list)
    assert "anomalies" in data
    assert isinstance(data["anomalies"], list)
    assert "recent_accesses" in data
    assert isinstance(data["recent_accesses"], list)


@pytest.mark.asyncio
async def test_ctsv_percolate_routing_endpoint(async_client: httpx.AsyncClient):
    """Kiểm tra Endpoint Phân luồng hồ sơ tự động bằng Elasticsearch Percolator (Reverse Search)."""
    # 1. Lấy 1 tài liệu có sẵn trong hệ thống
    search_res = await async_client.get("/api/v1/search", params={"page_size": 1})
    assert search_res.status_code == 200
    search_data = search_res.json()

    if search_data.get("results"):
        valid_doc_id = search_data["results"][0]["document_id"]
        res = await async_client.get(f"/api/v1/search/documents/{valid_doc_id}/percolate-routing")
        assert res.status_code == 200
        data = res.json()

        assert "document_id" in data
        assert "document_title" in data
        assert "matched_rules_count" in data
        assert data["matched_rules_count"] >= 1
        assert "primary_route" in data
        assert "assigned_department" in data
        assert "priority" in data
        assert data["priority"] in ("URGENT", "HIGH", "NORMAL")
        assert "matched_policies" in data
        assert isinstance(data["matched_policies"], list)

        first_match = data["matched_policies"][0]
        assert "rule_id" in first_match
        assert "policy_name" in first_match
        assert "target_department" in first_match
        assert "routing_action" in first_match
        assert "required_checklist" in first_match
        assert isinstance(first_match["required_checklist"], list)

    # 2. Thử với document_id giả mạo -> 404
    fake_uuid = "00000000-0000-0000-0000-000000000000"
    res_404 = await async_client.get(f"/api/v1/search/documents/{fake_uuid}/percolate-routing")
    assert res_404.status_code == 404


@pytest.mark.asyncio
async def test_ctsv_breakdown_analytics_endpoint(async_client: httpx.AsyncClient):
    """Kiểm tra Endpoint Báo cáo Đa chiều CTSV Toàn trường Thời gian thực (Multi-level Aggregations)."""
    res = await async_client.get("/api/v1/search/analytics/ctsv-breakdown")
    assert res.status_code == 200
    data = res.json()

    assert "total_student_documents" in data
    assert "total_active_students" in data
    assert "total_budget_allocated" in data
    assert data["total_budget_allocated"] > 0
    assert "avg_processing_sla_days" in data
    assert "faculty_breakdown" in data
    assert isinstance(data["faculty_breakdown"], list)
    assert len(data["faculty_breakdown"]) > 0

    first_faculty = data["faculty_breakdown"][0]
    assert "faculty_code" in first_faculty
    assert "faculty_name" in first_faculty
    assert "total_applications" in first_faculty
    assert "approved_count" in first_faculty
    assert "budget_disbursed" in first_faculty

    assert "policy_distribution" in data
    assert isinstance(data["policy_distribution"], list)
    assert len(data["policy_distribution"]) > 0

    first_policy = data["policy_distribution"][0]
    assert "policy_code" in first_policy
    assert "policy_name" in first_policy
    assert "percentage" in first_policy

    assert "monthly_application_trend" in data
    assert isinstance(data["monthly_application_trend"], list)


@pytest.mark.asyncio
async def test_ocr_quality_distribution_and_review_queue(async_client: httpx.AsyncClient):
    """Kiểm tra Endpoint Thống kê Chất lượng OCR & Hàng đợi Hiệu đính Human-in-the-Loop."""
    # 1. Thống kê phân bổ chất lượng
    res_stats = await async_client.get("/api/v1/search/analytics/ocr-quality")
    assert res_stats.status_code == 200
    stats = res_stats.json()
    assert "total_scanned_documents" in stats
    assert "avg_confidence" in stats
    assert "excellent_count" in stats
    assert "review_needed_count" in stats
    assert "distribution" in stats
    assert isinstance(stats["distribution"], list)
    assert len(stats["distribution"]) == 4

    # 2. Hàng đợi hiệu đính
    res_queue = await async_client.get("/api/v1/search/ocr-quality/review-queue", params={"page_size": 5})
    assert res_queue.status_code == 200
    queue = res_queue.json()
    assert "total_items" in queue
    assert "items" in queue
    assert isinstance(queue["items"], list)
    if queue["items"]:
        first = queue["items"][0]
        assert "document_id" in first
        assert "ocr_confidence" in first
        assert "urgency" in first
        assert first["urgency"] in ("URGENT", "HIGH", "NORMAL")


@pytest.mark.asyncio
async def test_document_auto_tags_significant_text(async_client: httpx.AsyncClient):
    """Kiểm tra Endpoint Tự động gán nhãn thực thể chính sách bằng significant_text."""
    # Lấy 1 tài liệu có sẵn
    search_res = await async_client.get("/api/v1/search", params={"page_size": 1})
    assert search_res.status_code == 200
    sdata = search_res.json()

    doc_id = sdata["results"][0]["document_id"] if sdata.get("results") else "a69799ce-74f2-46b9-94d3-fe7f1f50b0aa"
    res = await async_client.post(f"/api/v1/search/documents/{doc_id}/auto-tags")
    assert res.status_code == 200
    data = res.json()
    assert "document_id" in data
    assert "document_title" in data
    assert "total_tags" in data
    assert data["total_tags"] >= 1
    assert "tags" in data
    assert isinstance(data["tags"], list)
    assert "suggested_policy_category" in data
    assert "extracted_entities" in data

    first_tag = data["tags"][0]
    assert "tag" in first_tag
    assert "category" in first_tag
    assert "significance_score" in first_tag
    assert "evidence_snippet" in first_tag


@pytest.mark.asyncio
async def test_geo_priority_area_verification(async_client: httpx.AsyncClient):
    """Kiểm tra Endpoint Thẩm định Địa lý Xã ĐBKK Khu vực III NĐ 81/2021."""
    # 1. Thẩm định địa chỉ thuộc Xã Đạ Chais, Huyện Lạc Dương (Khu vực III)
    req_zone_iii = {
        "address_raw": "Thôn Đạ Tro, Xã Đạ Chais, Huyện Lạc Dương, Tỉnh Lâm Đồng",
        "commune": "Đạ Chais",
        "district": "Lạc Dương",
        "province": "Lâm Đồng",
    }
    res_iii = await async_client.post("/api/v1/search/geo/verify-priority-area", json=req_zone_iii)
    assert res_iii.status_code == 200
    data_iii = res_iii.json()
    assert data_iii["is_priority_area"] is True
    assert data_iii["area_category"] == "KHU_VUC_III"
    assert data_iii["tuition_reduction_rate"] == 70
    assert data_iii["subsidy_amount_monthly"] == 1490000.0
    assert "distance_to_dlu_km" in data_iii
    assert data_iii["distance_to_dlu_km"] > 0
    assert "Nghị định 81/2021/NĐ-CP" in data_iii["legal_reference"]

    # 2. Thẩm định địa chỉ đô thị thông thường (Không thuộc diện)
    req_normal = {
        "address_raw": "Số 01 Phù Đổng Thiên Vương, Phường 8, TP Đà Lạt, Lâm Đồng",
        "commune": "Phường 8",
        "district": "Đà Lạt",
        "province": "Lâm Đồng",
    }
    res_norm = await async_client.post("/api/v1/search/geo/verify-priority-area", json=req_normal)
    assert res_norm.status_code == 200
    data_norm = res_norm.json()
    assert data_norm["is_priority_area"] is False
    assert data_norm["area_category"] == "KHONG_THUOC_DIEN"
    assert data_norm["tuition_reduction_rate"] == 0


@pytest.mark.asyncio
async def test_student_entity_graph_and_dropout_risk(async_client: httpx.AsyncClient):
    """Kiểm tra Endpoint Đồ thị Thực thể Sinh viên 360 & Cảnh báo Nguy cơ Thôi học."""
    # 1. Sinh viên bình thường
    res = await async_client.get("/api/v1/search/students/2112463/entity-graph")
    assert res.status_code == 200
    data = res.json()
    assert data["student_id"] == "2112463"
    assert "student_name" in data
    assert "faculty" in data
    assert "nodes" in data
    assert "edges" in data
    assert len(data["nodes"]) >= 4
    assert len(data["edges"]) >= 3
    assert "dropout_risk" in data
    assert data["dropout_risk"]["risk_level"] in ("SAFE", "LOW", "MEDIUM", "HIGH", "CRITICAL")
    assert "risk_score" in data["dropout_risk"]

    # 2. Sinh viên có cảnh báo học vụ (MSSV chứa "warn" hoặc "2020")
    res_warn = await async_client.get("/api/v1/search/students/2020999_warn/entity-graph")
    assert res_warn.status_code == 200
    data_warn = res_warn.json()
    assert data_warn["dropout_risk"]["risk_level"] == "HIGH"
    assert data_warn["dropout_risk"]["risk_score"] > 50


@pytest.mark.asyncio
async def test_document_audit_trail_and_diffs(async_client: httpx.AsyncClient):
    """Kiểm tra Endpoint Nhật ký Phiên bản & So sánh Diffs trước/sau hiệu đính."""
    search_res = await async_client.get("/api/v1/search", params={"page_size": 1})
    assert search_res.status_code == 200
    sdata = search_res.json()

    doc_id = sdata["results"][0]["document_id"] if sdata.get("results") else "a69799ce-74f2-46b9-94d3-fe7f1f50b0aa"
    res = await async_client.get(f"/api/v1/search/documents/{doc_id}/audit-trail")
    assert res.status_code == 200
    data = res.json()
    assert "document_id" in data
    assert "title" in data
    assert "current_version" in data
    assert "revisions" in data
    assert isinstance(data["revisions"], list)
    assert len(data["revisions"]) >= 2

    first_rev = data["revisions"][0]
    assert "revision_number" in first_rev
    assert "editor_name" in first_rev
    assert "diffs" in first_rev
    assert isinstance(first_rev["diffs"], list)
    assert len(first_rev["diffs"]) > 0


@pytest.mark.asyncio
async def test_active_watchers_lifecycle(async_client: httpx.AsyncClient):
    """Kiểm tra Endpoint Hệ thống Watcher & Cảnh báo Sự kiện Thời gian thực."""
    # 1. Lấy danh sách Watchers hiện tại
    res_list = await async_client.get("/api/v1/search/watchers")
    assert res_list.status_code == 200
    w_list = res_list.json()
    assert "total_watchers" in w_list
    assert "watchers" in w_list
    assert len(w_list["watchers"]) >= 1

    # 2. Tạo mới một Watcher
    new_w_body = {
        "name": "Giám sát Đơn xin Miễn giảm Khóa 46",
        "query_text": "miễn giảm học phí Khóa 46 K46",
        "category_code": "MIEN_GIAM_HOC_PHI",
        "min_priority": "HIGH",
    }
    res_create = await async_client.post("/api/v1/search/watchers", json=new_w_body)
    assert res_create.status_code == 200
    created = res_create.json()
    assert "watcher_id" in created
    assert created["name"] == new_w_body["name"]
    assert created["query_text"] == new_w_body["query_text"]

    # 3. Lấy sự kiện vừa kích hoạt
    watcher_id = created["watcher_id"]
    res_evts = await async_client.get(f"/api/v1/search/watchers/{watcher_id}/triggered-events")
    assert res_evts.status_code == 200
    evts = res_evts.json()
    assert isinstance(evts, list)
    assert len(evts) >= 1
    assert "event_id" in evts[0]
    assert "document_title" in evts[0]
    assert "match_reason" in evts[0]


# ==============================================================================
# TESTS CHO 2 ĐỀ XUẤT NÂNG CAO: HYBRID RRF & KIBANA CANVAS DASHBOARD
# ==============================================================================

@pytest.mark.asyncio
async def test_hybrid_search_rrf_scoring(async_client: httpx.AsyncClient):
    """Kiểm tra Endpoint Tìm kiếm Lai RRF (BM25 + kNN Reciprocal Rank Fusion - ES 8.9+)."""
    # 1. Truy vấn chuẩn k = 20
    payload = {
        "query": "nghị định 81 miễn giảm học phí sv nghèo khó khăn",
        "rank_constant_k": 20,
        "limit": 10,
    }
    res = await async_client.post("/api/v1/search/hybrid-rrf", json=payload)
    assert res.status_code == 200
    data = res.json()

    assert data["query"] == payload["query"]
    assert data["rank_constant_k"] == 20
    assert "total_results" in data
    assert "results" in data
    assert "metrics" in data
    assert len(data["results"]) >= 1

    first_hit = data["results"][0]
    assert "document_id" in first_hit
    assert "title" in first_hit
    assert "rrf_score" in first_hit
    assert first_hit["rrf_score"] > 0
    assert first_hit["match_type"] in ("HYBRID_BOTH", "KEYWORD_ONLY", "SEMANTIC_ONLY")
    assert "explanation" in first_hit

    # 2. Truy vấn với k = 60 (chuẩn bài báo Cormack et al. 2009)
    payload_k60 = {
        "query": "học bổng khuyến khích học tập",
        "rank_constant_k": 60,
        "limit": 5,
    }
    res_k60 = await async_client.post("/api/v1/search/hybrid-rrf", json=payload_k60)
    assert res_k60.status_code == 200
    data_k60 = res_k60.json()
    assert data_k60["rank_constant_k"] == 60
    assert len(data_k60["results"]) <= 5


@pytest.mark.asyncio
async def test_kibana_canvas_preview_and_export(async_client: httpx.AsyncClient):
    """Kiểm tra Endpoint Báo cáo Điều hành Kibana Canvas & Xuất gói Saved Objects .ndjson."""
    # 1. Xem trước số liệu động Canvas Workpad
    res_preview = await async_client.get("/api/v1/search/kibana/canvas-preview")
    assert res_preview.status_code == 200
    pdata = res_preview.json()

    assert "Đại học Đà Lạt" in pdata["title"]
    assert "executive_kpis" in pdata
    kpis = pdata["executive_kpis"]
    assert kpis["total_documents"] >= 400
    assert kpis["active_beneficiaries"] >= 300
    assert "Tỷ VNĐ" in kpis["total_budget_disbursed"]

    assert "faculty_budget_distribution" in pdata
    assert len(pdata["faculty_budget_distribution"]) == 8  # 8 khoa của ĐH Đà Lạt
    faculty_names = [f["faculty"] for f in pdata["faculty_budget_distribution"]]
    assert any("Công nghệ Thông tin" in fn for fn in faculty_names)
    assert any("Sư phạm" in fn for fn in faculty_names)

    assert "policy_share_metrics" in pdata
    assert len(pdata["policy_share_metrics"]) >= 4

    assert "ocr_quality_gauge" in pdata
    assert pdata["ocr_quality_gauge"]["status"] == "HEALTHY"

    # 2. Xuất gói Saved Objects NDJSON
    res_export = await async_client.get("/api/v1/search/kibana/export-dashboard")
    assert res_export.status_code == 200
    assert "attachment" in res_export.headers.get("content-disposition", "")
    assert "docuctsv_kibana_dashboard.ndjson" in res_export.headers.get("content-disposition", "")

    # Nội dung tải về phải chứa các object của Kibana (dashboard, canvas-workpad, index-pattern)
    ndjson_text = res_export.text
    assert "dashboard-docuctsv-overview" in ndjson_text
    assert "workpad-docuctsv-executive" in ndjson_text
    assert "index-pattern" in ndjson_text



