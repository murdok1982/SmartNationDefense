# AUDIT.md — Auditoría del repositorio y del producto (FASE 9)

**Doc ID:** AUDIT-2026-SND-001
**Proyecto:** SmartNationDefense / SESIS-FEDERATION
**Tipo:** auditoría técnica AS-IS (inventario, calidad, seguridad, deuda, coherencia)
**Fecha:** 2026-11-21
**Commit de referencia:** `3152f117596bc4d5abc4fbd46a4035d1e43e5c7e`
**Alcance:** repositorio completo (`backend/`, `frontend/`, `mobile/`, `ml/`, `infra/`, `scripts/`, `docs/`, `.factory/`)
**Método:** lectura de código, introspección de la app FastAPI, ejecución de tests, validación estática de YAML/JSON, `flutter analyze`, comandos reproducibles.
**Auditor:** `@architect` (TASK-045) sobre evidencia de `@qa-verifier`, `@redteam-auditor` y mediciones propias.

> **Nota de independencia.** Esta auditoría no acepta como verdad las cifras de documentos previos. Cada dato se vuelve a medir. Cuando no se puede medir, se declara `NO VERIFICADO` o `BLOQUEADO`.

---

## 0. Resumen ejecutivo

### 0.1 Veredicto global

| Dimensión | Veredicto | Justificación breve |
| :--- | :--- | :--- |
| Inventario y arquitectura | **SÓLIDO** | Monolito modular coherente, 266 archivos / 26.963 LOC, capas claras |
| Seguridad de aplicación | **BUENO CON RESERVAS** | Controles reales y probados; capacidades críticas no montadas y auditoría formal abierta |
| Calidad de tests | **BUENO** | 157 tests en verde; 88% en suites de seguridad; frontend sin tests automatizados |
| Completitud funcional | **PARCIAL/BAJO** | Muchos endpoints son stubs; servicios existen sin API |
| Frontend | **BUENO** | 45 archivos, design system, estados UX; build Next 16 verificado en copia con Node 20.18 |
| Móvil | **VERIFICADO (FASE 7)** | 15 archivos lib + test; `flutter analyze` 0 errores; `flutter test` 11 passed |
| Infraestructura | **DECLARADA, NO EJECUTADA** | 12 servicios y 12 healthchecks; Docker ausente |
| Observabilidad | **BUENO EN CÓDIGO** | `/metrics` real, 7 dashboards y 8 alertas; runtime Docker sin verificar |
| Documentación | **EN REPARACIÓN** | FASE 9 corrige drift grave; este paquete de 8 docs es la corrección |
| Listo para producción | **NO** | Ver §11 y `FINAL_VALIDATION_REPORT.md` |

### 0.2 Cifras clave

| Métrica | Valor | Comando |
| :--- | ---: | :--- |
| Python `backend/app` | 266 archivos / 26.963 LOC | `find backend/app -name "*.py" \| wc -l` |
| Tests | 21 archivos / 157 tests / 157 passed | `pytest backend/tests -q` |
| OpenAPI | 168 paths / 177 operaciones | `app.openapi()` |
| Frontend | 45 archivos / 8.487 LOC | `find frontend/src ...` |
| Móvil | 16 archivos / 1.520 LOC | `find mobile -name "*.dart"` |
| Servicios compose | 12, 12 con healthcheck | `yaml.safe_load` |
| Dashboards | 7, 56 paneles | JSON parse |
| Alertas | 8 | `grep -c alert:` |
| TODOs/placeholders explícitos | 13 | `grep -rniE "TODO\|FIXME\|not implemented\|placeholder" backend/app` |
| Cobertura suites de seguridad | 88% (6 módulos) | `pytest --cov=... --cov-report=term` |
| Cobertura backend completo | ~73% agregado, sin umbral 80% | reproducción local | NO VERIFICADO al 80% |
| Build frontend | `tsc` 0, `next build` OK, 4 rutas | Node 20.18 en copia | VERIFICADO |
| SCA frontend | 0 vulnerabilidades prod | `npm audit --omit=dev --audit-level=high` | VERIFICADO |
| Migraciones Alembic | 4 | `ls backend/alembic/versions/*.py` |

### 0.3 Top hallazgos

1. **Superficie API sobreestimada.** 168 paths, pero OSINT (6), Intel (3), Satellite (2) y Agents (15) de primer nivel son stubs con respuestas fijas.
2. **Seguridad no expuesta.** Login/MFA OSINT e Intel existen en código pero no están montados en `app.main.app`.
3. **Código muerto confirmado.** `backend/app/api/v1/media.py` no está montado; `v1/intel.py` sí (corrección de la creencia previa).
4. **Móvil verificado.** `offline_queue.dart` implementado, `CardTheme` corregido; `flutter analyze` 0 errores y `flutter test` 11 passed.
5. **Docker no validado.** No hay Docker en el entorno; todo lo de compose es estático.
6. **Cobertura de seguridad medida.** 88% en los 6 módulos de seguridad; el backend completo no está medido al 80% (~73%). `pip-audit` y `npm audit --omit=dev` reportan 0 vulnerabilidades de producción.
7. **Observabilidad sin scrape real.** `/metrics` se verificó con TestClient, no con Prometheus.
8. **Drift documental múltiple.** 12 contradicciones documentadas en §8.

---

## 1. Metodología

### 1.1 Fuentes primarias

| Fuente | Uso |
| :--- | :--- |
| Código en `backend/app` | Verdad de implementación |
| `backend/contracts/openapi.json` | Verdad de superficie HTTP |
| `app.main.app` por introspección | Verdad de rutas montadas y dependencias |
| `backend/tests` | Verdad de comportamiento probado |
| `docker-compose.yml`, `infra/` | Verdad de despliegue declarado |
| `flutter analyze` | Verdad de compilación móvil |
| `scripts/validate_all.py` | Verdad de invariantes de seguridad automatizados |

### 1.2 Fuentes secundarias (contrastadas, no aceptadas ciegamente)

- `.factory/SPEC.md`, `.factory/ARCHITECTURE.md`, `.factory/TASKS.md`, `.factory/SECURITY_AUDIT.md`.
- `docs/TRANSFORMATION_PROGRESS.md`.
- `docs/architecture/*` (ADR-001..013, CONTRACTS.md).
- `docs/*` anteriores (objeto de esta regeneración).

### 1.3 Limitaciones declaradas

