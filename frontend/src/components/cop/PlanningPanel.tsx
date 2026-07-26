"use client";
import { useState } from "react";
import { FileText, Target, Shield, GitBranch, Plus, FolderOpen, BarChart3 } from "lucide-react";
import { useCOPStore } from "@/store/cop-store";
import { apiFetch, apiErrorMessage } from "@/lib/api";
import { mapOPORD, type BackendOPORD } from "@/lib/mappers";
import type { OPORD, COA, COAComparison, OPORDRiskAssessment, OPORDSyncMatrix } from "@/lib/cop-types";

type PlanningTab = "opord" | "coa" | "risk" | "sync";

const PARAGRAPH_LABELS: Record<string, string> = {
  paragraph_1_situation: "1. SITUACION",
  paragraph_2_mission: "2. MISION",
  paragraph_3_execution: "3. EJECUCION",
  paragraph_4_sustainment: "4. SOSTENIMIENTO",
  paragraph_5_command_signal: "5. MANDO Y SENALES",
};

const COA_CRITERIA = ["suitability", "feasibility", "acceptability", "distinguishability", "completeness"] as const;

function paragraphText(p: Record<string, unknown>): string {
  if (typeof p.summary === "string") return p.summary;
  return Object.keys(p).length > 0 ? JSON.stringify(p, null, 1) : "";
}

