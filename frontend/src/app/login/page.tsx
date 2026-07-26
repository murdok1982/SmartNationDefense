"use client";
import { useState, useEffect, FormEvent } from "react";
import { useRouter } from "next/navigation";
import { Shield, LogIn } from "lucide-react";
import { useAuthStore } from "@/store/auth-store";
import { apiErrorMessage } from "@/lib/api";

export default function LoginPage() {
  const router = useRouter();
  const { login, isAuthenticated, hydrated, restore } = useAuthStore();
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    void restore();
  }, [restore]);

  useEffect(() => {
    if (hydrated && isAuthenticated) router.replace("/");
  }, [hydrated, isAuthenticated, router]);

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    if (!username.trim() || !password) return;
    setSubmitting(true);
    setError(null);
    try {
      await login(username.trim(), password);
      router.replace("/");
    } catch (err) {
      setError(apiErrorMessage(err));
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="min-h-screen bg-[#0a0e17] flex items-center justify-center p-4">
      <div className="w-full max-w-sm bg-gray-900 border border-gray-700 rounded p-6">
        <div className="flex items-center gap-2 mb-1">
          <Shield size={20} className="text-green-400" />
          <span className="text-green-400 font-bold text-sm tracking-wider">SESIS-FEDERATION</span>
        </div>
        <div className="text-[10px] text-gray-500 font-mono mb-4">
          ACCESO RESTRINGIDO — PLATAFORMA C4ISR
        </div>

        <form onSubmit={handleSubmit} className="space-y-3">
          <div>
            <label className="text-[10px] text-gray-500 font-mono font-bold block mb-1">
              USUARIO
            </label>
            <input
              value={username}
              onChange={e => setUsername(e.target.value)}
              autoComplete="username"
              className="w-full bg-gray-800 text-gray-200 text-sm font-mono rounded px-3 py-2 border border-gray-700 outline-none focus:border-green-600"
            />
          </div>
          <div>
            <label className="text-[10px] text-gray-500 font-mono font-bold block mb-1">
              CONTRASENA
            </label>
            <input
              type="password"
              value={password}
              onChange={e => setPassword(e.target.value)}
              autoComplete="current-password"
              className="w-full bg-gray-800 text-gray-200 text-sm font-mono rounded px-3 py-2 border border-gray-700 outline-none focus:border-green-600"
            />
          </div>

          {error && (
            <div className="text-[11px] font-mono text-red-400 bg-red-900/20 border border-red-800 rounded px-2 py-1">
              {error}
            </div>
          )}

          <button
            type="submit"
            disabled={submitting || !username.trim() || !password}
            className="w-full bg-green-800 hover:bg-green-700 disabled:opacity-50 text-green-100 text-xs font-mono font-bold px-3 py-2 rounded flex items-center justify-center gap-2 transition-colors"
          >
            <LogIn size={14} />
            {submitting ? "AUTENTICANDO..." : "INICIAR SESION"}
          </button>
        </form>
      </div>
    </div>
  );
}