| Limitación | Efecto | Estado |
| :--- | :--- | :--- |
| Sin Docker | No se probó arranque real, redes, healthchecks en vivo | BLOQUEADO |
| Sin PostgreSQL/PostGIS | No se ejecutaron migraciones ni consultas geoespaciales | BLOQUEADO |
| Sin Redis/NATS/Neo4j | Tests usan dobles; no se probó concurrencia distribuida real | PARCIAL |
| Sin Node local | Build verificado en copia `/tmp/opencode/fe_verify` con Node 20.18 | VERIFICADO (copia) |
| Sin claves de APIs externas | OSINT/LLM/satélite no se probaron contra proveedores | NO VERIFICADO |
| Tiempo | No se ejecutó análisis dinámico (DAST) ni pentest de red | NO VERIFICADO |

---

## 2. Inventario del repositorio

### 2.1 Volumen por área

| Área | Archivos | LOC | Observación |
| :--- | ---: | ---: | :--- |
| `backend/app` | 266 `.py` | 26.963 | Núcleo del producto |
| `backend/tests` | 21 `test_*.py` + `conftest.py` | — | 157 tests |
| `backend/alembic/versions` | 4 | — | 001..004 |
| `frontend/src` | 45 `.ts/.tsx` | 8.487 | Next.js 16.4.6 |
| `mobile/sesis_cop/lib` | 14 `.dart` | 1.399 | Flutter |
| `ml` | 10 archivos | — | Modelos y reglas |
| `infra` | 14 archivos | — | nginx, Prometheus, Grafana, Alertmanager, SSL |
| `scripts` | 6 + archived | — | Validación, claves, seed, demo |
| `docs` | 20+ | — | Auditoría y arquitectura |
| `.factory` | 4 | — | Estado del factory |

### 2.2 Inventario backend por subpaquete

| Subpaquete | Contenido | Archivos destacados |
| :--- | :--- | :--- |
| `api/v1` | Routers legacy y de dominio | `alerts.py`, `assets.py`, `intel.py`, `sensors.py`, `planning.py`, `terrain.py` |
| `api/v2` | Dominios avanzados | `border.py`, `cyber.py`, `ew.py`, `logistics.py`, `space.py`, `c2.py` |
| `api/v3` | Maven y COA | `router.py`, `coa.py` |
| `api/tactical` | OPORD, wargaming, fires, BDA, PSYOPS | 5 routers finos |
| `api/agents` | Mesh, móvil, stego, wearable, sensores | mayoría stubs |
| `api/osint` | Router + auth + deps + audit | router montado es stub |
| `api/intel` | Auth, admin, reports, chat, signing | mayoría no montada |
| `api/satellite` | Router mínimo | stub |
| `core` | Seguridad, auditoría, rate limit, eventos, métricas, LLM | 16 archivos |
| `db/models` | Persistencia, intel, osint, messaging, AAR, OPORD | 22 archivos |
| `services` | 17 subpaquetes de dominio | 11.872 LOC |
| `agents` | Agentes OSINT/Intel | código de dominio |
| `workers` | Celery | tareas asíncronas |
| `schemas` | Pydantic compartidos | 8 archivos |

### 2.3 Inventario frontend

| Grupo | Archivos | Función |
| :--- | ---: | :--- |
| `app/` | 6 tsx (+1 CSS) | Layout y rutas (`/`, `/login`, `/maven`) |
| `components/cop/` | 22 | Paneles operativos |
| `components/ui/` | 7 | Primitivas visuales |
| `lib/` | 5 | Cliente API, tipos, mappers, hook de datos |
| `store/` | 3 | Zustand auth/cop/maven |

### 2.4 Inventario móvil

| Grupo | Archivos | Función |
| :--- | ---: | :--- |
| `core/` | 6 | Constantes, red, mesh, tema, colores |
| `features/` | 7 | Login, duress, COP, intel, misión, agentes, satélite |
| `main.dart` | 1 | Rutas y arranque |

### 2.5 Inventario de infraestructura

| Archivo | Función | Validación |
| :--- | :--- | :--- |
| `docker-compose.yml` | 12 servicios | YAML OK; runtime no |
| `docker-compose.demo.yml` | Override demo + seed | YAML OK |
| `infra/nginx.conf` | TLS, CSP, rate limit, healthz | Revisión estática |
| `infra/prometheus.yml` | Scrape + rules + alerting | YAML OK |
| `infra/alertmanager/alertmanager.yml` | Rutas e inhibiciones | YAML OK |
| `infra/alertmanager/alerts.yml` | 8 alertas | YAML OK |
| `infra/grafana/provisioning/` | Datasource + 7 dashboards | JSON OK |
| `infra/ssl/server.crt/.key` | Certificado local | Existe |
| `fernet.key` | Clave Fernet local | Existe (44 bytes) |

---

## 3. Auditoría de código backend

### 3.1 Capa API

| Aspecto | Hallazgo | Evidencia | Severidad |
| :--- | :--- | :--- | :--- |
| Rutas montadas | 184 objetos ruta, 173 paths únicos | introspección | INFO |
| Contrato | 168 paths, 177 operaciones | OpenAPI | INFO |
| Stubs | OSINT/Intel/Satellite/Agents devuelven datos fijos | §3.4 | ALTA (funcional) |
| Código muerto | `v1/media.py` sin montar | introspección | MEDIA |
| Duplicidad de routers | `v1/intel.py` (C2) y `api/intel/*` (Intel) con nombres similares | estructura | MEDIA (confusión) |
| Validación de entrada | Pydantic con `max_length`, `pattern`, `ge/le` en routers v2 y assets | `v2/border.py`, `v1/assets.py` | POSITIVO |
| Mass assignment | `assets.py` usa modelo "allowed-fields-only" | `AssetRegisterIn` | POSITIVO |
| Manejo de errores | `HTTPException` con `detail`; sin stack traces al cliente | routers | POSITIVO |
| Paginación | No uniforme; algunos listados devuelven todo | `v1/assets.py`, `v2/*` | MEDIA (escala) |

### 3.2 Capa de servicios

| Servicio | Implementación real | Evidencia | Veredicto |
| :--- | :--- | :--- | :--- |
| `tactical/coa_engine.py` | Generación de COA, riesgo, armas, comparación | clases y métodos | IMPLEMENTADO |
| `fusion/jdl_fusion.py` | JDL L0-L4 con reglas JSON | `JDLFusionEngine` | IMPLEMENTADO (heurístico) |
| `prediction/threat_prediction.py` | Kalman + patrones + DB | `ThreatPredictionService` | IMPLEMENTADO |
| `terrain/elevation.py` | Open Elevation + caché | `fetch_elevations` | IMPLEMENTADO (red externa) |
| `satellite/*` | Sentinel, cambio, detector, GDELT | 14 archivos | IMPLEMENTADO (sin API) |
| `osint/*` | Tools web/DNS/cert/social, grafos | 36 archivos | IMPLEMENTADO (sin API) |
| `intel/*` | MFA, RAG, LLM, firma | 15 archivos | IMPLEMENTADO (sin API) |
| `agents/*` | Data diode, kill switch, Link16, SIEM | 10 archivos | IMPLEMENTADO (sin API) |
| `reports/service.py` | SITREP, plantillas | diccionario en memoria | PARCIAL |
| `messaging/service.py` | Mensajes, hilos, TTL | memoria | PARCIAL |
| `aar/service.py` | AAR, timeline, lecciones | memoria | PARCIAL |
| `voice/service.py` | Comandos | servicio | PARCIAL |
| `vision/*` | YOLO, dron, análisis | requiere pesos | EXPERIMENTAL |
| `compliance/auto_reporter.py` | Informes ENS | servicio | PARCIAL |

