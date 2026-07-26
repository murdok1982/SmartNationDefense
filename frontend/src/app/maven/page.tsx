"use client";
import dynamic from "next/dynamic";

const COPUnified = dynamic(() => import("@/components/cop/COPUnified"), { ssr: false });

export default function MavenPage() {
  return <COPUnified />;
}
