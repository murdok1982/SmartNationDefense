"use client";
import dynamic from "next/dynamic";
import { useState } from "react";
import { useCOPStore } from "@/store/cop-store";
import ClassificationBanner from "./ClassificationBanner";
import StatusBar from "./StatusBar";
import MissionClock from "./MissionClock";
import AlertTicker from "./AlertTicker";
import IntelFeed from "./IntelFeed";
import ThreatPanel from "./ThreatPanel";
import CommandInput from "./CommandInput";
import QuickActions from "./QuickActions";
import MessagingPanel from "./MessagingPanel";
import TerrainAnalysis from "./TerrainAnalysis";
import LogisticsPanel from "./LogisticsPanel";
import AARPanel from "./AARPanel";
import ReportsPanel from "./ReportsPanel";
import ThreatPrediction from "./ThreatPrediction";
import PlanningPanel from "./PlanningPanel";
import VoiceCommand from "./VoiceCommand";
import TacticalMapEnhanced from "./TacticalMapEnhanced";
import MultiMonitor from "./MultiMonitor";
import {
  Map, MessageSquare, Mountain, Package, Clock, FileText,
  Target, Mic, Layers, Layout, ChevronLeft, ChevronRight,
} from "lucide-react";
import type { UnitPosition } from "@/lib/cop-types";

const TacticalMap = dynamic(() => import("./TacticalMap"), { ssr: false });

type PanelId = "overview" | "messages" | "terrain" | "logistics" | "aar" | "reports" | "threat-pred" | "planning" | "voice" | "map-enhanced" | "multi-monitor";

const panels: { id: PanelId; label: string; icon: typeof Map }[] = [
  { id: "overview", label: "Vista General", icon: Map },
  { id: "map-enhanced", label: "Mapa Avanzado", icon: Layers },
  { id: "messages", label: "Mensajeria", icon: MessageSquare },
  { id: "terrain", label: "Terreno", icon: Mountain },
  { id: "logistics", label: "Logistica", icon: Package },
  { id: "reports", label: "Reportes", icon: FileText },
  { id: "threat-pred", label: "Amenazas", icon: Target },
  { id: "planning", label: "Planificacion", icon: Target },
  { id: "aar", label: "AAR", icon: Clock },
  { id: "voice", label: "Voz", icon: Mic },
  { id: "multi-monitor", label: "Multi-Monitor", icon: Layout },
];

