import React, { useState, useEffect, useRef } from "react";
import { useNavigate } from "react-router-dom";
import {
  Bell,
  CheckCircle2,
  XCircle,
  Clock,
  ShieldCheck,
  UserCheck,
  GraduationCap,
  ExternalLink,
  CheckCheck,
  RefreshCw,
  Inbox,
} from "lucide-react";
import { documentsApi, DocumentNotificationItem } from "../../api/documents";
import { useAuthStore } from "../../stores/useAuthStore";

export const NotificationDropdown: React.FC = () => {
  const navigate = useNavigate();
  const { user } = useAuthStore();
  const [isOpen, setIsOpen] = useState(false);
  const [notifications, setNotifications] = useState<DocumentNotificationItem[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [readIds, setReadIds] = useState<Set<string>>(() => {
    try {
      const saved = localStorage.getItem("read_notification_ids");
      return saved ? new Set(JSON.parse(saved)) : new Set();
    } catch {
      return new Set();
    }
  });

  const dropdownRef = useRef<HTMLDivElement>(null);

  const fetchNotifications = async () => {
    if (!user) return;
    try {
      setIsLoading(true);
      const res = await documentsApi.getNotifications(25);
      setNotifications(res.items || []);
    } catch (err) {
      console.warn("Failed to load notifications:", err);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchNotifications();
    const timer = setInterval(fetchNotifications, 20000);
    return () => clearInterval(timer);
  }, [user?.id]);

  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setIsOpen(false);
      }
    };
    if (isOpen) {
      document.addEventListener("mousedown", handleClickOutside);
    }
    return () => {
      document.removeEventListener("mousedown", handleClickOutside);
    };
  }, [isOpen]);

  const markAsRead = (id: string) => {
    setReadIds((prev) => {
      const next = new Set(prev);
      next.add(id);
      try {
        localStorage.setItem("read_notification_ids", JSON.stringify(Array.from(next)));
      } catch (e) {
        // ignore
      }
      return next;
    });
  };

  const markAllAsRead = () => {
    const allIds = new Set(notifications.map((n) => n.id));
    setReadIds(allIds);
    try {
      localStorage.setItem("read_notification_ids", JSON.stringify(Array.from(allIds)));
    } catch (e) {
      // ignore
    }
  };

  const handleNotificationClick = (item: DocumentNotificationItem) => {
    markAsRead(item.id);
    setIsOpen(false);
    navigate(`/documents/${item.document_id}`);
  };

  const unreadCount = notifications.filter((n) => !readIds.has(n.id)).length;

  const formatTime = (isoString: string) => {
    try {
      const d = new Date(isoString);
      const now = new Date();
      const diffMs = now.getTime() - d.getTime();
      const diffMin = Math.floor(diffMs / 60000);
      const diffHour = Math.floor(diffMin / 60);
      const diffDay = Math.floor(diffHour / 24);

      if (diffMin < 1) return "Vừa xong";
      if (diffMin < 60) return `${diffMin} phút trước`;
      if (diffHour < 24) return `${diffHour} giờ trước`;
      if (diffDay < 7) return `${diffDay} ngày trước`;
      return d.toLocaleDateString("vi-VN", {
        day: "2-digit",
        month: "2-digit",
        year: "numeric",
        hour: "2-digit",
        minute: "2-digit",
      });
    } catch {
      return isoString;
    }
  };

  const isStudent = user?.role === "STUDENT";

  return (
    <div className="relative" ref={dropdownRef}>
      {/* Nút Chuông Thông Báo */}
      <button
        onClick={() => {
          setIsOpen(!isOpen);
          if (!isOpen) fetchNotifications();
        }}
        className={`relative flex items-center justify-center w-8 h-8 sm:w-9 sm:h-9 rounded-full border transition-all ${
          isOpen
            ? "border-dlu-navy-600 bg-dlu-navy-50 text-dlu-navy-900 ring-2 ring-dlu-navy-500/20"
            : "border-slate-200 bg-white text-slate-600 hover:text-slate-900 hover:bg-slate-50"
        }`}
        title="Thông báo xét duyệt hồ sơ"
        aria-label="Thông báo xét duyệt hồ sơ"
      >
        <Bell size={17} className={unreadCount > 0 ? "animate-pulse text-dlu-navy-700" : ""} />

        {unreadCount > 0 && (
          <span className="absolute -top-1 -right-1 bg-rose-600 text-white text-[10px] font-bold min-w-[16px] h-4 leading-4 rounded-full text-center px-1 border-2 border-white shadow-xs">
            {unreadCount > 9 ? "9+" : unreadCount}
          </span>
        )}
      </button>

      {/* Popover Menu Dropdown */}
      {isOpen && (
        <div className="absolute top-[calc(100%+8px)] -right-16 sm:right-0 w-[380px] sm:w-[420px] max-w-[92vw] bg-white rounded-lg shadow-paper-lg border border-slate-200/90 z-50 overflow-hidden animate-fade-in">
          {/* Header */}
          <div className="px-4 py-3 bg-slate-50/90 border-b border-slate-200/80 flex items-center justify-between">
            <div>
              <div className="flex items-center gap-1.5">
                <span className="font-bold text-sm text-slate-900">
                  Thông báo xét duyệt
                </span>
                {unreadCount > 0 && (
                  <span className="bg-rose-100 text-rose-800 text-[10px] font-bold px-1.5 py-0.5 rounded-full">
                    {unreadCount} mới
                  </span>
                )}
              </div>
              <div className="text-[11px] text-slate-500 mt-0.5">
                {isStudent
                  ? "Phản hồi phê duyệt từ Cán bộ CTSV & Quản trị viên"
                  : "Lịch sử phê duyệt & Hồ sơ sinh viên nộp"}
              </div>
            </div>

            <div className="flex items-center gap-1.5">
              <button
                onClick={fetchNotifications}
                disabled={isLoading}
                className="p-1 rounded text-slate-400 hover:text-slate-700 hover:bg-slate-200/60 transition-colors"
                title="Làm mới"
              >
                <RefreshCw size={13} className={isLoading ? "animate-spin" : ""} />
              </button>

              {unreadCount > 0 && (
                <button
                  onClick={markAllAsRead}
                  className="flex items-center gap-1 text-[11px] font-semibold text-dlu-navy-700 hover:text-dlu-navy-900 px-2 py-0.5 rounded hover:bg-dlu-navy-50 transition-colors whitespace-nowrap shrink-0"
                  title="Đánh dấu tất cả là đã đọc"
                >
                  <CheckCheck size={13} className="shrink-0" />
                  <span className="whitespace-nowrap">Đã đọc</span>
                </button>
              )}
            </div>
          </div>

          {/* Danh sách thông báo */}
          <div className="max-h-[380px] overflow-y-auto divide-y divide-slate-100">
            {notifications.length === 0 ? (
              <div className="py-10 px-4 text-center text-slate-400 flex flex-col items-center gap-2">
                <Inbox size={32} className="text-slate-300" />
                <span className="text-xs font-semibold text-slate-700">
                  Chưa có thông báo phê duyệt nào
                </span>
                <span className="text-[11px] text-slate-400 max-w-[280px]">
                  {isStudent
                    ? "Khi hồ sơ của bạn được Cán bộ Công tác Sinh viên hoặc Quản trị viên duyệt, hệ thống sẽ thông báo tại đây."
                    : "Các yêu cầu và quyết định phê duyệt mới sẽ xuất hiện tại đây."}
                </span>
              </div>
            ) : (
              notifications.map((item) => {
                const isRead = readIds.has(item.id);
                const isApproved = item.action === "APPROVE_DOCUMENT" || item.status === "APPROVED";
                const isRejected = item.action === "REJECT_DOCUMENT" || item.status === "REJECTED";
                const isAdmin = item.actor_role === "ADMIN";
                const isStaff = item.actor_role === "STAFF";

                return (
                  <div
                    key={item.id}
                    onClick={() => handleNotificationClick(item)}
                    className={`px-4 py-3 flex gap-3 items-start transition-colors relative cursor-pointer ${
                      isRead ? "bg-white hover:bg-slate-50" : "bg-sky-50/40 hover:bg-sky-50/70"
                    }`}
                  >
                    {/* Chấm tròn chưa đọc */}
                    {!isRead && (
                      <span className="absolute left-1.5 top-1/2 -translate-y-1/2 w-1.5 h-1.5 rounded-full bg-dlu-navy-600" />
                    )}

                    {/* Icon trạng thái */}
                    <div className="mt-0.5 shrink-0">
                      {isApproved ? (
                        <div className="w-7 h-7 rounded-full bg-emerald-100 text-emerald-700 flex items-center justify-center">
                          <CheckCircle2 size={16} />
                        </div>
                      ) : isRejected ? (
                        <div className="w-7 h-7 rounded-full bg-rose-100 text-rose-700 flex items-center justify-center">
                          <XCircle size={16} />
                        </div>
                      ) : (
                        <div className="w-7 h-7 rounded-full bg-sky-100 text-sky-700 flex items-center justify-center">
                          <Clock size={16} />
                        </div>
                      )}
                    </div>

                    {/* Nội dung thông báo */}
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-1.5 flex-wrap mb-1">
                        {/* Huy hiệu Người duyệt */}
                        {isAdmin ? (
                          <span className="inline-flex items-center gap-1 bg-rose-50 text-rose-800 border border-rose-200 rounded px-1.5 py-0.5 text-[10px] font-bold">
                            <ShieldCheck size={10} />
                            Quản trị viên (ADMIN)
                          </span>
                        ) : isStaff ? (
                          <span className="inline-flex items-center gap-1 bg-amber-50 text-amber-800 border border-amber-200 rounded px-1.5 py-0.5 text-[10px] font-bold">
                            <UserCheck size={10} />
                            Cán bộ CTSV
                          </span>
                        ) : (
                          <span className="inline-flex items-center gap-1 bg-sky-50 text-sky-800 border border-sky-200 rounded px-1.5 py-0.5 text-[10px] font-bold">
                            <GraduationCap size={10} />
                            Sinh viên
                          </span>
                        )}

                        {/* Huy hiệu Hành động */}
                        {isApproved ? (
                          <span className="bg-emerald-100 text-emerald-800 rounded px-1.5 py-0.5 text-[10px] font-semibold">
                            ✓ Đã phê duyệt
                          </span>
                        ) : isRejected ? (
                          <span className="bg-rose-100 text-rose-800 rounded px-1.5 py-0.5 text-[10px] font-semibold">
                            ✕ Đã từ chối
                          </span>
                        ) : (
                          <span className="bg-slate-100 text-slate-700 rounded px-1.5 py-0.5 text-[10px] font-semibold">
                            Mới tải lên
                          </span>
                        )}
                      </div>

                      {/* Tiêu đề tài liệu */}
                      <div
                        className="text-xs font-semibold text-slate-900 truncate mb-0.5"
                        title={item.document_title}
                      >
                        {item.document_title}
                      </div>

                      {/* Mô tả chi tiết */}
                      <div className="text-[11px] text-slate-600 leading-snug line-clamp-2 mb-1.5">
                        {item.message}
                      </div>

                      {/* Thời gian */}
                      <div className="flex items-center justify-between text-[10px] text-slate-400">
                        <span>{formatTime(item.created_at)}</span>
                        <span className="inline-flex items-center gap-0.5 text-dlu-navy-700 font-semibold hover:underline">
                          Xem chi tiết <ExternalLink size={9} />
                        </span>
                      </div>
                    </div>
                  </div>
                );
              })
            )}
          </div>

          {/* Footer */}
          <div className="px-4 py-2.5 bg-slate-50 border-t border-slate-200 text-xs flex items-center justify-between">
            <span className="text-[11px] text-slate-500">
              {isStudent ? "Phân quyền: Sinh viên DLU" : "Hệ thống số hóa CTSV DLU"}
            </span>
            <button
              onClick={() => {
                setIsOpen(false);
                navigate("/documents");
              }}
              className="text-[11px] font-semibold text-dlu-navy-700 hover:text-dlu-navy-950 transition-colors"
            >
              {isStudent ? "Xem tất cả hồ sơ đã nộp →" : "Mở kho hồ sơ →"}
            </button>
          </div>
        </div>
      )}
    </div>
  );
};
