export interface Alert {
  id: string; severity: "critical" | "high" | "medium" | "low"
  source: string; message: string; timestamp: string; acknowledged: boolean
}
export interface UnitPosition { id: string; name: string; type: string; lat: number; lon: number; status: string }
export interface IntelReport { id: string; title: string; classification: string; source: string; confidence: number; timestamp: string }
export interface ThreatAssessment { id: string; target: string; severity: number; confidence: number; recommended_action: string }
export interface BDAReport { strike_id: string; effectiveness: number; collateral: boolean; sources: string[] }
export interface AgentReport { id: string; agent: string; mission: string; status: string; location?: string }
export interface PSYOPSMessage { id: string; campaign: string; message: string; effectiveness: number }
export interface SensorNode { id: string; type: string; battery: number; status: string; last_reading?: string }
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
  replyTo?: string
}

export interface Conversation {
  id: string
  participants: string[]
  lastMessage: string
  lastTimestamp: string
  unreadCount: number
}

export interface TerrainAnalysisData {
  id: string
  type: "LOS" | "ROUTE" | "AREA"
  startPoint: [number, number]
  endPoint?: [number, number]
  results: {
    visible: boolean
    distance: number
    elevationGain: number
    estimatedTime: number
    obstacles: string[]
  }
}

export interface Supply {
  id: string
  type: "AMMO" | "FUEL" | "RATION" | "MEDICAL" | "EQUIPMENT"
  name: string
  quantity: number
  maxQuantity: number
  unit: string
  status: "AVAILABLE" | "REQUESTED" | "IN_TRANSIT" | "DELIVERED"
  priority: "CRITICAL" | "HIGH" | "MEDIUM" | "LOW"
}

export interface Personnel {
  id: string
  name: string
  rank: string
  unit: string
  status: "ACTIVE" | "WIA" | "KIA" | "MIA" | "OFF_DUTY"
  lastCheckin: string
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
  priority: "CRITICAL" | "HIGH" | "MEDIUM" | "LOW"
  status: "PENDING" | "IN_PROGRESS" | "COMPLETED"
  timestamp: string
}

export interface TimelineEvent {
  id: string
  timestamp: string
  description: string
  type: string
  actor: string
}

export interface Objective {
  id: string
  description: string
  status: "ACHIEVED" | "PARTIAL" | "FAILED" | "PENDING"
}

export interface LessonLearned {
  id: string
  category: string
  description: string
  impact: "HIGH" | "MEDIUM" | "LOW"
}

export interface AfterActionReview {
  id: string
  operationName: string
  startTime: string
  endTime: string
  timeline: TimelineEvent[]
  objectives: Objective[]
  lessonsLearned: LessonLearned[]
  recommendations: string[]
  status: "IN_PROGRESS" | "FINALIZED"
}

export interface ReportTemplate {
  id: string
  type: "SITREP" | "SPOTREP" | "SALUTE" | "MEDEVAC"
  name: string
  fields: ReportField[]
}

export interface ReportField {
  key: string
  label: string
  type: "text" | "textarea" | "select"
  required: boolean
  options?: string[]
}

export interface GeneratedReport {
  id: string
  template: string
  classification: string
  content: Record<string, string>
  timestamp: string
  author: string
  status: "DRAFT" | "SENT"
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
  paragraph1_situation: string
  paragraph2_mission: string
  paragraph3_execution: string
  paragraph4_sustainment: string
  paragraph5_commandSignal: string
  status: "DRAFT" | "APPROVED" | "DISTRIBUTED"
  createdAt: string
}

export interface COA {
  id: string
  name: string
  description: string
  successProbability: number
  risk: number
  resources: string
  duration: string
}

export interface RiskEntry {
  id: string
  hazard: string
  probability: 1 | 2 | 3 | 4 | 5
  impact: 1 | 2 | 3 | 4 | 5
  mitigation: string
  residualRisk: number
}

export interface VoiceCommandEntry {
  id: string
  command: string
  timestamp: string
  status: "SUCCESS" | "FAILED" | "UNKNOWN"
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

export interface DashboardLayout {
  id: string
  name: string
  preset: string
  widgets: WidgetConfig[]
}
