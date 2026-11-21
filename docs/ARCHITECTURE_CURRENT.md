# ARCHITECTURE_CURRENT.md — Arquitectura AS-IS verificada en código

**Doc ID:** ARCH-CUR-2026-SND-001
**Proyecto:** SmartNationDefense / SESIS-FEDERATION
**Estado del documento:** `FASE 9 — regenerado desde código real`
**Fecha de medición:** 2026-11-21
**Commit de referencia:** `3152f117596bc4d5abc4fbd46a4035d1e43e5c7e`
**Árbol de trabajo:** con cambios sin commitear en frontend, backend y configuración en el momento de la medición (ver §16 y `docs/FINAL_VALIDATION_REPORT.md` §2.4).
**Autor del documento:** `@architect` (TASK-045)
**Ámbito:** descripción AS-IS. No describe el estado objetivo; para eso ver `docs/ARCHITECTURE.md`.

> **Regla de honestidad de este documento.** Cada cifra tiene un comando reproducible. Cuando algo no se pudo ejecutar en este entorno se marca `NO VERIFICADO` o `BLOQUEADO` y se explica por qué. Cuando el código contradice la documentación previa, se dice explícitamente y se cita el archivo y la línea.

---

## 0. Leyenda de verificación

| Marca | Significado |
| :--- | :--- |
| `VERIFICADO` | Comprobado en este entorno con el comando indicado, con resultado exitoso. |
| `PARCIAL` | Existe implementación real, pero no cubre todo lo que su nombre promete, o no está conectada de extremo a extremo. |
| `NO VERIFICADO` | Existe código, pero no se ejecutó la comprobación (por falta de runtime, servicio externo o tiempo). |
| `BLOQUEADO` | No se puede verificar en este entorno por una dependencia ausente (Docker, Node, red, base de datos). |
| `FALLA` | Se ejecutó la comprobación y el resultado es negativo. Se documenta el error exacto. |
| `MUERTO` | Código presente en el repositorio que no está montado o no se referencia desde el entrypoint. |

---

## 1. Snapshot ejecutivo

### 1.1 Cifras medidas

| Métrica | Valor real | Comando de verificación | Estado |
| :--- | ---: | :--- | :--- |
| Archivos Python en `backend/app` | 266 | `find backend/app -name "*.py" \| wc -l` | VERIFICADO |
| Líneas Python en `backend/app` | 26.963 | `find backend/app -name "*.py" -exec cat {} + \| wc -l` | VERIFICADO |
| Archivos Python totales en `backend/` (incluye tests/alembic) | 291 | `find backend -name "*.py" \| wc -l` | VERIFICADO |
| Líneas en `backend/app/services` | 11.872 | `find backend/app/services -name "*.py" \| xargs wc -l \| tail -1` | VERIFICADO |
| Líneas en `backend/app/api` | 9.049 | `find backend/app/api -name "*.py" \| xargs wc -l \| tail -1` | VERIFICADO |
| Líneas en `backend/app/core` | 1.666 | `find backend/app/core -name "*.py" \| xargs wc -l \| tail -1` | VERIFICADO |
| Líneas en `backend/app/db` | 1.470 | `find backend/app/db -name "*.py" \| xargs wc -l \| tail -1` | VERIFICADO |
| Paths OpenAPI | 168 | ver §1.2 | VERIFICADO |
| Operaciones OpenAPI | 177 | ver §1.2 | VERIFICADO |
| Paths `/api/v1` | 129 (134 operaciones) | ver §1.2 | VERIFICADO |
| Paths `/api/v2` | 27 (31 operaciones) | ver §1.2 | VERIFICADO |
| Paths `/api/v3` | 11 (11 operaciones) | ver §1.2 | VERIFICADO |
| Archivos de test | 21 | `ls backend/tests/test_*.py \| wc -l` | VERIFICADO |
| Tests recolectados | 157 | `python3 -m pytest backend/tests --collect-only -q` | VERIFICADO |
| Tests en verde | 157 | `SECRET_KEY="test-secret-key-32-chars-minimum!!!" python3 -m pytest backend/tests -q` | VERIFICADO |
| Cobertura suites de seguridad | 88% | `pytest --cov=app/core/security.py ... --cov-report=term` | VERIFICADO (reportado por `@qa-verifier`) |
| Archivos frontend `.ts`/`.tsx` | 45 | `find frontend/src \( -name "*.ts" -o -name "*.tsx" \) \| wc -l` | VERIFICADO |
| Líneas frontend | 8.487 | `find frontend/src \( -name "*.ts" -o -name "*.tsx" \) \| xargs wc -l \| tail -1` | VERIFICADO |
| Build frontend | `tsc` 0 errores, `next build` OK, 4 rutas | Node 20.18 en `/tmp/opencode/fe_verify` | VERIFICADO |
| SCA frontend | 0 vulnerabilidades de producción | `npm audit --omit=dev --audit-level=high` | VERIFICADO |
| Archivos Dart | 16 (15 lib + 1 test) | `find mobile -name "*.dart" \| wc -l` | VERIFICADO |
| Líneas Dart | 1.520 (1.399 lib + 121 test) | `find mobile -name "*.dart" \| xargs wc -l \| tail -1` | VERIFICADO |
| Servicios docker-compose | 12 | ver §12.1 | VERIFICADO (estático) |
| Servicios con healthcheck | 12/12 | ver §12.1 | VERIFICADO (estático) |
| Dashboards Grafana | 7 | `ls infra/grafana/provisioning/dashboards/*.json \| wc -l` | VERIFICADO |
| Alertas Prometheus | 8 | `grep -c "alert:" infra/alertmanager/alerts.yml` | VERIFICADO |
| Versiones Alembic | 4 | `ls backend/alembic/versions/*.py` | VERIFICADO |

### 1.2 Evidencia OpenAPI

Comando exacto:

```bash
cd backend
SECRET_KEY="test-secret-key-32-chars-minimum!!!" python3 -c \
  "import json; from app.main import app; print(len(app.openapi()['paths']))"
```

Conteo por prefijo (script reproducible):

```bash
python3 - <<'EOF'
import json, collections
d = json.load(open('backend/contracts/openapi.json'))
c = collections.Counter()
for p in d['paths']:
    seg = p.split('/')
    c['/'.join(seg[:3]) if p != '/' else '/'] += 1
for k, v in sorted(c.items()):
    print(v, k)
EOF
```

Resultado real:

```text
1 /
129 /api/v1
27 /api/v2
11 /api/v3
```

Conteo de operaciones (un path puede tener varios métodos):

```bash
python3 - <<'EOF'
import json
d = json.load(open('backend/contracts/openapi.json'))
print(sum(len([m for m in ops if m in ('get','post','put','patch','delete')])
          for ops in d['paths'].values()))
EOF
# 177
```

### 1.3 Runtime del entorno de medición

| Elemento | Valor | Estado |
| :--- | :--- | :--- |
| Python | `3.14.10` (`python3 --version`) | VERIFICADO |
| FastAPI | `0.115.6` (`backend/requirements.txt`) | VERIFICADO (pin) |
| SQLAlchemy | `2.0.36` | VERIFICADO (pin) |
| Pydantic | `2.10.3` | VERIFICADO (pin) |
| PostgreSQL runtime | No levantado | BLOQUEADO |
| Redis runtime | No levantado | BLOQUEADO |
| Neo4j runtime | No levantado | BLOQUEADO |
| NATS runtime | No levantado | BLOQUEADO |
| Docker | `docker not found` | BLOQUEADO |
| Node.js | 20.18 en copia `/tmp/opencode/fe_verify`; ausente en PATH local | VERIFICADO (copia) |
| Flutter SDK | 3.24.5 portable en `/tmp` | VERIFICADO (analyze + test) |

