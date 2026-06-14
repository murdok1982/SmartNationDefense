"use client";
import { useState, useEffect } from "react";

export default function MissionClock() {
  const [time, setTime] = useState("");

  useEffect(() => {
    const tick = () => {
      const now = new Date();
      const y = now.getUTCFullYear();
      const mo = String(now.getUTCMonth() + 1).padStart(2, "0");
      const d = String(now.getUTCDate()).padStart(2, "0");
      const h = String(now.getUTCHours()).padStart(2, "0");
      const mi = String(now.getUTCMinutes()).padStart(2, "0");
      const s = String(now.getUTCSeconds()).padStart(2, "0");
      setTime(`${y}-${mo}-${d} ${h}:${mi}:${s} Z`);
    };
    tick();
    const id = setInterval(tick, 1000);
    return () => clearInterval(id);
  }, []);

  return (
    <div className="flex items-center gap-2">
      <span className="w-2 h-2 rounded-full bg-green-500 animate-pulse-glow" />
      <span className="text-green-400 font-mono text-sm tracking-wider">{time}</span>
    </div>
  );
}
