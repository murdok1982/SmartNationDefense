# -*- coding: utf-8 -*-
import asyncio
import logging
import time
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest
from starlette.requests import Request
from starlette.responses import Response

from app.core.config import settings, get_settings
from app.core.metrics import (
    HTTP_ERRORS_TOTAL,
    HTTP_REQUEST_DURATION,
    HTTP_REQUESTS_TOTAL,
    mark_modules_up,
)
from app.core.security import get_current_user, require_clearance
from app.db.session import engine, check_db_connected
from app.core.events import event_bus

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting SESIS-FEDERATION...")
    mark_modules_up(app.version, settings.ENVIRONMENT)

    # Database
    await check_db_connected()
    logger.info("Database connected")

    # Redis with retry
    redis_ok = False
    for attempt in range(5):
        try:
            from app.db.redis_pool import get_redis_pool
            r = await get_redis_pool()
            await r.ping()
            redis_ok = True
            logger.info("Redis connected")
            break
        except Exception as e:
            if attempt < 4:
                await asyncio.sleep(2 * (2 ** attempt))
                logger.warning(f"Redis retry {attempt + 1}: {e}")
            else:
                logger.warning(f"Redis unavailable after 5 retries: {e}")

    # NATS
    try:
        await event_bus.connect()
        logger.info("NATS connected")
    except Exception as e:
        logger.warning(f"NATS unavailable: {e}")

    # Init DB: siembra idempotente del admin (esquema solo via Alembic)
    from app.db.init_db import init_db
    await init_db(settings)

    yield

    from app.core.llm_orchestrator import llm as llm_orchestrator
    await llm_orchestrator.close()
    await event_bus.disconnect()
    await engine.dispose()
    logger.info("SESIS-FEDERATION stopped")


app = FastAPI(
    title="SESIS-FEDERATION",
    description="Plataforma Unificada de Gobierno Digital Militar — C4ISR",
    version="1.0.0",
    lifespan=lifespan,
)

# Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH"],
    allow_headers=["Authorization", "Content-Type", "X-API-Key"],
)

if settings.ENVIRONMENT == "production":
    app.add_middleware(TrustedHostMiddleware, allowed_hosts=["api.sesis.local"])

# Rate limiting (interno) y autenticacion (externo: establece request.state.principal)
from app.core.rate_limit import RateLimitMiddleware
from app.core.auth_middleware import AuthMiddleware
from app.db.redis_pool import get_redis_client

app.add_middleware(RateLimitMiddleware, redis_client=get_redis_client())
app.add_middleware(AuthMiddleware)


def _route_label(request: Request) -> str:
    """Etiqueta de baja cardinalidad: plantilla de ruta, no URL cruda."""
    route = request.scope.get("route")
    return getattr(route, "path", "unmatched")


@app.middleware("http")
async def prometheus_metrics_middleware(request: Request, call_next):
    """Instrumenta cada petición para los dashboards de FASE 6."""
    if request.url.path == "/metrics":
        return await call_next(request)

    started = time.perf_counter()
    try:
        response = await call_next(request)
    except Exception:
        HTTP_REQUESTS_TOTAL.labels(
            method=request.method, path=_route_label(request), status="500"
        ).inc()
        raise
    elapsed = time.perf_counter() - started
    path = _route_label(request)

    HTTP_REQUESTS_TOTAL.labels(
        method=request.method, path=path, status=str(response.status_code)
    ).inc()
    HTTP_REQUEST_DURATION.labels(method=request.method, path=path).observe(elapsed)
    if response.status_code >= 400:
        HTTP_ERRORS_TOTAL.labels(path=path, status=str(response.status_code)).inc()
    return response


@app.get("/metrics", include_in_schema=False)
async def prometheus_metrics():
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)


# Dependencia de autenticacion aplicada a todos los routers excepto health y auth
_AUTH_DEPS = [Depends(get_current_user)]

# Defensa en profundidad: autenticacion + clearance minimo RESTRICTED a nivel de
# router. Los routers que ya declaran `require_clearance` por handler conservan
# su nivel (p. ej. CONFIDENTIAL); este minimo evita endpoints "solo autenticados"
# que expongan datos clasificados (ADR-010).
_CLEARANCE_DEPS = [Depends(get_current_user), Depends(require_clearance("RESTRICTED"))]

# ── Module Routers ──

