"use client";

import type { ReactNode } from "react";
import clsx from "clsx";

type Tone = "accent" | "success" | "warning" | "danger" | "info" | "neutral";

const toneRing: Record<Tone, string> = {
  accent: "border-accent/25 bg-accent/10 text-accent",
  success: "border-signal-success/25 bg-signal-success/10 text-signal-success",
  warning: "border-signal-warning/25 bg-signal-warning/10 text-signal-warning",
  danger: "border-signal-danger/25 bg-signal-danger/10 text-signal-danger",
  info: "border-signal-info/25 bg-signal-info/10 text-signal-info",
  neutral: "border-stroke bg-surface-overlay text-ink-muted",
};

export interface KpiCardProps {
  label: string;
  value: string | number;
  unit?: string;
  hint?: string;
  delta?: { value: string; direction: "up" | "down" | "flat" };
  tone?: Tone;
  icon?: ReactNode;
  loading?: boolean;
}

export default function KpiCard({
  label,
  value,
  unit,
  hint,
  delta,
  tone = "accent",
  icon,
  loading = false,
}: KpiCardProps) {
  const deltaTone =
    delta?.direction === "up"
      ? "text-signal-success"
      : delta?.direction === "down"
        ? "text-signal-danger"
        : "text-ink-faint";

  return (
    <article className="panel group relative overflow-hidden p-4">
      <span className="pointer-events-none absolute inset-x-0 top-0 h-px bg-gradient-to-r from-transparent via-accent/40 to-transparent opacity-0 transition-opacity duration-300 group-hover:opacity-100" />

      <div className="flex items-start justify-between gap-3">
        <p className="kpi-label">{label}</p>
        {icon && (
          <span
            className={clsx(
              "flex h-8 w-8 items-center justify-center rounded-lg border",
              toneRing[tone],
            )}
            aria-hidden="true"
          >
            {icon}
          </span>
        )}
      </div>

      {loading ? (
        <div className="mt-3 space-y-2">
          <div className="skeleton h-7 w-24" />
          <div className="skeleton h-2.5 w-32" />
        </div>
      ) : (
        <>
          <div className="mt-3 flex items-baseline gap-1.5">
            <span className="kpi-value">{value}</span>
            {unit && <span className="font-mono text-xs text-ink-faint">{unit}</span>}
          </div>
          <div className="mt-2 flex items-center justify-between gap-2">
            {hint && <p className="truncate text-3xs text-ink-faint">{hint}</p>}
            {delta && (
              <span className={clsx("font-mono text-3xs font-semibold", deltaTone)}>
                {delta.direction === "up" ? "▲" : delta.direction === "down" ? "▼" : "—"}{" "}
                {delta.value}
              </span>
            )}
          </div>
        </>
      )}
    </article>
  );
}
