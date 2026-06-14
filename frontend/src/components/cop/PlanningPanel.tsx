"use client";
import { useState } from "react";
import { FileText, Target, Shield, GitBranch, Plus, Check, ChevronDown, ChevronRight } from "lucide-react";
import { useCOPStore } from "@/store/cop-store";
import type { OPORD, COA } from "@/lib/cop-types";

type PlanningTab = "opord" | "coa" | "risk" | "sync";

export default function PlanningPanel() {
  const { opords, coas, risks, addOPORD, updateOPORD, addCOA, addRisk } = useCOPStore();
  const [tab, setTab] = useState<PlanningTab>("opord");
  const [editingOPORD, setEditingOPORD] = useState<OPORD | null>(null);
  const [newCOA, setNewCOA] = useState({ name: "", description: "", successProbability: 0.5, risk: 5, resources: "", duration: "" });
  const [newRisk, setNewRisk] = useState<{ hazard: string; probability: 1 | 2 | 3 | 4 | 5; impact: 1 | 2 | 3 | 4 | 5; mitigation: string }>({
    hazard: "", probability: 3, impact: 3, mitigation: "",
  });

  const tabs = [
    { id: "opord" as const, label: "OPORD", icon: FileText },
    { id: "coa" as const, label: "COA", icon: Target },
    { id: "risk" as const, label: "Riesgos", icon: Shield },
    { id: "sync" as const, label: "Sincronizacion", icon: GitBranch },
  ];

  const startNewOPORD = () => {
    setEditingOPORD({
      id: `op${Date.now()}`,
      operationName: "",
      paragraph1_situation: "",
      paragraph2_mission: "",
      paragraph3_execution: "",
      paragraph4_sustainment: "",
      paragraph5_commandSignal: "",
      status: "DRAFT",
      createdAt: new Date().toISOString(),
    });
  };

  const saveOPORD = () => {
    if (!editingOPORD) return;
    const existing = opords.find(o => o.id === editingOPORD.id);
    if (existing) {
      updateOPORD(editingOPORD.id, editingOPORD);
    } else {
      addOPORD(editingOPORD);
    }
    setEditingOPORD(null);
  };

  const saveCOA = () => {
    addCOA({ ...newCOA, id: `coa${Date.now()}` });
    setNewCOA({ name: "", description: "", successProbability: 0.5, risk: 5, resources: "", duration: "" });
  };

  const saveRisk = () => {
    const residualRisk = Math.max(1, newRisk.probability + newRisk.impact - Math.min(newRisk.probability, newRisk.impact));
    addRisk({ ...newRisk, id: `r${Date.now()}`, residualRisk: Math.min(5, residualRisk) });
    setNewRisk({ hazard: "", probability: 3, impact: 3, mitigation: "" });
  };

  const riskMatrixColor = (p: number, i: number) => {
    const score = p * i;
    if (score >= 16) return "bg-red-600";
    if (score >= 9) return "bg-orange-600";
    if (score >= 4) return "bg-yellow-600";
    return "bg-green-600";
  };

  return (
    <div className="bg-gray-900 rounded border border-gray-700 flex flex-col h-full">
      <div className="flex items-center gap-2 px-3 py-2 border-b border-gray-700">
        <Target size={14} className="text-green-400" />
        <span className="text-xs font-bold text-gray-400">PLANIFICACION</span>
      </div>

      <div className="flex border-b border-gray-700">
        {tabs.map(t => {
          const Icon = t.icon;
          return (
            <button
              key={t.id}
              onClick={() => setTab(t.id)}
              className={`flex items-center gap-1 text-[10px] px-2 py-1.5 border-b-2 transition-colors ${
                tab === t.id ? "border-green-400 text-green-400" : "border-transparent text-gray-500 hover:text-gray-300"
              }`}
            >
              <Icon size={10} />
              {t.label}
            </button>
          );
        })}
      </div>

      <div className="flex-1 overflow-y-auto p-2">
        {tab === "opord" && (
          <div className="space-y-2">
            {!editingOPORD ? (
              <>
                <button
                  onClick={startNewOPORD}
                  className="flex items-center gap-1 text-[10px] bg-green-900/30 text-green-400 px-2 py-1 rounded border border-green-700 hover:bg-green-900/50 transition-colors"
                >
                  <Plus size={10} /> Nueva OPORD
                </button>
                {opords.map(o => (
                  <div key={o.id} className="text-xs font-mono p-2 rounded bg-gray-800/50 border border-gray-700">
                    <div className="flex items-center justify-between mb-1">
                      <span className="text-green-400 font-bold">{o.operationName}</span>
                      <span className={`text-[10px] px-1.5 py-0.5 rounded ${
                        o.status === "DISTRIBUTED" ? "text-green-400 bg-green-900/20" :
                        o.status === "APPROVED" ? "text-blue-400 bg-blue-900/20" :
                        "text-yellow-400 bg-yellow-900/20"
                      }`}>
                        {o.status}
                      </span>
                    </div>
                    <button
                      onClick={() => setEditingOPORD(o)}
                      className="text-[10px] text-gray-500 hover:text-gray-300"
                    >
                      Editar...
                    </button>
                  </div>
                ))}
              </>
            ) : (
              <div className="space-y-1">
                <input
                  value={editingOPORD.operationName}
                  onChange={e => setEditingOPORD({ ...editingOPORD, operationName: e.target.value })}
                  placeholder="Nombre de operacion"
                  className="w-full bg-gray-800 text-green-400 text-xs rounded px-2 py-1 border border-gray-700 font-bold"
                />
                {[
                  { key: "paragraph1_situation", label: "1. SITUACION" },
                  { key: "paragraph2_mission", label: "2. MISION" },
                  { key: "paragraph3_execution", label: "3. EJECUCION" },
                  { key: "paragraph4_sustainment", label: "4. SOSTENIMIENTO" },
                  { key: "paragraph5_commandSignal", label: "5. MANDO Y SENALES" },
                ].map(p => (
                  <div key={p.key}>
                    <label className="text-[10px] text-gray-500 font-bold">{p.label}</label>
                    <textarea
                      value={editingOPORD[p.key as keyof OPORD] as string}
                      onChange={e => setEditingOPORD({ ...editingOPORD, [p.key]: e.target.value })}
                      className="w-full bg-gray-800 text-gray-300 text-xs rounded px-2 py-1 border border-gray-700 resize-none h-16"
                    />
                  </div>
                ))}
                <div className="flex gap-1">
                  <button
                    onClick={() => setEditingOPORD(null)}
                    className="flex-1 bg-gray-800 text-gray-300 text-[10px] px-2 py-1 rounded border border-gray-700"
                  >
                    Cancelar
                  </button>
                  <button
                    onClick={saveOPORD}
                    className="flex-1 bg-green-800 hover:bg-green-700 text-green-100 text-[10px] px-2 py-1 rounded transition-colors"
                  >
                    Guardar
                  </button>
                </div>
              </div>
            )}
          </div>
        )}

        {tab === "coa" && (
          <div className="space-y-2">
            <div className="space-y-1">
              {coas.map(c => (
                <div key={c.id} className="text-xs font-mono p-2 rounded bg-gray-800/50 border border-gray-700">
                  <div className="flex items-center justify-between mb-0.5">
                    <span className="text-green-400 font-bold">{c.name}</span>
                    <span className="text-[10px] text-gray-500">{c.duration}</span>
                  </div>
                  <div className="text-[10px] text-gray-400 mb-1">{c.description}</div>
                  <div className="flex items-center gap-2 text-[10px]">
                    <span className="text-gray-500">Exito:</span>
                    <div className="w-16 bg-gray-700 h-1 rounded">
                      <div className="h-1 rounded bg-green-500" style={{ width: `${c.successProbability * 100}%` }} />
                    </div>
                    <span className="text-green-400">{Math.round(c.successProbability * 100)}%</span>
                    <span className="text-gray-500 ml-2">Riesgo: {c.risk}/10</span>
                  </div>
                  <div className="text-[10px] text-gray-600 mt-0.5">Recursos: {c.resources}</div>
                </div>
              ))}
            </div>

            <div className="border-t border-gray-700 pt-2">
              <div className="text-[10px] text-gray-500 font-bold mb-1">NUEVA COA</div>
              <div className="space-y-1">
                <input
                  value={newCOA.name}
                  onChange={e => setNewCOA({ ...newCOA, name: e.target.value })}
                  placeholder="Nombre"
                  className="w-full bg-gray-800 text-gray-300 text-[10px] rounded px-2 py-1 border border-gray-700"
                />
                <textarea
                  value={newCOA.description}
                  onChange={e => setNewCOA({ ...newCOA, description: e.target.value })}
                  placeholder="Descripcion"
                  className="w-full bg-gray-800 text-gray-300 text-[10px] rounded px-2 py-1 border border-gray-700 resize-none h-12"
                />
                <div className="flex gap-1">
                  <input
                    value={newCOA.resources}
                    onChange={e => setNewCOA({ ...newCOA, resources: e.target.value })}
                    placeholder="Recursos"
                    className="flex-1 bg-gray-800 text-gray-300 text-[10px] rounded px-2 py-1 border border-gray-700"
                  />
                  <input
                    value={newCOA.duration}
                    onChange={e => setNewCOA({ ...newCOA, duration: e.target.value })}
                    placeholder="Duracion"
                    className="w-20 bg-gray-800 text-gray-300 text-[10px] rounded px-2 py-1 border border-gray-700"
                  />
                </div>
                <button
                  onClick={saveCOA}
                  className="w-full bg-green-800 hover:bg-green-700 text-green-100 text-[10px] px-2 py-1 rounded transition-colors"
                >
                  Anadir COA
                </button>
              </div>
            </div>

            <div className="border-t border-gray-700 pt-2">
              <div className="text-[10px] text-gray-500 font-bold mb-1">MATRIZ COMPARATIVA</div>
              <div className="overflow-x-auto">
                <table className="w-full text-[10px] font-mono">
                  <thead>
                    <tr className="text-gray-500">
                      <th className="text-left py-0.5">COA</th>
                      <th className="text-center py-0.5">Exito</th>
                      <th className="text-center py-0.5">Riesgo</th>
                      <th className="text-center py-0.5">Duracion</th>
                    </tr>
                  </thead>
                  <tbody>
                    {coas.map(c => (
                      <tr key={c.id} className="text-gray-300">
                        <td className="py-0.5">{c.name}</td>
                        <td className="text-center text-green-400">{Math.round(c.successProbability * 100)}%</td>
                        <td className="text-center text-orange-400">{c.risk}/10</td>
                        <td className="text-center">{c.duration}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        )}

        {tab === "risk" && (
          <div className="space-y-2">
            <div className="space-y-1">
              {risks.map(r => (
                <div key={r.id} className="text-xs font-mono p-2 rounded bg-gray-800/50 border border-gray-700">
                  <div className="flex items-center justify-between mb-0.5">
                    <span className="text-gray-300 font-bold">{r.hazard}</span>
                    <span className={`text-[10px] px-1.5 py-0.5 rounded ${
                      r.residualRisk >= 4 ? "text-red-400 bg-red-900/20" :
                      r.residualRisk >= 2 ? "text-yellow-400 bg-yellow-900/20" :
                      "text-green-400 bg-green-900/20"
                    }`}>
                      Riesgo: {r.residualRisk}
                    </span>
                  </div>
                  <div className="flex items-center gap-2 text-[10px]">
                    <span className="text-gray-500">P:{r.probability}</span>
                    <span className="text-gray-500">I:{r.impact}</span>
                    <span className="text-gray-600">|</span>
                    <span className="text-gray-400">Mitigacion: {r.mitigation}</span>
                  </div>
                </div>
              ))}
            </div>

            <div className="border-t border-gray-700 pt-2">
              <div className="text-[10px] text-gray-500 font-bold mb-1">MATRIZ DE RIESGO</div>
              <div className="grid grid-cols-6 gap-0.5 text-[9px] font-mono">
                <div />
                {[1, 2, 3, 4, 5].map(i => (
                  <div key={i} className="text-center text-gray-600 py-0.5">I:{i}</div>
                ))}
                {[1, 2, 3, 4, 5].map(p => (
                  <>
                    <div key={`p${p}`} className="text-gray-600 py-0.5">P:{p}</div>
                    {[1, 2, 3, 4, 5].map(i => (
                      <div key={`c${p}${i}`} className={`h-6 rounded-sm ${riskMatrixColor(p, i)} flex items-center justify-center text-white text-[8px]`}>
                        {p * i}
                      </div>
                    ))}
                  </>
                ))}
              </div>
            </div>

            <div className="border-t border-gray-700 pt-2">
              <div className="text-[10px] text-gray-500 font-bold mb-1">NUEVO RIESGO</div>
              <div className="space-y-1">
                <input
                  value={newRisk.hazard}
                  onChange={e => setNewRisk({ ...newRisk, hazard: e.target.value })}
                  placeholder="Peligro"
                  className="w-full bg-gray-800 text-gray-300 text-[10px] rounded px-2 py-1 border border-gray-700"
                />
                <div className="flex gap-1">
                  <select
                    value={newRisk.probability}
                    onChange={e => setNewRisk({ ...newRisk, probability: Number(e.target.value) as 1 | 2 | 3 | 4 | 5 })}
                    className="bg-gray-800 text-gray-300 text-[10px] rounded px-1 py-1 border border-gray-700"
                  >
                    {[1, 2, 3, 4, 5].map(v => <option key={v} value={v}>P:{v}</option>)}
                  </select>
                  <select
                    value={newRisk.impact}
                    onChange={e => setNewRisk({ ...newRisk, impact: Number(e.target.value) as 1 | 2 | 3 | 4 | 5 })}
                    className="bg-gray-800 text-gray-300 text-[10px] rounded px-1 py-1 border border-gray-700"
                  >
                    {[1, 2, 3, 4, 5].map(v => <option key={v} value={v}>I:{v}</option>)}
                  </select>
                </div>
                <input
                  value={newRisk.mitigation}
                  onChange={e => setNewRisk({ ...newRisk, mitigation: e.target.value })}
                  placeholder="Mitigacion"
                  className="w-full bg-gray-800 text-gray-300 text-[10px] rounded px-2 py-1 border border-gray-700"
                />
                <button
                  onClick={saveRisk}
                  className="w-full bg-green-800 hover:bg-green-700 text-green-100 text-[10px] px-2 py-1 rounded transition-colors"
                >
                  Anadir Riesgo
                </button>
              </div>
            </div>
          </div>
        )}

        {tab === "sync" && (
          <div className="space-y-2">
            <div className="text-[10px] text-gray-500 font-bold mb-1">MATRIZ DE SINCRONIZACION</div>
            <div className="overflow-x-auto">
              <table className="w-full text-[9px] font-mono">
                <thead>
                  <tr className="text-gray-500">
                    <th className="text-left py-0.5 border-b border-gray-700">Hora</th>
                    <th className="text-center py-0.5 border-b border-gray-700">Alfa</th>
                    <th className="text-center py-0.5 border-b border-gray-700">Bravo</th>
                    <th className="text-center py-0.5 border-b border-gray-700">Charlie</th>
                    <th className="text-center py-0.5 border-b border-gray-700">Echo</th>
                  </tr>
                </thead>
                <tbody>
                  {[
                    { time: "0000Z", alfa: "Preparacion", bravo: "Preparacion", charlie: "Recon", echo: "Standby" },
                    { time: "0200Z", alfa: "Desplazamiento", bravo: "Desplazamiento", charlie: "Recon", echo: "Standby" },
                    { time: "0400Z", alfa: "Punto Bravo", bravo: "Posicion", charlie: "Contacto", echo: "Ready" },
                    { time: "0600Z", alfa: "Asalto F1", bravo: "Apoyo", charlie: "Flanco", echo: "CAS" },
                    { time: "0800Z", alfa: "Consolidar", bravo: "Consolidar", charlie: "Explorar", echo: "Reabast." },
                  ].map((row, i) => (
                    <tr key={i} className="text-gray-400">
                      <td className="py-0.5 text-green-400 font-bold">{row.time}</td>
                      <td className="text-center py-0.5">{row.alfa}</td>
                      <td className="text-center py-0.5">{row.bravo}</td>
                      <td className="text-center py-0.5">{row.charlie}</td>
                      <td className="text-center py-0.5">{row.echo}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
