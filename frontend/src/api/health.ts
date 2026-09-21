import axios from "axios";

export interface ServiceHealth {
  status: "ok" | "degraded" | "error";
  latency_ms?: number | null;
  cluster_status?: string;
  error?: string;
}

export interface HealthResponse {
  status: "ok" | "degraded";
  env: string;
  services: {
    postgres: ServiceHealth;
    elasticsearch: ServiceHealth;
    minio: ServiceHealth;
    redis: ServiceHealth;
  };
}

export const healthApi = {
  check: async (): Promise<HealthResponse> => {
    // Health endpoint is mounted at root /health
    const baseUrl = import.meta.env.VITE_API_BASE_URL?.replace("/api/v1", "") || "http://localhost:8000";
    const res = await axios.get<HealthResponse>(`${baseUrl}/health`, {
      validateStatus: (status) => status < 600, // Accepts 200 and 503
    });
    return res.data;
  },
};
