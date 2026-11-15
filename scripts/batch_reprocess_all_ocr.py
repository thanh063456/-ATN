#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
scripts/batch_reprocess_all_ocr.py — Chạy lại toàn bộ OCR cho tất cả tài liệu trong CSDL

Quy trình:
1. Lấy danh sách tài liệu chưa xóa (is_deleted == False) từ PostgreSQL theo thứ tự mới nhất (created_at DESC).
2. Gọi hàm async_process_ocr(doc_id, engine="vietocr") để chạy pipeline hoàn chỉnh:
   - VietOCR quét toàn trang (full pages)
   - Tích hợp OpenCV Morphology phát hiện khung bảng
   - Tự động chuẩn hóa header (Số hiệu, Ngày tháng, Tiêu đề)
   - Trích xuất metadata và Smart Fields (bằng regex/admin dictionary siêu tốc 0.05s)
   - Tự động gắn nhãn (Auto-tags) và tính điểm ưu tiên
   - Cập nhật OCRResult, DocumentMetadata, Document.ocr_status = "DONE"
   - Đồng bộ sang Elasticsearch
3. Ghi nhận tiến độ thời gian thực ra file `batch_ocr_progress.json`.
4. Cơ chế chịu lỗi: Nếu 1 tài liệu lỗi, ghi log lỗi và tiếp tục xử lý các tài liệu còn lại.
5. Hỗ trợ Resume: Tự động bỏ qua các tài liệu đã hoàn thành trong lượt chạy nếu được bật cờ --resume.
"""

import argparse
import asyncio
import json
import os
import sys
import time
from datetime import datetime
from pathlib import Path

# Cấu hình UTF-8 cho Windows console
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

# Thêm backend vào sys.path
backend_path = Path(__file__).resolve().parent.parent / "backend"
sys.path.insert(0, str(backend_path))

from loguru import logger
from sqlalchemy import select

from app.core.cache import app_cache
from app.core.config import settings
from app.core.database import AsyncSessionLocal
from app.models.documents import Document
from app.worker.tasks import async_process_ocr

PROGRESS_FILE = Path(__file__).resolve().parent.parent / "batch_ocr_progress.json"


def save_progress(data: dict) -> None:
    """Ghi dữ liệu tiến độ vào file JSON nguyên tử (atomic write)."""
    tmp_file = PROGRESS_FILE.with_suffix(".json.tmp")
    try:
        with open(tmp_file, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        tmp_file.replace(PROGRESS_FILE)
    except Exception as e:
        logger.warning(f"Không thể ghi file tiến độ {PROGRESS_FILE}: {e}")


def load_previous_progress() -> dict | None:
    """Đọc dữ liệu tiến độ lần chạy trước nếu có."""
    if PROGRESS_FILE.exists():
        try:
            with open(PROGRESS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return None
    return None


async def run_batch_reprocess(
    engine: str = "vietocr",
    limit: int | None = None,
    resume: bool = True,
    delay: float = 0.2,
    skip_ids: list[str] | None = None,
    ai_provider: str = "regex",
) -> None:
    # Cấu hình AI Provider cho smart fields (mặc định dùng regex/admin-dict để siêu tốc và không nghẽn)
    if ai_provider in ("regex", "none", "rule_based"):
        settings.ai_provider = "none"
    else:
        settings.ai_provider = ai_provider

    logger.info("=" * 70)
    logger.info("BẮT ĐẦU QUY TRÌNH CHẠY LẠI TOÀN BỘ OCR CHO TẤT CẢ TÀI LIỆU")
    logger.info(f"Engine: {engine} | Resume: {resume} | AI Provider: {settings.ai_provider} | Limit: {limit or 'Tất cả'}")
    logger.info("=" * 70)

    # 1. Truy vấn danh sách tài liệu từ PostgreSQL
    async with AsyncSessionLocal() as session:
        stmt = (
            select(Document.id, Document.title, Document.original_filename, Document.created_at, Document.page_count)
            .where(Document.is_deleted == False)
            .order_by(Document.created_at.desc())
        )
        res = await session.execute(stmt)
        all_docs = res.all()

    total_in_db = len(all_docs)
    logger.info(f"Tìm thấy tổng cộng {total_in_db} tài liệu active trong CSDL.")

    if limit and limit > 0:
        all_docs = all_docs[:limit]
        logger.info(f"Giới hạn xử lý {len(all_docs)} tài liệu theo tham số --limit.")

    skip_set = set(skip_ids or [])
    completed_ids = set()

    # Nếu bật resume, tải danh sách đã xử lý thành công trước đó
    if resume:
        prev_data = load_previous_progress()
        if prev_data and "completed_ids" in prev_data:
            completed_ids = set(prev_data.get("completed_ids", []))
            logger.info(f"Chế độ Resume: Đã tìm thấy {len(completed_ids)} tài liệu đã hoàn thành trước đó.")

    total_tasks = len(all_docs)
    successful_count = len(completed_ids)
    failed_docs: list[dict] = []
    recent_logs: list[dict] = []

    start_time = time.time()
    progress_state = {
        "status": "RUNNING",
        "engine": engine,
        "total": total_tasks,
        "processed": successful_count,
        "successful": successful_count,
        "failed": 0,
        "skipped": 0,
        "current_index": 0,
        "current_doc_id": "",
        "current_doc_title": "",
        "current_doc_filename": "",
        "started_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat(),
        "elapsed_seconds": 0.0,
        "avg_time_per_doc": 0.0,
        "estimated_remaining_seconds": 0.0,
        "completed_ids": list(completed_ids),
        "failed_documents": [],
        "recent_processed": [],
    }
    save_progress(progress_state)

    processed_in_session = 0
    total_session_doc_time = 0.0

    try:
        for idx, doc in enumerate(all_docs, start=1):
            doc_id_str = str(doc.id)

            # Kiểm tra bỏ qua nếu đã hoàn thành (resume) hoặc có trong skip_set
            if doc_id_str in completed_ids:
                logger.info(f"[{idx}/{total_tasks}] BỎ QUA (Đã hoàn thành): {doc.title} ({doc_id_str})")
                progress_state["skipped"] += 1
                continue

            if doc_id_str in skip_set:
                logger.info(f"[{idx}/{total_tasks}] BỎ QUA (Theo skip list): {doc.title} ({doc_id_str})")
                progress_state["skipped"] += 1
                continue

            doc_title = doc.title or doc.original_filename or "Không tên"
            logger.info("-" * 60)
            logger.info(f"[{idx}/{total_tasks}] ({idx/total_tasks*100:.1f}%) Đang xử lý: {doc_title}")
            logger.info(f"ID: {doc_id_str} | File: {doc.original_filename} | Số trang: {doc.page_count or 1}")

            progress_state["current_index"] = idx
            progress_state["current_doc_id"] = doc_id_str
            progress_state["current_doc_title"] = doc_title
            progress_state["current_doc_filename"] = doc.original_filename or ""
            progress_state["updated_at"] = datetime.now().isoformat()
            save_progress(progress_state)

            t_doc_start = time.perf_counter()
            doc_success = False
            err_msg = None

            try:
                # Chạy pipeline OCR hoàn chỉnh
                res = await async_process_ocr(doc_id_str, engine=engine)
                doc_success = True
                duration_sec = time.perf_counter() - t_doc_start
                logger.info(
                    f"✓ HOÀN THÀNH ({duration_sec:.1f}s): {doc_title} "
                    f"| Confidence: {res.get('confidence', 0):.2f}"
                )
            except Exception as e:
                duration_sec = time.perf_counter() - t_doc_start
                err_msg = f"{type(e).__name__}: {str(e)}"
                logger.error(f"✗ LỖI KHI XỬ LÝ ({duration_sec:.1f}s): {doc_title} -> {err_msg}")
                failed_docs.append({
                    "id": doc_id_str,
                    "title": doc_title,
                    "filename": doc.original_filename,
                    "error": err_msg,
                    "time": datetime.now().isoformat(),
                })

            # Invalidate in-memory cache
            try:
                app_cache.invalidate()
            except Exception:
                pass

            # Cập nhật thống kê
            processed_in_session += 1
            total_session_doc_time += duration_sec
            avg_time = total_session_doc_time / processed_in_session
            remaining_tasks = total_tasks - (successful_count + 1 if doc_success else successful_count)
            est_remaining_sec = max(0.0, avg_time * remaining_tasks)
            elapsed_sec = time.time() - start_time

            if doc_success:
                completed_ids.add(doc_id_str)
                successful_count += 1
                recent_logs.insert(0, {
                    "id": doc_id_str,
                    "title": doc_title,
                    "status": "SUCCESS",
                    "duration_sec": round(duration_sec, 2),
                    "timestamp": datetime.now().isoformat(),
                })
            else:
                recent_logs.insert(0, {
                    "id": doc_id_str,
                    "title": doc_title,
                    "status": "FAILED",
                    "error": err_msg,
                    "duration_sec": round(duration_sec, 2),
                    "timestamp": datetime.now().isoformat(),
                })

            # Giữ tối đa 20 log gần nhất
            recent_logs = recent_logs[:20]

            progress_state.update({
                "processed": successful_count + len(failed_docs),
                "successful": successful_count,
                "failed": len(failed_docs),
                "elapsed_seconds": round(elapsed_sec, 1),
                "avg_time_per_doc": round(avg_time, 2),
                "estimated_remaining_seconds": round(est_remaining_sec, 1),
                "updated_at": datetime.now().isoformat(),
                "completed_ids": list(completed_ids),
                "failed_documents": failed_docs,
                "recent_processed": recent_logs,
            })
            save_progress(progress_state)

            if delay > 0 and idx < total_tasks:
                await asyncio.sleep(delay)

    except (KeyboardInterrupt, asyncio.CancelledError):
        logger.warning("\nTiến trình bị hủy bởi người dùng hoặc hệ thống.")
        progress_state["status"] = "STOPPED"
        progress_state["updated_at"] = datetime.now().isoformat()
        save_progress(progress_state)
        return
    except Exception as fatal_err:
        logger.exception(f"Lỗi nghiêm trọng trong vòng lặp batch: {fatal_err}")
        progress_state["status"] = "ERROR"
        progress_state["error"] = str(fatal_err)
        progress_state["updated_at"] = datetime.now().isoformat()
        save_progress(progress_state)
        raise fatal_err

    # Hoàn thành tất cả
    total_time = time.time() - start_time
    progress_state["status"] = "COMPLETED"
    progress_state["completed_at"] = datetime.now().isoformat()
    progress_state["elapsed_seconds"] = round(total_time, 1)
    progress_state["updated_at"] = datetime.now().isoformat()
    save_progress(progress_state)

    logger.info("=" * 70)
    logger.info("HOÀN THÀNH QUY TRÌNH CHẠY LẠI OCR TOÀN BỘ TÀI LIỆU")
    logger.info(f"Tổng tài liệu: {total_tasks}")
    logger.info(f"Thành công: {successful_count}")
    logger.info(f"Thất bại: {len(failed_docs)}")
    logger.info(f"Tổng thời gian: {total_time:.1f}s (~{total_time/60:.1f} phút)")
    if processed_in_session > 0:
        logger.info(f"Thời gian trung bình: {total_session_doc_time/processed_in_session:.1f}s / tài liệu")
    logger.info("=" * 70)


def main():
    parser = argparse.ArgumentParser(description="Chạy lại OCR toàn bộ tài liệu trong CSDL.")
    parser.add_argument("--engine", type=str, default="vietocr", help="OCR engine (vietocr, trocr). Mặc định: vietocr")
    parser.add_argument("--limit", type=int, default=None, help="Giới hạn số lượng tài liệu xử lý (Mặc định: tất cả)")
    parser.add_argument("--no-resume", action="store_true", help="Không tải lại tiến trình cũ, chạy lại từ đầu")
    parser.add_argument("--delay", type=float, default=0.2, help="Thời gian chờ giữa 2 tài liệu (giây)")
    parser.add_argument("--skip", type=str, default="", help="Danh sách ID tài liệu bỏ qua, phân cách bởi dấu phẩy")
    parser.add_argument("--ai-provider", type=str, default="regex", help="AI provider cho smart fields (regex, ollama, gemini)")
    args = parser.parse_args()

    skip_list = [s.strip() for s in args.skip.split(",") if s.strip()]

    asyncio.run(run_batch_reprocess(
        engine=args.engine,
        limit=args.limit,
        resume=not args.no_resume,
        delay=args.delay,
        skip_ids=skip_list,
        ai_provider=args.ai_provider,
    ))


if __name__ == "__main__":
    main()
