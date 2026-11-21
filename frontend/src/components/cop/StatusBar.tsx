"use client";

import { useRouter } from "next/navigation";
import { LogOut } from "lucide-react";
import { useAuthStore } from "@/store/auth-store";
import { useApiData } from "@/lib/use-api-data";
import { apiFetch } from "@/lib/api";

export default function StatusBar() {
  const router = useRouter();
  const { username, clearance, logout } = useAuthStore();

  const health = useApiData(
    () => apiFetch<{ status: string }>("/api/v1/health", { auth: false }),
    { pollMs: 30000 },
  );

  const apiOk = !health.error && health.data?.status === "ok";
  const checking = health.loading && !health.data;

  const handleLogout = () => {
    logout();
    router.replace("/login");
  };

  return (
    <div className="flex items-center gap-3 border-t border-stroke/70 bg-surface-sunken/70 px-3 py-1 text-2xs sm:px-4">
      <span className="flex shrink-0 items-center gap-1.5">
        <span
          className={`status-dot ${
            checking ? "bg-signal-warning" : apiOk ? "status-operational" : "status-critical"
          }`}
          aria-hidden="true"
        />
        <span className={apiOk ? "text-signal-success" : checking ? "text-signal-warning" : "text-signal-danger"}>
          {checking ? "VERIFICANDO" : apiOk ? "ENLACE OPERATIVO" : "SIN ENLACE"}
        </span>
      </span>

      <span className="hidden h-3 w-px bg-stroke sm:block" aria-hidden="true" />
      <span className="hidden font-mono text-3xs text-ink-faint sm:inline">
        núcleo C2 · modular monolith
      </span>

      <div className="ml-auto flex min-w-0 items-center gap-3">
        {username && (
          <span className="min-w-0 truncate text-3xs text-ink-faint">
            OP: <span className="text-ink-muted">{username}</span>
            {clearance && <span className="ml-1 font-mono text-ink-faint">[{clearance}]</span>}
          </span>
        )}
        <button
          type="button"
          onClick={handleLogout}
          className="flex shrink-0 items-center gap-1 text-3xs font-semibold uppercase tracking-[0.12em] text-ink-faint transition-colors hover:text-signal-danger"
        >
          <LogOut size={11} aria-hidden="true" />
          Salir
        </button>
      </div>
    </div>
  );
}
