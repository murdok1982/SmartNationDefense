"use client";
import { useState } from "react";
import { Package, Users, Heart, Wrench, Plus } from "lucide-react";
import { useCOPStore } from "@/store/cop-store";
import { useApiData } from "@/lib/use-api-data";
import { apiFetch, apiErrorMessage } from "@/lib/api";
import {
  mapSupply, mapPersonnel, mapMedevac, mapMaintenance,
  type BackendSupply, type BackendPersonnelResponse, type BackendMedevac, type BackendMaintenance,
} from "@/lib/mappers";

type LogTab = "supplies" | "personnel" | "medevac" | "maintenance";

const supplyTypeColors: Record<string, string> = {
  AMMO: "text-red-400 bg-red-900/20",
  FUEL: "text-orange-400 bg-orange-900/20",
  RATION: "text-green-400 bg-green-900/20",
  MEDICAL: "text-blue-400 bg-blue-900/20",
  EQUIPMENT: "text-purple-400 bg-purple-900/20",
  WATER: "text-cyan-400 bg-cyan-900/20",
  COMMS: "text-yellow-400 bg-yellow-900/20",
};

const statusColors: Record<string, string> = {
  AVAILABLE: "text-green-400",
  REQUESTED: "text-yellow-400",
  IN_TRANSIT: "text-blue-400",
  DELIVERED: "text-gray-400",
};

const personnelStatusColors: Record<string, string> = {
  ACTIVE: "text-green-400 bg-green-900/20",
  WIA: "text-yellow-400 bg-yellow-900/20",
  KIA: "text-red-400 bg-red-900/20",
  MIA: "text-purple-400 bg-purple-900/20",
  OFF_DUTY: "text-gray-400 bg-gray-800",
};

