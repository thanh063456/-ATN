# Dataset — Chính sách & Quy chuẩn Quản lý Dữ liệu OCR

## Purpose

Tài liệu quy định toàn bộ Chính sách Dữ liệu (Dataset Policy), Quy chuẩn Kiểm kê (Inventory Schema), Phân loại Văn bản (Document Taxonomy), Tiêu chuẩn Chất lượng (Data Quality Checklist), Quy tắc Gán nhãn Chi tiết (Annotation Policy), Xử lý Nội dung Đặc biệt (Special Content Policy), Quy trình Kiểm định (Annotation Quality Workflow) và Quản lý Phiên bản (Versioning) cho hệ thống Student-Document-OCR.

## Scope

Toàn bộ quy trình quản lý tập dữ liệu từ tiếp nhận file thô, gán nhãn, kiểm định chất lượng đến chia tập dữ liệu (Train/Val/Test).

---

## 1. Trạng thái Dữ liệu (Dataset Status)

```yaml
DATASET_STATUS: NOT_PROVIDED
CURRENT_VERSION: v0.1-draft
TOTAL_DOCUMENTS: 0
TOTAL_PAGES: 0
TOTAL_TEXT_LINES: 0
```

> **QUAN TRỌNG**: Hiện tại dữ liệu tài liệu CTSV thực tế chưa được cung cấp (`DATASET_STATUS = NOT_PROVIDED`). Không tự ý sinh dữ liệu giả lập (dummy data) để thay thế dataset thật. Tất cả con số trong tài liệu này là quy chuẩn kỹ thuật và định ước chính sách.

---

## 2. Dataset Policy & Alignment (Chính sách Dữ liệu)

### 2.1 Line Crop Policy (Chính sách Cắt Dòng Ảnh)
- **Preserve Original Crop & Aspect Ratio**: Ảnh dòng chữ (Line Crop) trích xuất trong các thư mục `crops/`, `train/`, `val/`, `test/` **bắt buộc giữ nguyên độ phân giải và tỷ lệ khung hình gốc (Preserve Aspect Ratio)** từ ảnh trang.
- **Không ép cứng $H = 32\text{px}$ trong Dataset**: Tuyệt đối không nén méo hoặc resize cứng về $H = 32\text{px}$ khi lưu trữ trong dataset nhằm tránh làm biến dạng chữ và đứt nét dấu thanh tiếng Việt.
- **VietOCR Runtime Preprocessing**: Việc resize và padding chiều cao $H = 32\text{px}$ sẽ được thực hiện động ở tầng DataLoader/Preprocessing của VietOCR tại runtime dựa theo cấu hình mô hình (`Cfg`).
  ```
  Raw Line Crop (Giữ nguyên độ phân giải & tỷ lệ gốc trong dataset)
        │
        ▼
  Preserve Aspect Ratio (Không nén/ép méo ảnh khi lưu trữ)
        │
        ▼
  VietOCR Preprocessing Pipeline (Runtime DataLoader at Training/Inference)
        │
        ▼
  Dynamic Resize & Padding theo Model Configuration (Cfg)
  ```

### 2.2 Dynamic Character Inventory (Bảng Ký tự Động)
- **Không khóa cứng "89 ký tự có dấu"**: Không sử dụng khái niệm "89 ký tự" như một charset giới hạn cứng cho mô hình.
- **Trích xuất Động từ Ground Truth**: Tập ký tự (Character Inventory) được thống kê tự động từ 100% dữ liệu Ground Truth thực tế sau khi hoàn thành gán nhãn và được lưu tại `dataset/statistics/vocabulary.json`.
- **Thành phần Bao gồm**:
  - Toàn bộ chữ cái tiếng Việt hoa và thường có dấu (Vietnamese Accented Characters).
  - Chữ cái Latin (A-Z, a-z).
  - Chữ số (0-9).
  - Dấu câu & Ký hiệu hành chính: `. , : ; - / ( ) " ' % ! ? № § ° + = & [ ]`.
  - Khoảng trắng chuẩn (Whitespace).
  - Các từ viết tắt & ký hiệu chuyên ngành CTSV (vd: `CTSV`, `P.CTSV`, `QĐ-CTSV`, `v/v`, `K/g`).
