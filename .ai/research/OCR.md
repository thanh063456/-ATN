# OCR — Optical Character Recognition Pipeline

## Purpose

Mô tả chi tiết toàn bộ OCR pipeline của hệ thống Student-Document-OCR:
từng bước xử lý, input/output, công nghệ sử dụng, và các quyết định thiết kế.

## Scope

8 bước pipeline: Input Validation → Image Conversion → Preprocessing → Text Detection →
Text Line Cropping → VietOCR Recognition → Post-processing → Storage.

---

## 1. Tổng quan Pipeline

```
Input (PDF / Image)
        │
        ▼
[Step 1] Input Validation
        │
        ▼
[Step 2] Image Conversion (PDF → images nếu cần)
        │
        ▼
[Step 3] Image Preprocessing
        │
        ▼
[Step 4] Text Detection          ← [TBD: ADR-002]
        │
        ▼
[Step 5] Text Line Cropping & Sorting
        │
        ▼
[Step 6] VietOCR Recognition     ← ADR-001: DECIDED
        │
        ▼
[Step 7] Post-processing
        │
        ▼
[Step 8] Metadata Extraction
        │
    ┌───┴───┐
    ▼       ▼
PostgreSQL  Elasticsearch
```

---

## 2. Phân biệt Text Detection vs Text Recognition

> **QUAN TRỌNG**: Đây là 2 bài toán hoàn toàn khác nhau.

| Thuật ngữ | Bài toán | Input | Output | Engine trong dự án |
|-----------|---------|-------|--------|-------------------|
| **Text Detection** | Phát hiện vùng có chữ | Toàn trang ảnh | Danh sách bounding boxes | [TBD — ADR-002] |
| **Text Recognition** | Nhận dạng chữ | Ảnh đã crop (1 dòng chữ) | Chuỗi ký tự | **VietOCR** |

**VietOCR chỉ làm Text Recognition.** VietOCR nhận đầu vào là ảnh một dòng chữ và trả ra chuỗi ký tự.

---

## 3. Chi tiết từng bước

### Step 1 — Input Validation

| Field | Value |
|-------|-------|
| **Input** | File bytes từ HTTP upload |
| **Output** | Validated file bytes + file_type + page_count |
| **Công nghệ** | Python `magic` (MIME detection), size check |

**Validate:**
- File type: `application/pdf`, `image/jpeg`, `image/png`, `image/tiff`
- File size: ≤ 50MB
- File không bị corrupt (có thể mở được)

**Raise:** `InvalidFileTypeError`, `FileTooLargeError`, `CorruptFileError`

---

### Step 2 — Image Conversion

| Field | Value |
|-------|-------|
| **Input** | File bytes (PDF hoặc image) |
| **Output** | `list[PIL.Image]` — một image cho mỗi trang |
| **Công nghệ** | `pdf2image` (Poppler), `Pillow` |

**Logic:**
- Nếu PDF: `convert_from_bytes(bytes, dpi=200)` → list of images
- Nếu image: đọc bằng Pillow → wrap trong list
- Convert tất cả sang RGB (loại bỏ RGBA/grayscale nếu cần)

**Note:** DPI 200 là balance giữa quality và processing speed. Có thể điều chỉnh.

---

### Step 3 — Image Preprocessing

| Field | Value |
|-------|-------|
| **Input** | `PIL.Image` (một trang) |
| **Output** | `np.ndarray` (preprocessed) |
| **Công nghệ** | OpenCV, Pillow |

**Pipeline preprocessing:**
1. Convert sang grayscale (nếu cần)
2. **Deskew** (phát hiện và chỉnh rotation): dùng Hough Transform
3. **Denoise**: Gaussian blur nhẹ hoặc Non-local Means (nếu scan noisy)
4. **Binarization**: Adaptive thresholding (Otsu hoặc adaptive)
5. **Contrast enhancement**: CLAHE nếu ảnh quá tối/sáng

**Note:** Không áp dụng tất cả bước mặc định — tunable per document type.

---

### Step 4 — Text Detection

| Field | Value |
|-------|-------|
| **Input** | `np.ndarray` (preprocessed page image) |
| **Output** | `list[BoundingBox]` — tọa độ (x1, y1, x2, y2) mỗi text region |
| **Công nghệ** | **[TBD — ADR-002]** |
| **Status** | Chờ quyết định text detection engine |

