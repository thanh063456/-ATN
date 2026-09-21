import React from "react";

export type ButtonVariant = "primary" | "secondary" | "outline" | "danger" | "ghost";
export type ButtonSize = "sm" | "md" | "lg";

interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: ButtonVariant;
  size?: ButtonSize;
  isLoading?: boolean;
  leftIcon?: React.ReactNode;
  rightIcon?: React.ReactNode;
}

export const Button: React.FC<ButtonProps> = ({
  children,
  variant = "primary",
  size = "md",
  isLoading = false,
  leftIcon,
  rightIcon,
  disabled,
  style,
  ...props
}) => {
  const getStyles = () => {
    let base: React.CSSProperties = {
      display: "inline-flex",
      alignItems: "center",
      justifyContent: "center",
      gap: "0.5rem",
      fontWeight: 600,
      borderRadius: "8px",
      transition: "all 0.15s ease",
      cursor: disabled || isLoading ? "not-allowed" : "pointer",
      opacity: disabled || isLoading ? 0.65 : 1,
    };

    // Size
    if (size === "sm") {
      base = { ...base, padding: "0.35rem 0.75rem", fontSize: "0.8125rem" };
    } else if (size === "lg") {
      base = { ...base, padding: "0.75rem 1.5rem", fontSize: "1rem" };
    } else {
      base = { ...base, padding: "0.55rem 1.1rem", fontSize: "0.875rem" };
    }

    // Variant
    if (variant === "primary") {
      base = {
        ...base,
        backgroundColor: "var(--primary-600)",
        color: "#ffffff",
        boxShadow: "0 1px 2px rgba(79, 70, 229, 0.2)",
      };
    } else if (variant === "secondary") {
      base = {
        ...base,
        backgroundColor: "var(--gray-100)",
        color: "var(--gray-700)",
      };
    } else if (variant === "outline") {
      base = {
        ...base,
        backgroundColor: "transparent",
        color: "var(--gray-700)",
        border: "1px solid var(--border-color)",
      };
    } else if (variant === "danger") {
      base = {
        ...base,
        backgroundColor: "var(--danger-600)",
        color: "#ffffff",
      };
    } else if (variant === "ghost") {
      base = {
        ...base,
        backgroundColor: "transparent",
        color: "var(--gray-600)",
      };
    }

    return { ...base, ...style };
  };

  return (
    <button disabled={disabled || isLoading} style={getStyles()} {...props}>
      {isLoading ? (
        <span style={{ display: "inline-block", width: "14px", height: "14px", border: "2px solid currentColor", borderRightColor: "transparent", borderRadius: "50%", animation: "spin 0.6s linear infinite" }} />
      ) : (
        leftIcon
      )}
      {children}
      {!isLoading && rightIcon}
    </button>
  );
};
