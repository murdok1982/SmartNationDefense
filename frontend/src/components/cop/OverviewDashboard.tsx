"use client";

import dynamic from "next/dynamic";
import { useMemo } from "react";
import {
  Activity,
  AlertTriangle,
  Crosshair,
  MapPin,
  Radar,
  RefreshCw,
  Radio,
  ShieldCheck,
  Signal,
} from "lucide-react";
import { useCOPStore } from "@/store/cop-store";
import { useAuthStore } from "@/store/auth-store";
import { useApiData } from "@/lib/use-api-data";
import { apiFetch } from "@/lib/api";
import Panel from "@/components/ui/Panel";
import KpiCard from "@/components/ui/KpiCard";
import RadialGauge from "@/components/ui/RadialGauge";
import Sparkline from "@/components/ui/Sparkline";
import StatusPill from "@/components/ui/StatusPill";
import EmptyState from "@/components/ui/EmptyState";
import Skeleton from "@/components/ui/Skeleton";

const TacticalMap = dynamic(() => import("./TacticalMap"), { ssr: false });

const severityWeight: Record<string, number> = { critical: 10, high: 7, medium: 4, low: 1 };

function relativeTime(iso: string): string {
  const then = new Date(iso).getTime();
  if (Number.isNaN(then)) return "—";
  const diff = Math.max(0, Date.now() - then);
  const mins = Math.floor(diff / 60000);
  if (mins < 1) return "ahora";
  if (mins < 60) return `hace ${mins}m`;
  const hours = Math.floor(mins / 60);
  if (hours < 24) return `hace ${hours}h`;
  return `hace ${Math.floor(hours / 24)}d`;
}

function severityTone(severity: string): "danger" | "warning" | "info" | "neutral" {
  if (severity === "critical") return "danger";
  if (severity === "high") return "warning";
  if (severity === "medium") return "info";
  return "neutral";
}

