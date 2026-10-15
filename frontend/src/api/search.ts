import { apiClient } from "./client";

export interface SearchHit {
  document_id: string;
  title: string;
  content_snippet?: string;
  category_code?: string;
  category_name?: string;
  doc_type_code?: string;
  doc_type_name?: string;
  doc_group?: string;
  doc_subtype?: string;
  doc_type_confidence?: number;
  doc_type_source?: string;
  subject?: string;
  issuing_unit?: string;
  ocr_scope?: string;
  page_count?: number;
  pages_ocr?: number;
  needs_review?: boolean;
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

export interface FacetItem {
  code?: string;
  category?: string;
  status?: string;
  tag?: string;
  year?: string;
  count: number;
}

export interface SearchResponse {
  query: string;
  total_hits: number;
  page: number;
  page_size: number;
  total_pages: number;
  took_ms: number;
  facets?: {
    categories?: FacetItem[];
    statuses?: FacetItem[];
    tags?: FacetItem[];
    years?: FacetItem[];
    doc_type_code?: FacetItem[];
    doc_group?: FacetItem[];
    [key: string]: any;
  };
  results: SearchHit[];
}

export interface SearchParams {
  q: string;
  category_code?: string;
  doc_type_code?: string;
  doc_group?: string;
  ocr_scope?: string;
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
