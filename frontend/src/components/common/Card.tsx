import React from "react";

interface CardProps extends React.HTMLAttributes<HTMLDivElement> {
  children: React.ReactNode;
  padding?: "none" | "sm" | "md" | "lg";
  shadow?: "none" | "sm" | "md" | "lg";
  hoverable?: boolean;
}

export const Card: React.FC<CardProps> = ({
  children,
  padding = "md",
  shadow = "sm",
  hoverable = false,
  style,
  className = "",
  ...props
}) => {
  const paddingClasses = {
    none: "p-0",
    sm: "p-3 sm:p-4",
    md: "p-4 sm:p-6",
    lg: "p-6 sm:p-8",
  }[padding];

  const shadowClasses = {
    none: "shadow-none",
    sm: "shadow-paper",
    md: "shadow-paper-hover",
    lg: "shadow-paper-lg",
  }[shadow];

  const hoverClass = hoverable
    ? "transition-all duration-150 hover:shadow-paper-hover hover:border-slate-300"
    : "";

  return (
    <div
      className={`bg-white rounded-lg border border-slate-200/80 ${paddingClasses} ${shadowClasses} ${hoverClass} ${className}`}
      style={style}
      {...props}
    >
      {children}
    </div>
  );
};
