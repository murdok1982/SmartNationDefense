"use client";
import { useCOPStore } from "@/store/cop-store";
import type { IntelReport } from "@/lib/cop-types";

const classColor: Record<string, string> = {
  "PUBLIC": "text-green-400 bg-green-900/30",
  "UNCLASSIFIED": "text-green-400 bg-green-900/30",
  "RESTRICTED": "text-yellow-400 bg-yellow-900/30",
  "CONFIDENTIAL": "text-orange-400 bg-orange-900/30",
  "SECRET": "text-red-400 bg-red-900/30",
  "TOP SECRET": "text-purple-400 bg-purple-900/30",
};

export default function IntelFeed() {
  const { state } = useCOPStore();

  return (
    <div className="bg-gray-900 rounded p-2 border border-gray-700">
      <div className="text-xs font-bold text-gray-400 mb-1">FEED DE INTELIGENCIA</div>
      <div className="space-y-1 max-h-48 overflow-y-auto">
        {state.intelFeed.length === 0 && (
          <div className="text-xs font-mono text-gray-600">Sin reportes de inteligencia</div>
        )}
        {state.intelFeed.map((i: IntelReport) => (
          <div key={i.id} className="text-xs font-mono py-1 px-1 rounded bg-gray-800/50 border-l-2 border-gray-600">
            <div className="flex items-center gap-2 mb-0.5">
              <span className={`text-[10px] px-1.5 py-0.5 rounded font-bold ${classColor[i.classification] || "text-gray-400 bg-gray-800"}`}>
                {i.classification}
              </span>
              <span className="text-cyan-400">{i.source}</span>
              <span className="text-gray-600 ml-auto">
                {new Date(i.timestamp).toISOString().slice(11, 16)}Z
              </span>
            </div>
            <div className="text-gray-300">{i.title}</div>
            <div className="flex items-center gap-1 mt-0.5">
              <span className="text-gray-500 text-[10px]">Confianza:</span>
              <div className="w-16 bg-gray-700 h-1 rounded">
                <div
                  className={`h-1 rounded ${i.confidence > 0.8 ? "bg-green-500" : i.confidence > 0.5 ? "bg-yellow-500" : "bg-red-500"}`}
                  style={{ width: `${i.confidence * 100}%` }}
                />
              </div>
              <span className="text-gray-500 text-[10px]">{Math.round(i.confidence * 100)}%</span>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
