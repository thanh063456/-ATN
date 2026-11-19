import React from "react";
import { CheckCircle2, AlertCircle, Info, AlertTriangle, X } from "lucide-react";
import { useToastStore, ToastMessage } from "../../stores/useToastStore";

export const ToastContainer: React.FC = () => {
  const { toasts, removeToast } = useToastStore();

  if (toasts.length === 0) return null;

  return (
    <div
      style={{
        position: "fixed",
        bottom: "1.5rem",
        right: "1.5rem",
        zIndex: 9999,
        display: "flex",
        flexDirection: "column",
        gap: "0.75rem",
        maxWidth: "400px",
        width: "calc(100vw - 3rem)",
      }}
    >
      {toasts.map((toast) => (
        <ToastItem key={toast.id} toast={toast} onClose={() => removeToast(toast.id)} />
      ))}
    </div>
  );
};

const ToastItem: React.FC<{ toast: ToastMessage; onClose: () => void }> = ({ toast, onClose }) => {
  const getIcon = () => {
    switch (toast.type) {
      case "success":
        return <CheckCircle2 size={20} color="#16a34a" />;
      case "error":
        return <AlertCircle size={20} color="#dc2626" />;
      case "warning":
        return <AlertTriangle size={20} color="#d97706" />;
      case "info":
      default:
        return <Info size={20} color="#4f46e5" />;
    }
  };

  return (
    <div
      className="animate-fade-in"
      style={{
        display: "flex",
        alignItems: "flex-start",
        gap: "0.75rem",
        padding: "1rem",
        borderRadius: "var(--radius-md)",
        backgroundColor: "#ffffff",
        boxShadow: "var(--shadow-xl)",
        border: "1px solid var(--border-color)",
      }}
    >
      <div style={{ marginTop: "2px" }}>{getIcon()}</div>
      <div style={{ flex: 1 }}>
        <div style={{ fontWeight: 600, fontSize: "0.875rem", color: "var(--gray-900)" }}>
          {toast.title}
        </div>
        {toast.message && (
          <div style={{ fontSize: "0.8125rem", color: "var(--gray-600)", marginTop: "0.2rem" }}>
            {toast.message}
          </div>
        )}
      </div>
      <button
        onClick={onClose}
        style={{
          color: "var(--gray-400)",
          padding: "2px",
          borderRadius: "4px",
          display: "flex",
        }}
      >
        <X size={16} />
      </button>
    </div>
  );
};