- **Thời điểm Freeze**: Character Inventory chỉ được đóng băng (Freeze) **sau khi toàn bộ dataset annotation hoàn thành và được phê duyệt**.

### 2.3 Phân biệt Thư mục `source/` và `raw/`
- **`raw/` (Dữ liệu Đầu vào Pipeline)**: Chứa các tài liệu scan/ảnh chụp thực tế từ sinh viên/cán bộ. Đây là nguồn dữ liệu duy nhất dùng để trích xuất trang, gán nhãn, cắt dòng và đưa vào tập `train/val/test`.
- **`source/` (Tài liệu Tham chiếu / Template)**: Lưu trữ các biểu mẫu trống (blank form templates), văn bản quy định gốc dùng làm mẫu tham chiếu nghiệp vụ.
- **Quy tắc tuyệt đối**: **Các file trong `source/` KHÔNG ĐƯỢC tự động đưa vào tập huấn luyện/kiểm thử (`train/val/test`)** nếu chúng chỉ là mẫu biểu trống hoặc tài liệu tham chiếu thuần túy.

### 2.4 Train / Validation / Test Policy & Data Leakage Prevention
- **Tỷ lệ chia tập**: **80% Train / 10% Validation / 10% Test**.
- **Document-Level Split bắt buộc**: Chia tập dữ liệu **bắt buộc thực hiện ở CẤP ĐỘ TÀI LIỆU (Document Level)**, không chia ở cấp độ dòng chữ (Line Level).
- **Quy tắc chống Rò rỉ Dữ liệu**: Tất cả các trang và dòng chữ trích xuất từ cùng 1 tài liệu (cùng `document_id`) **BẮT BUỘC** phải nằm trong duy nhất 1 tập split (`TRAIN`, `VAL` hoặc `TEST`). Tuyệt đối không cho phép các dòng chữ từ cùng 1 file xuất hiện ở cả tập Train và tập Test.

---

## 3. Annotation Policy & Data Unit Schema

### 3.1 Annotation Unit (Đơn vị Gán nhãn)
- **Đơn vị chuẩn**: **Text Line** (Dòng chữ).

### 3.2 Schema Bản ghi Annotation (JSON Structure)
Mỗi annotation của 1 dòng chữ phải chứa đầy đủ các trường thông tin:

```json
{
  "annotation_id": "ann_uuid_123456",
  "document_id": "doc_uuid_a1b2c3d4",
  "page_id": 1,
  "line_id": 12,
  "bounding_box": {
    "x": 120,
    "y": 450,
    "width": 850,
    "height": 45,
    "polygon": [[120, 450], [970, 450], [970, 495], [120, 495]]
  },
  "transcription": "CỘNG HÒA XÃ HỘI CHỦ NGHĨA VIỆT NAM",
  "language": "vi",
  "quality": "GOOD",
  "annotation_status": "APPROVED",
  "annotated_by": "user_annotator_01",
  "reviewed_by": "user_reviewer_01",
  "created_at": "2026-08-08T08:30:00Z"
}
```

### 3.3 Quy tắc Trung thực Ground Truth (Fidelity Rules)
- **Bảo toàn nguyên bản**: Ground Truth bắt buộc phải phản ánh **chính xác 100% nội dung trực quan nhìn thấy trên văn bản**, bao gồm: dấu tiếng Việt, dấu câu, chữ số, chữ hoa/thường, và khoảng trắng có nghĩa.
- **KHÔNG tự ý sửa lỗi chính tả**: Nếu văn bản gốc của sinh viên/cán bộ có lỗi gõ sai chính tả (vd: `nghi hoc` thay vì `nghỉ học`, `bảo lưu` viết thành `báo lưu`), Ground Truth **BẮT BUỘC phải ghi lại đúng từ sai đó**. Tuyệt đối không tự ý sửa chính tả văn bản gốc khi gán nhãn.

