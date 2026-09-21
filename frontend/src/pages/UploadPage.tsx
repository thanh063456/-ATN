import React, { useState, useRef, useCallback, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import {
  UploadCloud,
  CheckCircle2,
  AlertCircle,
  X,
  Sparkles,
  ArrowRight,
  Clock,
  Loader2,
  Plus,
  Trash2,
  FileText,
  Image,
  ClipboardPaste,
  Camera,
} from "lucide-react";
import { Card } from "../components/common/Card";
import { Button } from "../components/common/Button";
import { CameraCaptureModal } from "../components/common/CameraCaptureModal";
import { documentsApi, UploadResponse } from "../api/documents";
import { useToastStore } from "../stores/useToastStore";

const ALLOWED_EXTENSIONS = ["pdf", "jpg", "jpeg", "png", "tiff"];
const MAX_SIZE_MB = 50;

type FileStatus = "pending" | "uploading" | "success" | "error";

interface QueuedFile {
  id: string;
  file: File;
  title: string;
  category: string;
  status: FileStatus;
  progress: number;
  result?: UploadResponse;
  error?: string;
}

const getFileIcon = (filename: string) => {
  const ext = filename.split(".").pop()?.toLowerCase();
  if (ext === "pdf") return <FileText size={20} color="var(--danger-500)" />;
  return <Image size={20} color="var(--primary-500)" />;
};

const formatSize = (bytes: number) => {
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(0)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(2)} MB`;
};

const StatusBadge: React.FC<{ status: FileStatus; progress: number }> = ({ status, progress }) => {
  const styles: Record<FileStatus, React.CSSProperties> = {
    pending: { backgroundColor: "#f3f4f6", color: "#6b7280" },
    uploading: { backgroundColor: "var(--primary-50)", color: "var(--primary-700)" },
    success: { backgroundColor: "#d1fae5", color: "#065f46" },
    error: { backgroundColor: "#fee2e2", color: "#991b1b" },
  };
  const labels: Record<FileStatus, string> = {
    pending: "Chờ upload",
    uploading: `Đang tải ${progress}%`,
    success: "Hoàn thành",
    error: "Lỗi",
  };
  const icons: Record<FileStatus, React.ReactNode> = {
    pending: <Clock size={12} />,
    uploading: <Loader2 size={12} style={{ animation: "spin 1s linear infinite" }} />,
    success: <CheckCircle2 size={12} />,
    error: <AlertCircle size={12} />,
  };

  return (
    <span
      style={{
        ...styles[status],
        display: "inline-flex",
        alignItems: "center",
        gap: "4px",
        padding: "2px 8px",
        borderRadius: "9999px",
        fontSize: "0.7rem",
        fontWeight: 600,
        whiteSpace: "nowrap",
      }}
    >
      {icons[status]}
      {labels[status]}
    </span>
  );
};

export const UploadPage: React.FC = () => {
  const navigate = useNavigate();
  const { addToast } = useToastStore();
  const fileInputRef = useRef<HTMLInputElement | null>(null);
  const [isDragging, setIsDragging] = useState(false);
  const [isCameraOpen, setIsCameraOpen] = useState(false);
  const [queue, setQueue] = useState<QueuedFile[]>([]);
  const [isRunning, setIsRunning] = useState(false);
  const [globalCategory, setGlobalCategory] = useState("");

  const validateAndAdd = useCallback(
    (files: FileList | File[]) => {
      const arr = Array.from(files);
      const newItems: QueuedFile[] = [];
      const errors: string[] = [];

      for (const file of arr) {
        const ext = file.name.split(".").pop()?.toLowerCase() || "";
        if (!ALLOWED_EXTENSIONS.includes(ext)) {
          errors.push(`"${file.name}" — định dạng .${ext} không được hỗ trợ.`);
          continue;
        }
        if (file.size > MAX_SIZE_MB * 1024 * 1024) {
          errors.push(`"${file.name}" — vượt quá ${MAX_SIZE_MB}MB.`);
          continue;
        }
        // skip duplicates
        const alreadyIn = queue.some((q) => q.file.name === file.name && q.file.size === file.size);
        if (alreadyIn) continue;

        newItems.push({
          id: `${Date.now()}-${Math.random()}`,
          file,
          title: file.name.replace(/\.[^/.]+$/, ""),
          category: globalCategory,
          status: "pending",
          progress: 0,
        });
      }

      if (errors.length > 0) {
        addToast({ type: "error", title: "Một số file bị bỏ qua", message: errors.join(" | ") });
      }
      if (newItems.length > 0) {
        setQueue((prev) => [...prev, ...newItems]);
      }
      return newItems.length;
    },
    [queue, globalCategory, addToast]
  );

  const handleCameraCapture = useCallback(
    (file: File) => {
      validateAndAdd([file]);
      addToast({
        type: "success",
        title: "Đã chụp ảnh tài liệu thành công",
        message: `Đã thêm "${file.name}" vào danh sách chờ xử lý OCR.`,
      });
    },
    [validateAndAdd, addToast]
  );

  // Lắng nghe sự kiện dán file / ảnh từ Clipboard (Ctrl + V)
  useEffect(() => {
    const handlePaste = (e: ClipboardEvent) => {
      // Bỏ qua nếu người dùng đang gõ vào input hoặc textarea
      const target = e.target as HTMLElement;
      if (target && (target.tagName === "INPUT" || target.tagName === "TEXTAREA")) {
        return;
      }

      const items = e.clipboardData?.items;
      if (!items || items.length === 0) return;

      const pastedFiles: File[] = [];

      for (let i = 0; i < items.length; i++) {
        const item = items[i];
        if (item.kind === "file") {
          const file = item.getAsFile();
          if (file) {
            let processedFile = file;
            // Nếu ảnh chụp màn hình dán trực tiếp tên mặc định là image.png
            if (file.name === "image.png" || !file.name || file.name === "blob") {
              const now = new Date();
              const timestamp = `${now.getHours()}${now.getMinutes()}${now.getSeconds()}_${now.getDate()}${now.getMonth() + 1}`;
              const ext = file.type.includes("pdf") ? "pdf" : file.type.includes("jpeg") ? "jpg" : "png";
              processedFile = new File([file], `Anh_dan_clipboard_${timestamp}.${ext}`, {
                type: file.type || "image/png",
              });
            }
            pastedFiles.push(processedFile);
          }
        }
      }

      if (pastedFiles.length > 0) {
        e.preventDefault();
        const addedCount = validateAndAdd(pastedFiles);
        if (addedCount > 0) {
          addToast({
            type: "success",
            title: "Đã dán file từ Clipboard (Ctrl+V)",
            message: `Đã nhận diện và thêm ${pastedFiles.length} file vào danh sách chờ upload.`,
          });
        }
      }
    };

    window.addEventListener("paste", handlePaste);
    return () => {
      window.removeEventListener("paste", handlePaste);
    };
  }, [validateAndAdd, addToast]);

  const handleDragOver = (e: React.DragEvent) => { e.preventDefault(); setIsDragging(true); };
  const handleDragLeave = () => setIsDragging(false);
  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    if (e.dataTransfer.files.length) validateAndAdd(e.dataTransfer.files);
  };

  const updateItem = (id: string, patch: Partial<QueuedFile>) => {
    setQueue((prev) => prev.map((q) => (q.id === id ? { ...q, ...patch } : q)));
  };

  const removeItem = (id: string) => setQueue((prev) => prev.filter((q) => q.id !== id));

  const handleUploadAll = async () => {
    const pending = queue.filter((q) => q.status === "pending");
    if (!pending.length) return;

    setIsRunning(true);
    let successCount = 0;
    let failCount = 0;

    for (const item of pending) {
      updateItem(item.id, { status: "uploading", progress: 20 });
      try {
        updateItem(item.id, { progress: 60 });
        const res = await documentsApi.upload(
          item.file,
          item.title.trim() || item.file.name,
          item.category || undefined
        );
        updateItem(item.id, { status: "success", progress: 100, result: res });
        successCount++;
      } catch (err: any) {
        updateItem(item.id, { status: "error", progress: 0, error: err.message || "Upload thất bại" });
        failCount++;
      }
    }

    setIsRunning(false);

    if (successCount > 0) {
      addToast({
        type: "success",
        title: `Tải lên hoàn tất — ${successCount} file thành công`,
        message: failCount > 0 ? `${failCount} file gặp lỗi.` : "Tất cả đã đưa vào hàng đợi OCR.",
      });
    }
  };

  const pendingCount = queue.filter((q) => q.status === "pending").length;
  const successItems = queue.filter((q) => q.status === "success");
  const allDone = queue.length > 0 && queue.every((q) => q.status === "success" || q.status === "error");

  return (
    <div className="animate-fade-in" style={{ maxWidth: "860px", margin: "0 auto" }}>
      {/* Header */}
      <div style={{ marginBottom: "1.5rem" }}>
        <h1 style={{ fontSize: "1.5rem", fontWeight: 800, color: "var(--gray-900)" }}>
          Upload & Số hóa Tài liệu CTSV
        </h1>
        <p style={{ fontSize: "0.875rem", color: "var(--gray-500)", marginTop: "0.25rem" }}>
          Hệ thống sẽ tự động lưu file an toàn trên MinIO/Supabase, trích xuất văn bản tiếng Việt bằng OCR và đánh chỉ mục Elasticsearch.
        </p>
      </div>

      {/* Dropzone */}
      <Card padding="lg" style={{ marginBottom: "1.25rem" }}>
        <div
          onDragOver={handleDragOver}
          onDragLeave={handleDragLeave}
          onDrop={handleDrop}
          onClick={() => fileInputRef.current?.click()}
          style={{
            border: `2px dashed ${isDragging ? "var(--primary-500)" : "var(--border-color)"}`,
            backgroundColor: isDragging ? "var(--primary-50)" : "var(--gray-50)",
            borderRadius: "var(--radius-lg)",
            padding: "2.25rem 1.5rem",
            textAlign: "center",
            cursor: "pointer",
            transition: "all 0.2s ease",
            position: "relative",
          }}
        >
          <input
            ref={fileInputRef}
            type="file"
            accept=".pdf,.jpg,.jpeg,.png,.tiff"
            multiple
            style={{ display: "none" }}
            onChange={(e) => {
              if (e.target.files && e.target.files.length > 0) {
                validateAndAdd(e.target.files);
                e.target.value = "";
              }
            }}
          />

          <div
            style={{
              width: "54px",
              height: "54px",
              borderRadius: "50%",
              backgroundColor: isDragging ? "var(--primary-100)" : "#ffffff",
              color: "var(--primary-600)",
              display: "inline-flex",
              alignItems: "center",
              justifyContent: "center",
              boxShadow: "var(--shadow-sm)",
              marginBottom: "0.85rem",
            }}
          >
            <UploadCloud size={28} />
          </div>

          <div style={{ fontSize: "0.95rem", fontWeight: 700, color: "var(--gray-800)" }}>
            Kéo thả <span style={{ color: "var(--primary-600)" }}>nhiều file</span>, <span style={{ color: "var(--primary-600)" }}>dán từ Clipboard</span> hoặc:
          </div>

          {/* Quick Action Buttons inside Dropzone */}
          <div style={{ display: "flex", alignItems: "center", justifyContent: "center", gap: "0.75rem", marginTop: "0.75rem", flexWrap: "wrap" }}>
            <button
              type="button"
              onClick={(e) => {
                e.stopPropagation();
                fileInputRef.current?.click();
              }}
              style={{
                display: "inline-flex",
                alignItems: "center",
                gap: "6px",
                padding: "8px 16px",
                backgroundColor: "#ffffff",
                border: "1px solid var(--primary-300, #a5b4fc)",
                borderRadius: "8px",
                fontSize: "0.85rem",
                fontWeight: 600,
                color: "var(--primary-700, #4338ca)",
                cursor: "pointer",
                boxShadow: "0 1px 2px rgba(0,0,0,0.05)",
                transition: "all 0.15s ease",
              }}
            >
              <UploadCloud size={16} /> Chọn file từ máy tính
            </button>

            <button
              type="button"
              onClick={(e) => {
                e.stopPropagation();
                setIsCameraOpen(true);
              }}
              style={{
                display: "inline-flex",
                alignItems: "center",
                gap: "6px",
                padding: "8px 16px",
                backgroundColor: "#6366f1",
                border: "none",
                borderRadius: "8px",
                fontSize: "0.85rem",
                fontWeight: 600,
                color: "#ffffff",
                cursor: "pointer",
                boxShadow: "0 2px 4px rgba(99, 102, 241, 0.3)",
                transition: "all 0.15s ease",
              }}
            >
              <Camera size={16} /> Chụp ảnh tài liệu (Camera)
            </button>
          </div>

          <div style={{ display: "flex", alignItems: "center", justifyContent: "center", gap: "0.5rem", marginTop: "0.75rem", flexWrap: "wrap" }}>
            <span style={{ fontSize: "0.8125rem", color: "var(--gray-500)" }}>
              PDF, JPG, PNG, TIFF · Tối đa 50MB mỗi file
            </span>
            <span
              style={{
                display: "inline-flex",
                alignItems: "center",
                gap: "4px",
                fontSize: "0.72rem",
                fontWeight: 600,
                color: "var(--primary-700)",
                backgroundColor: "var(--primary-50)",
                border: "1px solid var(--primary-200)",
                padding: "2px 8px",
                borderRadius: "6px",
              }}
            >
              <ClipboardPaste size={12} /> Hỗ trợ dán (Ctrl + V)
            </span>
          </div>
        </div>

        {/* Global category selector (shown when queue empty) */}
        {queue.length === 0 && (
          <div style={{ marginTop: "1.25rem" }}>
            <label style={{ display: "block", fontSize: "0.8125rem", fontWeight: 600, color: "var(--gray-700)", marginBottom: "0.4rem" }}>
              Loại danh mục (áp dụng cho tất cả file)
            </label>
            <select
              value={globalCategory}
              onChange={(e) => setGlobalCategory(e.target.value)}
              style={{
                width: "100%",
                padding: "0.65rem 0.85rem",
                borderRadius: "var(--radius-md)",
                border: "1px solid var(--border-color)",
                fontSize: "0.875rem",
                backgroundColor: "#ffffff",
              }}
            >
              <option value="">-- Tự động nhận diện qua OCR --</option>
              <option value="DON_NGHI_HOC">Đơn xin nghỉ học tạm thời / bảo lưu</option>
              <option value="GIAY_XAC_NHAN">Giấy xác nhận sinh viên</option>
              <option value="HOC_BONG">Hồ sơ xét học bổng khuyến khích</option>
              <option value="KHEN_THUONG">Hồ sơ Khen thưởng - Kỷ luật</option>
              <option value="MIEN_GIAM_HOC_PHI">Đơn xin miễn giảm học phí</option>
            </select>
          </div>
        )}
      </Card>

      {/* Queue list */}
      {queue.length > 0 && (
        <Card padding="lg" style={{ marginBottom: "1.25rem" }}>
          {/* Queue header */}
          <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: "1rem" }}>
            <div style={{ fontWeight: 700, fontSize: "0.9375rem", color: "var(--gray-800)" }}>
              Danh sách file ({queue.length})
            </div>
            <div style={{ display: "flex", gap: "0.5rem" }}>
              <button
                type="button"
                onClick={() => fileInputRef.current?.click()}
                disabled={isRunning}
                style={{
                  display: "inline-flex", alignItems: "center", gap: "4px",
                  padding: "5px 10px", fontSize: "0.8rem", fontWeight: 600,
                  borderRadius: "var(--radius-md)", border: "1px solid var(--border-color)",
                  backgroundColor: "#fff", cursor: isRunning ? "not-allowed" : "pointer", color: "var(--gray-700)",
                }}
              >
                <Plus size={14} /> Thêm file
              </button>
              <button
                type="button"
                onClick={() => setIsCameraOpen(true)}
                disabled={isRunning}
                style={{
                  display: "inline-flex", alignItems: "center", gap: "4px",
                  padding: "5px 10px", fontSize: "0.8rem", fontWeight: 600,
                  borderRadius: "var(--radius-md)", border: "1px solid var(--primary-300)",
                  backgroundColor: "var(--primary-50)", cursor: isRunning ? "not-allowed" : "pointer", color: "var(--primary-700)",
                }}
              >
                <Camera size={14} /> Chụp ảnh
              </button>
              <button
                type="button"
                onClick={() => setQueue((prev) => prev.filter((q) => q.status !== "pending"))}
                disabled={isRunning || pendingCount === 0}
                style={{
                  display: "inline-flex", alignItems: "center", gap: "4px",
                  padding: "5px 10px", fontSize: "0.8rem", fontWeight: 600,
                  borderRadius: "var(--radius-md)", border: "1px solid #fecaca",
                  backgroundColor: "#fff5f5", cursor: isRunning || pendingCount === 0 ? "not-allowed" : "pointer",
                  color: "var(--danger-600)", opacity: pendingCount === 0 ? 0.5 : 1,
                }}
              >
                <Trash2 size={14} /> Xóa chờ
              </button>
            </div>
          </div>

          {/* File rows */}
          <div style={{ display: "flex", flexDirection: "column", gap: "0.6rem" }}>
            {queue.map((item) => (
              <div
                key={item.id}
                style={{
                  borderRadius: "var(--radius-md)",
                  border: `1px solid ${item.status === "success" ? "#bbf7d0" : item.status === "error" ? "#fecaca" : "var(--border-color)"}`,
                  backgroundColor: item.status === "success" ? "#f0fdf4" : item.status === "error" ? "#fff5f5" : "var(--gray-50)",
                  padding: "0.75rem 1rem",
                  transition: "all 0.2s",
                }}
              >
                <div style={{ display: "flex", alignItems: "center", gap: "0.75rem" }}>
                  {/* Icon */}
                  <div style={{ flexShrink: 0 }}>
                    {item.status === "success" ? (
                      <CheckCircle2 size={20} color="#16a34a" />
                    ) : item.status === "error" ? (
                      <AlertCircle size={20} color="var(--danger-500)" />
                    ) : (
                      getFileIcon(item.file.name)
                    )}
                  </div>

                  {/* Info */}
                  <div style={{ flex: 1, minWidth: 0 }}>
                    {item.status === "pending" ? (
                      <input
                        type="text"
                        value={item.title}
                        onChange={(e) => updateItem(item.id, { title: e.target.value })}
                        style={{
                          width: "100%", fontSize: "0.8rem", fontWeight: 600,
                          color: "var(--gray-900)", border: "none", background: "transparent",
                          outline: "none", padding: 0,
                        }}
                      />
                    ) : (
                      <div style={{ fontSize: "0.8rem", fontWeight: 600, color: "var(--gray-900)", whiteSpace: "nowrap", overflow: "hidden", textOverflow: "ellipsis" }}>
                        {item.title || item.file.name}
                      </div>
                    )}
                    <div style={{ fontSize: "0.7rem", color: "var(--gray-500)", marginTop: "2px" }}>
                      {item.file.name} · {formatSize(item.file.size)}
                      {item.status === "error" && (
                        <span style={{ color: "var(--danger-600)", marginLeft: "6px" }}>— {item.error}</span>
                      )}
                    </div>

                    {/* Progress bar */}
                    {item.status === "uploading" && (
                      <div style={{ marginTop: "6px", height: "4px", backgroundColor: "var(--primary-100)", borderRadius: "9999px", overflow: "hidden" }}>
                        <div
                          style={{
                            height: "100%", width: `${item.progress}%`,
                            backgroundColor: "var(--primary-600)", borderRadius: "9999px", transition: "width 0.3s ease",
                          }}
                        />
                      </div>
                    )}
                  </div>

                  {/* Status badge */}
                  <StatusBadge status={item.status} progress={item.progress} />

                  {/* View result */}
                  {item.status === "success" && item.result && (
                    <button
                      type="button"
                      onClick={() => navigate(`/documents/${item.result!.id}`)}
                      style={{
                        display: "inline-flex", alignItems: "center", gap: "4px",
                        padding: "4px 8px", fontSize: "0.7rem", fontWeight: 600,
                        borderRadius: "var(--radius-sm)", border: "1px solid #bbf7d0",
                        backgroundColor: "#f0fdf4", cursor: "pointer", color: "#16a34a", whiteSpace: "nowrap",
                      }}
                    >
                      Xem <ArrowRight size={11} />
                    </button>
                  )}

                  {/* Remove (pending) */}
                  {item.status === "pending" && !isRunning && (
                    <button
                      type="button"
                      onClick={() => removeItem(item.id)}
                      style={{ color: "var(--gray-400)", padding: "4px", cursor: "pointer", border: "none", background: "transparent", flexShrink: 0 }}
                    >
                      <X size={16} />
                    </button>
                  )}

                  {/* Retry (error) */}
                  {item.status === "error" && !isRunning && (
                    <button
                      type="button"
                      onClick={() => updateItem(item.id, { status: "pending", error: undefined, progress: 0 })}
                      style={{
                        display: "inline-flex", alignItems: "center", gap: "4px",
                        padding: "4px 8px", fontSize: "0.7rem", fontWeight: 600,
                        borderRadius: "var(--radius-sm)", border: "1px solid #fecaca",
                        backgroundColor: "#fff5f5", cursor: "pointer", color: "var(--danger-600)", whiteSpace: "nowrap",
                      }}
                    >
                      Thử lại
                    </button>
                  )}
                </div>
              </div>
            ))}
          </div>

          {/* Summary */}
          {allDone && (
            <div
              style={{
                marginTop: "1rem", padding: "0.75rem 1rem",
                borderRadius: "var(--radius-md)",
                backgroundColor: successItems.length === queue.length ? "#d1fae5" : "#fef3c7",
                border: `1px solid ${successItems.length === queue.length ? "#6ee7b7" : "#fde68a"}`,
                fontSize: "0.8125rem", fontWeight: 600,
                color: successItems.length === queue.length ? "#065f46" : "#92400e",
                display: "flex", alignItems: "center", gap: "0.5rem",
              }}
            >
              <CheckCircle2 size={16} />
              {successItems.length}/{queue.length} file tải lên thành công
              {queue.length - successItems.length > 0 && ` · ${queue.length - successItems.length} file lỗi`}
            </div>
          )}
        </Card>
      )}

      {/* Action bar */}
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", gap: "0.75rem", flexWrap: "wrap" }}>
        <div style={{ fontSize: "0.8125rem", color: "var(--gray-500)" }}>
          {queue.length > 0 && (
            <>
              <span style={{ fontWeight: 600, color: "var(--gray-700)" }}>{queue.length}</span> file trong hàng đợi
              {pendingCount > 0 && <> · <span style={{ fontWeight: 600, color: "var(--primary-700)" }}>{pendingCount}</span> chờ upload</>}
            </>
          )}
        </div>

        <div style={{ display: "flex", gap: "0.75rem" }}>
          <Button type="button" variant="outline" onClick={() => navigate("/")} disabled={isRunning}>
            Hủy bỏ
          </Button>

          {allDone && successItems.length > 0 ? (
            <Button variant="primary" rightIcon={<ArrowRight size={16} />} onClick={() => navigate("/documents")}>
              Xem tất cả tài liệu
            </Button>
          ) : (
            <Button
              variant="primary"
              disabled={pendingCount === 0 || isRunning}
              isLoading={isRunning}
              leftIcon={<Sparkles size={17} />}
              onClick={handleUploadAll}
            >
              {isRunning ? "Đang upload..." : `Upload ${pendingCount > 0 ? `${pendingCount} file` : "tất cả"} & OCR`}
            </Button>
          )}
        </div>
      </div>

      {/* Camera Capture Modal */}
      <CameraCaptureModal
        isOpen={isCameraOpen}
        onClose={() => setIsCameraOpen(false)}
        onCapture={handleCameraCapture}
      />

      <style>{`@keyframes spin { from { transform: rotate(0deg); } to { transform: rotate(360deg); } }`}</style>
    </div>
  );
};
