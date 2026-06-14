"use client";
import { useState } from "react";
import { FileText, Eye, Send, History, ChevronDown } from "lucide-react";
import { useCOPStore } from "@/store/cop-store";

type ReportType = "SITREP" | "SPOTREP" | "SALUTE" | "MEDEVAC";

const templates: Record<ReportType, { name: string; color: string; fields: { key: string; label: string; type: "text" | "textarea" }[] }> = {
  SITREP: {
    name: "SITREP",
    color: "text-green-400 border-green-700 bg-green-900/20",
    fields: [
      { key: "situation", label: "1. Situacion General", type: "textarea" },
      { key: "enemy", label: "2. Enemigo", type: "textarea" },
      { key: "friendly", label: "3. Fuerzas Propias", type: "textarea" },
      { key: "weather", label: "4. Meteorologia", type: "text" },
      { key: "logistics", label: "5. Logistica", type: "textarea" },
      { key: "personnel", label: "6. Personal", type: "textarea" },
    ],
  },
  SPOTREP: {
    name: "SPOTREP",
    color: "text-blue-400 border-blue-700 bg-blue-900/20",
    fields: [
      { key: "size", label: "1. Tamano", type: "text" },
      { key: "activity", label: "2. Actividad", type: "textarea" },
      { key: "location", label: "3. Ubicacion", type: "text" },
      { key: "unit", label: "4. Unidad", type: "text" },
      { key: "time", label: "5. Hora", type: "text" },
      { key: "equipment", label: "6. Equipamiento", type: "textarea" },
    ],
  },
  SALUTE: {
    name: "SALUTE",
    color: "text-orange-400 border-orange-700 bg-orange-900/20",
    fields: [
      { key: "size", label: "S - Tamano", type: "text" },
      { key: "activity", label: "A - Actividad", type: "textarea" },
      { key: "location", label: "L - Ubicacion", type: "text" },
      { key: "unit", label: "U - Unidad", type: "text" },
      { key: "time", label: "T - Hora", type: "text" },
      { key: "equipment", label: "E - Equipamiento", type: "textarea" },
    ],
  },
  MEDEVAC: {
    name: "MEDEVAC",
    color: "text-red-400 border-red-700 bg-red-900/20",
    fields: [
      { key: "line1", label: "L1 - Ubicacion recogida", type: "text" },
      { key: "line2", label: "L2 - Numero heridos", type: "text" },
      { key: "line3", label: "L3 - Tipo de bajas", type: "text" },
      { key: "line4", label: "L4 - Prioridad", type: "text" },
      { key: "line5", label: "L5 - Tipo de aeronave", type: "text" },
      { key: "line6", label: "L6 - Equipamiento especial", type: "text" },
      { key: "line7", label: "L7 - Metodo de recogida", type: "text" },
      { key: "line8", label: "L8 - NBC / Proteccion", type: "text" },
      { key: "line9", label: "L9 - Descripcion terreno", type: "textarea" },
    ],
  },
};