---

## 4. Special Content Policy (Xử lý Nội dung Đặc biệt)

Không phải mọi vùng trên trang ảnh đều được đưa vào VietOCR recognition dataset. Quy định cụ thể:

| Loại Nội dung | Quy tắc Gán nhãn & Xử lý | Đưa vào VietOCR Training? |
|---------------|--------------------------|---------------------------|
| **Text Lines (Dòng chữ in)** | Bounding box vừa khít dòng chữ (margin 2-3px), gán nhãn đúng chữ in. | **CÓ** |
| **Tables (Bảng biểu)** | Cắt dòng chữ bên trong từng ô bảng (Cell-level line crop), đọc theo hàng. Không cắt cả khung bảng. | **CÓ** (chỉ cắt phần dòng chữ) |
| **Multi-column (Nhiều cột)** | Đọc hết cột bên trái từ trên xuống trước, sau đó sang cột bên phải. | **CÓ** |
| **Stamp (Con dấu đỏ)** | Nếu chữ in dưới dấu **đọc rõ 100%** -> Gán nhãn chữ in. Nếu bị che mờ hoàn toàn -> Gắn tag `[UNREADABLE]`. Không gửi riêng hình con dấu vào OCR. | **KHÔNG** (nếu unreadable) |
| **Signature (Chữ ký tay)** | Chữ ký tay nằm ngoài phạm vi OCR chữ in. Nếu chữ ký đè chữ in và che lấp hoàn toàn -> Gắn tag `[UNREADABLE]`. | **KHÔNG** |
| **Handwriting (Chữ viết tay điền đơn)** | Gắn tag `[HANDWRITING]` cho các đoạn chữ viết tay. | **KHÔNG** (không dùng train OCR chữ in) |
| **Unreadable Text (Chữ mờ nhòe/rách)** | Gắn tag `[UNREADABLE]` cho dòng chữ không thể đọc được. | **KHÔNG** |
| **Checkbox** | Không cắt riêng ô checkbox `[ ]`/`[x]` trừ khi nằm trong dòng chữ. | **KHÔNG** |
| **Logo (Biểu trưng trường/khoa)** | Không cắt hay gán nhãn logo. | **KHÔNG** |
| **Header / Footer** | Gán nhãn nếu chứa dòng chữ in hợp lệ. | **CÓ** |

---

## 5. Annotation Quality Workflow (Quy trình Kiểm định Chất lượng Gán nhãn)

Để đảm bảo chất lượng Ground Truth 100% tin cậy, quy trình gán nhãn áp dụng mô hình 2 vai trò **Annotator** và **Reviewer**:

```
[Mẫu ảnh dòng chữ PENDING]
           │
           ▼
┌──────────────────────┐
│  1. ANNOTATOR        │ (Tạo Bounding Box & Nhập Transcription)
└──────────┬───────────┘
           │
           ▼
[Trạng thái: REVIEW]
           │
           ▼
┌──────────────────────┐
│  2. REVIEWER         │ (Kiểm tra Bounding Box, NFC Normalization, Exact Match)
└──────────┬───────────┘
           │
     ┌─────┴────────────────┐
     ▼                      ▼
[APPROVED]             [REJECTED]
(Đủ điều kiện          (Trả về Annotator
 đợt chia split)        sửa lại)
```

### Các Trạng thái Gán nhãn (Annotation Status):
1. **`PENDING`**: Trang ảnh/dòng chữ mới nạp, chưa được gán nhãn.
2. **`REVIEW`**: Annotator đã hoàn thành gán nhãn, chờ Reviewer kiểm tra.
3. **`APPROVED`**: Reviewer đã kiểm tra và phê duyệt -> **Đủ điều kiện đưa vào tập dữ liệu**.
4. **`REJECTED`**: Reviewer phát hiện sai sót (lẹm dấu, sai Unicode, sai chữ) -> Trả về Annotator sửa.

