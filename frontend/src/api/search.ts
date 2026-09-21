import { apiClient } from "./client";

export interface SearchHit {
  document_id: string;
  title: string;
  content_snippet?: string;
  category_code?: string;
  category_name?: string;
  student_id?: string;
  student_name?: string;
  document_date?: string;
  document_number?: string;
  ocr_status: string;
  ocr_confidence?: number;
  score: number;
  highlights: Record<string, string[]>;
  created_at?: string;
}

export interface SearchResponse {
  query: string;
  total_hits: number;
  page: number;
  page_size: number;
  total_pages: number;
  took_ms: number;
  results: SearchHit[];
}

export interface SearchParams {
  q: string;
  category_code?: string;
  ocr_status?: string;
  date_from?: string;
  date_to?: string;
  fuzzy?: boolean;
  page?: number;
  page_size?: number;
}

export const searchApi = {
  search: async (params: SearchParams): Promise<SearchResponse> => {
    const res = await apiClient.get<SearchResponse>("/search", { params });
    return res.data;
  },
};
