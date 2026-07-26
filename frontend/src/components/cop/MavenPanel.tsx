"use client";
import { useState, useCallback } from "react";
import {
  Satellite, ScanEye, Route, ClipboardCheck, Upload,
  Search, Filter, MapPin, AlertTriangle, Loader2,
} from "lucide-react";
import { useMavenStore } from "@/store/maven-store";
import type { Detection, Track, ScoredCOA } from "@/lib/maven-types";

type MavenTab = "satellite" | "detections" | "tracks" | "coa";

interface TabConfig {
  id: MavenTab
  label: string
  icon: typeof Satellite
}

const tabs: TabConfig[] = [
  { id: "satellite", label: "Vista Satélite", icon: Satellite },
  { id: "detections", label: "Detecciones CV", icon: ScanEye },
  { id: "tracks", label: "Tracks Fusionados", icon: Route },
  { id: "coa", label: "COA Planner", icon: ClipboardCheck },
];

function DetectionBBox({ detection }: { detection: Detection }) {
  const [x1, y1, x2, y2] = detection.bbox;
  return (
    <div className="relative inline-block border border-green-500/30 rounded overflow-hidden bg-gray-800/50">
      <div
        className="absolute border-2 border-red-400 pointer-events-none"
        style={{
          left: `${x1 * 100}%`,
          top: `${y1 * 100}%`,
          width: `${(x2 - x1) * 100}%`,
          height: `${(y2 - y1) * 100}%`,
        }}
      />
      <div className="p-2 text-[10px] font-mono text-gray-400">
        bbox: [{x1.toFixed(3)}, {y1.toFixed(3)}, {x2.toFixed(3)}, {y2.toFixed(3)}]
      </div>
    </div>
  );
}