export default function PlanningPanel() {
  const { opords, coas, addOPORD, updateOPORD, addCOA } = useCOPStore();
  const [tab, setTab] = useState<PlanningTab>("opord");
  const [editingOPORD, setEditingOPORD] = useState<OPORD | null>(null);
  const [paragraphDrafts, setParagraphDrafts] = useState<Record<string, string>>({});
  const [newOpName, setNewOpName] = useState("");
  const [newOpClass, setNewOpClass] = useState("SECRET");
  const [loadId, setLoadId] = useState("");
  const [newCOA, setNewCOA] = useState({ name: "", description: "", resources: "", duration: "" });
  const [newCOAScores, setNewCOAScores] = useState<Record<string, number>>(
    Object.fromEntries(COA_CRITERIA.map(c => [c, 5])),
  );
  const [comparison, setComparison] = useState<COAComparison | null>(null);
  const [riskOpordId, setRiskOpordId] = useState("");
  const [riskAssessment, setRiskAssessment] = useState<OPORDRiskAssessment | null>(null);
  const [syncOpordId, setSyncOpordId] = useState("");
  const [syncMatrix, setSyncMatrix] = useState<OPORDSyncMatrix | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const tabs = [
    { id: "opord" as const, label: "OPORD", icon: FileText },
    { id: "coa" as const, label: "COA", icon: Target },
    { id: "risk" as const, label: "Riesgos", icon: Shield },
    { id: "sync" as const, label: "Sincronizacion", icon: GitBranch },
  ];

  const createOPORD = async () => {
    if (!newOpName.trim()) return;
    setBusy(true);
    setError(null);
    try {
      const result = await apiFetch<BackendOPORD>("/api/v1/planning/create", {
        method: "POST",
        body: { operation_name: newOpName.trim(), classification: newOpClass, created_by: "OPERATOR" },
      });
      addOPORD(mapOPORD(result));
      setNewOpName("");
    } catch (e) {
      setError(apiErrorMessage(e));
    } finally {
      setBusy(false);
    }
  };

  const loadOPORD = async (id: string) => {
    if (!id.trim()) return;
    setBusy(true);
    setError(null);
    try {
      const result = await apiFetch<BackendOPORD>(`/api/v1/planning/${encodeURIComponent(id.trim())}`);
      addOPORD(mapOPORD(result));
      setLoadId("");
    } catch (e) {
      setError(apiErrorMessage(e));
    } finally {
      setBusy(false);
    }
  };

  const startEdit = (o: OPORD) => {
    setEditingOPORD(o);
    const drafts: Record<string, string> = {};
    for (const key of Object.keys(PARAGRAPH_LABELS)) {
      drafts[key] = paragraphText(o.paragraphs[key] ?? {});
    }
    setParagraphDrafts(drafts);
  };

  const saveOPORD = async () => {
    if (!editingOPORD) return;
    setBusy(true);
    setError(null);
    try {
      for (const key of Object.keys(PARAGRAPH_LABELS)) {
        const text = paragraphDrafts[key] ?? "";
        const current = paragraphText(editingOPORD.paragraphs[key] ?? {});
        if (text !== current) {
          await apiFetch(`/api/v1/planning/${editingOPORD.id}/paragraph/${key}`, {
            method: "PUT",
            body: { data: { summary: text } },
          });
        }
      }
      const refreshed = await apiFetch<BackendOPORD>(`/api/v1/planning/${editingOPORD.id}`);
      updateOPORD(editingOPORD.id, mapOPORD(refreshed));
      setEditingOPORD(null);
    } catch (e) {
      setError(apiErrorMessage(e));
    } finally {
      setBusy(false);
    }
  };

  const saveCOA = () => {
    if (!newCOA.name.trim()) return;
    const total = Object.values(newCOAScores).reduce((a, b) => a + b, 0);
    addCOA({
      id: `coa${Date.now()}`,
      name: newCOA.name,
      description: newCOA.description,
      successProbability: Math.round((total / (COA_CRITERIA.length * 10)) * 100) / 100,
      risk: 10 - Math.round(total / COA_CRITERIA.length),
      resources: newCOA.resources,
      duration: newCOA.duration,
      scores: { ...newCOAScores },
    });
    setNewCOA({ name: "", description: "", resources: "", duration: "" });
    setNewCOAScores(Object.fromEntries(COA_CRITERIA.map(c => [c, 5])));
  };

  const compareCOAs = async () => {
    if (coas.length === 0) return;
    setBusy(true);
    setError(null);
    try {
      const result = await apiFetch<COAComparison>("/api/v1/planning/coa-compare", {
        method: "POST",
        body: { coa_list: coas.map(c => ({ id: c.id, name: c.name, ...c.scores })) },
      });
      setComparison(result);
    } catch (e) {
      setError(apiErrorMessage(e));
    } finally {
      setBusy(false);
    }
  };

  const runRiskAssessment = async () => {
    if (!riskOpordId) return;
    setBusy(true);
    setError(null);
    try {
      const result = await apiFetch<OPORDRiskAssessment>(`/api/v1/planning/${riskOpordId}/risk-assessment`);
      setRiskAssessment(result);
    } catch (e) {
      setError(apiErrorMessage(e));
    } finally {
      setBusy(false);
    }
  };

  const runSyncMatrix = async () => {
    if (!syncOpordId) return;
    setBusy(true);
    setError(null);
    try {
      const result = await apiFetch<OPORDSyncMatrix>(`/api/v1/planning/${syncOpordId}/sync-matrix`);
      setSyncMatrix(result);
    } catch (e) {
      setError(apiErrorMessage(e));
    } finally {
      setBusy(false);
    }
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
              onClick={() => { setTab(t.id); setError(null); }}
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
        {error && <div className="text-[10px] font-mono text-red-400 mb-1">{error}</div>}

        {tab === "opord" && (
          <div className="space-y-2">
            {!editingOPORD ? (
              <>
                <div className="space-y-1">
                  <input
                    value={newOpName}
                    onChange={e => setNewOpName(e.target.value)}
                    placeholder="Nombre de operacion"
                    className="w-full bg-gray-800 text-gray-300 text-xs rounded px-2 py-1 border border-gray-700"
                  />
                  <div className="flex gap-1">
                    <select
                      value={newOpClass}
                      onChange={e => setNewOpClass(e.target.value)}
                      className="flex-1 bg-gray-800 text-gray-300 text-[10px] rounded px-1 py-1 border border-gray-700"
                    >
                      <option value="RESTRICTED">RESTRINGIDO</option>
                      <option value="CONFIDENTIAL">CONFIDENCIAL</option>
                      <option value="SECRET">SECRETO</option>
                      <option value="TOP_SECRET">ALTO SECRETO</option>
                    </select>
                    <button
                      onClick={() => void createOPORD()}
                      disabled={busy || !newOpName.trim()}
                      className="bg-green-800 hover:bg-green-700 disabled:opacity-50 text-green-100 text-[10px] px-2 py-1 rounded flex items-center gap-1 transition-colors"
                    >
                      <Plus size={10} /> Nueva OPORD
                    </button>
                  </div>
                  <div className="flex gap-1">
                    <input
                      value={loadId}
                      onChange={e => setLoadId(e.target.value)}
                      placeholder="Cargar OPORD por ID..."
                      className="flex-1 bg-gray-800 text-gray-300 text-[10px] rounded px-2 py-1 border border-gray-700"
                    />
                    <button
                      onClick={() => void loadOPORD(loadId)}
                      disabled={busy || !loadId.trim()}
                      className="bg-gray-800 hover:bg-gray-700 disabled:opacity-50 text-gray-300 text-[10px] px-2 py-1 rounded border border-gray-700 flex items-center gap-1 transition-colors"
                    >
                      <FolderOpen size={10} /> Cargar
                    </button>
                  </div>
                </div>
                {opords.length === 0 && (
                  <div className="text-xs font-mono text-gray-600">Sin OPORDs cargadas</div>
                )}
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
                    <div className="text-[10px] text-gray-600 mb-1">
                      {o.classification} — ID: {o.id}
                    </div>
                    <button
                      onClick={() => startEdit(o)}
                      className="text-[10px] text-gray-500 hover:text-gray-300"
                    >
                      Editar...
                    </button>
                  </div>
                ))}
              </>
            ) : (
              <div className="space-y-1">
                <div className="text-green-400 text-xs font-bold font-mono">{editingOPORD.operationName}</div>
                {Object.entries(PARAGRAPH_LABELS).map(([key, label]) => (
                  <div key={key}>
                    <label className="text-[10px] text-gray-500 font-bold">{label}</label>
                    <textarea
                      value={paragraphDrafts[key] ?? ""}
                      onChange={e => setParagraphDrafts({ ...paragraphDrafts, [key]: e.target.value })}
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
                    onClick={() => void saveOPORD()}
                    disabled={busy}
                    className="flex-1 bg-green-800 hover:bg-green-700 disabled:opacity-50 text-green-100 text-[10px] px-2 py-1 rounded transition-colors"
                  >
                    {busy ? "Guardando..." : "Guardar"}
                  </button>
                </div>
              </div>
            )}
          </div>
        )}

        {tab === "coa" && (
          <div className="space-y-2">
            <div className="space-y-1">
              {coas.length === 0 && (
                <div className="text-xs font-mono text-gray-600">Sin COAs definidas</div>
              )}
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
                <div className="grid grid-cols-5 gap-1">
                  {COA_CRITERIA.map(crit => (
                    <div key={crit}>
                      <div className="text-[8px] text-gray-600 uppercase truncate">{crit.slice(0, 6)}</div>
                      <select
                        value={newCOAScores[crit] ?? 5}
                        onChange={e => setNewCOAScores({ ...newCOAScores, [crit]: Number(e.target.value) })}
                        className="w-full bg-gray-800 text-gray-300 text-[10px] rounded px-1 py-0.5 border border-gray-700"
                      >
                        {[1, 2, 3, 4, 5, 6, 7, 8, 9, 10].map(v => <option key={v} value={v}>{v}</option>)}
                      </select>
                    </div>
                  ))}
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
              <button
                onClick={() => void compareCOAs()}
                disabled={busy || coas.length === 0}
                className="w-full bg-blue-900/30 hover:bg-blue-900/50 disabled:opacity-50 text-blue-400 text-[10px] px-2 py-1 rounded border border-blue-800 flex items-center justify-center gap-1 transition-colors"
              >
                <BarChart3 size={10} /> Comparar COAs (backend)
              </button>
              {comparison && (
                <div className="mt-2 space-y-1">
                  <div className="text-[10px] text-green-400 font-bold">{comparison.recommendation}</div>
                  <div className="overflow-x-auto">
                    <table className="w-full text-[10px] font-mono">
                      <thead>
                        <tr className="text-gray-500">
                          <th className="text-left py-0.5">COA</th>
                          {comparison.criteria.map(c => (
                            <th key={c} className="text-center py-0.5">{c.slice(0, 4).toUpperCase()}</th>
                          ))}
                          <th className="text-center py-0.5">TOTAL</th>
                        </tr>
                      </thead>
                      <tbody>
                        {comparison.coa_evaluations.map(ev => (
                          <tr key={ev.coa_id} className="text-gray-300">
                            <td className="py-0.5">{ev.name}</td>
                            {comparison.criteria.map(c => (
                              <td key={c} className="text-center">{ev.scores[c] ?? "—"}</td>
                            ))}
                            <td className="text-center text-green-400 font-bold">{ev.total_score}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              )}
            </div>
          </div>
        )}

        {tab === "risk" && (
          <div className="space-y-2">
            <div className="flex gap-1">
              <select
                value={riskOpordId}
                onChange={e => setRiskOpordId(e.target.value)}
                className="flex-1 bg-gray-800 text-gray-300 text-[10px] rounded px-1 py-1 border border-gray-700"
              >
                <option value="">Seleccionar OPORD...</option>
                {opords.map(o => (
                  <option key={o.id} value={o.id}>{o.operationName}</option>
                ))}
              </select>
              <button
                onClick={() => void runRiskAssessment()}
                disabled={busy || !riskOpordId}
                className="bg-yellow-900/30 hover:bg-yellow-900/50 disabled:opacity-50 text-yellow-400 text-[10px] px-2 py-1 rounded border border-yellow-800 transition-colors"
              >
                Evaluar
              </button>
            </div>

            {opords.length === 0 && (
              <div className="text-xs font-mono text-gray-600">Cargue una OPORD para evaluar riesgos</div>
            )}

            {riskAssessment && (
              <div className="space-y-1">
                <div className="flex items-center justify-between">
                  <span className="text-[10px] text-gray-500 font-bold">RIESGO GLOBAL</span>
                  <span className={`text-[10px] font-bold px-1.5 py-0.5 rounded ${
                    riskAssessment.overall_risk_level === "HIGH" ? "text-red-400 bg-red-900/20" :
                    riskAssessment.overall_risk_level === "MEDIUM" ? "text-yellow-400 bg-yellow-900/20" :
                    "text-green-400 bg-green-900/20"
                  }`}>
                    {riskAssessment.overall_risk_level}
                  </span>
                </div>
                <div className="flex gap-2 text-[10px] font-mono">
                  <span className="text-red-400">Altos: {riskAssessment.risk_matrix.high}</span>
                  <span className="text-yellow-400">Medios: {riskAssessment.risk_matrix.medium}</span>
                  <span className="text-green-400">Bajos: {riskAssessment.risk_matrix.low}</span>
                </div>
                {riskAssessment.risks.map(r => (
                  <div key={r.id} className="text-xs font-mono p-2 rounded bg-gray-800/50 border border-gray-700">
                    <div className="flex items-center justify-between mb-0.5">
                      <span className="text-gray-300 font-bold">{r.category}</span>
                      <span className={`text-[10px] px-1.5 py-0.5 rounded ${
                        r.risk_level === "HIGH" ? "text-red-400 bg-red-900/20" :
                        r.risk_level === "MEDIUM" ? "text-yellow-400 bg-yellow-900/20" :
                        "text-green-400 bg-green-900/20"
                      }`}>
                        {r.risk_level}
                      </span>
                    </div>
                    <div className="text-[10px] text-gray-500">
                      {r.hazard} — P:{r.probability} S:{r.severity} → residual {r.residual_risk}
                    </div>
                  </div>
                ))}
                {riskAssessment.recommendations.length > 0 && (
                  <div>
                    <div className="text-[10px] text-gray-500 font-bold">RECOMENDACIONES</div>
                    {riskAssessment.recommendations.map((r, i) => (
                      <div key={i} className="text-[10px] font-mono text-gray-400">- {r}</div>
                    ))}
                  </div>
                )}
              </div>
            )}
          </div>
        )}

        {tab === "sync" && (
          <div className="space-y-2">
            <div className="flex gap-1">
              <select
                value={syncOpordId}
                onChange={e => setSyncOpordId(e.target.value)}
                className="flex-1 bg-gray-800 text-gray-300 text-[10px] rounded px-1 py-1 border border-gray-700"
              >
                <option value="">Seleccionar OPORD...</option>
                {opords.map(o => (
                  <option key={o.id} value={o.id}>{o.operationName}</option>
                ))}
              </select>
              <button
                onClick={() => void runSyncMatrix()}
                disabled={busy || !syncOpordId}
                className="bg-green-900/30 hover:bg-green-900/50 disabled:opacity-50 text-green-400 text-[10px] px-2 py-1 rounded border border-green-800 transition-colors"
              >
                Generar
              </button>
            </div>

            {opords.length === 0 && (
              <div className="text-xs font-mono text-gray-600">Cargue una OPORD para generar la matriz</div>
            )}

            {syncMatrix && (
              <div className="space-y-1">
                <div className="text-[10px] text-gray-500 font-bold">
                  MATRIZ DE SINCRONIZACION — {syncMatrix.operation_name}
                </div>
                <div className="overflow-x-auto">
                  <table className="w-full text-[9px] font-mono">
                    <thead>
                      <tr className="text-gray-500">
                        <th className="text-left py-0.5 border-b border-gray-700">Fase</th>
                        {syncMatrix.synchronization[0]
                          ? Object.keys(syncMatrix.synchronization[0].tasks).map(t => (
                              <th key={t} className="text-center py-0.5 border-b border-gray-700">{t}</th>
                            ))
                          : null}
                      </tr>
                    </thead>
                    <tbody>
                      {syncMatrix.synchronization.map(row => (
                        <tr key={row.phase} className="text-gray-400">
                          <td className="py-0.5 text-green-400 font-bold">{row.phase}</td>
                          {Object.values(row.tasks).map((task, i) => (
                            <td key={i} className="text-center py-0.5">{task.description}</td>
                          ))}
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