export default function LogisticsPanel() {
  const {
    supplies, personnel, medevacRequests, maintenanceRequests,
    setSupplies, setPersonnel, addMEDEVAC, addMaintenance,
  } = useCOPStore();
  const [tab, setTab] = useState<LogTab>("supplies");
  const [showMEDEVACForm, setShowMEDEVACForm] = useState(false);
  const [medevacData, setMedevacData] = useState<{
    location: string; woundedCount: number; classification: "URGENT" | "PRIORITY" | "ROUTINE";
    equipment: string; personnel: string;
  }>({
    location: "", woundedCount: 1, classification: "URGENT",
    equipment: "", personnel: "",
  });
  const [showMaintForm, setShowMaintForm] = useState(false);
  const [maintData, setMaintData] = useState({ equipmentId: "", equipmentType: "", issueType: "", description: "", priority: "MEDIUM" });
  const [formError, setFormError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [personnelSummary, setPersonnelSummary] = useState<{ active: number; casualties: number } | null>(null);

  const suppliesFetch = useApiData(
    async () => {
      const data = await apiFetch<BackendSupply[]>("/api/v1/logistics/supplies");
      setSupplies(data.map(mapSupply));
      return data.length;
    },
    { pollMs: 60000 },
  );

  const personnelFetch = useApiData(
    async () => {
      const data = await apiFetch<BackendPersonnelResponse>("/api/v1/logistics/personnel");
      setPersonnel(data.personnel.map(mapPersonnel));
      setPersonnelSummary({ active: data.active_count, casualties: data.casualties });
      return data.total;
    },
    { pollMs: 60000 },
  );

  const tabs = [
    { id: "supplies" as const, label: "Suministros", icon: Package, count: supplies.length },
    { id: "personnel" as const, label: "Personal", icon: Users, count: personnel.length },
    { id: "medevac" as const, label: "MEDEVAC", icon: Heart, count: medevacRequests.length },
    { id: "maintenance" as const, label: "Mantenimiento", icon: Wrench, count: maintenanceRequests.length },
  ];

  const activeCount = personnelSummary?.active ?? personnel.filter(p => p.status === "ACTIVE").length;
  const wiaCount = personnelSummary?.casualties ?? personnel.filter(p => p.status === "WIA" || p.status === "KIA").length;

  const handleMEDEVACSubmit = async () => {
    if (!medevacData.location.trim()) return;
    setSubmitting(true);
    setFormError(null);
    try {
      const result = await apiFetch<BackendMedevac>("/api/v1/logistics/medevac", {
        method: "POST",
        body: {
          casualty_id: `CAS-${Date.now()}`,
          location: { grid: medevacData.location },
          urgency: medevacData.classification,
          equipment: medevacData.equipment ? medevacData.equipment.split(",").map(s => s.trim()).filter(Boolean) : [],
          casualty_count: medevacData.woundedCount,
          special_equipment: medevacData.personnel,
        },
      });
      addMEDEVAC(mapMedevac(result));
      setShowMEDEVACForm(false);
      setMedevacData({ location: "", woundedCount: 1, classification: "URGENT", equipment: "", personnel: "" });
    } catch (e) {
      setFormError(apiErrorMessage(e));
    } finally {
      setSubmitting(false);
    }
  };

  const handleMaintSubmit = async () => {
    if (!maintData.equipmentId.trim() || !maintData.description.trim()) return;
    setSubmitting(true);
    setFormError(null);
    try {
      const result = await apiFetch<BackendMaintenance>("/api/v1/logistics/maintenance", {
        method: "POST",
        body: {
          equipment_id: maintData.equipmentId,
          equipment_type: maintData.equipmentType || "EQUIPO",
          issue_type: maintData.issueType || "FALLO",
          description: maintData.description,
          reported_by: "OPERATOR",
          priority: maintData.priority,
        },
      });
      addMaintenance(mapMaintenance(result));
      setShowMaintForm(false);
      setMaintData({ equipmentId: "", equipmentType: "", issueType: "", description: "", priority: "MEDIUM" });
    } catch (e) {
      setFormError(apiErrorMessage(e));
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="bg-gray-900 rounded border border-gray-700 flex flex-col h-full">
      <div className="flex items-center gap-2 px-3 py-2 border-b border-gray-700">
        <Package size={14} className="text-green-400" />
        <span className="text-xs font-bold text-gray-400">LOGISTICA</span>
        <div className="ml-auto flex items-center gap-2 text-[10px]">
          <span className="text-green-400">{activeCount} activos</span>
          {wiaCount > 0 && <span className="text-yellow-400">{wiaCount} bajas</span>}
        </div>
      </div>

      <div className="flex border-b border-gray-700">
        {tabs.map(t => {
          const Icon = t.icon;
          return (
            <button
              key={t.id}
              onClick={() => setTab(t.id)}
              className={`flex items-center gap-1 text-[10px] px-2 py-1.5 border-b-2 transition-colors ${
                tab === t.id
                  ? "border-green-400 text-green-400"
                  : "border-transparent text-gray-500 hover:text-gray-300"
              }`}
            >
              <Icon size={10} />
              {t.label}
              <span className="text-gray-600">({t.count})</span>
            </button>
          );
        })}
      </div>

      <div className="flex-1 overflow-y-auto p-2">
        {tab === "supplies" && (
          <div className="space-y-1">
            {suppliesFetch.loading && supplies.length === 0 && (
              <div className="text-xs font-mono text-gray-500 animate-pulse">Cargando suministros...</div>
            )}
            {suppliesFetch.error && (
              <div className="text-xs font-mono text-red-400">{suppliesFetch.error}</div>
            )}
            {!suppliesFetch.loading && !suppliesFetch.error && supplies.length === 0 && (
              <div className="text-xs font-mono text-gray-600">Sin suministros registrados</div>
            )}
            {supplies.map(s => {
              const belowThreshold = s.minThreshold > 0 && s.quantity < s.minThreshold;
              return (
                <div key={s.id} className="text-xs font-mono p-2 rounded bg-gray-800/50 border border-gray-700">
                  <div className="flex items-center justify-between mb-1">
                    <div className="flex items-center gap-1">
                      <span className={`text-[10px] px-1.5 py-0.5 rounded font-bold ${supplyTypeColors[s.type] ?? "text-gray-400 bg-gray-800"}`}>
                        {s.type}
                      </span>
                      <span className="text-gray-300">{s.quantity} {s.unit}</span>
                    </div>
                    <span className={`text-[10px] ${statusColors[s.status] ?? "text-gray-400"}`}>{s.status}</span>
                  </div>
                  <div className="flex items-center justify-between text-[10px]">
                    <span className="text-gray-500">Prioridad: {s.priority}</span>
                    {belowThreshold && (
                      <span className="text-red-400 font-bold">BAJO UMBRAL ({s.minThreshold} {s.unit})</span>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        )}

        {tab === "personnel" && (
          <div className="space-y-1">
            {personnelFetch.loading && personnel.length === 0 && (
              <div className="text-xs font-mono text-gray-500 animate-pulse">Cargando personal...</div>
            )}
            {personnelFetch.error && (
              <div className="text-xs font-mono text-red-400">{personnelFetch.error}</div>
            )}
            {!personnelFetch.loading && !personnelFetch.error && personnel.length === 0 && (
              <div className="text-xs font-mono text-gray-600">Sin personal registrado</div>
            )}
            {personnel.map(p => (
              <div key={p.id} className="text-xs font-mono p-2 rounded bg-gray-800/50 border border-gray-700">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <span className="text-green-400 font-bold">{p.rank}</span>
                    <span className="text-gray-300">{p.name}</span>
                    <span className="text-gray-600">({p.unit})</span>
                  </div>
                  <span className={`text-[10px] px-1.5 py-0.5 rounded font-bold ${personnelStatusColors[p.status] ?? "text-gray-400 bg-gray-800"}`}>
                    {p.status}
                  </span>
                </div>
                <div className="text-[10px] text-gray-600 mt-0.5">
                  {p.lastCheckin
                    ? `Ultimo check-in: ${new Date(p.lastCheckin).toISOString().slice(11, 16)}Z`
                    : "Sin check-in registrado"}
                  {p.medicalStatus ? ` — ${p.medicalStatus}` : ""}
                </div>
              </div>
            ))}
          </div>
        )}

        {tab === "medevac" && (
          <div className="space-y-2">
            <button
              onClick={() => setShowMEDEVACForm(!showMEDEVACForm)}
              className="flex items-center gap-1 text-[10px] bg-red-900/30 text-red-400 px-2 py-1 rounded border border-red-700 hover:bg-red-900/50 transition-colors"
            >
              <Plus size={10} /> Solicitar MEDEVAC
            </button>

            {showMEDEVACForm && (
              <div className="p-2 rounded bg-gray-800 border border-red-700 space-y-1">
                <div className="text-[10px] text-red-400 font-bold mb-1">MEDEVAC — 9 LINEAS NATO</div>
                <input
                  value={medevacData.location}
                  onChange={e => setMedevacData({ ...medevacData, location: e.target.value })}
                  placeholder="L1: Ubicacion del recogida"
                  className="w-full bg-gray-900 text-gray-300 text-[10px] rounded px-2 py-1 border border-gray-700"
                />
                <input
                  type="number"
                  value={medevacData.woundedCount}
                  onChange={e => setMedevacData({ ...medevacData, woundedCount: Number(e.target.value) })}
                  placeholder="L3: Numero de heridos"
                  className="w-full bg-gray-900 text-gray-300 text-[10px] rounded px-2 py-1 border border-gray-700"
                />
                <select
                  value={medevacData.classification}
                  onChange={e => setMedevacData({ ...medevacData, classification: e.target.value as "URGENT" | "PRIORITY" | "ROUTINE" })}
                  className="w-full bg-gray-900 text-gray-300 text-[10px] rounded px-2 py-1 border border-gray-700"
                >
                  <option value="URGENT">URGENTE</option>
                  <option value="PRIORITY">PRIORITARIO</option>
                  <option value="ROUTINE">RUTINA</option>
                </select>
                <input
                  value={medevacData.equipment}
                  onChange={e => setMedevacData({ ...medevacData, equipment: e.target.value })}
                  placeholder="L6: Equipamiento especial (coma)"
                  className="w-full bg-gray-900 text-gray-300 text-[10px] rounded px-2 py-1 border border-gray-700"
                />
                <input
                  value={medevacData.personnel}
                  onChange={e => setMedevacData({ ...medevacData, personnel: e.target.value })}
                  placeholder="L8: Equipamiento adicional"
                  className="w-full bg-gray-900 text-gray-300 text-[10px] rounded px-2 py-1 border border-gray-700"
                />
                {formError && <div className="text-[10px] font-mono text-red-400">{formError}</div>}
                <button
                  onClick={() => void handleMEDEVACSubmit()}
                  disabled={submitting}
                  className="w-full bg-red-800 hover:bg-red-700 disabled:opacity-50 text-red-100 text-[10px] px-2 py-1 rounded transition-colors"
                >
                  {submitting ? "Enviando..." : "Enviar Solicitud MEDEVAC"}
                </button>
              </div>
            )}

            {medevacRequests.length === 0 && !showMEDEVACForm && (
              <div className="text-xs font-mono text-gray-600">Sin solicitudes MEDEVAC en esta sesion</div>
            )}
            {medevacRequests.map(m => (
              <div key={m.id} className="text-xs font-mono p-2 rounded bg-gray-800/50 border border-red-700/50">
                <div className="flex items-center justify-between mb-1">
                  <span className={`text-[10px] font-bold ${
                    m.classification === "URGENT" ? "text-red-400" :
                    m.classification === "PRIORITY" ? "text-yellow-400" : "text-blue-400"
                  }`}>
                    {m.classification}
                  </span>
                  <span className={`text-[10px] ${
                    m.status === "COMPLETED" ? "text-green-400" :
                    m.status === "IN_TRANSIT" ? "text-blue-400" :
                    m.status === "APPROVED" ? "text-yellow-400" : "text-gray-400"
                  }`}>
                    {m.status}
                  </span>
                </div>
                <div className="text-[10px] text-gray-400">
                  {m.woundedCount} heridos — {m.location}
                </div>
                <div className="text-[10px] text-gray-600">
                  {new Date(m.timestamp).toISOString().slice(11, 16)}Z
                </div>
              </div>
            ))}
          </div>
        )}

        {tab === "maintenance" && (
          <div className="space-y-1">
            <button
              onClick={() => setShowMaintForm(!showMaintForm)}
              className="flex items-center gap-1 text-[10px] bg-yellow-900/30 text-yellow-400 px-2 py-1 rounded border border-yellow-700 hover:bg-yellow-900/50 transition-colors"
            >
              <Plus size={10} /> Reportar averia
            </button>

            {showMaintForm && (
              <div className="p-2 rounded bg-gray-800 border border-yellow-700 space-y-1">
                <input
                  value={maintData.equipmentId}
                  onChange={e => setMaintData({ ...maintData, equipmentId: e.target.value })}
                  placeholder="ID de equipo"
                  className="w-full bg-gray-900 text-gray-300 text-[10px] rounded px-2 py-1 border border-gray-700"
                />
                <input
                  value={maintData.equipmentType}
                  onChange={e => setMaintData({ ...maintData, equipmentType: e.target.value })}
                  placeholder="Tipo de equipo"
                  className="w-full bg-gray-900 text-gray-300 text-[10px] rounded px-2 py-1 border border-gray-700"
                />
                <input
                  value={maintData.issueType}
                  onChange={e => setMaintData({ ...maintData, issueType: e.target.value })}
                  placeholder="Tipo de fallo"
                  className="w-full bg-gray-900 text-gray-300 text-[10px] rounded px-2 py-1 border border-gray-700"
                />
                <textarea
                  value={maintData.description}
                  onChange={e => setMaintData({ ...maintData, description: e.target.value })}
                  placeholder="Descripcion"
                  className="w-full bg-gray-900 text-gray-300 text-[10px] rounded px-2 py-1 border border-gray-700 resize-none h-12"
                />
                <select
                  value={maintData.priority}
                  onChange={e => setMaintData({ ...maintData, priority: e.target.value })}
                  className="w-full bg-gray-900 text-gray-300 text-[10px] rounded px-2 py-1 border border-gray-700"
                >
                  <option value="LOW">BAJA</option>
                  <option value="MEDIUM">MEDIA</option>
                  <option value="HIGH">ALTA</option>
                  <option value="CRITICAL">CRITICA</option>
                </select>
                {formError && <div className="text-[10px] font-mono text-red-400">{formError}</div>}
                <button
                  onClick={() => void handleMaintSubmit()}
                  disabled={submitting}
                  className="w-full bg-yellow-800 hover:bg-yellow-700 disabled:opacity-50 text-yellow-100 text-[10px] px-2 py-1 rounded transition-colors"
                >
                  {submitting ? "Enviando..." : "Enviar reporte"}
                </button>
              </div>
            )}

            {maintenanceRequests.length === 0 && !showMaintForm && (
              <div className="text-xs font-mono text-gray-600">Sin reportes de mantenimiento en esta sesion</div>
            )}
            {maintenanceRequests.map(m => (
              <div key={m.id} className="text-xs font-mono p-2 rounded bg-gray-800/50 border border-gray-700">
                <div className="flex items-center justify-between mb-0.5">
                  <span className="text-gray-300 font-bold">{m.equipment}</span>
                  <span className={`text-[10px] px-1.5 py-0.5 rounded ${
                    m.priority === "CRITICAL" ? "text-red-400 bg-red-900/20" :
                    m.priority === "HIGH" ? "text-yellow-400 bg-yellow-900/20" :
                    "text-blue-400 bg-blue-900/20"
                  }`}>
                    {m.priority}
                  </span>
                </div>
                <div className="text-[10px] text-gray-500">{m.description}</div>
                <div className="flex items-center justify-between mt-0.5">
                  <span className={`text-[10px] ${
                    m.status === "COMPLETED" ? "text-green-400" :
                    m.status === "IN_PROGRESS" ? "text-yellow-400" : "text-gray-400"
                  }`}>
                    {m.status}
                  </span>
                  <span className="text-[10px] text-gray-600">
                    {new Date(m.timestamp).toISOString().slice(11, 16)}Z
                  </span>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
