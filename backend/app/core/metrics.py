# -*- coding: utf-8 -*-
"""Métricas Prometheus de SESIS-FEDERATION.

Expone contadores/Histogramas HTTP reales (alimentados por el middleware de
`app.main`) y gauges de estado por módulo, de modo que los dashboards de
Grafana provisionados en `infra/grafana/provisioning/dashboards/` consultan
series que existen de verdad (no queries muertas).
"""

from prometheus_client import Counter, Gauge, Histogram

HTTP_REQUESTS_TOTAL = Counter(
    "sesis_http_requests_total",
    "Peticiones HTTP atendidas por método, ruta y código de estado.",
    ["method", "path", "status"],
)

HTTP_REQUEST_DURATION = Histogram(
    "sesis_http_request_duration_seconds",
    "Latencia de peticiones HTTP por método y ruta.",
    ["method", "path"],
    buckets=(0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0),
)

HTTP_ERRORS_TOTAL = Counter(
    "sesis_http_errors_total",
    "Respuestas 4xx/5xx por ruta.",
    ["path", "status"],
)

MODULE_UP = Gauge(
    "sesis_module_up",
    "Módulo montado y operativo (1) o no disponible (0).",
    ["module"],
)

SECURITY_EVENTS_TOTAL = Counter(
    "sesis_security_events_total",
    "Eventos de seguridad relevantes (auth failures, clearance denials).",
    ["event", "module"],
)

APP_INFO = Gauge(
    "sesis_app_info",
    "Información de build de la aplicación (siempre 1).",
    ["version", "environment"],
)


# Módulos observados por los dashboards de FASE 6.
OBSERVED_MODULES = (
    "c2",
    "auth",
    "osint",
    "intel",
    "tactical",
    "maven",
    "security",
    "sensors",
    "grafana",
)


def mark_modules_up(version: str, environment: str) -> None:
    """Marca todos los módulos observados como operativos al arrancar.

    Es un snapshot de provisión: los paneles muestran `sesis_module_up` como
    disponibilidad declarada por el despliegue, no como health-check activo.
    """
    for module in OBSERVED_MODULES:
        MODULE_UP.labels(module=module).set(1)
    APP_INFO.labels(version=version, environment=environment).set(1)


def record_security_event(event: str, module: str = "security") -> None:
    SECURITY_EVENTS_TOTAL.labels(event=event, module=module).inc()
