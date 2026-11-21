import type {
  Alert,
  IntelReport,
  ThreatAssessment,
  TacticalMessage,
  Supply,
  Personnel,
  MEDEVACRequest,
  MaintenanceRequest,
  GeneratedReport,
  AfterActionReview,
  OPORD,
  ThreatPredictionData,
  UnitPosition,
  SensorNode,
  AARLesson,
} from "@/lib/cop-types";

export interface BackendAlert {
  id: string | number;
  severity?: string;
  source?: string;
  message?: string;
  title?: string;
  created_at?: string;
  timestamp?: string;
  acknowledged?: boolean;
}

export interface BackendIntelProduct {
  id: string;
  title?: string;
  name?: string;
  classification?: string;
  classification_level?: string;
  source?: string;
  confidence?: number;
  created_at?: string;
  timestamp?: string;
}

export interface BackendEarlyWarning {
  id?: string;
  target?: string;
  threat_level?: number;
  severity?: number;
  confidence?: number;
  recommended_response?: string;
  recommended_action?: string;
}

export interface BackendMessage {
  id: string;
  sender?: string;
  recipients?: string[];
  type?: string;
  priority?: string;
  subject?: string;
  content?: string;
  timestamp?: string;
  created_at?: string;
  acknowledged?: boolean;
  classification?: string;
}

export interface BackendSupply {
  id: string | number;
  item_type?: string;
  type?: string;
  quantity?: number;
  unit?: string;
  status?: string;
  priority?: string;
  min_threshold?: number;
  minThreshold?: number;
}

export interface BackendPersonnel {
  id: string | number;
  name?: string;
  full_name?: string;
  rank?: string;
  unit?: string;
  status?: string;
  last_checkin?: string;
  lastCheckin?: string;
  medical_status?: string;
  role?: string;
}

/** Envelope real de `/api/v1/logistics/personnel`. */
export interface BackendPersonnelResponse {
  personnel: BackendPersonnel[];
  active_count: number;
  casualties: number;
  total: number;
}

export interface BackendMedevac {
  id: string;
  location?: string;
  urgency?: string;
  casualties?: number;
  status?: string;
  requested_at?: string;
  eta_min?: number;
}

export interface BackendMaintenance {
  id: string;
  asset_id?: string;
  asset_type?: string;
  issue?: string;
  priority?: string;
  status?: string;
  reported_at?: string;
  estimated_hours?: number;
}

export interface BackendReport {
  id: string;
  title?: string;
  type?: string;
  classification?: string;
  generated_at?: string;
  summary?: string;
  url?: string;
}

export interface BackendAAR {
  id: string;
  mission_id?: string;
  title?: string;
  objectives_met?: boolean;
  success_rating?: number;
  lessons_learned?: string[];
  timeline?: any[];
  strengths?: string[];
  weaknesses?: string[];
}

export interface BackendOPORD {
  id: string;
  operation_name?: string;
  name?: string;
  classification?: string;
  situation?: string;
  mission?: string;
  execution?: string;
  admin_logistics?: string;
  command_signal?: string;
  status?: string;
  created_at?: string;
}

export interface BackendPrediction {
  unit_id?: string;
  unitId?: string;
  unit_name?: string;
  predicted_action?: string;
  recommended_action?: string;
  probability?: number;
  confidence?: number;
  threat_level?: number;
  timeframe_min?: number;
  current_location?: { lat: number; lon: number } | [number, number];
  predicted_location?: { lat: number; lon: number } | [number, number];
  target_location?: { lat: number; lon: number } | [number, number];
}

export interface BackendOrbatUnit {
  id: string;
  name?: string;
  type?: string;
  lat?: number;
  lon?: number;
  latitude?: number;
  longitude?: number;
  status?: string;
}

export interface BackendBlueForce {
  id: string;
  unit_id?: string;
  name?: string;
  lat?: number;
  lon?: number;
  latitude?: number;
  longitude?: number;
  status?: string;
}

export interface BackendSensorSource {
  id: string;
  source_type?: string;
  type?: string;
  status?: string;
  battery_level?: number;
  battery?: number;
  last_ping?: string;
  last_reading?: string;
}

export function mapAlert(b: BackendAlert): Alert {
  const sev = (b.severity || "medium").toLowerCase();
  const validSev = ["critical", "high", "medium", "low"].includes(sev)
    ? (sev as "critical" | "high" | "medium" | "low")
    : "medium";
  return {
    id: String(b.id),
    severity: validSev,
    source: b.source || "System",
    message: b.message || b.title || "Alert",
    timestamp: b.timestamp || b.created_at || new Date().toISOString(),
    acknowledged: !!b.acknowledged,
  };
}