export default function ReportsPanel() {
  const { reports, addReport, classification } = useCOPStore();
  const [selectedTemplate, setSelectedTemplate] = useState<ReportType | null>(null);
  const [formData, setFormData] = useState<Record<string, string>>({});
  const [showPreview, setShowPreview] = useState(false);
  const [showHistory, setShowHistory] = useState(false);

  const handleTemplateSelect = (type: ReportType) => {
    setSelectedTemplate(type);
    setFormData({});
    setShowPreview(false);
  };

  const handleGenerate = () => {
    if (!selectedTemplate) return;
    addReport({
      id: `rep${Date.now()}`,
      template: selectedTemplate,
      classification,
      content: formData,
      timestamp: new Date().toISOString(),
      author: "HQ",
      status: "DRAFT",
    });
    setSelectedTemplate(null);
    setFormData({});
    setShowPreview(false);
  };

  const templateList: ReportType[] = ["SITREP", "SPOTREP", "SALUTE", "MEDEVAC"];

  return (
    <div className="bg-gray-900 rounded border border-gray-700 flex flex-col h-full">
      <div className="flex items-center gap-2 px-3 py-2 border-b border-gray-700">
        <FileText size={14} className="text-green-400" />
        <span className="text-xs font-bold text-gray-400">GENERADOR DE REPORTES</span>
        <button
          onClick={() => setShowHistory(!showHistory)}
          className="ml-auto text-[10px] text-gray-500 hover:text-gray-300 flex items-center gap-0.5"
        >
          <History size={10} /> Historial ({reports.length})
        </button>
      </div>

      {showHistory ? (
        <div className="flex-1 overflow-y-auto p-2 space-y-1">
          <button
            onClick={() => setShowHistory(false)}
            className="text-[10px] text-gray-500 hover:text-gray-300 mb-1"
          >
            ← Volver a plantillas
          </button>
          {reports.map(r => (
            <div key={r.id} className="text-xs font-mono p-2 rounded bg-gray-800/50 border border-gray-700">
              <div className="flex items-center justify-between mb-0.5">
                <span className="text-green-400 font-bold">{r.template}</span>
                <span className={`text-[10px] px-1 py-0.5 rounded ${
                  r.status === "SENT" ? "text-green-400 bg-green-900/20" : "text-yellow-400 bg-yellow-900/20"
                }`}>
                  {r.status}
                </span>
              </div>
              <div className="text-[10px] text-gray-500">
                {new Date(r.timestamp).toISOString().slice(0, 16).replace("T", " ")}Z — {r.author}
              </div>
              <div className={`text-[10px] mt-0.5 px-1 py-0.5 rounded inline-block ${
                r.classification === "SECRET" ? "text-red-400 bg-red-900/30" :
                r.classification === "TOP SECRET" ? "text-purple-400 bg-purple-900/30" :
                "text-yellow-400 bg-yellow-900/30"
              }`}>
                {r.classification}
              </div>
            </div>
          ))}
        </div>
      ) : !selectedTemplate ? (
        <div className="flex-1 p-2">
          <div className="grid grid-cols-2 gap-2">
            {templateList.map(type => {
              const tmpl = templates[type];
              return (
                <button
                  key={type}
                  onClick={() => handleTemplateSelect(type)}
                  className={`p-3 rounded border text-xs font-mono font-bold transition-colors hover:brightness-125 ${tmpl.color}`}
                >
                  <FileText size={16} className="mx-auto mb-1" />
                  {tmpl.name}
                </button>
              );
            })}
          </div>
        </div>
      ) : showPreview ? (
        <div className="flex-1 overflow-y-auto p-2 space-y-2">
          <div className={`text-[10px] text-center py-1 font-bold tracking-wider ${
            classification === "SECRET" ? "bg-red-800 text-white" :
            classification === "TOP SECRET" ? "bg-purple-900 text-white" :
            "bg-blue-800 text-white"
          }`}>
            {classification}
          </div>
          <div className="text-xs font-mono text-green-400 font-bold text-center">
            {selectedTemplate} — {new Date().toISOString().slice(0, 10)}
          </div>
          {templates[selectedTemplate].fields.map(f => (
            <div key={f.key}>
              <div className="text-[10px] text-gray-500 font-bold">{f.label}</div>
              <div className="text-xs text-gray-300 bg-gray-800 rounded p-1 min-h-[20px]">
                {formData[f.key] || "—"}
              </div>
            </div>
          ))}
          <div className="flex gap-1">
            <button
              onClick={() => setShowPreview(false)}
              className="flex-1 bg-gray-800 text-gray-300 text-[10px] px-2 py-1 rounded border border-gray-700"
            >
              Editar
            </button>
            <button
              onClick={handleGenerate}
              className="flex-1 bg-green-800 hover:bg-green-700 text-green-100 text-[10px] px-2 py-1 rounded flex items-center justify-center gap-1 transition-colors"
            >
              <Send size={10} /> Generar
            </button>
          </div>
        </div>
      ) : (
        <div className="flex-1 overflow-y-auto p-2 space-y-1">
          <button
            onClick={() => setSelectedTemplate(null)}
            className="text-[10px] text-gray-500 hover:text-gray-300 mb-1"
          >
            ← Volver a plantillas
          </button>
          {templates[selectedTemplate].fields.map(f => (
            <div key={f.key}>
              <label className="text-[10px] text-gray-500 font-bold">{f.label}</label>
              {f.type === "textarea" ? (
                <textarea
                  value={formData[f.key] || ""}
                  onChange={e => setFormData({ ...formData, [f.key]: e.target.value })}
                  className="w-full bg-gray-800 text-gray-300 text-xs rounded px-2 py-1 border border-gray-700 resize-none h-16"
                />
              ) : (
                <input
                  value={formData[f.key] || ""}
                  onChange={e => setFormData({ ...formData, [f.key]: e.target.value })}
                  className="w-full bg-gray-800 text-gray-300 text-xs rounded px-2 py-1 border border-gray-700"
                />
              )}
            </div>
          ))}
          <button
            onClick={() => setShowPreview(true)}
            className="w-full bg-gray-800 hover:bg-gray-700 text-gray-300 text-[10px] px-2 py-1 rounded border border-gray-700 flex items-center justify-center gap-1 transition-colors"
          >
            <Eye size={10} /> Vista Previa
          </button>
        </div>
      )}
    </div>
  );
}
