export interface Detection {
  id?: string;
  class?: string;
  class_name?: string;
  confidence: number;
  bbox?: number[];
  is_military?: boolean;
  geo_position?: { lat: number; lon: number };
}

export interface SatelliteImage {
  id: string;
  url: string;
  timestamp: string;
  source: string;
  detections: Detection[];
}

export interface TrackPoint {
  ts: string;
  lat: number;
  lon: number;
  altitude?: number;
  speed_kmh?: number;
  heading_deg?: number;
}

export interface Track {
  id: string;
  track_id?: string;
  entity_id?: string;
  classification?: string;
  confidence?: number;
  source?: string;
  points?: TrackPoint[];
  last_lat?: number;
  last_lon?: number;
  status?: string;
}

export interface ScoredCOA {
  id: string;
  name: string;
  description?: string;
  score?: number;
  risk_level?: string;
  feasibility?: number;
  casualties_predicted?: number;
  timeline_hours?: number;
  assigned_units?: string[];
  recommendations?: string[];
}

export interface MissionParams {
  mission_id?: string;
  objective?: string;
  ao?: string;
  threat_level?: string;
  available_forces?: string[];
  timeframe_hours?: number;
  [key: string]: any;
}

export interface COPSnapshot {
  id: string;
  timestamp: string;
  summary: string;
  active_threats: number;
  friendly_units_count: number;
  hostile_units_count: number;
}
