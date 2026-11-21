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

export interface SparklineProps {
  values: number[];
  width?: number;
  height?: number;
  tone?: Tone;
  className?: string;
  ariaLabel?: string;
}

/** Mini-gráfico de tendencia en SVG puro (sin dependencias). */
export default function Sparkline({
  values,
  width = 160,
  height = 44,
  tone = "accent",
  className,
  ariaLabel = "Tendencia",
}: SparklineProps) {
  const gradientId = useId().replace(/:/g, "");
  const color = toneColor[tone];
  const data = values.length > 0 ? values : [0];
  const max = Math.max(...data);
  const min = Math.min(...data);
  const span = max - min || 1;
  const stepX = data.length > 1 ? width / (data.length - 1) : width;
  const pad = 3;

  const points = data.map((v, i) => {
    const x = data.length > 1 ? i * stepX : width / 2;
    const y = height - pad - ((v - min) / span) * (height - pad * 2);
    return [x, y] as const;
  });

  const line = points.map(([x, y], i) => `${i === 0 ? "M" : "L"}${x.toFixed(2)},${y.toFixed(2)}`).join(" ");
  const area = `${line} L${width},${height} L0,${height} Z`;
  const last = points[points.length - 1];

  return (
    <svg
      viewBox={`0 0 ${width} ${height}`}
      width="100%"
      height={height}
      className={clsx("overflow-visible", className)}
      role="img"
      aria-label={ariaLabel}
      preserveAspectRatio="none"
    >
      <defs>
        <linearGradient id={gradientId} x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stopColor={color} stopOpacity="0.32" />
          <stop offset="100%" stopColor={color} stopOpacity="0" />
        </linearGradient>
      </defs>
      <path d={area} fill={`url(#${gradientId})`} />
      <path d={line} fill="none" stroke={color} strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round" />
      <circle cx={last[0]} cy={last[1]} r="2.2" fill={color} />
    </svg>
  );
}
