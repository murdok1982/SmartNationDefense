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

  const handleLogout = () => {
    logout();
    router.replace("/login");
  };

  return (
    <div className="flex gap-4 px-4 py-1 bg-gray-900 text-xs font-mono items-center border-b border-gray-700 overflow-x-auto">
      <div className="flex items-center gap-1 shrink-0">
        <span className={`w-2 h-2 rounded-full ${health.loading && !health.data ? "bg-yellow-400" : apiOk ? "bg-green-400" : "bg-red-400 animate-pulse"}`} />
        <span className={apiOk ? "text-green-400" : "text-red-400"}>
          API {health.loading && !health.data ? "..." : apiOk ? "OPERATIVA" : "SIN CONEXION"}
        </span>
      </div>
      <div className="flex-1" />
      {username && (
        <span className="text-gray-400 shrink-0">
          OP: <span className="text-green-400">{username}</span>
          {clearance && <span className="text-gray-600"> [{clearance}]</span>}
        </span>
      )}
      <button
        onClick={handleLogout}
        className="flex items-center gap-1 text-gray-500 hover:text-red-400 transition-colors shrink-0"
      >
        <LogOut size={12} />
        SALIR
      </button>
    </div>
  );
}