# sesis-core
from app.api.health import router as health_router
app.include_router(health_router, prefix="/api/v1", tags=["Health"])

# sesis-c2 (from SESIS)
from app.api.v1 import alerts, assets, intel, ingestion, sensors, timeline, brain
app.include_router(alerts.router, prefix="/api/v1/c2", tags=["C2"], dependencies=_AUTH_DEPS)
app.include_router(assets.router, prefix="/api/v1/c2", tags=["C2"], dependencies=_AUTH_DEPS)
app.include_router(intel.router, prefix="/api/v1/c2", tags=["C2"], dependencies=_AUTH_DEPS)
app.include_router(ingestion.router, prefix="/api/v1/c2", tags=["C2"], dependencies=_AUTH_DEPS)
app.include_router(sensors.router, prefix="/api/v1/c2", tags=["C2"], dependencies=_AUTH_DEPS)
app.include_router(timeline.router, prefix="/api/v1/c2", tags=["C2"], dependencies=_AUTH_DEPS)
app.include_router(brain.router, prefix="/api/v1/c2", tags=["C2"], dependencies=_AUTH_DEPS)

# sesis-c2 v2 (border, cyber, ew, logistics, space)
from app.api.v2 import border, cyber, ew, logistics, space, c2
app.include_router(border.router, prefix="/api/v2/border", tags=["Border"], dependencies=_AUTH_DEPS)
app.include_router(cyber.router, prefix="/api/v2/cyber", tags=["Cyber"], dependencies=_AUTH_DEPS)
app.include_router(ew.router, prefix="/api/v2/ew", tags=["EW"], dependencies=_AUTH_DEPS)
app.include_router(logistics.router, prefix="/api/v2/logistics", tags=["Logistics"], dependencies=_AUTH_DEPS)
app.include_router(space.router, prefix="/api/v2/space", tags=["Space"], dependencies=_AUTH_DEPS)
app.include_router(c2.router, prefix="/api/v2/c2", tags=["C2 v2"], dependencies=_AUTH_DEPS)

# sesis-satellite (from AEGIS-IMINT)
from app.api.satellite.router import router as satellite_router
app.include_router(satellite_router, prefix="/api/v1/satellite", tags=["Satellite", "AEGIS-IMINT"], dependencies=_CLEARANCE_DEPS)

# sesis-osint (from Atalaya)
from app.api.osint.router import router as osint_router
app.include_router(osint_router, prefix="/api/v1/osint", tags=["OSINT", "Atalaya"], dependencies=_CLEARANCE_DEPS)

# sesis-intel (from Global-Intelligence)
from app.api.intel.router import router as intel_router
app.include_router(intel_router, prefix="/api/v1/intel", tags=["Intelligence", "Global-Intel"], dependencies=_CLEARANCE_DEPS)

# sesis-agents (from SpyManager)
from app.api.agents.router import router as agents_router
app.include_router(agents_router, prefix="/api/v1/agents", tags=["Agents", "SpyManager"], dependencies=_CLEARANCE_DEPS)

# Extra agent API modules
from app.api.agents import intel_api, mesh_api, mobile_api, multimodal_api, steganography_api, threat_api, wearable_api
app.include_router(intel_api.router, prefix="/api/v1/agents/intel", tags=["Agents", "Intel"], dependencies=_CLEARANCE_DEPS)
app.include_router(mesh_api.router, prefix="/api/v1/agents/mesh", tags=["Agents", "Mesh"], dependencies=_CLEARANCE_DEPS)
app.include_router(mobile_api.router, prefix="/api/v1/agents/mobile", tags=["Agents", "Mobile"], dependencies=_CLEARANCE_DEPS)
app.include_router(multimodal_api.router, prefix="/api/v1/agents/multimodal", tags=["Agents", "Multimodal"], dependencies=_CLEARANCE_DEPS)
app.include_router(steganography_api.router, prefix="/api/v1/agents/stego", tags=["Agents", "Steganography"], dependencies=_CLEARANCE_DEPS)
app.include_router(threat_api.router, prefix="/api/v1/agents/threat", tags=["Agents", "Threat"], dependencies=_CLEARANCE_DEPS)
app.include_router(wearable_api.router, prefix="/api/v1/agents/wearable", tags=["Agents", "Wearable"], dependencies=_CLEARANCE_DEPS)

