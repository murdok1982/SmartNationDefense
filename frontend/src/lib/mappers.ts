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

export interface BackendPersonnelResponse {
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
  predicted_action?: string;
  probability?: number;
  confidence?: number;
  timeframe_min?: number;
  target_location?: { lat: number; lon: number };
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

export function mapPersonnel(b: BackendPersonnelResponse): Personnel {
  return {
    id: String(b.id),
    name: b.name || b.full_name || "Unknown Operator",
    rank: b.rank || "PVT",
    unit: b.unit || "Base Unit",
    status: b.status || "ACTIVE",
    lastCheckin: b.lastCheckin || b.last_checkin || new Date().toISOString(),
    medicalStatus: b.medical_status || "Fit",
    role: b.role,
  };
}

export function mapMedevac(b: BackendMedevac): MEDEVACRequest {
  return {
    id: String(b.id),
    location: b.location || "Coordinates Pending",
    urgency: (b.urgency as any) || "URGENT",
    casualties: b.casualties || 1,
    status: (b.status as any) || "REQUESTED",
    requestedAt: b.requested_at || new Date().toISOString(),
    etaMin: b.eta_min,
  };
}

export function mapMaintenance(b: BackendMaintenance): MaintenanceRequest {
  return {
    id: String(b.id),
    assetId: b.asset_id || "ASSET-UNKNOWN",
    assetType: b.asset_type || "Vehicle",
    issue: b.issue || "General maintenance required",
    priority: (b.priority as any) || "MEDIUM",
    status: (b.status as any) || "OPEN",
    reportedAt: b.reported_at || new Date().toISOString(),
    estimatedHours: b.estimated_hours,
  };
}

export function mapReport(b: BackendReport): GeneratedReport {
  return {
    id: String(b.id),
    title: b.title || "Intelligence Summary",
    type: (b.type as any) || "SITREP",
    classification: b.classification || "SECRET",
    generatedAt: b.generated_at || new Date().toISOString(),
    summary: b.summary || "Summary report",
    url: b.url,
  };
}

export function mapAAR(b: BackendAAR): AfterActionReview {
  return {
    id: String(b.id),
    missionId: b.mission_id || "MISSION-001",
    title: b.title || "After Action Review",
    objectivesMet: b.objectives_met ?? true,
    successRating: b.success_rating || 85,
    lessonsLearned: b.lessons_learned || [],
    timeline: b.timeline || [],
    strengths: b.strengths || [],
    weaknesses: b.weaknesses || [],
  };
}

export function mapOPORD(b: BackendOPORD): OPORD {
  return {
    id: String(b.id),
    name: b.name || b.operation_name || "OPERATION DEFAULT",
    classification: b.classification || "SECRET",
    situation: b.situation || "Situation baseline",
    mission: b.mission || "Mission objectives defined",
    execution: b.execution || "Execution steps assigned",
    adminLogistics: b.admin_logistics || "Logistics support active",
    commandSignal: b.command_signal || "Command channels secured",
    status: (b.status as any) || "DRAFT",
    createdAt: b.created_at || new Date().toISOString(),
  };
}

export function mapPrediction(b: BackendPrediction): ThreatPredictionData {
  return {
    unitId: b.unitId || b.unit_id || "UNIT-UNKNOWN",
    predictedAction: b.predicted_action || "TRANSIT",
    probability: b.probability || b.confidence || 0.5,
    timeframeMin: b.timeframe_min || 30,
    targetLocation: b.target_location,
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
