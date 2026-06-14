import { create } from "zustand";
import {
  COPState, Alert, IntelReport, ThreatAssessment, MissionEvent, COPModule,
  TacticalMessage, Conversation, TerrainAnalysisData, Supply, Personnel,
  MEDEVACRequest, MaintenanceRequest, AfterActionReview, GeneratedReport,
  ThreatPredictionData, OPORD, COA, RiskEntry, VoiceCommandEntry,
  WidgetConfig, DashboardLayout,
} from "@/lib/cop-types";

const defaultModules: COPModule[] = [
  { id: "c2", name: "C2", status: "operational", color: "text-green-400" },
  { id: "satellite", name: "SAT", status: "operational", color: "text-green-400" },
  { id: "osint", name: "OSINT", status: "operational", color: "text-green-400" },
  { id: "intel", name: "INTEL", status: "degraded", color: "text-yellow-400" },
  { id: "agents", name: "AGENTS", status: "operational", color: "text-green-400" },
  { id: "tactical", name: "TACTICAL", status: "operational", color: "text-green-400" },
  { id: "sensors", name: "SENSORS", status: "operational", color: "text-green-400" },
  { id: "ml", name: "ML", status: "operational", color: "text-green-400" },
  { id: "cop", name: "COP", status: "operational", color: "text-green-400" },
];

const mockAlerts: Alert[] = [
  { id: "a1", severity: "critical", source: "SIGINT", message: "Emisiones radar no identificadas en sector Delta-7", timestamp: "2026-06-14T03:22:00Z", acknowledged: false },
  { id: "a2", severity: "high", source: "SAT", message: "Movimiento de tropas detectado via satelital — 40.2°N 3.5°E", timestamp: "2026-06-14T03:18:00Z", acknowledged: false },
  { id: "a3", severity: "medium", source: "OSINT", message: "Incremento de comunicaciones cifradas en banda HF", timestamp: "2026-06-14T03:15:00Z", acknowledged: true },
  { id: "a4", severity: "low", source: "SENSOR", message: "Nodo sensor-14 battery por debajo del 20%", timestamp: "2026-06-14T03:10:00Z", acknowledged: true },
  { id: "a5", severity: "high", source: "HUMINT", message: "Fuente reporta actividad inusual en base subordinada", timestamp: "2026-06-14T02:55:00Z", acknowledged: false },
  { id: "a6", severity: "critical", source: "C2", message: "Intento de intrusion en canal seguro Charlie-9", timestamp: "2026-06-14T02:48:00Z", acknowledged: false },
  { id: "a7", severity: "medium", source: "CYBER", message: "Anomalia en trafico de red — segmento Tango", timestamp: "2026-06-14T02:40:00Z", acknowledged: true },
];

const mockIntel: IntelReport[] = [
  { id: "i1", title: "Despliegue de SAM en coordenadas 39.8°N 2.1°E", classification: "SECRET", source: "SAT-RECON", confidence: 0.92, timestamp: "2026-06-14T03:20:00Z" },
  { id: "i2", title: "Red de comunicaciones enemiga reconfigurada", classification: "RESTRICTED", source: "SIGINT", confidence: 0.78, timestamp: "2026-06-14T03:12:00Z" },
  { id: "i3", title: "Movimiento logistico — convoy de 12 vehiculos hacia el norte", classification: "SECRET", source: "OSINT-GEOINT", confidence: 0.85, timestamp: "2026-06-14T02:58:00Z" },
  { id: "i4", title: "Evaluacion de moral de unidad adversaria — baja", classification: "CONFIDENTIAL", source: "HUMINT", confidence: 0.65, timestamp: "2026-06-14T02:45:00Z" },
  { id: "i5", title: "Actividad cibernetica hostil contra infraestructura civil", classification: "TOP SECRET", source: "CYBER-INTEL", confidence: 0.88, timestamp: "2026-06-14T02:30:00Z" },
  { id: "i6", title: "Patrulla naval adversaria cambia ruta habitual", classification: "RESTRICTED", source: "MARITIME-IS", confidence: 0.71, timestamp: "2026-06-14T02:15:00Z" },
];

const mockThreats: ThreatAssessment[] = [
  { id: "t1", target: "Bateria SAM — Sector Delta", severity: 9, confidence: 0.92, recommended_action: "Evadir sector; solicitar supresion SEAD" },
  { id: "t2", target: "Blindados — 40.2°N 3.5°E", severity: 7, confidence: 0.78, recommended_action: "Monitorear; preparar COA ofensiva" },
  { id: "t3", target: "Celula cibernetica — APT-47", severity: 8, confidence: 0.88, recommended_action: "Aislar segmentos afectados; hardening" },
  { id: "t4", target: "Emboscada probable — Ruta Tango-6", severity: 6, confidence: 0.55, recommended_action: "Ruta alternativa; reconocimiento previo" },
];

