# Activity Diagram — Sơ đồ Hoạt động

## Purpose

Mô tả luồng điều khiển và luồng xử lý dữ liệu (Control & Data Flow) của các tiến trình chính trong hệ thống Student-Document-OCR.

## Scope

2 Activity Diagrams: Tiến trình Xử lý OCR Async & Tiến trình Tìm kiếm & Tra cứu Văn bản.

---

## 1. Activity Diagram 1: Tiến trình Xử lý OCR Async (OCR Processing Pipeline)

```mermaid
stateDiagram-v2
    [*] --> UploadFile: Cán bộ upload File PDF/Image
    UploadFile --> ValidateFile: Kiểm tra định dạng & dung lượng

    state ValidateFile {
        [*] --> CheckFormat
        CheckFormat --> FormatValid: File PDF/JPG/PNG/TIFF
        CheckFormat --> FormatInvalid: Định dạng không hỗ trợ
        FormatValid --> CheckSize: Dung lượng <= 50MB
        CheckSize --> SizeValid: Đạt chuẩn
        CheckSize --> SizeInvalid: Over 50MB
    }

    FormatInvalid --> RejectUpload: Báo lỗi định dạng
    SizeInvalid --> RejectUpload: Báo lỗi dung lượng
    RejectUpload --> [*]

    SizeValid --> SaveMinIO: Ghi file gốc lên MinIO Bucket
    SaveMinIO --> CreateDBRecord: Tạo Document status='PENDING'
    CreateDBRecord --> PushCelery: Gửi Task vào Redis Queue
    PushCelery --> ReturnAccepted: Trả về HTTP 202 Accepted cho FE

    state CeleryWorkerExecution {
        [*] --> PickTask: Worker nhận Task từ Queue
        PickTask --> UpdateStatusProcessing: Set status='PROCESSING'
        UpdateStatusProcessing --> CheckFileType: Loại file?

        CheckFileType --> ConvertPDF: File PDF
        ConvertPDF --> PreprocessImage: Output list ảnh các trang
        CheckFileType --> PreprocessImage: File Ảnh (JPG/PNG/TIFF)

        PreprocessImage --> DeskewDenoise: Chỉnh nghiêng & khử nhiễu
        DeskewDenoise --> TextDetection: Phát hiện vùng chứa chữ (Bounding Boxes)
        TextDetection --> CropLines: Crop ảnh theo từng dòng chữ
        CropLines --> VietOCRRecognition: Nhận dạng dòng chữ với VietOCR
        VietOCRRecognition --> MergeText: Ghép các dòng thành văn bản hoàn chỉnh
        MergeText --> ExtractMetadata: Bóc tách MSSV, Ngày tháng (Regex/Rules)
    }

    ExtractMetadata --> SaveDBResults: Lưu ocr_results & document_metadata vào PostgreSQL
    SaveDBResults --> UpdateStatusDone: Set document ocr_status='DONE'
    UpdateStatusDone --> IndexElasticsearch: Push văn bản & metadata vào Elasticsearch
    IndexElasticsearch --> [*]: Hoàn tất tiến trình OCR
```

---

## 2. Activity Diagram 2: Tiến trình Tìm kiếm & Lọc Tài liệu (Search & Filtering)

```mermaid
stateDiagram-v2
    [*] --> EnterKeyword: Người dùng nhập từ khóa tìm kiếm
    EnterKeyword --> SetFilters: Tùy chọn Bộ lọc (Danh mục, Ngày, Status)
    SetFilters --> ClickSearch: Click "Tìm kiếm"

    ClickSearch --> VerifyToken: FastAPI kiểm tra JWT Token
    VerifyToken --> TokenInvalid: Token không hợp lệ / Hết hạn
    TokenInvalid --> RedirectLogin: Chuyển hướng về trang Đăng nhập
    RedirectLogin --> [*]

    VerifyToken --> BuildESQuery: Token Hợp lệ -> Dựng Query DSL
    BuildESQuery --> ExecuteES: Gửi Query đến Elasticsearch Engine

    state ExecuteES {
        [*] --> MatchQuery: Tìm kiếm Multi-match (title, content)
        MatchQuery --> DiacriticFolding: Xử lý Tiếng Việt không dấu
        DiacriticFolding --> FuzzyMatch: Áp dụng Fuzziness (Lỗi OCR)
        FuzzyMatch --> ApplyFilters: Lọc theo Category, Date, Status
        ApplyFilters --> GenerateHighlight: Tạo snippet Highlight từ khóa
    }

    ExecuteES --> ProcessHits: Trả về danh sách Hits & Scores
    ProcessHits --> CheckResults: Có kết quả khớp không?

    CheckResults --> DisplayResults: CÓ -> Hiển thị danh sách kèm Highlight
    CheckResults --> DisplayEmpty: KHÔNG -> Hiển thị thông báo "Không tìm thấy"

    DisplayResults --> ClickDetail: User click chọn 1 tài liệu
    ClickDetail --> ViewDocDetail: Chuyển sang màn hình Chi tiết Tài liệu
    ViewDocDetail --> [*]
    DisplayEmpty --> [*]
```

---

## TODO

- [ ] Chuyển đổi sơ đồ sang dạng PlantUML nếu cần vẽ bản in chính thức.
- [ ] Bổ sung sơ đồ Activity cho quy trình Chỉnh sửa OCR và Quản lý User.

## References

- Architecture.md
- UseCase.md
- SequenceDiagram.md
