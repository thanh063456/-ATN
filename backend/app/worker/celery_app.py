"""
backend/app/worker/celery_app.py — Celery App Instance

Ref: ADR-011 trong .ai/DECISIONS.md
"""
from celery import Celery
from app.core.config import settings

celery_app = Celery(
    "ocr_tasks",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
)

celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="Asia/Ho_Chi_Minh",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=300,        # Max 5 phút cho 1 document
    task_soft_time_limit=240,   # Cảnh báo ở phút thứ 4
    worker_prefetch_multiplier=1,
    task_acks_late=True,
    broker_connection_retry_on_startup=True,
)