---

## 6. Dataset Inventory Schema (Cấu trúc Kiểm kê Dữ liệu)

Mỗi tài liệu trong dataset được quản lý thông qua bản ghi Metadata kiểm kê (lưu tại `dataset/metadata/inventory.json` / `inventory.csv`).

| Field Name | Data Type | Value / Enum | Mô tả |
|------------|-----------|--------------|-------|
| `document_id` | String (UUID) | `a1b2c3d4-xxxx...` | ID duy nhất quản lý trong dataset |
| `source_file` | String | `don_nghi_hoc_sample.pdf` | Tên file gốc ban đầu |
| `file_type` | String | `PDF`, `JPG`, `PNG`, `TIFF` | Định dạng file gốc |
| `document_type` | String (Enum) | `DON_NGHI_HOC`, `KY_LUAT`,... | Mã danh mục tài liệu theo Taxonomy |
| `page_count` | Integer | `1`, `2`, `5` | Tổng số trang |
| `resolution` | Integer | `150`, `200`, `300` | Độ phân giải (DPI) |
| `language` | String | `vi` | Ngôn ngữ văn bản |
| `quality` | String (Enum) | `GOOD`, `ACCEPTABLE`, `REJECT` | Phân loại chất lượng ảnh |
| `source` | String | `PHONG_CTSV_SCAN`, `PUBLIC_DATASET` | Nguồn thu thập |
| `annotation_status`| String (Enum)| `UNANNOTATED`, `IN_PROGRESS`, `ANNOTATED`, `VERIFIED` | Trạng thái gán nhãn |
| `split` | String (Enum) | `TRAIN`, `VAL`, `TEST`, `UNASSIGNED` | Tập dữ liệu được phân chia |
| `created_at` | String (ISO8601)| `2026-08-08T08:30:00Z` | Thời điểm ghi nhận vào inventory |

---

## 7. Document Taxonomy (Phân loại Tài liệu CTSV - 11 Loại)

| STT | Category Code | Tên Loại Tài liệu | Mô tả & Đặc điểm |
|-----|---------------|-------------------|------------------|
| 1 | `THONG_BAO` | Thông báo | Thông báo chung của Phòng CTSV tới sinh viên |
| 2 | `QUYET_DINH` | Quyết định | Quyết định khen thưởng, kỷ luật, tiếp nhận |
| 3 | `BIEU_MAU` | Biểu mẫu | Đơn từ mẫu (Đơn xin nghỉ học, bảo lưu, chuyển ca) |
| 4 | `VAN_BAN_HANH_CHINH` | Văn bản hành chính | Công văn, tờ trình, biên bản họp |
| 5 | `HO_SO` | Hồ sơ sinh viên | Lý lịch sinh viên, hồ sơ nhập học |
| 6 | `DANH_SACH` | Danh sách | Danh sách sinh viên nhận học bổng, xét tốt nghiệp |
| 7 | `CHE_DO_CHINH_SACH` | Chế độ chính sách | Đơn đề nghị trợ cấp xã hội, ưu đãi giáo dục |
| 8 | `HOC_BONG` | Học bổng | Đơn xin học bổng khuyến khích, tài trợ |
| 9 | `KHEN_THUONG` | Khen thưởng | Bằng khen, giấy khen sinh viên xuất sắc |
| 10 | `KY_LUAT` | Kỷ luật | Biên bản vi phạm quy chế, quyết định kỷ luật |
| 11 | `MIEN_GIAM_HOC_PHI` | Miễn giảm học phí | Đơn xin miễn giảm học phí theo đối tượng |

---

## 8. Data Quality Checklist & Classification (Tiêu chuẩn Chất lượng)

