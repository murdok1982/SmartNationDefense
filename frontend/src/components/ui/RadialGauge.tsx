"use client";

import { useId } from "react";
import clsx from "clsx";

type Tone = "accent" | "success" | "warning" | "danger" | "info";

const toneColor: Record<Tone, string> = {
  accent: "#22d3ee",
  success: "#34d399",
  warning: "#fbbf24",
  danger: "#f87171",
  info: "#60a5fa",
};

export interface RadialGaugeProps {
  value: number;
  max?: number;
  size?: number;
  thickness?: number;
  label?: string;
  sublabel?: string;
  tone?: Tone;
  className?: string;
  showValue?: boolean;
}

/**
 * Gauge radial (donut) con trazo redondeado y gradiente sutil.
 * Accesible: expone `role="meter"` con los valores reales.
 */
export default function RadialGauge({
  value,
  max = 100,
  size = 148,
  thickness = 11,
  label,
  sublabel,
  tone = "accent",
  className,
  showValue = true,
}: RadialGaugeProps) {
  const gradientId = useId().replace(/:/g, "");
  const safeMax = max <= 0 ? 100 : max;
  const pct = Math.max(0, Math.min(100, (value / safeMax) * 100));
  const radius = (size - thickness) / 2;
  const circumference = 2 * Math.PI * radius;
  const dash = (pct / 100) * circumference;
  const color = toneColor[tone];

  return (
    <div
      className={clsx("relative inline-flex items-center justify-center", className)}
      style={{ width: size, height: size }}
      role="meter"
      aria-valuenow={Math.round(pct)}
      aria-valuemin={0}
      aria-valuemax={100}
      aria-label={label ?? "Indicador"}
    >
      <svg width={size} height={size} className="-rotate-90" aria-hidden="true">
        <defs>
          <linearGradient id={gradientId} x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" stopColor={color} stopOpacity="0.55" />
            <stop offset="100%" stopColor={color} stopOpacity="1" />
          </linearGradient>
        </defs>
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          fill="none"
          stroke="rgba(38,56,84,0.65)"
          strokeWidth={thickness}
        />
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          fill="none"
          stroke={`url(#${gradientId})`}
          strokeWidth={thickness}
          strokeLinecap="round"
          strokeDasharray={`${dash} ${circumference - dash}`}
          style={{ transition: "stroke-dasharray 700ms cubic-bezier(0.22,1,0.36,1)" }}
        />
      </svg>

      <div className="absolute inset-0 flex flex-col items-center justify-center text-center">
        {showValue && (
          <span className="font-mono text-2xl font-semibold leading-none text-ink">
            {Math.round(pct)}
            <span className="ml-0.5 text-xs text-ink-faint">%</span>
          </span>
        )}
        {label && (
          <span className="mt-1 max-w-[80%] text-3xs font-semibold uppercase tracking-[0.14em] text-ink-muted">
            {label}
          </span>
        )}
        {sublabel && <span className="mt-0.5 text-3xs text-ink-faint">{sublabel}</span>}
      </div>
    </div>
  );
}
