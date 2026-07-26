"use client";
import { useEffect, useRef } from "react";
import { useCOPStore } from "@/store/cop-store";
import { useApiData } from "@/lib/use-api-data";
import { apiFetch } from "@/lib/api";
import { mapAlert, type BackendAlert } from "@/lib/mappers";

const sevConfig: Record<string, { color: string; bg: string }> = {
  critical: { color: "text-red-400", bg: "bg-red-900/20" },
  high: { color: "text-orange-400", bg: "bg-orange-900/20" },
  medium: { color: "text-yellow-400", bg: "bg-yellow-900/20" },
  low: { color: "text-blue-400", bg: "bg-blue-900/20" },
};

export default function AlertTicker() {
  const { state, setAlerts } = useCOPStore();
  const scrollRef = useRef<HTMLDivElement>(null);

  const { loading, error } = useApiData(
    async () => {
      const data = await apiFetch<BackendAlert[]>("/api/v1/c2/?limit=50");
      setAlerts(data.map(mapAlert));
      return data.length;
    },
    { pollMs: 30000 },
  );

  useEffect(() => {
    const el = scrollRef.current;
    if (!el) return;
    const interval = setInterval(() => {
      if (el.scrollTop < el.scrollHeight - el.clientHeight) {
        el.scrollTop += 1;
      } else {
        el.scrollTop = 0;
      }
    }, 80);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="bg-gray-900 rounded p-2 border border-gray-700">
      <div className="text-xs font-bold text-gray-400 mb-1 flex items-center gap-1">
        <span className="w-2 h-2 rounded-full bg-red-500 animate-pulse-glow" />
        ALERTAS
        <span className="text-gray-600 ml-auto">{state.alerts.length}</span>
      </div>
      <div ref={scrollRef} className="space-y-0.5 max-h-40 overflow-y-auto">
        {loading && state.alerts.length === 0 && (
          <div className="text-xs font-mono text-gray-500 animate-pulse">Cargando alertas...</div>
        )}
        {error && (
          <div className="text-xs font-mono text-red-400">{error}</div>
        )}
        {!loading && !error && state.alerts.length === 0 && (
          <div className="text-xs font-mono text-gray-600">Sin alertas activas</div>
        )}
        {state.alerts.map((a) => {
          const cfg = sevConfig[a.severity] || sevConfig.low;
          return (
            <div key={a.id} className={`text-xs font-mono flex gap-2 py-1 px-1 rounded ${cfg.bg} ${a.acknowledged ? "opacity-60" : ""}`}>
              <span className={`${cfg.color} font-bold shrink-0 w-16`}>
                {a.severity.toUpperCase()}
              </span>
              <span className="text-gray-300 flex-1">{a.message}</span>
              {a.timestamp && (
                <span className="text-gray-600 shrink-0">
                  {new Date(a.timestamp).toISOString().slice(11, 16)}Z
                </span>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