const mockTimeline: MissionEvent[] = [
  { id: "e1", type: "OPORD", description: "OPORD FRAGO-7 recibida — Mision UPDATE", timestamp: "2026-06-14T00:00:00Z", severity: "info" },
  { id: "e2", type: "MOVEMENT", description: "Peloton Alfa inicia desplazamiento a PUNTO BRAVO", timestamp: "2026-06-14T02:00:00Z", severity: "info" },
  { id: "e3", type: "CONTACT", description: "Contacto visual con elemento adversario — 38.9°N 1.8°E", timestamp: "2026-06-14T04:00:00Z", severity: "warning" },
];

const mockMessages: TacticalMessage[] = [
  { id: "m1", sender: "HQ", recipients: ["Alfa-1", "Bravo-2"], type: "COMMAND", priority: "HIGH", subject: "FRAGO-7 Actualizacion", content: "Proceder con desplazamiento a PUNTO BRAVO. Mantener silencio radio hasta contacto.", timestamp: "2026-06-14T01:00:00Z", acknowledged: true, classification: "SECRET" },
  { id: "m2", sender: "Alfa-1", recipients: ["HQ"], type: "STATUS", priority: "MEDIUM", subject: "Reporte de posicion", content: "Alfa-1 en posicion 40.42N -3.70W. Sin novedad.", timestamp: "2026-06-14T02:15:00Z", acknowledged: true, classification: "RESTRICTED" },
  { id: "m3", sender: "Charlie-3", recipients: ["HQ"], type: "ALERT", priority: "CRITICAL", subject: "Contacto visual", content: "Contacto visual con elemento blindado adversario. 39.47N -0.38W. Solicito instrucciones.", timestamp: "2026-06-14T03:45:00Z", acknowledged: false, classification: "SECRET" },
  { id: "m4", sender: "Delta-4", recipients: ["HQ", "Echo-5"], type: "TEXT", priority: "LOW", subject: "Reabastecimiento", content: "Solicito coordinar reabastecimiento de combustible para 0600Z.", timestamp: "2026-06-14T03:30:00Z", acknowledged: false, classification: "CONFIDENTIAL" },
];

const mockConversations: Conversation[] = [
  { id: "c1", participants: ["HQ", "Alfa-1"], lastMessage: "Alfa-1 en posicion", lastTimestamp: "2026-06-14T02:15:00Z", unreadCount: 0 },
  { id: "c2", participants: ["HQ", "Charlie-3"], lastMessage: "Solicito instrucciones", lastTimestamp: "2026-06-14T03:45:00Z", unreadCount: 1 },
  { id: "c3", participants: ["HQ", "Delta-4", "Echo-5"], lastMessage: "Reabastecimiento 0600Z", lastTimestamp: "2026-06-14T03:30:00Z", unreadCount: 1 },
  { id: "c4", participants: ["HQ", "Bravo-2"], lastMessage: "Recibido FRAGO-7", lastTimestamp: "2026-06-14T01:05:00Z", unreadCount: 0 },
];

const mockSupplies: Supply[] = [
  { id: "sup1", type: "AMMO", name: "5.56x45mm NATO", quantity: 15000, maxQuantity: 20000, unit: "rds", status: "AVAILABLE", priority: "HIGH" },
  { id: "sup2", type: "FUEL", name: "JP-8 Combustible", quantity: 2400, maxQuantity: 5000, unit: "L", status: "AVAILABLE", priority: "HIGH" },
  { id: "sup3", type: "RATION", name: "MRE Pack", quantity: 350, maxQuantity: 500, unit: "uds", status: "AVAILABLE", priority: "MEDIUM" },
  { id: "sup4", type: "MEDICAL", name: "Kit IFAK", quantity: 45, maxQuantity: 100, unit: "uds", status: "AVAILABLE", priority: "CRITICAL" },
  { id: "sup5", type: "AMMO", name: "7.62x51mm NATO", quantity: 3000, maxQuantity: 10000, unit: "rds", status: "REQUESTED", priority: "HIGH" },
  { id: "sup6", type: "EQUIPMENT", name: "Baterias radio PRC-152", quantity: 8, maxQuantity: 20, unit: "uds", status: "IN_TRANSIT", priority: "MEDIUM" },
];

