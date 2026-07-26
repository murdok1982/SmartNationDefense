import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "MAVEN FUSION — SESIS-FEDERATION C4ISR",
  description: "Maven Fusion System — Análisis satelital, detecciones CV, tracks fusionados y planeamiento COA",
};

export default function MavenLayout({ children }: { children: React.ReactNode }) {
  return <>{children}</>;
}
