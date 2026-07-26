"use client";
import { useState } from "react";
import { Clock, Target, BookOpen, Lightbulb, BarChart3, Play, CheckCircle, XCircle, MinusCircle, Circle, Plus, FolderOpen, Flag } from "lucide-react";
import { useCOPStore } from "@/store/cop-store";
import { apiFetch, apiErrorMessage } from "@/lib/api";
import { mapAAR, type BackendAAR } from "@/lib/mappers";

const objStatusIcons: Record<string, typeof CheckCircle> = {
  ACHIEVED: CheckCircle,
  PARTIAL: MinusCircle,
  FAILED: XCircle,
  PENDING: Circle,
};

const objStatusColors: Record<string, string> = {
  ACHIEVED: "text-green-400",
  PARTIAL: "text-yellow-400",
  FAILED: "text-red-400",
  PENDING: "text-gray-500",
};

interface ReplayEvent {
  timestamp: string
  type: string
  description: string
  actor: string
}

interface ReplayResponse {
  aar_id: string
  operation_name: string
  total_events: number
  events: ReplayEvent[]
}

export default function AARPanel() {
  const { aar, setAAR, updateAAR } = useCOPStore();
  const [newLesson, setNewLesson] = useState("");
  const [newLessonCategory, setNewLessonCategory] = useState("TACTICAL");
  const [newRecommendation, setNewRecommendation] = useState("");
  const [isReplaying, setIsReplaying] = useState(false);
  const [replayEvents, setReplayEvents] = useState<ReplayEvent[] | null>(null);
  const [replayIndex, setReplayIndex] = useState(0);
  const [loadId, setLoadId] = useState("");
  const [operationId, setOperationId] = useState("");
  const [operationName, setOperationName] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleCreate = async () => {
    if (!operationId.trim() || !operationName.trim()) return;
    setBusy(true);
    setError(null);
    try {
      const result = await apiFetch<BackendAAR>("/api/v1/aar/create", {
        method: "POST",
        body: {
          operation_id: operationId.trim(),
          operation_name: operationName.trim(),
          start_time: new Date().toISOString(),
          created_by: "OPERATOR",
        },
      });
      setAAR(mapAAR(result));
    } catch (e) {
      setError(apiErrorMessage(e));
    } finally {
      setBusy(false);
    }
  };

  const handleLoad = async () => {
    if (!loadId.trim()) return;
    setBusy(true);
    setError(null);
    try {
      const result = await apiFetch<BackendAAR>(`/api/v1/aar/${encodeURIComponent(loadId.trim())}`);
      setAAR(mapAAR(result));
    } catch (e) {
      setError(apiErrorMessage(e));
    } finally {
      setBusy(false);
    }
  };

  const addLesson = async () => {
    if (!newLesson.trim() || !aar) return;
    setBusy(true);
    setError(null);
    try {
      await apiFetch(`/api/v1/aar/${aar.id}/lessons`, {
        method: "POST",
        body: { category: newLessonCategory, observation: newLesson, priority: "MEDIUM" },
      });
      const refreshed = await apiFetch<BackendAAR>(`/api/v1/aar/${aar.id}`);
      setAAR(mapAAR(refreshed));
      setNewLesson("");
    } catch (e) {
      setError(apiErrorMessage(e));
    } finally {
      setBusy(false);
    }
  };

  const addRecommendation = () => {
    if (!newRecommendation.trim() || !aar) return;
    updateAAR({ recommendations: [...aar.recommendations, newRecommendation] });
    setNewRecommendation("");
  };

  const finalize = async () => {
    if (!aar) return;
    setBusy(true);
    setError(null);
    try {
      await apiFetch(`/api/v1/aar/${aar.id}/finalize`, {
        method: "POST",
        body: {
          recommendations: aar.recommendations.map(r => ({ recommendation: r })),
        },
      });
      const refreshed = await apiFetch<BackendAAR>(`/api/v1/aar/${aar.id}`);
      setAAR(mapAAR(refreshed));
    } catch (e) {
      setError(apiErrorMessage(e));
    } finally {
      setBusy(false);
    }
  };

  const startReplay = async () => {
    if (!aar || isReplaying) return;
    setError(null);
    try {
      const replay = await apiFetch<ReplayResponse>(`/api/v1/aar/${aar.id}/replay`);
      if (replay.events.length === 0) return;
      setReplayEvents(replay.events);
      setIsReplaying(true);
      setReplayIndex(0);
      const interval = setInterval(() => {
        setReplayIndex(prev => {
          if (prev >= replay.events.length - 1) {
            clearInterval(interval);
            setIsReplaying(false);
            return prev;
          }
          return prev + 1;
        });
      }, 1500);
    } catch (e) {
      setError(apiErrorMessage(e));
    }
  };

  if (!aar) {
    return (
      <div className="bg-gray-900 rounded border border-gray-700 flex flex-col h-full">
        <div className="flex items-center gap-2 px-3 py-2 border-b border-gray-700">
          <Clock size={14} className="text-green-400" />
          <span className="text-xs font-bold text-gray-400">AAR — AFTER ACTION REVIEW</span>
        </div>
        <div className="flex-1 overflow-y-auto p-3 space-y-3">
          <div className="text-xs font-mono text-gray-600">No hay ninguna AAR cargada.</div>
          <div className="space-y-1">
            <div className="text-[10px] text-gray-500 font-bold">CREAR NUEVA AAR</div>
            <input
              value={operationId}
              onChange={e => setOperationId(e.target.value)}
              placeholder="ID de operacion"
              className="w-full bg-gray-800 text-gray-300 text-xs rounded px-2 py-1 border border-gray-700"
            />
            <input
              value={operationName}
              onChange={e => setOperationName(e.target.value)}
              placeholder="Nombre de operacion"
              className="w-full bg-gray-800 text-gray-300 text-xs rounded px-2 py-1 border border-gray-700"
            />
            <button
              onClick={() => void handleCreate()}
              disabled={busy || !operationId.trim() || !operationName.trim()}
              className="w-full bg-green-800 hover:bg-green-700 disabled:opacity-50 text-green-100 text-[10px] px-2 py-1 rounded flex items-center justify-center gap-1 transition-colors"
            >
              <Plus size={10} /> Crear AAR
            </button>
          </div>
          <div className="space-y-1">
            <div className="text-[10px] text-gray-500 font-bold">CARGAR AAR EXISTENTE</div>
            <div className="flex gap-1">
              <input
                value={loadId}
                onChange={e => setLoadId(e.target.value)}
                placeholder="ID de AAR"
                className="flex-1 bg-gray-800 text-gray-300 text-xs rounded px-2 py-1 border border-gray-700"
              />
              <button
                onClick={() => void handleLoad()}
                disabled={busy || !loadId.trim()}
                className="bg-gray-800 hover:bg-gray-700 disabled:opacity-50 text-gray-300 text-[10px] px-2 py-1 rounded border border-gray-700 flex items-center gap-1 transition-colors"
              >
                <FolderOpen size={10} /> Cargar
              </button>
            </div>
          </div>
          {error && <div className="text-[10px] font-mono text-red-400">{error}</div>}
        </div>
      </div>
    );
  }

  const achievedCount = aar.objectives.filter(o => o.status === "ACHIEVED").length;
  const totalObjectives = aar.objectives.length;
  const successRate = totalObjectives > 0 ? Math.round((achievedCount / totalObjectives) * 100) : 0;
  const durationH = aar.endTime
    ? Math.round((new Date(aar.endTime).getTime() - new Date(aar.startTime).getTime()) / 3600000)
    : null;

  const timelineSource: { id: string; timestamp: string; type: string; description: string; actor: string }[] =
    replayEvents !== null
      ? replayEvents.map((e, i) => ({ id: `rp${i}`, ...e }))
      : aar.timeline;

  return (
    <div className="bg-gray-900 rounded border border-gray-700 flex flex-col h-full">
      <div className="flex items-center gap-2 px-3 py-2 border-b border-gray-700">
        <Clock size={14} className="text-green-400" />
        <span className="text-xs font-bold text-gray-400">AAR — {aar.operationName}</span>
        <span className={`ml-auto text-[10px] px-1.5 py-0.5 rounded ${
          aar.status === "FINALIZED" ? "bg-green-900/30 text-green-400" : "bg-yellow-900/30 text-yellow-400"
        }`}>
          {aar.status}
        </span>
        {aar.status !== "FINALIZED" && (
          <button
            onClick={() => void finalize()}
            disabled={busy}
            className="text-[10px] text-green-400 hover:text-green-300 flex items-center gap-0.5 disabled:opacity-50"
          >
            <Flag size={10} /> Finalizar
          </button>
        )}
      </div>

      <div className="flex-1 overflow-y-auto p-2 space-y-3">
        {error && <div className="text-[10px] font-mono text-red-400">{error}</div>}

        <div className="grid grid-cols-3 gap-2">
          <div className="bg-gray-800 rounded p-2 text-center">
            <div className="text-[10px] text-gray-500">Tasa Exito</div>
            <div className={`text-lg font-bold ${successRate >= 70 ? "text-green-400" : successRate >= 40 ? "text-yellow-400" : "text-red-400"}`}>
              {totalObjectives > 0 ? `${successRate}%` : "—"}
            </div>
          </div>
          <div className="bg-gray-800 rounded p-2 text-center">
            <div className="text-[10px] text-gray-500">Duracion</div>
            <div className="text-lg font-bold text-gray-300">
              {durationH !== null ? `${durationH}h` : "En curso"}
            </div>
          </div>
          <div className="bg-gray-800 rounded p-2 text-center">
            <div className="text-[10px] text-gray-500">Eventos</div>
            <div className="text-lg font-bold text-gray-300">{aar.timeline.length}</div>
          </div>
        </div>

        <div>
          <div className="flex items-center gap-1 mb-1">
            <Target size={12} className="text-gray-400" />
            <span className="text-[10px] font-bold text-gray-400">OBJETIVOS</span>
            <span className="text-[10px] text-gray-600 ml-auto">{achievedCount}/{totalObjectives}</span>
          </div>
          <div className="space-y-0.5">
            {aar.objectives.length === 0 && (
              <div className="text-[10px] font-mono text-gray-600">Sin objetivos registrados</div>
            )}
            {aar.objectives.map(obj => {
              const Icon = objStatusIcons[obj.status] || Circle;
              return (
                <div key={obj.id} className="flex items-center gap-1 text-[10px] font-mono">
                  <Icon size={10} className={objStatusColors[obj.status] ?? "text-gray-500"} />
                  <span className="text-gray-300">{obj.description}</span>
                </div>
              );
            })}
          </div>
        </div>

        <div>
          <div className="flex items-center gap-1 mb-1">
            <BarChart3 size={12} className="text-gray-400" />
            <span className="text-[10px] font-bold text-gray-400">LINEA TEMPORAL</span>
            <button
              onClick={() => void startReplay()}
              disabled={isReplaying}
              className="ml-auto text-[10px] text-green-400 hover:text-green-300 flex items-center gap-0.5 disabled:opacity-50"
            >
              <Play size={10} /> Replay
            </button>
          </div>
          <div className="space-y-0.5 border-l border-gray-700 ml-2 pl-2">
            {timelineSource.length === 0 && (
              <div className="text-[10px] font-mono text-gray-600">Sin eventos registrados</div>
            )}
            {timelineSource.map((ev, idx) => (
              <div
                key={ev.id}
                className={`text-[10px] font-mono py-0.5 transition-colors ${
                  isReplaying && idx <= replayIndex ? "text-gray-300" :
                  isReplaying ? "text-gray-700" : "text-gray-300"
                }`}
              >
                <span className="text-gray-600">
                  {ev.timestamp ? new Date(ev.timestamp).toISOString().slice(11, 16) : "--"}Z
                </span>
                <span className="text-cyan-400 ml-1">[{ev.actor}]</span>
                <span className="ml-1">{ev.description}</span>
              </div>
            ))}
          </div>
        </div>

        <div>
          <div className="flex items-center gap-1 mb-1">
            <BookOpen size={12} className="text-gray-400" />
            <span className="text-[10px] font-bold text-gray-400">LECCIONES APRENDIDAS</span>
          </div>
          <div className="space-y-0.5">
            {aar.lessonsLearned.length === 0 && (
              <div className="text-[10px] font-mono text-gray-600">Sin lecciones registradas</div>
            )}
            {aar.lessonsLearned.map(ll => (
              <div key={ll.id} className="text-[10px] font-mono text-gray-300 flex gap-1">
                <span className={`px-1 py-0.5 rounded text-[9px] ${
                  ll.impact === "HIGH" ? "bg-red-900/30 text-red-400" :
                  ll.impact === "MEDIUM" ? "bg-yellow-900/30 text-yellow-400" :
                  "bg-gray-800 text-gray-400"
                }`}>
                  {ll.category}
                </span>
                {ll.description}
              </div>
            ))}
          </div>
          <div className="flex gap-1 mt-1">
            <select
              value={newLessonCategory}
              onChange={e => setNewLessonCategory(e.target.value)}
              className="bg-gray-800 text-gray-300 text-[10px] rounded px-1 py-0.5 border border-gray-700"
            >
              <option value="TACTICAL">TACTICA</option>
              <option value="COMMS">COMMS</option>
              <option value="LOGISTICS">LOG</option>
              <option value="MOVEMENT">MOV</option>
            </select>
            <input
              value={newLesson}
              onChange={e => setNewLesson(e.target.value)}
              placeholder="Nueva leccion..."
              className="flex-1 bg-gray-800 text-gray-300 text-[10px] rounded px-2 py-0.5 border border-gray-700"
            />
            <button
              onClick={() => void addLesson()}
              disabled={busy}
              className="text-[10px] text-green-400 hover:text-green-300 px-1 disabled:opacity-50"
            >
              +
            </button>
          </div>
        </div>

        <div>
          <div className="flex items-center gap-1 mb-1">
            <Lightbulb size={12} className="text-gray-400" />
            <span className="text-[10px] font-bold text-gray-400">RECOMENDACIONES</span>
          </div>
          <div className="space-y-0.5">
            {aar.recommendations.length === 0 && (
              <div className="text-[10px] font-mono text-gray-600">Sin recomendaciones</div>
            )}
            {aar.recommendations.map((r, i) => (
              <div key={i} className="text-[10px] font-mono text-gray-300 flex gap-1">
                <span className="text-green-400">→</span> {r}
              </div>
            ))}
          </div>
          <div className="flex gap-1 mt-1">
            <input
              value={newRecommendation}
              onChange={e => setNewRecommendation(e.target.value)}
              placeholder="Nueva recomendacion..."
              className="flex-1 bg-gray-800 text-gray-300 text-[10px] rounded px-2 py-0.5 border border-gray-700"
            />
            <button
              onClick={addRecommendation}
              className="text-[10px] text-green-400 hover:text-green-300 px-1"
            >
              +
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
