"use client";
import dynamic from "next/dynamic";
import { useState, useMemo } from "react";
import {
  Brain, AlertTriangle, Route, ClipboardCheck, Satellite,
  ChevronLeft, ChevronRight, Layers,
} from "lucide-react";
import { useCOPStore } from "@/store/cop-store";
import { useMavenStore } from "@/store/maven-store";
import ClassificationBanner from "./ClassificationBanner";
import StatusBar from "./StatusBar";
import MissionClock from "./MissionClock";
import AlertTicker from "./AlertTicker";
import MavenPanel from "./MavenPanel";
import COAComparison from "./COAComparison";
import type { UnitPosition } from "@/lib/cop-types";
import type { Detection } from "@/lib/maven-types";

const TacticalMap = dynamic(() => import("./TacticalMap"), { ssr: false });

type SidebarTab = "intel" | "alerts" | "coa" | "fusion" | "maven";

const sidebarTabs: { id: SidebarTab; label: string; icon: typeof Brain }[] = [
  { id: "intel", label: "Intel", icon: Layers },
  { id: "alerts", label: "Alertas", icon: AlertTriangle },
  { id: "coa", label: "COA", icon: ClipboardCheck },
  { id: "fusion", label: "Fusión", icon: Route },
  { id: "maven", label: "Maven", icon: Satellite },
];

function DetectionMarker({ detection }: { detection: Detection }) {
  const color = detection.classification === "hostile"
    ? "bg-red-500" : detection.classification === "friendly"
    ? "bg-green-500" : "bg-yellow-500";
  return (
    <span
      className={`inline-block w-1.5 h-1.5 rounded-full ${color} animate-pulse`}
      title={`${detection.class_name} (${(detection.confidence * 100).toFixed(0)}%)`}
    />
  );
}

