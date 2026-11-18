import { apiClient, API_BASE_URL } from "./client";

export interface DocumentSummary {
  id: string;
  title: string;
  original_filename: string;
  file_type: string;
  file_size_bytes: number;
  ocr_status: "PENDING" | "PROCESSING" | "DONE" | "APPROVED" | "REJECTED" | "FAILED" | "SKIPPED";
  minio_object_key?: string;
  is_public?: boolean;
  created_at: string;
}

export interface ApprovalInfo {
  status: string;
  action: string;
  approver_id?: string;
  approver_name?: string;
  approver_role?: string;
  approver_role_label?: string;
  timestamp?: string;
  note?: string;
}

export interface DocumentListItem extends DocumentSummary {
  page_count?: number;
  category_id?: string;
  uploaded_by?: string;
  is_deleted?: boolean;
  updated_at?: string;
  uploader_name?: string;
  uploader_mssv?: string;
  category_name?: string;
  category_code?: string;
  confidence_score?: number;
  ocr_confidence?: number;
  student_id?: string;
  student_name?: string;
  document_number?: string;
  tags?: string[];
  priority_score?: number;
  ocr_progress?: number;  // 0-100 tiến độ OCR thực tế
  approval_info?: ApprovalInfo;
}

export interface DocumentListResponse {
  items: DocumentListItem[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

export interface OCRResult {
  id: string;
  document_id: string;
  is_latest: boolean;
  raw_text?: string;
  corrected_text?: string;
  confidence_score?: number;
  ocr_engine: string;
  ocr_engine_version?: string;
  status?: "DONE" | "FAILED" | "RUNNING" | string;
  error_message?: string;
  is_corrected: boolean;
  corrected_by?: string;
  corrected_at?: string;
  processing_time_ms?: number;
  created_at: string;
}

export interface ProcessingJob {
  id: string;
  status: "PENDING" | "RUNNING" | "SUCCESS" | "FAILED";
  error_message?: string;
  retry_count: number;
  ocr_progress: number;  // 0-100
  started_at?: string;
  completed_at?: string;
}

export interface DocumentMetadata {
  student_id?: string;
  student_name?: string;
  document_date?: string;
  document_number?: string;
  tags?: string[];
  priority_score?: number;
  extra?: {
    class_name?: string;
    faculty?: string;
    document_type?: string;
    reason?: string;
    tags?: string[];
    [key: string]: any;
  };
}

export interface DocumentDetail extends DocumentSummary {
  page_count?: number;
  category_id?: string;
  category?: { id: string; code: string; name: string };
  category_name?: string;
  category_code?: string;
  uploaded_by?: string;
  is_deleted: boolean;
  updated_at: string;
  ocr_result?: OCRResult;
  all_ocr_results?: OCRResult[];
  processing_job?: ProcessingJob;
  metadata?: DocumentMetadata;
  tags?: string[];
  priority_score?: number;
  file_url?: string;
  is_public?: boolean;
  approval_info?: ApprovalInfo;
}

export interface TagSummaryItem {
  tag: string;
  count: number;
  priority: number;
  color: string;
  category: string;
}

export interface TagSummaryResponse {
  items: TagSummaryItem[];
  total_tags: number;
}

export interface VerificationData {
  is_valid: boolean;
  document_id: string;
  title: string;
  original_filename: string;
  ocr_status: string;
  student_name?: string;
  student_id?: string;
  approved_at?: string;
  approved_by_name?: string;
  approved_by_role?: string;
  approved_by_role_label?: string;
  verification_code: string;
  qr_payload: string;
  issued_by: string;
}

export interface DocumentNotificationItem {
  id: string;
  document_id: string;
  document_title: string;
  action: string;
  status: string;
  actor_id?: string;
  actor_name: string;
  actor_role: string;
  actor_role_label: string;
  message: string;
  created_at: string;
  is_read?: boolean;
}

export interface DocumentNotificationsResponse {
  items: DocumentNotificationItem[];
  total: number;
  unread_count: number;
}

export interface UploadResponse {
  id: string;
  title: string;
  original_filename: string;
  file_type: string;
  file_size_bytes: number;
  ocr_status: string;
  minio_object_key: string;
  job_id?: string;
  celery_task_id?: string;
  message: string;
  created_at: string;
}

export interface ListDocumentsParams {
  page?: number;
  pageSize?: number;
  ocrStatus?: string;
  approvalStatus?: string;
  categoryId?: string;
  tag?: string;
  search?: string;
  onlyMyUploads?: boolean;
}

export interface AIRefineResponse {
  original_text: string;
  refined_text: string;
  provider: string;
  model: string;
  success: boolean;
  message?: string;
}

export interface AIExtractResponse {
  student_name?: string;
  student_id?: string;
  class_name?: string;
  faculty?: string;
  document_type?: string;
  document_number?: string;
  reason?: string;
  amount?: string;
  document_date?: string;
  tags?: string[];
  priority_score?: number;
  summary?: string;
  suggested_action?: string;
  provider?: string;
  model?: string;
  confidence_score: number;
}

export interface ModelBenchmarkItem {
  engine_name: string;
  text: string;
  confidence: number;
  inference_time_seconds: number;
  char_count: number;
  word_count: number;
  status: string;
}

export interface ModelComparisonResponse {
  document_id: string;
  filename: string;
  comparison: {
    vietocr?: ModelBenchmarkItem;
    trocr?: ModelBenchmarkItem;
    tesseract?: ModelBenchmarkItem;
    [key: string]: any;
  };
}

export const documentsApi = {
  list: async (params?: ListDocumentsParams): Promise<DocumentListResponse> => {
    const res = await apiClient.get<DocumentListResponse>("/documents", {
      params: {
        page: params?.page || 1,
        page_size: params?.pageSize || 20,
        ocr_status: params?.ocrStatus && params.ocrStatus !== "ALL" ? params.ocrStatus : undefined,
        approval_status: params?.approvalStatus && params.approvalStatus !== "ALL" ? params.approvalStatus : undefined,
        category_id: params?.categoryId,
        tag: params?.tag && params.tag !== "ALL" ? params.tag : undefined,
        search: params?.search?.trim() || undefined,
        only_my_uploads: params?.onlyMyUploads || undefined,
      },
    });
    return res.data;
  },

  upload: async (
    file: File | File[],
    title?: string,
    categoryId?: string,
    mergeImages?: boolean
  ): Promise<UploadResponse> => {
    const formData = new FormData();
    if (Array.isArray(file)) {
      file.forEach((f) => formData.append("files", f));
      if (mergeImages !== undefined) {
        formData.append("merge_images", String(mergeImages));
      }
    } else {
      formData.append("file", file);
    }
    if (title) formData.append("title", title);
    if (categoryId) formData.append("category_id", categoryId);

    const res = await apiClient.post<UploadResponse>("/documents/upload", formData, {
      headers: { "Content-Type": "multipart/form-data" },
    });
    return res.data;
  },

  getById: async (id: string): Promise<DocumentDetail> => {
    const res = await apiClient.get<DocumentDetail>(`/documents/${id}`);
    return res.data;
  },

  saveCorrection: async (id: string, correctedText: string, engine?: string): Promise<DocumentDetail> => {
    const res = await apiClient.put<DocumentDetail>(`/documents/${id}/ocr-correction`, {
      corrected_text: correctedText,
      engine: engine,
    });
    return res.data;
  },

  getEngineOcrResult: async (id: string, engine: string): Promise<OCRResult> => {
    const res = await apiClient.get<OCRResult>(`/documents/${id}/ocr-results/${engine}`);
    return res.data;
  },

  reprocessOCR: async (id: string, engine?: string): Promise<{ message: string; document_id: string; status: string }> => {
    const url = engine ? `/documents/${id}/reprocess-ocr?engine=${engine}` : `/documents/${id}/reprocess-ocr`;
    const res = await apiClient.post(url);
    return res.data;
  },

  triggerExtractFields: async (id: string): Promise<DocumentMetadata> => {
    const res = await apiClient.post<DocumentMetadata>(`/documents/${id}/extract-fields`);
    return res.data;
  },

  aiRefine: async (id: string, text?: string): Promise<AIRefineResponse> => {
    const res = await apiClient.post<AIRefineResponse>(`/documents/${id}/ai-refine`, {
      text: text || null,
    });
    return res.data;
  },

  aiExtract: async (id: string): Promise<AIExtractResponse> => {
    const res = await apiClient.post<AIExtractResponse>(`/documents/${id}/ai-extract`);
    return res.data;
  },

  compareModels: async (id: string): Promise<ModelComparisonResponse> => {
    const res = await apiClient.post<ModelComparisonResponse>(`/documents/${id}/compare-models`);
    return res.data;
  },

  getVerification: async (id: string): Promise<VerificationData> => {
    const res = await apiClient.get<VerificationData>(`/documents/${id}/verification`);
    return res.data;
  },

  getPublicVerification: async (id: string): Promise<VerificationData> => {
    const res = await apiClient.get<VerificationData>(`/verify/${id}`);
    return res.data;
  },

  approve: async (id: string): Promise<DocumentDetail> => {
    const res = await apiClient.patch<DocumentDetail>(`/documents/${id}/approve`);
    return res.data;
  },

  reject: async (id: string): Promise<DocumentDetail> => {
    const res = await apiClient.patch<DocumentDetail>(`/documents/${id}/reject`);
    return res.data;
  },

  setPublic: async (id: string, isPublic: boolean): Promise<DocumentDetail> => {
    const res = await apiClient.patch<DocumentDetail>(`/documents/${id}/public`, { is_public: isPublic });
    return res.data;
  },

  overrideType: async (id: string, category_code: string): Promise<any> => {
    const res = await apiClient.patch(`/documents/${id}/type`, { category_code });
    return res.data;
  },

  triggerOcrFull: async (id: string): Promise<any> => {
    const res = await apiClient.post(`/documents/${id}/ocr-full`);
    return res.data;
  },

  getTagsSummary: async (): Promise<TagSummaryResponse> => {
    const res = await apiClient.get<TagSummaryResponse>("/documents/tags/summary");
    return res.data;
  },

  updateTags: async (id: string, tags: string[]): Promise<DocumentDetail> => {
    const res = await apiClient.put<DocumentDetail>(`/documents/${id}/tags`, { tags });
    return res.data;
  },

  autoTag: async (id: string, engine?: string): Promise<DocumentDetail> => {
    const params = engine ? `?engine=${encodeURIComponent(engine)}` : "";
    const res = await apiClient.post<DocumentDetail>(`/documents/${id}/auto-tag${params}`);
    return res.data;
  },

  getNotifications: async (limit = 20): Promise<DocumentNotificationsResponse> => {
    const res = await apiClient.get<DocumentNotificationsResponse>("/documents/notifications", {
      params: { limit },
    });
    return res.data;
  },

  exportExcelUrl: (status?: string, categoryId?: string) => {
    const params = new URLSearchParams();
    if (status && status !== "ALL") params.append("ocr_status", status);
    if (categoryId) params.append("category_id", categoryId);
    return `${API_BASE_URL}/documents/export/excel?${params.toString()}`;
  },

  detectStamp: async (id: string, page = 0): Promise<StampDetectionData> => {
    const res = await apiClient.post<StampDetectionData>(`/documents/${id}/detect-stamp?page=${page}`);
    return res.data;
  },

  extractTables: async (id: string, page?: number, ocrCells = true): Promise<TableExtractionData> => {
    const url =
      page !== undefined && page >= 0
        ? `/documents/${id}/extract-tables?page=${page}&ocr_cells=${ocrCells}`
        : `/documents/${id}/extract-tables?ocr_cells=${ocrCells}`;
    const res = await apiClient.post<TableExtractionData>(url);
    return res.data;
  },

  getCategories: async (): Promise<CategoryAdminItem[]> => {
    const res = await apiClient.get<CategoryAdminItem[]>("/documents/categories");
    return res.data;
  },

  createCategory: async (payload: { name: string; code: string; description?: string }): Promise<CategoryAdminItem> => {
    const res = await apiClient.post<CategoryAdminItem>("/documents/categories", payload);
    return res.data;
  },

  toggleCategoryStatus: async (id: string): Promise<{ id: string; is_active: boolean }> => {
    const res = await apiClient.patch<{ id: string; is_active: boolean }>(`/documents/categories/${id}/status`);
    return res.data;
  },
};

export interface CategoryAdminItem {
  id: string;
  name: string;
  code: string;
  description: string;
  is_active: boolean;
  doc_count: number;
}

export interface DetectedStampItem {
  bbox: [number, number, number, number];
  confidence: number;
  area: number;
  aspect_ratio: number;
  image_base64: string;
  is_circular: boolean;
}

export interface StampDetectionData {
  document_id: string;
  has_stamp: boolean;
  stamps: DetectedStampItem[];
  cleaned_image_base64: string;
  red_pixel_ratio: number;
}

export interface TableCellItem {
  row_idx: number;
  col_idx: number;
  bbox: [number, number, number, number];
  text: string;
}

export interface ExtractedTableItem {
  table_idx: number;
  page_num?: number;
  bbox: [number, number, number, number];
  headers: string[];
  rows: string[][];
  cells: TableCellItem[];
  row_count: number;
  col_count: number;
  markdown: string;
  html: string;
}

export interface TableExtractionData {
  document_id: string;
  has_table: boolean;
  tables: ExtractedTableItem[];
  total_tables: number;
  total_cells: number;
}

