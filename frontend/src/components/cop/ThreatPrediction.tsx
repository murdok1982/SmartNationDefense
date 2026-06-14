"use client";
import { useState } from "react";
import { Target, TrendingUp, MapPin, AlertTriangle, Eye, EyeOff, Clock } from "lucide-react";
import { useCOPStore } from "@/store/cop-store";

const threatLevelColor = (level: number) =>
  level >= 8 ? "text-red-400" : level >= 6 ? "text-orange-400" : level >= 4 ? "text-yellow-400" : "text-blue-400";

const threatBarColor = (level: number) =>
  level >= 8 ? "bg-red-500" : level >= 6 ? "bg-orange-500" : level >= 4 ? "bg-yellow-500" : "bg-blue-500";

const confidenceColor = (c: number) =>
  c > 0.8 ? "text-green-400" : c > 0.5 ? "text-yellow-400" : "text-red-400";

export default function ThreatPrediction() {
  const { threatPredictions } = useCOPStore();
  const [showOverlay, setShowOverlay] = useState(true);
  const [selectedThreat, setSelectedThreat] = useState<string | null>(null);
  const [timeHorizon, setTimeHorizon] = useState(6);

  const filtered = threatPredictions.filter(t => t.timeHorizon <= timeHorizon);

  return (
    <div className="bg-gray-900 rounded border border-gray-700 flex flex-col h-full">
      <div className="flex items-center gap-2 px-3 py-2 border-b border-gray-700">
        <Target size={14} className="text-red-400" />
        <span className="text-xs font-bold text-gray-400">PREDICCION DE AMENAZAS</span>
        <button
          onClick={() => setShowOverlay(!showOverlay)}
          className={`ml-auto text-[10px] flex items-center gap-0.5 px-1.5 py-0.5 rounded border transition-colors ${
            showOverlay ? "text-green-400 border-green-700 bg-green-900/20" : "text-gray-500 border-gray-700"
          }`}
        >
          {showOverlay ? <Eye size={10} /> : <EyeOff size={10} />} Overlay
        </button>
      </div>

      <div className="p-2 border-b border-gray-700">
        <div className="flex items-center gap-2">
          <Clock size={10} className="text-gray-500" />
          <span className="text-[10px] text-gray-500">Horizonte:</span>
          <div className="flex gap-1">
            {[3, 6, 12, 24].map(h => (
              <button
                key={h}
                onClick={() => setTimeHorizon(h)}
                className={`text-[10px] px-1.5 py-0.5 rounded border transition-colors ${
                  timeHorizon === h
                    ? "bg-green-900/30 border-green-700 text-green-400"
                    : "bg-gray-800 border-gray-700 text-gray-500"
                }`}
              >
                {h}h
              </button>
            ))}
          </div>
        </div>
      </div>

      <div className="flex-1 overflow-y-auto p-2 space-y-2">
        {filtered.length === 0 && (
          <div className="text-xs font-mono text-gray-600 text-center py-4">
            Sin predicciones en el horizonte seleccionado
          </div>
        )}
        {filtered.map(t => (
          <button
            key={t.unitId}
            onClick={() => setSelectedThreat(selectedThreat === t.unitId ? null : t.unitId)}
            className={`w-full text-left text-xs font-mono p-2 rounded border transition-colors ${
              selectedThreat === t.unitId
                ? "bg-gray-800 border-gray-600"
                : "bg-gray-800/50 border-gray-700 hover:bg-gray-800"
            }`}
          >
            <div className="flex items-center justify-between mb-1">
              <span className="text-red-400 font-bold">{t.unitName}</span>
              <span className={`text-[10px] font-bold ${threatLevelColor(t.threatLevel)}`}>
                {t.threatLevel}/10
              </span>
            </div>

            <div className="w-full bg-gray-700 h-1 rounded mb-1">
              <div
                className={`h-1 rounded ${threatBarColor(t.threatLevel)}`}
                style={{ width: `${t.threatLevel * 10}%` }}
              />
            </div>

            <div className="grid grid-cols-2 gap-1 text-[10px]">
              <div className="flex items-center gap-0.5 text-gray-500">
                <MapPin size={8} /> Actual:
              </div>
              <div className="text-gray-400">
                {t.currentLocation[0].toFixed(2)}°N {t.currentLocation[1].toFixed(2)}°E
              </div>
              <div className="flex items-center gap-0.5 text-gray-500">
                <TrendingUp size={8} /> Prediccion:
              </div>
              <div className="text-gray-400">
                {t.predictedLocation[0].toFixed(2)}°N {t.predictedLocation[1].toFixed(2)}°E
              </div>
            </div>

            <div className="flex items-center gap-2 mt-1">
              <span className={`text-[10px] ${confidenceColor(t.confidence)}`}>
                Confianza: {Math.round(t.confidence * 100)}%
              </span>
              <span className="text-[10px] text-gray-600">
                {t.timeHorizon}h horizonte
              </span>
            </div>

            {selectedThreat === t.unitId && (
              <div className="mt-2 pt-2 border-t border-gray-700 space-y-1">
                <div className="text-[10px] text-gray-500">
                  <span className="font-bold">Patron:</span> {t.movementPattern}
                </div>
                <div className="text-[10px] text-yellow-400 flex items-start gap-0.5">
                  <AlertTriangle size={10} className="shrink-0 mt-0.5" />
                  <span><span className="font-bold">ACC:</span> {t.recommendedAction}</span>
                </div>
              </div>
            )}
          </button>
        ))}
      </div>
    </div>
  );
}
