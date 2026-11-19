"""
backend/app/core/ilm.py — Index Lifecycle Management (ILM) & Index Templates
DocuCTSV — Hệ thống Số hóa & OCR Hồ sơ Sinh viên (Đại học Đà Lạt)

Chức năng:
1. Thiết lập chính sách Quản lý Vòng đời Chỉ mục (ILM Policy): Phân tầng Hot-Warm-Cold.
   - Hot Phase: Ghi nhận hồ sơ scan mới trong năm học hiện hành.
   - Warm Phase: Chuyển hồ sơ năm trước sang trạng thái Read-Only, thu nhỏ shard.
   - Cold Phase: Tự động nén tối đa (best_compression) và force-merge 1 segment cho hồ sơ sinh viên đã tốt nghiệp.
2. Đăng ký Composable Index Template tự động gắn ILM policy cho các index theo niên khóa (documents-2024, documents-2025,...).
"""

from typing import Any
from loguru import logger
from app.core.elasticsearch import INDEX_MAPPINGS, INDEX_SETTINGS, get_es_client, is_es_available

ILM_POLICY_NAME = "ctsv_ilm_policy"
TEMPLATE_NAME = "documents_template"

# ── Cấu hình Chính sách Vòng đời Chỉ mục (ILM Policy) ──────────────────────
ILM_POLICY_DEFINITION: dict[str, Any] = {
    "policy": {
        "phases": {
            # 1. Hot Phase: Đọc/ghi liên tục cho năm học hiện hành
            "hot": {
                "min_age": "0ms",
                "actions": {
                    "rollover": {
                        "max_age": "365d",
                        "max_primary_shard_size": "25gb",
                        "max_docs": 500000,
                    },
                    "set_priority": {
                        "priority": 100,
                    },
                },
            },
            # 2. Warm Phase: Chuyển sang chế độ chỉ đọc sau 1 năm
            "warm": {
                "min_age": "365d",
                "actions": {
                    "readonly": {},
                    "set_priority": {
                        "priority": 50,
                    },
                },
            },
            # 3. Cold Phase: Nén tối ưu dung lượng cho hồ sơ sinh viên đã ra trường (> 3 năm)
            "cold": {
                "min_age": "1095d",
                "actions": {
                    "forcemerge": {
                        "max_num_segments": 1,
                    },
                    "set_priority": {
                        "priority": 20,
                    },
                },
            },
            # 4. Delete Phase: Xóa an toàn sau thời hạn lưu trữ theo luật (10 năm)
            "delete": {
                "min_age": "3650d",
                "actions": {
                    "delete": {
                        "delete_searchable_snapshot": True,
                    },
                },
            },
        }
    }
}


async def init_ilm_policy_and_template() -> dict[str, Any]:
    """
    Khởi tạo hoặc đồng bộ ILM Policy và Index Template lên Elasticsearch cluster.
    """
    if not is_es_available():
        return {
            "status": "SKIPPED",
            "message": "Elasticsearch offline. Bỏ qua cấu hình ILM trong môi trường cơ sở dữ liệu Fallback.",
        }

    client = get_es_client()
    results: dict[str, Any] = {"ilm_policy": False, "index_template": False}

    try:
        # 1. Đăng ký ILM Policy
        await client.ilm.put_lifecycle(policy=ILM_POLICY_NAME, body=ILM_POLICY_DEFINITION)
        results["ilm_policy"] = True
        logger.info(f"Elasticsearch ILM Policy '{ILM_POLICY_NAME}' successfully registered.")

        # 2. Đăng ký Composable Index Template
        template_body = {
            "index_patterns": ["documents-*"],
            "template": {
                "settings": {
                    **INDEX_SETTINGS,
                    "index.lifecycle.name": ILM_POLICY_NAME,
                    "index.lifecycle.rollover_alias": "documents",
                    "index.codec": "best_compression",
                },
                "mappings": INDEX_MAPPINGS,
            },
            "priority": 200,
            "_meta": {
                "description": "Index template tự động áp dụng vòng đời Hot-Cold cho hồ sơ sinh viên ĐH Đà Lạt",
                "project": "DocuCTSV",
            },
        }
        await client.indices.put_index_template(name=TEMPLATE_NAME, body=template_body)
        results["index_template"] = True
        logger.info(f"Elasticsearch Index Template '{TEMPLATE_NAME}' successfully registered.")

    except Exception as exc:
        logger.warning(f"Could not setup ILM policy or Index Template: {exc}")
        results["error"] = str(exc)

    return results

