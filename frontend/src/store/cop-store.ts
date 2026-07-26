import { create } from "zustand";
import {
  COPState, Alert, IntelReport, ThreatAssessment, MissionEvent, COPModule,
  TacticalMessage, TerrainAnalysisData, Supply, Personnel,
  MEDEVACRequest, MaintenanceRequest, AfterActionReview, GeneratedReport,
  ThreatPredictionData, OPORD, COA, VoiceCommandEntry,
  WidgetConfig, DashboardLayout, UnitPosition, SensorNode, PlanningEntry, LogisticsEntry,
} from "@/lib/cop-types";
import { apiFetch, apiRequest } from "@/lib/api";
import {
  mapAlert, mapIntelProduct, mapEarlyWarning, mapMessage,
  mapSupply, mapPersonnel, mapMedevac, mapMaintenance,
  mapReport, mapAAR, mapOPORD, mapPrediction, mergeUnits, mapSensor,
  type BackendAlert, type BackendIntelProduct, type BackendEarlyWarning,
  type BackendMessage, type BackendSupply, type BackendPersonnelResponse,
  type BackendMedevac, type BackendMaintenance, type BackendReport,
  type BackendAAR, type BackendOPORD, type BackendPrediction,
  type BackendOrbatUnit, type BackendBlueForce, type BackendSensorSource,
} from "@/lib/mappers";

const defaultWidgets: WidgetConfig[] = [
  { id: "w1", component: "TacticalMap", title: "Mapa Tactico", x: 0, y: 0, width: 6, height: 4, minimized: false },
  { id: "w2", component: "IntelFeed", title: "Feed Intel", x: 6, y: 0, width: 3, height: 2, minimized: false },
  { id: "w3", component: "ThreatPanel", title: "Amenazas", x: 6, y: 2, width: 3, height: 2, minimized: false },
  { id: "w4", component: "MessagingPanel", title: "Mensajeria", x: 9, y: 0, width: 3, height: 4, minimized: false },
];

export type COPActivePanel = "map" | "messages" | "terrain" | "logistics" | "aar" | "reports" | "threat-pred" | "planning" | "voice" | "multi-monitor";