const mockPersonnel: Personnel[] = [
  { id: "p1", name: "CPT Garcia M.", rank: "CPT", unit: "Alfa-1", status: "ACTIVE", lastCheckin: "2026-06-14T03:00:00Z" },
  { id: "p2", name: "SGT Lopez R.", rank: "SGT", unit: "Alfa-1", status: "ACTIVE", lastCheckin: "2026-06-14T03:00:00Z" },
  { id: "p3", name: "CPL Martinez A.", rank: "CPL", unit: "Bravo-2", status: "WIA", lastCheckin: "2026-06-14T02:30:00Z" },
  { id: "p4", name: "PFC Sanchez J.", rank: "PFC", unit: "Charlie-3", status: "ACTIVE", lastCheckin: "2026-06-14T03:45:00Z" },
  { id: "p5", name: "SGT Fernandez L.", rank: "SGT", unit: "Delta-4", status: "ACTIVE", lastCheckin: "2026-06-14T03:15:00Z" },
  { id: "p6", name: "1LT Ruiz P.", rank: "1LT", unit: "Echo-5", status: "ACTIVE", lastCheckin: "2026-06-14T02:50:00Z" },
];

const mockMEDEVAC: MEDEVACRequest[] = [
  { id: "med1", location: "39.47°N -0.38°W", woundedCount: 2, classification: "URGENT", equipment: "Litter x2", personnel: "Medico + 2 camilleros", status: "APPROVED", timestamp: "2026-06-14T03:50:00Z" },
];

const mockMaintenance: MaintenanceRequest[] = [
  { id: "mnt1", equipment: "Vehiculo HMMWV #14", description: "Fallo en sistema de refrigeracion", priority: "HIGH", status: "IN_PROGRESS", timestamp: "2026-06-14T02:00:00Z" },
  { id: "mnt2", equipment: "Radio PRC-152 #7", description: "Interferencia en canal 3", priority: "MEDIUM", status: "PENDING", timestamp: "2026-06-14T03:00:00Z" },
];

const mockAAR: AfterActionReview = {
  id: "aar1",
  operationName: "OP IRON SHIELD",
  startTime: "2026-06-13T18:00:00Z",
  endTime: "2026-06-14T03:00:00Z",
  timeline: [
    { id: "tl1", timestamp: "2026-06-13T18:00:00Z", description: "Inicio de operaciones", type: "START", actor: "HQ" },
    { id: "tl2", timestamp: "2026-06-13T20:30:00Z", description: "Alfa-1 alcanza PUNTO ALFA", type: "MOVEMENT", actor: "Alfa-1" },
    { id: "tl3", timestamp: "2026-06-13T22:15:00Z", description: "Contacto indirecto — fuego de mortero", type: "CONTACT", actor: "Bravo-2" },
    { id: "tl4", timestamp: "2026-06-14T01:00:00Z", description: "FRAGO-7 emitida", type: "OPORD", actor: "HQ" },
    { id: "tl5", timestamp: "2026-06-14T03:00:00Z", description: "Pausa operacional", type: "PAUSE", actor: "HQ" },
  ],
  objectives: [
    { id: "obj1", description: "Establecer posicion en PUNTO ALFA", status: "ACHIEVED" },
    { id: "obj2", description: "Neutralizar puesto de observacion adversario", status: "PARTIAL" },
    { id: "obj3", description: "Asegurar ruta de suministro Tango-6", status: "PENDING" },
  ],
  lessonsLearned: [
    { id: "ll1", category: "COMMS", description: "Las comunicaciones HF fueron intermitentes en zona urbana", impact: "HIGH" },
    { id: "ll2", category: "MOVEMENT", description: "Ruta alternativa redujo tiempo de desplazamiento en 30%", impact: "MEDIUM" },
  ],
  recommendations: [
    "Desplegar repetidor de comunicaciones en PUNTO CHARLIE",
    "Actualizar rutas de evacuacion con datos de terreno recientes",
    "Solicitar apoyo CAS para proxima fase",
  ],
  status: "IN_PROGRESS",
};