Consecuencia: la suite de tests corre con SQLite (`aiosqlite`) y dobles de Redis/NATS, no contra la infraestructura real. Esto se detalla en `docs/FINAL_VALIDATION_REPORT.md`.

---

## 2. Topografía del repositorio

### 2.1 Árbol real de primer y segundo nivel

```text
SmartNationDefense/
├── backend/
│   ├── app/
│   │   ├── agents/            # agentes OSINT/Intel (código de dominio, no API)
│   │   ├── api/               # routers HTTP
│   │   ├── core/              # seguridad, auditoría, métricas, eventos, rate limit
│   │   ├── db/                # modelos SQLAlchemy, sesión, init_db
│   │   ├── schemas/           # Pydantic schemas compartidos
│   │   ├── services/          # lógica de dominio (17 subpaquetes + __pycache__)
│   │   ├── workers/           # Celery
│   │   └── main.py            # entrypoint FastAPI
│   ├── alembic/               # migraciones reales (001..004)
│   ├── migrations/            # SQL legacy + archived/
│   ├── contracts/openapi.json # contrato generado (168 paths)
│   ├── tests/                 # 21 archivos de test
│   └── requirements.txt
├── frontend/
│   └── src/
│       ├── app/               # rutas Next.js (/, /login, /maven)
│       ├── components/cop/    # 24 componentes COP
│       ├── components/ui/     # 7 primitivas UI
│       ├── lib/               # cliente API, tipos, hook de datos
│       └── store/             # Zustand (auth, cop, maven)
├── mobile/sesis_cop/
│   └── lib/
│       ├── core/              # constants, network, theme
│       └── features/          # 6 features con pantalla
├── ml/                        # visión, anomalías, correlación, briefing
├── infra/                     # nginx, prometheus, grafana, alertmanager, ssl
├── compliance/                # ENS ALTA + STANAG 4774/4778
├── scripts/                   # validate_all, generate_keys, seed, demo
├── docs/                      # auditoría, arquitectura, este documento
├── .factory/                  # SPEC/ARCHITECTURE/TASKS/SECURITY_AUDIT
├── docker-compose.yml         # 12 servicios
├── docker-compose.demo.yml
├── .env.example
└── Makefile
```

### 2.2 Distribución de código backend por capa

| Capa | Archivos | LOC | Peso |
| :--- | ---: | ---: | ---: |
| `app/services` | — | 11.872 | 44,0 % de `app` |
| `app/api` | — | 9.049 | 33,6 % |
| `app/core` | 16 | 1.666 | 6,2 % |
| `app/db` | — | 1.470 | 5,5 % |
| `app/agents` | — | resto | ~7 % |
| `app/schemas` | 8 | resto | ~2 % |

> Nota: el desglose exacto por subpaquete se obtiene con
> `for d in backend/app/*/; do echo "$d $(find $d -name '*.py' -exec cat {} + | wc -l)"; done`.
> Los porcentajes son aritmética directa sobre las cifras medidas, no estimaciones.

### 2.3 Subpaquetes de servicios y tamaño

| Subpaquete | Archivos `.py` (incl. `__init__`) | LOC | Función declarada |
| :--- | ---: | ---: | :--- |
| `services/osint` | 36 | 3.136 | Herramientas OSINT, wrappers, grafos, informes |
| `services/intel` | 15 | — | MFA, RAG, proveedores LLM, firma |
| `services/satellite` | 14 | — | Sentinel, cambio, detección, análisis temporal |
| `services/agents` | 10 | — | Data diode, kill switch, Link16, mesh, SIEM |
| `services/tactical` | 7 | — | OPORD, COA, BDA, fires, PSYOPS, wargaming |
| `services/vision` | 4 | — | YOLO, dron, analista |
| `services/terrain` | 3 | — | Elevación con caché Redis/memoria |
| `services/fusion` | 3 | — | Motor JDL L0-L4 |
| `services/aar`, `logistics`, `mapping`, `messaging`, `planning`, `prediction`, `reports`, `voice`, `compliance` | 2 cada uno | — | Dominios tácticos |

Comando:

```bash
for d in backend/app/services/*/; do
  echo "$d $(find $d -name '*.py' | wc -l)"
done
```

---

## 3. Proceso de arranque y middleware

### 3.1 Entrypoint

Archivo: `backend/app/main.py`.

- Se crea `FastAPI(title="SESIS-FEDERATION", version="1.0.0")`.
- `lifespan` realiza, en orden:
  1. `mark_modules_up(app.version, settings.ENVIRONMENT)`.
  2. `await check_db_connected()` — fallo de base de datos es fail-fast.
  3. Conexión Redis con 5 reintentos y backoff exponencial (`asyncio.sleep(2 * 2**attempt)`).
  4. Conexión NATS; si falla, sólo warning (degradación graceful).
  5. `init_db(settings)` — siembra idempotente del usuario `admin`; exige `ADMIN_INITIAL_PASSWORD` si el usuario no existe.
- En el apagado: cierre del orquestador LLM, desconexión NATS, `engine.dispose()`.

### 3.2 Orden de middleware

El orden efectivo (Starlette añade el último primero en la pila de ejecución) es:

```text
Request
  → CORSMiddleware
  → TrustedHostMiddleware (sólo si ENVIRONMENT == "production")
  → RateLimitMiddleware (Redis)
  → AuthMiddleware (establece request.state.principal)
  → prometheus_metrics_middleware (instrumentación)
  → Router / handler
Response
```

Evidencia:

```bash
grep -n "add_middleware\|@app.middleware" backend/app/main.py
```

Consecuencias reales:

- El rate limit se evalúa antes de la autenticación; la clave se deriva de usuario si `request.state.principal` ya existe, y si no, de IP. Esto es coherente con `get_limiter_key` en `app/core/rate_limit.py`.
- `AuthMiddleware` es el que rellena `request.state.principal`; `get_current_user` vuelve a decodificar el token para las dependencias. Hay dos lecturas del JWT por petición autenticada (coste aceptado, no medido).
- El middleware de métricas usa la plantilla de ruta (`request.scope["route"].path`) para evitar cardinalidad alta. Esto es correcto y está implementado.

### 3.3 Middleware de seguridad

| Middleware | Archivo | Efecto | Estado |
| :--- | :--- | :--- | :--- |
| `CORSMiddleware` | `app/main.py` | Orígenes desde `settings.CORS_ORIGINS` (por defecto `http://localhost:3000,http://localhost:8501`) | VERIFICADO |
| `TrustedHostMiddleware` | `app/main.py` | Sólo en producción; `allowed_hosts=["api.sesis.local"]` | VERIFICADO (código) |
| `RateLimitMiddleware` | `app/core/rate_limit.py` | Ventana deslizante Redis + headers `X-RateLimit-*` + 429 con `Retry-After` | VERIFICADO (tests) |
| `AuthMiddleware` | `app/core/auth_middleware.py` | Puebla `request.state.principal` | VERIFICADO (código) |
| Métricas | `app/main.py` + `app/core/metrics.py` | `sesis_http_requests_total`, histograma, errores | VERIFICADO (TestClient) |

---

## 4. Inventario de routers y montaje real

### 4.1 Montaje en `app.main`

