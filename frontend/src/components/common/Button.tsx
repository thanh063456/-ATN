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
  className = "",
  style,
  ...props
}) => {
  // Size classes
  const sizeClasses = {
    sm: "btn-sm text-xs px-2.5 py-1 min-h-[2rem] h-8",
    md: "btn-md text-sm px-4 h-10 min-h-[2.5rem]",
    lg: "btn-lg text-base px-6 h-12 min-h-[3rem]",
  }[size];

  // Variant classes adhering to DLU Academic palette
  const variantClasses = {
    primary: "btn-primary bg-dlu-navy-900 hover:bg-dlu-navy-800 text-white border-transparent shadow-sm",
    secondary: "bg-slate-100 hover:bg-slate-200 text-slate-800 border-slate-200",
    outline: "btn-outline border-slate-300 text-slate-700 hover:bg-slate-100 hover:border-slate-400 hover:text-slate-900",
    danger: "bg-dlu-crimson-700 hover:bg-dlu-crimson-800 text-white border-transparent shadow-sm",
    ghost: "btn-ghost text-slate-700 hover:bg-slate-100 hover:text-slate-900 border-transparent",
  }[variant];

  return (
    <button
      disabled={disabled || isLoading}
      className={`btn normal-case font-medium rounded-md transition-all duration-150 inline-flex !flex-nowrap items-center justify-center gap-1.5 !whitespace-nowrap shrink-0 focus:ring-2 focus:ring-dlu-navy-500/30 focus:outline-none disabled:opacity-60 disabled:cursor-not-allowed ${sizeClasses} ${variantClasses} ${className}`}
      style={{ flexWrap: "nowrap", whiteSpace: "nowrap", ...style }}
      {...props}
    >
      {isLoading ? (
        <span className="loading loading-spinner loading-xs text-current shrink-0" />
      ) : (
        leftIcon && <span className="shrink-0 inline-flex items-center">{leftIcon}</span>
      )}
      <span className="whitespace-nowrap shrink-0">{children}</span>
      {!isLoading && rightIcon && <span className="shrink-0 inline-flex items-center">{rightIcon}</span>}
    </button>
  );
};
