"use client";
import { useState } from "react";
import { FileText, Eye, Send, History } from "lucide-react";
import { useCOPStore } from "@/store/cop-store";
import { useApiData } from "@/lib/use-api-data";
import { apiFetch, apiErrorMessage } from "@/lib/api";
import { mapReport, type BackendReport } from "@/lib/mappers";

type ReportType = "SITREP" | "SPOTREP" | "SALUTE" | "MEDEVAC";

const templates: Record<ReportType, { name: string; color: string; fields: { key: string; label: string; type: "text" | "textarea" }[] }> = {
  SITREP: {
    name: "SITREP",
    color: "text-green-400 border-green-700 bg-green-900/20",
    fields: [
      { key: "from_unit", label: "De (unidad)", type: "text" },
      { key: "to_unit", label: "Para (unidad)", type: "text" },
      { key: "enemy_forces", label: "1. Fuerzas Enemigas", type: "textarea" },
      { key: "friendly_forces", label: "2. Fuerzas Propias", type: "textarea" },
      { key: "weather_current", label: "3. Meteorologia Actual", type: "text" },
      { key: "supply_status", label: "4. Estado Logistico", type: "textarea" },
      { key: "personnel_strength", label: "5. Personal", type: "text" },
      { key: "comms_status", label: "6. Comunicaciones", type: "text" },
    ],
  },
  SPOTREP: {
    name: "SPOTREP",
    color: "text-blue-400 border-blue-700 bg-blue-900/20",
    fields: [
      { key: "size", label: "1. Tamano", type: "text" },
      { key: "activity", label: "2. Actividad", type: "textarea" },
      { key: "location", label: "3. Ubicacion (grid)", type: "text" },
      { key: "unit_identified", label: "4. Unidad", type: "text" },
      { key: "time_observed", label: "5. Hora observacion", type: "text" },
      { key: "equipment", label: "6. Equipamiento", type: "textarea" },
      { key: "narrative", label: "7. Narrativa", type: "textarea" },
      { key: "assessment", label: "8. Evaluacion", type: "textarea" },
    ],
  },
  SALUTE: {
    name: "SALUTE",
    color: "text-orange-400 border-orange-700 bg-orange-900/20",
    fields: [
      { key: "size", label: "S - Tamano", type: "text" },
      { key: "activity", label: "A - Actividad", type: "textarea" },
      { key: "location", label: "L - Ubicacion (grid)", type: "text" },
      { key: "unit", label: "U - Unidad", type: "text" },
      { key: "time", label: "T - Hora", type: "text" },
      { key: "equipment", label: "E - Equipamiento", type: "textarea" },
      { key: "assessment", label: "Evaluacion", type: "textarea" },
    ],
  },
  MEDEVAC: {
    name: "MEDEVAC",
    color: "text-red-400 border-red-700 bg-red-900/20",
    fields: [
      { key: "urgency", label: "Urgencia (URGENT/PRIORITY/ROUTINE)", type: "text" },
      { key: "pickup_location", label: "L1 - Ubicacion recogida (grid)", type: "text" },
      { key: "radio_freq", label: "L2 - Frecuencia radio", type: "text" },
      { key: "casualty_count", label: "L3 - Numero de bajas", type: "text" },
      { key: "security", label: "L4 - Seguridad (N/P/E/X)", type: "text" },
      { key: "casualty_status", label: "L7 - Estado de bajas", type: "text" },
      { key: "special_equipment", label: "L8 - Equipamiento especial", type: "text" },
      { key: "terrain", label: "L9 - Descripcion terreno", type: "textarea" },
      { key: "requesting_unit", label: "Unidad solicitante", type: "text" },
    ],
  },
};