| Prefijo | Router(s) | Dependencias de router | Nº paths | Estado de implementación |
| :--- | :--- | :--- | ---: | :--- |
| `/api/v1` (health) | `app.api.health` | ninguna | 1 | REAL |
| `/api/v1/c2` | `v1.alerts`, `v1.assets`, `v1.intel`, `v1.ingestion`, `v1.sensors`, `v1.timeline`, `v1.brain` | `_AUTH_DEPS` | 20 | REAL con acceso a DB en varios; `intel.py` es el router C2 de productos/PIR |
| `/api/v1/satellite` | `app.api.satellite.router` | `_CLEARANCE_DEPS` | 2 | STUB (respuestas estáticas / `queued`) |
| `/api/v1/osint` | `app.api.osint.router` | `_CLEARANCE_DEPS` | 6 | STUB (listas vacías y estado fijo) |
| `/api/v1/intel` | `app.api.intel.router` | `_CLEARANCE_DEPS` | 3 | STUB (listas vacías y estado fijo) |
| `/api/v1/agents` | `app.api.agents.router` | `_CLEARANCE_DEPS` | 1 | STUB (estado fijo) |
| `/api/v1/agents/intel` | `agents.intel_api` | `_CLEARANCE_DEPS` | 1 (2 operaciones) | STUB (delegación mínima) |
| `/api/v1/agents/mesh` | `agents.mesh_api` | `_CLEARANCE_DEPS` | 2 | STUB |
| `/api/v1/agents/mobile` | `agents.mobile_api` | `_CLEARANCE_DEPS` | 2 | STUB |
| `/api/v1/agents/multimodal` | `agents.multimodal_api` | `_CLEARANCE_DEPS` | 1 | STUB |
| `/api/v1/agents/stego` | `agents.steganography_api` | `_CLEARANCE_DEPS` | 2 | STUB |
| `/api/v1/agents/threat` | `agents.threat_api` | `_CLEARANCE_DEPS` | 1 | STUB |
| `/api/v1/agents/wearable` | `agents.wearable_api` | `_CLEARANCE_DEPS` | 2 | STUB |
| `/api/v1/tactical/opord` | `tactical.opord` | `_CLEARANCE_DEPS` | 4 | REAL (delega en `enhanced_opord_service`) |
| `/api/v1/tactical/wargaming` | `tactical.wargaming` | `_CLEARANCE_DEPS` | 3 | REAL (delega en servicio) |
| `/api/v1/tactical/fires` | `tactical.joint_fires` | `_CLEARANCE_DEPS` | 3 | REAL (delega en servicio) |
| `/api/v1/tactical/bda` | `tactical.bda` | `_CLEARANCE_DEPS` | 3 | REAL (delega en servicio) |
| `/api/v1/tactical/psyops` | `tactical.psyops` | `_CLEARANCE_DEPS` | 3 | REAL (delega en servicio) |
| `/api/v1/agents/sensors` | `agents.sensor_mesh_api` | `_CLEARANCE_DEPS` | 3 | REAL (delega en `sensor_mesh`) |
| `/api/v1/auth` | `app.api.auth` | ninguna (público) | 5 | REAL (login/refresh/logout/me/register) |
| `/api/v1/messaging` | `v1.messaging` | `_AUTH_DEPS` | 6 | REAL (servicio en memoria) |
| `/api/v1/terrain` | `v1.terrain` | `_AUTH_DEPS` | 5 | REAL (proveedor externo + caché) |
| `/api/v1/logistics` | `v1.logistics` | `_AUTH_DEPS` | 7 | REAL (servicio en memoria) |
| `/api/v1/aar` | `v1.aar` | `_AUTH_DEPS` | 6 | REAL (servicio en memoria) |
| `/api/v1/reports` | `v1.reports` | `_AUTH_DEPS` | 6 | REAL (servicio en memoria) |
| `/api/v1/fusion` | `v1.fusion` | `_AUTH_DEPS` | 4 | REAL (motor JDL) |
| `/api/v1/prediction` | `v1.prediction` | `_AUTH_DEPS` | 5 | REAL (Kalman + DB) |
| `/api/v1/map` | `v1.map` | `_AUTH_DEPS` | 8 | REAL (cálculos geométricos) |
| `/api/v1/voice` | `v1.voice` | `_AUTH_DEPS` | 3 | REAL (servicio) |
| `/api/v1/planning` | `v1.planning` | `_AUTH_DEPS` | 11 | REAL (servicio OPORD) |
| `/api/v2/border` | `v2.border` | `_AUTH_DEPS` | 5 | REAL con DB (`EventStore`, `Asset`, `Sensor`) |
| `/api/v2/cyber` | `v2.cyber` | `_AUTH_DEPS` | 4 | REAL con DB |
| `/api/v2/ew` | `v2.ew` | `_AUTH_DEPS` | 4 | REAL con DB |
| `/api/v2/logistics` | `v2.logistics` | `_AUTH_DEPS` | 4 | REAL con DB |
| `/api/v2/space` | `v2.space` | `_AUTH_DEPS` | 4 | REAL con DB |
| `/api/v2/c2` | `v2.c2` | `_AUTH_DEPS` | 7 | REAL con DB |
| `/api/v3` (Maven) | `v3.router` | `_CLEARANCE_DEPS` | 3 | REAL (5 imports de servicios) |
| `/api/v3/coa` | `v3.coa` | `_CLEARANCE_DEPS` | 5 | REAL (`coa_engine`) |
| `/metrics` | función directa | ninguna (excluido del schema) | 1 | REAL |
| `/` | función directa | ninguna | 1 | REAL |

> **Hallazgo de honestidad #1.** La documentación previa (`docs/API.md`, `.factory/ARCHITECTURE.md`) afirmaba que `backend/app/api/v1/intel.py` no estaba montado. **Sí está montado**, bajo `/api/v1/c2` (`from app.api.v1 import ... intel ...` y `include_router(intel.router, prefix="/api/v1/c2")` en `main.py`). Lo que no está montado es `backend/app/api/v1/media.py`, verificado con introspección (`media mounted? False`).

> **Hallazgo de honestidad #2.** Los routers OSINT/Intel/Satellite/Agents de nivel superior son **stubs**. El código de dominio existe en `app/services/`, pero las rutas devuelven listas vacías o estados fijos. Ver §15.

### 4.2 Rutas vivas vs rutas documentadas

Comando de introspección:

```bash
cd backend
SECRET_KEY="test-secret-key-32-chars-minimum!!!" python3 - <<'EOF'
from app.main import app
routes = [r for r in app.routes if hasattr(r, "methods")]
print("routes", len(routes))
print("unique paths", len({r.path for r in routes}))
EOF
```

Resultado real: **184 objetos ruta**, **173 paths únicos**. La diferencia con los 168 del contrato se explica por:

- `/metrics` y `/` no forman parte del OpenAPI versionado en algunos conteos, y
- rutas con el mismo path y métodos distintos se agrupan de forma diferente.

El contrato `backend/contracts/openapi.json` es la fuente canónica para clientes; la introspección es la fuente para tests de seguridad.

---

## 5. Modelo de datos AS-IS

### 5.1 Entidades principales

Archivo canónico: `backend/app/db/models/persistence.py`.

| Entidad | Tabla | Campos relevantes | Estado |
| :--- | :--- | :--- | :--- |
| `User` | `users` | `id`, `username`, `email`, `hashed_password`, `role`, `classification_level`, `is_active`, `last_login`, `last_ip` | REAL, única declaración |
| `AuditLog` | `audit_log` | `id`, `ts`, `actor`, `action`, `resource_type`, `resource_id`, `context`, `prev_hash`, `row_hash`, `user_id`, `username`, `details`, `ip_address`, `user_agent`, `request_id`, `success`, `error_message` | REAL, cadena SHA-256 |
| `EventStore` | `events` | `event_id`, `event_type`, `asset_id`, `ts`, `lat/lon`, `classification_level`, `confidence_score`, `payload`, `signature` | REAL |
| `Asset` | `assets` | `id`, `kind`, `current_status`, `last_heartbeat`, `lat/lon`, `classification_level`, `metadata_json` | REAL |
| `Sensor` | sensores | `sensor_id`, estado, posición | REAL (usada por v1/sensors y v2/border) |
| `Alert` | alertas | incluye campos cifrados con `EncryptedField` | REAL |
| `Messaging` | mensajería | mensajes, hilos, TTL | REAL (servicio en memoria, modelo disponible) |
| `AAR` | after action review | informes, timeline, lecciones | REAL |
| `OPORD` | órdenes | párrafos, anexos, validación | REAL |

