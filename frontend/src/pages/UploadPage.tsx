import React, { useState, useRef, useCallback, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import {
  UploadCloud,
  CheckCircle2,
  AlertCircle,
  X,
  ArrowRight,
  Clock,
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
  if (ext === "pdf") return <FileText size={18} className="text-rose-600" />;
  return <Image size={18} className="text-dlu-navy-700" />;
};

const formatSize = (bytes: number) => {
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(0)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(2)} MB`;
};

const StatusBadge: React.FC<{ status: FileStatus; progress: number }> = ({ status, progress }) => {
  const styles: Record<FileStatus, string> = {
    pending: "bg-slate-100 text-slate-600 border-slate-200",
    uploading: "bg-sky-50 text-sky-800 border-sky-200",
    success: "bg-emerald-50 text-emerald-800 border-emerald-200 font-semibold",
    error: "bg-rose-50 text-rose-800 border-rose-200 font-semibold",
  };
  const labels: Record<FileStatus, string> = {
    pending: "Chờ upload",
    uploading: `Đang tải ${progress}%`,
    success: "Hoàn thành",
    error: "Lỗi",
  };
  const icons: Record<FileStatus, React.ReactNode> = {
    pending: <Clock size={11} />,
    uploading: <span className="loading loading-spinner loading-xs text-current" />,
    success: <CheckCircle2 size={11} />,
    error: <AlertCircle size={11} />,
  };

  return (
    <span
      className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-medium border leading-none ${styles[status]}`}
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
  const [mergeImages, setMergeImages] = useState<boolean>(true);
  const [mergedTitle, setMergedTitle] = useState<string>("");

  const isImageFile = (name: string) => {
    const ext = name.split(".").pop()?.toLowerCase() || "";
    return ["jpg", "jpeg", "png", "tiff", "tif", "bmp", "webp"].includes(ext);
  };

  const pendingImages = queue.filter((q) => q.status === "pending" && isImageFile(q.file.name));
  const canMerge = pendingImages.length >= 2;

  useEffect(() => {
    if (canMerge && !mergedTitle && pendingImages.length > 0) {
      const firstStem = pendingImages[0].file.name.replace(/\.[^/.]+$/, "");
      const cleaned = firstStem.replace(/[-_]?(?:images?|page|p|scan)[-_]?\d+$/i, "").trim();
      setMergedTitle(cleaned || firstStem);
    }
  }, [queue.length, canMerge, mergedTitle]);

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

  useEffect(() => {
    const handlePaste = (e: ClipboardEvent) => {
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

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  };
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

    const currentPendingImages = pending.filter((q) => isImageFile(q.file.name));
    const shouldMerge = mergeImages && currentPendingImages.length >= 2;

    if (shouldMerge) {
      const sortedImages = [...currentPendingImages].sort((a, b) =>
        a.file.name.localeCompare(b.file.name, undefined, { numeric: true, sensitivity: "base" })
      );

      sortedImages.forEach((item) => updateItem(item.id, { status: "uploading", progress: 30 }));
      try {
        const imageFiles = sortedImages.map((item) => item.file);
        const titleToUse = mergedTitle.trim() || imageFiles[0].name.replace(/\.[^/.]+$/, "");

        sortedImages.forEach((item) => updateItem(item.id, { progress: 60 }));
        const res = await documentsApi.upload(
          imageFiles,
          titleToUse,
          globalCategory || undefined,
          true
        );
        sortedImages.forEach((item) => updateItem(item.id, { status: "success", progress: 100, result: res }));
        successCount++;
        addToast({
          type: "success",
          title: "Ghép tài liệu & Tải lên thành công",
          message: `Đã tự động ghép ${imageFiles.length} file ảnh thành 1 tài liệu PDF và đưa vào hàng đợi OCR.`,
        });
      } catch (err: any) {
        sortedImages.forEach((item) =>
          updateItem(item.id, { status: "error", progress: 0, error: err.message || "Upload thất bại" })
        );
        failCount += sortedImages.length;
      }

      const nonImages = pending.filter((q) => !isImageFile(q.file.name));
      for (const item of nonImages) {
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
    } else {
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
    }

    setIsRunning(false);

    if (successCount > 0 && !shouldMerge) {
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
    <div className="max-w-4xl mx-auto space-y-6 animate-fade-in">
      {/* Header */}
      <div>
        <h1 className="text-xl sm:text-2xl font-bold text-slate-900 tracking-tight">
          Upload & Số hóa Tài liệu CTSV
        </h1>
        <p className="text-xs sm:text-sm text-slate-500 mt-1">
          Hệ thống sẽ tự động lưu file an toàn trên MinIO/Supabase, trích xuất văn bản tiếng Việt bằng OCR và đánh chỉ mục Elasticsearch.
        </p>
      </div>

      {/* Dropzone */}
      <Card padding="lg">
        <div
          onDragOver={handleDragOver}
          onDragLeave={handleDragLeave}
          onDrop={handleDrop}
          onClick={() => fileInputRef.current?.click()}
          className={`border-2 border-dashed rounded-lg p-6 sm:p-10 text-center cursor-pointer transition-all ${
            isDragging
              ? "border-sky-500 bg-sky-50/70"
              : "border-slate-300 hover:border-slate-400 bg-slate-50/60"
          }`}
        >
          <input
            ref={fileInputRef}
            type="file"
            accept=".pdf,.jpg,.jpeg,.png,.tiff"
            multiple
            className="hidden"
            onChange={(e) => {
              if (e.target.files && e.target.files.length > 0) {
                validateAndAdd(e.target.files);
                e.target.value = "";
              }
            }}
          />

          <div className="w-12 h-12 rounded-full bg-white text-dlu-navy-800 inline-flex items-center justify-center shadow-sm mb-3 border border-slate-200">
            <UploadCloud size={24} />
          </div>

          <div className="text-sm sm:text-base font-bold text-slate-800">
            Kéo thả <span className="text-dlu-navy-700">nhiều file</span>, <span className="text-dlu-navy-700">dán từ Clipboard</span> hoặc:
          </div>

          {/* Quick Action Buttons inside Dropzone */}
          <div className="flex items-center justify-center gap-2.5 mt-3 flex-wrap">
            <button
              type="button"
              onClick={(e) => {
                e.stopPropagation();
                fileInputRef.current?.click();
              }}
              className="inline-flex items-center gap-1.5 px-4 py-2 bg-white border border-slate-200 hover:border-slate-300 rounded-md text-xs font-semibold text-slate-700 shadow-xs hover:bg-slate-50 transition-colors"
            >
              <UploadCloud size={14} className="text-dlu-navy-700" /> Chọn file từ máy tính
            </button>

            <button
              type="button"
              onClick={(e) => {
                e.stopPropagation();
                setIsCameraOpen(true);
              }}
              className="inline-flex items-center gap-1.5 px-4 py-2 bg-dlu-navy-900 hover:bg-dlu-navy-800 text-white rounded-md text-xs font-semibold shadow-xs transition-colors"
            >
              <Camera size={14} /> Chụp ảnh tài liệu (Camera)
            </button>
          </div>

          <div className="flex items-center justify-center gap-2 mt-4 text-xs text-slate-500 flex-wrap">
            <span>PDF, JPG, PNG, TIFF · Tối đa 50MB mỗi file</span>
            <span>•</span>
            <span className="inline-flex items-center gap-1 text-[11px] font-semibold text-dlu-navy-800 bg-sky-50 border border-sky-200 px-2 py-0.5 rounded">
              <ClipboardPaste size={11} /> Hỗ trợ dán (Ctrl + V)
            </span>
          </div>
        </div>

        {/* Global category selector */}
        {queue.length === 0 && (
          <div className="mt-4 pt-4 border-t border-slate-100">
            <label className="block text-xs font-semibold text-slate-700 mb-1.5">
              Loại danh mục (áp dụng cho tất cả file)
            </label>
            <select
              value={globalCategory}
              onChange={(e) => setGlobalCategory(e.target.value)}
              className="w-full px-3 py-2 rounded-md border border-slate-200 text-xs sm:text-sm bg-white text-slate-800 outline-none focus:ring-2 focus:ring-dlu-navy-500/20 focus:border-dlu-navy-600"
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
        <Card padding="md">
          {/* Queue header */}
          <div className="flex items-center justify-between mb-3.5 pb-2.5 border-b border-slate-100 flex-wrap gap-2">
            <div className="font-bold text-xs sm:text-sm text-slate-900">
              Danh sách file ({queue.length})
            </div>
            <div className="flex items-center gap-1.5">
              <button
                type="button"
                onClick={() => fileInputRef.current?.click()}
                disabled={isRunning}
                className="inline-flex items-center gap-1 px-2.5 py-1 text-xs font-semibold rounded border border-slate-200 bg-white text-slate-700 hover:bg-slate-50 disabled:opacity-50"
              >
                <Plus size={13} /> Thêm file
              </button>
              <button
                type="button"
                onClick={() => setIsCameraOpen(true)}
                disabled={isRunning}
                className="inline-flex items-center gap-1 px-2.5 py-1 text-xs font-semibold rounded border border-sky-300 bg-sky-50 text-sky-800 hover:bg-sky-100 disabled:opacity-50"
              >
                <Camera size={13} /> Chụp ảnh
              </button>
              <button
                type="button"
                onClick={() => setQueue((prev) => prev.filter((q) => q.status !== "pending"))}
                disabled={isRunning || pendingCount === 0}
                className="inline-flex items-center gap-1 px-2.5 py-1 text-xs font-semibold rounded border border-rose-200 bg-rose-50 text-rose-700 hover:bg-rose-100 disabled:opacity-50"
              >
                <Trash2 size={13} /> Xóa chờ
              </button>
            </div>
          </div>

          {/* Banner tùy chọn ghép nhiều ảnh thành 1 tài liệu PDF */}
          {canMerge && (
            <div
              className={`rounded-md p-3.5 mb-3 transition-all border ${
                mergeImages
                  ? "bg-indigo-50/70 border-indigo-200 text-indigo-950"
                  : "bg-slate-50 border-slate-200 text-slate-800"
              }`}
            >
              <div className="flex items-center justify-between flex-wrap gap-2">
                <label className="flex items-center gap-2 cursor-pointer font-bold text-xs sm:text-sm">
                  <input
                    type="checkbox"
                    checked={mergeImages}
                    onChange={(e) => setMergeImages(e.target.checked)}
                    className="w-4 h-4 accent-indigo-600 cursor-pointer"
                  />
                  <span>⚡ Ghép các file ảnh thành 1 tài liệu nhiều trang (PDF)</span>
                </label>
                <span className="text-[11px] font-semibold px-2 py-0.5 rounded-full bg-indigo-100 text-indigo-800 font-mono">
                  {pendingImages.length} trang ảnh
                </span>
              </div>

              {mergeImages && (
                <div className="mt-2.5 pt-2.5 border-t border-indigo-200/60">
                  <label className="block text-[11px] font-semibold text-indigo-900 mb-1">
                    Tiêu đề tài liệu hợp nhất (gồm {pendingImages.length} trang ảnh):
                  </label>
                  <input
                    type="text"
                    value={mergedTitle}
                    onChange={(e) => setMergedTitle(e.target.value)}
                    placeholder="Nhập tiêu đề tài liệu sau khi ghép các trang ảnh..."
                    className="w-full px-3 py-1.5 text-xs font-semibold rounded border border-indigo-300 bg-white text-slate-900 outline-none focus:ring-1 focus:ring-indigo-500"
                  />
                  <div className="text-[10px] text-indigo-700 mt-1">
                    ✓ Các ảnh sẽ được ghép nối theo thứ tự trang tự nhiên thành 1 file PDF thống nhất, giữ nguyên chất lượng và chạy OCR cho toàn bộ các trang.
                  </div>
                </div>
              )}
            </div>
          )}

          {/* File rows */}
          <div className="space-y-2">
            {queue.map((item) => {
              const imageIndex = pendingImages.findIndex((pi) => pi.id === item.id);
              return (
                <div
                  key={item.id}
                  className={`rounded-md border p-3 transition-colors ${
                    item.status === "success"
                      ? "bg-emerald-50/50 border-emerald-200"
                      : item.status === "error"
                      ? "bg-rose-50/50 border-rose-200"
                      : "bg-slate-50/60 border-slate-200"
                  }`}
                >
                  <div className="flex items-center gap-3">
                    {/* Icon */}
                    <div className="shrink-0">
                      {item.status === "success" ? (
                        <CheckCircle2 size={18} className="text-emerald-600" />
                      ) : item.status === "error" ? (
                        <AlertCircle size={18} className="text-rose-600" />
                      ) : (
                        getFileIcon(item.file.name)
                      )}
                    </div>

                    {/* Info */}
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-1.5">
                        {mergeImages && canMerge && isImageFile(item.file.name) && imageIndex !== -1 && (
                          <span className="bg-indigo-600 text-white text-[10px] font-bold px-1.5 py-0.2 rounded shrink-0">
                            Trang {imageIndex + 1}
                          </span>
                        )}
                        {item.status === "pending" ? (
                          <input
                            type="text"
                            value={item.title}
                            onChange={(e) => updateItem(item.id, { title: e.target.value })}
                            className="w-full text-xs font-semibold text-slate-900 border-none bg-transparent outline-none p-0 focus:underline"
                          />
                        ) : (
                          <div className="text-xs font-semibold text-slate-900 truncate">
                            {item.title || item.file.name}
                          </div>
                        )}
                      </div>
                      <div className="text-[11px] text-slate-400 mt-0.5">
                        {item.file.name} · {formatSize(item.file.size)}
                        {item.status === "error" && (
                          <span className="text-rose-600 font-medium ml-1.5">— {item.error}</span>
                        )}
                      </div>

                      {/* Progress bar */}
                      {item.status === "uploading" && (
                        <div className="mt-1.5 h-1.5 bg-sky-100 rounded-full overflow-hidden">
                          <div
                            className="h-full bg-sky-600 rounded-full transition-all duration-300"
                            style={{ width: `${item.progress}%` }}
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
                        className="inline-flex items-center gap-1 px-2 py-0.5 text-xs font-semibold rounded bg-emerald-100 text-emerald-800 hover:bg-emerald-200 transition-colors"
                      >
                        Xem <ArrowRight size={10} />
                      </button>
                    )}

                    {/* Remove (pending) */}
                    {item.status === "pending" && !isRunning && (
                      <button
                        type="button"
                        onClick={() => removeItem(item.id)}
                        className="text-slate-400 hover:text-slate-700 p-1 shrink-0"
                        title="Xóa khỏi danh sách"
                      >
                        <X size={15} />
                      </button>
                    )}

                    {/* Retry (error) */}
                    {item.status === "error" && !isRunning && (
                      <button
                        type="button"
                        onClick={() => updateItem(item.id, { status: "pending", error: undefined, progress: 0 })}
                        className="inline-flex items-center gap-1 px-2 py-0.5 text-xs font-semibold rounded bg-rose-100 text-rose-800 hover:bg-rose-200 transition-colors"
                      >
                        Thử lại
                      </button>
                    )}
                  </div>
                </div>
              );
            })}
          </div>

          {/* Summary */}
          {allDone && (
            <div
              className={`mt-3 p-3 rounded-md border text-xs font-semibold flex items-center gap-2 ${
                successItems.length === queue.length
                  ? "bg-emerald-50 text-emerald-800 border-emerald-200"
                  : "bg-amber-50 text-amber-800 border-amber-200"
              }`}
            >
              <CheckCircle2 size={15} />
              {successItems.length}/{queue.length} file tải lên thành công
              {queue.length - successItems.length > 0 && ` · ${queue.length - successItems.length} file lỗi`}
            </div>
          )}
        </Card>
      )}

      {/* Action bar */}
      <div className="flex justify-between items-center gap-3 flex-wrap">
        <div className="text-xs text-slate-500">
          {queue.length > 0 && (
            <>
              <span className="font-semibold text-slate-800">{queue.length}</span> file trong hàng đợi
              {pendingCount > 0 && (
                <> · <span className="font-semibold text-dlu-navy-800">{pendingCount}</span> chờ upload</>
              )}
            </>
          )}
        </div>

        <div className="flex items-center gap-2">
          <Button type="button" variant="outline" onClick={() => navigate("/")} disabled={isRunning}>
            Hủy bỏ
          </Button>

          {allDone && successItems.length > 0 ? (
            <Button variant="primary" rightIcon={<ArrowRight size={15} />} onClick={() => navigate("/documents")}>
              Xem tất cả tài liệu
            </Button>
          ) : (
            <Button
              variant="primary"
              disabled={pendingCount === 0 || isRunning}
              isLoading={isRunning}
              leftIcon={<UploadCloud size={16} />}
              onClick={handleUploadAll}
            >
              {isRunning
                ? "Đang xử lý..."
                : mergeImages && canMerge
                ? `Ghép ${pendingImages.length} ảnh thành 1 tài liệu & OCR`
                : `Upload ${pendingCount > 0 ? `${pendingCount} file` : "tất cả"} & OCR`}
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
    </div>
  );
};
