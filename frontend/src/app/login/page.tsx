"use client";

import { useEffect, useState, type FormEvent } from "react";
import { useRouter } from "next/navigation";
import { Fingerprint, Lock, Shield, ShieldCheck, User } from "lucide-react";
import { useAuthStore } from "@/store/auth-store";
import { apiErrorMessage } from "@/lib/api";

const capabilities = [
  "Autenticación MFA con ticket de un solo uso",
  "Cadena de auditoría con hash encadenado",
  "Aislamiento de sesión por clasificación",
];

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
    <div className="relative flex min-h-screen items-center justify-center overflow-hidden px-4 py-10">
      <div className="pointer-events-none absolute inset-0 bg-app-grid opacity-[0.35]" aria-hidden="true" />
      <div
        className="pointer-events-none absolute left-1/2 top-0 h-[420px] w-[720px] -translate-x-1/2 rounded-full bg-accent/10 blur-[120px]"
        aria-hidden="true"
      />

      <div className="relative grid w-full max-w-4xl gap-6 lg:grid-cols-[1.05fr_0.95fr]">
        {/* Panel de contexto */}
        <section className="hidden flex-col justify-between rounded-2xl border border-stroke bg-surface/70 p-7 shadow-panel backdrop-blur-sm lg:flex">
          <div>
            <div className="flex items-center gap-2.5">
              <span className="relative flex h-9 w-9 items-center justify-center rounded-lg border border-accent/30 bg-accent/10 text-accent">
                <Shield size={18} />
              </span>
              <div className="leading-tight">
                <p className="text-sm font-semibold tracking-[0.16em] text-ink">SESIS-FEDERATION</p>
                <p className="text-3xs uppercase tracking-[0.22em] text-ink-faint">Command Center · C4ISR</p>
              </div>
            </div>

            <h1 className="mt-8 text-2xl font-semibold leading-snug tracking-tight text-ink">
              Acceso restringido a la red de mando y control.
            </h1>
            <p className="mt-2 max-w-[42ch] text-sm leading-relaxed text-ink-muted">
              Plataforma unificada de inteligencia, vigilancia y reconocimiento. Toda
              interacción queda registrada en la cadena de auditoría inmutable.
            </p>

            <ul className="mt-6 space-y-2.5">
              {capabilities.map((item) => (
                <li key={item} className="flex items-start gap-2 text-xs text-ink-muted">
                  <ShieldCheck size={14} className="mt-0.5 shrink-0 text-signal-success" />
                  {item}
                </li>
              ))}
            </ul>
          </div>

          <div className="mt-8 flex items-center justify-between border-t border-stroke/70 pt-4 text-3xs text-ink-faint">
            <span className="flex items-center gap-1.5">
              <span className="status-dot status-operational" aria-hidden="true" />
              Núcleo C2 operativo
            </span>
            <span className="font-mono">build 2026.11</span>
          </div>
        </section>

        {/* Formulario */}
        <section className="rounded-2xl border border-stroke bg-surface/85 p-6 shadow-panel backdrop-blur-sm sm:p-7">
          <div className="flex items-center gap-2 lg:hidden">
            <span className="flex h-8 w-8 items-center justify-center rounded-lg border border-accent/30 bg-accent/10 text-accent">
              <Shield size={16} />
            </span>
            <p className="text-xs font-semibold tracking-[0.16em] text-ink">SESIS-FEDERATION</p>
          </div>

          <div className="mt-4 lg:mt-0">
            <h2 className="text-base font-semibold tracking-tight text-ink">Identificación del operador</h2>
            <p className="mt-1 text-xs text-ink-faint">
              Introduce tus credenciales de dominio para iniciar sesión.
            </p>
          </div>

          <form onSubmit={handleSubmit} aria-busy={submitting} className="mt-5 space-y-3.5">
            <div>
              <label htmlFor="username" className="kpi-label mb-1.5 block">
                Usuario
              </label>
              <div className="relative">
                <User
                  size={14}
                  className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-ink-faint"
                  aria-hidden="true"
                />
                <input
                  id="username"
                  value={username}
                  onChange={(e) => setUsername(e.target.value)}
                  autoComplete="username"
                  autoFocus
                  required
                  placeholder="operador"
                  className="input-field !pl-9"
                />
              </div>
            </div>

            <div>
              <label htmlFor="password" className="kpi-label mb-1.5 block">
                Contraseña
              </label>
              <div className="relative">
                <Lock
                  size={14}
                  className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-ink-faint"
                  aria-hidden="true"
                />
                <input
                  id="password"
                  type="password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  autoComplete="current-password"
                  required
                  className="input-field !pl-9"
                />
              </div>
            </div>

            {error && (
              <div
                role="alert"
                className="rounded-lg border border-signal-danger/30 bg-signal-danger/10 px-3 py-2 text-xs text-signal-danger"
              >
                {error}
              </div>
            )}

            <button
              type="submit"
              disabled={submitting || !username.trim() || !password}
              aria-busy={submitting}
              className="btn-primary w-full !py-2.5 !text-sm"
            >
              <Fingerprint size={15} />
              {submitting ? "Autenticando…" : "Iniciar sesión"}
            </button>
          </form>

          <p className="mt-4 flex items-center justify-center gap-1.5 text-3xs text-ink-faint">
            <Lock size={10} aria-hidden="true" />
            Conexión cifrada · uso monitorizado
          </p>
        </section>
      </div>
    </div>
  );
}
