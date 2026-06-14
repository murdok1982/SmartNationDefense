"use client";
import { useState } from "react";
import { Clock, Target, BookOpen, Lightbulb, BarChart3, Play, CheckCircle, XCircle, MinusCircle, Circle } from "lucide-react";
import { useCOPStore } from "@/store/cop-store";

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

export default function AARPanel() {
  const { aar, updateAAR } = useCOPStore();
  const [newLesson, setNewLesson] = useState("");
  const [newLessonCategory, setNewLessonCategory] = useState("TACTICA");
  const [newRecommendation, setNewRecommendation] = useState("");
  const [isReplaying, setIsReplaying] = useState(false);
  const [replayIndex, setReplayIndex] = useState(0);

  const achievedCount = aar.objectives.filter(o => o.status === "ACHIEVED").length;
  const totalObjectives = aar.objectives.length;
  const successRate = totalObjectives > 0 ? Math.round((achievedCount / totalObjectives) * 100) : 0;

  const addLesson = () => {
    if (!newLesson.trim()) return;
    updateAAR({
      lessonsLearned: [...aar.lessonsLearned, {
        id: `ll${Date.now()}`,
        category: newLessonCategory,
        description: newLesson,
        impact: "MEDIUM",
      }],
    });
    setNewLesson("");
  };

  const addRecommendation = () => {
    if (!newRecommendation.trim()) return;
    updateAAR({
      recommendations: [...aar.recommendations, newRecommendation],
    });
    setNewRecommendation("");
  };

  const startReplay = () => {
    setIsReplaying(true);
    setReplayIndex(0);
    const interval = setInterval(() => {
      setReplayIndex(prev => {
        if (prev >= aar.timeline.length - 1) {
          clearInterval(interval);
          setIsReplaying(false);
          return prev;
        }
        return prev + 1;
      });
    }, 1500);
  };

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
      </div>

      <div className="flex-1 overflow-y-auto p-2 space-y-3">
        <div className="grid grid-cols-3 gap-2">
          <div className="bg-gray-800 rounded p-2 text-center">
            <div className="text-[10px] text-gray-500">Tasa Exito</div>
            <div className={`text-lg font-bold ${successRate >= 70 ? "text-green-400" : successRate >= 40 ? "text-yellow-400" : "text-red-400"}`}>
              {successRate}%
            </div>
          </div>
          <div className="bg-gray-800 rounded p-2 text-center">
            <div className="text-[10px] text-gray-500">Duracion</div>
            <div className="text-lg font-bold text-gray-300">
              {Math.round((new Date(aar.endTime).getTime() - new Date(aar.startTime).getTime()) / 3600000)}h
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
            {aar.objectives.map(obj => {
              const Icon = objStatusIcons[obj.status] || Circle;
              return (
                <div key={obj.id} className="flex items-center gap-1 text-[10px] font-mono">
                  <Icon size={10} className={objStatusColors[obj.status]} />
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
              onClick={startReplay}
              disabled={isReplaying}
              className="ml-auto text-[10px] text-green-400 hover:text-green-300 flex items-center gap-0.5 disabled:opacity-50"
            >
              <Play size={10} /> Replay
            </button>
          </div>
          <div className="space-y-0.5 border-l border-gray-700 ml-2 pl-2">
            {aar.timeline.map((ev, idx) => (
              <div
                key={ev.id}
                className={`text-[10px] font-mono py-0.5 transition-colors ${
                  isReplaying && idx <= replayIndex ? "text-gray-300" :
                  isReplaying ? "text-gray-700" : "text-gray-300"
                }`}
              >
                <span className="text-gray-600">
                  {new Date(ev.timestamp).toISOString().slice(11, 16)}Z
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
              <option value="TACTICA">TACTICA</option>
              <option value="COMMS">COMMS</option>
              <option value="LOGISTICA">LOG</option>
              <option value="MOVEMENT">MOV</option>
            </select>
            <input
              value={newLesson}
              onChange={e => setNewLesson(e.target.value)}
              placeholder="Nueva leccion..."
              className="flex-1 bg-gray-800 text-gray-300 text-[10px] rounded px-2 py-0.5 border border-gray-700"
            />
            <button
              onClick={addLesson}
              className="text-[10px] text-green-400 hover:text-green-300 px-1"
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
