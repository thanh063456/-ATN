# Dataset Inventory & Management Directory

## Purpose

Thư mục quản lý toàn bộ tập dữ liệu (Dataset) cho hệ thống **Student-Document-OCR**, từ dữ liệu gốc thô đến dữ liệu đã tiền xử lý, gán nhãn, kiểm định, chia tập (Train/Val/Test), quản lý metadata và thống kê.

## Scope

Quản lý dữ liệu tài liệu Công tác sinh viên (CTSV) phục vụ huấn luyện và đánh giá mô hình OCR VietOCR / PaddleOCR.

---

## 1. Trạng thái Dữ liệu Hiện tại (Dataset Status)

```yaml
DATASET_STATUS: NOT_PROVIDED
CURRENT_VERSION: v0.1-draft
TOTAL_DOCUMENTS: 0
TOTAL_PAGES: 0
TOTAL_TEXT_LINES: 0
```

> **LƯU Ý**: Hiện tại dữ liệu tài liệu CTSV thực tế chưa được tải lên hệ thống (`DATASET_STATUS = NOT_PROVIDED`). Không tự ý sinh dữ liệu giả lập (dummy data) để thay thế dữ liệu thật.

---

## 2. Cấu trúc & Mục đích Các Thư mục Con

```
dataset/
├── raw/         # File tài liệu thô đầu vào của pipeline (PDF scan gốc, ảnh chụp)
├── source/      # Biểu mẫu trống (templates) & văn bản quy định - KHÔNG đưa vào Train/Test
├── images/      # Ảnh trang tài liệu đã chuẩn hóa (DPI 200/300, Grayscale/RGB)
├── annotations/ # File gán nhãn vùng chữ & văn bản thô (LabelMe JSON / CVAT XML)
├── crops/       # Ảnh dòng chữ cắt sẵn (Line Crops, giữ nguyên Aspect Ratio gốc)
├── train/       # Tập huấn luyện VietOCR (80%): crops/ + labels.txt (TSV) - Document-level split
├── val/         # Tập kiểm định VietOCR (10%): crops/ + labels.txt (TSV) - Document-level split
├── test/        # Tập kiểm thử độc lập (10%): crops/ + labels.txt (TSV) - Document-level split
├── metadata/    # Dữ liệu kiểm kê chi tiết từng tài liệu (inventory JSON/CSV)
├── statistics/  # Báo cáo thống kê tập dữ liệu (vocabulary.json trích xuất động)
└── README.md    # Tài liệu hướng dẫn quản lý dataset (file này)
```

### Mục đích Chi tiết từng Thư mục:

| Thư mục | Mục đích & Quy tắc Bảo vệ |
|---------|---------------------------|
| `raw/` | Lưu trữ file nguyên bản khi tiếp nhận từ Phòng CTSV (`.pdf`, `.jpg`, `.png`, `.tiff`). Nguồn chính để trích xuất ảnh trang và tập train/val/test. |
| `source/` | Lưu trữ biểu mẫu trống (blank templates), tài liệu tham chiếu nghiệp vụ. **Quy tắc**: File trong `source/` KHÔNG ĐƯỢC tự động đưa vào tập `train/val/test`. |
| `images/` | Chứa các trang ảnh đã trích xuất từ PDF (bằng `pdf2image` DPI 200/300) và chuẩn hóa xoay góc (deskew). |
| `annotations/` | Lưu file gán nhãn tọa độ dòng chữ và nội dung nhãn Ground Truth (định dạng LabelMe JSON hoặc CVAT). |
| `crops/` | Chứa các bức ảnh cắt dòng chữ (line crops) giữ nguyên độ phân giải và tỷ lệ khung hình gốc (Preserve Aspect Ratio). |
| `train/` | Tập dữ liệu 80% dùng để fine-tune weights mô hình VietOCR (chia theo Document Level). Gồm line crops và file `labels.txt` (TSV). |
| `val/` | Tập dữ liệu 10% dùng để đo `val_CER` sau mỗi epoch và thực hiện Early Stopping. |
| `test/` | Tập dữ liệu 10% giữ kín hoàn toàn, chỉ dùng để đánh giá CER/WER chính thức ở Phase 4. |
| `metadata/` | Lưu trữ file `inventory.json` / `inventory.csv` chứa thông tin quản lý 12 trường metadata. |
| `statistics/` | Báo cáo thống kê số lượng văn bản, trang, dòng chữ, và bảng từ vựng động (`vocabulary.json`). |

---

## 3. Quy trình Quản lý Dữ liệu (Dataset Pipeline Workflow)

```
[raw/] PDF/Image gốc thực tế (Không dùng blank templates trong source/)
   │
   ▼
[images/] Trích xuất trang & Chuẩn hóa (DPI 200/300, Deskew)
   │
   ▼
[annotations/] Gán nhãn Bounding Box & Ground Truth Text (Annotator -> Reviewer Workflow)
   │
   ▼
[crops/] Cắt dòng chữ (Line Cropping, Preserve Aspect Ratio gốc)
   │
   ▼
[train/ / val/ / test/] Chia tập ở Cấp độ Tài liệu (Document Level 80/10/10) & Xuất labels.txt (TSV)
   │
   ▼
[metadata/ & statistics/] Cập nhật Dataset Inventory & Trích xuất Vocabulary Động
```

---

## 4. Dataset Tooling (Công cụ Quản lý Dữ liệu)

Hệ thống cung cấp 4 công cụ tự động trong thư mục `scripts/` hỗ trợ kiểm tra và quản lý dữ liệu mà không làm thay đổi hay xóa file:

| Script Tool | Chức năng | Đầu ra (Output) |
|-------------|-----------|-----------------|
| `scripts/dataset_validator.py` | Kiểm tra định dạng, kích thước, convention, trùng lặp & corruption | Báo cáo kiểm tra JSON (không xóa file) |
| `scripts/dataset_inventory.py` | Tự động lập danh mục kiểm kê từ `dataset/raw/` | `dataset/metadata/inventory.json` & `.csv` |
| `scripts/dataset_statistics.py` | Thống kê số lượng, loại file, dung lượng, phân phối | Trả về `DATASET_STATUS = NOT_PROVIDED` nếu rỗng |
| `scripts/dataset_report.py` | Sinh báo cáo tổng hợp Markdown và JSON | `dataset/statistics/dataset_report.json` & `.md` |

### Chạy Công cụ Quản lý & Kiểm tra

```bash
# 1. Kiểm tra tập file thô
python scripts/dataset_validator.py

# 2. Sinh danh mục kiểm kê (Inventory)
python scripts/dataset_inventory.py

# 3. Sinh báo cáo thống kê
python scripts/dataset_report.py

# 4. Chạy Unit Tests kiểm tra Tooling
python -m unittest tests/test_dataset_tooling.py
```

---

## TODO

- [ ] Tiếp nhận tập tài liệu CTSV thật từ cán bộ quản lý.
- [ ] Tiến hành phân loại tài liệu vào `raw/` và trích xuất ra `images/`.
- [ ] Chạy `scripts/dataset_validator.py` kiểm tra toàn bộ file đầu vào.
- [ ] Thực hiện gán nhãn LabelMe theo Annotation Rules cho tập ảnh và lưu vào `annotations/`.
- [ ] Chạy script cắt dòng (Preserve aspect ratio) và chia tập `train/val/test`.

## References

- .ai/research/Dataset.md
- .ai/research/OCR.md
- .ai/research/Training.md
- .ai/PROJECT_SPEC.md
