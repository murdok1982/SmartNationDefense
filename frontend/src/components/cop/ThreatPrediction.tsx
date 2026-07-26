"use client";
import { useState, FormEvent } from "react";
import { Target, TrendingUp, MapPin, AlertTriangle, Clock, Play } from "lucide-react";
import { useCOPStore } from "@/store/cop-store";
import { apiFetch, apiErrorMessage } from "@/lib/api";
import { mapPrediction, type BackendPrediction } from "@/lib/mappers";

const threatLevelColor = (level: number) =>
  level >= 80 ? "text-red-400" : level >= 60 ? "text-orange-400" : level >= 40 ? "text-yellow-400" : "text-blue-400";

const threatBarColor = (level: number) =>
  level >= 80 ? "bg-red-500" : level >= 60 ? "bg-orange-500" : level >= 40 ? "bg-yellow-500" : "bg-blue-500";

const confidenceColor = (c: number) =>
  c > 0.8 ? "text-green-400" : c > 0.5 ? "text-yellow-400" : "text-red-400";

export default function ThreatPrediction() {
  const { threatPredictions, addThreatPrediction } = useCOPStore();
  const [selectedThreat, setSelectedThreat] = useState<string | null>(null);
  const [timeHorizon, setTimeHorizon] = useState(6);
  const [unitId, setUnitId] = useState("");
  const [lat, setLat] = useState("");
  const [lon, setLon] = useState("");
  const [speed, setSpeed] = useState("0");
  const [heading, setHeading] = useState("0");
  const [threatLevelInput, setThreatLevelInput] = useState("50");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const filtered = threatPredictions.filter(t => t.timeHorizon <= timeHorizon);

  const handlePredict = async (e: FormEvent) => {
    e.preventDefault();
    const latN = Number(lat);
    const lonN = Number(lon);
    if (!unitId.trim() || Number.isNaN(latN) || Number.isNaN(lonN)) return;
    setSubmitting(true);
    setError(null);
    try {
      const result = await apiFetch<BackendPrediction>("/api/v1/prediction/predict-movement", {
        method: "POST",
        body: {
          id: unitId.trim(),
          lat: latN,
          lon: lonN,
          speed: Number(speed) || 0,
          heading: Number(heading) || 0,
          threat_level: Number(threatLevelInput) || 50,
          time_horizon_min: timeHorizon * 60,
        },
      });
      addThreatPrediction(mapPrediction(result));
    } catch (err) {
      setError(apiErrorMessage(err));
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="bg-gray-900 rounded border border-gray-700 flex flex-col h-full">
      <div className="flex items-center gap-2 px-3 py-2 border-b border-gray-700">
        <Target size={14} className="text-red-400" />
        <span className="text-xs font-bold text-gray-400">PREDICCION DE AMENAZAS</span>
      </div>

      <form onSubmit={handlePredict} className="p-2 border-b border-gray-700 space-y-1">
        <div className="text-[10px] text-gray-500 font-bold">NUEVA PREDICCION (KALMAN)</div>
        <div className="flex gap-1">
          <input
            value={unitId}
            onChange={e => setUnitId(e.target.value)}
            placeholder="ID unidad hostil"
            className="flex-1 bg-gray-800 text-gray-300 text-[10px] rounded px-2 py-1 border border-gray-700"
          />
          <input
            value={lat}
            onChange={e => setLat(e.target.value)}
            placeholder="Lat"
            className="w-20 bg-gray-800 text-gray-300 text-[10px] rounded px-2 py-1 border border-gray-700"
          />
          <input
            value={lon}
            onChange={e => setLon(e.target.value)}
            placeholder="Lon"
            className="w-20 bg-gray-800 text-gray-300 text-[10px] rounded px-2 py-1 border border-gray-700"
          />
        </div>
        <div className="flex gap-1 items-center">
          <input
            value={speed}
            onChange={e => setSpeed(e.target.value)}
            placeholder="Velocidad km/h"
            className="flex-1 bg-gray-800 text-gray-300 text-[10px] rounded px-2 py-1 border border-gray-700"
          />
          <input
            value={heading}
            onChange={e => setHeading(e.target.value)}
            placeholder="Rumbo deg"
            className="flex-1 bg-gray-800 text-gray-300 text-[10px] rounded px-2 py-1 border border-gray-700"
          />
          <input
            value={threatLevelInput}
            onChange={e => setThreatLevelInput(e.target.value)}
            placeholder="Amenaza 0-100"
            className="flex-1 bg-gray-800 text-gray-300 text-[10px] rounded px-2 py-1 border border-gray-700"
          />
          <button
            type="submit"
            disabled={submitting}
            className="bg-red-900/40 hover:bg-red-900/60 disabled:opacity-50 text-red-300 text-[10px] px-2 py-1 rounded border border-red-800 flex items-center gap-1 transition-colors"
          >
            <Play size={10} />
            {submitting ? "..." : "Predecir"}
          </button>
        </div>
        {error && <div className="text-[10px] font-mono text-red-400">{error}</div>}
      </form>

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
            Sin predicciones. Solicite una prediccion de movimiento.
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
                {Math.round(t.threatLevel)}/100
              </span>
            </div>

            <div className="w-full bg-gray-700 h-1 rounded mb-1">
              <div
                className={`h-1 rounded ${threatBarColor(t.threatLevel)}`}
                style={{ width: `${Math.min(100, t.threatLevel)}%` }}
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
