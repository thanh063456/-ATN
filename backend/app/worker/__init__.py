from app.worker.celery_app import celery_app
from app.worker.tasks import async_process_ocr, process_ocr_task

# Alias app = celery_app for celery CLI
app = celery_app

__all__ = ["celery_app", "app", "async_process_ocr", "process_ocr_task"]