const mockThreatPredictions: ThreatPredictionData[] = [
  { unitId: "adv1", unitName: "Bateria SAM movil", currentLocation: [39.8, 2.1], predictedLocation: [40.1, 2.5], confidence: 0.78, timeHorizon: 6, threatLevel: 9, movementPattern: "NORESTE — repliegue tactico", recommendedAction: "Interceptar antes de alcanzar nueva posicion" },
  { unitId: "adv2", unitName: "Columna blindada", currentLocation: [40.2, 3.5], predictedLocation: [40.5, 3.0], confidence: 0.62, timeHorizon: 12, threatLevel: 7, movementPattern: "NOROESTE — avance", recommendedAction: "Preparar emboscada en ruta probable" },
  { unitId: "adv3", unitName: "Equipo reconocimiento", currentLocation: [38.9, 1.8], predictedLocation: [39.2, 2.0], confidence: 0.85, timeHorizon: 3, threatLevel: 5, movementPattern: "NORTE — exploracion", recommendedAction: "Monitorear; evitar contacto" },
];

const mockOPORDs: OPORD[] = [
  {
    id: "op1",
    operationName: "OP IRON SHIELD",
    paragraph1_situation: "Fuerza adversaria despliega bateria SAM en sector Delta. Blindados en 40.2N 3.5E. Moral enemiga baja.",
    paragraph2_mission: "Establecer control del area de operaciones DELTA para neutralizar capacidades SAM adversarias.",
    paragraph3_execution: "Fase 1: Desplazamiento a PUNTO BRAVO. Fase 2: Supresion SEAD. Fase 3: Avance principal.",
    paragraph4_sustainment: "Reabastecimiento en PUNTO CHARLIE a 0600Z. MEDEVAC via ruta TANGO.",
    paragraph5_commandSignal: "Puesto de mando en PUNTO ALFA. Frecuencia primaria: CH-7. Alterna: CH-12.",
    status: "DISTRIBUTED",
    createdAt: "2026-06-13T16:00:00Z",
  },
];

const mockCOAs: COA[] = [
  { id: "coa1", name: "COA 1 — Asalto frontal", description: "Ataque directo con apoyo de artilleria", successProbability: 0.65, risk: 7, resources: "Alfa + Bravo + Echo", duration: "4h" },
  { id: "coa2", name: "COA 2 — Maniobra envolvente", description: "Flanco por norte evitando SAM", successProbability: 0.78, risk: 4, resources: "Alfa + Charlie", duration: "8h" },
  { id: "coa3", name: "COA 3 — Infiltracion", description: "Equipos pequenos por terreno dificil", successProbability: 0.55, risk: 8, resources: "Charlie + Fuerzas Especiales", duration: "12h" },
];

const mockRisks: RiskEntry[] = [
  { id: "r1", hazard: "Fuego SAM", probability: 4, impact: 5, mitigation: "Apoyo SEAD previo", residualRisk: 2 },
  { id: "r2", hazard: "Emboscada en ruta", probability: 3, impact: 4, mitigation: "Reconocimiento previo + drone", residualRisk: 2 },
  { id: "r3", hazard: "Perdida de comunicaciones", probability: 2, impact: 3, mitigation: "Repetidores + PACE plan", residualRisk: 1 },
  { id: "r4", hazard: "Bajas propias", probability: 3, impact: 5, mitigation: "Cobertura medica + MEDEVAC", residualRisk: 3 },
];

const mockReports: GeneratedReport[] = [
  { id: "rep1", template: "SITREP", classification: "SECRET", content: { situation: "Operaciones en curso", enemy: "SAM activo", friendly: "Alfa en PUNTO BRAVO" }, timestamp: "2026-06-14T03:00:00Z", author: "HQ", status: "SENT" },
];

const mockVoiceCommands: VoiceCommandEntry[] = [
  { id: "vc1", command: "Generar SITREP", timestamp: "2026-06-14T03:10:00Z", status: "SUCCESS" },
  { id: "vc2", command: "Enviar mensaje a Alfa-1", timestamp: "2026-06-14T02:50:00Z", status: "SUCCESS" },
];

const defaultWidgets: WidgetConfig[] = [
  { id: "w1", component: "TacticalMap", title: "Mapa Tactico", x: 0, y: 0, width: 6, height: 4, minimized: false },
  { id: "w2", component: "IntelFeed", title: "Feed Intel", x: 6, y: 0, width: 3, height: 2, minimized: false },
  { id: "w3", component: "ThreatPanel", title: "Amenazas", x: 6, y: 2, width: 3, height: 2, minimized: false },
  { id: "w4", component: "MessagingPanel", title: "Mensajeria", x: 9, y: 0, width: 3, height: 4, minimized: false },
];

export type COPActivePanel = "map" | "messages" | "terrain" | "logistics" | "aar" | "reports" | "threat-pred" | "planning" | "voice" | "multi-monitor";

