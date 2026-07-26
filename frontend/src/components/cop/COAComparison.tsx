"use client";
import { useState, useMemo } from "react";
import { ChevronDown, ChevronUp, Trophy, ArrowUpDown } from "lucide-react";
import { useMavenStore } from "@/store/maven-store";
import type { ScoredCOA } from "@/lib/maven-types";

const criteriaOptions = [
  { key: "overall_score", label: "Score máximo", direction: "desc" as const },
  { key: "risk_level", label: "Riesgo mínimo", direction: "asc" as const },
  { key: "estimated_casualties", label: "Bajas mínimas", direction: "asc" as const },
  { key: "duration_h", label: "Duración mínima", direction: "asc" as const },
  { key: "weapon_readiness", label: "Readiness máximo", direction: "desc" as const },
];

const riskOrder: Record<string, number> = {
  low: 0,
  medium: 1,
  high: 2,
  critical: 3,
};

function RiskBadge({ level }: { level: string }) {
  const colors: Record<string, string> = {
    critical: "bg-red-900/40 text-red-400",
    high: "bg-orange-900/40 text-orange-400",
    medium: "bg-yellow-900/40 text-yellow-400",
    low: "bg-green-900/40 text-green-400",
  };
  return (
    <span className={`text-[10px] font-mono px-1.5 py-0.5 rounded ${colors[level] || "bg-gray-700 text-gray-400"}`}>
      {level.toUpperCase()}
    </span>
  );
}

function COARow({ coa, isBest, isExpanded, onToggle }: {
  coa: ScoredCOA
  isBest: boolean
  isExpanded: boolean
  onToggle: () => void
}) {
  return (
    <>
      <tr className={`border-b border-gray-800 hover:bg-gray-800/30 ${isBest ? "bg-green-900/10" : ""}`}>
        <td className="py-1.5 px-2">
          <div className="flex items-center gap-1">
            {isBest && <Trophy size={10} className="text-yellow-400" />}
            <span className="text-xs font-mono text-green-400">{coa.name}</span>
          </div>
        </td>
        <td className="py-1.5 px-2">
          <div className="flex items-center gap-1">
            <div className="w-16 h-1.5 bg-gray-700 rounded overflow-hidden">
              <div className="h-full bg-green-500 rounded" style={{ width: `${coa.overall_score * 100}%` }} />
            </div>
            <span className="text-[10px] font-mono text-green-400">{(coa.overall_score * 100).toFixed(0)}%</span>
          </div>
        </td>
        <td className="py-1.5 px-2"><RiskBadge level={coa.risk_level} /></td>
        <td className="py-1.5 px-2 text-[10px] font-mono text-gray-400">{coa.estimated_casualties}</td>
        <td className="py-1.5 px-2 text-[10px] font-mono text-gray-400">{coa.duration_h}h</td>
        <td className="py-1.5 px-2">
          <div className="flex items-center gap-1">
            <div className="w-12 h-1.5 bg-gray-700 rounded overflow-hidden">
              <div className="h-full bg-blue-500 rounded" style={{ width: `${coa.weapon_readiness * 100}%` }} />
            </div>
            <span className="text-[10px] font-mono text-blue-400">{(coa.weapon_readiness * 100).toFixed(0)}%</span>
          </div>
        </td>
        <td className="py-1.5 px-2">
          <button onClick={onToggle} className="text-gray-500 hover:text-gray-300 transition-colors">
            {isExpanded ? <ChevronUp size={12} /> : <ChevronDown size={12} />}
          </button>
        </td>
      </tr>
      {isExpanded && (
        <tr className="bg-gray-900/50">
          <td colSpan={7} className="px-2 pb-2">
            <div className="text-[10px] font-mono text-gray-400 mb-1">{coa.description}</div>
            <div className="text-[10px] font-bold text-gray-500 mb-1">FASES</div>
            <div className="space-y-1">
              {coa.phases.map((phase, i) => (
                <div key={i} className="bg-gray-800 rounded px-2 py-1 border border-gray-700">
                  <div className="text-[10px] font-mono text-green-400">{phase.name}</div>
                  <div className="text-[10px] font-mono text-gray-400">{phase.description}</div>
                  <div className="text-[10px] font-mono text-gray-500">Duración: {phase.duration_h}h</div>
                  {phase.waypoints.length > 0 && (
                    <div className="text-[10px] font-mono text-gray-600">
                      Rutas: {phase.waypoints.map(w => `${w[0].toFixed(2)}°N,${w[1].toFixed(2)}°E`).join(" → ")}
                    </div>
                  )}
                </div>
              ))}
            </div>
          </td>
        </tr>
      )}
    </>
  );
}