# sesis-tactical (OPORD, Wargaming, Joint Fires, BDA, PSYOPS)
from app.api.tactical import opord, wargaming, joint_fires, bda, psyops
app.include_router(opord.router, prefix="/api/v1/tactical/opord", tags=["Tactical", "OPORD"], dependencies=_CLEARANCE_DEPS)
app.include_router(wargaming.router, prefix="/api/v1/tactical/wargaming", tags=["Tactical", "Wargaming"], dependencies=_CLEARANCE_DEPS)
app.include_router(joint_fires.router, prefix="/api/v1/tactical/fires", tags=["Tactical", "Joint Fires"], dependencies=_CLEARANCE_DEPS)
app.include_router(bda.router, prefix="/api/v1/tactical/bda", tags=["Tactical", "BDA"], dependencies=_CLEARANCE_DEPS)
app.include_router(psyops.router, prefix="/api/v1/tactical/psyops", tags=["Tactical", "PSYOPS"], dependencies=_CLEARANCE_DEPS)

# sesis-sensors (IoT Mesh)
from app.api.agents import sensor_mesh_api
app.include_router(sensor_mesh_api.router, prefix="/api/v1/agents/sensors", tags=["Agents", "Sensors"], dependencies=_CLEARANCE_DEPS)

# sesis-auth (unified)
from app.api.auth import router as auth_router
app.include_router(auth_router, prefix="/api/v1/auth", tags=["Auth"])

# sesis-messaging (Mensajeria Tactica)
from app.api.v1 import messaging
app.include_router(messaging.router, prefix="/api/v1/messaging", tags=["Messaging"], dependencies=_AUTH_DEPS)

# sesis-terrain (Analisis de Terreno)
from app.api.v1 import terrain
app.include_router(terrain.router, prefix="/api/v1/terrain", tags=["Terrain"], dependencies=_AUTH_DEPS)

# sesis-logistics-v1 (Logistica Militar)
from app.api.v1 import logistics as logistics_v1
app.include_router(logistics_v1.router, prefix="/api/v1/logistics", tags=["Logistics v1"], dependencies=_AUTH_DEPS)

# sesis-aar (After Action Review)
from app.api.v1 import aar
app.include_router(aar.router, prefix="/api/v1/aar", tags=["AAR"], dependencies=_AUTH_DEPS)

# sesis-reports (Reportes Automaticos)
from app.api.v1 import reports
app.include_router(reports.router, prefix="/api/v1/reports", tags=["Reports"], dependencies=_AUTH_DEPS)

# sesis-fusion (Fusion JDL Level 2)
from app.api.v1 import fusion
app.include_router(fusion.router, prefix="/api/v1/fusion", tags=["Fusion"], dependencies=_AUTH_DEPS)

# sesis-prediction (Prediccion de Amenazas)
from app.api.v1 import prediction
app.include_router(prediction.router, prefix="/api/v1/prediction", tags=["Prediction"], dependencies=_AUTH_DEPS)

# sesis-map (Mapa Tactico)
from app.api.v1 import map as tactical_map
app.include_router(tactical_map.router, prefix="/api/v1/map", tags=["Tactical Map"], dependencies=_AUTH_DEPS)

# sesis-voice (Comandos de Voz)
from app.api.v1 import voice
app.include_router(voice.router, prefix="/api/v1/voice", tags=["Voice"], dependencies=_AUTH_DEPS)

# sesis-planning (Planificacion NATO Mejorada)
from app.api.v1 import planning
app.include_router(planning.router, prefix="/api/v1/planning", tags=["Planning"], dependencies=_AUTH_DEPS)

# sesis-maven (Computer Vision + Fusion Multisensor)
from app.api.v3.router import router as maven_router
app.include_router(maven_router, prefix="/api/v3", tags=["Maven"], dependencies=_CLEARANCE_DEPS)

# sesis-coa-v3 (Cursos de Accion Algoritmicos — Palantir Gotham)
from app.api.v3.coa import router as coa_v3_router
app.include_router(coa_v3_router, prefix="/api/v3", dependencies=_CLEARANCE_DEPS)


@app.get("/")
async def root():
    return {
        "service": "SESIS-FEDERATION",
        "version": "1.0.0",
        "status": "operational",
        "environment": settings.ENVIRONMENT,
        "llm": settings.OLLAMA_MODEL,
    }
