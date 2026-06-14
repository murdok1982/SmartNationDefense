"use client";
import { useEffect, useRef } from "react";
import L from "leaflet";
import "leaflet/dist/leaflet.css";

interface TacticalMapProps {
  units: { id: string; name: string; type: string; lat: number; lon: number; status: string }[];
}

const unitColors: Record<string, string> = {
  INF: "#3ddc84",
  ARM: "#f59e0b",
  REC: "#3498db",
  LOG: "#9ca3af",
  ART: "#e94560",
};

function createUnitIcon(type: string, name: string) {
  const color = unitColors[type] || "#3ddc84";
  const svg = `
    <svg xmlns="http://www.w3.org/2000/svg" width="28" height="28" viewBox="0 0 28 28">
      <circle cx="14" cy="14" r="12" fill="${color}" fill-opacity="0.3" stroke="${color}" stroke-width="2"/>
      <circle cx="14" cy="14" r="4" fill="${color}"/>
    </svg>`;
  return L.divIcon({
    html: svg,
    className: "",
    iconSize: [28, 28],
    iconAnchor: [14, 14],
  });
}

export default function TacticalMap({ units }: TacticalMapProps) {
  const mapRef = useRef<HTMLDivElement>(null);
  const mapInstanceRef = useRef<L.Map | null>(null);

  useEffect(() => {
    if (!mapRef.current || mapInstanceRef.current) return;

    const map = L.map(mapRef.current, {
      center: [40.4168, -3.7038],
      zoom: 6,
      zoomControl: true,
      attributionControl: true,
    });

    L.tileLayer("https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png", {
      attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OSM</a> &copy; <a href="https://carto.com/">CARTO</a>',
      subdomains: "abcd",
      maxZoom: 19,
    }).addTo(map);

    units.forEach(u => {
      const marker = L.marker([u.lat, u.lon], { icon: createUnitIcon(u.type, u.name) }).addTo(map);
      marker.bindTooltip(`<b>${u.name}</b><br/>Tipo: ${u.type}<br/>Estado: ${u.status}`, {
        className: "bg-gray-900 text-green-400 border border-gray-600 font-mono text-xs",
      });
    });

    mapInstanceRef.current = map;

    return () => {
      map.remove();
      mapInstanceRef.current = null;
    };
  }, []);

  useEffect(() => {
    const map = mapInstanceRef.current;
    if (!map) return;

    const layerGroup = (map as unknown as { _unitLayers?: L.LayerGroup })._unitLayers;
    if (layerGroup) {
      map.removeLayer(layerGroup);
    }

    const group = L.layerGroup();
    units.forEach(u => {
      const marker = L.marker([u.lat, u.lon], { icon: createUnitIcon(u.type, u.name) });
      marker.bindTooltip(`<b>${u.name}</b><br/>Tipo: ${u.type}<br/>Estado: ${u.status}`, {
        className: "bg-gray-900 text-green-400 border border-gray-600 font-mono text-xs",
      });
      group.addLayer(marker);
    });
    group.addTo(map);
    (map as unknown as { _unitLayers: L.LayerGroup })._unitLayers = group;
  }, [units]);

  return <div ref={mapRef} className="w-full h-full rounded" style={{ minHeight: "250px" }} />;
}