### 3.3 Capa de persistencia

| Aspecto | Hallazgo | Evidencia | Severidad |
| :--- | :--- | :--- | :--- |
| Modelo `User` | Único, `users` | `persistence.py` | POSITIVO |
| Auditoría | Tabla única `audit_log` | migración 004 | POSITIVO |
| Uso de DB | C2/v2/assets/sensors usan SQLAlchemy | `db_refs` > 0 | POSITIVO |
| Uso de memoria | mensajería, AAR, reportes | `Dict[...]` | MEDIA |
| Migraciones | 4 revisiones; no ejecutadas | `alembic/versions` | NO VERIFICADO |
| SQL legacy | Archivado | `migrations/archived/` | POSITIVO |
| Índices | Presentes en migraciones; no medidos en runtime | migraciones | NO VERIFICADO |
| Transacciones | `commit()` por operación; sin patrón unidad-de-trabajo explícito | routers | MEDIA |

### 3.4 Stubs y código no conectado (evidencia literal)

```text
backend/app/api/osint/router.py:
  @router.get("/cases")   → {"cases": [], "total": 0}
  @router.get("/entities")→ {"entities": [], "total": 0}
  @router.get("/jobs")    → {"jobs": [], "total": 0}
  @router.get("/reports") → {"reports": [], "total": 0}
  @router.get("/status")  → {"module": "osint", "status": "operational"}

backend/app/api/intel/router.py:
  @router.get("/reports") → {"reports": [], "total": 0}
  @router.get("/feeds")   → {"feeds": [], "total": 0}
  @router.get("/status")  → {"module": "intelligence", "status": "operational"}

backend/app/api/satellite/router.py:
  @router.post("/analyze")→ {"status": "queued", "coordinates": ...}
  @router.get("/status")  → {"module": "satellite-imint", "status": "operational"}
```

Consecuencia: un cliente que descubra la API por OpenAPI creerá que existen casos, entidades, jobs, feeds y análisis de satélite. **No existen a nivel HTTP.**

### 3.5 Duplicidades y colisiones

| Duplicidad | Detalle | Impacto |
| :--- | :--- | :--- |
| `v1/intel.py` vs `api/intel/*` | Dos dominios "intel" distintos: C2 de productos/PIR vs Global-Intelligence | Confusión de mantenimiento |
| `v1/logistics.py` vs `v2/logistics.py` | Dos APIs logísticas con modelos distintos | Deuda funcional |
| `v1/aar.py` vs `v2` (no hay) | Sólo v1 | — |
| `v1/map.py` vs `services/mapping` | Router + servicio | Correcto |
| `core/classification.py` vs `core/security.CLEARANCE_ORDER` | Dos definiciones de niveles | Riesgo de divergencia |

> `classification.py` usa minúsculas (`public`, `restricted`, ...) y `CLEARANCE_ORDER` usa mayúsculas (`OPEN`, `RESTRICTED`, ...). Los routers usan la segunda. La primera se usa en modelos/etiquetas. No hay test que garantice que ambas escalas coinciden. Ver R-009.

---

## 4. Auditoría de seguridad verificada

> Esta sección audita **código**. El estado formal de la auditoría adversarial vive en `.factory/SECURITY_AUDIT.md`, que puede estar en reescritura por `@redteam-auditor`. No se modifica desde aquí.

### 4.1 Controles positivos (verificados)

| Control | Implementación | Prueba | Estado |
| :--- | :--- | :--- | :--- |
| Hash bcrypt | passlib 1.9.3 + bcrypt 4.0.1 | `test_auth.py` | VERIFICADO |
| JWT HS256 con tipo | `decode_token(expected_type)` | `test_mfa_security.py` | VERIFICADO |
| Refresh rotation | revocación de `jti` | `test_auth.py` | VERIFICADO |
| MFA challenge aislado | tipo `mfa_challenge` rechazado | `test_mfa_security.py` | VERIFICADO |
| Cifrado de secreto MFA | AES-256-GCM | `test_mfa_security.py` | VERIFICADO |
| Clearance | `require_clearance` | `test_clearance_enforcement.py`, `test_v1_clearance_matrix.py` | VERIFICADO |
| SSRF IPv4/IPv6 | denylist + pinning | `test_ssrf.py` | VERIFICADO |
| SSRF en visión | validación de URL | `test_vision_ssrf.py` | VERIFICADO |
| Auditoría encadenada | SHA-256 + persistencia | `test_audit_persistence.py` | VERIFICADO |
| Rate limit distribuido | Redis + lockout | `test_rate_limit.py` | VERIFICADO (dobles) |
| Fail-closed en prod | `SECURITY_FAIL_MODE=closed`, 503 | `test_rate_limit_hardening.py` | VERIFICADO |
| IP real tras proxy | `resolve_client_ip` + `TRUSTED_PROXIES` | `test_rate_limit_hardening.py` | VERIFICADO |
| SCA backend | `pip-audit` + allowlist | CI | VERIFICADO (0) |
| DLQ / idempotencia | NATS + fallback | `test_events_dlq.py` | VERIFICADO (dobles) |
| Hardening de producción | model validator | `validate_all.py` | VERIFICADO |
| Cabeceras HTTP | nginx | revisión estática | VERIFICADO |
| Sin X-XSS | eliminado | `grep -c` → 0 | VERIFICADO |

### 4.2 Hallazgos abiertos o parciales

