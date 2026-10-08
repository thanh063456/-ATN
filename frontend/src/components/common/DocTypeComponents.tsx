import React from "react";

export interface DocTypeBadgeProps {
  code?: string;
  name?: string;
}

export const DocTypeBadge: React.FC<DocTypeBadgeProps> = ({ code, name }) => {
  const displayName = name || code || "Chưa phân loại";
  return (
    <span
      data-testid="doc-type-badge"
      style={{
        display: "inline-flex",
        alignItems: "center",
        fontSize: "0.75rem",
        color: "var(--primary-700, #3730a3)",
        backgroundColor: "var(--primary-50, #eef2ff)",
        padding: "0.15rem 0.5rem",
        borderRadius: "4px",
        fontWeight: 600,
      }}
    >
      {displayName}
    </span>
  );
};

export interface NeedsReviewChipProps {
  typeCode?: string;
  confidence?: number;
  needsReview?: boolean;
  threshold?: number;
}

export const NeedsReviewChip: React.FC<NeedsReviewChipProps> = ({
  typeCode,
  confidence,
  needsReview,
  threshold = 0.6,
}) => {
  const shouldShow =
    needsReview === true ||
    typeCode === "KHAC" ||
    (confidence !== undefined && confidence !== null && confidence < threshold);

  if (!shouldShow) return null;

  return (
    <span
      data-testid="needs-review-chip"
      style={{
        display: "inline-flex",
        alignItems: "center",
        gap: "0.25rem",
        fontSize: "0.75rem",
        color: "#b91c1c",
        backgroundColor: "#fee2e2",
        padding: "0.15rem 0.5rem",
        borderRadius: "4px",
        fontWeight: 600,
      }}
    >
      Cần kiểm tra
    </span>
  );
};

export interface FacetFilterChipsProps {
  facets?: Record<string, number>;
  selectedCode?: string;
  totalHits?: number;
  onSelect: (code: string) => void;
}

export const FacetFilterChips: React.FC<FacetFilterChipsProps> = ({
  facets,
  selectedCode = "",
  totalHits = 0,
  onSelect,
}) => {
  if (!facets || Object.keys(facets).length === 0) return null;

  return (
    <div data-testid="facet-filter-chips" style={{ display: "flex", gap: "0.5rem", alignItems: "center", flexWrap: "wrap" }}>
      <button
        type="button"
        data-testid="facet-chip-all"
        onClick={() => onSelect("")}
        style={{
          padding: "0.2rem 0.6rem",
          borderRadius: "9999px",
          fontSize: "0.75rem",
          fontWeight: 600,
          backgroundColor: !selectedCode ? "#4f46e5" : "#f3f4f6",
          color: !selectedCode ? "#ffffff" : "#374151",
          cursor: "pointer",
        }}
      >
        Tất cả ({totalHits})
      </button>
      {Object.entries(facets).map(([code, count]) => (
        <button
          key={code}
          type="button"
          data-testid={`facet-chip-${code}`}
          onClick={() => onSelect(code)}
          style={{
            padding: "0.2rem 0.6rem",
            borderRadius: "9999px",
            fontSize: "0.75rem",
            fontWeight: 600,
            backgroundColor: selectedCode === code ? "#4f46e5" : "#f3f4f6",
            color: selectedCode === code ? "#ffffff" : "#374151",
            cursor: "pointer",
          }}
        >
          {code} ({count})
        </button>
      ))}
    </div>
  );
};

export interface OcrFullButtonProps {
  userRole?: string;
  onClick: () => void;
}

export const OcrFullButton: React.FC<OcrFullButtonProps> = ({ userRole, onClick }) => {
  const isAllowed = userRole === "ADMIN" || userRole === "STAFF";
  if (!isAllowed) return null;

  return (
    <button
      data-testid="ocr-full-button"
      onClick={onClick}
      style={{
        padding: "0.4rem 0.8rem",
        borderRadius: "4px",
        cursor: "pointer",
      }}
    >
      Quét OCR Toàn Bộ
    </button>
  );
};
