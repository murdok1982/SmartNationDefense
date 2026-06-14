"use client";
import { useCOPStore } from "@/store/cop-store";
import type { ThreatAssessment } from "@/lib/cop-types";

const severityLabel = (s: number) =>
  s >= 8 ? "CRÍTICA" : s >= 6 ? "ALTA" : s >= 4 ? "MEDIA" : "BAJA";

const severityColor = (s: number) =>
  s >= 8 ? "text-red-400" : s >= 6 ? "text-orange-400" : s >= 4 ? "text-yellow-400" : "text-blue-400";

const barColor = (s: number) =>
  s >= 8 ? "bg-red-500" : s >= 6 ? "bg-orange-500" : s >= 4 ? "bg-yellow-500" : "bg-blue-500";

export default function ThreatPanel() {
  const { state } = useCOPStore();

  const maxSeverity = state.threats.length > 0
    ? Math.max(...state.threats.map((t: ThreatAssessment) => t.severity))
    : 0;

  return (
    <div className="bg-gray-900 rounded p-2 border border-gray-700">
      <div className="flex items-center justify-between mb-1">
        <div className="text-xs font-bold text-gray-400">EVALUACIÓN DE AMENAZAS</div>
        {state.threats.length > 0 && (
          <span className={`text-[10px] font-mono font-bold ${severityColor(maxSeverity)}`}>
            NIVEL MÁX: {severityLabel(maxSeverity)}
          </span>
        )}
      </div>
      {state.threats.length > 0 && (
        <div className="mb-2">
          <div className="flex items-center justify-between text-[10px] text-gray-500 mb-0.5">
            <span>Confianza global</span>
            <span>{Math.round(
              (state.threats.reduce((acc: number, t: ThreatAssessment) => acc + t.confidence, 0) / state.threats.length) * 100
            )}%</span>
          </div>
          <div className="w-full bg-gray-700 h-1.5 rounded">
            <div
              className="h-1.5 rounded bg-red-500 transition-all"
              style={{
                width: `${(state.threats.reduce((acc: number, t: ThreatAssessment) => acc + t.confidence, 0) / state.threats.length) * 100}%`,
              }}
            />
          </div>
        </div>
      )}
      <div className="space-y-1 max-h-40 overflow-y-auto">
        {state.threats.length === 0 && (
          <div className="text-xs font-mono text-gray-600">Sin amenazas evaluadas</div>
        )}
        {state.threats.map((t: ThreatAssessment) => (
          <div key={t.id} className="text-xs font-mono py-1 px-1 rounded bg-gray-800/50">
            <div className="flex items-center justify-between mb-0.5">
              <span className={`font-bold ${severityColor(t.severity)}`}>{t.target}</span>
              <span className={`text-[10px] ${severityColor(t.severity)}`}>
                {severityLabel(t.severity)} ({t.severity}/10)
              </span>
            </div>
            <div className="w-full bg-gray-700 h-1 rounded mb-0.5">
              <div
                className={`h-1 rounded ${barColor(t.severity)}`}
                style={{ width: `${t.confidence * 100}%` }}
              />
            </div>
            <div className="text-[10px] text-gray-500">ACC: {t.recommended_action}</div>
          </div>
        ))}
      </div>
    </div>
  );
}
