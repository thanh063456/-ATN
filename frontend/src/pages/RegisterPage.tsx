import React, { useState, useEffect } from "react";
import { useNavigate, Link } from "react-router-dom";
import {
  FileText,
  Lock,
  Mail,
  User,
  ArrowRight,
  ShieldCheck,
  Eye,
  EyeOff,
  GraduationCap,
  CheckCircle2,
  IdCard,
} from "lucide-react";
import { useAuthStore } from "../stores/useAuthStore";
import { useToastStore } from "../stores/useToastStore";
import { authApi } from "../api/auth";

export const RegisterPage: React.FC = () => {
  const navigate = useNavigate();
  const { isAuthenticated } = useAuthStore();
  const { addToast } = useToastStore();

  const [fullName, setFullName] = useState("");
  const [mssv, setMssv] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);

  useEffect(() => {
    if (isAuthenticated) navigate("/", { replace: true });
  }, [isAuthenticated, navigate]);

  const passwordStrength = (p: string): { level: number; label: string; color: string } => {
    if (p.length === 0) return { level: 0, label: "", color: "transparent" };
    if (p.length < 6) return { level: 1, label: "Quá ngắn", color: "#ef4444" };
    if (p.length < 8) return { level: 2, label: "Yếu", color: "#f97316" };
    if (!/[A-Z]/.test(p) || !/[0-9]/.test(p))
      return { level: 3, label: "Trung bình", color: "#eab308" };
    return { level: 4, label: "Mạnh", color: "#22c55e" };
  };

  const strength = passwordStrength(password);

  const handleRegister = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    if (!fullName.trim() || !email.trim() || !password || !confirmPassword) {
      setError("Vui lòng điền đầy đủ tất cả các trường bắt buộc");
      return;
    }

    if (!email.toLowerCase().endsWith("@dlu.edu.vn")) {
      setError("Chỉ email đuôi @dlu.edu.vn mới được phép đăng ký tài khoản");
      return;
    }

    if (password.length < 6) {
      setError("Mật khẩu phải có ít nhất 6 ký tự");
      return;
    }

    if (password !== confirmPassword) {
      setError("Mật khẩu xác nhận không khớp");
      return;
    }

    setIsLoading(true);
    try {
      const data = await authApi.register({
        email: email.trim(),
        password,
        fullName: fullName.trim(),
        mssv: mssv.trim() || undefined,
      });

      if (data.user || data.backendUser) {
        setSuccess(true);
        addToast({
          type: "success",
          title: "Đăng ký thành công!",
          message: "Tài khoản của bạn đã sẵn sàng để đăng nhập.",
        });
      }
    } catch (err: any) {
      const msg = err?.message ?? "Đăng ký thất bại";
      setError(
        msg.includes("User already registered") || msg.includes("đã được đăng ký")
          ? "Email này đã được đăng ký. Vui lòng đăng nhập."
          : msg.includes("Password should be")
          ? "Mật khẩu không đủ mạnh. Hãy dùng ít nhất 6 ký tự."
          : msg
      );
    } finally {
      setIsLoading(false);
    }
  };

  if (success) {
    return (
      <div style={pageStyle}>
        <div style={blobStyle1} />
        <div style={blobStyle2} />
        <div style={{ ...cardStyle, textAlign: "center" }} className="animate-fade-in">
          <div style={{ ...logoStyle, background: "linear-gradient(135deg,#22c55e,#16a34a)" }}>
            <CheckCircle2 size={26} color="#fff" />
          </div>
          <h2 style={{ fontSize: "1.3rem", fontWeight: 800, color: "#0f172a", marginTop: "1rem" }}>
            Đăng ký thành công! 🎉
          </h2>
          <p style={{ color: "#64748b", fontSize: "0.875rem", marginTop: "0.5rem", lineHeight: 1.6 }}>
            Tài khoản <strong>{email}</strong> đã được kích hoạt thành công.
            <br />
            Bạn có thể đăng nhập vào hệ thống ngay bây giờ.
          </p>
          <Link
            to="/login"
            style={{
              display: "inline-flex",
              alignItems: "center",
              gap: "0.5rem",
              marginTop: "1.5rem",
              padding: "0.7rem 1.5rem",
              borderRadius: 10,
              background: "linear-gradient(135deg,#6366f1,#4f46e5)",
              color: "#fff",
              fontWeight: 700,
              fontSize: "0.9rem",
              textDecoration: "none",
              boxShadow: "0 4px 12px rgba(79,70,229,0.3)",
            }}
          >
            Đến trang đăng nhập <ArrowRight size={16} />
          </Link>
        </div>
      </div>
    );
  }

  return (
    <div style={pageStyle}>
      <div style={blobStyle1} />
      <div style={blobStyle2} />

      <div style={cardStyle} className="animate-fade-in">
        {/* Header */}
        <div style={{ textAlign: "center", marginBottom: "1.5rem" }}>
          <div style={logoStyle}>
            <FileText size={26} color="#ffffff" />
          </div>
          <h1 style={titleStyle}>Tạo tài khoản sinh viên</h1>
          <p style={subtitleStyle}>
            <GraduationCap size={14} style={{ display: "inline", marginRight: 4 }} />
            Chỉ dành cho thành viên @dlu.edu.vn
          </p>
        </div>

        {/* Tab Indicator */}
        <div style={tabContainerStyle}>
          <Link to="/login" style={{ ...tabStyle, textDecoration: "none" }}>
            Đăng nhập
          </Link>
          <span style={{ ...tabStyle, ...tabActiveStyle }}>Đăng ký</span>
        </div>

        {/* Form */}
        <form onSubmit={handleRegister} style={formStyle}>
          {error && <div style={errorBoxStyle}>{error}</div>}

          {/* Full Name */}
          <div>
            <label style={labelStyle}>Họ và tên *</label>
            <div style={{ position: "relative" }}>
              <User size={16} color="var(--gray-400)" style={iconStyle} />
              <input
                id="register-fullname"
                type="text"
                value={fullName}
                onChange={(e) => setFullName(e.target.value)}
                placeholder="Nguyễn Văn A"
                autoFocus
                autoComplete="name"
                style={inputStyle}
              />
            </div>
          </div>

          {/* MSSV */}
          <div>
            <label style={labelStyle}>
              Mã số sinh viên (MSSV)
              <span style={{ color: "var(--gray-400)", fontWeight: 400, fontSize: "0.75rem", marginLeft: 4 }}>
                (khuyên dùng cho sinh viên)
              </span>
            </label>
            <div style={{ position: "relative" }}>
              <IdCard size={16} color="var(--gray-400)" style={iconStyle} />
              <input
                id="register-mssv"
                type="text"
                value={mssv}
                onChange={(e) => setMssv(e.target.value)}
                placeholder="Ví dụ: 20210678"
                style={inputStyle}
              />
            </div>
          </div>

          {/* Email */}
          <div>
            <label style={labelStyle}>
              Email <span style={{ color: "#6366f1", fontWeight: 700 }}>@dlu.edu.vn</span> *
            </label>
            <div style={{ position: "relative" }}>
              <Mail size={16} color="var(--gray-400)" style={iconStyle} />
              <input
                id="register-email"
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="ten.nguyen@dlu.edu.vn"
                autoComplete="email"
                style={{
                  ...inputStyle,
                  borderColor:
                    email && !email.toLowerCase().endsWith("@dlu.edu.vn")
                      ? "#fca5a5"
                      : email && email.toLowerCase().endsWith("@dlu.edu.vn")
                      ? "#86efac"
                      : "#e2e8f0",
                }}
              />
            </div>
            {email && !email.toLowerCase().endsWith("@dlu.edu.vn") && (
              <p style={{ fontSize: "0.75rem", color: "#ef4444", marginTop: "0.3rem" }}>
                ⚠ Email phải có đuôi @dlu.edu.vn
              </p>
            )}
          </div>

          {/* Password */}
          <div>
            <label style={labelStyle}>Mật khẩu *</label>
            <div style={{ position: "relative" }}>
              <Lock size={16} color="var(--gray-400)" style={iconStyle} />
              <input
                id="register-password"
                type={showPassword ? "text" : "password"}
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="Tối thiểu 6 ký tự"
                autoComplete="new-password"
                style={{ ...inputStyle, paddingRight: "2.75rem" }}
              />
              <button
                type="button"
                onClick={() => setShowPassword(!showPassword)}
                style={eyeButtonStyle}
              >
                {showPassword ? <EyeOff size={16} /> : <Eye size={16} />}
              </button>
            </div>
            {/* Password strength bar */}
            {password && (
              <div style={{ marginTop: "0.4rem" }}>
                <div style={{ display: "flex", gap: 4, marginBottom: 4 }}>
                  {[1, 2, 3, 4].map((i) => (
                    <div
                      key={i}
                      style={{
                        flex: 1,
                        height: 4,
                        borderRadius: 2,
                        backgroundColor:
                          i <= strength.level ? strength.color : "#e2e8f0",
                        transition: "background-color 0.2s",
                      }}
                    />
                  ))}
                </div>
                <span style={{ fontSize: "0.72rem", color: strength.color, fontWeight: 600 }}>
                  {strength.label}
                </span>
              </div>
            )}
          </div>

          {/* Confirm Password */}
          <div>
            <label style={labelStyle}>Xác nhận mật khẩu *</label>
            <div style={{ position: "relative" }}>
              <Lock size={16} color="var(--gray-400)" style={iconStyle} />
              <input
                id="register-confirm-password"
                type={showConfirmPassword ? "text" : "password"}
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
                placeholder="Nhập lại mật khẩu"
                autoComplete="new-password"
                style={{
                  ...inputStyle,
                  paddingRight: "2.75rem",
                  borderColor:
                    confirmPassword && confirmPassword !== password
                      ? "#fca5a5"
                      : confirmPassword && confirmPassword === password
                      ? "#86efac"
                      : "#e2e8f0",
                }}
              />
              <button
                type="button"
                onClick={() => setShowConfirmPassword(!showConfirmPassword)}
                style={eyeButtonStyle}
              >
                {showConfirmPassword ? <EyeOff size={16} /> : <Eye size={16} />}
              </button>
            </div>
            {confirmPassword && confirmPassword !== password && (
              <p style={{ fontSize: "0.75rem", color: "#ef4444", marginTop: "0.3rem" }}>
                ⚠ Mật khẩu không khớp
              </p>
            )}
          </div>

          {/* Submit */}
          <button
            id="register-submit"
            type="submit"
            disabled={isLoading}
            style={{
              ...submitBtnStyle,
              marginTop: "0.25rem",
              opacity: isLoading ? 0.75 : 1,
              cursor: isLoading ? "not-allowed" : "pointer",
            }}
          >
            {isLoading ? (
              <>
                <span style={spinnerStyle} />
                Đang tạo tài khoản...
              </>
            ) : (
              <>
                Tạo tài khoản
                <ArrowRight size={17} />
              </>
            )}
          </button>
        </form>

        {/* Footer */}
        <div style={footerStyle}>
          <ShieldCheck size={13} color="#16a34a" />
          <span>Bảo mật bởi Supabase Auth · Chỉ @dlu.edu.vn</span>
        </div>

        <p style={{ textAlign: "center", fontSize: "0.8rem", color: "var(--gray-500)", marginTop: "1rem" }}>
          Đã có tài khoản?{" "}
          <Link to="/login" style={{ color: "#6366f1", fontWeight: 600, textDecoration: "none" }}>
            Đăng nhập
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
  maxWidth: 440,
  backgroundColor: "#ffffff",
  borderRadius: 20,
  boxShadow: "0 24px 48px -12px rgba(0,0,0,0.28)",
  padding: "2rem 2rem",
};