| ID | Hallazgo | Evidencia | Severidad | Estado |
| :--- | :--- | :--- | :--- | :--- |
| AUD-SEC-01 | MFA OSINT/Intel no montado en la app | `main.py` no incluye `osint/auth` ni `intel/auth` | ALTA | ABIERTO |
| AUD-SEC-02 | `MFA_CHALLENGE_SECRET` vacío → fallback a `SECRET_KEY` | warning en 522 tests | MEDIA | ABIERTO |
| AUD-SEC-03 | Rate limit fail-open si Redis cae | `SECURITY_FAIL_MODE=closed` en staging/prod; fail-open sólo dev | MEDIA | MITIGADO (prod) |
| AUD-SEC-04 | Lock de auditoría por proceso, no distribuido | `asyncio.Lock` | MEDIA | ABIERTO |
| AUD-SEC-05 | `SECRET_KEY` con default `CHANGE_ME_IMMEDIATELY` | `config.py` | MEDIA | MITIGADO en producción |
| AUD-SEC-06 | Upload presigned sin clearance si se monta | `v1/media.py` | MEDIA | LATENTE |
| AUD-SEC-07 | CORS por defecto localhost; en prod depende de env | `config.py` | BAJA | MITIGADO |
| AUD-SEC-08 | CSP `connect-src 'self'` incompatible con frontend separado | `nginx.conf` | BAJA | ABIERTO |
| AUD-SEC-09 | Sin mTLS interno | no implementado | MEDIA | PLANNED |
| AUD-SEC-10 | Sin HSM/WORM para auditoría | no implementado | MEDIA | PLANNED |
| AUD-SEC-11 | `WebAuthn` devuelve 501 | `intel/auth.py` | BAJA | STUB |
| AUD-SEC-12 | Dependencias: `pip-audit` con allowlist | 0 vulnerabilidades reportadas | MEDIA | MITIGADO |
| AUD-SEC-13 | SEC-FIX-007 (MEDIUM) | auditoría adversarial en curso | MEDIA | ABIERTO |
| AUD-SEC-14 | SEC-FIX-008 (MEDIUM) | auditoría adversarial en curso | MEDIA | ABIERTO |

### 4.3 Modelo de amenazas resumido

| Activo | Amenaza | Control actual | Cobertura |
| :--- | :--- | :--- | :--- |
| Credenciales | Fuerza bruta | Rate limit + lockout Redis | PARCIAL (fail-open) |
| Tokens | Confusión de tipo | `expected_type` | BUENA |
| Tokens | Robo/replay | TTL corto + revocación | BUENA |
| Datos clasificados | Lectura por clearance bajo | `require_clearance` | BUENA en v1/v3; no matriculada en v2 |
| SSRF | Rebinding a metadata | IP pinning + peer check | BUENA |
| Auditoría | Manipulación | Hash chain | PARCIAL (sin WORM) |
| Secretos | Defaults débiles | Validador de producción | BUENA en prod; débil en dev |
| Uploads | Ejecución/路径 traversal | Router no montado | LATENTE |
| LLM | Prompt injection | No hay control específico | NO CUBIERTO |
| Cadena de suministro | Dependencia comprometida | Pins + `pip-audit` con allowlist + CI bloqueante | BUENA |

### 4.4 Superficie expuesta sin autenticación

| Ruta | Motivo | Evaluación |
| :--- | :--- | :--- |
| `/` | Info de servicio | Aceptable; revela versión y modelo LLM |
| `/api/v1/health` | Probe | Aceptable |
| `/api/v1/auth/login`, `/register`, `/refresh` | Público por diseño | Aceptable con rate limit |
| `/metrics` | Prometheus | **RIESGO**: expuesto sin auth en la app; nginx no lo restringe explícitamente |
| `/docs`, `/openapi.json` | Documentación | Aceptable en dev; en prod debería deshabilitarse |

> `GET /` devuelve `environment` y `llm` (nombre del modelo). Es información útil para un atacante. Bajo, pero real. `/metrics` puede revelar rutas y volúmenes. Ver R-013.

---

## 5. Auditoría de tests

### 5.1 Estado real

```bash
SECRET_KEY="test-secret-key-32-chars-minimum!!!" python3 -m pytest backend/tests -q
# 157 passed, 1906 warnings in 15.19s
```

### 5.2 Distribución y valor

| Test | Valor | Limitación |
| :--- | :--- | :--- |
| `test_security_core.py` (34) | JWT, refresh, clearance, ABAC, MFA | No prueba servicios reales |
| `test_ssrf.py` (18) | Excelente cobertura de clases de IP | No prueba red real |
| `test_web_tools_core.py` (15) | DNS, URLs, pinning y límites | Sin red externa |
| `test_mfa_core.py` (14) | Cifrado, TOTP, tickets, recuperación | No prueba proveedor TOTP externo |
| `test_vision_ssrf.py` (10) | Cubre descarga de imágenes | No prueba YOLO |
| `test_rate_limit_hardening.py` (7) | Fail-closed, proxies, bucket por sujeto | Redis simulado |
| `test_auth.py` (7) | Flujo de tokens | No prueba MFA OSINT montado |
| `test_crypto_quantum.py` (6) | Etiquetas y fallback | Sin pqcrypto |
| `test_rate_limit.py` (6) | Lockout y aislamiento | Redis falso |
| `test_v1_clearance_matrix.py` (5) | Introspección real de la app | Sólo v1/v3 |
| `test_clearance_enforcement.py` (5) | 403 real | No cubre todos los routers |
| `test_contracts.py` (5) | Drift contract ⊆ app | No valida semántica |
| `test_vision_yolo_integrity.py` (5) | Integrity sha256 del modelo | Sin pesos reales |
| `test_audit_persistence.py` (3) | Cadena y concurrencia | Mismo proceso |
| `test_audit_unified.py` (3) | Dedup | — |
| `test_mfa_security.py` (3) | Cifrado y tipo | No TOTP real |
| `test_events_dlq.py` (3) | DLQ | Fallback memoria |
| `test_intel_api.py` (3) | API C2 | Datos sintéticos |
| `test_login_lockout.py` (2) | Lockout path-aware en login | Redis simulado |
| `test_terrain.py` (2) | Caché | Sin red |
| `test_e2e_intelligence_cycle.py` (1) | Flujo completo | Alcance acotado |

### 5.3 Ausencias

| Ausencia | Impacto | Severidad |
| :--- | :--- | :--- |
| Cobertura global del backend | El 88% cubre suites de seguridad, no todo `app/` | MEDIA |
| Tests de frontend | Componentes y estados UX sin verificación automatizada | MEDIA |
| Tests de móvil | 11 tests de protocolo mesh; faltan pantallas y cola | BAJA |
| Tests de integración con DB real | Migraciones y queries no probadas | ALTA |
| Tests de contrato de respuesta | Sólo presencia de paths | MEDIA |
| Tests de carga | Sin medición de latencia/throughput | MEDIA |
| Tests de seguridad dinámicos | Sin DAST | MEDIA |
| Tests de regresión visual | Sin snapshots | BAJA |

### 5.4 Calidad de los tests

Positivo:

- Los tests de seguridad no son cosméticos: prueban 403, 401, hash chaining, pinning y lockout.
- Cobertura de las suites de seguridad: **88%** en **6 módulos** (`security.py` 97%, `mfa.py` 99%, `web_tools.py` 87%, `audit.py` 87%, `rate_limit.py` 82%, `crypto_quantum.py` 62%). La cobertura del backend completo no está medida al 80% (agregado ~73%); AC-22 se refiere a *security suites*.
- `test_v1_clearance_matrix.py` introspecciona el árbol real de dependencias, no una copia.
- Se corrigió un bug de test-double (`FakeRedis.delete` no limpiaba ZSETs), lo que evita falsos verdes.
- `test_contracts.py` compara el contrato con la app viva.

Negativo:

- 1906 warnings, varios sobre configuración MFA débil. Los warnings no fallan el build, pero ocultan señales.
- No hay `-W error` ni umbral de warnings.
- Los tests de Redis/NATS usan dobles; la concurrencia distribuida real no está probada.

---

## 6. Auditoría de frontend

### 6.1 Fortalezas

| Aspecto | Evidencia |
| :--- | :--- |
| Design system con variables CSS | `globals.css` |
| Componentes de estado | `Skeleton.tsx`, `EmptyState.tsx` |
| Hook de datos con error/loading/reload | `use-api-data.ts` |
| Separación de stores | `auth-store.ts`, `cop-store.ts`, `maven-store.ts` |
| Tipado | `cop-types.ts`, `maven-types.ts`, `mappers.ts` |
| Accesibilidad básica | roles `status`, `aria-live`, `aria-busy` en login |
| Responsive | clases Tailwind con breakpoints |

### 6.2 Debilidades

| Aspecto | Hallazgo | Severidad |
| :--- | :--- | :--- |
| Build en copia | `tsc` 0, `next build` OK, 4 rutas; Node 20.18 | VERIFICADO |
| Cobertura UI | Sin tests de componentes | MEDIA |
| Contrato API | Algunos mappers asumen formas no garantizadas por stubs | MEDIA |
| Doble prefijo potencial | `NEXT_PUBLIC_API_URL=.../api/v1` + cliente añade `/api/v1` | MEDIA |
| Manejo de sesión | Token en store; no se evaluó almacenamiento (localStorage vs memoria) | MEDIA |
| SSE/WebSocket | No implementado | BAJA |
| Internacionalización | Sólo español | BAJA |

### 6.3 Coherencia con backend

- El cliente llama a `/api/v1/auth/*` (existe).
- Las páginas COP consumen endpoints v1/v2/v3 que existen en OpenAPI.
- No se encontraron endpoints inventados en `api.ts` (verificación cruzada por grep de rutas).
- **Pero** varios endpoints consumidos devuelven stubs (OSINT/Intel/Satellite), por lo que la UI puede mostrar vacíos legítimos y no errores.

---

## 7. Auditoría de móvil

### 7.1 Estado

| Aspecto | Hallazgo | Estado |
| :--- | :--- | :--- |
| Estructura | 15 archivos lib, 7 pantallas + 1 test | VERIFICADO |
| Tema | `app_theme.dart`, `colors.dart`; `CardTheme` corregido | VERIFICADO |
| Red | `api_client.dart`, `mesh_protocol.dart`, `mesh_service.dart` | VERIFICADO (código) |
| Offline queue | `core/storage/offline_queue.dart` implementado (138 LOC) | VERIFICADO |
| Compilación | `flutter analyze` → 0 errores | VERIFICADO (Flutter 3.24.5 portable) |
| Tests | `flutter test` → 11 passed (`mesh_protocol_test.dart`) | VERIFICADO |
| Mesh real | `nearby_connections` no probado en dispositivo | NO VERIFICADO |
| Seguridad | `flutter_secure_storage` declarado | NO VERIFICADO en dispositivo |
| Pubspec | lockfile regenerado y alineado con el SDK usado | VERIFICADO |

### 7.2 Evidencia de compilación y tests

```text
Analyzing sesis_cop...
No issues found! (ran in 18.6s)

00:02 +11: All tests passed!
```

### 7.3 Evaluación

El móvil pasa de **prototipo estructural** a **entrega verificable**: compila sin errores, tiene cola offline persistente y 11 tests del protocolo mesh. Quedan fuera de verificación la mesh en dispositivos reales, el borrado por duress y la integración con el backend en vivo. AC-25 se considera cumplido.

## 8. Auditoría de documentación y coherencia

### 8.1 Contradicciones verificadas

| # | Documento | Dice | Código dice | Veredicto |
| ---: | :--- | :--- | :--- | :--- |
| 1 | `.factory/ARCHITECTURE.md` | 9 suites de test | 21 archivos, 157 tests | DRIFT |
| 2 | `.factory/ARCHITECTURE.md` | 11 servicios | 12 servicios | DRIFT |
| 3 | `.factory/ARCHITECTURE.md` | Tokens `--bg-canvas`, `#10b981` | `--color-bg-primary`, `#22d3ee` | DRIFT |
| 4 | `.factory/ARCHITECTURE.md` | `media.py` e `intel.py` no montados | Sólo `media` no montado | INCORRECTO |
| 5 | `TASKS.md` | 9 alertas | 8 | INCORRECTO |
| 6 | `TRANSFORMATION_PROGRESS.md` | cifra histórica de tests | 157 passed | DESACTUALIZADO |
| 7 | `docs/API.md` previo | OSINT auth/MFA/web_fetch | No montado | INVENTADO |
| 8 | `README.md` | 35 pruebas | 157 | DESACTUALIZADO |
| 9 | `README.md` | PostgreSQL 15 | PostgreSQL 16 (`pg16`) | DESACTUALIZADO |
| 10 | `docs/ARCHITECTURE.md` previo | 11 services | 12 | DESACTUALIZADO |
| 11 | `docs/API.md` previo | Contrato exhaustivo | No refleja stubs | ENGAÑOSO |
| 12 | `docs/FEATURE_MATRIX.md` previo | Veredictos sin evidencia de línea | No reproducible | DÉBIL |

### 8.2 Documentos que sí son fiables

| Documento | Motivo |
| :--- | :--- |
| `docs/audit/*` (FASE 0) | Inventario con paths y hallazgos concretos |
| `docs/architecture/CONTRACTS.md` | Generado desde la app; 168 paths |
| `docs/TRANSFORMATION_PROGRESS.md` | Evidencia por tarea, aunque con cifras desactualizadas |
| `.factory/TASKS.md` | Backlog atómico con verificación |
| `compliance/*` | Declara honestamente lo que es PARCIAL/EXPERIMENTAL |

### 8.3 Política de documentación a partir de FASE 9

