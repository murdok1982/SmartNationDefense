"use client";
import { useState } from "react";
import { Crosshair, Route, Mountain, Trash2, Eye, EyeOff } from "lucide-react";
import { useCOPStore } from "@/store/cop-store";
import { apiFetch, apiErrorMessage } from "@/lib/api";
import type { TerrainAnalysisData } from "@/lib/cop-types";

interface LOSResponse {
  visible: boolean
  distance_km: number
  min_clearance_m: number
  obstructions: { distance_km: number; blockage_m: number }[]
}

interface RouteResponse {
  total_distance_km: number
  estimated_time_min: number
  difficulty: string
  obstacles: { segment: number; obstacle: string }[]
  recommendations: string[]
}

interface AreaResponse {
  trafficability: Record<string, { accessible_pct: number }>
  key_terrain: { location: { lat: number; lon: number }; elevation_m: number; strategic_value: string; description: string }[]
  obstacles: { type: string; description: string; severity: string }[]
  recommendations: string[]
}

function parsePoint(input: string): [number, number] | null {
  const parts = input.split(",").map(s => Number(s.trim()));
  if (parts.length !== 2 || parts.some(Number.isNaN)) return null;
  return [parts[0], parts[1]];
}

export default function TerrainAnalysis() {
  const { terrainAnalyses, addTerrainAnalysis, clearTerrainAnalyses } = useCOPStore();
  const [tool, setTool] = useState<"LOS" | "ROUTE" | "AREA" | null>(null);
  const [startPoint, setStartPoint] = useState("");
  const [endPoint, setEndPoint] = useState("");
  const [running, setRunning] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const runAnalysis = async () => {
    if (!tool) return;
    const start = parsePoint(startPoint);
    if (!start) {
      setError("Coordenadas de inicio invalidas (formato: lat,lon)");
      return;
    }
    const end = tool !== "AREA" ? parsePoint(endPoint) : null;
    if (tool !== "AREA" && !end) {
      setError("Coordenadas de fin invalidas (formato: lat,lon)");
      return;
    }

    setRunning(true);
    setError(null);
    try {
      const id = `ta${Date.now()}`;
      if (tool === "LOS" && end) {
        const r = await apiFetch<LOSResponse>("/api/v1/terrain/line-of-sight", {
          method: "POST",
          body: { observer: { lat: start[0], lon: start[1] }, target: { lat: end[0], lon: end[1] } },
        });
        const analysis: TerrainAnalysisData = {
          id, type: "LOS", startPoint: start, endPoint: end,
          los: {
            visible: r.visible,
            distanceKm: r.distance_km,
            minClearanceM: r.min_clearance_m,
            obstructions: r.obstructions.map(o => ({ distanceKm: o.distance_km, blockageM: o.blockage_m })),
          },
        };
        addTerrainAnalysis(analysis);
      } else if (tool === "ROUTE" && end) {
        const r = await apiFetch<RouteResponse>("/api/v1/terrain/route-analysis", {
          method: "POST",
          body: { start: { lat: start[0], lon: start[1] }, end: { lat: end[0], lon: end[1] }, vehicle_type: "INFANTRY" },
        });
        const analysis: TerrainAnalysisData = {
          id, type: "ROUTE", startPoint: start, endPoint: end,
          route: {
            distanceKm: r.total_distance_km,
            estimatedTimeMin: r.estimated_time_min,
            difficulty: r.difficulty,
            obstacles: r.obstacles.map(o => o.obstacle),
            recommendations: r.recommendations,
          },
        };
        addTerrainAnalysis(analysis);
      } else {
        const r = await apiFetch<AreaResponse>("/api/v1/terrain/terrain-analysis", {
          method: "POST",
          body: { center_lat: start[0], center_lon: start[1], radius_km: 10 },
        });
        const analysis: TerrainAnalysisData = {
          id, type: "AREA", startPoint: start,
          area: {
            trafficability: r.trafficability,
            keyTerrain: r.key_terrain,
            obstacles: r.obstacles,
            recommendations: r.recommendations,
          },
        };
        addTerrainAnalysis(analysis);
      }
      setStartPoint("");
      setEndPoint("");
    } catch (e) {
      setError(apiErrorMessage(e));
    } finally {
      setRunning(false);
    }
  };

  const tools = [
    { id: "LOS" as const, label: "Linea de Vision", icon: Eye },
    { id: "ROUTE" as const, label: "Análisis de Ruta", icon: Route },
    { id: "AREA" as const, label: "Análisis de Área", icon: Mountain },
  ];

  return (
    <div className="bg-gray-900 rounded border border-gray-700 flex flex-col h-full">
      <div className="flex items-center gap-2 px-3 py-2 border-b border-gray-700">
        <Mountain size={14} className="text-green-400" />
        <span className="text-xs font-bold text-gray-400">ANALISIS DE TERRENO</span>
      </div>

      <div className="p-2 border-b border-gray-700">
        <div className="flex gap-1 mb-2">
          {tools.map(t => {
            const Icon = t.icon;
            return (
              <button
                key={t.id}
                onClick={() => { setTool(t.id); setError(null); }}
                className={`flex items-center gap-1 text-[10px] px-2 py-1 rounded border transition-colors ${
                  tool === t.id
                    ? "bg-green-900/30 border-green-700 text-green-400"
                    : "bg-gray-800 border-gray-700 text-gray-500 hover:text-gray-300"
                }`}
              >
                <Icon size={10} />
                {t.label}
              </button>
            );
          })}
        </div>

        {tool && (
          <div className="space-y-1">
            <div className="flex gap-1">
              <input
                value={startPoint}
                onChange={e => setStartPoint(e.target.value)}
                placeholder={tool === "AREA" ? "Centro (lat,lon)" : "Inicio (lat,lon)"}
                className="flex-1 bg-gray-800 text-gray-300 text-[10px] rounded px-2 py-1 border border-gray-700"
              />
              <button
                onClick={() => setStartPoint("40.42,-3.70")}
                className="text-[10px] text-gray-500 hover:text-gray-300 px-1"
              >
                <Crosshair size={10} />
              </button>
            </div>
            {tool !== "AREA" && (
              <div className="flex gap-1">
                <input
                  value={endPoint}
                  onChange={e => setEndPoint(e.target.value)}
                  placeholder="Fin (lat,lon)"
                  className="flex-1 bg-gray-800 text-gray-300 text-[10px] rounded px-2 py-1 border border-gray-700"
                />
                <button
                  onClick={() => setEndPoint("40.50,-3.50")}
                  className="text-[10px] text-gray-500 hover:text-gray-300 px-1"
                >
                  <Crosshair size={10} />
                </button>
              </div>
            )}
            {error && <div className="text-[10px] font-mono text-red-400">{error}</div>}
            <button
              onClick={() => void runAnalysis()}
              disabled={running}
              className="w-full bg-green-800 hover:bg-green-700 disabled:opacity-50 text-green-100 text-[10px] px-2 py-1 rounded transition-colors"
            >
              {running ? "Ejecutando..." : "Ejecutar Analisis"}
            </button>
          </div>
        )}
      </div>

      <div className="flex-1 overflow-y-auto p-2 space-y-2">
        {terrainAnalyses.length === 0 && (
          <div className="text-xs font-mono text-gray-600 text-center py-4">
            Sin analisis. Seleccione herramienta y puntos.
          </div>
        )}
        {terrainAnalyses.map(ta => (
          <div key={ta.id} className="text-xs font-mono p-2 rounded bg-gray-800/50 border border-gray-700">
            <div className="flex items-center justify-between mb-1">
              <span className={`px-1.5 py-0.5 rounded text-[10px] font-bold ${
                ta.type === "LOS" ? "bg-blue-900/30 text-blue-400" :
                ta.type === "ROUTE" ? "bg-green-900/30 text-green-400" :
                "bg-purple-900/30 text-purple-400"
              }`}>
                {ta.type}
              </span>
              {ta.los && (
                <span className={`text-[10px] flex items-center gap-0.5 ${
                  ta.los.visible ? "text-green-400" : "text-red-400"
                }`}>
                  {ta.los.visible ? <Eye size={10} /> : <EyeOff size={10} />}
                  {ta.los.visible ? "VISIBLE" : "NO VISIBLE"}
                </span>
              )}
              {ta.route && (
                <span className="text-[10px] text-yellow-400 font-bold">{ta.route.difficulty}</span>
              )}
            </div>

            {ta.los && (
              <div className="grid grid-cols-2 gap-1 text-[10px]">
                <div className="text-gray-500">Distancia:</div>
                <div className="text-gray-300">{ta.los.distanceKm} km</div>
                <div className="text-gray-500">Claro minimo:</div>
                <div className="text-gray-300">{ta.los.minClearanceM} m</div>
                {ta.los.obstructions.length > 0 && (
                  <>
                    <div className="text-gray-500">Obstrucciones:</div>
                    <div className="text-yellow-400">
                      {ta.los.obstructions.map((o, i) => (
                        <div key={i}>- {o.distanceKm} km (bloqueo {o.blockageM} m)</div>
                      ))}
                    </div>
                  </>
                )}
              </div>
            )}

            {ta.route && (
              <div className="grid grid-cols-2 gap-1 text-[10px]">
                <div className="text-gray-500">Distancia:</div>
                <div className="text-gray-300">{ta.route.distanceKm} km</div>
                <div className="text-gray-500">Tiempo est.:</div>
                <div className="text-gray-300">{ta.route.estimatedTimeMin} min</div>
                {ta.route.obstacles.length > 0 && (
                  <>
                    <div className="text-gray-500">Obstaculos:</div>
                    <div className="text-yellow-400">
                      {ta.route.obstacles.map((o, i) => <div key={i}>- {o}</div>)}
                    </div>
                  </>
                )}
                <div className="text-gray-500">Recomend.:</div>
                <div className="text-gray-400">
                  {ta.route.recommendations.map((r, i) => <div key={i}>- {r}</div>)}
                </div>
              </div>
            )}

            {ta.area && (
              <div className="space-y-1 text-[10px]">
                <div className="flex gap-2">
                  {Object.entries(ta.area.trafficability).map(([vehicle, t]) => (
                    <span key={vehicle} className="text-gray-400">
                      {vehicle}: <span className="text-green-400">{t.accessible_pct}%</span>
                    </span>
                  ))}
                </div>
                {ta.area.keyTerrain.length > 0 && (
                  <div>
                    <div className="text-gray-500">Terreno clave:</div>
                    {ta.area.keyTerrain.map((k, i) => (
                      <div key={i} className="text-gray-400">
                        - {k.description} ({k.elevation_m} m, valor {k.strategic_value})
                      </div>
                    ))}
                  </div>
                )}
                {ta.area.obstacles.length > 0 && (
                  <div>
                    <div className="text-gray-500">Obstaculos:</div>
                    {ta.area.obstacles.map((o, i) => (
                      <div key={i} className="text-yellow-400">- [{o.type}] {o.description} ({o.severity})</div>
                    ))}
                  </div>
                )}
                {ta.area.recommendations.length > 0 && (
                  <div>
                    <div className="text-gray-500">Recomendaciones:</div>
                    {ta.area.recommendations.map((r, i) => (
                      <div key={i} className="text-gray-400">- {r}</div>
                    ))}
                  </div>
                )}
              </div>
            )}

            <div className="flex gap-1 mt-1">
              <span className="text-[10px] text-gray-600">
                {ta.startPoint[0].toFixed(3)}, {ta.startPoint[1].toFixed(3)}
              </span>
              {ta.endPoint && (
                <>
                  <span className="text-gray-600">→</span>
                  <span className="text-[10px] text-gray-600">
                    {ta.endPoint[0].toFixed(3)}, {ta.endPoint[1].toFixed(3)}
                  </span>
                </>
              )}
            </div>
          </div>
        ))}
      </div>

      <div className="border-t border-gray-700 p-2 flex gap-1">
        <button
          onClick={clearTerrainAnalyses}
          className="flex items-center gap-1 text-[10px] text-gray-500 hover:text-gray-300 px-2 py-1 rounded border border-gray-700 transition-colors"
        >
          <Trash2 size={10} /> Limpiar
        </button>
      </div>
    </div>
  );
}
