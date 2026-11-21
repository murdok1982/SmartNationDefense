/**
 * Contratos Maven (visión, fusión y COA).
 *
 * Los tipos distinguen entre la **forma del backend** (`*Raw`, campos
 * snake_case tal como los emite FastAPI) y la **forma de la UI** (campos
 * normalizados que consumen los componentes). Los normalizadores son la
 * única frontera de traducción: ningún componente debe adivinar el contrato.
 */

// ---------------------------------------------------------------------------
// Visión / detecciones
// ---------------------------------------------------------------------------

/** Detección tal como la emite `/api/v3/vision/*`. */
export interface DetectionRaw {
  id?: string;
  bbox?: number[];
  confidence: number;
  class_id?: number;
  class_name?: string;
  class?: string;
  is_military?: boolean;
  geo_position?: { lat: number; lon: number };
  lat?: number;
  lon?: number;
  classification?: string;
  timestamp?: string;
}

/** Detección normalizada para la UI. */
export interface Detection {
  id?: string;
  class_name: string;
  confidence: number;
  bbox: [number, number, number, number];
  classification: string;
  timestamp: string;
  lat?: number;
  lon?: number;
  is_military?: boolean;
}

export interface SatelliteImage {
  id: string;
  url: string;
  timestamp: string;
  source: string;
  detections: Detection[];
}

// ---------------------------------------------------------------------------
// Fusión / tracks
// ---------------------------------------------------------------------------

export interface TrackPoint {
  ts: string;
  lat: number;
  lon: number;
  altitude?: number;
  speed_kmh?: number;
  heading_deg?: number;
}

/** Track tal como lo emite `/api/v3/fusion/tracks`. */
export interface TrackRaw {
  id?: string;
  track_id?: string;
  entity_id?: string;
  classification?: string;
  confidence?: number;
  source?: string;
  points?: TrackPoint[];
  centroid_lat?: number;
  centroid_lon?: number;
  last_lat?: number;
  last_lon?: number;
  last_seen?: string;
  first_seen?: string;
  status?: string;
}

/** Track normalizado para la UI. */
export interface Track {
  id: string;
  track_id: string;
  source: string;
  position: [number, number];
  classification: string;
  confidence: number;
  last_seen: string;
  status: string;
  points: TrackPoint[];
}

// ---------------------------------------------------------------------------
// COA
// ---------------------------------------------------------------------------

export interface COAPhase {
  name: string;
  description: string;
  duration_h: number;
  waypoints: [number, number][];
}

/** COA tal como lo emite `/api/v3/coa/*`. */
export interface ScoredCOARaw {
  id: string;
  name: string;
  description?: string;
  template_id?: string;
  phases?: {
    name?: string;
    objective?: string;
    description?: string;
    duration_min?: number;
    duration_h?: number;
    forces_assigned?: string[];
    key_terrain?: { lat?: number; lon?: number }[];
    waypoints?: [number, number][];
  }[];
  /** El motor emite aquí el nivel de riesgo como texto ("HIGH"), no un número. */
  risk_score?: number | string;
  risk_level?: string;
  weapon_score?: number;
  overall_score?: number;
  score?: number;
  feasibility?: number;
  estimated_casualties?: number;
  casualties_predicted?: number;
  estimated_duration_min?: number;
  timeline_hours?: number;
  assigned_units?: string[];
  recommendations?: string[];
  /** `/coa/compare` envuelve el COA en `{ coa, score, strengths, weaknesses }`. */
  coa?: ScoredCOARaw;
}

