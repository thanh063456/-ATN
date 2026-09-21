import React, { useState, useEffect } from "react";
import { useNavigate, Link } from "react-router-dom";
import {
  FileText,
  Lock,
  Mail,
  ArrowRight,
  ShieldCheck,
  Eye,
  EyeOff,
  GraduationCap,
} from "lucide-react";
import { useAuthStore, buildUserProfile } from "../stores/useAuthStore";
import { useToastStore } from "../stores/useToastStore";
import { authApi } from "../api/auth";

export const LoginPage: React.FC = () => {
  const navigate = useNavigate();
  const { login, updateProfile, isAuthenticated } = useAuthStore();
  const { addToast } = useToastStore();

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Nếu đã đăng nhập thì redirect về dashboard
  useEffect(() => {
    if (isAuthenticated) navigate("/", { replace: true });
  }, [isAuthenticated, navigate]);

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    if (!email.trim() || !password.trim()) {
      setError("Vui lòng nhập đầy đủ email và mật khẩu");
      return;
    }

    if (!email.toLowerCase().endsWith("@dlu.edu.vn")) {
      setError("Chỉ tài khoản email @dlu.edu.vn mới được phép đăng nhập");
      return;
    }

    setIsLoading(true);
    try {
      const { session, user } = await authApi.login({ email, password });
      if (!session || !user) throw new Error("Đăng nhập thất bại");

      let profile = buildUserProfile(user);
      login(profile, session.access_token, session);

      // Thử đồng bộ thông tin role/mssv từ FastAPI backend
      try {
        const backendUser = await authApi.getMe();
        if (backendUser) {
          updateProfile({
            role: backendUser.role_name,
            mssv: backendUser.mssv,
            fullName: backendUser.full_name || profile.fullName,
          });
        }
      } catch (err) {
        // Fallback to supabase user metadata
      }

      addToast({
        type: "success",
        title: "Đăng nhập thành công",
        message: `Chào mừng ${profile.fullName} quay trở lại!`,
      });
      navigate("/");
    } catch (err: any) {
      const msg = err?.message ?? "Đăng nhập thất bại";
      setError(
        msg.includes("Invalid login credentials")
          ? "Email hoặc mật khẩu không chính xác"
          : msg
      );
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div style={pageStyle}>
      {/* Background decorations */}
      <div style={blobStyle1} />
      <div style={blobStyle2} />

      <div style={cardStyle} className="animate-fade-in">
        {/* Header */}
        <div style={{ textAlign: "center", marginBottom: "2rem" }}>
          <div style={logoStyle}>
            <FileText size={26} color="#ffffff" />
          </div>
          <h1 style={titleStyle}>DocuCTSV OCR</h1>
          <p style={subtitleStyle}>
            <GraduationCap size={14} style={{ display: "inline", marginRight: 4 }} />
            Hệ thống Số hóa Tài liệu — Đại học Đà Lạt
          </p>
        </div>

        {/* Tab Indicator */}
        <div style={tabContainerStyle}>
          <span style={{ ...tabStyle, ...tabActiveStyle }}>Đăng nhập</span>
          <Link to="/register" style={{ ...tabStyle, textDecoration: "none" }}>
            Đăng ký
          </Link>
        </div>

        {/* Form */}
        <form onSubmit={handleLogin} style={formStyle}>
          {error && <div style={errorBoxStyle}>{error}</div>}

          {/* Email */}
          <div>
            <label style={labelStyle}>Email @dlu.edu.vn</label>
            <div style={{ position: "relative" }}>
              <Mail
                size={16}
                color="var(--gray-400)"
                style={iconStyle}
              />
              <input
                id="login-email"
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="ten.sinhvien@dlu.edu.vn"
                autoFocus
                autoComplete="email"
                style={inputStyle}
              />
            </div>
          </div>

          {/* Password */}
          <div>
            <div style={{ display: "flex", justifyContent: "space-between", marginBottom: "0.4rem" }}>
              <label style={labelStyle}>Mật khẩu</label>
            </div>
            <div style={{ position: "relative" }}>
              <Lock
                size={16}
                color="var(--gray-400)"
                style={iconStyle}
              />
              <input
                id="login-password"
                type={showPassword ? "text" : "password"}
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="Nhập mật khẩu"
                autoComplete="current-password"
                style={{ ...inputStyle, paddingRight: "2.75rem" }}
              />
              <button
                type="button"
                onClick={() => setShowPassword(!showPassword)}
                style={eyeButtonStyle}
                aria-label={showPassword ? "Ẩn mật khẩu" : "Hiện mật khẩu"}
              >
                {showPassword ? <EyeOff size={16} /> : <Eye size={16} />}
              </button>
            </div>
          </div>

          {/* Submit Button */}
          <button
            id="login-submit"
            type="submit"
            disabled={isLoading}
            style={{
              ...submitBtnStyle,
              marginTop: "0.5rem",
              opacity: isLoading ? 0.75 : 1,
              cursor: isLoading ? "not-allowed" : "pointer",
            }}
          >
            {isLoading ? (
              <>
                <span style={spinnerStyle} />
                Đang đăng nhập...
              </>
            ) : (
              <>
                Đăng nhập
                <ArrowRight size={17} />
              </>
            )}
          </button>
        </form>

        {/* Footer info */}
        <div style={footerStyle}>
          <ShieldCheck size={13} color="#16a34a" />
          <span>Bảo mật bởi Supabase Auth · Chỉ @dlu.edu.vn</span>
        </div>

        {/* Register CTA */}
        <p style={{ textAlign: "center", fontSize: "0.825rem", color: "var(--gray-500)", marginTop: "1.25rem" }}>
          Chưa có tài khoản?{" "}
          <Link to="/register" style={{ color: "#6366f1", fontWeight: 600, textDecoration: "none" }}>
            Đăng ký ngay (@dlu.edu.vn)
          </Link>
        </p>
      </div>
    </div>
  );
};