export function mapIntelProduct(b: BackendIntelProduct): IntelReport {
  return {
    id: String(b.id),
    title: b.title || b.name || "Intel Report",
    classification: b.classification || b.classification_level || "RESTRICTED",
    source: b.source || "OSINT",
    confidence: b.confidence ?? null,
    timestamp: b.timestamp || b.created_at || new Date().toISOString(),
  };
}

export function mapEarlyWarning(b: BackendEarlyWarning): ThreatAssessment {
  return {
    id: b.id || `threat-${Math.random().toString(36).substring(2, 9)}`,
    target: b.target || "General AO",
    severity: b.severity || b.threat_level || 50,
    confidence: b.confidence ?? null,
    recommended_action: b.recommended_action || b.recommended_response || "Monitor",
  };
}

export function mapMessage(b: BackendMessage): TacticalMessage {
  const p = (b.priority || "MEDIUM").toUpperCase();
  const validP = ["CRITICAL", "HIGH", "MEDIUM", "LOW"].includes(p)
    ? (p as "CRITICAL" | "HIGH" | "MEDIUM" | "LOW")
    : "MEDIUM";
  const t = (b.type || "TEXT").toUpperCase();
  const validT = ["TEXT", "COMMAND", "ALERT", "STATUS", "LOCATION"].includes(t)
    ? (t as "TEXT" | "COMMAND" | "ALERT" | "STATUS" | "LOCATION")
    : "TEXT";
  return {
    id: String(b.id),
    sender: b.sender || "HQ",
    recipients: b.recipients || ["ALL"],
    type: validT,
    priority: validP,
    subject: b.subject || "Message",
    content: b.content || "",
    timestamp: b.timestamp || b.created_at || new Date().toISOString(),
    acknowledged: !!b.acknowledged,
    classification: b.classification || "RESTRICTED",
  };
}

export function mapSupply(b: BackendSupply): Supply {
  return {
    id: String(b.id),
    type: b.type || b.item_type || "Generic Supply",
    quantity: b.quantity || 0,
    unit: b.unit || "units",
    status: b.status || "OK",
    priority: b.priority || "NORMAL",
    minThreshold: b.minThreshold || b.min_threshold || 10,
  };
}

export function mapPersonnel(b: BackendPersonnel): Personnel {
  return {
    id: String(b.id),
    name: b.name || b.full_name || "Operador sin identificar",
    rank: b.rank || "PVT",
    unit: b.unit || "Base Unit",
    status: b.status || "ACTIVE",
    lastCheckin: b.lastCheckin || b.last_checkin || new Date().toISOString(),
    medicalStatus: b.medical_status || "Fit",
    role: b.role,
  };
}

export function mapMedevac(b: BackendMedevac): MEDEVACRequest {
  const urgency = (b.urgency || "").toUpperCase();
  return {
    id: String(b.id),
    location: b.location || "Coordenadas pendientes",
    woundedCount: b.casualties ?? 1,
    classification:
      urgency === "PRIORITY" || urgency === "ROUTINE" ? urgency : "URGENT",
    equipment: b.eta_min ? `ETA ${b.eta_min} min` : "Sin asignar",
    personnel: "Equipo médico",
    status:
      b.status === "APPROVED" ||
      b.status === "IN_TRANSIT" ||
      b.status === "COMPLETED"
        ? b.status
        : "PENDING",
    timestamp: b.requested_at || new Date().toISOString(),
  };
}

export function mapMaintenance(b: BackendMaintenance): MaintenanceRequest {
  return {
    id: String(b.id),
    equipment: b.asset_type || b.asset_id || "Activo sin identificar",
    description: b.issue || "Mantenimiento general requerido",
    priority: (b.priority || "MEDIUM").toUpperCase(),
    status: (b.status || "OPEN").toUpperCase(),
    timestamp: b.reported_at || new Date().toISOString(),
  };
}

export function mapReport(b: BackendReport): GeneratedReport {
  return {
    id: String(b.id),
    template: b.type || "SITREP",
    title: b.title || "Resumen de inteligencia",
    classification: b.classification || "SECRET",
    content: { summary: b.summary || "Sin resumen disponible", url: b.url },
    timestamp: b.generated_at || new Date().toISOString(),
    author: "Sistema",
    status: "FINAL",
  };
}