1. Toda cifra debe incluir comando.
2. Todo veredicto debe incluir archivo/línea o test.
3. Lo no ejecutado se marca `NO VERIFICADO`/`BLOQUEADO`.
4. Los stubs no se documentan como implementados.
5. Los documentos se regeneran al cerrar cada fase, no al final.

---

## 9. Auditoría de infraestructura

### 9.1 Lo que está bien

| Aspecto | Evidencia |
| :--- | :--- |
| 12 servicios con healthcheck | `yaml.safe_load` |
| Red segmentada | compose `networks` |
| Puertos ligados a loopback | `127.0.0.1:...` salvo nginx 80/443 |
| TLS 1.2/1.3 | `nginx.conf` |
| Cabeceras de seguridad | `nginx.conf` |
| Rate limit de borde | `limit_req_zone` |
| Healthcheck estático | `location = /healthz` |
| Observabilidad provisionada | Prometheus + Grafana + Alertmanager |
| Volúmenes persistentes | postgres, redis, neo4j, prometheus, grafana, alertmanager |
| Secretos por entorno | `.env.example` sin valores reales |

### 9.2 Lo que falta o no se probó

| Aspecto | Hallazgo | Severidad |
| :--- | :--- | :--- |
| Runtime | Docker ausente; nada arrancado | ALTA |
| Migraciones | No ejecutadas | ALTA |
| Backups | No hay estrategia declarada | MEDIA |
| Rotación de secretos | No hay procedimiento | MEDIA |
| mTLS | No implementado | MEDIA |
| Límites de recursos | No se revisaron `deploy.resources` | MEDIA |
| Alta disponibilidad | Una réplica por servicio | MEDIA |
| Escalado | Sin horizontal scaling | MEDIA |
| SBOM | No generado | MEDIA |
| Firma de imágenes | No implementada | BAJA |
| Secret manager | Variables de entorno | MEDIA |

### 9.3 Configuración potencialmente insegura

| Configuración | Riesgo | Evaluación |
| :--- | :--- | :--- |
| `NEXT_PUBLIC_API_URL=https://localhost/api/v1` en demo | Doble `/api/v1` si el cliente lo añade | ROTO en demo |
| `GRAFANA_ADMIN_PASSWORD` por env | Aceptable si es fuerte | OK condicional |
| `fernet.key` en filesystem | Sin KMS/HSM | MEDIA |
| `/metrics` sin auth | Fuga de información | MEDIA |
| `docs`/`openapi.json` en prod | Reconocimiento | BAJA |
| Ollama sin auth en loopback | Aceptable en single-host | BAJA |

---

## 10. Deuda técnica

### 10.1 Registro (sólo deuda verificada)

| ID | Deuda | Evidencia | Impacto | Estado |
| :--- | :--- | :--- | :--- | :--- |
| TD-001 | Consolidación de User | resuelta (1 tabla) | — | CERRADA |
| TD-002 | Auditoría efímera | resuelta (persistencia) | — | CERRADA |
| TD-003 | Clearance irregular v1 | resuelta (141 rutas, 0 gaps) | — | CERRADA |
| TD-004 | SSRF TOCTOU | resuelta (pinning) | — | CERRADA |
| TD-005 | Etiqueta post-cuántica engañosa | resuelta (`fernet-aes128-cbc-hmac-sha256`) | — | CERRADA |
| TD-006 | EncryptedField fail-open | resuelta (fail-closed) | — | CERRADA |
| TD-007 | Falta infra/ssl + fernet | resuelta | — | CERRADA |
| TD-008 | Settings multi-tenant | resuelta | — | CERRADA |
| TD-009 | Rate limit path-blind | resuelta | — | CERRADA |
| TD-010 | Circuit breaker fail-open | mitigada (decisión) | — | ACEPTADA |
| TD-011 | AuditLog duplicado | resuelta | — | CERRADA |
| TD-012 | Migraciones legacy | resuelta (archivadas) | — | CERRADA |
| TD-013 | Guardian scripts | resuelta (archivados) | — | CERRADA |
| TD-014 | Routers stub OSINT/Intel/Sat | **abierta** | Producto incompleto | ABIERTA |
| TD-015 | Build móvil incompleto (histórico) | resuelta (offline queue + `CardTheme`) | Sin bloqueo de build | CERRADA |
| TD-016 | Cobertura de seguridad | mitigada (88% con `pytest-cov`) | Cobertura global no fijada | MITIGADA |
| TD-017 | Servicios en memoria | **abierta** | Pérdida de datos al reiniciar | ABIERTA |
| TD-018 | Falta de `pip-audit`/`npm audit` | mitigada (`pip-audit` 0; frontend 0 prod; build Next 16 verificado) | Advisory dev `brace-expansion` | MITIGADA |
| TD-019 | Estados UX incompletos en algunos paneles | **abierta** | UX inconsistente | ABIERTA |
| TD-020 | Observabilidad sin runtime | **abierta** | Sin evidencia operativa | ABIERTA |

### 10.2 Deuda por severidad

| Severidad | Cantidad | Ejemplos |
| :--- | ---: | :--- |
| Bloqueante | 2 | stubs, Docker no validado |
| Alta | 2 | persistencia en memoria, observabilidad |
| Media | 5 | duplicidad de routers, paginación, métricas expuestas, CSP, locks distribuidos |
| Baja | 3 | i18n, WebAuthn 501, docs endpoints en prod |

---

## 11. Evaluación arquitectónica

### 11.1 Fortalezas

1. **Modular monolith coherente.** La separación `api/core/services/db` es real y consistente en 266 archivos.
2. **Seguridad integrada, no pegada.** `require_clearance` está en 19 routers y 109 referencias en handlers de v1; los tests lo verifican por introspección.
3. **SSRF de nivel producción.** IP pinning + peer check + 28 tests es más de lo habitual en proyectos de este tamaño.
4. **Auditoría encadenada.** Hash chaining con persistencia y detección de reordenación.
5. **Observabilidad provisionada como código.** 7 dashboards y 8 alertas consultan series que existen.
6. **Design system propio.** Tokens, primitivas y 24 componentes COP.
7. **Honestidad en compliance.** `ENS_ALTA_matrix.md` marca explícitamente lo que no está implementado.

### 11.2 Debilidades estructurales

1. **Dos productos en uno.** La superficie declarada (168 paths) y la funcionalidad real (subconjunto) divergen.
2. **Servicios huérfanos.** 11.872 LOC de servicios, muchos sin API.
3. **Persistencia desigual.** Unos dominios en DB, otros en memoria.
4. **Acoplamiento de seguridad a routers.** El clearance se declara por handler y por router; hay dos mecanismos y dos definiciones de niveles.
5. **Observabilidad no operada.** Provisionar no es operar.
6. **Móvil verificado, mesh pendiente.** Compila y pasa 11 tests; falta probar mesh en dispositivos y duress.
7. **Sin estrategia de migración de datos.** Alembic existe, pero no se ha ejecutado contra una base real.

