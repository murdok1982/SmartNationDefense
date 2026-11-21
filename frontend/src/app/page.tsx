"use client";
import dynamic from "next/dynamic";
import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { useAuthStore } from "@/store/auth-store";

const COPPage = dynamic(() => import("@/components/cop/COPPage"), { ssr: false });

export default function Home() {
  const router = useRouter();
  const { isAuthenticated, hydrated, restore } = useAuthStore();

  useEffect(() => {
    void restore();
  }, [restore]);

  useEffect(() => {
    if (hydrated && !isAuthenticated) router.replace("/login");
  }, [hydrated, isAuthenticated, router]);

  if (!hydrated || !isAuthenticated) {
    return (
      <div
        role="status"
        aria-live="polite"
        className="flex min-h-screen flex-col items-center justify-center gap-3 bg-background px-6 text-center"
      >
        <span className="relative flex h-9 w-9 items-center justify-center rounded-lg border border-accent/30 bg-accent/10">
          <span className="status-dot status-operational animate-pulse" aria-hidden="true" />
        </span>
        <p className="text-2xs font-semibold uppercase tracking-[0.18em] text-ink-muted">
          Verificando sesión
        </p>
        <p className="text-3xs text-ink-faint">Restaurando credenciales del núcleo C2…</p>
      </div>
    );
  }

  return <COPPage />;
}