function SatelliteTab() {
  const { satelliteImages, loading, error, requestAnalysis } = useMavenStore();
  const [imageUrl, setImageUrl] = useState("");
  const [analyzing, setAnalyzing] = useState(false);

  const handleAnalyze = useCallback(async () => {
    if (!imageUrl.trim()) return;
    setAnalyzing(true);
    await requestAnalysis(imageUrl.trim());
    setAnalyzing(false);
  }, [imageUrl, requestAnalysis]);

  return (
    <div className="space-y-3">
      <div className="bg-gray-900 rounded border border-gray-700 p-3">
        <div className="text-xs font-bold text-gray-400 mb-2">ANÁLISIS DE IMAGEN SATELITAL/DRON</div>
        <div className="flex gap-2">
          <input
            type="text"
            value={imageUrl}
            onChange={e => setImageUrl(e.target.value)}
            placeholder="URL de imagen satelital o dron..."
            className="flex-1 bg-gray-800 border border-gray-700 rounded px-2 py-1.5 text-xs font-mono text-gray-200 placeholder-gray-600 focus:outline-none focus:border-green-700"
          />
          <button
            onClick={handleAnalyze}
            disabled={analyzing || !imageUrl.trim()}
            className="flex items-center gap-1 bg-green-900/30 text-green-400 border border-green-700 rounded px-3 py-1.5 text-xs font-mono hover:bg-green-900/50 disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
          >
            {analyzing ? <Loader2 size={12} className="animate-spin" /> : <Upload size={12} />}
            Analizar con CV
          </button>
        </div>
      </div>

      {error && (
        <div className="bg-red-900/20 border border-red-800 rounded p-3">
          <div className="flex items-center gap-1 text-red-400 text-xs font-mono">
            <AlertTriangle size={12} />
            Backend CV no disponible: {error}
          </div>
        </div>
      )}

      {!error && loading && satelliteImages.length === 0 && (
        <div className="bg-gray-900 rounded border border-gray-700 p-6 text-center">
          <Loader2 size={16} className="animate-spin text-green-400 mx-auto mb-2" />
          <div className="text-xs font-mono text-gray-500">Procesando imagen...</div>
        </div>
      )}

      {!error && !loading && satelliteImages.length === 0 && (
        <div className="bg-gray-900 rounded border border-gray-700 p-6 text-center">
          <Satellite size={24} className="text-gray-700 mx-auto mb-2" />
          <div className="text-xs font-mono text-gray-600">Ingrese una URL de imagen y presione "Analizar con CV"</div>
        </div>
      )}

      <div className="space-y-2">
        {satelliteImages.map(img => (
          <div key={img.id} className="bg-gray-900 rounded border border-gray-700 p-3">
            <div className="flex items-center justify-between mb-2">
              <span className="text-[10px] font-mono text-gray-500">
                {img.source.toUpperCase()} — {new Date(img.timestamp).toISOString().slice(11, 19)}Z
              </span>
              <span className="text-[10px] font-mono text-green-400">
                {img.detections.length} deteccion(es)
              </span>
            </div>
            {img.detections.length > 0 ? (
              <div className="space-y-1">
                {img.detections.map(d => (
                  <div key={d.id} className="flex items-center gap-2 text-[10px] font-mono bg-gray-800 rounded px-2 py-1">
                    <span className="text-green-400">{d.class_name}</span>
                    <span className="text-gray-500">conf: {(d.confidence * 100).toFixed(0)}%</span>
                    <span className={`px-1 rounded ${
                      d.classification === "hostile" ? "bg-red-900/40 text-red-400" :
                      d.classification === "friendly" ? "bg-green-900/40 text-green-400" :
                      "bg-gray-700 text-gray-400"
                    }`}>
                      {d.classification}
                    </span>
                  </div>
                ))}
              </div>
            ) : (
              <div className="text-[10px] font-mono text-gray-600">Sin detecciones en esta imagen</div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}

function DetectionsTab() {
  const { detections, loading, error } = useMavenStore();
  const [filterClass, setFilterClass] = useState("");
  const [filterConf, setFilterConf] = useState(0);

  const filtered = detections.filter(d => {
    if (filterClass && !d.class_name.toLowerCase().includes(filterClass.toLowerCase())) return false;
    if (d.confidence < filterConf) return false;
    return true;
  });

  const centerMap = (lat?: number, lon?: number) => {
    if (lat === undefined || lon === undefined) return;
    const detail = document.getElementById("cop-map");
    if (detail) detail.scrollIntoView({ behavior: "smooth" });
  };

  if (error) {
    return (
      <div className="bg-red-900/20 border border-red-800 rounded p-3">
        <div className="flex items-center gap-1 text-red-400 text-xs font-mono">
          <AlertTriangle size={12} />
          Backend CV no disponible: {error}
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-3">
      <div className="flex gap-2 items-center">
        <div className="flex items-center gap-1 bg-gray-800 rounded px-2 py-1 border border-gray-700">
          <Search size={10} className="text-gray-500" />
          <input
            type="text"
            value={filterClass}
            onChange={e => setFilterClass(e.target.value)}
            placeholder="Filtrar por clase..."
            className="bg-transparent text-xs font-mono text-gray-200 placeholder-gray-600 w-28 focus:outline-none"
          />
        </div>
        <div className="flex items-center gap-1 bg-gray-800 rounded px-2 py-1 border border-gray-700">
          <Filter size={10} className="text-gray-500" />
          <input
            type="range"
            min={0}
            max={1}
            step={0.05}
            value={filterConf}
            onChange={e => setFilterConf(Number(e.target.value))}
            className="w-16 accent-green-500"
          />
          <span className="text-[10px] font-mono text-gray-400 w-8">{(filterConf * 100).toFixed(0)}%</span>
        </div>
        <span className="text-[10px] font-mono text-gray-500 ml-auto">{filtered.length} de {detections.length}</span>
      </div>

      {loading && (
        <div className="text-center py-4">
          <Loader2 size={16} className="animate-spin text-green-400 mx-auto" />
        </div>
      )}

      {!loading && filtered.length === 0 && (
        <div className="bg-gray-900 rounded border border-gray-700 p-6 text-center">
          <ScanEye size={24} className="text-gray-700 mx-auto mb-2" />
          <div className="text-xs font-mono text-gray-600">Sin detecciones. Analice una imagen satelital o espere datos del backend.</div>
        </div>
      )}

      <div className="overflow-x-auto">
        <table className="w-full text-xs font-mono">
          <thead>
            <tr className="text-gray-500 border-b border-gray-700">
              <th className="text-left py-1 px-2">Clase</th>
              <th className="text-left py-1 px-2">Confianza</th>
              <th className="text-left py-1 px-2">Clasificación</th>
              <th className="text-left py-1 px-2">Timestamp</th>
              <th className="text-left py-1 px-2">Acción</th>
            </tr>
          </thead>
          <tbody>
            {filtered.map(d => (
              <tr key={d.id} className="border-b border-gray-800 hover:bg-gray-800/50">
                <td className="py-1 px-2 text-green-400">{d.class_name}</td>
                <td className="py-1 px-2">
                  <div className="flex items-center gap-1">
                    <div className="w-16 h-1.5 bg-gray-700 rounded overflow-hidden">
                      <div className="h-full bg-green-500 rounded" style={{ width: `${d.confidence * 100}%` }} />
                    </div>
                    <span className="text-gray-400">{(d.confidence * 100).toFixed(0)}%</span>
                  </div>
                </td>
                <td className="py-1 px-2">
                  <span className={`px-1.5 py-0.5 rounded text-[9px] ${
                    d.classification === "hostile" ? "bg-red-900/40 text-red-400" :
                    d.classification === "friendly" ? "bg-green-900/40 text-green-400" :
                    "bg-gray-700 text-gray-400"
                  }`}>
                    {d.classification}
                  </span>
                </td>
                <td className="py-1 px-2 text-gray-500">{new Date(d.timestamp).toISOString().slice(11, 19)}Z</td>
                <td className="py-1 px-2">
                  {d.lat !== undefined && d.lon !== undefined && (
                    <button
                      onClick={() => centerMap(d.lat, d.lon)}
                      className="flex items-center gap-1 text-blue-400 hover:text-blue-300 transition-colors"
                    >
                      <MapPin size={10} />
                      Ver en mapa
                    </button>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

const trackSourceColors: Record<string, string> = {
  satellite: "text-purple-400",
  drone: "text-cyan-400",
  radar: "text-yellow-400",
  sigint: "text-orange-400",
};

function TracksTab() {
  const { tracks, loading, error } = useMavenStore();

  if (error) {
    return (
      <div className="bg-red-900/20 border border-red-800 rounded p-3">
        <div className="flex items-center gap-1 text-red-400 text-xs font-mono">
          <AlertTriangle size={12} />
          Backend de fusión no disponible: {error}
        </div>
      </div>
    );
  }

  if (loading && tracks.length === 0) {
    return (
      <div className="text-center py-8">
        <Loader2 size={16} className="animate-spin text-green-400 mx-auto mb-2" />
        <div className="text-xs font-mono text-gray-500">Cargando tracks fusionados...</div>
      </div>
    );
  }

  if (!loading && tracks.length === 0) {
    return (
      <div className="bg-gray-900 rounded border border-gray-700 p-6 text-center">
        <Route size={24} className="text-gray-700 mx-auto mb-2" />
        <div className="text-xs font-mono text-gray-600">Sin tracks fusionados. Espere datos del FusionEngine.</div>
      </div>
    );
  }

  const sorted = [...tracks].sort((a, b) => new Date(b.last_seen).getTime() - new Date(a.last_seen).getTime());

  return (
    <div className="space-y-2">
      <div className="flex items-center gap-2 text-[10px] font-mono text-gray-500">
        <span className="flex items-center gap-1"><span className="w-2 h-2 rounded-full bg-purple-400" /> Satélite</span>
        <span className="flex items-center gap-1"><span className="w-2 h-2 rounded-full bg-cyan-400" /> Dron</span>
        <span className="flex items-center gap-1"><span className="w-2 h-2 rounded-full bg-yellow-400" /> Radar</span>
        <span className="flex items-center gap-1"><span className="w-2 h-2 rounded-full bg-orange-400" /> SIGINT</span>
        <span className="ml-auto">{tracks.length} tracks activos</span>
      </div>
      <div className="overflow-x-auto">
        <table className="w-full text-xs font-mono">
          <thead>
            <tr className="text-gray-500 border-b border-gray-700">
              <th className="text-left py-1 px-2">Track ID</th>
              <th className="text-left py-1 px-2">Origen</th>
              <th className="text-left py-1 px-2">Posición</th>
              <th className="text-left py-1 px-2">Clasificación</th>
              <th className="text-left py-1 px-2">Confianza</th>
              <th className="text-left py-1 px-2">Último contacto</th>
            </tr>
          </thead>
          <tbody>
            {sorted.map(t => (
              <tr key={t.track_id} className="border-b border-gray-800 hover:bg-gray-800/50">
                <td className="py-1 px-2 text-gray-300">{t.track_id}</td>
                <td className={`py-1 px-2 ${trackSourceColors[t.source] || "text-gray-400"}`}>
                  {t.source.toUpperCase()}
                </td>
                <td className="py-1 px-2 text-gray-400">
                  {t.position[0].toFixed(4)}°N, {t.position[1].toFixed(4)}°E
                </td>
                <td className="py-1 px-2">
                  <span className={`px-1.5 py-0.5 rounded text-[9px] ${
                    t.classification === "hostile" ? "bg-red-900/40 text-red-400" :
                    t.classification === "friendly" ? "bg-green-900/40 text-green-400" :
                    "bg-gray-700 text-gray-400"
                  }`}>
                    {t.classification}
                  </span>
                </td>
                <td className="py-1 px-2">
                  <div className="flex items-center gap-1">
                    <div className="w-12 h-1.5 bg-gray-700 rounded overflow-hidden">
                      <div className="h-full bg-green-500 rounded" style={{ width: `${t.confidence * 100}%` }} />
                    </div>
                    <span className="text-gray-400">{(t.confidence * 100).toFixed(0)}%</span>
                  </div>
                </td>
                <td className="py-1 px-2 text-gray-500">
                  {new Date(t.last_seen).toISOString().slice(11, 19)}Z
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

function RiskBadge({ level }: { level: string }) {
  const colors: Record<string, string> = {
    critical: "bg-red-900/40 text-red-400 border-red-800",
    high: "bg-orange-900/40 text-orange-400 border-orange-800",
    medium: "bg-yellow-900/40 text-yellow-400 border-yellow-800",
    low: "bg-green-900/40 text-green-400 border-green-800",
  };
  return (
    <span className={`text-[10px] font-mono px-1.5 py-0.5 rounded border ${colors[level] || "bg-gray-700 text-gray-400 border-gray-600"}`}>
      {level.toUpperCase()}
    </span>
  );
}

function COATab() {
  const { coas, selectedCOA, loading, error, generateCOA, selectCOA } = useMavenStore();
  const [missionParams, setMissionParams] = useState({
    objective_lat: 40.4168,
    objective_lon: -3.7038,
    time_window_start: "",
    time_window_end: "",
    forces: [] as string[],
  });
  const [availableForces] = useState([
    { id: "inf-1", label: "Infantería Mecanizada - BriG I" },
    { id: "arm-1", label: "Blindados - BriG II" },
    { id: "rec-1", label: "Reconocimiento - Escuadrón Alfa" },
    { id: "art-1", label: "Artillería - Grupo Fuego" },
    { id: "log-1", label: "Logística - Batallón Apoyo" },
    { id: "drone-1", label: "Drones - Escuadrón UAV" },
  ]);

  const toggleForce = (id: string) => {
    setMissionParams(prev => ({
      ...prev,
      forces: prev.forces.includes(id)
        ? prev.forces.filter(f => f !== id)
        : [...prev.forces, id],
    }));
  };

  const handleGenerate = () => {
    if (!missionParams.time_window_start || !missionParams.time_window_end) return;
    generateCOA({
      objective_lat: missionParams.objective_lat,
      objective_lon: missionParams.objective_lon,
      forces: missionParams.forces,
      time_window_start: missionParams.time_window_start,
      time_window_end: missionParams.time_window_end,
    });
  };

  return (
    <div className="space-y-3">
      <div className="bg-gray-900 rounded border border-gray-700 p-3">
        <div className="text-xs font-bold text-gray-400 mb-2">FORMULARIO DE MISIÓN</div>
        <div className="grid grid-cols-2 gap-2 mb-2">
          <div>
            <label className="text-[10px] font-mono text-gray-500 block mb-0.5">Latitud objetivo</label>
            <input
              type="number"
              step="any"
              value={missionParams.objective_lat}
              onChange={e => setMissionParams(p => ({ ...p, objective_lat: Number(e.target.value) }))}
              className="w-full bg-gray-800 border border-gray-700 rounded px-2 py-1 text-xs font-mono text-gray-200 focus:outline-none focus:border-green-700"
            />
          </div>
          <div>
            <label className="text-[10px] font-mono text-gray-500 block mb-0.5">Longitud objetivo</label>
            <input
              type="number"
              step="any"
              value={missionParams.objective_lon}
              onChange={e => setMissionParams(p => ({ ...p, objective_lon: Number(e.target.value) }))}
              className="w-full bg-gray-800 border border-gray-700 rounded px-2 py-1 text-xs font-mono text-gray-200 focus:outline-none focus:border-green-700"
            />
          </div>
          <div>
            <label className="text-[10px] font-mono text-gray-500 block mb-0.5">Ventana inicio</label>
            <input
              type="datetime-local"
              value={missionParams.time_window_start}
              onChange={e => setMissionParams(p => ({ ...p, time_window_start: e.target.value }))}
              className="w-full bg-gray-800 border border-gray-700 rounded px-2 py-1 text-xs font-mono text-gray-200 focus:outline-none focus:border-green-700"
            />
          </div>
          <div>
            <label className="text-[10px] font-mono text-gray-500 block mb-0.5">Ventana fin</label>
            <input
              type="datetime-local"
              value={missionParams.time_window_end}
              onChange={e => setMissionParams(p => ({ ...p, time_window_end: e.target.value }))}
              className="w-full bg-gray-800 border border-gray-700 rounded px-2 py-1 text-xs font-mono text-gray-200 focus:outline-none focus:border-green-700"
            />
          </div>
        </div>
        <div className="mb-2">
          <label className="text-[10px] font-mono text-gray-500 block mb-0.5">Fuerzas disponibles</label>
          <div className="flex flex-wrap gap-1">
            {availableForces.map(f => (
              <button
                key={f.id}
                onClick={() => toggleForce(f.id)}
                className={`text-[10px] font-mono px-2 py-0.5 rounded border transition-colors ${
                  missionParams.forces.includes(f.id)
                    ? "bg-green-900/30 text-green-400 border-green-700"
                    : "bg-gray-800 text-gray-500 border-gray-700 hover:text-gray-300"
                }`}
              >
                {f.label}
              </button>
            ))}
          </div>
        </div>
        <button
          onClick={handleGenerate}
          disabled={loading || !missionParams.time_window_start || !missionParams.time_window_end}
          className="flex items-center gap-1 bg-green-900/30 text-green-400 border border-green-700 rounded px-3 py-1.5 text-xs font-mono hover:bg-green-900/50 disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
        >
          {loading ? <Loader2 size={12} className="animate-spin" /> : <ClipboardCheck size={12} />}
          Generar Cursos de Acción
        </button>
      </div>

      {error && (
        <div className="bg-red-900/20 border border-red-800 rounded p-3">
          <div className="flex items-center gap-1 text-red-400 text-xs font-mono">
            <AlertTriangle size={12} />
            Backend COA no disponible: {error}
          </div>
        </div>
      )}

      {!error && !loading && coas.length === 0 && (
        <div className="bg-gray-900 rounded border border-gray-700 p-6 text-center">
          <ClipboardCheck size={24} className="text-gray-700 mx-auto mb-2" />
          <div className="text-xs font-mono text-gray-600">Configure la misión y genere cursos de acción.</div>
        </div>
      )}

      {loading && coas.length === 0 && (
        <div className="text-center py-4">
          <Loader2 size={16} className="animate-spin text-green-400 mx-auto mb-2" />
          <div className="text-xs font-mono text-gray-500">Generando cursos de acción...</div>
        </div>
      )}

      {coas.length > 0 && (
        <div className="grid grid-cols-2 gap-2">
          {coas.map(coa => (
            <button
              key={coa.id}
              onClick={() => selectCOA(coa.id)}
              className={`text-left bg-gray-900 rounded border p-3 transition-colors ${
                selectedCOA?.id === coa.id
                  ? "border-green-500 bg-green-900/20"
                  : "border-gray-700 hover:border-gray-600"
              }`}
            >
              <div className="flex items-center justify-between mb-1">
                <span className="text-xs font-bold text-green-400">{coa.name}</span>
                <RiskBadge level={coa.risk_level} />
              </div>
              <div className="flex items-center gap-1 mb-1">
                <div className="flex-1 h-2 bg-gray-700 rounded overflow-hidden">
                  <div className="h-full bg-green-500 rounded" style={{ width: `${coa.overall_score * 100}%` }} />
                </div>
                <span className="text-[10px] font-mono text-green-400">{(coa.overall_score * 100).toFixed(0)}%</span>
              </div>
              <div className="text-[10px] font-mono text-gray-500 space-y-0.5">
                <div>Readiness armas: {(coa.weapon_readiness * 100).toFixed(0)}%</div>
                <div>Duración: {coa.duration_h}h</div>
                <div>Bajas est.: {coa.estimated_casualties}</div>
              </div>
            </button>
          ))}
        </div>
      )}

      {selectedCOA && (
        <div className="bg-gray-900 rounded border border-green-700/50 p-3">
          <div className="text-xs font-bold text-green-400 mb-2">DETALLE COA: {selectedCOA.name}</div>
          <div className="text-[10px] font-mono text-gray-400 mb-2">{selectedCOA.description}</div>
          <div className="space-y-2">
            <div className="text-[10px] font-bold text-gray-500">FASES</div>
            {selectedCOA.phases.map((phase, i) => (
              <div key={i} className="bg-gray-800 rounded p-2 border border-gray-700">
                <div className="text-[10px] font-mono text-green-400">{phase.name}</div>
                <div className="text-[10px] font-mono text-gray-400">{phase.description}</div>
                <div className="text-[10px] font-mono text-gray-500">Duración: {phase.duration_h}h</div>
                {phase.waypoints.length > 0 && (
                  <div className="text-[10px] font-mono text-gray-600 mt-0.5">
                    Waypoints: {phase.waypoints.map(w => `${w[0].toFixed(3)}°N ${w[1].toFixed(3)}°E`).join(" → ")}
                  </div>
                )}
              </div>
            ))}
          </div>
          <div className="flex gap-2 mt-2">
            <button className="flex items-center gap-1 bg-orange-900/30 text-orange-400 border border-orange-700 rounded px-2 py-1 text-[10px] font-mono hover:bg-orange-900/50 transition-colors">
              Evaluar Riesgo
            </button>
            <button className="flex items-center gap-1 bg-blue-900/30 text-blue-400 border border-blue-700 rounded px-2 py-1 text-[10px] font-mono hover:bg-blue-900/50 transition-colors">
              Evaluar Armas
            </button>
          </div>
        </div>
      )}
    </div>
  );
}

export default function MavenPanel() {
  const [activeTab, setActiveTab] = useState<MavenTab>("satellite");

  return (
    <div className="flex flex-col h-full bg-[#0a0e17]">
      <div className="flex border-b border-gray-800">
        {tabs.map(tab => {
          const Icon = tab.icon;
          return (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`flex items-center gap-1.5 px-3 py-2 text-xs font-mono transition-colors border-b-2 ${
                activeTab === tab.id
                  ? "text-green-400 border-green-400 bg-green-900/10"
                  : "text-gray-500 border-transparent hover:text-gray-300 hover:bg-gray-900"
              }`}
            >
              <Icon size={14} />
              {tab.label}
            </button>
          );
        })}
      </div>
      <div className="flex-1 overflow-y-auto p-3">
        {activeTab === "satellite" && <SatelliteTab />}
        {activeTab === "detections" && <DetectionsTab />}
        {activeTab === "tracks" && <TracksTab />}
        {activeTab === "coa" && <COATab />}
      </div>
    </div>
  );
}
