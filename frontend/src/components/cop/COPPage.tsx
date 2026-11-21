"use client";

import dynamic from "next/dynamic";
import { useEffect, useMemo, useState, type ReactElement } from "react";
import { useCOPStore } from "@/store/cop-store";
import { useAuthStore } from "@/store/auth-store";
import ClassificationBanner from "./ClassificationBanner";
import StatusBar from "./StatusBar";
import MissionClock from "./MissionClock";
import MessagingPanel from "./MessagingPanel";
import TerrainAnalysis from "./TerrainAnalysis";
import LogisticsPanel from "./LogisticsPanel";
import AARPanel from "./AARPanel";
import ReportsPanel from "./ReportsPanel";
import ThreatPrediction from "./ThreatPrediction";
import PlanningPanel from "./PlanningPanel";
import VoiceCommand from "./VoiceCommand";
import TacticalMapEnhanced from "./TacticalMapEnhanced";
import MultiMonitor from "./MultiMonitor";
import MavenPanel from "./MavenPanel";
import OverviewDashboard from "./OverviewDashboard";
import {
  Activity,
  ChevronRight,
  Clock,
  FileText,
  Layers,
  Layout,
  Map,
  MessageSquare,
  Mic,
  Mountain,
  Package,
  PanelLeftClose,
  PanelLeftOpen,
  Radar,
  Satellite,
  Search,
  Shield,
  Target,
} from "lucide-react";

type PanelId =
  | "overview"
  | "messages"
  | "terrain"
  | "logistics"
  | "aar"
  | "reports"
  | "threat-pred"
  | "planning"
  | "voice"
  | "map-enhanced"
  | "multi-monitor"
  | "maven";

type NavItem = {
  id: PanelId;
  label: string;
  icon: typeof Map;
  hint: string;
};

const navSections: { title: string; items: NavItem[] }[] = [
  {
    title: "Operaciones",
    items: [
      { id: "overview", label: "Vista general", icon: Radar, hint: "KPIs y estado" },
      { id: "map-enhanced", label: "Mapa avanzado", icon: Layers, hint: "Capas tácticas" },
      { id: "messages", label: "Mensajería", icon: MessageSquare, hint: "Enlaces tácticos" },
    ],
  },
  {
    title: "Inteligencia",
    items: [
      { id: "threat-pred", label: "Amenazas", icon: Target, hint: "Predicción" },
      { id: "terrain", label: "Terreno", icon: Mountain, hint: "Análisis GEOINT" },
      { id: "planning", label: "Planificación", icon: Map, hint: "OPORD / COA" },
    ],
  },
  {
    title: "Soporte",
    items: [
      { id: "logistics", label: "Logística", icon: Package, hint: "Suministros" },
      { id: "reports", label: "Reportes", icon: FileText, hint: "Productos" },
      { id: "aar", label: "AAR", icon: Clock, hint: "Lecciones" },
    ],
  },
  {
    title: "Sistema",
    items: [
      { id: "voice", label: "Voz", icon: Mic, hint: "Comandos" },
      { id: "multi-monitor", label: "Multi-monitor", icon: Layout, hint: "Mosaicos" },
      { id: "maven", label: "Maven Fusion", icon: Satellite, hint: "Fusión multi-INT" },
    ],
  },
];

const allPanels = navSections.flatMap((section) => section.items);

const panelRenderers: Record<Exclude<PanelId, "overview">, () => ReactElement> = {
  "map-enhanced": () => <TacticalMapEnhanced />,
  messages: () => <MessagingPanel />,
  terrain: () => <TerrainAnalysis />,
  logistics: () => <LogisticsPanel />,
  aar: () => <AARPanel />,
  reports: () => <ReportsPanel />,
  "threat-pred": () => <ThreatPrediction />,
  planning: () => <PlanningPanel />,
  voice: () => <VoiceCommand />,
  "multi-monitor": () => <MultiMonitor />,
  maven: () => <MavenPanel />,
};

