export interface Alert {
  id: string; severity: "critical" | "high" | "medium" | "low"
  source: string; message: string; timestamp: string; acknowledged: boolean
}
export interface UnitPosition { id: string; name: string; type: string; lat: number; lon: number; status: string }
export interface IntelReport { id: string; title: string; classification: string; source: string; confidence: number | null; timestamp: string }
export interface ThreatAssessment { id: string; target: string; severity: number; confidence: number | null; recommended_action: string }
export interface BDAReport { strike_id: string; effectiveness: number; collateral: boolean; sources: string[] }
export interface AgentReport { id: string; agent: string; mission: string; status: string; location?: string }
export interface PSYOPSMessage { id: string; campaign: string; message: string; effectiveness: number }
export interface SensorNode { id: string; type: string; battery?: number; status: string; last_reading?: string }
export interface WargamingResult { coa: string; success_probability: number; casualties: number; duration_hours: number }
export interface MissionEvent { id: string; type: string; description: string; timestamp: string; severity: string }
export interface COPModule { id: string; name: string; status: "operational" | "degraded" | "offline"; color: string }
export interface COPState {
  alerts: Alert[]; units: UnitPosition[]; intelFeed: IntelReport[]
  threats: ThreatAssessment[]; bdaReports: BDAReport[]; agentReports: AgentReport[]
  psyopsMessages: PSYOPSMessage[]; sensors: SensorNode[]; wargamingResults: WargamingResult[]
  timeline: MissionEvent[]; modules: COPModule[]
}

export interface TacticalMessage {
  id: string
  sender: string
  recipients: string[]
  type: "TEXT" | "COMMAND" | "ALERT" | "STATUS" | "LOCATION"
  priority: "CRITICAL" | "HIGH" | "MEDIUM" | "LOW"
  subject: string
  content: string
  timestamp: string
  acknowledged: boolean
  classification: string
  threadId?: string
  replyTo?: string
}

export interface Conversation {
  id: string
  participants: string[]
  lastMessage: string
  lastTimestamp: string
  unreadCount: number
}

export interface TerrainLOSResult {
  visible: boolean
  distanceKm: number
  minClearanceM: number
  obstructions: { distanceKm: number; blockageM: number }[]
}

export interface TerrainRouteResult {
  distanceKm: number
  estimatedTimeMin: number
  difficulty: string
  obstacles: string[]
  recommendations: string[]
}

export interface TerrainAreaResult {
  trafficability: Record<string, { accessible_pct: number }>
  keyTerrain: { location: { lat: number; lon: number }; elevation_m: number; strategic_value: string; description: string }[]
  obstacles: { type: string; description: string; severity: string }[]
  recommendations: string[]
}

export interface TerrainAnalysisData {
  id: string
  type: "LOS" | "ROUTE" | "AREA"
  startPoint: [number, number]
  endPoint?: [number, number]
  los?: TerrainLOSResult
  route?: TerrainRouteResult
  area?: TerrainAreaResult
}

export interface Supply {
  id: string
  type: string
  quantity: number
  unit: string
  status: string
  priority: string
  minThreshold: number
}

export interface Personnel {
  id: string
  name: string
  rank: string
  unit: string
  status: string
  lastCheckin: string
  medicalStatus?: string
  role?: string
}

export interface MEDEVACRequest {
  id: string
  location: string
  woundedCount: number
  classification: "URGENT" | "PRIORITY" | "ROUTINE"
  equipment: string
  personnel: string
  status: "PENDING" | "APPROVED" | "IN_TRANSIT" | "COMPLETED"
  timestamp: string
}

export interface MaintenanceRequest {
  id: string
  equipment: string
  description: string
  priority: string
  status: string
  timestamp: string
}

export interface AARTimelineEvent {
  id: string
  timestamp: string
  description: string
  type: string
  actor: string
}

export interface AARObjective {
  id: string
  description: string
  status: string
}

export interface AARLesson {
  id: string
  category: string
  description: string
  impact: string
}

export interface AfterActionReview {
  id: string
  operationName: string
  startTime: string
  endTime: string | null
  timeline: AARTimelineEvent[]
  objectives: AARObjective[]
  lessonsLearned: AARLesson[]
  recommendations: string[]
  status: string
}

export interface GeneratedReport {
  id: string
  template: string
  title: string
  classification: string
  content: Record<string, unknown>
  timestamp: string
  author: string
  status: string
}

export interface ThreatPredictionData {
  unitId: string
  unitName: string
  currentLocation: [number, number]
  predictedLocation: [number, number]
  confidence: number
  timeHorizon: number
  threatLevel: number
  movementPattern: string
  recommendedAction: string
}

export interface OPORD {
  id: string
  operationName: string
  classification: string
  status: string
  createdAt: string
  paragraphs: Record<string, Record<string, unknown>>
}

export interface COA {
  id: string
  name: string
  description: string
  successProbability: number
  risk: number
  resources: string
  duration: string
  scores: Record<string, number>
}

export interface COAEvaluation {
  coa_id: string
  name: string
  scores: Record<string, number>
  total_score: number
}

export interface COAComparison {
  criteria: string[]
  coa_evaluations: COAEvaluation[]
  recommendation: string
}

export interface OPORDRisk {
  id: string
  category: string
  hazard: string
  probability: string
  severity: string
  risk_level: string
  mitigation: string
  residual_risk: string
}

export interface OPORDRiskAssessment {
  opord_id: string
  operation_name: string
  risks: OPORDRisk[]
  overall_risk_level: string
  risk_matrix: { high: number; medium: number; low: number }
  recommendations: string[]
}

export interface SyncMatrixEntry {
  phase: string
  tasks: Record<string, { description: string; responsible: string; start_condition: string; end_condition: string }>
}

export interface OPORDSyncMatrix {
  opord_id: string
  operation_name: string
  phases: { name: string; duration_h?: number }[]
  synchronization: SyncMatrixEntry[]
}

export interface VoiceCommandEntry {
  id: string
  command: string
  timestamp: string
  status: "SUCCESS" | "FAILED" | "UNKNOWN"
  resultMessage?: string
}

export interface WidgetConfig {
  id: string
  component: string
  title: string
  x: number
  y: number
  width: number
  height: number
  minimized: boolean
}

export interface PlanningEntry {
  id: string
  type: "OPORD" | "COA" | "FRAGORD"
  title: string
  status: string
  timestamp: string
}

export interface LogisticsEntry {
  id: string
  type: "SUPPLY" | "PERSONNEL" | "MEDEVAC" | "MAINTENANCE"
  description: string
  status: string
}

export interface DashboardLayout {
  id: string
  name: string
  preset: string
  widgets: WidgetConfig[]
}