**Candidates:**
- PaddleOCR Detection (DBNet++)
- CRAFT
- DBNet standalone

**Expected output format:**
```python
[
  {"x1": 10, "y1": 20, "x2": 300, "y2": 50, "confidence": 0.98},
  ...
]
```

---

### Step 5 — Text Line Cropping & Sorting

| Field | Value |
|-------|-------|
| **Input** | `list[BoundingBox]` + original page image |
| **Output** | `list[PIL.Image]` — ordered list of cropped line images |
| **Công nghệ** | OpenCV, numpy |

**Logic:**
1. Sắp xếp bounding boxes theo thứ tự đọc: top-to-bottom, left-to-right
2. Crop từng region từ ảnh gốc (với padding nhỏ)
3. Mỗi crop là input cho VietOCR

---

### Step 6 — VietOCR Recognition

| Field | Value |
|-------|-------|
| **Input** | `PIL.Image` — một dòng chữ đã crop |
| **Output** | `(text: str, prob: float)` |
| **Công nghệ** | VietOCR (ADR-001) |
| **Model** | vgg_transformer.pth (pre-trained) hoặc fine-tuned version |

**VietOCR Architecture:**
- **Backbone**: VGG-like CNN → extract visual features
- **Sequence model**: Transformer Seq2Seq với attention
- **Decoder**: Beam search (beam_width=5 mặc định)
- **Vocabulary**: Tiếng Việt đầy đủ có dấu

**Call:**
```python
from vietocr.tool.predictor import Predictor
from vietocr.tool.config import Cfg

config = Cfg.load_config_from_name('vgg_transformer')
config['device'] = 'cpu'  # hoặc 'cuda'
detector = Predictor(config)

text, prob = detector.predict(img, return_prob=True)
```

---

### Step 7 — Post-processing

| Field | Value |
|-------|-------|
| **Input** | `list[(text: str, prob: float)]` — tất cả text lines |
| **Output** | `clean_text: str` |
| **Công nghệ** | Python standard library, `unicodedata` |

**Pipeline:**
1. Join text lines thành đoạn văn (newline separator)
2. Unicode normalization: `unicodedata.normalize('NFC', text)`
3. Loại bỏ control characters (non-printable)
4. Bảo toàn paragraph structure (double newline giữa đoạn)
5. Tính confidence_score trung bình: `mean([prob for _, prob in results])`

---

### Step 8 — Metadata Extraction

| Field | Value |
|-------|-------|
| **Input** | `clean_text: str` + `document_category: str` |
| **Output** | `DocumentMetadata` object |
| **Công nghệ** | Python `re` (regex), rule-based |

**Extraction rules (ví dụ):**
```python
STUDENT_ID_PATTERN = r'\b\d{8,10}\b'       # MSSV dạng 8-10 chữ số
DATE_PATTERN = r'\d{1,2}/\d{1,2}/\d{4}'    # DD/MM/YYYY
DOC_NUMBER_PATTERN = r'Số:\s*(\S+)'         # Số văn bản
```

**Note:** Rule-based extraction — accuracy phụ thuộc vào format chuẩn của tài liệu.

---

## 4. Error Handling

| Error | Handling |
|-------|---------|
| File corrupt | Raise error → OCR status = FAILED |
| Text detection finds 0 regions | Cảnh báo, vẫn trả text="" với confidence=0 |
| VietOCR model not loaded | Retry 3 lần, raise exception nếu vẫn fail |
| Timeout (>30s) | Celery task timeout → FAILED |

---

## 5. Performance Targets

| Metric | Target |
|--------|--------|
| Processing time (1 trang A4, CPU) | < 10 giây |
| CER trên test set (in ấn chuẩn) | < 5% |
| WER trên test set | < 10% |
| Memory (model loaded) | < 1GB RAM |

---

## TODO

- [ ] Quyết định ADR-002 (text detection engine) → hoàn thiện Step 4
- [ ] Benchmark deskew algorithm cho tài liệu CTSV
- [ ] Benchmark preprocessing pipeline (on vs off từng bước)
- [ ] Xác định best DPI cho pdf2image với tài liệu CTSV
- [ ] Implement và test pipeline với 10 tài liệu mẫu

## References

- .ai/ARCHITECTURE.md (OCR Pipeline section)
- .ai/research/VietOCR.md
- .ai/research/PaddleOCR.md
- .ai/DECISIONS.md (ADR-001, ADR-002)
- training/README.md