export default function COPPage() {
  const { state } = useCOPStore();
  const [activePanel, setActivePanel] = useState<PanelId>("overview");
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);

  const renderPanel = () => {
    switch (activePanel) {
      case "overview": return null;
      case "map-enhanced": return <TacticalMapEnhanced />;
      case "messages": return <MessagingPanel />;
      case "terrain": return <TerrainAnalysis />;
      case "logistics": return <LogisticsPanel />;
      case "aar": return <AARPanel />;
      case "reports": return <ReportsPanel />;
      case "threat-pred": return <ThreatPrediction />;
      case "planning": return <PlanningPanel />;
      case "voice": return <VoiceCommand />;
      case "multi-monitor": return <MultiMonitor />;
      default: return null;
    }
  };

  return (
    <div className="min-h-screen bg-[#0a0e17] flex flex-col">
      <ClassificationBanner />
      <div className="flex justify-between items-center px-4 py-1 bg-gray-950 border-b border-gray-800">
        <span className="text-green-400 font-bold text-sm tracking-wider">SESIS-FEDERATION COP</span>
        <div className="flex items-center gap-3">
          <span className="text-[10px] text-gray-500 font-mono">
            PANEL: <span className="text-green-400">{panels.find(p => p.id === activePanel)?.label}</span>
          </span>
          <MissionClock />
        </div>
      </div>
      <StatusBar />

      <div className="flex-1 flex min-h-0">
        <div className={`${sidebarCollapsed ? "w-10" : "w-32"} bg-gray-950 border-r border-gray-800 flex flex-col transition-all`}>
          <button
            onClick={() => setSidebarCollapsed(!sidebarCollapsed)}
            className="p-2 text-gray-500 hover:text-gray-300 border-b border-gray-800 transition-colors"
          >
            {sidebarCollapsed ? <ChevronRight size={14} /> : <ChevronLeft size={14} />}
          </button>
          <div className="flex-1 overflow-y-auto py-1">
            {panels.map(p => {
              const Icon = p.icon;
              return (
                <button
                  key={p.id}
                  onClick={() => setActivePanel(p.id)}
                  className={`w-full flex items-center gap-2 px-2 py-1.5 text-left transition-colors ${
                    activePanel === p.id
                      ? "bg-green-900/20 text-green-400 border-l-2 border-green-400"
                      : "text-gray-500 hover:text-gray-300 hover:bg-gray-900 border-l-2 border-transparent"
                  }`}
                >
                  <Icon size={14} className="shrink-0" />
                  {!sidebarCollapsed && <span className="text-[10px] font-mono truncate">{p.label}</span>}
                </button>
              );
            })}
          </div>
        </div>

        <div className="flex-1 flex flex-col min-h-0">
          {activePanel === "overview" ? (
            <div className="flex-1 grid grid-cols-12 gap-2 p-2 overflow-auto">
              <div className="col-span-3 flex flex-col gap-2">
                <div className="bg-gray-900 rounded p-2 border border-gray-700" style={{ minHeight: "300px" }}>
                  <div className="text-xs font-bold text-gray-400 mb-1">MAPA TACTICO</div>
                  <div className="rounded overflow-hidden" style={{ height: "260px" }}>
                    <TacticalMap units={state.units as UnitPosition[]} />
                  </div>
                </div>
                <AlertTicker />
              </div>
              <div className="col-span-6 flex flex-col gap-2">
                <IntelFeed />
                <ThreatPanel />
                <div className="bg-gray-900 rounded p-2 border border-gray-700">
                  <div className="text-xs font-bold text-gray-400 mb-1">LINEA TEMPORAL DE MISION</div>
                  <div className="flex flex-wrap gap-1 text-xs font-mono text-gray-500">
                    {state.timeline.map((ev, idx) => (
                      <span key={ev.id} className="flex items-center gap-1">
                        {idx > 0 && <span className="text-gray-600 mx-1">|</span>}
                        <span className={
                          ev.severity === "warning" ? "text-yellow-400" :
                          ev.severity === "critical" ? "text-red-400" : "text-green-400"
                        }>
                          {new Date(ev.timestamp).toISOString().slice(11, 16)}Z
                        </span>
                        <span className="text-gray-300">{ev.description}</span>
                      </span>
                    ))}
                  </div>
                </div>
              </div>
              <div className="col-span-3 flex flex-col gap-2">
                <div className="bg-gray-900 rounded p-2 border border-gray-700">
                  <div className="text-xs font-bold text-gray-400 mb-1">ANALISIS DE ENLACES</div>
                  <div className="bg-gray-800 rounded flex items-center justify-center text-gray-600 text-xs" style={{ height: "100px" }}>
                    [Grafo Neo4j]
                  </div>
                </div>
                <div className="bg-gray-900 rounded p-2 border border-gray-700">
                  <div className="text-xs font-bold text-gray-400 mb-1">MALLA DE SENSORES</div>
                  <div className="space-y-1">
                    {state.sensors.map((s) => (
                      <div key={s.id} className="flex items-center justify-between text-xs font-mono">
                        <span className={
                          s.status === "online" ? "text-green-400" :
                          s.status === "low_battery" ? "text-yellow-400" : "text-red-400"
                        }>
                          {s.type}
                        </span>
                        <span className="text-gray-500">{s.battery}%</span>
                      </div>
                    ))}
                  </div>
                </div>
                <div className="bg-gray-900 rounded p-2 border border-gray-700">
                  <div className="text-xs font-bold text-gray-400 mb-1">WARGAMING</div>
                  <div className="text-xs font-mono text-gray-500">Sin simulaciones activas</div>
                </div>
              </div>
            </div>
          ) : (
            <div className="flex-1 p-2 min-h-0">
              {renderPanel()}
            </div>
          )}
        </div>
      </div>

      <div className="border-t border-gray-800 p-2 bg-gray-950 flex gap-2 items-center">
        <QuickActions />
        <div className="flex-1" />
        <CommandInput />
      </div>
    </div>
  );
}