export default function COPPage() {
  const { setClassification, fetchAll } = useCOPStore();
  const { clearance } = useAuthStore();
  const [activePanel, setActivePanel] = useState<PanelId>("overview");
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
  const [query, setQuery] = useState("");

  useEffect(() => {
    if (clearance) setClassification(clearance.replace("_", " "));
  }, [clearance, setClassification]);

  useEffect(() => {
    void fetchAll();
    const interval = setInterval(() => void fetchAll(), 60000);
    return () => clearInterval(interval);
  }, [fetchAll]);

  const filteredSections = useMemo(() => {
    const q = query.trim().toLowerCase();
    if (!q) return navSections;
    return navSections
      .map((section) => ({
        ...section,
        items: section.items.filter(
          (item) =>
            item.label.toLowerCase().includes(q) ||
            item.hint.toLowerCase().includes(q) ||
            section.title.toLowerCase().includes(q),
        ),
      }))
      .filter((section) => section.items.length > 0);
  }, [query]);

  const activeMeta = allPanels.find((panel) => panel.id === activePanel);
  const ActiveIcon = activeMeta?.icon ?? Radar;

  return (
    <div className="flex h-screen flex-col overflow-hidden bg-background text-ink">
      <ClassificationBanner />

      <header className="z-30 shrink-0 border-b border-stroke bg-surface/85 backdrop-blur-md">
        <div className="flex items-center gap-3 px-3 py-2 sm:px-4">
          <div className="flex min-w-0 items-center gap-2.5">
            <span className="relative flex h-8 w-8 shrink-0 items-center justify-center rounded-lg border border-accent/30 bg-accent/10 text-accent">
              <Shield size={16} />
              <span className="absolute inset-0 rounded-lg ring-1 ring-inset ring-white/5" />
            </span>
            <div className="min-w-0 leading-tight">
              <p className="truncate text-xs font-semibold tracking-[0.16em] text-ink">SESIS-FEDERATION</p>
              <p className="hidden truncate text-3xs uppercase tracking-[0.2em] text-ink-faint sm:block">
                Command Center · C4ISR
              </p>
            </div>
          </div>

          <nav aria-label="Ruta actual" className="hidden min-w-0 items-center gap-1.5 text-3xs text-ink-faint xl:flex">
            <ChevronRight size={11} />
            <span className="uppercase tracking-[0.16em]">Operaciones</span>
            <ChevronRight size={11} />
            <span className="flex min-w-0 items-center gap-1.5 text-ink-muted">
              <ActiveIcon size={11} className="shrink-0" />
              <span className="truncate">{activeMeta?.label}</span>
            </span>
          </nav>

          <div className="ml-auto flex shrink-0 items-center gap-2">
            <label className="relative hidden items-center lg:flex">
              <Search size={13} className="pointer-events-none absolute left-2.5 text-ink-faint" />
              <input
                value={query}
                onChange={(event) => setQuery(event.target.value)}
                placeholder="Buscar módulo…"
                aria-label="Buscar módulo"
                className="input-field !w-44 !py-1.5 !pl-8 !text-2xs xl:!w-52"
              />
            </label>
            <MissionClock />
          </div>
        </div>
        <StatusBar />
      </header>

      <div className="flex min-h-0 flex-1">
        {/* Rail de navegación (desktop) */}
        <aside
          className={`hidden h-full shrink-0 flex-col border-r border-stroke bg-surface-sunken/60 transition-[width] duration-200 lg:flex ${
            sidebarCollapsed ? "w-[68px]" : "w-60"
          }`}
        >
          <div className="flex items-center justify-between px-3 py-2.5">
            {!sidebarCollapsed && (
              <span className="text-3xs font-semibold uppercase tracking-[0.18em] text-ink-faint">
                Módulos
              </span>
            )}
            <button
              type="button"
              onClick={() => setSidebarCollapsed((value) => !value)}
              className="rounded-md border border-transparent p-1 text-ink-faint transition-colors hover:border-stroke hover:text-ink"
              aria-label={sidebarCollapsed ? "Expandir navegación" : "Colapsar navegación"}
            >
              {sidebarCollapsed ? <PanelLeftOpen size={15} /> : <PanelLeftClose size={15} />}
            </button>
          </div>

          <div className="flex-1 space-y-4 overflow-y-auto px-2 pb-3 scrollbar-military">
            {filteredSections.map((section) => (
              <div key={section.title}>
                {!sidebarCollapsed && (
                  <p className="mb-1 px-2 text-3xs font-semibold uppercase tracking-[0.18em] text-ink-faint">
                    {section.title}
                  </p>
                )}
                <div className="space-y-0.5">
                  {section.items.map((item) => {
                    const Icon = item.icon;
                    const active = activePanel === item.id;
                    return (
                      <button
                        key={item.id}
                        type="button"
                        onClick={() => setActivePanel(item.id)}
                        aria-current={active ? "page" : undefined}
                        title={sidebarCollapsed ? item.label : undefined}
                        className={`rail-item ${active ? "rail-item-active" : ""} ${
                          sidebarCollapsed ? "justify-center px-0" : ""
                        }`}
                      >
                        <Icon size={15} className="shrink-0" />
                        {!sidebarCollapsed && (
                          <span className="min-w-0 flex-1 truncate">
                            {item.label}
                            <span className="mt-0.5 block truncate text-3xs font-normal text-ink-faint">
                              {item.hint}
                            </span>
                          </span>
                        )}
                      </button>
                    );
                  })}
                </div>
              </div>
            ))}
            {filteredSections.length === 0 && (
              <p className="px-2 py-4 text-center text-3xs text-ink-faint">
                Sin módulos que coincidan con “{query}”.
              </p>
            )}
          </div>

          {!sidebarCollapsed && (
            <div className="border-t border-stroke px-3 py-2.5 text-3xs text-ink-faint">
              <p className="flex items-center gap-1.5">
                <span className="status-dot status-operational" aria-hidden="true" />
                Núcleo C2 v3.0
              </p>
              <p className="mt-1 font-mono text-[10px] text-ink-faint">build 2026.11 · modular monolith</p>
            </div>
          )}
        </aside>

        {/* Contenido */}
        <main className="min-h-0 min-w-0 flex-1 overflow-y-auto p-3 sm:p-4">
          <div className="mx-auto w-full max-w-[1680px]">
            {activePanel === "overview" ? (
              <OverviewDashboard />
            ) : (
              <div className="animate-fade-in space-y-3">
                <div className="flex flex-wrap items-center justify-between gap-2">
                  <div className="flex items-center gap-2">
                    <span className="flex h-7 w-7 items-center justify-center rounded-lg border border-stroke bg-surface-raised text-accent">
                      <ActiveIcon size={14} />
                    </span>
                    <div>
                      <h1 className="text-sm font-semibold tracking-tight text-ink">{activeMeta?.label}</h1>
                      <p className="text-3xs text-ink-faint">{activeMeta?.hint}</p>
                    </div>
                  </div>
                  <span className="badge badge-neutral">
                    <Activity size={10} />
                    módulo operativo
                  </span>
                </div>
                {panelRenderers[activePanel as Exclude<PanelId, "overview">]?.()}
              </div>
            )}
          </div>
        </main>
      </div>

      {/* Navegación inferior (móvil) */}
      <nav
        aria-label="Navegación de módulos"
        className="flex shrink-0 gap-1 overflow-x-auto border-t border-stroke bg-surface/95 px-2 py-1.5 backdrop-blur lg:hidden"
      >
        {allPanels.map((item) => {
          const Icon = item.icon;
          const active = activePanel === item.id;
          return (
            <button
              key={item.id}
              type="button"
              onClick={() => setActivePanel(item.id)}
              aria-current={active ? "page" : undefined}
              className={`flex min-w-[64px] flex-col items-center gap-1 rounded-lg px-2 py-1.5 text-[10px] font-medium transition-colors ${
                active ? "bg-accent/10 text-accent" : "text-ink-faint hover:text-ink"
              }`}
            >
              <Icon size={16} />
              <span className="truncate">{item.label.split(" ")[0]}</span>
            </button>
          );
        })}
      </nav>
    </div>
  );
}