function buildPayload(type: ReportType, formData: Record<string, string>, classification: string): Record<string, unknown> {
  const base = { classification, created_by: "OPERATOR" };
  switch (type) {
    case "SITREP":
      return {
        ...base,
        from_unit: formData.from_unit ?? "",
        to_unit: formData.to_unit ?? "",
        enemy_forces: formData.enemy_forces ?? "",
        friendly_forces: formData.friendly_forces ?? "",
        weather_current: formData.weather_current ?? "",
        supply_status: formData.supply_status ?? "",
        personnel_strength: formData.personnel_strength ?? "",
        comms_status: formData.comms_status ?? "",
      };
    case "SPOTREP":
      return {
        ...base,
        size: formData.size ?? "",
        activity: formData.activity ?? "",
        location: { grid: formData.location ?? "" },
        unit_identified: formData.unit_identified ?? "",
        time_observed: formData.time_observed || undefined,
        equipment: formData.equipment ?? "",
        narrative: formData.narrative ?? "",
        assessment: formData.assessment ?? "",
      };
    case "SALUTE":
      return {
        ...base,
        size: formData.size ?? "",
        activity: formData.activity ?? "",
        location: { grid: formData.location ?? "" },
        unit: formData.unit ?? "",
        time: formData.time || undefined,
        equipment: formData.equipment ?? "",
        assessment: formData.assessment ?? "",
      };
    case "MEDEVAC":
      return {
        urgency: formData.urgency || "ROUTINE",
        pickup_location: { grid: formData.pickup_location ?? "" },
        radio_freq: formData.radio_freq ?? "",
        casualty_count: Number(formData.casualty_count) || 0,
        security: formData.security || "N",
        casualty_status: formData.casualty_status ?? "",
        special_equipment: formData.special_equipment ?? "",
        terrain: formData.terrain ?? "",
        requesting_unit: formData.requesting_unit ?? "",
        created_by: "OPERATOR",
      };
  }
}

export default function ReportsPanel() {
  const { reports, setReports, addReport, classification } = useCOPStore();
  const [selectedTemplate, setSelectedTemplate] = useState<ReportType | null>(null);
  const [formData, setFormData] = useState<Record<string, string>>({});
  const [showPreview, setShowPreview] = useState(false);
  const [showHistory, setShowHistory] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const historyFetch = useApiData(
    async () => {
      const data = await apiFetch<BackendReport[]>("/api/v1/reports?limit=50");
      setReports(data.map(mapReport));
      return data.length;
    },
    { pollMs: 60000 },
  );

  const handleTemplateSelect = (type: ReportType) => {
    setSelectedTemplate(type);
    setFormData({});
    setShowPreview(false);
    setError(null);
  };

  const handleGenerate = async () => {
    if (!selectedTemplate) return;
    setSubmitting(true);
    setError(null);
    try {
      const result = await apiFetch<BackendReport>(`/api/v1/reports/${selectedTemplate.toLowerCase()}`, {
        method: "POST",
        body: buildPayload(selectedTemplate, formData, classification),
      });
      addReport(mapReport(result));
      setSelectedTemplate(null);
      setFormData({});
      setShowPreview(false);
      setShowHistory(true);
    } catch (e) {
      setError(apiErrorMessage(e));
    } finally {
      setSubmitting(false);
    }
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
          {historyFetch.loading && reports.length === 0 && (
            <div className="text-xs font-mono text-gray-500 animate-pulse">Cargando historial...</div>
          )}
          {historyFetch.error && (
            <div className="text-xs font-mono text-red-400">{historyFetch.error}</div>
          )}
          {!historyFetch.loading && !historyFetch.error && reports.length === 0 && (
            <div className="text-xs font-mono text-gray-600">Sin reportes generados</div>
          )}
          {reports.map(r => (
            <div key={r.id} className="text-xs font-mono p-2 rounded bg-gray-800/50 border border-gray-700">
              <div className="flex items-center justify-between mb-1">
                <span className={`font-bold ${
                  r.template === "SITREP" ? "text-green-400" :
                  r.template === "SPOTREP" ? "text-blue-400" :
                  r.template === "SALUTE" ? "text-orange-400" : "text-red-400"
                }`}>
                  {r.template}
                </span>
                <span className="text-[10px] text-gray-500">{r.classification}</span>
              </div>
              <div className="text-[10px] text-gray-400">{r.title}</div>
              <div className="flex items-center justify-between mt-0.5">
                <span className="text-[10px] text-gray-600">{r.author}</span>
                <span className="text-[10px] text-gray-600">
                  {r.timestamp ? new Date(r.timestamp).toISOString().slice(11, 16) : "--"}Z
                </span>
              </div>
              <pre className="text-[9px] text-gray-500 mt-1 max-h-24 overflow-y-auto whitespace-pre-wrap">
                {JSON.stringify(r.content, null, 1)}
              </pre>
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
          {error && <div className="text-[10px] font-mono text-red-400">{error}</div>}
          <div className="flex gap-1">
            <button
              onClick={() => setShowPreview(false)}
              className="flex-1 bg-gray-800 text-gray-300 text-[10px] px-2 py-1 rounded border border-gray-700"
            >
              Editar
            </button>
            <button
              onClick={() => void handleGenerate()}
              disabled={submitting}
              className="flex-1 bg-green-800 hover:bg-green-700 disabled:opacity-50 text-green-100 text-[10px] px-2 py-1 rounded flex items-center justify-center gap-1 transition-colors"
            >
              <Send size={10} /> {submitting ? "Generando..." : "Generar"}
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