export default function COPUnified() {
  const { state } = useCOPStore();
  const { detections, tracks, coas } = useMavenStore();
  const [sidebarTab, setSidebarTab] = useState<SidebarTab>("intel");
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
  const [showTimeline, setShowTimeline] = useState(true);

  const recentEvents = useMemo(() => {
    const events: { type: string; label: string; timestamp: string; severity: string }[] = [];
    state.timeline.forEach(ev => events.push({
      type: "mission",
      label: ev.description,
      timestamp: ev.timestamp,
      severity: ev.severity,
    }));
    detections.forEach(d => events.push({
      type: "detection",
      label: `${d.class_name} detectado`,
      timestamp: d.timestamp,
      severity: d.classification === "hostile" ? "critical" : "medium",
    }));
    tracks.forEach(t => events.push({
      type: "track",
      label: `Track ${t.track_id} - ${t.source}`,
      timestamp: t.last_seen,
      severity: t.classification === "hostile" ? "high" : "low",
    }));
    events.sort((a, b) => new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime());
    return events.slice(0, 50);
  }, [state.timeline, detections, tracks]);

  const sidebarContent = () => {
    switch (sidebarTab) {
      case "intel":
        return (
          <div className="space-y-2">
            <div className="text-[10px] font-bold text-gray-400 mb-1">SENSORES</div>
            {state.sensors.length === 0 ? (
              <div className="text-[10px] font-mono text-gray-600">Sin sensores</div>
            ) : (
              state.sensors.map(s => (
                <div key={s.id} className="flex items-center justify-between text-[10px] font-mono">
                  <span className="text-gray-400">{s.type}</span>
                  <span className={s.status === "active" || s.status === "online" ? "text-green-400" : "text-red-400"}>
                    {s.status.toUpperCase()}
                  </span>
                </div>
              ))
            )}
            <div className="text-[10px] font-bold text-gray-400 mt-3 mb-1">UNIDADES</div>
            {state.units.length === 0 ? (
              <div className="text-[10px] font-mono text-gray-600">Sin unidades</div>
            ) : (
              state.units.map(u => (
                <div key={u.id} className="text-[10px] font-mono text-gray-400">
                  {u.name} <span className={u.status === "active" ? "text-green-400" : "text-yellow-400"}>({u.status})</span>
                </div>
              ))
            )}
            <div className="text-[10px] font-bold text-gray-400 mt-3 mb-1">DETECCIONES EN VIVO</div>
            {detections.length === 0 ? (
              <div className="text-[10px] font-mono text-gray-600">Sin detecciones CV</div>
            ) : (
              detections.map(d => (
                <div key={d.id} className="flex items-center gap-1 text-[10px] font-mono">
                  <DetectionMarker detection={d} />
                  <span className="text-gray-400">{d.class_name}</span>
                  <span className="text-gray-600">{(d.confidence * 100).toFixed(0)}%</span>
                </div>
              ))
            )}
          </div>
        );
      case "alerts":
        return (
          <div className="space-y-1">
            {state.alerts.length === 0 ? (
              <div className="text-[10px] font-mono text-gray-600">Sin alertas activas</div>
            ) : (
              state.alerts.map(a => (
                <div key={a.id} className={`text-[10px] font-mono p-1.5 rounded border ${
                  a.severity === "critical" ? "bg-red-900/20 border-red-800 text-red-400" :
                  a.severity === "high" ? "bg-orange-900/20 border-orange-800 text-orange-400" :
                  "bg-yellow-900/20 border-yellow-800 text-yellow-400"
                }`}>
                  <div className="font-bold">{a.source}</div>
                  <div>{a.message}</div>
                </div>
              ))
            )}
          </div>
        );
      case "coa":
        return (
          <div className="space-y-2">
            <div className="text-[10px] font-bold text-gray-400 mb-1">CURSOS DE ACCIÓN</div>
            {coas.length === 0 ? (
              <div className="text-[10px] font-mono text-gray-600">Sin COAs generados</div>
            ) : (
              coas.map(coa => (
                <div key={coa.id} className="bg-gray-800 rounded p-1.5 border border-gray-700">
                  <div className="text-[10px] font-mono text-green-400">{coa.name}</div>
                  <div className="flex items-center gap-1 mt-0.5">
                    <div className="flex-1 h-1 bg-gray-700 rounded overflow-hidden">
                      <div className="h-full bg-green-500 rounded" style={{ width: `${coa.overall_score * 100}%` }} />
                    </div>
                    <span className="text-[9px] font-mono text-green-400">{(coa.overall_score * 100).toFixed(0)}%</span>
                  </div>
                </div>
              ))
            )}
            {coas.length > 1 && <COAComparison />}
          </div>
        );
      case "fusion":
        return (
          <div className="space-y-2">
            <div className="text-[10px] font-bold text-gray-400 mb-1">TRACKS FUSIONADOS</div>
            {tracks.length === 0 ? (
              <div className="text-[10px] font-mono text-gray-600">Sin tracks del FusionEngine</div>
            ) : (
              tracks.slice(0, 20).map(t => (
                <div key={t.track_id} className="flex items-center justify-between text-[10px] font-mono border-b border-gray-800 py-0.5">
                  <span className="text-gray-300">{t.track_id}</span>
                  <span className="text-gray-500">{t.source.toUpperCase()}</span>
                  <span className={t.classification === "hostile" ? "text-red-400" : "text-green-400"}>
                    {t.classification}
                  </span>
                </div>
              ))
            )}
          </div>
        );
      case "maven":
        return <MavenPanel />;
      default:
        return null;
    }
  };

  return (
    <div className="min-h-screen bg-[#0a0e17] flex flex-col">
      <ClassificationBanner />
      <div className="flex justify-between items-center px-4 py-1 bg-gray-950 border-b border-gray-800">
        <span className="text-green-400 font-bold text-sm tracking-wider">SESIS-FEDERATION MAVEN FUSION</span>
        <MissionClock />
      </div>
      <StatusBar />

      <div className="flex-1 flex min-h-0">
        <div className={`${sidebarCollapsed ? "w-10" : "w-64"} bg-gray-950 border-r border-gray-800 flex flex-col transition-all duration-150`}>
          <button
            onClick={() => setSidebarCollapsed(!sidebarCollapsed)}
            className="p-2 text-gray-500 hover:text-gray-300 border-b border-gray-800 transition-colors"
          >
            {sidebarCollapsed ? <ChevronRight size={14} /> : <ChevronLeft size={14} />}
          </button>
          <div className="flex border-b border-gray-800">
            {sidebarTabs.map(tab => {
              const Icon = tab.icon;
              return (
                <button
                  key={tab.id}
                  onClick={() => setSidebarTab(tab.id)}
                  className={`flex-1 flex items-center justify-center gap-1 px-1 py-1.5 text-[10px] font-mono transition-colors border-b-2 ${
                    sidebarTab === tab.id
                      ? "text-green-400 border-green-400 bg-green-900/10"
                      : "text-gray-500 border-transparent hover:text-gray-300"
                  }`}
                >
                  <Icon size={12} />
                  {!sidebarCollapsed && tab.label}
                </button>
              );
            })}
          </div>
          <div className="flex-1 overflow-y-auto p-2">
            {!sidebarCollapsed && sidebarContent()}
          </div>
        </div>

        <div className="flex-1 flex flex-col min-h-0">
          <div className="flex-1 relative">
            <div className="absolute inset-0" id="cop-map">
              <TacticalMap units={state.units as UnitPosition[]} />
            </div>
            <div className="absolute top-2 right-2 z-[1000] space-y-1">
              <div className="bg-gray-900/90 border border-gray-700 rounded p-2 text-[10px] font-mono">
                <div className="text-gray-500">MAP OVERLAY</div>
                <div className="text-green-400">{state.units.length} unidades</div>
                <div className="text-red-400">{tracks.filter(t => t.classification === "hostile").length} tracks hostiles</div>
                <div className="text-yellow-400">{detections.length} detecciones CV</div>
              </div>
            </div>
          </div>

          {showTimeline && (
            <div className="border-t border-gray-800 bg-gray-950">
              <div className="flex items-center justify-between px-2 py-1">
                <span className="text-[10px] font-bold text-gray-500">TIMELINE FUSIONADO</span>
                <button onClick={() => setShowTimeline(false)} className="text-gray-600 hover:text-gray-400 text-[10px]">ocultar</button>
              </div>
              <div className="flex gap-1 px-2 pb-2 overflow-x-auto" style={{ maxHeight: "80px" }}>
                {recentEvents.length === 0 && (
                  <span className="text-[10px] font-mono text-gray-600">Sin eventos fusionados</span>
                )}
                {recentEvents.map((ev, i) => (
                  <div
                    key={i}
                    className="flex-shrink-0 bg-gray-900 border border-gray-800 rounded px-2 py-1 text-[9px] font-mono"
                  >
                    <div className={`${
                      ev.severity === "critical" || ev.severity === "high" ? "text-red-400" :
                      ev.severity === "warning" || ev.severity === "medium" ? "text-yellow-400" :
                      "text-green-400"
                    }`}>
                      {new Date(ev.timestamp).toISOString().slice(11, 19)}Z
                    </div>
                    <div className="text-gray-400 truncate max-w-[120px]">{ev.label}</div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>

      <div className="border-t border-gray-800 p-2 bg-gray-950">
        <AlertTicker />
      </div>
    </div>
  );
}