### 5.2 Consolidación de `User` (ADR-003)

Evidencia:

```bash
grep -rn '__tablename__ = "users"' backend/app/db/models | wc -l   # 1
python3 -c "from app.db.models import User; print(User.__tablename__)"  # users
```

`app/db/models/intel/user.py` y `app/db/models/osint/user.py` son re-exports/alias, no mapeos duplicados. `app/db/models/__init__.py` exporta `User`, `IntelUserSchema`, `OsistUserSchema`.

### 5.3 Deduplicación de auditoría (TD-011 / TASK-043)

- Existe **una** tabla canónica `audit_log`.
- `app/db/models/osint/audit_log.py` es un shim de re-export sin mapeo duplicado.
- Migración: `backend/alembic/versions/004_unify_audit_log.py`.
- Test de regresión: `backend/tests/test_audit_unified.py` (3 tests).

### 5.4 Migraciones

| Revisión | Archivo | Contenido declarado | Estado |
| :--- | :--- | :--- | :--- |
| `001_sesis_initial` | `backend/alembic/versions/001_sesis_initial.py` | Esquema inicial | VERIFICADO (existe; no ejecutado sin PostgreSQL) |
| `002_audit_chain` | `002_audit_chain.py` | Cadena de auditoría | VERIFICADO (existe) |
| `003_intel_products` | `003_intel_products.py` | Productos de inteligencia | VERIFICADO (existe; `down_revision='002_audit_chain'`) |
| `004_unify_audit_log` | `004_unify_audit_log.py` | Unificación de auditoría | VERIFICADO (existe) |

- `backend/migrations/archived/` contiene `002_intel_products.sql.legacy` y `schema_design.sql.legacy`.
- **No se ejecutó `alembic upgrade head`** en este entorno: requiere PostgreSQL y `geoalchemy2`/PostGIS operativos. Estado: `BLOQUEADO`. La comprobación usada fue `py_compile` + parseo AST, documentada en TASKS.md TASK-011.

---

## 6. Seguridad implementada (AS-IS)

### 6.1 Autenticación y tokens

| Control | Implementación | Evidencia | Estado |
| :--- | :--- | :--- | :--- |
| Hash de contraseñas | `passlib[bcrypt] 1.9.3`, `bcrypt 4.0.1` | `backend/requirements.txt` | VERIFICADO (pin) |
| Access token | JWT HS256, `jose`, TTL 15 min | `app/core/security.py` | VERIFICADO |
| Refresh token | TTL 7 días, rotación y revocación por `jti` | `app/api/auth.py`, `revoke_jti` | VERIFICADO |
| Tipo de token | `decode_token(..., expected_type)`; `mfa_challenge` rechazado en rutas protegidas | `security.py`, `test_mfa_security.py` | VERIFICADO |
| Revocación | Redis `jti` blacklist | `is_jti_revoked`, `revoke_jti` | VERIFICADO (con fallback) |
| MFA OSINT | `_encrypt_secret` AES-256-GCM, ticket de un solo uso | `app/api/osint/auth.py`, `services/intel/auth/mfa.py` | PARCIAL: el router OSINT montado no expone auth/MFA |
| MFA Intel | TOTP L3, ticket de desafío | `app/api/intel/auth.py` | PARCIAL: no montado |

> **Advertencia real de la suite:** 1906 warnings, entre ellos `MFA_CHALLENGE_SECRET no esta configurado; el ticket MFA usa SECRET_KEY como fallback`. No es un fallo de test, pero sí una debilidad de configuración por defecto. Ver `ENGINEERING_RISKS.md` R-008.

### 6.2 Autorización por clasificación

- `CLEARANCE_ORDER` en `app/core/security.py`: `OPEN < RESTRICTED < CONFIDENTIAL < SECRET < TOP_SECRET`.
- `require_clearance(min_level)` devuelve una dependencia que compara el nivel del principal y emite 403 con `record_security_event("clearance_denied")`.
- `ABACEngine` añade comprobaciones por atributo (tenant, compartimento, necesidad de conocer).
- `app/core/classification.py` define además `ClassificationLevel`, `TLPMarker` y `STANAG4774` para etiquetado.

Cobertura de rutas (ADR-010):

- 19 routers montados con `_CLEARANCE_DEPS` (`grep -c "_CLEARANCE_DEPS)" backend/app/main.py` → 19).
- `grep -rn "require_clearance(" backend/app/api/v1/*.py | wc -l` → 109 referencias.
- Test de introspección: `backend/tests/test_v1_clearance_matrix.py`, 5 tests, **0 gaps** en 141 rutas `/api/v1` + `/api/v3` (excluye health y auth públicos por diseño).

> Matiz honesto: las rutas `/api/v2` no están incluidas en la matriz de introspección. Sus handlers declaran `require_clearance`, pero no existe un test de matriz equivalente para v2. Ver R-006.

### 6.3 SSRF con IP pinning

Archivo: `backend/app/services/osint/tools/web_tools.py`.

- `is_safe_url_async(url)` resuelve y valida IPs.
- `_resolve_validated_ips(url)` obtiene la lista de IPs permitidas.
- `_PinnedDNS` sustituye temporalmente `socket.getaddrinfo` para fijar la IP validada durante la petición.
- `safe_http_get` verifica además el peer real tras la conexión (defensa en profundidad).
- Bloquea loopback, privadas, link-local, ULA, IPv4-mapped IPv6 y metadatos de cloud.

Evidencia:

```bash
grep -n "_PinnedDNS\|_resolve_validated_ips\|peer address mismatch" \
  backend/app/services/osint/tools/web_tools.py
```

Tests: `backend/tests/test_ssrf.py` (18 tests) + `backend/tests/test_vision_ssrf.py` (10 tests). **VERIFICADO**.

### 6.4 Cadena de auditoría

Archivo: `backend/app/core/audit.py`.

- `AuditChain.record(...)` calcula `row_hash = SHA-256(entry)` y enlaza `previous_hash`.
- Rehidrata el último hash desde `audit_log` si el proceso arranca de cero.
- `asyncio.Lock` serializa la escritura dentro de un proceso.
- `verify_chain(entries)` recalcula y detecta manipulación o reordenación.
- Los callers pasan `db_session`, por lo que la entrada se persiste.

Tests: `test_audit_persistence.py` (3), `test_audit_unified.py` (3). **VERIFICADO**.

Límite real: el lock es por proceso, no distribuido; dos réplicas de API pueden competir por el mismo `last_hash`. No hay bloqueo `SELECT ... FOR UPDATE` ni almacenamiento WORM. Ver R-007.

### 6.5 Rate limiting

Archivo: `backend/app/core/rate_limit.py`.

- `SlidingWindowRateLimiter` sobre Redis.
- `get_limiter_key(user, path)` evita la ceguera por path (login vs MFA).
- Respuesta 429 con `Retry-After` y headers `X-RateLimit-Limit` / `X-RateLimit-Remaining`.
- `CircuitBreaker` con estados `OPEN` / `HALF_OPEN` / `CLOSED`, claves `rl:state`, `rl:count`, `rl:failures`.
- Fail-closed en staging/producción (`SECURITY_FAIL_MODE=closed`): 503 si Redis cae, abort de arranque sin Redis.
- `resolve_client_ip` con `TRUSTED_PROXIES` y bucket por `sub` (SEC-FIX-004).
- Métrica `sesis_security_fail_open_total` para observar degradaciones.
- En desarrollo se mantiene fail-open de forma explícita.

