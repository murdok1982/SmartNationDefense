"use client";
import { useState, useCallback } from "react";
import { GripHorizontal, Maximize2, Minimize2, Save, FolderOpen, Layout, X, Plus } from "lucide-react";
import { useCOPStore } from "@/store/cop-store";
import type { WidgetConfig } from "@/lib/cop-types";
import dynamic from "next/dynamic";

const DynamicTacticalMap = dynamic(() => import("./TacticalMapEnhanced"), { ssr: false });
const DynamicMessaging = dynamic(() => import("./MessagingPanel"), { ssr: false });
const DynamicLogistics = dynamic(() => import("./LogisticsPanel"), { ssr: false });
const DynamicReports = dynamic(() => import("./ReportsPanel"), { ssr: false });
const DynamicTerrain = dynamic(() => import("./TerrainAnalysis"), { ssr: false });
const DynamicAAR = dynamic(() => import("./AARPanel"), { ssr: false });
const DynamicThreatPred = dynamic(() => import("./ThreatPrediction"), { ssr: false });
const DynamicPlanning = dynamic(() => import("./PlanningPanel"), { ssr: false });

const widgetComponents: Record<string, React.ComponentType> = {
  TacticalMap: DynamicTacticalMap,
  MessagingPanel: DynamicMessaging,
  LogisticsPanel: DynamicLogistics,
  ReportsPanel: DynamicReports,
  TerrainAnalysis: DynamicTerrain,
  AARPanel: DynamicAAR,
  ThreatPrediction: DynamicThreatPred,
  PlanningPanel: DynamicPlanning,
};

const availableWidgets = [
  { component: "TacticalMap", title: "Mapa Tactico" },
  { component: "MessagingPanel", title: "Mensajeria" },
  { component: "LogisticsPanel", title: "Logistica" },
  { component: "ReportsPanel", title: "Reportes" },
  { component: "TerrainAnalysis", title: "Terreno" },
  { component: "AARPanel", title: "AAR" },
  { component: "ThreatPrediction", title: "Prediccion" },
  { component: "PlanningPanel", title: "Planificacion" },
];

const presets: Record<string, WidgetConfig[]> = {
  c2: [
    { id: "w1", component: "TacticalMap", title: "Mapa Tactico", x: 0, y: 0, width: 6, height: 4, minimized: false },
    { id: "w2", component: "MessagingPanel", title: "Mensajeria", x: 6, y: 0, width: 3, height: 4, minimized: false },
    { id: "w3", component: "PlanningPanel", title: "Planificacion", x: 9, y: 0, width: 3, height: 4, minimized: false },
  ],
  intel: [
    { id: "w1", component: "TacticalMap", title: "Mapa Tactico", x: 0, y: 0, width: 4, height: 4, minimized: false },
    { id: "w2", component: "ThreatPrediction", title: "Prediccion", x: 4, y: 0, width: 4, height: 2, minimized: false },
    { id: "w3", component: "TerrainAnalysis", title: "Terreno", x: 4, y: 2, width: 4, height: 2, minimized: false },
    { id: "w4", component: "ReportsPanel", title: "Reportes", x: 8, y: 0, width: 4, height: 4, minimized: false },
  ],
  logistics: [
    { id: "w1", component: "LogisticsPanel", title: "Logistica", x: 0, y: 0, width: 6, height: 4, minimized: false },
    { id: "w2", component: "AARPanel", title: "AAR", x: 6, y: 0, width: 6, height: 4, minimized: false },
  ],
};

