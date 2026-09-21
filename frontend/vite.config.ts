import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

/**
 * vite.config.ts — PLACEHOLDER
 * Sẽ được mở rộng ở Phase 8 (Frontend Implementation).
 *
 * Lưu ý quan trọng cho Docker:
 *   server.host: true  → bind ra 0.0.0.0 để truy cập từ máy host
 *   server.port: 3000  → khớp với port mapping trong docker-compose.yml
 */
export default defineConfig({
  plugins: [react()],
  server: {
    host: true,       // ← Bắt buộc khi chạy trong Docker container
    port: 3000,
    strictPort: true,
    // Proxy API calls sang backend để tránh CORS trong dev
    proxy: {
      "/api": {
        target: process.env.VITE_BACKEND_URL || "http://localhost:8000",
        changeOrigin: true,
      },
      "/health": {
        target: process.env.VITE_BACKEND_URL || "http://localhost:8000",
        changeOrigin: true,
      },
    },
  },
  build: {
    outDir: "dist",
    sourcemap: true,
  },
});