export const useCOPStore = create<{
  state: COPState;
  classification: string;
  activePanel: COPActivePanel;
  messages: TacticalMessage[];
  conversations: Conversation[];
  terrainAnalyses: TerrainAnalysisData[];
  supplies: Supply[];
  personnel: Personnel[];
  medevacRequests: MEDEVACRequest[];
  maintenanceRequests: MaintenanceRequest[];
  aar: AfterActionReview;
  threatPredictions: ThreatPredictionData[];
  opords: OPORD[];
  coas: COA[];
  risks: RiskEntry[];
  reports: GeneratedReport[];
  voiceCommands: VoiceCommandEntry[];
  voiceStatus: "IDLE" | "LISTENING" | "PROCESSING";
  widgets: WidgetConfig[];
  layouts: DashboardLayout[];
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
  addRisk: (r: RiskEntry) => void;
  addReport: (r: GeneratedReport) => void;
  addVoiceCommand: (v: VoiceCommandEntry) => void;
  setVoiceStatus: (s: "IDLE" | "LISTENING" | "PROCESSING") => void;
  updateWidgets: (w: WidgetConfig[]) => void;
  saveLayout: (name: string) => void;
  loadLayout: (id: string) => void;
}>(set => ({
  state: {
    alerts: mockAlerts,
    units: [
      { id: "u1", name: "Alfa-1", type: "INF", lat: 40.4168, lon: -3.7038, status: "active" },
      { id: "u2", name: "Bravo-2", type: "ARM", lat: 41.15, lon: -3.10, status: "active" },
      { id: "u3", name: "Charlie-3", type: "REC", lat: 39.47, lon: -0.376, status: "active" },
      { id: "u4", name: "Delta-4", type: "LOG", lat: 40.97, lon: -5.66, status: "standby" },
      { id: "u5", name: "Echo-5", type: "ART", lat: 41.65, lon: -0.88, status: "active" },
    ],
    intelFeed: mockIntel,
    threats: mockThreats,
    bdaReports: [],
    agentReports: [],
    psyopsMessages: [],
    sensors: [
      { id: "s1", type: "SIGINT", battery: 94, status: "online", last_reading: "2026-06-14T03:20:00Z" },
      { id: "s2", type: "EO", battery: 87, status: "online", last_reading: "2026-06-14T03:19:00Z" },
      { id: "s3", type: "RADAR", battery: 100, status: "online", last_reading: "2026-06-14T03:21:00Z" },
      { id: "s4", type: "ACOUSTIC", battery: 18, status: "low_battery", last_reading: "2026-06-14T03:10:00Z" },
    ],
    wargamingResults: [],
    timeline: mockTimeline,
    modules: defaultModules,
  },
  classification: "RESTRICTED",
  activePanel: "map",
  messages: mockMessages,
  conversations: mockConversations,
  terrainAnalyses: [],
  supplies: mockSupplies,
  personnel: mockPersonnel,
  medevacRequests: mockMEDEVAC,
  maintenanceRequests: mockMaintenance,
  aar: mockAAR,
  threatPredictions: mockThreatPredictions,
  opords: mockOPORDs,
  coas: mockCOAs,
  risks: mockRisks,
  reports: mockReports,
  voiceCommands: mockVoiceCommands,
  voiceStatus: "IDLE",
  widgets: defaultWidgets,
  layouts: [
    { id: "l1", name: "C2 Principal", preset: "c2", widgets: defaultWidgets },
  ],
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
    const current = useCOPStore.getState();
    return current.state.alerts.filter((a: Alert) => a.severity === severity);
  },
  setActivePanel: (p) => set(() => ({ activePanel: p })),
  addMessage: (m) => set(s => ({ messages: [m, ...s.messages] })),
  acknowledgeMessage: (id) => set(s => ({
    messages: s.messages.map(m => m.id === id ? { ...m, acknowledged: true } : m),
  })),
  addTerrainAnalysis: (t) => set(s => ({ terrainAnalyses: [t, ...s.terrainAnalyses] })),
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
  updateAAR: (updates) => set(s => ({ aar: { ...s.aar, ...updates } })),
  addOPORD: (o) => set(s => ({ opords: [o, ...s.opords] })),
  updateOPORD: (id, updates) => set(s => ({
    opords: s.opords.map(o => o.id === id ? { ...o, ...updates } : o),
  })),
  addCOA: (c) => set(s => ({ coas: [...s.coas, c] })),
  addRisk: (r) => set(s => ({ risks: [...s.risks, r] })),
  addReport: (r) => set(s => ({ reports: [r, ...s.reports] })),
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
}));
