import { create } from "zustand";
import { apiFetch, apiErrorMessage } from "@/lib/api";
import type {
  SatelliteImage,
  Detection,
  DetectionRaw,
  Track,
  TrackRaw,
  ScoredCOA,
  ScoredCOARaw,
  MissionParams,
  COPSnapshot,
} from "@/lib/maven-types";
import { normalizeCOA, normalizeDetection, normalizeTrack } from "@/lib/maven-types";

interface MavenStore {
  satelliteImages: SatelliteImage[]
  detections: Detection[]
  tracks: Track[]
  coas: ScoredCOA[]
  selectedCOA: ScoredCOA | null
  copSnapshot: COPSnapshot | null
  loading: boolean
  error: string | null

  fetchDetections: () => Promise<void>
  fetchTracks: () => Promise<void>
  fetchCOAs: (params?: Partial<MissionParams>) => Promise<void>
  generateCOA: (params: MissionParams) => Promise<void>
  compareCOAs: (coas: ScoredCOA[], criteria: string[]) => Promise<ScoredCOA[]>
  assessRisk: (coaId: string) => Promise<{ risk_level: string; factors: string[] }>
  assessWeapons: (coaId: string) => Promise<{ readiness: number; gaps: string[] }>
  selectCOA: (id: string) => void
  requestAnalysis: (imageUrl: string) => Promise<Detection[]>
  setError: (error: string | null) => void
  clearError: () => void
}

export const useMavenStore = create<MavenStore>((set, get) => ({
  satelliteImages: [],
  detections: [],
  tracks: [],
  coas: [],
  selectedCOA: null,
  copSnapshot: null,
  loading: false,
  error: null,

  fetchDetections: async () => {
    set({ loading: true, error: null });
    try {
      const data = await apiFetch<DetectionRaw[]>("/api/v3/vision/detections?limit=200");
      set({ detections: data.map((d) => normalizeDetection(d)), loading: false });
    } catch (e) {
      set({ loading: false, error: apiErrorMessage(e) });
    }
  },

  fetchTracks: async () => {
    set({ loading: true, error: null });
    try {
      const data = await apiFetch<TrackRaw[]>("/api/v3/fusion/tracks?limit=500");
      set({ tracks: data.map(normalizeTrack), loading: false });
    } catch (e) {
      set({ loading: false, error: apiErrorMessage(e) });
    }
  },

  fetchCOAs: async (params) => {
    set({ loading: true, error: null });
    try {
      const qs = params
        ? `?${new URLSearchParams(
            Object.fromEntries(
              Object.entries(params).filter(([_, v]) => v !== undefined).map(([k, v]) => [k, String(v)])
            )
          ).toString()}`
        : "";
      const data = await apiFetch<ScoredCOARaw[]>(`/api/v3/coa/list${qs}`);
      set({ coas: data.map(normalizeCOA), loading: false });
    } catch (e) {
      set({ loading: false, error: apiErrorMessage(e) });
    }
  },

  generateCOA: async (params) => {
    set({ loading: true, error: null });
    try {
      const data = await apiFetch<ScoredCOARaw[]>("/api/v3/coa/generate", {
        method: "POST",
        body: params,
      });
      set({ coas: data.map(normalizeCOA), loading: false });
    } catch (e) {
      set({ loading: false, error: apiErrorMessage(e) });
    }
  },

  compareCOAs: async (coas, criteria) => {
    set({ loading: true, error: null });
    try {
      const data = await apiFetch<ScoredCOARaw[]>("/api/v3/coa/compare", {
        method: "POST",
        body: { coa_ids: coas.map(c => c.id), criteria },
      });
      set({ loading: false });
      return data.map(normalizeCOA);
    } catch (e) {
      set({ loading: false, error: apiErrorMessage(e) });
      return coas;
    }
  },

  assessRisk: async (coaId) => {
    set({ loading: true, error: null });
    try {
      const data = await apiFetch<{ risk_level: string; factors: string[] }>(
        `/api/v3/coa/${encodeURIComponent(coaId)}/risk`
      );
      set({ loading: false });
      return data;
    } catch (e) {
      set({ loading: false, error: apiErrorMessage(e) });
      return { risk_level: "unknown", factors: [] };
    }
  },

  assessWeapons: async (coaId) => {
    set({ loading: true, error: null });
    try {
      const data = await apiFetch<{ readiness: number; gaps: string[] }>(
        `/api/v3/coa/${encodeURIComponent(coaId)}/weapons`
      );
      set({ loading: false });
      return data;
    } catch (e) {
      set({ loading: false, error: apiErrorMessage(e) });
      return { readiness: 0, gaps: [] };
    }
  },

  selectCOA: (id) => {
    const coa = get().coas.find(c => c.id === id) ?? null;
    set({ selectedCOA: coa });
  },

  requestAnalysis: async (imageUrl) => {
    set({ loading: true, error: null });
    try {
      const data = await apiFetch<{ detections: DetectionRaw[] }>("/api/v3/vision/analyze-satellite", {
        method: "POST",
        body: { image_url: imageUrl },
      });
      const receivedAt = new Date().toISOString();
      const detections = data.detections.map((d) => normalizeDetection(d, receivedAt));
      set(s => ({
        satelliteImages: [
          {
            id: `img-${Date.now()}`,
            url: imageUrl,
            timestamp: receivedAt,
            source: "satellite",
            detections,
          },
          ...s.satelliteImages,
        ],
        detections: [...detections, ...s.detections],
        loading: false,
      }));
      return detections;
    } catch (e) {
      set({ loading: false, error: apiErrorMessage(e) });
      return [];
    }
  },

  setError: (error) => set({ error }),
  clearError: () => set({ error: null }),
}));