interface COPStore {
  state: COPState;
  classification: string;
  activePanel: COPActivePanel;
  messages: TacticalMessage[];
  terrainAnalyses: TerrainAnalysisData[];
  supplies: Supply[];
  personnel: Personnel[];
  medevacRequests: MEDEVACRequest[];
  maintenanceRequests: MaintenanceRequest[];
  aar: AfterActionReview | null;
  threatPredictions: ThreatPredictionData[];
  opords: OPORD[];
  coas: COA[];
  reports: GeneratedReport[];
  voiceCommands: VoiceCommandEntry[];
  voiceStatus: "IDLE" | "LISTENING" | "PROCESSING";
  widgets: WidgetConfig[];
  layouts: DashboardLayout[];
  intelItems: IntelReport[];
  planning: PlanningEntry[];
  logistics: LogisticsEntry[];
  loading: boolean;
  error: string | null;
  lastFetch: number | null;
  setAlerts: (a: Alert[]) => void;
  setIntelFeed: (i: IntelReport[]) => void;
  setThreats: (t: ThreatAssessment[]) => void;
  setUnits: (u: UnitPosition[]) => void;
  setSensors: (s: SensorNode[]) => void;
  setMessages: (m: TacticalMessage[]) => void;
  setSupplies: (s: Supply[]) => void;
  setPersonnel: (p: Personnel[]) => void;
  setReports: (r: GeneratedReport[]) => void;
  setAAR: (a: AfterActionReview | null) => void;
  addAlert: (a: Alert) => void;
  addIntel: (i: IntelReport) => void;
  addThreat: (t: ThreatAssessment) => void;
  addEvent: (e: MissionEvent) => void;
  setModuleStatus: (id: string, status: COPModule["status"]) => void;
  setClassification: (c: string) => void;
  getAlertsBySeverity: (severity: string) => Alert[];
  setActivePanel: (p: COPActivePanel) => void;
  addMessage: (m: TacticalMessage) => void;
  acknowledgeMessage: (id: string) => void;
  addTerrainAnalysis: (t: TerrainAnalysisData) => void;
  clearTerrainAnalyses: () => void;
  addSupply: (s: Supply) => void;
  updateSupply: (id: string, updates: Partial<Supply>) => void;
  addPersonnel: (p: Personnel) => void;
  updatePersonnel: (id: string, updates: Partial<Personnel>) => void;
  addMEDEVAC: (m: MEDEVACRequest) => void;
  addMaintenance: (m: MaintenanceRequest) => void;
  updateAAR: (updates: Partial<AfterActionReview>) => void;
  addOPORD: (o: OPORD) => void;
  updateOPORD: (id: string, updates: Partial<OPORD>) => void;
  addCOA: (c: COA) => void;
  addReport: (r: GeneratedReport) => void;
  addThreatPrediction: (t: ThreatPredictionData) => void;
  addVoiceCommand: (v: VoiceCommandEntry) => void;
  setVoiceStatus: (s: "IDLE" | "LISTENING" | "PROCESSING") => void;
  updateWidgets: (w: WidgetConfig[]) => void;
  saveLayout: (name: string) => void;
  loadLayout: (id: string) => void;
  fetchAll: () => Promise<void>;
  fetchAlerts: () => Promise<void>;
  fetchIntel: () => Promise<void>;
  fetchThreats: () => Promise<void>;
  fetchMessages: () => Promise<void>;
  fetchUnits: () => Promise<void>;
  fetchSensors: () => Promise<void>;
  fetchReports: () => Promise<void>;
  fetchPlanning: () => Promise<void>;
  fetchAAR: (aarId?: string) => Promise<void>;
  fetchLogistics: () => Promise<void>;
}

const emptyState: COPState = {
  alerts: [],
  units: [],
  intelFeed: [],
  threats: [],
  bdaReports: [],
  agentReports: [],
  psyopsMessages: [],
  sensors: [],
  wargamingResults: [],
  timeline: [],
  modules: [],
};

