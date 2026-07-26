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
      <div className="min-h-screen bg-[#0a0e17] flex items-center justify-center">
        <span className="text-green-400 font-mono text-xs animate-pulse">VERIFICANDO SESION...</span>
      </div>
    );
  }

  return <COPPage />;
}