export default function COAComparison() {
  const { coas, loading, error } = useMavenStore();
  const [selectedCriterion, setSelectedCriterion] = useState(criteriaOptions[0].key);
  const [expandedId, setExpandedId] = useState<string | null>(null);

  const criterion = criteriaOptions.find(c => c.key === selectedCriterion)!;

  const sorted = useMemo(() => {
    const list = [...coas];
    list.sort((a, b) => {
      let valA: number;
      let valB: number;

      switch (criterion.key) {
        case "risk_level":
          valA = riskOrder[a.risk_level] ?? 99;
          valB = riskOrder[b.risk_level] ?? 99;
          break;
        case "overall_score":
          valA = a.overall_score;
          valB = b.overall_score;
          break;
        case "estimated_casualties":
          valA = a.estimated_casualties;
          valB = b.estimated_casualties;
          break;
        case "duration_h":
          valA = a.duration_h;
          valB = b.duration_h;
          break;
        case "weapon_readiness":
          valA = a.weapon_readiness;
          valB = b.weapon_readiness;
          break;
        default:
          valA = a.overall_score;
          valB = b.overall_score;
      }

      return criterion.direction === "desc" ? valB - valA : valA - valB;
    });
    return list;
  }, [coas, criterion]);

  if (error) {
    return (
      <div className="bg-red-900/20 border border-red-800 rounded p-3 m-2">
        <div className="text-xs font-mono text-red-400">Error: {error}</div>
      </div>
    );
  }

  if (!loading && coas.length === 0) {
    return (
      <div className="bg-gray-900 rounded border border-gray-700 p-6 m-2 text-center">
        <ArrowUpDown size={24} className="text-gray-700 mx-auto mb-2" />
        <div className="text-xs font-mono text-gray-600">Genere cursos de acción para ver la comparativa.</div>
      </div>
    );
  }

  const best = sorted[0];

  return (
    <div className="bg-[#0a0e17] p-2">
      <div className="flex items-center justify-between mb-2">
        <span className="text-xs font-bold text-gray-400">COMPARATIVA DE CURSOS DE ACCIÓN</span>
        <div className="flex items-center gap-1">
          <span className="text-[10px] font-mono text-gray-500">Ordenar por:</span>
          <select
            value={selectedCriterion}
            onChange={e => setSelectedCriterion(e.target.value)}
            className="bg-gray-800 border border-gray-700 rounded px-2 py-0.5 text-[10px] font-mono text-gray-200 focus:outline-none focus:border-green-700"
          >
            {criteriaOptions.map(c => (
              <option key={c.key} value={c.key}>{c.label}</option>
            ))}
          </select>
        </div>
      </div>

      <div className="overflow-x-auto">
        <table className="w-full text-xs font-mono">
          <thead>
            <tr className="text-gray-500 border-b border-gray-700">
              <th className="text-left py-1 px-2">Nombre</th>
              <th className="text-left py-1 px-2">Score</th>
              <th className="text-left py-1 px-2">Riesgo</th>
              <th className="text-left py-1 px-2">Bajas est.</th>
              <th className="text-left py-1 px-2">Duración</th>
              <th className="text-left py-1 px-2">Readiness armas</th>
              <th className="text-left py-1 px-2">Detalle</th>
            </tr>
          </thead>
          <tbody>
            {sorted.map(coa => (
              <COARow
                key={coa.id}
                coa={coa}
                isBest={coa.id === best?.id}
                isExpanded={expandedId === coa.id}
                onToggle={() => setExpandedId(expandedId === coa.id ? null : coa.id)}
              />
            ))}
          </tbody>
        </table>
      </div>

      {best && (
        <div className="mt-2 bg-green-900/20 border border-green-800 rounded p-2">
          <div className="flex items-center gap-1 text-[10px] font-mono text-green-400">
            <Trophy size={10} />
            Mejor COA: <strong>{best.name}</strong> según criterio "{criterion.label}"
          </div>
        </div>
      )}
    </div>
  );
}
