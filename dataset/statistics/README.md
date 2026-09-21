# Dataset Statistics & Reports Directory

## Purpose

Thư mục lưu trữ các tệp thống kê và báo cáo tự động của tập dữ liệu (Dataset Reports & Statistics).

## Scope

Báo cáo phân phối dữ liệu, kích thước, định dạng, loại tài liệu, trạng thái gán nhãn và chia tập Train/Val/Test.

---

## 1. Trạng thái Báo cáo Dữ liệu (Dataset Report Status)

```yaml
DATASET_STATUS: NOT_PROVIDED
CURRENT_VERSION: v0.1-draft
DATASET_REPORT: "No dataset available."
```

> **LƯU Ý**: Hiện tại dữ liệu tài liệu CTSV thực tế chưa được cung cấp (`DATASET_STATUS = NOT_PROVIDED`). Không tự ý sinh số liệu giả lập để báo cáo.

---

## 2. Các Tệp Báo cáo Tự động (Generated Report Artifacts)

- **`dataset_report.json`**: Tệp JSON chứa toàn bộ chỉ số thống kê máy đọc được (machine-readable report).
- **`dataset_report.md`**: Báo cáo tổng hợp bằng Markdown dành cho con người (human-readable report).

---

## 3. Lệnh Tự động Sinh Báo cáo

Khi tiếp nhận file tài liệu thật vào `dataset/raw/`, chạy lệnh sau để cập nhật báo cáo:

```bash
python scripts/dataset_report.py
```

---

## References

- dataset/README.md
- .ai/research/Dataset.md
- scripts/dataset_statistics.py
