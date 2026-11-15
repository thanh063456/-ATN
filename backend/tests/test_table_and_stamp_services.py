"""
backend/tests/test_table_and_stamp_services.py — Unit Tests for Table & Red Stamp Services
"""

import io
import pytest
import numpy as np
from PIL import Image, ImageDraw
from app.services.stamp_service import stamp_service, StampService, DetectedStamp, StampExtractionResult
from app.services.table_service import table_service, TableService, ExtractedTable, TableCell


def create_sample_stamp_image(w=500, h=400, with_text=True):
    img = Image.new("RGB", (w, h), color=(255, 255, 255))
    draw = ImageDraw.Draw(img)

    if with_text:
        # Nét chữ đen
        draw.text((80, 120), "TRUONG PHONG CTSV", fill=(0, 0, 0))
        draw.text((80, 160), "Pham Hong Hai", fill=(0, 0, 0))

    # Con dấu đỏ tròn (Red seal) đè lên góc chữ
    draw.ellipse((60, 90, 220, 250), outline=(210, 25, 25), width=5)
    draw.ellipse((80, 110, 200, 230), outline=(210, 25, 25), width=2)
    draw.text((95, 140), "DAI HOC DA LAT", fill=(210, 25, 25))
    return img


def create_sample_table_image(w=600, h=400, rows=3, cols=3):
    img = Image.new("RGB", (w, h), color=(255, 255, 255))
    draw = ImageDraw.Draw(img)

    x_start, y_start = 50, 50
    cell_w, cell_h = 160, 70

    # Vẽ đường ngang
    for r in range(rows + 1):
        y = y_start + r * cell_h
        draw.line([(x_start, y), (x_start + cols * cell_w, y)], fill=(0, 0, 0), width=2)

    # Vẽ đường dọc
    for c in range(cols + 1):
        x = x_start + c * cell_w
        draw.line([(x, y_start), (x, y_start + rows * cell_h)], fill=(0, 0, 0), width=2)

    # Thêm text mẫu trong các ô
    draw.text((60, 65), "STT", fill=(0, 0, 0))
    draw.text((220, 65), "Noi dung", fill=(0, 0, 0))
    draw.text((380, 65), "Ghi chu", fill=(0, 0, 0))

    draw.text((60, 135), "1", fill=(0, 0, 0))
    draw.text((220, 135), "Huy dong SV", fill=(0, 0, 0))
    draw.text((380, 135), "Khan dai A25", fill=(0, 0, 0))

    return img


class TestStampService:
    def test_get_red_mask(self):
        img_bgr = np.zeros((100, 100, 3), dtype=np.uint8)
        # BGR: Red has B=0, G=0, R=255
        img_bgr[20:80, 20:80] = [0, 0, 255]

        mask = StampService.get_red_mask(img_bgr)
        assert np.count_nonzero(mask[20:80, 20:80]) > 0
        assert np.count_nonzero(mask[0:10, 0:10]) == 0

    def test_detect_stamps_success(self):
        img = create_sample_stamp_image()
        result = stamp_service.detect_and_extract_stamps(img)

        assert result.has_stamp is True
        assert len(result.stamps) >= 1
        assert result.stamps[0].confidence > 0.5
        assert result.stamps[0].area > 1000
        assert result.stamps[0].image_base64.startswith("data:image/png;base64,")
        assert result.cleaned_image is not None

    def test_detect_stamps_empty_image(self):
        plain_img = Image.new("RGB", (300, 300), color=(255, 255, 255))
        result = stamp_service.detect_and_extract_stamps(plain_img)

        assert result.has_stamp is False
        assert len(result.stamps) == 0

    def test_remove_red_stamp_for_ocr(self):
        img = create_sample_stamp_image()
        cleaned = stamp_service.remove_red_stamp_for_ocr(img)

        assert cleaned is not None
        assert cleaned.size == img.size
        # Sau khi tẩy, lượng pixel đỏ phải giảm rõ rệt
        cleaned_bgr = np.array(cleaned.convert("RGB"))[:, :, ::-1]
        mask_after = StampService.get_red_mask(cleaned_bgr)
        orig_bgr = np.array(img)[:, :, ::-1]
        mask_before = StampService.get_red_mask(orig_bgr)
        assert np.count_nonzero(mask_after) < np.count_nonzero(mask_before)


class TestTableService:
    def test_detect_table_grid(self):
        img = create_sample_table_image()
        img_rgb = np.array(img)
        gray, thresh = TableService._to_gray_thresh(img_rgb)
        horiz, vert, grid = TableService.detect_table_grid(thresh)

        assert np.count_nonzero(horiz) > 0
        assert np.count_nonzero(vert) > 0
        assert np.count_nonzero(grid) > 0

    def test_extract_tables_structure(self):
        img = create_sample_table_image(rows=3, cols=3)
        result = table_service.extract_tables(img, ocr_cells=False)

        assert result.has_table is True
        assert result.total_tables >= 1
        tbl = result.tables[0]
        assert tbl.row_count >= 2
        assert tbl.col_count >= 2
        assert len(tbl.cells) >= 4
        assert "|" in tbl.markdown
        assert "<table" in tbl.html

    def test_extract_tables_plain_image(self):
        plain_img = Image.new("RGB", (400, 400), color=(255, 255, 255))
        result = table_service.extract_tables(plain_img, ocr_cells=False)

        assert result.has_table is False
        assert result.total_tables == 0
        assert len(result.tables) == 0


import httpx

@pytest.mark.asyncio
async def test_detect_stamp_endpoint(async_client: httpx.AsyncClient, staff_token: str):
    """Kiểm tra API bóc tách con dấu đỏ /documents/{id}/detect-stamp."""
    img = create_sample_stamp_image()
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    files = {"file": ("stamp_sample.png", buf.getvalue(), "image/png")}
    headers = {"Authorization": f"Bearer {staff_token}"}
    up_res = await async_client.post(
        "/api/v1/documents/upload", data={"title": "Văn bản có dấu đỏ"}, files=files, headers=headers
    )
    assert up_res.status_code == 202
    doc_id = up_res.json()["id"]

    resp = await async_client.post(f"/api/v1/documents/{doc_id}/detect-stamp", headers=headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["document_id"] == doc_id
    assert data["has_stamp"] is True
    assert len(data["stamps"]) >= 1
    assert data["stamps"][0]["confidence"] > 0.5


@pytest.mark.asyncio
async def test_extract_tables_endpoint(async_client: httpx.AsyncClient, staff_token: str):
    """Kiểm tra API bóc tách bảng biểu /documents/{id}/extract-tables."""
    img = create_sample_table_image()
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    files = {"file": ("table_sample.png", buf.getvalue(), "image/png")}
    headers = {"Authorization": f"Bearer {staff_token}"}
    up_res = await async_client.post(
        "/api/v1/documents/upload", data={"title": "Văn bản có bảng biểu"}, files=files, headers=headers
    )
    assert up_res.status_code == 202
    doc_id = up_res.json()["id"]

    resp = await async_client.post(f"/api/v1/documents/{doc_id}/extract-tables?ocr_cells=false", headers=headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["document_id"] == doc_id
    assert data["has_table"] is True
    assert len(data["tables"]) >= 1
    assert data["tables"][0]["markdown"] != ""