/** COA normalizado para la UI. */
export interface ScoredCOA {
  id: string;
  name: string;
  description: string;
  risk_level: string;
  overall_score: number;
  estimated_casualties: number;
  duration_h: number;
  weapon_readiness: number;
  phases: COAPhase[];
  assigned_units: string[];
  recommendations: string[];
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

// ---------------------------------------------------------------------------
// Normalizadores
// ---------------------------------------------------------------------------

const clamp01 = (value: number): number => Math.max(0, Math.min(1, value));

function riskLevelFromScore(score: number): string {
  if (score >= 0.75) return "critical";
  if (score >= 0.5) return "high";
  if (score >= 0.25) return "medium";
  return "low";
}

const RISK_LEVELS = ["low", "medium", "high", "critical"] as const;
type RiskLevelName = (typeof RISK_LEVELS)[number];

function asRiskLevel(value: unknown): RiskLevelName | null {
  if (typeof value !== "string") return null;
  const normalized = value.toLowerCase();
  return (RISK_LEVELS as readonly string[]).includes(normalized) ? (normalized as RiskLevelName) : null;
}

/**
 * Puntuaciones del motor COA: algunas llegan como fracción (0–1) y otras como
 * porcentaje (0–100). Se normalizan siempre a fracción para que la UI pueda
 * multiplicar por 100 sin mostrar 100% en todos los COA.
 */
function scoreToRatio(value: unknown): number {
  const numeric = Number(value);
  if (!Number.isFinite(numeric) || numeric <= 0) return 0;
  return clamp01(numeric > 1 ? numeric / 100 : numeric);
}

export function normalizeDetection(raw: DetectionRaw, receivedAt?: string): Detection {
  const bbox = raw.bbox && raw.bbox.length >= 4 ? raw.bbox : [0, 0, 0, 0];
  return {
    id: raw.id,
    class_name: raw.class_name || raw.class || "unknown",
    confidence: clamp01(Number(raw.confidence) || 0),
    bbox: [bbox[0], bbox[1], bbox[2], bbox[3]],
    classification: (raw.classification || "unknown").toLowerCase(),
    timestamp: raw.timestamp || receivedAt || new Date().toISOString(),
    lat: raw.lat ?? raw.geo_position?.lat,
    lon: raw.lon ?? raw.geo_position?.lon,
    is_military: raw.is_military,
  };
}

export function normalizeTrack(raw: TrackRaw): Track {
  const lastLat = raw.centroid_lat ?? raw.last_lat ?? raw.points?.[raw.points.length - 1]?.lat ?? 0;
  const lastLon = raw.centroid_lon ?? raw.last_lon ?? raw.points?.[raw.points.length - 1]?.lon ?? 0;
  return {
    id: raw.id || raw.track_id || raw.entity_id || `track-${lastLat}-${lastLon}`,
    track_id: raw.track_id || raw.id || raw.entity_id || "TRACK-UNKNOWN",
    source: (raw.source || "fused").toLowerCase(),
    position: [lastLat, lastLon],
    classification: (raw.classification || "unknown").toLowerCase(),
    confidence: clamp01(Number(raw.confidence) || 0),
    last_seen: raw.last_seen || raw.first_seen || new Date().toISOString(),
    status: raw.status || "ACTIVE",
    points: raw.points || [],
  };
}

export function normalizeCOA(raw: ScoredCOARaw): ScoredCOA {
  // `/coa/compare` envuelve el COA: `{ coa, score, strengths, weaknesses }`.
  const base = raw.coa ?? raw;
  const phases: COAPhase[] = (base.phases || []).map((phase) => {
    const waypoints: [number, number][] = (phase.waypoints || []).map((wp) => [wp[0], wp[1]]);
    if (waypoints.length === 0 && phase.key_terrain) {
      for (const point of phase.key_terrain) {
        if (typeof point.lat === "number" && typeof point.lon === "number") {
          waypoints.push([point.lat, point.lon]);
        }
      }
    }
    const durationH =
      typeof phase.duration_h === "number"
        ? phase.duration_h
        : Math.round(((phase.duration_min ?? 30) / 60) * 10) / 10;
    return {
      name: phase.name || "Fase sin nombre",
      description: phase.description || phase.objective || "Sin descripción",
      duration_h: durationH,
      waypoints,
    };
  });

  const durationH =
    typeof base.timeline_hours === "number"
      ? base.timeline_hours
      : Math.round(((base.estimated_duration_min ?? 0) / 60) * 10) / 10;

  const assignedUnits =
    base.assigned_units && base.assigned_units.length > 0
      ? base.assigned_units
      : Array.from(
          new Set((base.phases || []).flatMap((phase) => phase.forces_assigned ?? [])),
        );

  const riskLevel =
    asRiskLevel(base.risk_level) ??
    asRiskLevel(base.risk_score) ??
    riskLevelFromScore(scoreToRatio(base.risk_score));

  return {
    id: base.id,
    name: base.name,
    description: base.description || base.phases?.[0]?.objective || "Sin descripción operativa",
    risk_level: riskLevel,
    overall_score: scoreToRatio(raw.score ?? base.overall_score ?? 0),
    estimated_casualties: Number(base.estimated_casualties ?? base.casualties_predicted ?? 0),
    duration_h: durationH,
    weapon_readiness: scoreToRatio(base.weapon_score ?? base.feasibility ?? 0),
    phases,
    assigned_units: assignedUnits,
    recommendations: base.recommendations || [],
  };
}
