"use client";

import type { ReactNode } from "react";
import clsx from "clsx";

interface PanelProps {
  title?: string;
  subtitle?: string;
  icon?: ReactNode;
  actions?: ReactNode;
  children: ReactNode;
  className?: string;
  bodyClassName?: string;
  dense?: boolean;
  as?: "section" | "div" | "article";
}

/**
 * Superficie base del sistema de diseño: borde hairline, elevación sutil y
 * cabecera con jerarquía tipográfica consistente.
 */
export default function Panel({
  title,
  subtitle,
  icon,
  actions,
  children,
  className,
  bodyClassName,
  dense = false,
  as: Tag = "section",
}: PanelProps) {
  return (
    <Tag className={clsx("panel flex min-h-0 flex-col", className)}>
      {(title || actions) && (
        <header className="panel-header">
          <div className="min-w-0">
            <h2 className="panel-title truncate">
              {icon}
              {title}
            </h2>
            {subtitle && (
              <p className="mt-0.5 truncate text-3xs text-ink-faint">{subtitle}</p>
            )}
          </div>
          {actions && <div className="flex shrink-0 items-center gap-1.5">{actions}</div>}
        </header>
      )}
      <div className={clsx("min-h-0 flex-1", dense ? "p-0" : "panel-body", bodyClassName)}>
        {children}
      </div>
    </Tag>
  );
}