export function mapAAR(b: BackendAAR): AfterActionReview {
  const lessons: AARLesson[] = (b.lessons_learned || []).map((text, index) => ({
    id: `lesson-${index + 1}`,
    category: "Operaciones",
    description: text,
    impact: b.success_rating && b.success_rating >= 70 ? "Positivo" : "A mejorar",
  }));

  return {
    id: String(b.id),
    operationName: b.title || "Revisión posterior a la acción",
    startTime: b.timeline?.[0]?.timestamp || new Date().toISOString(),
    endTime: b.timeline?.length ? b.timeline[b.timeline.length - 1]?.timestamp ?? null : null,
    timeline: (b.timeline || []).map((event, index) => ({
      id: event?.id || `event-${index + 1}`,
      timestamp: event?.timestamp || new Date().toISOString(),
      description: event?.description || String(event?.event || "Evento sin descripción"),
      type: event?.type || "MISSION",
      actor: event?.actor || "Sistema",
    })),
    objectives: (b.strengths || []).map((text, index) => ({
      id: `obj-${index + 1}`,
      description: text,
      status: "MET",
    })),
    lessonsLearned: lessons,
    recommendations: b.weaknesses || [],
    status: b.objectives_met === false ? "REVIEWED" : "COMPLETED",
  };
}

export function mapOPORD(b: BackendOPORD): OPORD {
  return {
    id: String(b.id),
    operationName: b.name || b.operation_name || "OPERACIÓN SIN NOMBRE",
    classification: b.classification || "SECRET",
    status: (b.status || "DRAFT").toUpperCase(),
    createdAt: b.created_at || new Date().toISOString(),
    paragraphs: {
      situation: { text: b.situation || "Situación no especificada" },
      mission: { text: b.mission || "Misión no especificada" },
      execution: { text: b.execution || "Ejecución no especificada" },
      admin_logistics: { text: b.admin_logistics || "Logística no especificada" },
      command_signal: { text: b.command_signal || "Comunicaciones no especificadas" },
    },
  };
}

export function mapPrediction(b: BackendPrediction): ThreatPredictionData {
  const toTuple = (
    value: { lat: number; lon: number } | [number, number] | undefined,
    fallback: [number, number],
  ): [number, number] => {
    if (!value) return fallback;
    if (Array.isArray(value)) return [value[0] ?? 0, value[1] ?? 0];
    return [value.lat ?? 0, value.lon ?? 0];
  };

  const unitId = b.unitId || b.unit_id || "UNIT-UNKNOWN";
  const current = toTuple(b.current_location, [0, 0]);
  const predicted = toTuple(b.predicted_location ?? b.target_location, current);

  return {
    unitId,
    unitName: b.unit_name || unitId,
    currentLocation: current,
    predictedLocation: predicted,
    confidence: b.probability || b.confidence || 0.5,
    timeHorizon: b.timeframe_min || 30,
    threatLevel: b.threat_level ?? 3,
    movementPattern: b.predicted_action || "TRANSIT",
    recommendedAction: b.recommended_action || "Mantener observación",
  };
}

export function mergeUnits(
  orbat: BackendOrbatUnit[] = [],
  blueForce: BackendBlueForce[] = []
): UnitPosition[] {
  const map = new Map<string, UnitPosition>();
  for (const u of orbat) {
    const lat = u.lat ?? u.latitude ?? 40.4168;
    const lon = u.lon ?? u.longitude ?? -3.7038;
    map.set(String(u.id), {
      id: String(u.id),
      name: u.name || `Unit ${u.id}`,
      type: u.type || "INFANTRY",
      lat,
      lon,
      status: u.status || "OPERATIONAL",
    });
  }
  for (const bf of blueForce) {
    const id = String(bf.unit_id || bf.id);
    const lat = bf.lat ?? bf.latitude ?? 40.4168;
    const lon = bf.lon ?? bf.longitude ?? -3.7038;
    if (map.has(id)) {
      const existing = map.get(id)!;
      map.set(id, { ...existing, lat, lon, status: bf.status || existing.status });
    } else {
      map.set(id, {
        id,
        name: bf.name || `Unit ${id}`,
        type: "BLUE_FORCE",
        lat,
        lon,
        status: bf.status || "ACTIVE",
      });
    }
  }
  return Array.from(map.values());
}

export function mapSensor(b: BackendSensorSource): SensorNode {
  return {
    id: String(b.id),
    type: b.type || b.source_type || "RADAR",
    battery: b.battery ?? b.battery_level ?? 100,
    status: b.status || "ACTIVE",
    last_reading: b.last_reading || b.last_ping || new Date().toISOString(),
  };
}
