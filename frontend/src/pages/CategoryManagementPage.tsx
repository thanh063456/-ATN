import React, { useEffect, useState } from "react";
import { Plus, FileText, Search, RefreshCw, Layers, CheckCircle2, FolderCheck, AlertCircle } from "lucide-react";
import { Card } from "../components/common/Card";
import { Button } from "../components/common/Button";
import { Badge } from "../components/common/Badge";
import { documentsApi, CategoryAdminItem } from "../api/documents";
import { useToastStore } from "../stores/useToastStore";

export const CategoryManagementPage: React.FC = () => {
  const { addToast } = useToastStore();
  const [categories, setCategories] = useState<CategoryAdminItem[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState<"ALL" | "ACTIVE" | "INACTIVE">("ALL");

  const [showAddModal, setShowAddModal] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [togglingId, setTogglingId] = useState<string | null>(null);

  // Form states
  const [name, setName] = useState("");
  const [code, setCode] = useState("");
  const [desc, setDesc] = useState("");

  const loadCategories = async () => {
    setIsLoading(true);
    try {
      const data = await documentsApi.getCategories();
      setCategories(data);
    } catch (err: any) {
      addToast({
        type: "error",
        title: "Không thể tải danh mục từ Supabase",
        message: err?.response?.data?.message || err.message || "Vui lòng kiểm tra kết nối CSDL.",
      });
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    loadCategories();
  }, []);

  const handleToggleStatus = async (cat: CategoryAdminItem) => {
    setTogglingId(cat.id);
    try {
      await documentsApi.toggleCategoryStatus(cat.id);
      setCategories((prev) =>
        prev.map((c) => (c.id === cat.id ? { ...c, is_active: !c.is_active } : c))
      );
      addToast({
        type: !cat.is_active ? "success" : "warning",
        title: !cat.is_active ? "Đã kích hoạt danh mục" : "Đã tạm dừng danh mục",
        message: `${cat.name} (${cat.code})`,
      });
    } catch (err: any) {
      addToast({
        type: "error",
        title: "Lỗi cập nhật trạng thái",
        message: err?.response?.data?.message || err.message || "Không thể đổi trạng thái danh mục.",
      });
    } finally {
      setTogglingId(null);
    }
  };

  const handleAddCategory = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!name || !code) return;

    setIsSubmitting(true);
    try {
      const created = await documentsApi.createCategory({
        name: name.trim(),
        code: code.trim().toUpperCase().replace(/\s+/g, "_"),
        description: desc.trim() || undefined,
      });

      setCategories((prev) => [created, ...prev]);
      setShowAddModal(false);
      setName("");
      setCode("");
      setDesc("");

      addToast({
        type: "success",
        title: "Thêm danh mục thành công",
        message: `Đã lưu danh mục "${created.name}" vào Supabase.`,
      });
    } catch (err: any) {
      addToast({
        type: "error",
        title: "Không thể thêm danh mục",
        message: err?.response?.data?.message || err.message || "Vui lòng thử lại sau.",
      });
    } finally {
      setIsSubmitting(false);
    }
  };

  const filteredCategories = categories.filter((cat) => {
    const q = search.trim().toLowerCase();
    const matchSearch =
      !q ||
      cat.name.toLowerCase().includes(q) ||
      cat.code.toLowerCase().includes(q) ||
      (cat.description && cat.description.toLowerCase().includes(q));

    const matchStatus =
      statusFilter === "ALL" ||
      (statusFilter === "ACTIVE" && cat.is_active) ||
      (statusFilter === "INACTIVE" && !cat.is_active);

    return matchSearch && matchStatus;
  });

  const totalDocs = categories.reduce((sum, c) => sum + (c.doc_count || 0), 0);
  const activeCount = categories.filter((c) => c.is_active).length;

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Header */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-xl sm:text-2xl font-bold text-slate-900 tracking-tight">
              Quản lý Danh mục Biểu mẫu CTSV
            </h1>
            <span className="text-[11px] font-semibold text-emerald-800 bg-emerald-50 px-2 py-0.5 rounded border border-emerald-200">
              Supabase Live
            </span>
          </div>
          <p className="text-xs sm:text-sm text-slate-500 mt-1">
            Cấu hình các loại hồ sơ, mã biểu mẫu và quy chuẩn phân loại tài liệu tự động cho Đại học Đà Lạt.
          </p>
        </div>
        <div className="flex items-center gap-2 w-full sm:w-auto">
          <Button
            variant="outline"
            leftIcon={<RefreshCw size={15} className={isLoading ? "animate-spin" : ""} />}
            onClick={loadCategories}
            disabled={isLoading}
          >
            Làm mới
          </Button>
          <Button
            variant="primary"
            leftIcon={<Plus size={16} />}
            onClick={() => setShowAddModal(true)}
          >
            Thêm danh mục mới
          </Button>
        </div>
      </div>

      {/* KPI Stats */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-3.5 sm:gap-4">
        <Card padding="md" className="border-slate-200/90 shadow-card">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-xs font-semibold text-slate-700 tracking-wide uppercase">
                Tổng danh mục
              </p>
              <h3 className="text-2xl font-black text-slate-900 mt-1">
                {categories.length}
              </h3>
              <p className="text-[11px] text-slate-400 mt-0.5">Loại văn bản chuẩn DLU</p>
            </div>
            <div className="w-10 h-10 rounded-lg bg-dlu-navy-50 text-dlu-navy-800 border border-dlu-navy-200/60 flex items-center justify-center">
              <Layers size={20} />
            </div>
          </div>
        </Card>

        <Card padding="md" className="border-slate-200/90 shadow-card">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-xs font-semibold text-slate-700 tracking-wide uppercase">
                Đang áp dụng
              </p>
              <h3 className="text-2xl font-black text-emerald-700 mt-1">
                {activeCount}
              </h3>
              <p className="text-[11px] text-slate-400 mt-0.5">Sẵn sàng nhận diện OCR</p>
            </div>
            <div className="w-10 h-10 rounded-lg bg-emerald-50 text-emerald-700 border border-emerald-200 flex items-center justify-center">
              <CheckCircle2 size={20} />
            </div>
          </div>
        </Card>

        <Card padding="md" className="border-slate-200/90 shadow-card">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-xs font-semibold text-slate-700 tracking-wide uppercase">
                Tổng hồ sơ đã phân loại
              </p>
              <h3 className="text-2xl font-black text-dlu-navy-900 mt-1">
                {totalDocs}
              </h3>
              <p className="text-[11px] text-slate-400 mt-0.5">Văn bản số hóa trong CSDL</p>
            </div>
            <div className="w-10 h-10 rounded-lg bg-blue-50 text-blue-700 border border-blue-200 flex items-center justify-center">
              <FolderCheck size={20} />
            </div>
          </div>
        </Card>
      </div>

      {/* Filter and Search Bar */}
      <Card padding="sm" className="border-slate-200/90 shadow-card">
        <div className="flex flex-col sm:flex-row gap-3 items-stretch sm:items-center justify-between">
          <div className="relative flex-1">
            <Search
              size={15}
              className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400 pointer-events-none"
            />
            <input
              type="text"
              placeholder="Tìm theo tên danh mục, mã biểu mẫu (vd: KE_HOACH, THONG_BAO)..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="w-full pl-9 pr-3 py-2 text-xs sm:text-sm bg-slate-50 hover:bg-slate-100/70 focus:bg-white rounded-md border border-slate-200 outline-none focus:ring-2 focus:ring-dlu-navy-500/20 focus:border-dlu-navy-600 transition-colors"
            />
          </div>

          <div className="flex items-center gap-2">
            <span className="text-xs font-semibold text-slate-500 whitespace-nowrap">
              Trạng thái:
            </span>
            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value as any)}
              className="px-3 py-2 text-xs sm:text-sm bg-white rounded-md border border-slate-200 text-slate-700 outline-none focus:ring-2 focus:ring-dlu-navy-500/20 focus:border-dlu-navy-600 cursor-pointer"
            >
              <option value="ALL">Tất cả ({categories.length})</option>
              <option value="ACTIVE">Đang áp dụng ({activeCount})</option>
              <option value="INACTIVE">Tạm dừng ({categories.length - activeCount})</option>
            </select>
          </div>
        </div>
      </Card>

      {/* Loading state */}
      {isLoading ? (
        <div className="py-20 flex flex-col items-center justify-center text-slate-400">
          <RefreshCw size={28} className="animate-spin mb-3 text-dlu-navy-600" />
          <p className="text-xs sm:text-sm font-medium">Đang tải danh mục từ Supabase...</p>
        </div>
      ) : filteredCategories.length === 0 ? (
        /* Empty state */
        <div className="py-16 text-center bg-white rounded-lg border border-dashed border-slate-200 p-8">
          <div className="w-12 h-12 rounded-full bg-slate-100 text-slate-400 flex items-center justify-center mx-auto mb-3">
            <AlertCircle size={24} />
          </div>
          <h4 className="text-sm font-bold text-slate-800">Không tìm thấy danh mục phù hợp</h4>
          <p className="text-xs text-slate-500 mt-1 max-w-sm mx-auto">
            Thử thay đổi từ khóa tìm kiếm hoặc bấm &ldquo;Làm mới&rdquo; để tải lại dữ liệu từ Supabase.
          </p>
        </div>
      ) : (
        /* Grid of Categories */
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {filteredCategories.map((cat) => (
            <Card key={cat.id} padding="md" hoverable className="flex flex-col justify-between border-slate-200/90 shadow-card">
              <div>
                <div className="flex justify-between items-start mb-3">
                  <div className="w-9 h-9 rounded-md bg-dlu-navy-50 text-dlu-navy-800 border border-dlu-navy-200/60 flex items-center justify-center">
                    <FileText size={18} />
                  </div>
                  {cat.is_active ? (
                    <Badge variant="success" size="sm" dot>Đang áp dụng</Badge>
                  ) : (
                    <Badge variant="default" size="sm">Tạm dừng</Badge>
                  )}
                </div>

                <h3 className="text-sm sm:text-base font-bold text-slate-900 leading-snug">
                  {cat.name}
                </h3>
                <div className="text-xs mt-1.5 flex items-center gap-1.5">
                  <span className="text-slate-400 font-medium">Mã:</span>
                  <code className="font-mono text-[11px] bg-slate-100 text-dlu-navy-900 px-1.5 py-0.5 rounded font-semibold border border-slate-200">
                    {cat.code}
                  </code>
                </div>

                <p className="text-xs text-slate-500 mt-2.5 line-clamp-3 leading-relaxed">
                  {cat.description || "Chưa có mô tả chi tiết cho loại biểu mẫu này."}
                </p>
              </div>

              <div className="flex justify-between items-center mt-4 pt-3 border-t border-slate-100 text-xs text-slate-500">
                <span>
                  Đang lưu: <strong className="text-dlu-navy-900 font-mono text-xs">{cat.doc_count || 0}</strong> văn bản
                </span>
                <button
                  type="button"
                  disabled={togglingId === cat.id}
                  onClick={() => handleToggleStatus(cat)}
                  className={`text-[11px] font-semibold px-2 py-1 rounded transition-colors ${
                    cat.is_active
                      ? "text-amber-700 hover:bg-amber-50"
                      : "text-emerald-700 hover:bg-emerald-50"
                  }`}
                >
                  {togglingId === cat.id ? "Đang xử lý..." : cat.is_active ? "Tạm dừng" : "Kích hoạt"}
                </button>
              </div>
            </Card>
          ))}
        </div>
      )}

      {/* Add Category Modal */}
      {showAddModal && (
        <div className="fixed inset-0 bg-slate-900/50 backdrop-blur-xs flex items-center justify-center z-50 p-4 animate-fade-in">
          <div className="bg-white rounded-lg shadow-modal border border-slate-200/90 w-full max-w-md p-6">
            <h2 className="text-base sm:text-lg font-bold text-slate-900 mb-1">
              Thêm danh mục biểu mẫu mới
            </h2>
            <p className="text-xs text-slate-500 mb-4">
              Dữ liệu sẽ được lưu trực tiếp vào bảng <code className="text-dlu-navy-700 font-mono">document_categories</code> trên Supabase.
            </p>

            <form onSubmit={handleAddCategory} className="space-y-3.5">
              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">
                  Tên danh mục biểu mẫu <span className="text-rose-500">*</span>
                </label>
                <input
                  type="text"
                  required
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  placeholder="vd: Giấy xác nhận tình trạng học tập"
                  className="w-full px-3 py-2 rounded-md border border-slate-200 text-xs sm:text-sm bg-white text-slate-900 outline-none focus:ring-2 focus:ring-dlu-navy-500/20 focus:border-dlu-navy-600"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">
                  Mã Code định danh (viết hoa, không dấu) <span className="text-rose-500">*</span>
                </label>
                <input
                  type="text"
                  required
                  value={code}
                  onChange={(e) => setCode(e.target.value)}
                  placeholder="vd: GIAY_XAC_NHAN_HOC_TAP"
                  className="w-full px-3 py-2 rounded-md border border-slate-200 text-xs sm:text-sm bg-white text-slate-900 font-mono outline-none focus:ring-2 focus:ring-dlu-navy-500/20 focus:border-dlu-navy-600"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">
                  Mô tả chi tiết quy định / biểu mẫu
                </label>
                <textarea
                  value={desc}
                  onChange={(e) => setDesc(e.target.value)}
                  rows={3}
                  placeholder="Mô tả đối tượng áp dụng, thủ tục hoặc lưu ý của biểu mẫu..."
                  className="w-full px-3 py-2 rounded-md border border-slate-200 text-xs sm:text-sm bg-white text-slate-900 resize-none outline-none focus:ring-2 focus:ring-dlu-navy-500/20 focus:border-dlu-navy-600"
                />
              </div>

              <div className="flex justify-end gap-2.5 pt-3 border-t border-slate-100">
                <Button
                  type="button"
                  variant="outline"
                  onClick={() => setShowAddModal(false)}
                  disabled={isSubmitting}
                >
                  Hủy
                </Button>
                <Button
                  type="submit"
                  variant="primary"
                  disabled={isSubmitting}
                >
                  {isSubmitting ? "Đang lưu Supabase..." : "Tạo danh mục"}
                </Button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
