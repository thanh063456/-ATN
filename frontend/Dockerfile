# =============================================================
# frontend/Dockerfile — Student-Document-OCR
# Node 20 (LTS) · React 18 · Vite 5 · TypeScript
# =============================================================
# Dev-only image — Vite dev server với HMR
# Production sẽ dùng nginx image riêng (Phase 8)
# =============================================================
FROM node:20-alpine

WORKDIR /app

# Cài curl để Docker healthcheck hoạt động
RUN apk add --no-cache curl

# Cài dependencies trước (tận dụng layer cache)
# package.json và lock file được copy riêng
COPY package.json package-lock.json* ./
RUN npm ci --prefer-offline 2>/dev/null || npm install

# Copy source code
# (trong dev, thư mục này được mount qua volume nên ít dùng bước này)
COPY . .

EXPOSE 3000

# Vite dev server:
# --host → bind ra 0.0.0.0 để truy cập từ máy host qua Docker port mapping
# --port → khớp với port mapping trong docker-compose.yml
CMD ["npm", "run", "dev", "--", "--host", "--port", "3000"]
