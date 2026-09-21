import React, { useState, useRef, useEffect, useCallback } from "react";
import {
  Camera,
  CameraOff,
  RotateCw,
  RefreshCw,
  Check,
  X,
  SwitchCamera,
  Sparkles,
} from "lucide-react";

interface CameraCaptureModalProps {
  isOpen: boolean;
  onClose: () => void;
  onCapture: (file: File) => void;
}

export const CameraCaptureModal: React.FC<CameraCaptureModalProps> = ({
  isOpen,
  onClose,
  onCapture,
}) => {
  const videoRef = useRef<HTMLVideoElement | null>(null);
  const canvasRef = useRef<HTMLCanvasElement | null>(null);

  const [stream, setStream] = useState<MediaStream | null>(null);
  const [capturedImage, setCapturedImage] = useState<string | null>(null);
  const [rotation, setRotation] = useState<number>(0);
  const [devices, setDevices] = useState<MediaDeviceInfo[]>([]);
  const [selectedDeviceId, setSelectedDeviceId] = useState<string>("");
  const [facingMode, setFacingMode] = useState<"environment" | "user">("environment");
  const [error, setError] = useState<string | null>(null);
  const [isCapturing, setIsCapturing] = useState<boolean>(false);
  const [hasMultipleCameras, setHasMultipleCameras] = useState<boolean>(false);

  // Stop camera stream
  const stopStream = useCallback(() => {
    if (stream) {
      stream.getTracks().forEach((track) => track.stop());
      setStream(null);
    }
  }, [stream]);

  // Start camera stream
  const startCamera = useCallback(async () => {
    setError(null);
    stopStream();

    try {
      const constraints: MediaStreamConstraints = {
        video: selectedDeviceId
          ? { deviceId: { exact: selectedDeviceId }, width: { ideal: 1920 }, height: { ideal: 1080 } }
          : { facingMode: facingMode, width: { ideal: 1920 }, height: { ideal: 1080 } },
        audio: false,
      };

      const mediaStream = await navigator.mediaDevices.getUserMedia(constraints);
      setStream(mediaStream);

      if (videoRef.current) {
        videoRef.current.srcObject = mediaStream;
      }

      // Enumerate devices to check if multiple cameras are available
      const allDevices = await navigator.mediaDevices.enumerateDevices();
      const videoInputs = allDevices.filter((d) => d.kind === "videoinput");
      setDevices(videoInputs);
      setHasMultipleCameras(videoInputs.length > 1);
    } catch (err: any) {
      console.error("Camera access error:", err);
      if (err.name === "NotAllowedError" || err.name === "PermissionDeniedError") {
        setError("Bạn chưa cấp quyền truy cập Camera. Vui lòng cho phép quyền Camera trên trình duyệt.");
      } else if (err.name === "NotFoundError" || err.name === "DevicesNotFoundError") {
        setError("Không tìm thấy thiết bị Camera trên máy tính hoặc điện thoại.");
      } else {
        setError(`Không thể mở Camera: ${err.message || "Lỗi không xác định"}`);
      }
    }
  }, [selectedDeviceId, facingMode, stopStream]);

  useEffect(() => {
    if (isOpen && !capturedImage) {
      startCamera();
    } else if (!isOpen) {
      stopStream();
      setCapturedImage(null);
      setRotation(0);
      setError(null);
    }
    return () => {
      stopStream();
    };
  }, [isOpen, capturedImage]);

  // Take photo from video stream
  const handleTakeSnapshot = () => {
    if (!videoRef.current) return;
    setIsCapturing(true);

    const video = videoRef.current;
    const canvas = canvasRef.current || document.createElement("canvas");
    canvas.width = video.videoWidth || 1280;
    canvas.height = video.videoHeight || 720;

    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    // Draw video frame to canvas
    ctx.drawImage(video, 0, 0, canvas.width, canvas.height);

    const dataUrl = canvas.toDataURL("image/jpeg", 0.95);
    setCapturedImage(dataUrl);
    setRotation(0);
    setIsCapturing(false);
    stopStream();
  };

  // Rotate captured image by 90 degrees
  const handleRotate = () => {
    setRotation((prev) => (prev + 90) % 360);
  };

  // Retake photo
  const handleRetake = () => {
    setCapturedImage(null);
    setRotation(0);
    startCamera();
  };

  // Confirm and submit captured image
  const handleConfirm = () => {
    if (!capturedImage) return;

    const img = new window.Image();
    img.onload = () => {
      const canvas = document.createElement("canvas");
      const ctx = canvas.getContext("2d");
      if (!ctx) return;

      if (rotation === 90 || rotation === 270) {
        canvas.width = img.height;
        canvas.height = img.width;
      } else {
        canvas.width = img.width;
        canvas.height = img.height;
      }

      ctx.save();
      ctx.translate(canvas.width / 2, canvas.height / 2);
      ctx.rotate((rotation * Math.PI) / 180);
      ctx.drawImage(img, -img.width / 2, -img.height / 2);
      ctx.restore();

      canvas.toBlob(
        (blob) => {
          if (!blob) return;
          const now = new Date();
          const timestamp = `${now.getFullYear()}${String(now.getMonth() + 1).padStart(2, "0")}${String(now.getDate()).padStart(2, "0")}_${String(now.getHours()).padStart(2, "0")}${String(now.getMinutes()).padStart(2, "0")}${String(now.getSeconds()).padStart(2, "0")}`;
          const file = new File([blob], `Chup_tai_lieu_${timestamp}.jpg`, {
            type: "image/jpeg",
          });

          onCapture(file);
          onClose();
        },
        "image/jpeg",
        0.95
      );
    };
    img.src = capturedImage;
  };

  // Switch camera between front/back
  const handleSwitchCamera = () => {
    if (devices.length > 1) {
      const currentIndex = devices.findIndex((d) => d.deviceId === selectedDeviceId);
      const nextDevice = devices[(currentIndex + 1) % devices.length];
      setSelectedDeviceId(nextDevice.deviceId);
    } else {
      setFacingMode((prev) => (prev === "environment" ? "user" : "environment"));
    }
  };

  if (!isOpen) return null;

  return (
    <div style={overlayStyle} className="animate-fade-in">
      <div style={modalStyle}>
        {/* Header */}
        <div style={headerStyle}>
          <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
            <div style={iconBadgeStyle}>
              <Camera size={18} color="#ffffff" />
            </div>
            <div>
              <h2 style={modalTitleStyle}>Chụp ảnh Tài liệu / Hồ sơ trực tiếp</h2>
              <p style={modalSubtitleStyle}>
                Căn chỉnh tài liệu vào giữa khung hình rồi bấm chụp để OCR nhận dạng
              </p>
            </div>
          </div>
          <button onClick={onClose} style={closeBtnStyle} aria-label="Đóng">
            <X size={20} />
          </button>
        </div>

        {/* Viewport Area */}
        <div style={viewportContainerStyle}>
          {error ? (
            <div style={errorContainerStyle}>
              <div style={errorIconStyle}>
                <CameraOff size={36} color="var(--danger-500, #ef4444)" />
              </div>
              <h3 style={{ fontSize: "1rem", fontWeight: 700, color: "var(--gray-900, #111827)", marginBottom: "0.5rem" }}>
                Không thể khởi động Camera
              </h3>
              <p style={{ fontSize: "0.85rem", color: "var(--gray-600, #4b5563)", maxWidth: "380px", marginBottom: "1.25rem", lineHeight: 1.5 }}>
                {error}
              </p>
              <button onClick={startCamera} style={retryBtnStyle}>
                <RefreshCw size={15} /> Thử lại
              </button>
            </div>
          ) : capturedImage ? (
            /* Preview Image */
            <div style={previewWrapperStyle}>
              <img
                src={capturedImage}
                alt="Captured Document"
                style={{
                  ...previewImageStyle,
                  transform: `rotate(${rotation}deg)`,
                }}
              />
            </div>
          ) : (
            /* Live Camera Stream */
            <div style={videoWrapperStyle}>
              <video
                ref={videoRef}
                autoPlay
                playsInline
                muted
                style={videoStyle}
              />
              {/* Document Alignment Frame Guides */}
              <div style={documentGuideOverlayStyle}>
                <div style={{ ...cornerStyle, top: 12, left: 12, borderTop: "3px solid #6366f1", borderLeft: "3px solid #6366f1" }} />
                <div style={{ ...cornerStyle, top: 12, right: 12, borderTop: "3px solid #6366f1", borderRight: "3px solid #6366f1" }} />
                <div style={{ ...cornerStyle, bottom: 12, left: 12, borderBottom: "3px solid #6366f1", borderLeft: "3px solid #6366f1" }} />
                <div style={{ ...cornerStyle, bottom: 12, right: 12, borderBottom: "3px solid #6366f1", borderRight: "3px solid #6366f1" }} />
                
                <div style={guideBadgeStyle}>
                  <Sparkles size={13} color="#6366f1" />
                  <span>Giữ tài liệu phẳng & đủ ánh sáng</span>
                </div>
              </div>
            </div>
          )}

          <canvas ref={canvasRef} style={{ display: "none" }} />
        </div>

        {/* Footer Actions */}
        <div style={footerStyle}>
          {capturedImage ? (
            /* Review Controls */
            <div style={controlsRowStyle}>
              <button onClick={handleRetake} style={secondaryBtnStyle}>
                <RefreshCw size={16} /> Chụp lại
              </button>

              <button onClick={handleRotate} style={secondaryBtnStyle}>
                <RotateCw size={16} /> Xoay 90° {rotation > 0 ? `(${rotation}°)` : ""}
              </button>

              <button onClick={handleConfirm} style={primaryBtnStyle}>
                <Check size={18} /> Sử dụng ảnh này
              </button>
            </div>
          ) : (
            /* Live Stream Controls */
            <div style={controlsRowStyle}>
              {hasMultipleCameras ? (
                <button
                  type="button"
                  onClick={handleSwitchCamera}
                  style={iconCircleBtnStyle}
                  title="Đổi camera"
                >
                  <SwitchCamera size={20} />
                </button>
              ) : (
                <div style={{ width: "44px" }} />
              )}

              {/* Shutter Button */}
              <button
                type="button"
                onClick={handleTakeSnapshot}
                disabled={!!error || isCapturing}
                style={{
                  ...shutterBtnStyle,
                  opacity: !!error ? 0.5 : 1,
                  cursor: !!error ? "not-allowed" : "pointer",
                }}
                aria-label="Chụp hình"
              >
                <div style={shutterInnerStyle} />
              </button>

              <div style={{ width: "44px" }} />
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

// ─── STYLES ──────────────────────────────────────────────────────────────────
const overlayStyle: React.CSSProperties = {
  position: "fixed",
  inset: 0,
  backgroundColor: "rgba(15, 23, 42, 0.75)",
  backdropFilter: "blur(6px)",
  zIndex: 9999,
  display: "flex",
  alignItems: "center",
  justifyContent: "center",
  padding: "1rem",
};

const modalStyle: React.CSSProperties = {
  backgroundColor: "#ffffff",
  borderRadius: "16px",
  width: "100%",
  maxWidth: "680px",
  boxShadow: "0 25px 50px -12px rgba(0, 0, 0, 0.25)",
  overflow: "hidden",
  display: "flex",
  flexDirection: "column",
};

const headerStyle: React.CSSProperties = {
  padding: "1rem 1.25rem",
  borderBottom: "1px solid #e5e7eb",
  display: "flex",
  alignItems: "center",
  justifyContent: "space-between",
  backgroundColor: "#f9fafb",
};

const iconBadgeStyle: React.CSSProperties = {
  width: "36px",
  height: "36px",
  borderRadius: "10px",
  backgroundColor: "#6366f1",
  display: "flex",
  alignItems: "center",
  justifyContent: "center",
  boxShadow: "0 2px 4px rgba(99, 102, 241, 0.3)",
};

const modalTitleStyle: React.CSSProperties = {
  fontSize: "1rem",
  fontWeight: 700,
  color: "#111827",
  margin: 0,
};

const modalSubtitleStyle: React.CSSProperties = {
  fontSize: "0.775rem",
  color: "#6b7280",
  margin: 0,
  marginTop: "2px",
};

const closeBtnStyle: React.CSSProperties = {
  background: "none",
  border: "none",
  color: "#6b7280",
  cursor: "pointer",
  padding: "6px",
  borderRadius: "8px",
  display: "flex",
  alignItems: "center",
  justifyContent: "center",
};

const viewportContainerStyle: React.CSSProperties = {
  position: "relative",
  width: "100%",
  height: "420px",
  backgroundColor: "#090d16",
  display: "flex",
  alignItems: "center",
  justifyContent: "center",
  overflow: "hidden",
};

const videoWrapperStyle: React.CSSProperties = {
  position: "relative",
  width: "100%",
  height: "100%",
  display: "flex",
  alignItems: "center",
  justifyContent: "center",
};

const videoStyle: React.CSSProperties = {
  width: "100%",
  height: "100%",
  objectFit: "contain",
};

const documentGuideOverlayStyle: React.CSSProperties = {
  position: "absolute",
  inset: "24px",
  border: "1.5px dashed rgba(255, 255, 255, 0.45)",
  borderRadius: "12px",
  pointerEvents: "none",
  display: "flex",
  alignItems: "flex-end",
  justifyContent: "center",
  paddingBottom: "12px",
};

const cornerStyle: React.CSSProperties = {
  position: "absolute",
  width: "24px",
  height: "24px",
  borderRadius: "2px",
};

const guideBadgeStyle: React.CSSProperties = {
  backgroundColor: "rgba(15, 23, 42, 0.75)",
  backdropFilter: "blur(4px)",
  color: "#f3f4f6",
  fontSize: "0.75rem",
  fontWeight: 500,
  padding: "4px 12px",
  borderRadius: "9999px",
  display: "flex",
  alignItems: "center",
  gap: "6px",
  boxShadow: "0 2px 6px rgba(0, 0, 0, 0.3)",
};

const previewWrapperStyle: React.CSSProperties = {
  width: "100%",
  height: "100%",
  display: "flex",
  alignItems: "center",
  justifyContent: "center",
  backgroundColor: "#0f172a",
};

const previewImageStyle: React.CSSProperties = {
  maxWidth: "90%",
  maxHeight: "90%",
  objectFit: "contain",
  borderRadius: "8px",
  transition: "transform 0.25s ease",
  boxShadow: "0 10px 25px rgba(0,0,0,0.5)",
};

const errorContainerStyle: React.CSSProperties = {
  textAlign: "center",
  padding: "2rem",
  display: "flex",
  flexDirection: "column",
  alignItems: "center",
};

const errorIconStyle: React.CSSProperties = {
  width: "64px",
  height: "64px",
  borderRadius: "50%",
  backgroundColor: "#fee2e2",
  display: "flex",
  alignItems: "center",
  justifyContent: "center",
  marginBottom: "1rem",
};

const retryBtnStyle: React.CSSProperties = {
  display: "inline-flex",
  alignItems: "center",
  gap: "6px",
  padding: "8px 16px",
  borderRadius: "8px",
  border: "1px solid #d1d5db",
  backgroundColor: "#ffffff",
  fontSize: "0.85rem",
  fontWeight: 600,
  color: "#374151",
  cursor: "pointer",
};

const footerStyle: React.CSSProperties = {
  padding: "1rem 1.25rem",
  backgroundColor: "#f9fafb",
  borderTop: "1px solid #e5e7eb",
};

const controlsRowStyle: React.CSSProperties = {
  display: "flex",
  alignItems: "center",
  justifyContent: "center",
  gap: "14px",
};

const shutterBtnStyle: React.CSSProperties = {
  width: "64px",
  height: "64px",
  borderRadius: "50%",
  backgroundColor: "transparent",
  border: "4px solid #6366f1",
  padding: "4px",
  display: "flex",
  alignItems: "center",
  justifyContent: "center",
  transition: "transform 0.1s ease",
};

const shutterInnerStyle: React.CSSProperties = {
  width: "100%",
  height: "100%",
  borderRadius: "50%",
  backgroundColor: "#6366f1",
  transition: "background-color 0.15s ease",
};

const iconCircleBtnStyle: React.CSSProperties = {
  width: "44px",
  height: "44px",
  borderRadius: "50%",
  border: "1px solid #d1d5db",
  backgroundColor: "#ffffff",
  color: "#374151",
  display: "flex",
  alignItems: "center",
  justifyContent: "center",
  cursor: "pointer",
  boxShadow: "0 1px 2px rgba(0,0,0,0.05)",
};

const primaryBtnStyle: React.CSSProperties = {
  display: "inline-flex",
  alignItems: "center",
  gap: "6px",
  padding: "9px 20px",
  backgroundColor: "#16a34a",
  color: "#ffffff",
  borderRadius: "8px",
  border: "none",
  fontSize: "0.875rem",
  fontWeight: 600,
  cursor: "pointer",
  boxShadow: "0 2px 4px rgba(22, 163, 74, 0.25)",
};

const secondaryBtnStyle: React.CSSProperties = {
  display: "inline-flex",
  alignItems: "center",
  gap: "6px",
  padding: "9px 16px",
  backgroundColor: "#ffffff",
  color: "#374151",
  borderRadius: "8px",
  border: "1px solid #d1d5db",
  fontSize: "0.875rem",
  fontWeight: 600,
  cursor: "pointer",
};
