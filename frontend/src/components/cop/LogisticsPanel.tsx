"use client";
import { useState } from "react";
import { Package, Users, Heart, Wrench, AlertTriangle, Plus, Check } from "lucide-react";
import { useCOPStore } from "@/store/cop-store";
import type { Supply, Personnel } from "@/lib/cop-types";

type LogTab = "supplies" | "personnel" | "medevac" | "maintenance";

const supplyTypeColors: Record<string, string> = {
  AMMO: "text-red-400 bg-red-900/20",
  FUEL: "text-orange-400 bg-orange-900/20",
  RATION: "text-green-400 bg-green-900/20",
  MEDICAL: "text-blue-400 bg-blue-900/20",
  EQUIPMENT: "text-purple-400 bg-purple-900/20",
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
  const { supplies, personnel, medevacRequests, maintenanceRequests, updateSupply, updatePersonnel, addMEDEVAC } = useCOPStore();
  const [tab, setTab] = useState<LogTab>("supplies");
  const [showMEDEVACForm, setShowMEDEVACForm] = useState(false);
  const [medevacData, setMedevacData] = useState<{
    location: string; woundedCount: number; classification: "URGENT" | "PRIORITY" | "ROUTINE";
    equipment: string; personnel: string;
  }>({
    location: "", woundedCount: 1, classification: "URGENT",
    equipment: "", personnel: "",
  });

  const tabs = [
    { id: "supplies" as const, label: "Suministros", icon: Package, count: supplies.length },
    { id: "personnel" as const, label: "Personal", icon: Users, count: personnel.length },
    { id: "medevac" as const, label: "MEDEVAC", icon: Heart, count: medevacRequests.length },
    { id: "maintenance" as const, label: "Mantenimiento", icon: Wrench, count: maintenanceRequests.length },
  ];

  const activeCount = personnel.filter(p => p.status === "ACTIVE").length;
  const wiaCount = personnel.filter(p => p.status === "WIA").length;

  const handleMEDEVACSubmit = () => {
    addMEDEVAC({
      id: `med${Date.now()}`,
      ...medevacData,
      status: "PENDING",
      timestamp: new Date().toISOString(),
    });
    setShowMEDEVACForm(false);
    setMedevacData({ location: "", woundedCount: 1, classification: "URGENT", equipment: "", personnel: "" });
  };

  return (
    <div className="bg-gray-900 rounded border border-gray-700 flex flex-col h-full">
      <div className="flex items-center gap-2 px-3 py-2 border-b border-gray-700">
        <Package size={14} className="text-green-400" />
        <span className="text-xs font-bold text-gray-400">LOGISTICA</span>
        <div className="ml-auto flex items-center gap-2 text-[10px]">
          <span className="text-green-400">{activeCount} activos</span>
          {wiaCount > 0 && <span className="text-yellow-400">{wiaCount} WIA</span>}
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
            {supplies.map(s => {
              const pct = (s.quantity / s.maxQuantity) * 100;
              const barColor = pct > 50 ? "bg-green-500" : pct > 20 ? "bg-yellow-500" : "bg-red-500";
              return (
                <div key={s.id} className="text-xs font-mono p-2 rounded bg-gray-800/50 border border-gray-700">
                  <div className="flex items-center justify-between mb-1">
                    <div className="flex items-center gap-1">
                      <span className={`text-[10px] px-1.5 py-0.5 rounded font-bold ${supplyTypeColors[s.type]}`}>
                        {s.type}
                      </span>
                      <span className="text-gray-300">{s.name}</span>
                    </div>
                    <span className={`text-[10px] ${statusColors[s.status]}`}>{s.status}</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <div className="flex-1 bg-gray-700 h-1.5 rounded">
                      <div className={`h-1.5 rounded ${barColor}`} style={{ width: `${pct}%` }} />
                    </div>
                    <span className="text-[10px] text-gray-400 w-20 text-right">
                      {s.quantity}/{s.maxQuantity} {s.unit}
                    </span>
                  </div>
                </div>
              );
            })}
          </div>
        )}

        {tab === "personnel" && (
          <div className="space-y-1">
            {personnel.map(p => (
              <div key={p.id} className="text-xs font-mono p-2 rounded bg-gray-800/50 border border-gray-700">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <span className="text-green-400 font-bold">{p.rank}</span>
                    <span className="text-gray-300">{p.name}</span>
                    <span className="text-gray-600">({p.unit})</span>
                  </div>
                  <span className={`text-[10px] px-1.5 py-0.5 rounded font-bold ${personnelStatusColors[p.status]}`}>
                    {p.status}
                  </span>
                </div>
                <div className="text-[10px] text-gray-600 mt-0.5">
                  Ultimo check-in: {new Date(p.lastCheckin).toISOString().slice(11, 16)}Z
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
                  placeholder="L2: Numero de heridos"
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
                  placeholder="L6: Equipamiento especial"
                  className="w-full bg-gray-900 text-gray-300 text-[10px] rounded px-2 py-1 border border-gray-700"
                />
                <input
                  value={medevacData.personnel}
                  onChange={e => setMedevacData({ ...medevacData, personnel: e.target.value })}
                  placeholder="L9: Personal medico"
                  className="w-full bg-gray-900 text-gray-300 text-[10px] rounded px-2 py-1 border border-gray-700"
                />
                <button
                  onClick={handleMEDEVACSubmit}
                  className="w-full bg-red-800 hover:bg-red-700 text-red-100 text-[10px] px-2 py-1 rounded transition-colors"
                >
                  Enviar Solicitud MEDEVAC
                </button>
              </div>
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
