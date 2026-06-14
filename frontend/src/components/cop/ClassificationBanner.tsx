"use client";
import { useCOPStore } from "@/store/cop-store";

const levelColors: Record<string, string> = {
  "UNCLASSIFIED": "bg-green-800",
  "PUBLIC": "bg-green-800",
  "RESTRICTED": "bg-blue-800",
  "CONFIDENTIAL": "bg-yellow-700",
  "SECRET": "bg-red-800",
  "TOP SECRET": "bg-purple-900",
};

export default function ClassificationBanner() {
  const { classification } = useCOPStore();
  const bg = levelColors[classification] || "bg-blue-800";

  return (
    <div className={`${bg} text-white text-center text-xs font-mono py-1 tracking-[0.3em] font-bold`}>
      {classification} — SESIS-FEDERATION C4ISR — {classification}
    </div>
  );
}
