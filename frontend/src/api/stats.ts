import { apiClient } from "./client";

export interface CategoryStat {
  name: string;
  code: string;
  count: number;
}

export interface RecentDocStat {
  id: string;
  title: string;
  category: string;
  student_name?: string;
  student_id?: string;
  file_type: string;
  ocr_status: string;
  confidence_score?: number;
  created_at: string;
}

export interface DashboardStatsResponse {
  total_documents: number;
  pending_count: number;
  done_count: number;
  approved_count: number;
  rejected_count: number;
  failed_count: number;
  avg_confidence: number;
  avg_processing_time_ms: number;
  corrected_count: number;
  cer_estimation: number;
  category_breakdown: CategoryStat[];
  recent_documents: RecentDocStat[];
}

export const statsApi = {
  getDashboardStats: async (): Promise<DashboardStatsResponse> => {
    const res = await apiClient.get<DashboardStatsResponse>("/stats/dashboard");
    return res.data;
  },
};
