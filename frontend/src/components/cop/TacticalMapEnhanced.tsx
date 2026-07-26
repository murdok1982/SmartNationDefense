"use client";
import dynamic from "next/dynamic";
import { useState, useRef, useEffect } from "react";
import { Layers, Ruler, Circle, Maximize2, Minimize2 } from "lucide-react";
import L from "leaflet";
import "leaflet/dist/leaflet.css";
import { useCOPStore } from "@/store/cop-store";
import type { UnitPosition } from "@/lib/cop-types";

const baseLayers: Record<string, { url: string; name: string }> = {
  dark: { url: "https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png", name: "Oscuro" },
  satellite: { url: "https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}", name: "Satelite" },
  terrain: { url: "https://{s}.tile.opentopomap.org/{z}/{x}/{y}.png", name: "Terreno" },
  tactical: { url: "https://{s}.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}{r}.png", name: "Tactico" },
};

const unitColors: Record<string, string> = {
  INF: "#3ddc84",
  ARM: "#f59e0b",
  REC: "#3498db",
  LOG: "#9ca3af",
  ART: "#e94560",
};

function createUnitIcon(type: string) {
  const color = unitColors[type] || "#3ddc84";
  const svg = `
    <svg xmlns="http://www.w3.org/2000/svg" width="28" height="28" viewBox="0 0 28 28">
      <circle cx="14" cy="14" r="12" fill="${color}" fill-opacity="0.3" stroke="${color}" stroke-width="2"/>
      <circle cx="14" cy="14" r="4" fill="${color}"/>
    </svg>`;
  return L.divIcon({ html: svg, className: "", iconSize: [28, 28], iconAnchor: [14, 14] });
}

