import React from "react";
import { describe, it, expect, vi } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import {
  DocTypeBadge,
  NeedsReviewChip,
  FacetFilterChips,
  OcrFullButton,
} from "../components/common/DocTypeComponents";

describe("Part E: Frontend Component Tests", () => {
  describe("1. Document Type Badge", () => {
    it("renders document type name when provided", () => {
      render(<DocTypeBadge code="QUYET_DINH" name="Quyết định" />);
      const badge = screen.getByTestId("doc-type-badge");
      expect(badge).toBeInTheDocument();
      expect(badge).toHaveTextContent("Quyết định");
    });

    it("falls back to code when name is not provided", () => {
      render(<DocTypeBadge code="THONG_BAO" />);
      const badge = screen.getByTestId("doc-type-badge");
      expect(badge).toBeInTheDocument();
      expect(badge).toHaveTextContent("THONG_BAO");
    });

    it("shows default fallback when neither code nor name provided", () => {
      render(<DocTypeBadge />);
      const badge = screen.getByTestId("doc-type-badge");
      expect(badge).toHaveTextContent("Chưa phân loại");
    });
  });

  describe("2. 'Cần kiểm tra' Chip", () => {
    it("renders when typeCode is KHAC", () => {
      render(<NeedsReviewChip typeCode="KHAC" confidence={0.9} />);
      const chip = screen.getByTestId("needs-review-chip");
      expect(chip).toBeInTheDocument();
      expect(chip).toHaveTextContent("Cần kiểm tra");
    });

    it("renders when confidence is below threshold (< 0.6)", () => {
      render(<NeedsReviewChip typeCode="CONG_VAN" confidence={0.45} threshold={0.6} />);
      const chip = screen.getByTestId("needs-review-chip");
      expect(chip).toBeInTheDocument();
      expect(chip).toHaveTextContent("Cần kiểm tra");
    });

    it("renders when needsReview is true", () => {
      render(<NeedsReviewChip typeCode="THONG_BAO" confidence={0.95} needsReview={true} />);
      const chip = screen.getByTestId("needs-review-chip");
      expect(chip).toBeInTheDocument();
    });

    it("does NOT render when confidence is high and doc is standard", () => {
      render(<NeedsReviewChip typeCode="QUYET_DINH" confidence={0.88} needsReview={false} threshold={0.6} />);
      expect(screen.queryByTestId("needs-review-chip")).not.toBeInTheDocument();
    });
  });

  describe("3. Type Filter with Facet Counts", () => {
    it("renders facet chips with count numbers", () => {
      const facets = {
        QUYET_DINH: 12,
        CONG_VAN: 5,
        DON_TU: 3,
      };
      render(
        <FacetFilterChips
          facets={facets}
          selectedCode=""
          totalHits={20}
          onSelect={vi.fn()}
        />
      );

      expect(screen.getByTestId("facet-chip-all")).toHaveTextContent("Tất cả (20)");
      expect(screen.getByTestId("facet-chip-QUYET_DINH")).toHaveTextContent("QUYET_DINH (12)");
      expect(screen.getByTestId("facet-chip-CONG_VAN")).toHaveTextContent("CONG_VAN (5)");
      expect(screen.getByTestId("facet-chip-DON_TU")).toHaveTextContent("DON_TU (3)");
    });

    it("triggers onSelect callback when clicking a facet chip", () => {
      const handleSelect = vi.fn();
      const facets = { QUYET_DINH: 10 };
      render(
        <FacetFilterChips
          facets={facets}
          selectedCode=""
          totalHits={10}
          onSelect={handleSelect}
        />
      );

      fireEvent.click(screen.getByTestId("facet-chip-QUYET_DINH"));
      expect(handleSelect).toHaveBeenCalledWith("QUYET_DINH");

      fireEvent.click(screen.getByTestId("facet-chip-all"));
      expect(handleSelect).toHaveBeenCalledWith("");
    });
  });

  describe("4. OCR-Full Button Visibility (Role-based RBAC)", () => {
    it("renders for ADMIN role", () => {
      render(<OcrFullButton userRole="ADMIN" onClick={vi.fn()} />);
      const btn = screen.getByTestId("ocr-full-button");
      expect(btn).toBeInTheDocument();
      expect(btn).toHaveTextContent("Quét OCR Toàn Bộ");
    });

    it("renders for STAFF role", () => {
      render(<OcrFullButton userRole="STAFF" onClick={vi.fn()} />);
      const btn = screen.getByTestId("ocr-full-button");
      expect(btn).toBeInTheDocument();
    });

    it("does NOT render for STUDENT role", () => {
      render(<OcrFullButton userRole="STUDENT" onClick={vi.fn()} />);
      expect(screen.queryByTestId("ocr-full-button")).not.toBeInTheDocument();
    });

    it("does NOT render for anonymous/guest users", () => {
      render(<OcrFullButton userRole={undefined} onClick={vi.fn()} />);
      expect(screen.queryByTestId("ocr-full-button")).not.toBeInTheDocument();
    });

    it("handles click callback when allowed", () => {
      const handleClick = vi.fn();
      render(<OcrFullButton userRole="ADMIN" onClick={handleClick} />);
      fireEvent.click(screen.getByTestId("ocr-full-button"));
      expect(handleClick).toHaveBeenCalledTimes(1);
    });
  });
});