export default function MultiMonitor() {
  const { widgets, updateWidgets, layouts, saveLayout, loadLayout } = useCOPStore();
  const [draggingId, setDraggingId] = useState<string | null>(null);
  const [showPresets, setShowPresets] = useState(false);
  const [showSaveDialog, setShowSaveDialog] = useState(false);
  const [layoutName, setLayoutName] = useState("");
  const [showAddWidget, setShowAddWidget] = useState(false);

  const toggleMinimize = (id: string) => {
    updateWidgets(widgets.map(w => w.id === id ? { ...w, minimized: !w.minimized } : w));
  };

  const removeWidget = (id: string) => {
    updateWidgets(widgets.filter(w => w.id !== id));
  };

  const handleSaveLayout = () => {
    if (!layoutName.trim()) return;
    saveLayout(layoutName);
    setLayoutName("");
    setShowSaveDialog(false);
  };

  const applyPreset = (preset: string) => {
    const presetWidgets = presets[preset];
    if (presetWidgets) {
      updateWidgets(presetWidgets.map(w => ({ ...w, id: `${w.id}_${Date.now()}` })));
    }
    setShowPresets(false);
  };

  const addWidget = (component: string, title: string) => {
    const maxX = widgets.length > 0 ? Math.max(...widgets.map(w => w.x + w.width)) : 0;
    const newWidget: WidgetConfig = {
      id: `w_${Date.now()}`,
      component,
      title,
      x: maxX,
      y: 0,
      width: 3,
      height: 2,
      minimized: false,
    };
    updateWidgets([...widgets, newWidget]);
    setShowAddWidget(false);
  };

  const colWidth = 100 / 12;

  return (
    <div className="bg-gray-900 rounded border border-gray-700 flex flex-col h-full">
      <div className="flex items-center gap-2 px-3 py-2 border-b border-gray-700">
        <Layout size={14} className="text-green-400" />
        <span className="text-xs font-bold text-gray-400">MULTI-MONITOR</span>
        <div className="ml-auto flex items-center gap-1">
          <button
            onClick={() => setShowPresets(!showPresets)}
            className="text-[10px] text-gray-500 hover:text-gray-300 px-1.5 py-0.5 rounded border border-gray-700 transition-colors"
          >
            Presets
          </button>
          <button
            onClick={() => setShowSaveDialog(!showSaveDialog)}
            className="text-[10px] text-gray-500 hover:text-gray-300 px-1.5 py-0.5 rounded border border-gray-700 flex items-center gap-0.5 transition-colors"
          >
            <Save size={10} /> Guardar
          </button>
          <button
            onClick={() => setShowAddWidget(!showAddWidget)}
            className="text-[10px] text-gray-500 hover:text-gray-300 px-1.5 py-0.5 rounded border border-gray-700 flex items-center gap-0.5 transition-colors"
          >
            <Plus size={10} /> Widget
          </button>
        </div>
      </div>

      {showPresets && (
        <div className="p-2 border-b border-gray-700 flex gap-1">
          {Object.keys(presets).map(p => (
            <button
              key={p}
              onClick={() => applyPreset(p)}
              className="text-[10px] px-2 py-1 rounded bg-gray-800 border border-gray-700 text-gray-400 hover:text-green-400 hover:border-green-700 transition-colors uppercase"
            >
              {p}
            </button>
          ))}
          {layouts.map(l => (
            <button
              key={l.id}
              onClick={() => { loadLayout(l.id); setShowPresets(false); }}
              className="text-[10px] px-2 py-1 rounded bg-gray-800 border border-gray-700 text-gray-400 hover:text-green-400 hover:border-green-700 transition-colors flex items-center gap-0.5"
            >
              <FolderOpen size={10} /> {l.name}
            </button>
          ))}
        </div>
      )}

      {showSaveDialog && (
        <div className="p-2 border-b border-gray-700 flex gap-1">
          <input
            value={layoutName}
            onChange={e => setLayoutName(e.target.value)}
            placeholder="Nombre del layout..."
            className="flex-1 bg-gray-800 text-gray-300 text-[10px] rounded px-2 py-1 border border-gray-700"
          />
          <button
            onClick={handleSaveLayout}
            className="text-[10px] bg-green-800 hover:bg-green-700 text-green-100 px-2 py-1 rounded transition-colors"
          >
            Guardar
          </button>
        </div>
      )}

      {showAddWidget && (
        <div className="p-2 border-b border-gray-700">
          <div className="grid grid-cols-4 gap-1">
            {availableWidgets.map(w => (
              <button
                key={w.component}
                onClick={() => addWidget(w.component, w.title)}
                className="text-[10px] px-2 py-1 rounded bg-gray-800 border border-gray-700 text-gray-400 hover:text-green-400 hover:border-green-700 transition-colors"
              >
                {w.title}
              </button>
            ))}
          </div>
        </div>
      )}

      <div className="flex-1 relative overflow-auto p-1">
        {widgets.length === 0 && (
          <div className="text-xs font-mono text-gray-600 text-center py-8">
            Sin widgets. Anadir widgets o seleccionar un preset.
          </div>
        )}
        {widgets.map(w => {
          const Component = widgetComponents[w.component];
          if (!Component) return null;
          return (
            <div
              key={w.id}
              className={`absolute border border-gray-700 rounded overflow-hidden bg-gray-900 ${
                draggingId === w.id ? "opacity-70 z-50" : ""
              }`}
              style={{
                left: `${w.x * colWidth}%`,
                top: `${w.y * 80}px`,
                width: `${w.width * colWidth}%`,
                height: w.minimized ? "32px" : `${w.height * 80}px`,
                transition: draggingId === w.id ? "none" : "all 0.2s",
              }}
            >
              <div className="flex items-center gap-1 px-2 py-1 bg-gray-800 border-b border-gray-700 cursor-move">
                <GripHorizontal size={10} className="text-gray-600" />
                <span className="text-[10px] text-gray-400 font-mono">{w.title}</span>
                <div className="ml-auto flex items-center gap-0.5">
                  <button
                    onClick={() => toggleMinimize(w.id)}
                    className="text-gray-500 hover:text-gray-300 p-0.5"
                  >
                    {w.minimized ? <Maximize2 size={10} /> : <Minimize2 size={10} />}
                  </button>
                  <button
                    onClick={() => removeWidget(w.id)}
                    className="text-gray-500 hover:text-red-400 p-0.5"
                  >
                    <X size={10} />
                  </button>
                </div>
              </div>
              {!w.minimized && (
                <div className="h-[calc(100%-24px)] overflow-hidden">
                  <Component />
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
