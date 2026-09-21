import React from "react";

export type BadgeVariant = "default" | "success" | "warning" | "danger" | "info" | "primary";

interface BadgeProps {
  children: React.ReactNode;
  variant?: BadgeVariant;
  size?: "sm" | "md";
  dot?: boolean;
}

const variantStyles: Record<BadgeVariant, { bg: string; color: string; border: string }> = {
  default: { bg: "#f1f5f9", color: "#475569", border: "#e2e8f0" },
  success: { bg: "#ecfdf5", color: "#065f46", border: "#a7f3d0" },
  warning: { bg: "#fffbeb", color: "#92400e", border: "#fde68a" },
  danger: { bg: "#fef2f2", color: "#991b1b", border: "#fecaca" },
  info: { bg: "#ecfeff", color: "#155e75", border: "#a5f3fc" },
  primary: { bg: "#eef2ff", color: "#3730a3", border: "#c7d2fe" },
};

export const Badge: React.FC<BadgeProps> = ({
  children,
  variant = "default",
  size = "sm",
  dot = false,
}) => {
  const style = variantStyles[variant];

  return (
    <span
      style={{
        display: "inline-flex",
        alignItems: "center",
        gap: "0.35rem",
        padding: size === "sm" ? "0.2rem 0.55rem" : "0.35rem 0.8rem",
        fontSize: size === "sm" ? "0.75rem" : "0.85rem",
        fontWeight: 600,
        borderRadius: "9999px",
        backgroundColor: style.bg,
        color: style.color,
        border: `1px solid ${style.border}`,
        lineHeight: 1.2,
      }}
    >
      {dot && (
        <span
          style={{
            width: "6px",
            height: "6px",
            borderRadius: "50%",
            backgroundColor: style.color,
          }}
        />
      )}
      {children}
    </span>
  );
};

export const OCRStatusBadge: React.FC<{ status: string }> = ({ status }) => {
  switch (status?.toUpperCase()) {
    case "DONE":
    case "SUCCESS":
      return <Badge variant="success" dot>OCR Hoàn thành</Badge>;
    case "PROCESSING":
    case "RUNNING":
      return <Badge variant="info" dot>Đang OCR...</Badge>;
    case "PENDING":
      return <Badge variant="warning" dot>Chờ xử lý</Badge>;
    case "FAILED":
      return <Badge variant="danger" dot>Thất bại</Badge>;
    default:
      return <Badge variant="default">{status || "Không xác định"}</Badge>;
  }
};
