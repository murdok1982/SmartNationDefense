"use client";

import { useMemo } from "react";

interface TacticalMapProps {
  units: { id: string; name: string; type: string; lat: number; lon: number; status: string }[];
}

const unitColors: Record<string, string> = {
  INF: "#34d399",
  ARM: "#fbbf24",
  REC: "#60a5fa",
  LOG: "#94a3b8",
  ART: "#f87171",
  AIR: "#22d3ee",
  NAV: "#a78bfa",
};

const WIDTH = 1000;
const HEIGHT = 600;
const PAD = 90;

const DEFAULT_BOUNDS = { minLat: 36, maxLat: 44, minLon: -10, maxLon: 4 };

function project(
  lat: number,
  lon: number,
  bounds: { minLat: number; maxLat: number; minLon: number; maxLon: number },
): { x: number; y: number } {
  const lonSpan = bounds.maxLon - bounds.minLon || 1;
  const latSpan = bounds.maxLat - bounds.minLat || 1;
  const x = PAD + ((lon - bounds.minLon) / lonSpan) * (WIDTH - PAD * 2);
  const y = HEIGHT - PAD - ((lat - bounds.minLat) / latSpan) * (HEIGHT - PAD * 2);
  return { x, y };
}

/**
 * Mapa táctico autocontenido.
 *
 * No usa teselas externas: dibuja una retícula geográfica y las posiciones
 * reales de las unidades en SVG. Esto evita fugas de posiciones a terceros y
 * elimina la dependencia de claves de proveedores de mapas.
 */
