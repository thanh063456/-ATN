import { apiClient, API_BASE_URL } from "./client";

export interface DocumentSummary {
  id: string;
  title: string;
  original_filename: string;
  file_type: string;
  file_size_bytes: number;
  ocr_status: "PENDING" | "PROCESSING" | "DONE" | "APPROVED" | "REJECTED" | "FAILED" | "SKIPPED";
  minio_object_key: string;
  created_at: string;
}

export interface DocumentListItem extends DocumentSummary {
  page_count?: number;
  category_id?: string;
  uploaded_by: string;
  is_deleted: boolean;
  updated_at: string;
  uploader_name?: string;
  uploader_mssv?: string;
  category_name?: string;
  confidence_score?: number;
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
  started_at?: string;
  completed_at?: string;
}

export interface DocumentMetadata {
  student_id?: string;
  student_name?: string;
  document_date?: string;
  document_number?: string;
  extra?: {
    class_name?: string;
    faculty?: string;
    document_type?: string;
    reason?: string;
    [key: string]: any;
  };
}

export interface DocumentDetail extends DocumentSummary {
  page_count?: number;
  category_id?: string;
  uploaded_by: string;
  is_deleted: boolean;
  updated_at: string;
  ocr_result?: OCRResult;
  processing_job?: ProcessingJob;
  metadata?: DocumentMetadata;
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
  verification_code: string;
  qr_payload: string;
  issued_by: string;
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
  categoryId?: string;
  search?: string;
}

export const documentsApi = {
  list: async (params?: ListDocumentsParams): Promise<DocumentListResponse> => {
    const res = await apiClient.get<DocumentListResponse>("/documents", {
      params: {
        page: params?.page || 1,
        page_size: params?.pageSize || 20,
        ocr_status: params?.ocrStatus,
        category_id: params?.categoryId,
        search: params?.search,
      },
    });
    return res.data;
  },

  upload: async (file: File, title?: string, categoryId?: string): Promise<UploadResponse> => {
    const formData = new FormData();
    formData.append("file", file);
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

  saveCorrection: async (id: string, correctedText: string): Promise<DocumentDetail> => {
    const res = await apiClient.put<DocumentDetail>(`/documents/${id}/ocr-correction`, {
      corrected_text: correctedText,
    });
    return res.data;
  },

  reprocessOCR: async (id: string): Promise<{ message: string; document_id: string; status: string }> => {
    const res = await apiClient.post(`/documents/${id}/reprocess-ocr`);
    return res.data;
  },

  triggerExtractFields: async (id: string): Promise<DocumentMetadata> => {
    const res = await apiClient.post<DocumentMetadata>(`/documents/${id}/extract-fields`);
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

  exportExcelUrl: (status?: string, categoryId?: string) => {
    const params = new URLSearchParams();
    if (status && status !== "ALL") params.append("ocr_status", status);
    if (categoryId) params.append("category_id", categoryId);
    return `${API_BASE_URL}/documents/export/excel?${params.toString()}`;
  },
};