Tests: `test_rate_limit.py` (6), `test_rate_limit_hardening.py` (7), `test_login_lockout.py` (2). **VERIFICADO**.

### 6.6 Endurecimiento de producción

`Settings.validate_production_hardening` (model validator) rechaza el arranque en `production` si:

- `DEMO_MODE` está activo,
- `SECRET_KEY` es débil o conocida,
- `DATABASE_URL` contiene `sesis:sesis@` o `change`,
- `NEO4J_PASSWORD` está vacío o es débil,
- `GRAFANA_ADMIN_PASSWORD` está vacío o es débil,
- `MFA_ENCRYPTION_KEY` no tiene 64 caracteres hex,
- `ADMIN_INITIAL_PASSWORD` falta o es débil.

Estado: **VERIFICADO en código**; `validate_all.py` comprueba el invariante. No se ejecutó un arranque real en `production` porque faltan servicios. Ver R-011.

### 6.7 Cabeceras HTTP y TLS

Archivo: `infra/nginx.conf`.

| Cabecera / control | Valor | Estado |
| :--- | :--- | :--- |
| HSTS | `max-age=63072000; includeSubDomains; preload` | VERIFICADO |
| X-Frame-Options | `DENY` | VERIFICADO |
| X-Content-Type-Options | `nosniff` | VERIFICADO |
| Referrer-Policy | `strict-origin-when-cross-origin` | VERIFICADO |
| Content-Security-Policy | `default-src 'self'; ... frame-ancestors 'none'` | VERIFICADO |
| Permissions-Policy | `camera=(), microphone=(), geolocation=()` | VERIFICADO |
| X-XSS-Protection | **eliminado** (`grep -c X-XSS` → 0) | VERIFICADO |
| TLS | `TLSv1.2 TLSv1.3`, ciphers ECDHE | VERIFICADO |
| Rate limit edge | `auth` 1 r/s, `api` 30 r/s, burst 100 | VERIFICADO |
| Healthcheck estático | `location = /healthz` | VERIFICADO |

> La CSP `connect-src 'self'` es correcta para el frontend servido por el mismo nginx, pero impediría llamadas directas del navegador a `http://localhost:8000` si se despliega el frontend separado. En desarrollo se usa el puerto `3000` con su propia configuración. Ver R-014.

---

## 7. Superficie de API por dominio

Resumen (detalle completo en `docs/API.md`):

| Dominio | Prefijo | Paths | Implementación real |
| :--- | :--- | ---: | :--- |
| C2 legacy | `/api/v1/c2` | 20 | DB + servicios |
| Tactical | `/api/v1/tactical` | 16 | Servicios de dominio |
| Agents (incl. submódulos) | `/api/v1/agents` | 15 | Stubs en su mayoría |
| Planning | `/api/v1/planning` | 11 | Servicio OPORD |
| Map | `/api/v1/map` | 8 | Cálculos geométricos |
| Logistics v1 | `/api/v1/logistics` | 7 | Servicio en memoria |
| OSINT | `/api/v1/osint` | 6 | Stub |
| Messaging | `/api/v1/messaging` | 6 | Servicio en memoria |
| AAR | `/api/v1/aar` | 6 | Servicio en memoria |
| Reports | `/api/v1/reports` | 6 | Servicio en memoria |
| Auth | `/api/v1/auth` | 5 | REAL |
| Terrain | `/api/v1/terrain` | 5 | Proveedor externo |
| Prediction | `/api/v1/prediction` | 5 | Kalman + DB |
| Fusion | `/api/v1/fusion` | 4 | Motor JDL |
| Intel | `/api/v1/intel` | 3 | Stub |
| Voice | `/api/v1/voice` | 3 | Servicio |
| Satellite | `/api/v1/satellite` | 2 | Stub |
| Health | `/api/v1/health` | 1 | REAL |
| Border v2 | `/api/v2/border` | 5 | DB |
| C2 v2 | `/api/v2/c2` | 7 | DB |
| Cyber v2 | `/api/v2/cyber` | 4 | DB |
| EW v2 | `/api/v2/ew` | 4 | DB |
| Logistics v2 | `/api/v2/logistics` | 4 | DB |
| Space v2 | `/api/v2/space` | 4 | DB |
| COA v3 | `/api/v3/coa` | 5 | Motor COA |
| Maven (fusion/vision) | `/api/v3` | 6 | Servicios |

---

## 8. Frontend AS-IS (Next.js 16.4.6)

### 8.1 Rutas

| Ruta | Archivo | Contenido | Estado |
| :--- | :--- | :--- | :--- |
| `/` | `frontend/src/app/page.tsx` | Guard de sesión + `COPPage` dinámico | VERIFICADO (código) |
| `/login` | `frontend/src/app/login/page.tsx` | Formulario + estados de error/submit | VERIFICADO (código) |
| `/maven` | `frontend/src/app/maven/page.tsx` | `COPUnified` dinámico | VERIFICADO (código) |
| `/_not-found` | generada por Next | 404 | VERIFICADO (build Node 20.18) |

Build **verificado** en copia limpia (`rsync` a `/tmp/opencode/fe_verify`) con Node 20.18: `npm ci` OK, `npx tsc --noEmit` 0 errores, `next build` OK, 4 rutas (`/`, `/_not-found`, `/login`, `/maven`), `npm audit --omit=dev --audit-level=high` → **found 0 vulnerabilities**. Riesgo residual: advisory dev de `brace-expansion` vía eslint, no producción.

### 8.2 Componentes

- 24 componentes COP: `COPPage`, `COPUnified`, `OverviewDashboard`, `TacticalMap`, `TacticalMapEnhanced`, `IntelFeed`, `ThreatPanel`, `ThreatPrediction`, `COAComparison`, `PlanningPanel`, `LogisticsPanel`, `MessagingPanel`, `ReportsPanel`, `AARPanel`, `MavenPanel`, `TerrainAnalysis`, `VoiceCommand`, `MultiMonitor`, `MissionClock`, `StatusBar`, `AlertTicker`, `ClassificationBanner`, `CommandInput`, `QuickActions`.
- 7 primitivas UI: `Skeleton`, `EmptyState`, `Panel`, `KpiCard`, `RadialGauge`, `Sparkline`, `StatusPill`.
- Hook `useApiData` con `loading`, `error`, `reload` y polling; es la base de los estados UX reales.

### 8.3 Design tokens reales

`frontend/src/app/globals.css` define variables CSS (no las de la documentación antigua):

```css
--color-bg-primary: #060a12;
--color-bg-secondary: #0b1220;
--color-bg-tertiary: #152136;
--color-border: #1c2942;
--color-border-strong: #263854;
--color-text-primary: #e8eefc;
--color-text-secondary: #93a4c2;
--color-text-faint: #778bab;
--color-accent: #22d3ee;
--color-success: #34d399;
--color-warning: #fbbf24;
--color-danger: #f87171;
--color-info: #60a5fa;
```

> **Hallazgo de honestidad #3.** `.factory/ARCHITECTURE.md` y `docs/ARCHITECTURE.md` antiguos listaban tokens (`--bg-canvas: #0b1220`, `--accent-primary: #10b981`, etc.) que **no coinciden** con `globals.css`. Los tokens vigentes son los de arriba. La documentación de diseño se alinea en `docs/ARCHITECTURE.md` (nuevo).

### 8.4 Cliente API

`frontend/src/lib/api.ts`:

- `API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"`.
- Login contra `/api/v1/auth/login`.
- Refresh con reintento.
- No hay endpoints inventados en el cliente: las rutas usadas existen en el contrato (verificación cruzada en `VALIDATION_PLAN.md`).

---

## 9. Móvil AS-IS (Flutter)

### 9.1 Pantallas

| Ruta | Archivo |
| :--- | :--- |
| `/login` | `features/auth/screens/login_screen.dart` |
| `/duress` | `features/auth/screens/duress_screen.dart` |
| `/cop` | `features/dashboard/screens/cop_screen.dart` |
| `/intel` | `features/intel/screens/intel_feed_screen.dart` |
| `/mission` | `features/c2/screens/mission_screen.dart` |
| `/agents` | `features/agents/screens/agents_screen.dart` |
| `/satellite` | `features/satellite/screens/satellite_screen.dart` |

### 9.2 Red y offline

- `core/network/api_client.dart` — cliente HTTP.
- `core/network/mesh_protocol.dart` — protocolo mesh.
- `core/network/mesh_service.dart` — servicio mesh; usa la cola offline.
- `core/storage/offline_queue.dart` — cola persistente implementada (138 LOC); elimina el bloqueo anterior.
- `test/mesh_protocol_test.dart` — 11 tests del protocolo mesh.

### 9.3 Resultado real de `flutter analyze`

Comando (Flutter 3.24.5 portable sobre copia en `/tmp`):

```bash
cd mobile/sesis_cop
flutter analyze
flutter test
```

Resultado (2026-11-21, actualización post-FASE 7):

```text
Analyzing sesis_cop...
No issues found! (ran in 18.6s)
```

`flutter test`:

```text
00:02 +11: All tests passed!
```

Estado: **VERIFICADO** (0 errores, 11 tests). AC-25 cumplido. La corrección aplicada fue `CardThemeData` → `CardTheme` y la creación de `core/storage/offline_queue.dart`.

---

## 10. Observabilidad AS-IS

| Elemento | Implementación | Evidencia | Estado |
| :--- | :--- | :--- | :--- |
| Métricas Prometheus | `sesis_http_requests_total`, `sesis_http_request_duration_seconds`, `sesis_http_errors_total`, `sesis_module_up`, `sesis_security_events_total`, `sesis_security_fail_open_total`, `sesis_app_info` | `app/core/metrics.py` | VERIFICADO (código) |
| Endpoint `/metrics` | `generate_latest()` | `app/main.py` | VERIFICADO (código + TestClient) |
| Instrumentación | middleware por plantilla de ruta | `app/main.py` | VERIFICADO |
| Dashboards | 7 JSON: overview, c2, auth, osint, tactile, maven, security | `infra/grafana/provisioning/dashboards/` | VERIFICADO (JSON válido) |
| Paneles | 8 + 8 + 9 + 8 + 8 + 8 + 7 = 56 paneles | ver §12.3 | VERIFICADO |
| Alertmanager | rutas default/critical, slack, slack-pager, inhibit_rules | `infra/alertmanager/alertmanager.yml` | VERIFICADO (YAML) |
| Alertas | 8 reglas en 3 grupos | `infra/alertmanager/alerts.yml` | VERIFICADO |
| Provisión Grafana | datasource `uid: prometheus` | `infra/grafana/provisioning/datasources/datasource.yml` | VERIFICADO |
| Runtime Docker | No ejecutado | — | BLOQUEADO |

> **Hallazgo de honestidad #4.** TASKS.md y TRANSFORMATION_PROGRESS.md dicen "9 alertas". El archivo real tiene **8**. Se documenta el número real y se corrige en la matriz de validación.

---

## 11. Tests AS-IS

| Archivo | Tests | Cobertura funcional |
| :--- | ---: | :--- |
| `test_audit_persistence.py` | 3 | Encadenado, tamper, concurrencia |
| `test_audit_unified.py` | 3 | Tabla única, re-exports |
| `test_auth.py` | 7 | Login, refresh, revocación, registro |
| `test_clearance_enforcement.py` | 5 | 403 por nivel insuficiente |
| `test_contracts.py` | 5 | Contrato OpenAPI vs app viva |
| `test_crypto_quantum.py` | 6 | Etiquetas honestas y fallback |
| `test_e2e_intelligence_cycle.py` | 1 | Ciclo de inteligencia extremo a extremo |
| `test_events_dlq.py` | 3 | Idempotencia, DLQ, ack/nak |
| `test_intel_api.py` | 3 | API de inteligencia C2 |
| `test_login_lockout.py` | 2 | Lockout path-aware en login real |
| `test_mfa_core.py` | 14 | Cifrado, TOTP, tickets y recuperación |
| `test_mfa_security.py` | 3 | Cifrado en reposo, aislamiento de ticket |
| `test_rate_limit_hardening.py` | 7 | Fail-closed, proxies, bucket por sujeto |
| `test_rate_limit.py` | 6 | Ventana, lockout distribuido, reset |
| `test_security_core.py` | 34 | JWT, refresh, clearance, ABAC, MFA |
| `test_ssrf.py` | 18 | IPv4/IPv6, metadatos, pinning |
| `test_terrain.py` | 2 | Elevación y caché |
| `test_v1_clearance_matrix.py` | 5 | 141 rutas, 0 gaps |
| `test_vision_ssrf.py` | 10 | SSRF en descarga de imágenes |
| `test_vision_yolo_integrity.py` | 5 | Integridad del modelo YOLO (sha256) |
| `test_web_tools_core.py` | 15 | DNS, URLs, pinning y límites |
| **Total** | **157** | |

Comando y resultado:

```bash
SECRET_KEY="test-secret-key-32-chars-minimum!!!" python3 -m pytest backend/tests -q
# 157 passed, 1906 warnings in 15.19s
```

> **Cobertura de las suites de seguridad:** **88%** medida con `pytest-cov`
> sobre **6 módulos** (`security.py` 97%, `mfa.py` 99%, `web_tools.py` 87%,
> `audit.py` 87%, `rate_limit.py` 82%, `crypto_quantum.py` 62%). **Alcance:**
> AC-22 se refiere a *security suites*; la cobertura del **backend completo**
> no está medida al 80% (reproducción agregada ~73%). Ver `VALIDATION_PLAN.md`
> §5.4 y R-005.

---

## 12. Infraestructura AS-IS

### 12.1 Servicios docker-compose

Comando:

```bash
python3 - <<'EOF'
import yaml
d = yaml.safe_load(open('docker-compose.yml'))
print(len(d['services']), sum(1 for s in d['services'].values() if s.get('healthcheck')))
EOF
# 12 12
```

| Servicio | Imagen / build | Healthcheck | Puerto host |
| :--- | :--- | :---: | :--- |
| `postgres` | `pgvector/pgvector:pg16` | Sí | `127.0.0.1:5432` |
| `redis` | `redis:7-alpine` | Sí | `127.0.0.1:6379` |
| `nats` | `nats:2-alpine` | Sí | `127.0.0.1:4222` |
| `neo4j` | `neo4j:5-community` | Sí | `127.0.0.1:7474`, `:7687` |
| `api` | build `backend/` | Sí | `127.0.0.1:8000` |
| `nginx` | `nginx:alpine` | Sí | `443`, `80` |
| `celery-worker` | build `backend/` | Sí | — |
| `ollama` | `ollama/ollama:latest` | Sí | `127.0.0.1:11434` |
| `frontend` | build `frontend/` | Sí | `127.0.0.1:3000` |
| `alertmanager` | `prom/alertmanager:latest` | Sí | `127.0.0.1:9093` |
| `prometheus` | `prom/prometheus:latest` | Sí | `127.0.0.1:9090` |
| `grafana` | `grafana/grafana:latest` | Sí | `127.0.0.1:3001` |

