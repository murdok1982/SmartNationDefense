"use client";
import { useState } from "react";
import { Crosshair, Route, Mountain, Download, Trash2, Eye, EyeOff } from "lucide-react";
import { useCOPStore } from "@/store/cop-store";
import type { TerrainAnalysisData } from "@/lib/cop-types";

export default function TerrainAnalysis() {
  const { terrainAnalyses, addTerrainAnalysis } = useCOPStore();
  const [tool, setTool] = useState<"LOS" | "ROUTE" | "AREA" | null>(null);
  const [startPoint, setStartPoint] = useState("");
  const [endPoint, setEndPoint] = useState("");

  const runAnalysis = () => {
    if (!tool || !startPoint) return;
    const start = startPoint.split(",").map(Number) as [number, number];
    const end = endPoint ? endPoint.split(",").map(Number) as [number, number] : undefined;
    const distance = end
      ? Math.sqrt(Math.pow((end[0] - start[0]) * 111, 2) + Math.pow((end[1] - start[1]) * 85, 2))
      : 0;
    const analysis: TerrainAnalysisData = {
      id: `ta${Date.now()}`,
      type: tool,
      startPoint: start,
      endPoint: end,
      results: {
        visible: tool === "LOS" ? Math.random() > 0.3 : true,
        distance: Math.round(distance * 10) / 10,
        elevationGain: Math.round(Math.random() * 500 + 50),
        estimatedTime: Math.round(distance * 15 + 30),
        obstacles: tool === "LOS" ? ["Cresta en 2.3km", "Vegetacion densa"] : ["Rio en waypoint 2", "Zona urbana"],
      },
    };
    addTerrainAnalysis(analysis);
    setStartPoint("");
    setEndPoint("");
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
                onClick={() => setTool(t.id)}
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
                placeholder="Inicio (lat,lon)"
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
            <button
              onClick={runAnalysis}
              className="w-full bg-green-800 hover:bg-green-700 text-green-100 text-[10px] px-2 py-1 rounded transition-colors"
            >
              Ejecutar Analisis
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
              {ta.type === "LOS" && (
                <span className={`text-[10px] flex items-center gap-0.5 ${
                  ta.results.visible ? "text-green-400" : "text-red-400"
                }`}>
                  {ta.results.visible ? <Eye size={10} /> : <EyeOff size={10} />}
                  {ta.results.visible ? "VISIBLE" : "NO VISIBLE"}
                </span>
              )}
            </div>
            <div className="grid grid-cols-2 gap-1 text-[10px]">
              <div className="text-gray-500">Distancia:</div>
              <div className="text-gray-300">{ta.results.distance} km</div>
              <div className="text-gray-500">Elev. gain:</div>
              <div className="text-gray-300">{ta.results.elevationGain} m</div>
              <div className="text-gray-500">Tiempo est.:</div>
              <div className="text-gray-300">{ta.results.estimatedTime} min</div>
            </div>
            {ta.results.obstacles.length > 0 && (
              <div className="mt-1">
                <div className="text-[10px] text-gray-500">Obstaculos:</div>
                {ta.results.obstacles.map((o, i) => (
                  <div key={i} className="text-[10px] text-yellow-400">- {o}</div>
                ))}
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
        <button className="flex items-center gap-1 text-[10px] text-gray-500 hover:text-gray-300 px-2 py-1 rounded border border-gray-700 transition-colors">
          <Download size={10} /> Exportar
        </button>
        <button className="flex items-center gap-1 text-[10px] text-gray-500 hover:text-gray-300 px-2 py-1 rounded border border-gray-700 transition-colors">
          <Trash2 size={10} /> Limpiar
        </button>
      </div>
    </div>
  );
}