// ─── Styles ───────────────────────────────────────────────────────────────────
const pageStyle: React.CSSProperties = {
  minHeight: "100vh",
  display: "flex",
  alignItems: "center",
  justifyContent: "center",
  backgroundColor: "#0f172a",
  backgroundImage:
    "radial-gradient(at 0% 0%, rgba(99,102,241,0.18) 0, transparent 55%), radial-gradient(at 100% 100%, rgba(6,182,212,0.12) 0, transparent 55%)",
  padding: "1.5rem",
  position: "relative",
  overflow: "hidden",
};

const blobStyle1: React.CSSProperties = {
  position: "absolute",
  width: 380,
  height: 380,
  borderRadius: "50%",
  background: "rgba(99,102,241,0.07)",
  filter: "blur(60px)",
  top: -100,
  left: -100,
  pointerEvents: "none",
};

const blobStyle2: React.CSSProperties = {
  position: "absolute",
  width: 300,
  height: 300,
  borderRadius: "50%",
  background: "rgba(6,182,212,0.06)",
  filter: "blur(50px)",
  bottom: -80,
  right: -80,
  pointerEvents: "none",
};

const cardStyle: React.CSSProperties = {
  position: "relative",
  width: "100%",
  maxWidth: 420,
  backgroundColor: "#ffffff",
  borderRadius: 20,
  boxShadow: "0 24px 48px -12px rgba(0,0,0,0.28)",
  padding: "2.25rem 2rem",
};

const logoStyle: React.CSSProperties = {
  width: 52,
  height: 52,
  borderRadius: 14,
  background: "linear-gradient(135deg,#6366f1,#4338ca)",
  display: "inline-flex",
  alignItems: "center",
  justifyContent: "center",
  boxShadow: "0 8px 16px rgba(99,102,241,0.35)",
  marginBottom: "0.85rem",
};

