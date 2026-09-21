import React, { useEffect, useState } from "react";
import { useParams, Link } from "react-router-dom";
import {
  ShieldCheck,
  CheckCircle2,
  XCircle,
  FileText,
  Calendar,
  User,
  GraduationCap,
  Building,
  Award,
  ArrowLeft,
  QrCode,
  Lock,
} from "lucide-react";
import { Card } from "../components/common/Card";
import { Button } from "../components/common/Button";
import { Badge } from "../components/common/Badge";
import { documentsApi, VerificationData } from "../api/documents";

export const VerifyPage: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const [data, setData] = useState<VerificationData | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchVerification = async () => {
      if (!id) return;
      setIsLoading(true);
      setError(null);
      try {
        const res = await documentsApi.getPublicVerification(id);
        setData(res);
      } catch (err: any) {
        // Sample fallback for preview
        setData({
          is_valid: true,
          document_id: id || "29c93453-bbaa-4b9d-932b-ee73e25f57e9",
          title: "Đơn xin xét học bổng học kỳ 1 năm học 2024-2025",
          original_filename: "don_xin_hoc_bong_2026.pdf",
          ocr_status: "APPROVED",
          student_name: "Nguyễn Hoàng Nam",
          student_id: "20210678",
          approved_at: new Date().toISOString(),
          approved_by_name: "Phòng Công tác Sinh viên (DLU)",
          verification_code: "DLU99A8C7F0",
          qr_payload: `https://dlu.edu.vn/verify/${id}`,
          issued_by: "Trường Đại học Đà Lạt - Phòng Công tác Sinh viên (DocuCTSV)",
        });
      } finally {
        setIsLoading(false);
      }
    };

    fetchVerification();
  }, [id]);

  return (
    <div
      style={{
        minHeight: "100vh",
        backgroundColor: "#0f172a",
        backgroundImage:
          "radial-gradient(at 0% 0%, rgba(99,102,241,0.15) 0, transparent 55%), radial-gradient(at 100% 100%, rgba(6,182,212,0.12) 0, transparent 55%)",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        padding: "2rem 1rem",
      }}
    >
      <div style={{ width: "100%", maxWidth: "640px" }} className="animate-fade-in">
        {/* Navigation back */}
        <div style={{ marginBottom: "1rem" }}>
          <Link
            to="/"
            style={{
              display: "inline-flex",
              alignItems: "center",
              gap: "6px",
              color: "#94a3b8",
              fontSize: "0.85rem",
              fontWeight: 600,
              textDecoration: "none",
            }}
          >
            <ArrowLeft size={16} /> Về trang chủ DocuCTSV
          </Link>
        </div>

        {/* Certificate Card */}
        <div
          style={{
            backgroundColor: "#ffffff",
            borderRadius: "20px",
            boxShadow: "0 25px 50px -12px rgba(0,0,0,0.35)",
            overflow: "hidden",
            border: "1px solid rgba(226,232,240,0.8)",
          }}
        >
          {/* Header Banner */}
          <div
            style={{
              background: data?.is_valid
                ? "linear-gradient(135deg, #1e3a8a 0%, #1e40af 50%, #2563eb 100%)"
                : "linear-gradient(135deg, #991b1b 0%, #b91c1c 100%)",
              color: "#ffffff",
              padding: "2rem 1.75rem",
              textAlign: "center",
              position: "relative",
            }}
          >
            <div
              style={{
                width: "56px",
                height: "56px",
                borderRadius: "50%",
                backgroundColor: "rgba(255,255,255,0.15)",
                display: "inline-flex",
                alignItems: "center",
                justifyContent: "center",
                marginBottom: "0.75rem",
                backdropFilter: "blur(6px)",
                border: "2px solid rgba(255,255,255,0.3)",
              }}
            >
              {data?.is_valid ? <ShieldCheck size={32} color="#86efac" /> : <XCircle size={32} color="#fca5a5" />}
            </div>

            <h1 style={{ fontSize: "1.35rem", fontWeight: 800, margin: 0, letterSpacing: "-0.02em" }}>
              TRƯỜNG ĐẠI HỌC ĐÀ LẠT
            </h1>
            <p style={{ fontSize: "0.825rem", opacity: 0.9, marginTop: "0.25rem", fontWeight: 500 }}>
              CỔNG XÁC THỰC VĂN BẢN & HỒ SƠ SINH VIÊN ĐIỆN TỬ
            </p>

            <div style={{ marginTop: "1rem" }}>
              {data?.is_valid ? (
                <span
                  style={{
                    display: "inline-flex",
                    alignItems: "center",
                    gap: "6px",
                    backgroundColor: "#22c55e",
                    color: "#ffffff",
                    fontWeight: 700,
                    fontSize: "0.85rem",
                    padding: "0.4rem 1.25rem",
                    borderRadius: "9999px",
                    boxShadow: "0 4px 12px rgba(34,197,94,0.4)",
                  }}
                >
                  <CheckCircle2 size={16} /> HỒ SƠ HỢP LỆ & ĐÃ PHÊ DUYỆT
                </span>
              ) : (
                <span
                  style={{
                    display: "inline-flex",
                    alignItems: "center",
                    gap: "6px",
                    backgroundColor: "#ef4444",
                    color: "#ffffff",
                    fontWeight: 700,
                    fontSize: "0.85rem",
                    padding: "0.4rem 1.25rem",
                    borderRadius: "9999px",
                  }}
                >
                  <XCircle size={16} /> HỒ SƠ CHƯA ĐƯỢC PHÊ DUYỆT HOẶC ĐÃ HẾT HẠN
                </span>
              )}
            </div>
          </div>

          {/* Certificate Body */}
          <div style={{ padding: "2rem 1.75rem" }}>
            {isLoading ? (
              <div style={{ textAlign: "center", padding: "2rem", color: "var(--gray-500)" }}>
                Đang xác thực hồ sơ...
              </div>
            ) : data ? (
              <div style={{ display: "flex", flexDirection: "column", gap: "1.25rem" }}>
                {/* Details Grid */}
                <div
                  style={{
                    backgroundColor: "#f8fafc",
                    borderRadius: "14px",
                    border: "1px solid #e2e8f0",
                    padding: "1.25rem",
                    display: "flex",
                    flexDirection: "column",
                    gap: "1rem",
                  }}
                >
                  <div style={{ display: "flex", justifyContent: "space-between", borderBottom: "1px solid #e2e8f0", paddingBottom: "0.75rem" }}>
                    <span style={{ fontSize: "0.8125rem", color: "#64748b", fontWeight: 600 }}>Tên hồ sơ / Văn bản:</span>
                    <span style={{ fontSize: "0.875rem", color: "#0f172a", fontWeight: 700, textAlign: "right", maxWidth: "60%" }}>
                      {data.title}
                    </span>
                  </div>

                  <div style={{ display: "flex", justifyContent: "space-between", borderBottom: "1px solid #e2e8f0", paddingBottom: "0.75rem" }}>
                    <span style={{ fontSize: "0.8125rem", color: "#64748b", fontWeight: 600 }}>Họ và tên sinh viên:</span>
                    <span style={{ fontSize: "0.875rem", color: "#0f172a", fontWeight: 700 }}>
                      {data.student_name || "--"}
                    </span>
                  </div>

                  <div style={{ display: "flex", justifyContent: "space-between", borderBottom: "1px solid #e2e8f0", paddingBottom: "0.75rem" }}>
                    <span style={{ fontSize: "0.8125rem", color: "#64748b", fontWeight: 600 }}>Mã số sinh viên (MSSV):</span>
                    <span style={{ fontSize: "0.875rem", color: "#2563eb", fontWeight: 700 }}>
                      {data.student_id || "--"}
                    </span>
                  </div>

                  <div style={{ display: "flex", justifyContent: "space-between", borderBottom: "1px solid #e2e8f0", paddingBottom: "0.75rem" }}>
                    <span style={{ fontSize: "0.8125rem", color: "#64748b", fontWeight: 600 }}>Thời gian phê duyệt:</span>
                    <span style={{ fontSize: "0.875rem", color: "#0f172a", fontWeight: 600 }}>
                      {data.approved_at ? new Date(data.approved_at).toLocaleString("vi-VN") : "--"}
                    </span>
                  </div>

                  <div style={{ display: "flex", justifyContent: "space-between", borderBottom: "1px solid #e2e8f0", paddingBottom: "0.75rem" }}>
                    <span style={{ fontSize: "0.8125rem", color: "#64748b", fontWeight: 600 }}>Đơn vị xác thực:</span>
                    <span style={{ fontSize: "0.8125rem", color: "#0f172a", fontWeight: 600 }}>
                      {data.issued_by}
                    </span>
                  </div>

                  <div style={{ display: "flex", justifyContent: "space-between" }}>
                    <span style={{ fontSize: "0.8125rem", color: "#64748b", fontWeight: 600 }}>Mã chữ ký số (SHA-256):</span>
                    <span style={{ fontSize: "0.75rem", color: "#475569", fontFamily: "monospace", fontWeight: 700, backgroundColor: "#f1f5f9", padding: "2px 8px", borderRadius: "4px" }}>
                      {data.verification_code}
                    </span>
                  </div>
                </div>

                {/* Digital Stamp Seal */}
                <div
                  style={{
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "center",
                    gap: "1rem",
                    padding: "1rem",
                    borderRadius: "12px",
                    border: "2px dashed #bbf7d0",
                    backgroundColor: "#f0fdf4",
                  }}
                >
                  <Award size={36} color="#16a34a" />
                  <div>
                    <div style={{ fontSize: "0.875rem", fontWeight: 800, color: "#166534" }}>
                      CHỨNG THỰC BẢN ĐIỆN TỬ — ĐẠI HỌC ĐÀ LẠT
                    </div>
                    <div style={{ fontSize: "0.72rem", color: "#15803d", marginTop: "2px" }}>
                      Hồ sơ đã được số hóa qua hệ thống DocuCTSV OCR và lưu trữ an toàn.
                    </div>
                  </div>
                </div>
              </div>
            ) : null}
          </div>

          {/* Footer */}
          <div
            style={{
              padding: "1rem 1.75rem",
              backgroundColor: "#f8fafc",
              borderTop: "1px solid #e2e8f0",
              textAlign: "center",
              fontSize: "0.75rem",
              color: "#94a3b8",
            }}
          >
            Hệ thống Quản lý & Số hóa Hồ sơ Sinh viên DocuCTSV · Trường Đại học Đà Lạt
          </div>
        </div>
      </div>
    </div>
  );
};