export const useCOPStore = create<COPStore>((set, get) => ({
  state: emptyState,
  classification: "RESTRICTED",
  activePanel: "map",
  messages: [],
  terrainAnalyses: [],
  supplies: [],
  personnel: [],
  medevacRequests: [],
  maintenanceRequests: [],
  aar: null,
  threatPredictions: [],
  opords: [],
  coas: [],
  reports: [],
  voiceCommands: [],
  voiceStatus: "IDLE",
  widgets: defaultWidgets,
  layouts: [
    { id: "l1", name: "C2 Principal", preset: "c2", widgets: defaultWidgets },
  ],
  intelItems: [],
  planning: [],
  logistics: [],
  loading: false,
  error: null,
  lastFetch: null,

  setAlerts: (alerts) => set(s => ({ state: { ...s.state, alerts } })),
  setIntelFeed: (intelFeed) => set(s => ({ state: { ...s.state, intelFeed } })),
  setThreats: (threats) => set(s => ({ state: { ...s.state, threats } })),
  setUnits: (units) => set(s => ({ state: { ...s.state, units } })),
  setSensors: (sensors) => set(s => ({ state: { ...s.state, sensors } })),
  setMessages: (messages) => set(() => ({ messages })),
  setSupplies: (supplies) => set(() => ({ supplies })),
  setPersonnel: (personnel) => set(() => ({ personnel })),
  setReports: (reports) => set(() => ({ reports })),
  setAAR: (aar) => set(() => ({ aar })),
  addAlert: (a) => set(s => ({ state: { ...s.state, alerts: [a, ...s.state.alerts].slice(0, 100) } })),
  addIntel: (i) => set(s => ({ state: { ...s.state, intelFeed: [i, ...s.state.intelFeed].slice(0, 50) } })),
  addThreat: (t) => set(s => ({ state: { ...s.state, threats: [t, ...s.state.threats].slice(0, 20) } })),
  addEvent: (e) => set(s => ({ state: { ...s.state, timeline: [e, ...s.state.timeline].slice(0, 200) } })),
  setModuleStatus: (id, status) => set(s => ({
    state: {
      ...s.state,
      modules: s.state.modules.map(m => m.id === id ? { ...m, status } : m),
    },
  })),
  setClassification: (c) => set(() => ({ classification: c })),
  getAlertsBySeverity: (severity: string): Alert[] => {
    return get().state.alerts.filter((a: Alert) => a.severity === severity);
  },
  setActivePanel: (p) => set(() => ({ activePanel: p })),
  addMessage: (m) => set(s => ({ messages: [m, ...s.messages] })),
  acknowledgeMessage: (id) => set(s => ({
    messages: s.messages.map(m => m.id === id ? { ...m, acknowledged: true } : m),
  })),
  addTerrainAnalysis: (t) => set(s => ({ terrainAnalyses: [t, ...s.terrainAnalyses] })),
  clearTerrainAnalyses: () => set(() => ({ terrainAnalyses: [] })),
  addSupply: (sup) => set(s => ({ supplies: [...s.supplies, sup] })),
  updateSupply: (id, updates) => set(s => ({
    supplies: s.supplies.map(sup => sup.id === id ? { ...sup, ...updates } : sup),
  })),
  addPersonnel: (p) => set(s => ({ personnel: [...s.personnel, p] })),
  updatePersonnel: (id, updates) => set(s => ({
    personnel: s.personnel.map(p => p.id === id ? { ...p, ...updates } : p),
  })),
  addMEDEVAC: (m) => set(s => ({ medevacRequests: [m, ...s.medevacRequests] })),
  addMaintenance: (m) => set(s => ({ maintenanceRequests: [m, ...s.maintenanceRequests] })),
  updateAAR: (updates) => set(s => (s.aar ? { aar: { ...s.aar, ...updates } } : {})),
  addOPORD: (o) => set(s => ({ opords: [o, ...s.opords.filter(x => x.id !== o.id)] })),
  updateOPORD: (id, updates) => set(s => ({
    opords: s.opords.map(o => o.id === id ? { ...o, ...updates } : o),
  })),
  addCOA: (c) => set(s => ({ coas: [...s.coas, c] })),
  addReport: (r) => set(s => ({ reports: [r, ...s.reports] })),
  addThreatPrediction: (t) => set(s => ({
    threatPredictions: [t, ...s.threatPredictions.filter(x => x.unitId !== t.unitId)],
  })),
  addVoiceCommand: (v) => set(s => ({ voiceCommands: [v, ...s.voiceCommands].slice(0, 50) })),
  setVoiceStatus: (st) => set(() => ({ voiceStatus: st })),
  updateWidgets: (w) => set(() => ({ widgets: w })),
  saveLayout: (name) => set(s => {
    const newLayout: DashboardLayout = {
      id: `l${Date.now()}`,
      name,
      preset: "custom",
      widgets: [...s.widgets],
    };
    return { layouts: [...s.layouts, newLayout] };
  }),
  loadLayout: (id) => set(s => {
    const layout = s.layouts.find(l => l.id === id);
    return layout ? { widgets: [...layout.widgets] } : {};
  }),

  fetchAll: async () => {
    set({ loading: true, error: null });
    try {
      await Promise.all([
        get().fetchAlerts(),
        get().fetchIntel(),
        get().fetchThreats(),
        get().fetchMessages(),
        get().fetchUnits(),
        get().fetchSensors(),
        get().fetchReports(),
        get().fetchLogistics(),
      ]);
      set({ loading: false, lastFetch: Date.now() });
    } catch (e) {
      const msg = e instanceof Error ? e.message : "Error en fetchAll";
      set({ loading: false, error: msg });
    }
  },

  fetchAlerts: async () => {
    try {
      const data = await apiRequest<BackendAlert[]>("/api/v1/c2/?limit=50");
      const alerts = data.map(mapAlert);
      set(s => ({ state: { ...s.state, alerts } }));
    } catch { /* individual errors handled by components */ }
  },

  fetchIntel: async () => {
    try {
      const data = await apiRequest<BackendIntelProduct[]>("/api/v1/c2/products?limit=20");
      const intelFeed = data.map(mapIntelProduct);
      set(s => ({ state: { ...s.state, intelFeed }, intelItems: intelFeed }));
    } catch { /* handled by components */ }
  },

  fetchThreats: async () => {
    try {
      const units = get().state.units;
      if (units.length === 0) return;
      const data = await apiRequest<BackendEarlyWarning[]>("/api/v1/prediction/early-warning", {
        method: "POST",
        body: { friendly_locations: units.map(u => ({ lat: u.lat, lon: u.lon })), threat_radius_km: 50 },
      });
      const threats = data.map(mapEarlyWarning);
      set(s => ({ state: { ...s.state, threats } }));
    } catch { /* handled by components */ }
  },

  fetchMessages: async () => {
    try {
      const data = await apiRequest<BackendMessage[]>(`/api/v1/messaging/history?user_id=OPERATOR&limit=100`);
      const messages = data.map(mapMessage);
      set(() => ({ messages }));
    } catch { /* handled by components */ }
  },

  fetchUnits: async () => {
    try {
      const [orbat, blueForce] = await Promise.all([
        apiRequest<BackendOrbatUnit[]>("/api/v2/c2/orbat"),
        apiRequest<BackendBlueForce[]>("/api/v2/c2/blue-force/active"),
      ]);
      const units = mergeUnits(orbat, blueForce);
      set(s => ({ state: { ...s.state, units } }));
    } catch { /* handled by components */ }
  },

  fetchSensors: async () => {
    try {
      const data = await apiRequest<BackendSensorSource[]>("/api/v1/c2/status");
      const sensors = data.map(mapSensor);
      set(s => ({ state: { ...s.state, sensors } }));
    } catch { /* handled by components */ }
  },

  fetchReports: async () => {
    try {
      const data = await apiRequest<BackendReport[]>("/api/v1/reports?limit=50");
      const reports = data.map(mapReport);
      set(() => ({ reports }));
    } catch { /* handled by components */ }
  },

  fetchPlanning: async () => {
    try {
      const opords = get().opords;
      set(() => ({
        planning: opords.map(o => ({
          id: o.id,
          type: "OPORD" as const,
          title: o.operationName,
          status: o.status,
          timestamp: o.createdAt,
        })),
      }));
    } catch { /* handled */ }
  },

  fetchAAR: async (aarId?: string) => {
    try {
      if (!aarId) {
        set(() => ({ aar: null }));
        return;
      }
      const data = await apiRequest<BackendAAR>(`/api/v1/aar/${encodeURIComponent(aarId)}`);
      set(() => ({ aar: mapAAR(data) }));
    } catch { /* handled */ }
  },

  fetchLogistics: async () => {
    try {
      const supData = await apiRequest<BackendSupply[]>("/api/v1/logistics/supplies");
      const persData = await apiRequest<BackendPersonnelResponse>("/api/v1/logistics/personnel");
      const supplies = supData.map(mapSupply);
      const personnel = persData.personnel.map(mapPersonnel);
      const logistics: LogisticsEntry[] = [
        ...supplies.map(s => ({ id: s.id, type: "SUPPLY" as const, description: `${s.type}: ${s.quantity} ${s.unit}`, status: s.status })),
        ...personnel.map(p => ({ id: p.id, type: "PERSONNEL" as const, description: `${p.rank} ${p.name}`, status: p.status })),
      ];
      set(() => ({ supplies, personnel, logistics }));
    } catch { /* handled */ }
  },
}));