Estado de ejecución: `docker` no está instalado (`which docker` → vacío). `docker compose config` **no ejecutado**. La validación es estática (`yaml.safe_load` + conteo). Ver `ENGINEERING_RISKS.md` R-003.

### 12.2 Redes y volúmenes

- Red interna `backend` para API/DB/Redis/NATS/Neo4j.
- Volúmenes nombrados para PostgreSQL, Redis, Neo4j, Prometheus, Grafana, Alertmanager.
- Montajes `:ro` para `fernet.key` en `api` y `celery-worker` (mitigación de permisos en el filesystem del proyecto).

### 12.3 Dashboards y paneles

| Dashboard | Paneles |
| :--- | ---: |
| `sesis-overview.json` | 8 |
| `sesis-c2.json` | 8 |
| `sesis-auth.json` | 9 |
| `sesis-osint.json` | 8 |
| `sesis-tactile.json` | 8 |
| `sesis-maven.json` | 8 |
| `sesis-security.json` | 7 |
| **Total** | **56** |

Comando:

```bash
for f in infra/grafana/provisioning/dashboards/*.json; do
  echo "$f $(python3 -c "import json;print(len(json.load(open('$f'))['panels']))")"
done
```

### 12.4 Alertas

Grupos y reglas reales:

| Grupo | Reglas |
| :--- | :--- |
| `sesis-availability` | `SesisApiDown`, `SesisModuleDown` |
| `sesis-performance` | `SesisHighLatencyP95`, `SesisHighServerErrorRate` |
| `sesis-security` | `SesisClearanceDenialsSpike`, `SesisAuthFailureSpike`, `SesisBruteForceLockout`, `SesisClearanceDeniedEvent` |

Total: 8.

---

## 13. Integraciones externas

| Integración | Archivo | Uso | Estado |
| :--- | :--- | :--- | :--- |
| Open Elevation | `services/terrain/elevation.py` | Elevación de terreno, caché Redis/memoria | REAL (requiere red) |
| Celestrak | `services/satellite/sentinel.py` | TLEs de satélites | REAL (requiere red) |
| AISStream | `services/satellite/...` | Tracks marítimos | PARCIAL |
| GDELT | `services/satellite/gdelt.py` | Eventos globales | REAL (requiere red) |
| Ollama | `services/intel/ollama.py`, `llm_orchestrator.py` | LLM local | PARCIAL (sin modelo descargado) |
| OpenRouter / vLLM / OpenAI | `services/intel/openrouter.py`, `vllm.py` | Fallback LLM | PARCIAL (claves opcionales) |
| Hunter / HIBP / Shodan / VirusTotal | `services/osint/*_wrapper.py` | Enriquecimiento OSINT | REAL (claves opcionales) |
| Neo4j | `services/agents/neo4j_service.py`, `services/osint/graph_intel.py` | Grafo de entidades | PARCIAL (sin runtime) |
| NATS | `app/core/events.py` | Event bus, DLQ, idempotencia | REAL con fallback en memoria |

Ninguna integración externa se ejecutó contra el proveedor real en este entorno. Todas las marcas `REAL` significan "código de cliente HTTP/DB implementado", no "llamada de red verificada".

---

## 14. Flujo de una petición autenticada

```text
Cliente
  │  Authorization: Bearer <JWT>
  ▼
Nginx (TLS, HSTS, CSP, rate limit de borde)
  ▼
RateLimitMiddleware (Redis, clave por usuario/IP + path)
  ▼
AuthMiddleware (decodifica JWT, puebla request.state.principal)
  ▼
Router dependency
  ├─ get_current_user  → valida firma, exp, tipo de token, jti revocado
  └─ require_clearance → compara nivel y registra evento si deniega
  ▼
Handler
  ├─ Pydantic valida el body (tipos, longitudes, patrones)
  ├─ Servicio de dominio
  └─ DB / Redis / NATS / servicio externo
  ▼
Respuesta
  ├─ 2xx con datos
  ├─ 4xx con JSON estructurado (detail)
  └─ métricas Prometheus (status, latencia)
```

Puntos verificados en código:

- El tipo `mfa_challenge` no puede usarse como bearer en rutas protegidas (`test_mfa_security.py`).
- Un refresh token no puede usarse como access token (`decode_token(..., is_refresh=True)`).
- Un clearance insuficiente produce 403 y evento de seguridad.
- Un SSRF produce error antes de abrir el socket, y el pinning impide el rebinding.

---

## 15. Código muerto, stubs y capacidades no conectadas

Esta sección es deliberadamente explícita. Es la diferencia entre "el repositorio contiene código" y "el producto ejecuta la capacidad".

### 15.1 Código no montado

| Elemento | Ubicación | Qué contiene | Estado | Riesgo |
| :--- | :--- | :--- | :--- | :--- |
| Router de media | `backend/app/api/v1/media.py` | `POST /upload`, `PUT /upload/{upload_id}/{filename}` | MUERTO (no montado) | Si se monta sin clearance, expone upload presigned |
| Auth OSINT | `backend/app/api/osint/auth.py` | Login, MFA setup/verify, brute force, single-use ticket | MUERTO en la app montada | Funcionalidad de seguridad no accesible |
| Auth Intel | `backend/app/api/intel/auth.py` | TOTP L3, endpoints clasificados | MUERTO en la app montada | Ídem |
| Admin/países/contributors Intel | `backend/app/api/intel/admin.py`, `countries.py`, `contributors.py`, `continents.py`, `chat.py`, `reports.py`, `signing.py` | Módulos funcionales | MUERTO en la app montada | drift funcional |
| Guardian scripts | `scripts/archived/guardian/` | Utilidades antiguas | ARCHIVADO | ninguno (aislado) |

Comprobación de `media`:

```bash
cd backend
SECRET_KEY="test-secret-key-32-chars-minimum!!!" python3 - <<'EOF'
from app.main import app
print(any("media" in r.path for r in app.routes if hasattr(r, "methods")))
EOF
# False
```

### 15.2 Routers stub (respuesta fija, sin dominio)

| Router | Paths | Evidencia |
| :--- | ---: | :--- |
| `app/api/osint/router.py` | 6 | `return {"cases": [], "total": 0}` |
| `app/api/intel/router.py` | 3 | `return {"reports": [], "total": 0}` |
| `app/api/satellite/router.py` | 2 | `return {"status": "queued", ...}` |
| `app/api/agents/router.py` | 1 | `return {"module": "agents", "status": "operational"}` |
| `agents/intel_api.py`, `mesh_api.py`, `mobile_api.py`, `multimodal_api.py`, `steganography_api.py`, `threat_api.py`, `wearable_api.py` | 11 (12 ops) | Rutas mínimas sin servicio |

Consecuencia: la superficie OpenAPI de 168 paths **sobreestima** la funcionalidad real. La matriz de funcionalidades (`docs/FEATURE_MATRIX.md`) corrige esta sobreestimación con veredictos por módulo.

### 15.3 Servicios de dominio sin API conectada

| Servicio | LOC / archivos | API conectada |
| :--- | :--- | :--- |
| `services/osint` (36 archivos, 3.136 LOC) | Herramientas web/DNS/cert/social/archive, grafos, informes | Sólo 6 rutas stub |
| `services/satellite` (14 archivos) | Sentinel, cambio, detector, análisis temporal | 2 rutas stub |
| `services/intel` (15 archivos) | MFA, RAG, LLM, firma | 3 rutas stub |
| `services/agents` (10 archivos) | Data diode, kill switch, Link16, SIEM | Rutas stub |
| `ml/` (10 archivos) | Visión, anomalías, correlación, briefing | Sin API directa; se usa desde servicios |