export default function TacticalMap({ units }: TacticalMapProps) {
  const validUnits = useMemo(
    () =>
      units.filter(
        (u) => Number.isFinite(u.lat) && Number.isFinite(u.lon) && !(u.lat === 0 && u.lon === 0),
      ),
    [units],
  );

  const bounds = useMemo(() => {
    if (validUnits.length === 0) return DEFAULT_BOUNDS;
    const lats = validUnits.map((u) => u.lat);
    const lons = validUnits.map((u) => u.lon);
    const minLat = Math.min(...lats);
    const maxLat = Math.max(...lats);
    const minLon = Math.min(...lons);
    const maxLon = Math.max(...lons);
    const latPad = Math.max(0.35, (maxLat - minLat) * 0.25);
    const lonPad = Math.max(0.35, (maxLon - minLon) * 0.25);
    return {
      minLat: minLat - latPad,
      maxLat: maxLat + latPad,
      minLon: minLon - lonPad,
      maxLon: maxLon + lonPad,
    };
  }, [validUnits]);

  const gridLines = useMemo(() => {
    const lines: { x1: number; y1: number; x2: number; y2: number; major: boolean }[] = [];
    const cols = 12;
    const rows = 8;
    for (let i = 0; i <= cols; i += 1) {
      const x = PAD + (i / cols) * (WIDTH - PAD * 2);
      lines.push({ x1: x, y1: PAD, x2: x, y2: HEIGHT - PAD, major: i % 3 === 0 });
    }
    for (let j = 0; j <= rows; j += 1) {
      const y = PAD + (j / rows) * (HEIGHT - PAD * 2);
      lines.push({ x1: PAD, y1: y, x2: WIDTH - PAD, y2: y, major: j % 2 === 0 });
    }
    return lines;
  }, []);

  return (
    <svg
      viewBox={`0 0 ${WIDTH} ${HEIGHT}`}
      preserveAspectRatio="xMidYMid slice"
      className="h-full w-full"
      role="img"
      aria-label={
        validUnits.length
          ? `Mapa táctico con ${validUnits.length} unidades desplegadas`
          : "Mapa táctico sin unidades desplegadas"
      }
    >
      <defs>
        <radialGradient id="tactical-glow" cx="50%" cy="50%" r="65%">
          <stop offset="0%" stopColor="#0e2a3a" stopOpacity="0.85" />
          <stop offset="100%" stopColor="#070d18" stopOpacity="1" />
        </radialGradient>
        <pattern id="tactical-hatch" width="6" height="6" patternUnits="userSpaceOnUse">
          <path d="M0 6 L6 0" stroke="#12243a" strokeWidth="0.6" />
        </pattern>
      </defs>

      <rect width={WIDTH} height={HEIGHT} fill="url(#tactical-glow)" />
      <rect width={WIDTH} height={HEIGHT} fill="url(#tactical-hatch)" opacity="0.25" />

      {/* Retícula */}
      <g>
        {gridLines.map((line, index) => (
          <line
            key={index}
            x1={line.x1}
            y1={line.y1}
            x2={line.x2}
            y2={line.y2}
            stroke={line.major ? "#1d3350" : "#14273d"}
            strokeWidth={line.major ? 0.9 : 0.6}
            opacity={line.major ? 0.9 : 0.55}
          />
        ))}
      </g>

      {/* Marco HUD */}
      <rect
        x={PAD}
        y={PAD}
        width={WIDTH - PAD * 2}
        height={HEIGHT - PAD * 2}
        fill="none"
        stroke="#22d3ee"
        strokeOpacity="0.25"
        strokeWidth="1"
      />
      {[
        [PAD, PAD, 1, 1],
        [WIDTH - PAD, PAD, -1, 1],
        [PAD, HEIGHT - PAD, 1, -1],
        [WIDTH - PAD, HEIGHT - PAD, -1, -1],
      ].map(([x, y, dx, dy], index) => (
        <path
          key={index}
          d={`M${x + dx * 18} ${y} L${x} ${y} L${x} ${y + dy * 18}`}
          fill="none"
          stroke="#22d3ee"
          strokeOpacity="0.6"
          strokeWidth="1.4"
        />
      ))}

      {/* Etiquetas de borde */}
      <text x={PAD} y={PAD - 10} fill="#778bab" fontSize="11" fontFamily="monospace">
        {bounds.maxLat.toFixed(2)}°N
      </text>
      <text x={PAD} y={HEIGHT - PAD + 18} fill="#778bab" fontSize="11" fontFamily="monospace">
        {bounds.minLat.toFixed(2)}°N
      </text>
      <text
        x={WIDTH - PAD}
        y={HEIGHT - PAD + 18}
        fill="#778bab"
        fontSize="11"
        fontFamily="monospace"
        textAnchor="end"
      >
        {bounds.maxLon.toFixed(2)}°E
      </text>
      <text x={WIDTH / 2} y={HEIGHT - PAD + 18} fill="#778bab" fontSize="11" fontFamily="monospace" textAnchor="middle">
        MGRS · WGS84
      </text>

      {/* Unidades */}
      {validUnits.map((unit) => {
        const { x, y } = project(unit.lat, unit.lon, bounds);
        const color = unitColors[unit.type?.toUpperCase()] || "#34d399";
        const active = /ACTIVE|OPERATIONAL|READY|ONLINE/i.test(unit.status || "");
        return (
          <g key={unit.id}>
            <circle cx={x} cy={y} r={18} fill={color} fillOpacity={active ? 0.08 : 0.04} stroke={color} strokeOpacity={0.25} />
            <circle cx={x} cy={y} r={9} fill="none" stroke={color} strokeWidth={1.2} strokeOpacity={0.7} />
            <circle cx={x} cy={y} r={3.6} fill={color} />
            <line x1={x} y1={y - 14} x2={x} y2={y - 22} stroke={color} strokeWidth={1} strokeOpacity={0.6} />
            <text
              x={x}
              y={y - 27}
              fill="#cbd7ea"
              fontSize="11"
              fontFamily="monospace"
              textAnchor="middle"
            >
              {unit.name}
            </text>
            <text x={x} y={y + 30} fill="#7f93b4" fontSize="9.5" fontFamily="monospace" textAnchor="middle">
              {unit.type} · {unit.status}
            </text>
          </g>
        );
      })}

      {/* Cruz central de referencia */}
      <g stroke="#22d3ee" strokeOpacity="0.35" strokeWidth="1">
        <line x1={WIDTH / 2 - 12} y1={HEIGHT / 2} x2={WIDTH / 2 + 12} y2={HEIGHT / 2} />
        <line x1={WIDTH / 2} y1={HEIGHT / 2 - 12} x2={WIDTH / 2} y2={HEIGHT / 2 + 12} />
      </g>

      {validUnits.length === 0 && (
        <text
          x={WIDTH / 2}
          y={HEIGHT / 2 + 34}
          fill="#778bab"
          fontSize="12"
          fontFamily="monospace"
          textAnchor="middle"
        >
          SIN TELEMETRÍA DE POSICIÓN
        </text>
      )}
    </svg>
  );
}
