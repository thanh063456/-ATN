"""
scripts/kibana/setup_kibana_dashboard.py — Tự động triển khai Kibana Dashboard & Canvas Workpad

Tự động hóa kết nối với Kibana API để nhập file cấu hình `docuctsv_kibana_dashboard.ndjson`:
- API: POST /api/saved_objects/_import?overwrite=true
- Tạo Index Pattern: docuctsv_documents
- Nạp 4 Lens Visualizations (KPI Budget, Bar 8 Khoa, Donut Chính sách, Gauge OCR)
- Nạp Dashboard điều hành CTSV
- Nạp Canvas Workpad trình chiếu điều hành cho Ban Giám hiệu
"""
import os
import sys
from typing import Any
import urllib.request
import urllib.error

# Thiết lập encoding UTF-8 cho Windows console
if sys.platform == "win32" and hasattr(sys.stdout, "reconfigure"):
    getattr(sys.stdout, "reconfigure")(encoding="utf-8")

KIBANA_URL = os.getenv("KIBANA_URL", "http://localhost:5601")
NDJSON_PATH = os.path.join(os.path.dirname(__file__), "docuctsv_kibana_dashboard.ndjson")


def import_kibana_saved_objects(kibana_base_url: str = KIBANA_URL) -> bool:
    """Gửi yêu cầu import Saved Objects tới Kibana API."""
    if not os.path.exists(NDJSON_PATH):
        print(f"[ERROR] Không tìm thấy file NDJSON tại: {NDJSON_PATH}")
        return False

    print(f"[*] Đang kết nối tới Kibana tại: {kibana_base_url}...")
    import_url = f"{kibana_base_url}/api/saved_objects/_import?overwrite=true"

    try:
        with open(NDJSON_PATH, "rb") as f:
            file_data = f.read()

        # Multipart form-data payload cho Kibana
        boundary = "----DocuCtsvKibanaBoundaryX77"
        body = (
            f"--{boundary}\r\n"
            f'Content-Disposition: form-data; name="file"; filename="docuctsv_kibana_dashboard.ndjson"\r\n'
            f"Content-Type: application/ndjson\r\n\r\n"
        ).encode("utf-8") + file_data + f"\r\n--{boundary}--\r\n".encode("utf-8")

        req = urllib.request.Request(
            import_url,
            data=body,
            headers={
                "kbn-xsrf": "true",
                "Content-Type": f"multipart/form-data; boundary={boundary}",
            },
            method="POST",
        )

        with urllib.request.urlopen(req, timeout=10) as resp:
            status_code = resp.status
            resp_body = resp.read().decode("utf-8")
            print(f"[SUCCESS] Import thành công lên Kibana! HTTP {status_code}")
            print(f"  Chi tiết: {resp_body[:200]}...")
            return True

    except urllib.error.URLError as e:
        print(f"[NOTICE] Không thể kết nối trực tiếp Kibana lúc này ({e}).")
        print(f"  Bạn có thể import thủ công file sau vào Kibana UI (Stack Management -> Saved Objects -> Import):")
        print(f"  👉 {os.path.abspath(NDJSON_PATH)}")
        return False


if __name__ == "__main__":
    url_arg = sys.argv[1] if len(sys.argv) > 1 else KIBANA_URL
    import_kibana_saved_objects(url_arg)