### 11.3 Riesgo arquitectónico principal

El riesgo no es que el diseño sea malo; es que **la documentación y la superficie API prometen más de lo que el runtime entrega**. Eso produce decisiones de negocio incorrectas (demostraciones, ventas, auditorías). FASE 9 corrige la documentación; FASE 7 está cerrada y el producto sigue necesitando el cierre de stubs y la validación Docker.

---

## 12. Cumplimiento y normativa

| Norma | Estado declarado | Verificación | Evaluación |
| :--- | :--- | :--- | :--- |
| ENS ALTA — control de acceso | VALIDATED | `require_clearance` + ABAC | Creíble en v1/v3; v2 sin matriz |
| ENS ALTA — MFA | VALIDATED | AES-256-GCM + ticket | Código sí; endpoints no montados |
| ENS ALTA — separación | PARTIAL | Contenedores, no MicroVM | Honesto |
| ENS ALTA — auditoría | VALIDATED | Hash chain + DB | Sin WORM |
| ENS ALTA — cifrado | PARTIAL | AES-256-GCM software | Sin HSM |
| ENS ALTA — continuidad | EXPERIMENTAL | Mesh offline | Móvil compila; mesh en dispositivos pendiente |
| STANAG 4774 | IMPLEMENTED | Metadatos Pydantic | Creíble |
| STANAG 4778 | PARTIAL | SHA-256 + JWS | Sin mTLS |
| mTLS federado | PLANNED | No existe | Correcto declararlo |

**Conclusión de compliance:** las etiquetas son mayoritariamente honestas. El problema es que "VALIDATED" a nivel de control no equivale a "expuesto y operado". La matriz de funcionalidades lo aclara.

---

## 13. Auditoría de dependencias

### 13.1 Backend (`backend/requirements.txt`)

| Grupo | Dependencias | Evaluación |
| :--- | :--- | :--- |
| Web | fastapi 0.115.6, uvicorn 0.34.0, pydantic 2.10.3, pydantic-settings 2.7.0 | Pins correctos |
| DB | sqlalchemy 2.0.36, asyncpg 0.32.0, alembic 1.14.0 | Pins correctos |
| Cache/Eventos | redis 5.2.1, nats-py 2.9.0 | Pins correctos |
| HTTP | httpx 0.28.1 | Pin correcto |
| Auth | python-jose 3.5.0, passlib 1.7.4, bcrypt 4.0.1, python-multipart 0.0.34 | Pins actualizados por SEC-FIX-006 |
| Crypto | cryptography 50.0.2 | Pin actualizado por SEC-FIX-006 |
| Tareas | celery 5.4.0 | Pin correcto |
| Observabilidad | prometheus-client 0.21.1 | Pin correcto |
| Rate limit | slowapi 0.1.9 | Presente, aunque el middleware propio es el usado |
| Grafos | neo4j 5.27.0 | Pin correcto |
| LLM | ollama 0.4.7 | Pin correcto |
| OSINT | beautifulsoup4 4.12.2, lxml 6.1.3, duckduckgo_search 7.5.0, trafilatura 2.0.0 | Pins actualizados |
| CV | opencv-python-headless 4.10.0.84, numpy 2.2.1; torch/ultralytics en `requirements-vision.txt` | Runtime base ligero; visión opcional |
| Test | pytest 8.3.4, pytest-asyncio 0.25.0, aiosqlite 0.21.0, pytest-cov | Cobertura de seguridad 88% |

Riesgos:

- `torch`/`ultralytics` salen del runtime base (SEC-FIX-006); sólo se instalan para visión.
- `pip-audit` corre en CI con allowlist `docs/security/SCA_ALLOWLIST.md` → **0 vulnerabilidades** reportadas.
- `duckduckgo_search` puede romperse por cambios del proveedor; no verificado aquí.
- `python-jose` se actualizó a 3.5.0; no se evaluó una alternativa `PyJWT`.

### 13.2 Frontend (`package.json`)

| Grupo | Dependencias | Evaluación |
| :--- | :--- | :--- |
| Framework | next ^16.4.6 + React 19 | **VERIFICADO** en copia con Node 20.18: `tsc` 0, `next build` OK |
| Estado | zustand ^4.4.0 | Correcto |
| Mapas | leaflet ^1.9.0, react-leaflet ^5.0.0 | Correcto |
| Gráficos | recharts ^2.10.0 | Correcto |
| Iconos | lucide-react ^1.77.0 | Correcto |
| Estilos | tailwindcss ^3.4.0 | Correcto |
| Calidad | typescript ^5.3.0, eslint ^9.0.0, eslint-config-next ^16.4.6 | Correcto |

Riesgos:

- Dependencias con `^` permiten actualizaciones menores no auditadas.
- `npm audit --omit=dev --audit-level=high` → 0 vulnerabilidades de producción; residual dev `brace-expansion` vía eslint.
- `leaflet` y `recharts` requieren `window`; se usan con `dynamic(..., { ssr: false })`, correcto.

### 13.3 Móvil (`pubspec.yaml`)

| Grupo | Dependencias | Evaluación |
| :--- | :--- | :--- |
| Red | http ^1.0.0, web_socket_channel ^2.4.0 | Correcto |
| Mesh | nearby_connections ^3.0.0 | Requiere permisos nativos; no probado |
| Seguridad | flutter_secure_storage ^9.0.0, cryptography ^2.7.0 | Correcto |
| Estado | flutter_bloc ^8.1.0, hydrated_bloc ^9.1.0 | Correcto |
| DB local | sqflite ^2.3.0, path_provider ^2.1.0 | Correcto; cola offline implementada en `core/storage/offline_queue.dart` |
| Mapas | flutter_map ^6.0.0, latlong2 ^0.9.0 | Correcto |
| UI | google_fonts ^6.1.0, fl_chart ^0.65.0 | Correcto |
| Sensores | sensors_plus ^3.0.0, location ^5.0.0 | Correcto |

Riesgo residual: el lockfile se regeneró al ejecutar `flutter analyze`; ya está alineado con Flutter 3.24.5. En CI debe fijarse la versión del SDK para evitar builds distintos. Ver R-010 (mitigado).

---

## 14. Comparación README vs realidad

