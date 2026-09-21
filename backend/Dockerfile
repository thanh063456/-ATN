# =============================================================
# backend/Dockerfile — Student-Document-OCR
# Python 3.11 · FastAPI · Uvicorn
# =============================================================
# Stage 1: builder — cài dependencies vào virtualenv riêng
# =============================================================
FROM python:3.11-slim AS builder

# Không tạo .pyc, không buffer stdout/stderr
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /build

# Cài curl + các system library cần thiết
# - libpq-dev: psycopg2
# - poppler-utils: pdf2image
# - libgl1: opencv
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    gcc \
    libpq-dev \
    poppler-utils \
    libgl1 \
    && rm -rf /var/lib/apt/lists/*

# Tạo virtualenv
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Cài dependencies trước (tận dụng Docker layer cache)
# requirements.txt được copy riêng để cache lại khi code thay đổi
COPY requirements.txt .
RUN pip install --upgrade pip && \
    pip install -r requirements.txt

# =============================================================
# Stage 2: runtime
# =============================================================
FROM python:3.11-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/opt/venv/bin:$PATH"

WORKDIR /app

# Chỉ cài runtime system libs (không cần gcc nữa)
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    libpq5 \
    poppler-utils \
    libgl1 \
    && rm -rf /var/lib/apt/lists/*

# Copy virtualenv từ builder stage
COPY --from=builder /opt/venv /opt/venv

# Copy source code
# (trong dev, thư mục này được mount qua volume nên thực tế ít dùng)
COPY . .

EXPOSE 8000

# Dev: --reload để hot-reload khi thay đổi code (kết hợp với volume mount)
# Production: bỏ --reload, tăng --workers
CMD ["uvicorn", "app.main:app", \
     "--host", "0.0.0.0", \
     "--port", "8000", \
     "--reload", \
     "--log-level", "info"]