const logoStyle: React.CSSProperties = {
  width: 50,
  height: 50,
  borderRadius: 14,
  background: "linear-gradient(135deg,#6366f1,#4338ca)",
  display: "inline-flex",
  alignItems: "center",
  justifyContent: "center",
  boxShadow: "0 8px 16px rgba(99,102,241,0.35)",
  marginBottom: "0.75rem",
};

const titleStyle: React.CSSProperties = {
  fontSize: "1.35rem",
  fontWeight: 800,
  color: "#0f172a",
  letterSpacing: "-0.03em",
  margin: 0,
};

const subtitleStyle: React.CSSProperties = {
  fontSize: "0.8rem",
  color: "#64748b",
  marginTop: "0.25rem",
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
  marginBottom: "1.25rem",
  gap: 4,
};

const tabStyle: React.CSSProperties = {
  flex: 1,
  textAlign: "center",
  padding: "0.45rem",
  borderRadius: 8,
  fontSize: "0.85rem",
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
  gap: "0.85rem",
};

const labelStyle: React.CSSProperties = {
  display: "block",
  fontSize: "0.8rem",
  fontWeight: 600,
  color: "#334155",
  marginBottom: "0.3rem",
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
  padding: "0.6rem 0.875rem 0.6rem 2.5rem",
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
  marginTop: "1.1rem",
  fontSize: "0.75rem",
  color: "#64748b",
};