export default function TacticalMapEnhanced() {
  const { state } = useCOPStore();
  const mapRef = useRef<HTMLDivElement>(null);
  const mapInstanceRef = useRef<L.Map | null>(null);
  const [activeBase, setActiveBase] = useState("dark");
  const [showRangeCircles, setShowRangeCircles] = useState(false);
  const [showHistory, setShowHistory] = useState(false);
  const [showLayers, setShowLayers] = useState(false);
  const [measureMode, setMeasureMode] = useState(false);
  const [measurePoints, setMeasurePoints] = useState<[number, number][]>([]);
  const [measureDistance, setMeasureDistance] = useState(0);
  const [selectedUnit, setSelectedUnit] = useState<UnitPosition | null>(null);
  const [isFullscreen, setIsFullscreen] = useState(false);
  const baseLayerRef = useRef<L.TileLayer | null>(null);
  const rangeLayerRef = useRef<L.LayerGroup | null>(null);
  const measureLayerRef = useRef<L.LayerGroup | null>(null);

  useEffect(() => {
    if (!mapRef.current || mapInstanceRef.current) return;
    const map = L.map(mapRef.current, {
      center: [40.4168, -3.7038],
      zoom: 6,
      zoomControl: true,
      attributionControl: true,
    });
    const tile = L.tileLayer(baseLayers.dark.url, {
      attribution: '&copy; OSM &copy; CARTO',
      subdomains: "abcd",
      maxZoom: 19,
    }).addTo(map);
    baseLayerRef.current = tile;

    state.units.forEach(u => {
      const marker = L.marker([u.lat, u.lon], { icon: createUnitIcon(u.type) }).addTo(map);
      marker.bindTooltip(`<b>${u.name}</b><br/>Tipo: ${u.type}<br/>Estado: ${u.status}`, {
        className: "bg-gray-900 text-green-400 border border-gray-600 font-mono text-xs",
      });
      marker.on("click", () => setSelectedUnit(u));
    });

    map.on("click", (e: L.LeafletMouseEvent) => {
      if (!measureMode) return;
      const pt: [number, number] = [e.latlng.lat, e.latlng.lng];
      setMeasurePoints(prev => {
        const newPts = [...prev, pt];
        if (newPts.length >= 2) {
          const dist = calculateDistance(newPts);
          setMeasureDistance(dist);
          if (measureLayerRef.current && mapInstanceRef.current) {
            mapInstanceRef.current.removeLayer(measureLayerRef.current);
          }
          const lg = L.layerGroup().addTo(map);
          for (let i = 0; i < newPts.length - 1; i++) {
            L.polyline([newPts[i], newPts[i + 1]], { color: "#00ff00", weight: 2, dashArray: "5,5" }).addTo(lg);
          }
          newPts.forEach(p => {
            L.circleMarker(p, { radius: 4, color: "#00ff00", fillColor: "#00ff00", fillOpacity: 1 }).addTo(lg);
          });
          measureLayerRef.current = lg;
        }
        return newPts;
      });
    });

    mapInstanceRef.current = map;
    return () => { map.remove(); mapInstanceRef.current = null; };
  }, []);

  useEffect(() => {
    const map = mapInstanceRef.current;
    if (!map || !baseLayerRef.current) return;
    map.removeLayer(baseLayerRef.current);
    const tile = L.tileLayer(baseLayers[activeBase].url, {
      attribution: '&copy; OSM',
      subdomains: activeBase === "dark" || activeBase === "tactical" ? "abcd" : undefined,
      maxZoom: 19,
    }).addTo(map);
    baseLayerRef.current = tile;
  }, [activeBase]);

  useEffect(() => {
    const map = mapInstanceRef.current;
    if (!map) return;
    if (rangeLayerRef.current) {
      map.removeLayer(rangeLayerRef.current);
    }
    if (!showRangeCircles) return;
    const lg = L.layerGroup().addTo(map);
    state.units.forEach(u => {
      const rangeKm = u.type === "ART" ? 30 : u.type === "ARM" ? 5 : 2;
      L.circle([u.lat, u.lon], {
        radius: rangeKm * 1000,
        color: unitColors[u.type] || "#3ddc84",
        fillColor: unitColors[u.type] || "#3ddc84",
        fillOpacity: 0.05,
        weight: 1,
        dashArray: "3,3",
      }).addTo(lg);
    });
    rangeLayerRef.current = lg;
  }, [showRangeCircles, state.units]);

  const calculateDistance = (points: [number, number][]) => {
    let total = 0;
    for (let i = 0; i < points.length - 1; i++) {
      const dLat = (points[i + 1][0] - points[i][0]) * 111;
      const dLon = (points[i + 1][1] - points[i][1]) * 85;
      total += Math.sqrt(dLat * dLat + dLon * dLon);
    }
    return Math.round(total * 10) / 10;
  };

  const clearMeasure = () => {
    setMeasurePoints([]);
    setMeasureDistance(0);
    if (measureLayerRef.current && mapInstanceRef.current) {
      mapInstanceRef.current.removeLayer(measureLayerRef.current);
      measureLayerRef.current = null;
    }
  };

  return (
    <div className={`relative bg-gray-900 rounded border border-gray-700 flex flex-col ${isFullscreen ? "fixed inset-0 z-50" : "h-full"}`}>
      <div className="absolute top-2 left-2 z-[1000] flex gap-1">
        <button
          onClick={() => setShowLayers(!showLayers)}
          className={`p-1 rounded text-[10px] flex items-center gap-0.5 transition-colors ${
            showLayers ? "bg-green-900/80 text-green-400" : "bg-gray-900/80 text-gray-400 hover:text-gray-200"
          }`}
        >
          <Layers size={12} />
        </button>
        <button
          onClick={() => { setMeasureMode(!measureMode); if (measureMode) clearMeasure(); }}
          className={`p-1 rounded text-[10px] flex items-center gap-0.5 transition-colors ${
            measureMode ? "bg-green-900/80 text-green-400" : "bg-gray-900/80 text-gray-400 hover:text-gray-200"
          }`}
        >
          <Ruler size={12} />
        </button>
        <button
          onClick={() => setShowRangeCircles(!showRangeCircles)}
          className={`p-1 rounded text-[10px] flex items-center gap-0.5 transition-colors ${
            showRangeCircles ? "bg-green-900/80 text-green-400" : "bg-gray-900/80 text-gray-400 hover:text-gray-200"
          }`}
        >
          <Circle size={12} />
        </button>
        <button
          onClick={() => setIsFullscreen(!isFullscreen)}
          className="bg-gray-900/80 text-gray-400 hover:text-gray-200 p-1 rounded text-[10px] flex items-center gap-0.5 transition-colors"
        >
          {isFullscreen ? <Minimize2 size={12} /> : <Maximize2 size={12} />}
        </button>
      </div>

      {showLayers && (
        <div className="absolute top-10 left-2 z-[1000] bg-gray-900/95 border border-gray-700 rounded p-2 space-y-1">
          <div className="text-[10px] text-gray-500 font-bold mb-1">CAPAS BASE</div>
          {Object.entries(baseLayers).map(([key, layer]) => (
            <button
              key={key}
              onClick={() => { setActiveBase(key); setShowLayers(false); }}
              className={`block w-full text-left text-[10px] px-2 py-0.5 rounded transition-colors ${
                activeBase === key ? "bg-green-900/30 text-green-400" : "text-gray-400 hover:text-gray-200"
              }`}
            >
              {layer.name}
            </button>
          ))}
        </div>
      )}

      {measureMode && measureDistance > 0 && (
        <div className="absolute bottom-2 left-2 z-[1000] bg-gray-900/95 border border-green-700 rounded p-2">
          <div className="text-[10px] text-green-400 font-mono">
            Distancia: {measureDistance} km
          </div>
          <button onClick={clearMeasure} className="text-[10px] text-red-400 hover:text-red-300">
            Limpiar
          </button>
        </div>
      )}

      {selectedUnit && (
        <div className="absolute top-2 right-2 z-[1000] bg-gray-900/95 border border-gray-700 rounded p-2 w-48">
          <div className="flex items-center justify-between mb-1">
            <span className="text-[10px] font-bold text-green-400">{selectedUnit.name}</span>
            <button onClick={() => setSelectedUnit(null)} className="text-gray-500 hover:text-gray-300 text-[10px]">x</button>
          </div>
          <div className="text-[10px] font-mono space-y-0.5 text-gray-400">
            <div>Tipo: <span className="text-gray-300">{selectedUnit.type}</span></div>
            <div>Estado: <span className={selectedUnit.status === "active" ? "text-green-400" : "text-yellow-400"}>{selectedUnit.status}</span></div>
            <div>Pos: <span className="text-gray-300">{selectedUnit.lat.toFixed(4)}°N {selectedUnit.lon.toFixed(4)}°E</span></div>
          </div>
        </div>
      )}

      <div ref={mapRef} className="flex-1 rounded" />
    </div>
  );
}
