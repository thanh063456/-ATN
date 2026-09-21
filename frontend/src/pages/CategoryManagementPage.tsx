import React, { useState } from "react";
import { FolderKanban, Plus, Check, Edit2, FileText } from "lucide-react";
import { Card } from "../components/common/Card";
import { Button } from "../components/common/Button";
import { Badge } from "../components/common/Badge";
import { useToastStore } from "../stores/useToastStore";

interface CategoryItem {
  id: string;
  name: string;
  code: string;
  description: string;
  docCount: number;
  isActive: boolean;
}

export const CategoryManagementPage: React.FC = () => {
  const { addToast } = useToastStore();
  const [showAddModal, setShowAddModal] = useState(false);

  const [name, setName] = useState("");
  const [code, setCode] = useState("");
  const [desc, setDesc] = useState("");

  const [categories, setCategories] = useState<CategoryItem[]>([
    {
      id: "1",
      name: "Đơn xin nghỉ học tạm thời",
      code: "DON_NGHI_HOC",
      description: "Đơn bảo lưu kết quả học tập, nghỉ học có thời hạn vì lý do cá nhân hoặc y tế.",
      docCount: 48,
      isActive: true,
    },
    {
      id: "2",
      name: "Giấy xác nhận sinh viên",
      code: "GIAY_XAC_NHAN",
      description: "Giấy xác nhận phục vụ vay vốn ngân hàng, tạm hoãn nghĩa vụ quân sự.",
      docCount: 39,
      isActive: true,
    },
    {
      id: "3",
      name: "Hồ sơ xét học bổng khuyến khích",
      code: "HOC_BONG",
      description: "Đơn xin học bổng khuyến khích học tập theo kỳ học.",
      docCount: 34,
      isActive: true,
    },
    {
      id: "4",
      name: "Hồ sơ Khen thưởng - Kỷ luật",
      code: "KHEN_THUONG",
      description: "Các quyết định khen thưởng NCKH, thành tích hoạt động Đoàn/Hội.",
      docCount: 18,
      isActive: true,
    },
    {
      id: "5",
      name: "Đơn xin miễn giảm học phí",
      code: "MIEN_GIAM_HOC_PHI",
      description: "Hồ sơ đối tượng chính sách, hộ nghèo, con thương binh.",
      docCount: 9,
      isActive: true,
    },
  ]);

  const handleAddCategory = (e: React.FormEvent) => {
    e.preventDefault();
    if (!name || !code) return;

    const newCat: CategoryItem = {
      id: Math.random().toString(),
      name: name.trim(),
      code: code.trim().toUpperCase().replace(/\s+/g, "_"),
      description: desc.trim(),
      docCount: 0,
      isActive: true,
    };

    setCategories([...categories, newCat]);
    setShowAddModal(false);
    setName("");
    setCode("");
    setDesc("");

    addToast({
      type: "success",
      title: "Thêm danh mục thành công",
      message: `Đã tạo danh mục biểu mẫu: ${newCat.name}`,
    });
  };

  return (
    <div className="animate-fade-in" style={{ display: "flex", flexDirection: "column", gap: "1.5rem" }}>
      {/* Header */}
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
        <div>
          <h1 style={{ fontSize: "1.5rem", fontWeight: 800, color: "var(--gray-900)" }}>
            Quản lý Danh mục Biểu mẫu CTSV
          </h1>
          <p style={{ fontSize: "0.875rem", color: "var(--gray-500)", marginTop: "0.25rem" }}>
            Cấu hình các loại hồ sơ, mã biểu mẫu và quy chuẩn phân loại tài liệu tự động.
          </p>
        </div>
        <Button variant="primary" leftIcon={<Plus size={16} />} onClick={() => setShowAddModal(true)}>
          + Thêm danh mục mới
        </Button>
      </div>

      {/* Grid of Categories */}
      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(320px, 1fr))", gap: "1.25rem" }}>
        {categories.map((cat) => (
          <Card key={cat.id} padding="md" hoverable>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: "0.75rem" }}>
              <div style={{ width: "40px", height: "40px", borderRadius: "10px", backgroundColor: "var(--primary-50)", color: "var(--primary-600)", display: "flex", alignItems: "center", justifyContent: "center" }}>
                <FileText size={20} />
              </div>
              <Badge variant="success">Hoạt động</Badge>
            </div>

            <h3 style={{ fontSize: "1.05rem", fontWeight: 700, color: "var(--gray-900)" }}>
              {cat.name}
            </h3>
            <div style={{ fontSize: "0.75rem", color: "var(--primary-600)", fontWeight: 600, marginTop: "0.15rem" }}>
              Mã: <code>{cat.code}</code>
            </div>

            <p style={{ fontSize: "0.8125rem", color: "var(--gray-600)", marginTop: "0.5rem", minHeight: "2.4rem", lineHeight: 1.4 }}>
              {cat.description}
            </p>

            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginTop: "1rem", paddingTop: "0.75rem", borderTop: "1px solid var(--border-color)", fontSize: "0.75rem", color: "var(--gray-500)" }}>
              <span>Đang lưu: <strong>{cat.docCount}</strong> tài liệu</span>
              <button style={{ color: "var(--primary-600)", fontWeight: 600, cursor: "pointer" }}>
                Chỉnh sửa
              </button>
            </div>
          </Card>
        ))}
      </div>

      {/* Add Category Modal */}
      {showAddModal && (
        <div
          style={{
            position: "fixed",
            top: 0,
            left: 0,
            right: 0,
            bottom: 0,
            backgroundColor: "rgba(15, 23, 42, 0.6)",
            backdropFilter: "blur(4px)",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            zIndex: 999,
            padding: "1.5rem",
          }}
        >
          <div
            className="animate-fade-in"
            style={{
              width: "100%",
              maxWidth: "480px",
              backgroundColor: "#ffffff",
              borderRadius: "var(--radius-xl)",
              boxShadow: "var(--shadow-xl)",
              padding: "2rem",
            }}
          >
            <h2 style={{ fontSize: "1.25rem", fontWeight: 700, color: "var(--gray-900)", marginBottom: "1.25rem" }}>
              Thêm danh mục biểu mẫu mới
            </h2>

            <form onSubmit={handleAddCategory} style={{ display: "flex", flexDirection: "column", gap: "1rem" }}>
              <div>
                <label style={{ display: "block", fontSize: "0.8125rem", fontWeight: 600, color: "var(--gray-700)", marginBottom: "0.3rem" }}>
                  Tên hiển thị danh mục
                </label>
                <input
                  type="text"
                  required
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  placeholder="vd: Đơn xin chuyển ngành / chuyển lớp"
                  style={{ width: "100%", padding: "0.55rem 0.85rem", borderRadius: "var(--radius-md)", border: "1px solid var(--border-color)", fontSize: "0.875rem" }}
                />
              </div>

              <div>
                <label style={{ display: "block", fontSize: "0.8125rem", fontWeight: 600, color: "var(--gray-700)", marginBottom: "0.3rem" }}>
                  Mã Code định danh (viết hoa, không dấu)
                </label>
                <input
                  type="text"
                  required
                  value={code}
                  onChange={(e) => setCode(e.target.value)}
                  placeholder="vd: DON_CHUYEN_NGANH"
                  style={{ width: "100%", padding: "0.55rem 0.85rem", borderRadius: "var(--radius-md)", border: "1px solid var(--border-color)", fontSize: "0.875rem" }}
                />
              </div>

              <div>
                <label style={{ display: "block", fontSize: "0.8125rem", fontWeight: 600, color: "var(--gray-700)", marginBottom: "0.3rem" }}>
                  Mô tả chi tiết
                </label>
                <textarea
                  value={desc}
                  onChange={(e) => setDesc(e.target.value)}
                  rows={3}
                  placeholder="Mô tả mục đích và đối tượng áp dụng..."
                  style={{ width: "100%", padding: "0.55rem 0.85rem", borderRadius: "var(--radius-md)", border: "1px solid var(--border-color)", fontSize: "0.875rem", resize: "none" }}
                />
              </div>

              <div style={{ display: "flex", justifyContent: "flex-end", gap: "0.75rem", marginTop: "1rem" }}>
                <Button type="button" variant="outline" onClick={() => setShowAddModal(false)}>
                  Hủy
                </Button>
                <Button type="submit" variant="primary">
                  Tạo danh mục
                </Button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
