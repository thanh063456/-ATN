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
  const paddingMap = {
    none: "0",
    sm: "1rem",
    md: "1.5rem",
    lg: "2rem",
  };

  const shadowMap = {
    none: "none",
    sm: "var(--shadow-sm)",
    md: "var(--shadow-md)",
    lg: "var(--shadow-lg)",
  };

  return (
    <div
      style={{
        backgroundColor: "var(--bg-surface)",
        borderRadius: "var(--radius-lg)",
        border: "1px solid var(--border-color)",
        padding: paddingMap[padding],
        boxShadow: shadowMap[shadow],
        transition: hoverable ? "transform 0.2s ease, box-shadow 0.2s ease" : undefined,
        ...style,
      }}
      className={`card ${hoverable ? "card-hover" : ""} ${className}`}
      {...props}
    >
      {children}
    </div>
  );
};