export default function OverviewDashboard() {
  const { state, loading, error, fetchAll, lastFetch } = useCOPStore();
  const { clearance, username } = useAuthStore();

  const health = useApiData(
    // `/health` es público: sin token no se dispara el flujo de refresh en 401.
    () => apiFetch<{ status: string; service?: string }>("/api/v1/health", { auth: false }),
    { pollMs: 30000 },
  );

  const apiOk = !health.error && health.data?.status === "ok";

  const metrics = useMemo(() => {
    const units = state.units;
    const alerts = state.alerts;
    const threats = state.threats;
    const sensors = state.sensors;

    const activeUnits = units.filter((u) =>
      ["ACTIVE", "OPERATIONAL", "READY", "ONLINE"].includes((u.status || "").toUpperCase()),
    ).length;
    const onlineSensors = sensors.filter((s) =>
      ["ONLINE", "ACTIVE", "OPERATIONAL"].includes((s.status || "").toUpperCase()),
    ).length;
    const criticalAlerts = alerts.filter((a) => a.severity === "critical").length;
    const highAlerts = alerts.filter((a) => a.severity === "high").length;
    const maxThreat = threats.reduce((acc, t) => Math.max(acc, t.severity), 0);

    const hasTelemetry = units.length + sensors.length > 0;
    const unitRatio = units.length ? activeUnits / units.length : 0;
    const sensorRatio = sensors.length ? onlineSensors / sensors.length : 0;
    const penalty = Math.min(35, criticalAlerts * 9 + highAlerts * 4);
    const readiness = hasTelemetry
      ? Math.round(Math.max(0, Math.min(100, 58 + unitRatio * 22 + sensorRatio * 14 + (apiOk ? 6 : -10) - penalty)))
      : 0;

    const threatIndex = Math.round(Math.min(100, maxThreat * 10));
    const spark = alerts
      .slice(0, 18)
      .reverse()
      .map((a) => severityWeight[a.severity] ?? 1);

    return {
      units,
      activeUnits,
      alerts,
      criticalAlerts,
      highAlerts,
      threats,
      sensors,
      onlineSensors,
      maxThreat,
      hasTelemetry,
      readiness,
      threatIndex,
      spark,
    };
  }, [state, apiOk]);

  const tone = !metrics.hasTelemetry
    ? "info"
    : metrics.readiness >= 80
      ? "success"
      : metrics.readiness >= 55
        ? "accent"
        : "warning";
  const threatTone = metrics.threatIndex >= 70 ? "danger" : metrics.threatIndex >= 40 ? "warning" : "success";
  const threatHasData = metrics.threats.length > 0;
  const threatLabel = !threatHasData
    ? "sin datos"
    : metrics.threatIndex >= 70
      ? "crítico"
      : metrics.threatIndex >= 40
        ? "elevado"
        : "bajo";
  const readinessBadge = error ? "degradado" : loading ? "sincronizando" : "en vivo";

  const lastSync = lastFetch ? new Date(lastFetch).toLocaleTimeString("es-ES", { hour12: false }) : "—";

  return (
    <div className="space-y-3">
      {/* Contexto de sesión */}
      <div className="flex flex-wrap items-center justify-between gap-2">
        <div>
          <h1 className="text-sm font-semibold tracking-tight text-ink">Vista general de operaciones</h1>
          <p className="mt-0.5 text-3xs text-ink-faint">
            {username ? `Operador ${username}` : "Operador"} · Clasificación {clearance ?? "sin sesión"} · Última sincronización {lastSync}
          </p>
        </div>
        <div className="flex items-center gap-2">
          <StatusPill tone={apiOk ? "success" : "danger"} pulse={!apiOk}>
            {apiOk ? "Enlace operativo" : "Sin enlace"}
          </StatusPill>
          <button
            type="button"
            onClick={() => void fetchAll()}
            className="btn-ghost"
            disabled={loading}
          >
            <RefreshCw size={12} className={loading ? "animate-spin" : undefined} />
            {loading ? "Sincronizando" : "Sincronizar"}
          </button>
        </div>
      </div>

      {error && (
        <div
          role="alert"
          className="flex items-start justify-between gap-3 rounded-lg border border-signal-danger/30 bg-signal-danger/10 px-3 py-2 text-xs text-signal-danger"
        >
          <span className="flex items-start gap-2">
            <AlertTriangle size={14} className="mt-0.5 shrink-0" />
            Sincronización incompleta: {error}
          </span>
          <button type="button" onClick={() => void fetchAll()} className="btn-ghost !py-1 !text-3xs">
            Reintentar
          </button>
        </div>
      )}

      {/* KPIs */}
      <div className="grid grid-cols-2 gap-3 xl:grid-cols-4">
        <KpiCard
          label="Unidades activas"
          value={metrics.activeUnits}
          unit={`/ ${metrics.units.length}`}
          hint={metrics.units.length ? "Telemetría ORBAT + Blue Force" : "Sin telemetría de unidades"}
          tone="accent"
          icon={<Crosshair size={14} />}
          loading={loading && metrics.units.length === 0}
        />
        <KpiCard
          label="Alertas críticas"
          value={metrics.criticalAlerts}
          hint={`${metrics.highAlerts} de severidad alta`}
          tone={metrics.criticalAlerts > 0 ? "danger" : "success"}
          icon={<AlertTriangle size={14} />}
          loading={loading && metrics.alerts.length === 0}
        />
        <KpiCard
          label="Amenazas detectadas"
          value={metrics.threats.length}
          hint={metrics.threats.length ? `Índice máximo ${metrics.maxThreat}/10` : "Sin evaluación activa"}
          tone={metrics.threats.length ? "warning" : "neutral"}
          icon={<Radar size={14} />}
          loading={loading && metrics.threats.length === 0}
        />
        <KpiCard
          label="Sensores en línea"
          value={metrics.onlineSensors}
          unit={`/ ${metrics.sensors.length}`}
          hint={metrics.sensors.length ? "Fuentes C2 reportando" : "Sin fuentes registradas"}
          tone={metrics.onlineSensors > 0 ? "success" : "neutral"}
          icon={<Radio size={14} />}
          loading={loading && metrics.sensors.length === 0}
        />
      </div>

      {/* Cuerpo principal */}
      <div className="grid grid-cols-1 gap-3 xl:grid-cols-12">
        {/* Columna izquierda */}
        <div className="flex flex-col gap-3 xl:col-span-3">
          <Panel
            title="Preparación"
            icon={<ShieldCheck size={13} />}
            actions={<span className="badge badge-neutral">{readinessBadge}</span>}
          >
            <div className="flex flex-col items-center gap-3">
              <RadialGauge
                value={metrics.readiness}
                label="Operatividad"
                sublabel={metrics.hasTelemetry ? "unidades + sensores" : "sin telemetría"}
                tone={tone}
                size={150}
              />
              <div className="w-full space-y-2">
                {[
                  { label: "Enlace API", ok: apiOk, detail: apiOk ? "operativo" : "sin conexión" },
                  {
                    label: "Unidades",
                    ok: metrics.units.length > 0 && metrics.activeUnits === metrics.units.length,
                    detail: `${metrics.activeUnits}/${metrics.units.length}`,
                  },
                  {
                    label: "Sensores",
                    ok: metrics.sensors.length > 0 && metrics.onlineSensors === metrics.sensors.length,
                    detail: `${metrics.onlineSensors}/${metrics.sensors.length}`,
                  },
                  {
                    label: "Alertas críticas",
                    ok: apiOk && metrics.criticalAlerts === 0,
                    detail: metrics.criticalAlerts === 0 ? "ninguna" : `${metrics.criticalAlerts}`,
                  },
                ].map((row) => (
                  <div key={row.label} className="flex items-center justify-between gap-2 text-2xs">
                    <span className="flex items-center gap-2 text-ink-muted">
                      <span
                        className={`status-dot ${row.ok ? "status-operational" : "status-degraded"}`}
                        aria-hidden="true"
                      />
                      {row.label}
                    </span>
                    <span className="font-mono text-3xs text-ink-faint">{row.detail}</span>
                  </div>
                ))}
              </div>
            </div>
          </Panel>

          <Panel title="Actividad de alertas" icon={<Activity size={13} />}>
            {metrics.spark.length === 0 ? (
              loading ? (
                <div className="space-y-2" aria-hidden="true">
                  <Skeleton className="h-10" />
                  <Skeleton className="h-2.5 w-2/3" />
                </div>
              ) : (
                <EmptyState
                  compact
                  icon={<Activity size={14} />}
                  title="Sin actividad registrada"
                  description="No hay alertas en la ventana actual. El indicador se actualizará con la próxima sincronización."
                />
              )
            ) : (
              <>
                <Sparkline
                  values={metrics.spark}
                  tone={metrics.criticalAlerts > 0 ? "danger" : "accent"}
                  ariaLabel="Peso de las últimas alertas"
                />
                <div className="mt-2 flex items-center justify-between text-3xs text-ink-faint">
                  <span>Últimas {metrics.spark.length} alertas</span>
                  <span className="font-mono">pico {Math.max(...metrics.spark)}/10</span>
                </div>
              </>
            )}
          </Panel>
        </div>

        {/* Centro: mapa + feed */}
        <div className="flex flex-col gap-3 xl:col-span-6">
          <Panel
            title="Mapa táctico"
            subtitle="Posiciones Blue Force / ORBAT"
            icon={<MapPin size={13} />}
            actions={
              <span className="badge badge-info">{metrics.units.length} unidades</span>
            }
            bodyClassName="p-0"
            dense
          >
            <div className="relative h-[300px] overflow-hidden rounded-b-xl bg-surface-sunken sm:h-[360px] xl:h-[420px]">
              <TacticalMap units={metrics.units} />
              {metrics.units.length === 0 && (
                <div className="absolute inset-0 z-20 flex items-center justify-center bg-surface-sunken/80 p-4">
                  <EmptyState
                    icon={<MapPin size={16} />}
                    title="Sin posiciones reportadas"
                    description="El mapa se poblará cuando ORBAT o Blue Force publiquen telemetría."
                    action={
                      <button type="button" className="btn-ghost !py-1 !text-3xs" onClick={() => void fetchAll()}>
                        Solicitar telemetría
                      </button>
                    }
                  />
                </div>
              )}
            </div>
          </Panel>

          <Panel
            title="Feed de inteligencia"
            subtitle="Productos recientes"
            icon={<Signal size={13} />}
            actions={<span className="badge badge-neutral">{state.intelFeed.length}</span>}
            bodyClassName="p-0"
            dense
          >
            <div className="max-h-64 divide-y divide-stroke/60 overflow-y-auto scrollbar-military">
              {loading && state.intelFeed.length === 0 && (
                <div className="space-y-2 p-3">
                  <Skeleton lines={3} />
                  <Skeleton lines={2} />
                </div>
              )}
              {!loading && state.intelFeed.length === 0 && (
                <EmptyState
                  compact
                  icon={<Signal size={14} />}
                  title="Sin productos de inteligencia"
                  description="El feed se llena cuando el motor de fusión publica productos."
                />
              )}
              {state.intelFeed.slice(0, 8).map((item) => (
                <article key={item.id} className="flex items-start justify-between gap-3 px-3 py-2.5">
                  <div className="min-w-0">
                    <p className="truncate text-xs font-medium text-ink">{item.title}</p>
                    <p className="mt-0.5 flex items-center gap-2 text-3xs text-ink-faint">
                      <span className="truncate font-mono">{item.source}</span>
                      <span aria-hidden="true">·</span>
                      <span className="shrink-0">{relativeTime(item.timestamp)}</span>
                    </p>
                  </div>
                  <div className="flex shrink-0 flex-col items-end gap-1">
                    <span className="badge badge-neutral">{item.classification}</span>
                    {item.confidence !== null && (
                      <span className="font-mono text-3xs text-ink-faint">
                        conf. {Math.round(item.confidence * (item.confidence <= 1 ? 100 : 1))}%
                      </span>
                    )}
                  </div>
                </article>
              ))}
            </div>
          </Panel>
        </div>

        {/* Derecha: amenazas + timeline */}
        <div className="flex flex-col gap-3 xl:col-span-3">
          <Panel
            title="Índice de amenaza"
            icon={<Radar size={13} />}
            actions={<StatusPill tone={threatHasData ? threatTone : "neutral"}>{threatLabel}</StatusPill>}
          >
            <div className="flex flex-col items-center gap-3">
              <RadialGauge
                value={metrics.threatIndex}
                label="Índice de amenaza"
                sublabel={metrics.threats.length ? `${metrics.threats.length} amenazas` : "sin evaluación"}
                tone={threatHasData ? threatTone : "info"}
                size={132}
              />
              <div className="w-full space-y-2">
                {metrics.threats.slice(0, 4).map((threat) => (
                  <div key={threat.id} className="space-y-1">
                    <div className="flex items-center justify-between gap-2 text-2xs">
                      <span className="truncate text-ink-muted">{threat.target}</span>
                      <span className="font-mono text-3xs text-ink-faint">{threat.severity}/10</span>
                    </div>
                    <div className="metric-bar" role="presentation">
                      <div
                        className={`h-full rounded-full ${
                          threat.severity >= 8
                            ? "bg-signal-danger"
                            : threat.severity >= 5
                              ? "bg-signal-warning"
                              : "bg-accent"
                        }`}
                        style={{ width: `${Math.min(100, threat.severity * 10)}%` }}
                      />
                    </div>
                  </div>
                ))}
                {loading && metrics.threats.length === 0 && (
                  <div className="space-y-2 py-1" aria-hidden="true">
                    <Skeleton className="h-2.5" />
                    <Skeleton className="h-2.5 w-4/5" />
                    <Skeleton className="h-2.5 w-3/5" />
                  </div>
                )}
                {!loading && metrics.threats.length === 0 && (
                  <EmptyState
                    compact
                    icon={<ShieldCheck size={14} />}
                    title="Sin amenazas evaluadas"
                    description="El motor de predicción requiere posiciones de unidades para calcular."
                  />
                )}
              </div>
            </div>
          </Panel>

          <Panel
            title="Línea temporal"
            subtitle="Eventos de misión"
            icon={<Activity size={13} />}
            bodyClassName="p-0"
            dense
          >
            <ol className="max-h-64 overflow-y-auto scrollbar-military">
              {loading && state.timeline.length === 0 && (
                <li className="space-y-2 p-3" aria-hidden="true">
                  <Skeleton className="h-2.5 w-4/5" />
                  <Skeleton className="h-2.5 w-3/5" />
                </li>
              )}
              {!loading && state.timeline.length === 0 && (
                <li>
                  <EmptyState
                    compact
                    icon={<Activity size={14} />}
                    title="Sin eventos de misión"
                    description="Los eventos aparecerán aquí en orden cronológico inverso."
                  />
                </li>
              )}
              {state.timeline.slice(0, 8).map((event) => (
                <li key={event.id} className="flex gap-2.5 border-b border-stroke/50 px-3 py-2 last:border-0">
                  <span
                    className={`mt-1 h-1.5 w-1.5 shrink-0 rounded-full ${
                      event.severity === "critical"
                        ? "bg-signal-danger"
                        : event.severity === "warning"
                          ? "bg-signal-warning"
                          : "bg-signal-success"
                    }`}
                    aria-hidden="true"
                  />
                  <div className="min-w-0">
                    <p className="truncate text-2xs text-ink">{event.description}</p>
                    <p className="mt-0.5 font-mono text-3xs text-ink-faint">
                      {new Date(event.timestamp).toLocaleTimeString("es-ES", { hour12: false })} · {event.type}
                    </p>
                  </div>
                </li>
              ))}
            </ol>
          </Panel>

          <Panel title="Alertas recientes" icon={<AlertTriangle size={13} />} bodyClassName="p-0" dense>
            <ul className="max-h-52 divide-y divide-stroke/60 overflow-y-auto scrollbar-military">
              {loading && metrics.alerts.length === 0 && (
                <li className="space-y-2 p-3" aria-hidden="true">
                  <Skeleton className="h-2.5 w-3/4" />
                  <Skeleton className="h-2.5 w-1/2" />
                </li>
              )}
              {!loading && metrics.alerts.length === 0 && (
                <li>
                  <EmptyState
                    compact
                    icon={<AlertTriangle size={14} />}
                    title="Bandeja vacía"
                    description="No hay alertas activas en este momento."
                  />
                </li>
              )}
              {metrics.alerts.slice(0, 6).map((alert) => (
                <li key={alert.id} className="flex items-start justify-between gap-2 px-3 py-2">
                  <div className="min-w-0">
                    <p className="truncate text-2xs text-ink">{alert.message}</p>
                    <p className="mt-0.5 font-mono text-3xs text-ink-faint">
                      {alert.source} · {relativeTime(alert.timestamp)}
                    </p>
                  </div>
                  <StatusPill tone={severityTone(alert.severity)} className="shrink-0">
                    {alert.severity}
                  </StatusPill>
                </li>
              ))}
            </ul>
          </Panel>
        </div>
      </div>
    </div>
  );
}
