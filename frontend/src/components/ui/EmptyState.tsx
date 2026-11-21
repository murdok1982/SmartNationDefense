"use client";

import type { ReactNode } from "react";
import clsx from "clsx";

/** Estado vacío accionable: explica por qué no hay datos y qué hacer. */
export default function EmptyState({
  icon,
  title,
  description,
  action,
  className,
  compact = false,
}: {
  icon?: ReactNode;
  title: string;
  description?: string;
  action?: ReactNode;
  className?: string;
  compact?: boolean;
}) {
  return (
    <div
      className={clsx(
        "flex flex-col items-center justify-center gap-2 text-center",
        compact ? "py-5" : "py-10",
        className,
      )}
    >
      {icon && (
        <span className="flex h-9 w-9 items-center justify-center rounded-lg border border-stroke bg-surface-overlay text-ink-faint">
          {icon}
        </span>
      )}
      <p className="text-xs font-semibold text-ink-muted">{title}</p>
      {description && (
        <p className="max-w-[34ch] text-3xs leading-relaxed text-ink-faint">{description}</p>
      )}
      {action && <div className="mt-1">{action}</div>}
    </div>
  );
}
