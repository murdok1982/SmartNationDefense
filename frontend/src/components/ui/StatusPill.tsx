"use client";

import type { ReactNode } from "react";
import clsx from "clsx";

type Tone = "success" | "warning" | "danger" | "info" | "neutral";

const toneStyles: Record<Tone, string> = {
  success: "border-signal-success/30 bg-signal-success/10 text-signal-success",
  warning: "border-signal-warning/30 bg-signal-warning/10 text-signal-warning",
  danger: "border-signal-danger/30 bg-signal-danger/10 text-signal-danger",
  info: "border-accent/30 bg-accent/10 text-accent",
  neutral: "border-stroke bg-surface-overlay text-ink-muted",
};

const dotStyles: Record<Tone, string> = {
  success: "bg-signal-success",
  warning: "bg-signal-warning",
  danger: "bg-signal-danger",
  info: "bg-accent",
  neutral: "bg-ink-faint",
};

export default function StatusPill({
  tone = "neutral",
  children,
  pulse = false,
  className,
}: {
  tone?: Tone;
  children: ReactNode;
  pulse?: boolean;
  className?: string;
}) {
  return (
    <span className={clsx("badge", toneStyles[tone], className)}>
      <span
        className={clsx(
          "status-dot",
          dotStyles[tone],
          pulse && "animate-pulse-ring",
        )}
        aria-hidden="true"
      />
      {children}
    </span>
  );
}
