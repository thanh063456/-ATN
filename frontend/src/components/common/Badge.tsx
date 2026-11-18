import React from "react";

export type BadgeVariant = "default" | "success" | "warning" | "danger" | "info" | "primary";

interface BadgeProps {
  children: React.ReactNode;
  variant?: BadgeVariant;
  size?: "sm" | "md";
  dot?: boolean;
  className?: string;
  style?: React.CSSProperties;
}

const variantClasses: Record<BadgeVariant, { badge: string; dot: string }> = {
  default: {
    badge: "bg-slate-100 text-slate-700 border-slate-200",
    dot: "bg-slate-500",
  },
  success: {
    badge: "bg-emerald-50 text-emerald-800 border-emerald-200 font-medium",
    dot: "bg-emerald-600",
  },
  warning: {
    badge: "bg-amber-50 text-amber-800 border-amber-200 font-medium",
    dot: "bg-amber-600",
  },
  danger: {
    badge: "bg-rose-50 text-rose-800 border-rose-200 font-medium",
    dot: "bg-rose-600",
  },
  info: {
    badge: "bg-sky-50 text-sky-800 border-sky-200 font-medium",
    dot: "bg-sky-600",
  },
  primary: {
    badge: "bg-dlu-navy-50 text-dlu-navy-900 border-dlu-navy-200 font-semibold",
    dot: "bg-dlu-navy-700",
  },
};

export const Badge: React.FC<BadgeProps> = ({
  children,
  variant = "default",
  size = "sm",
  dot = false,
  className = "",
  style,
}) => {
  const styles = variantClasses[variant];
  const sizeClass = size === "sm" ? "text-xs px-2 py-0.5 gap-1.5" : "text-sm px-2.5 py-1 gap-2";

  return (
    <span
      className={`inline-flex flex-nowrap items-center rounded border font-medium leading-none select-none whitespace-nowrap shrink-0 ${sizeClass} ${styles.badge} ${className}`}
      style={style}
    >
      {dot && <span className={`w-1.5 h-1.5 rounded-full shrink-0 ${styles.dot}`} />}
      <span className="whitespace-nowrap">{children}</span>
    </span>
  );
};

export const OCRStatusBadge: React.FC<{ status: string; className?: string }> = ({ status, className = "" }) => {
  switch (status?.toUpperCase()) {
    case "DONE":
    case "SUCCESS":
      return <Badge variant="success" dot className={className}>OCR Hoàn thành</Badge>;
    case "PROCESSING":
    case "RUNNING":
      return <Badge variant="info" dot className={className}>Đang OCR...</Badge>;
    case "PENDING":
      return <Badge variant="warning" dot className={className}>Chờ xử lý</Badge>;
    case "FAILED":
      return <Badge variant="danger" dot className={className}>Thất bại</Badge>;
    default:
      return <Badge variant="default" className={className}>{status || "Không xác định"}</Badge>;
  }
};