- **Checklist 13 tiêu chí**: Corrupted file, Low resolution (<150 DPI), Blur, Noise, Skew (>5°), Rotation, Low contrast, Background noise, Vietnamese diacritics, Tables, Stamps, Signatures, Handwriting.
- **Phân loại**:
  - `GOOD`: Scan sắc nét ≥ 200 DPI, chữ rõ ràng -> Đưa trực tiếp vào pipeline.
  - `ACCEPTABLE`: Hơi nghiêng (<3°), nhiễu nhẹ -> Đưa qua Preprocessing (Deskew, Denoise) trước khi gán nhãn.
  - `REJECT`: Hỏng, mờ không đọc được, < 150 DPI -> **Loại bỏ hoàn toàn**.

---

## 9. Dataset Versioning (Quản lý Phiên bản Dataset)

| Dataset Version | Status | Total Docs | Total Pages | Line Crops | Train / Val / Test | Ghi chú & Thay đổi |
|-----------------|--------|------------|-------------|------------|--------------------|-------------------|
| **`v0.1-draft`** | **CURRENT** | **0** | **0** | **0** | **0 / 0 / 0** | **Khởi tạo khung Dataset Inventory, Policies, Special Content Rules & Review Workflow (`DATASET_STATUS = NOT_PROVIDED`).** |
| `v0.2` | Planned | [TBD] | [TBD] | [TBD] | [TBD] / [TBD] / [TBD] | Đợt tiếp nhận dữ liệu thô đầu tiên từ Phòng CTSV. |
| `v1.0` | Planned | [TBD] | [TBD] | [TBD] | [TBD] / [TBD] / [TBD] | Tập dữ liệu hoàn chỉnh đã gán nhãn 100%, sẵn sàng cho Fine-tuning Phase 3. |

---

## 10. Dataset Tooling & Validation Suite (Công cụ Quản lý & Unit Tests)

Để phục vụ quản lý dữ liệu an toàn và chính xác, 4 công cụ đã được phát triển trong `scripts/` cùng bộ kiểm thử Unit Test tại `tests/test_dataset_tooling.py`:

| Công cụ (Tool) | File Script | Chức năng Kỹ thuật | Xử lý khi Dataset Rỗng |
|----------------|-------------|---------------------|------------------------|
| **Dataset Validator** | `scripts/dataset_validator.py` | Kiểm tra định dạng (PDF/JPG/PNG/TIFF), kích thước (≤50MB), filename convention, phát hiện trùng lặp hash SHA256 và corruption. Không tự động xóa file. | Trả về `total_files: 0` và `DATASET_STATUS = NOT_PROVIDED`. |
| **Inventory Generator** | `scripts/dataset_inventory.py` | Tự động sinh `dataset/metadata/inventory.json` và `inventory.csv` với 13 trường metadata. Trường không xác định được giữ nguyên `null`. | Xuất `[]` (JSON) và header-only (CSV). |
| **Statistics Calculator**| `scripts/dataset_statistics.py` | Thống kê số lượng văn bản, file, loại file, dung lượng, phân phối categories, quality, annotation status, split. | Trả về `DATASET_STATUS = NOT_PROVIDED` với số liệu = 0. |
| **Report Generator** | `scripts/dataset_report.py` | Tự động tạo `dataset/statistics/dataset_report.json` và `dataset_report.md`. | Ghi rõ `"No dataset available."` & `NOT_PROVIDED`. |
| **Unit Tests Suite** | `tests/test_dataset_tooling.py` | 8 Unit Tests kiểm thử độc lập validator, inventory, statistics, report và empty dataset handling. | **Pass 100% (8/8 tests pass)** với `dataset/raw/` rỗng. |

---

## TODO

- [ ] Tiếp nhận file dữ liệu thật để cập nhật `inventory.json` sang `v0.2`.
- [ ] Chạy `python scripts/dataset_validator.py` kiểm tra tập dữ liệu thô.

## References

- dataset/README.md
- OCR.md
- Training.md
- Evaluation.md
- PROJECT_SPEC.md