Esto no es necesariamente deuda inaceptable —puede ser trabajo en curso—, pero **debe documentarse como no entregado**, no como "implementado" a nivel de producto.

### 15.4 Modelos y tablas no usados por la API montada

- `Messaging`, `AAR`, `OPORD` tienen modelos y servicios, pero los servicios de mensajería/AAR/reportes usan diccionarios en memoria (`self._reports: Dict[...]`), no la base de datos.
- `Neo4j` tiene servicio, pero no hay ruta montada que lo consuma en la app actual.
- `WebAuthnCredential` es un placeholder explícito; los endpoints devuelven 501 según el propio código (`app/db/models/intel/auth.py`).

---

## 16. Coherencia documento ↔ código (hallazgos)

| # | Documento previo | Afirmación | Realidad verificada | Veredicto |
| ---: | :--- | :--- | :--- | :--- |
| 1 | `.factory/ARCHITECTURE.md` §2 | `backend/tests/` = "9 test suites" | 21 archivos, 157 tests | DESACTUALIZADO |
| 2 | `TRANSFORMATION_PROGRESS.md` | `pytest` (cifra histórica) | 157 passed | DESACTUALIZADO |
| 3 | `TRANSFORMATION_PROGRESS.md` | `media.py` **y** `intel.py` no montados | `media` no montado; `intel` sí (`/api/v1/c2`) | INCORRECTO |
| 4 | `TASKS.md` / `TRANSFORMATION_PROGRESS.md` | 9 alertas | 8 alertas | INCORRECTO |
| 5 | `.factory/ARCHITECTURE.md` §5 | Tokens `--bg-canvas`, `--accent-primary: #10b981` | `globals.css` usa `--color-*` y `#22d3ee` | DESACTUALIZADO |
| 6 | `docs/API.md` previo | Endpoints OSINT auth, MFA, web_fetch, graph | No existen en la app montada | INVENTADO/DRIFT |
| 7 | `README.md` | "35 pruebas automatizadas" | 157 | DESACTUALIZADO |
| 8 | `README.md` | "PostgreSQL 15 + PostGIS" | Compose usa `pgvector/pgvector:pg16` (PostgreSQL 16) | DESACTUALIZADO |
| 9 | `docker-compose.demo.yml` | `NEXT_PUBLIC_API_URL=https://localhost/api/v1` | El cliente añade `/api/v1` de nuevo en los endpoints → posible doble prefijo | RIESGO REAL (R-014) |
| 10 | `docs/ARCHITECTURE.md` previo | "11 services" | 12 servicios | DESACTUALIZADO |

> Estos hallazgos son la razón de ser de TASK-045. Los documentos regenerados sustituyen a los anteriores; no se conserva la información obsoleta salvo para trazabilidad en `docs/AUDIT.md`.

---

## 17. Matriz de verificación de esta arquitectura

| Afirmación | Cómo se comprobó | Resultado |
| :--- | :--- | :--- |
| 266 archivos / 26.963 LOC | `find` + `wc` | VERIFICADO |
| 168 paths / 177 operaciones | `app.openapi()` + JSON | VERIFICADO |
| 129/27/11 por prefijo | script de conteo | VERIFICADO |
| 19 routers con clearance | `grep -c _CLEARANCE_DEPS` | VERIFICADO |
| 0 gaps en v1+v3 | `pytest test_v1_clearance_matrix.py` | VERIFICADO |
| SSRF pinning | código + 28 tests | VERIFICADO |
| Auditoría persistente | código + 6 tests | VERIFICADO |
| 12 servicios / 12 healthchecks | `yaml.safe_load` | VERIFICADO (estático) |
| 7 dashboards / 56 paneles | JSON parse | VERIFICADO |
| 8 alertas | `grep -c alert:` | VERIFICADO |
| Frontend 4 rutas / 0 vulnerabilidades prod | `tsc` + `next build` + `npm audit --omit=dev` con Node 20.18 | VERIFICADO |
| Flutter 0 errores / 11 tests | `flutter analyze` + `flutter test` | VERIFICADO |
| Docker runtime | `docker` ausente | BLOQUEADO |
| Cobertura suites de seguridad | `pytest-cov` | 88% (reportado) |

---

## 18. Gaps estructurales AS-IS (resumen)

1. **Superficie API inflada por stubs.** 168 paths, pero OSINT/Intel/Satellite/Agents de primer nivel no ejecutan dominio real.
2. **Capacidades de seguridad no expuestas.** MFA OSINT/Intel y uploads existen en código, pero no en la app montada.
3. **Persistencia desigual.** C2/v2 usan DB; mensajería/AAR/reportes usan memoria.
4. **Observabilidad sin runtime probado.** Métricas y dashboards son correctos en código, pero no se ha visto un scrape real.
5. **Móvil compila y pasa tests.** `offline_queue.dart` implementado; `flutter analyze` 0 errores y `flutter test` 11 passed.
6. **Cobertura de seguridad medida.** 88% en las 6 suites/módulos de seguridad; el backend completo no está medido al 80% (~73% agregado).
7. **Una sola réplica asumida.** El lock de auditoría y el rate limit tienen límites distribuidos no resueltos.
8. **Documentación histórica divergente.** Este documento y los siete restantes de FASE 9 son la corrección.

---

## 19. Comandos de reproducción (bloque único)

```bash
# 1. Inventario backend
find backend/app -name "*.py" | wc -l
find backend/app -name "*.py" -exec cat {} + | wc -l

# 2. Contrato OpenAPI
python3 - <<'EOF'
import json, collections
d = json.load(open('backend/contracts/openapi.json'))
print("paths", len(d['paths']))
print("ops", sum(len([m for m in o if m in ('get','post','put','patch','delete')]) for o in d['paths'].values()))
c = collections.Counter('/'.join(p.split('/')[:3]) if p != '/' else '/' for p in d['paths'])
print(dict(sorted(c.items())))
EOF

# 3. Tests
SECRET_KEY="test-secret-key-32-chars-minimum!!!" python3 -m pytest backend/tests -q

# 4. Validación global
python3 scripts/validate_all.py

# 5. Infra estática
python3 - <<'EOF'
import yaml
d = yaml.safe_load(open('docker-compose.yml'))
print("services", len(d['services']))
print("healthchecks", sum(1 for s in d['services'].values() if s.get('healthcheck')))
EOF

# 6. Frontend (requiere Node, ausente aquí)
# cd frontend && npx tsc --noEmit && npm run build

# 7. Móvil (requiere Flutter, disponible aquí)
cd mobile/sesis_cop && flutter analyze && flutter test
```

---

## 20. Conclusión AS-IS

El sistema es un **monolito modular FastAPI real**, con una capa de seguridad sustancialmente implementada y probada (JWT, clearance, SSRF pinning, auditoría encadenada, rate limit), una infraestructura declarada coherente (12 servicios, observabilidad provisionada) y un frontend Next.js con design system propio.

Al mismo tiempo, el producto **no está completo**: una parte importante de la superficie HTTP son stubs, varias capacidades de seguridad no están montadas y Docker no se ha ejecutado. El móvil ya compila y pasa 11 tests, el frontend Next 16 compila con 0 vulnerabilidades de producción, y la cobertura de las 6 suites de seguridad es 88% (backend completo ≈73%). Cualquier afirmación de "listo para producción" seguiría siendo falsa con la evidencia actual.

Este documento no maquilla esa realidad. Los documentos `AUDIT.md`, `FEATURE_MATRIX.md`, `VALIDATION_PLAN.md`, `FINAL_VALIDATION_REPORT.md` y `ENGINEERING_RISKS.md` la desarrollan con el mismo criterio.