| Afirmación del README | Realidad | Veredicto |
| :--- | :--- | :--- |
| "35 pruebas automatizadas" | 157 | DESACTUALIZADO |
| "PostgreSQL 15 + PostGIS" | PostgreSQL 16 + pgvector (imagen `pgvector/pgvector:pg16`) | DESACTUALIZADO |
| Stack microservicios | Monolito modular | INCORRECTO (si aparece) |
| 11 servicios | 12 | DESACTUALIZADO |
| Funcionalidades OSINT | Rutas stub | SOBREESTIMADO |
| Móvil offline-first | Compila, 11 tests, cola offline implementada | VERIFICADO |
| Seguridad MFA | Código sí, rutas no montadas | PARCIAL |

El README no es una fuente de verdad técnica. Se mantiene como documento de presentación; las cifras operativas viven en este paquete de FASE 9.

---

## 15. Auditoría de scripts y automatización

| Script | Función | Verificación | Estado |
| :--- | :--- | :--- | :--- |
| `scripts/validate_all.py` | pytest + invariantes + reporte JSON | ejecutado, exit 0 | VERIFICADO |
| `scripts/generate_keys.py` | claves Fernet/secretos | código | VERIFICADO (código) |
| `scripts/seed_data.py` | datos demo | no ejecutado (requiere DB) | BLOQUEADO |
| `scripts/demo.sh` / `.bat` | arranque demo | no ejecutado | BLOQUEADO |
| `scripts/init_ollama.sh` | modelo LLM | no ejecutado | BLOQUEADO |
| `scripts/archived/guardian/` | utilidades antiguas | archivado | AISLADO |
| `.github/workflows/ci.yml` | CI backend + frontend advisory | no ejecutado en GitHub | NO VERIFICADO |

`validate_all.py` comprueba:

1. Suite de tests.
2. Cifrado de secretos MFA.
3. Aislamiento de tickets MFA.
4. Validador de producción.
5. Lock de auditoría y modelos DB.

Es un buen gate, pero **no mide cobertura** y **no prueba infraestructura**.

---

## 16. Hallazgos priorizados

### 16.1 Bloqueantes de entrega

| ID | Hallazgo | Por qué bloquea |
| :--- | :--- | :--- |
| B-01 | Stubs en OSINT/Intel/Satellite/Agents | La API promete lo que no hace |
| B-03 | Docker no validado | No hay evidencia de despliegue |
| B-04 | Auditoría adversarial sin cierre formal | Exit Gate exige 0 CRITICAL/HIGH |

### 16.2 Altos

| ID | Hallazgo |
| :--- | :--- |
| A-01 | Cobertura global no fijada (88% sólo seguridad) |
| A-02 | MFA OSINT/Intel no montado |
| A-03 | Persistencia en memoria en dominios clave |
| A-04 | Advisory dev de `brace-expansion` (eslint); advisories de Starlette aceptadas |
| A-05 | Observabilidad sin scrape real |
| A-06 | Migraciones no ejecutadas |

### 16.3 Medios

| ID | Hallazgo |
| :--- | :--- |
| M-01 | Duplicidad `v1/intel` vs `api/intel` |
| M-02 | Dos escalas de clasificación |
| M-03 | `/metrics` sin auth |
| M-04 | Lock de auditoría no distribuido |
| M-05 | CSP incompatible con frontend separado |
| M-06 | `MFA_CHALLENGE_SECRET` fallback |
| M-07 | Sin paginación uniforme |

### 16.4 Bajos

| ID | Hallazgo |
| :--- | :--- |
| L-01 | `WebAuthn` 501 |
| L-02 | `/` revela entorno y modelo LLM |
| L-03 | `docs`/`openapi` expuestos en prod |
| L-04 | i18n ausente |

---

## 17. Recomendaciones (ordenadas)

1. **Cerrar stubs o despublicarlos.** Si OSINT/Intel/Satellite no se van a entregar, quitarlos del OpenAPI público. Si se van a entregar, montar los routers reales y añadir tests.
2. **Montar MFA OSINT/Intel** o retirar la promesa de la documentación y de la UI.
3. **Mantener el móvil verde**: `flutter analyze` 0 y `flutter test` 11; añadir tests de pantallas, cola y duress.
4. **Fijar cobertura global** además del 88% de las 6 suites de seguridad (agregado backend ~73%).
5. **Validar Docker** en un host con Docker: `docker compose config`, `up -d`, healthchecks, `/metrics`, Grafana.
6. **Ejecutar migraciones** contra PostgreSQL 16 con PostGIS y pgvector.
7. **Cerrar SEC-FIX-007/008**; el build de Next 16.4.6 ya está verificado.
8. **Restringir `/metrics`** a red interna o auth.
9. **Unificar escalas de clasificación** en una sola fuente.
10. **Documentar y probar** la concurrencia distribuida de auditoría.

---

## 18. Conclusión

El repositorio contiene un producto real, con arquitectura defendible y controles de seguridad por encima de la media. También contiene una parte importante de promesa no ejecutada. La auditoría no encuentra evidencia de malicia ni de "humo" deliberado: encuentra un proyecto en construcción cuya documentación se adelantó al código.

La corrección correcta no es maquillar los documentos, sino decir la verdad y priorizar:

- **Verdad:** este paquete de 8 documentos.
- **Prioridad 1:** stubs + Docker + SEC-FIX-007/008.
- **Prioridad 2:** cobertura + dependencias + persistencia.
- **Prioridad 3:** pulido de observabilidad y UX.

Con esas correcciones, el sistema puede pasar de "prototipo avanzado" a "producto entregable". Sin ellas, cualquier afirmación de producción es falsa.

---

## 19. Anexo: comandos de auditoría

```bash
# Inventario
find backend/app -name "*.py" | wc -l
find backend/app -name "*.py" -exec cat {} + | wc -l
find frontend/src \( -name "*.ts" -o -name "*.tsx" \) | wc -l
find mobile -name "*.dart" | wc -l

# Superficie
python3 -c "import json;d=json.load(open('backend/contracts/openapi.json'));print(len(d['paths']))"

# Tests
SECRET_KEY="test-secret-key-32-chars-minimum!!!" python3 -m pytest backend/tests -q
python3 scripts/validate_all.py

# Seguridad
grep -rn "require_clearance(" backend/app/api/v1/*.py | wc -l
grep -c "_CLEARANCE_DEPS)" backend/app/main.py
grep -n "_PinnedDNS\|peer address mismatch" backend/app/services/osint/tools/web_tools.py
grep -c "X-XSS" infra/nginx.conf

# Stubs
grep -rn '"cases": \[\]\|"reports": \[\]\|"status": "queued"' backend/app/api

# Infra
python3 -c "import yaml;d=yaml.safe_load(open('docker-compose.yml'));print(len(d['services']))"
grep -c "alert:" infra/alertmanager/alerts.yml
ls infra/grafana/provisioning/dashboards/*.json | wc -l

# Móvil
cd mobile/sesis_cop && flutter analyze && flutter test
```