const titleStyle: React.CSSProperties = {
  fontSize: "1.45rem",
  fontWeight: 800,
  color: "#0f172a",
  letterSpacing: "-0.03em",
  margin: 0,
};

const subtitleStyle: React.CSSProperties = {
  fontSize: "0.8rem",
  color: "#64748b",
  marginTop: "0.3rem",
  display: "flex",
  alignItems: "center",
  justifyContent: "center",
  gap: 4,
};

const tabContainerStyle: React.CSSProperties = {
  display: "flex",
  backgroundColor: "#f1f5f9",
  borderRadius: 10,
  padding: 4,
  marginBottom: "1.5rem",
  gap: 4,
};

const tabStyle: React.CSSProperties = {
  flex: 1,
  textAlign: "center",
  padding: "0.5rem",
  borderRadius: 8,
  fontSize: "0.875rem",
  fontWeight: 600,
  color: "#64748b",
  cursor: "pointer",
  transition: "all 0.2s",
};

const tabActiveStyle: React.CSSProperties = {
  backgroundColor: "#ffffff",
  color: "#0f172a",
  boxShadow: "0 1px 3px rgba(0,0,0,0.1)",
};

const formStyle: React.CSSProperties = {
  display: "flex",
  flexDirection: "column",
  gap: "1.1rem",
};

const labelStyle: React.CSSProperties = {
  display: "block",
  fontSize: "0.825rem",
  fontWeight: 600,
  color: "#334155",
  marginBottom: "0.35rem",
};

const iconStyle: React.CSSProperties = {
  position: "absolute",
  left: "0.875rem",
  top: "50%",
  transform: "translateY(-50%)",
  pointerEvents: "none",
};

const inputStyle: React.CSSProperties = {
  width: "100%",
  padding: "0.65rem 0.875rem 0.65rem 2.5rem",
  borderRadius: 10,
  border: "1.5px solid #e2e8f0",
  fontSize: "0.875rem",
  color: "#0f172a",
  backgroundColor: "#f8fafc",
  outline: "none",
  transition: "border-color 0.2s, box-shadow 0.2s",
  boxSizing: "border-box",
};

const eyeButtonStyle: React.CSSProperties = {
  position: "absolute",
  right: "0.75rem",
  top: "50%",
  transform: "translateY(-50%)",
  background: "none",
  border: "none",
  cursor: "pointer",
  color: "#94a3b8",
  padding: 0,
  display: "flex",
  alignItems: "center",
};

const errorBoxStyle: React.CSSProperties = {
  backgroundColor: "#fef2f2",
  border: "1px solid #fecaca",
  borderRadius: 8,
  padding: "0.65rem 0.875rem",
  color: "#dc2626",
  fontSize: "0.8rem",
  lineHeight: 1.4,
};

const submitBtnStyle: React.CSSProperties = {
  width: "100%",
  padding: "0.75rem",
  borderRadius: 10,
  border: "none",
  background: "linear-gradient(135deg, #6366f1 0%, #4f46e5 100%)",
  color: "#ffffff",
  fontWeight: 700,
  fontSize: "0.9rem",
  display: "flex",
  alignItems: "center",
  justifyContent: "center",
  gap: "0.5rem",
  boxShadow: "0 4px 14px rgba(79,70,229,0.35)",
  transition: "transform 0.15s, box-shadow 0.15s",
};

const spinnerStyle: React.CSSProperties = {
  width: 16,
  height: 16,
  border: "2px solid rgba(255,255,255,0.4)",
  borderTopColor: "#fff",
  borderRadius: "50%",
  display: "inline-block",
  animation: "spin 0.6s linear infinite",
};

const footerStyle: React.CSSProperties = {
  display: "flex",
  alignItems: "center",
  justifyContent: "center",
  gap: 5,
  marginTop: "1.25rem",
  fontSize: "0.75rem",
  color: "#64748b",
};
