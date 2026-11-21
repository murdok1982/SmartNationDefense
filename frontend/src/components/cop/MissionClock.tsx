"use client";

import { useEffect, useState } from "react";

/** Reloj de misión en UTC, con segundos y sin dependencias externas. */
export default function MissionClock() {
  const [now, setNow] = useState<Date | null>(null);

  useEffect(() => {
    const tick = () => setNow(new Date());
    tick();
    const id = setInterval(tick, 1000);
    return () => clearInterval(id);
  }, []);

  const pad = (value: number) => String(value).padStart(2, "0");
  const display = now
    ? `${now.getUTCFullYear()}-${pad(now.getUTCMonth() + 1)}-${pad(now.getUTCDate())} ${pad(
        now.getUTCHours(),
      )}:${pad(now.getUTCMinutes())}:${pad(now.getUTCSeconds())}Z`
    : null;
  // `dateTime` exige un valor ISO 8601 válido (con `T`), no el formato de pantalla.
  const isoTime = now ? now.toISOString().replace(/\.\d{3}Z$/, "Z") : undefined;

  return (
    <div className="flex items-center gap-1.5 rounded-lg border border-stroke bg-surface-sunken/70 px-2.5 py-1">
      <span className="status-dot status-operational animate-pulse" aria-hidden="true" />
      <time
        dateTime={isoTime}
        className="font-mono text-3xs tabular-nums tracking-[0.08em] text-ink-muted"
      >
        {display ?? "——:——:——Z"}
      </time>
    </div>
  );
}
