# FEATURE_MATRIX.md — Matriz de funcionalidades reales

**Doc ID:** FEAT-2026-SND-001
**Proyecto:** SmartNationDefense / SESIS-FEDERATION
**Fecha:** 2026-11-21
**Base:** código en `backend/app`, `frontend/src`, `mobile/sesis_cop/lib`, `infra/`, tests.
**Método:** lectura de código + introspección de rutas + ejecución de tests. Cada fila tiene evidencia.
**Autor:** `@architect`

> Esta matriz sustituye a la anterior. Su objetivo es responder a una pregunta: **¿qué puede hacer el producto hoy, no qué archivos existen?**

---

## 0. Leyenda de veredictos

| Veredicto | Definición operativa |
| :--- | :--- |
| `IMPLEMENTADO` | La capacidad existe en código, está conectada a una ruta o flujo real y tiene evidencia de ejecución o test. |
| `PARCIAL` | Existe una parte sustancial, pero falta persistencia, cobertura, conexión o completitud funcional. |
| `EXPERIMENTAL` | El código existe y puede ejecutarse, pero el resultado no es fiable para uso operativo (heurístico, sin modelo, sin datos). |
| `NO IMPLEMENTADO` | No hay código funcional para la capacidad. |
| `STUB` | Hay ruta y respuesta, pero devuelve datos fijos o vacíos sin lógica de dominio. |
| `PLANNED` | Declarado en documentación o roadmap, sin código. |
| `UNSUPPORTED` | Explícitamente fuera de alcance o dependiente de una plataforma no soportada. |
| `MUERTO` | Código presente pero no montado ni referenciado desde el entrypoint. |

### 0.1 Regla de doble nivel

Una funcionalidad puede ser `IMPLEMENTADO` a nivel de **servicio** y `STUB` a nivel de **API**. En ese caso se indica `Servicio: IMPLEMENTADO / API: STUB`. Esto evita la trampa de contar líneas de código como producto.

---

## 1. Resumen por dominio

| Dominio | Servicio | API | UI | Test | Veredicto de producto |
| :--- | :--- | :--- | :--- | :--- | :--- |
| Autenticación | IMPLEMENTADO | IMPLEMENTADO | IMPLEMENTADO | IMPLEMENTADO | IMPLEMENTADO |
| MFA OSINT/Intel | IMPLEMENTADO | MUERTO | NO IMPLEMENTADO | PARCIAL | NO IMPLEMENTADO |
| Autorización/clearance | IMPLEMENTADO | IMPLEMENTADO | PARCIAL | IMPLEMENTADO | IMPLEMENTADO |
| Auditoría encadenada | IMPLEMENTADO | IMPLEMENTADO | NO IMPLEMENTADO | IMPLEMENTADO | IMPLEMENTADO |
| SSRF | IMPLEMENTADO | IMPLEMENTADO | — | IMPLEMENTADO | IMPLEMENTADO |
| Rate limiting | IMPLEMENTADO | IMPLEMENTADO | — | IMPLEMENTADO | IMPLEMENTADO |
| C2 / activos / alertas | IMPLEMENTADO | IMPLEMENTADO | IMPLEMENTADO | PARCIAL | IMPLEMENTADO |
| Inteligencia (productos/PIR) | IMPLEMENTADO | IMPLEMENTADO | PARCIAL | PARCIAL | PARCIAL |
| OSINT | IMPLEMENTADO (servicio) | STUB | NO IMPLEMENTADO | NO VERIFICADO | STUB |
| Satellite/IMINT | IMPLEMENTADO (servicio) | STUB | PARCIAL | NO VERIFICADO | STUB |
| Tactical (OPORD/BDA/fires) | IMPLEMENTADO | IMPLEMENTADO | PARCIAL | NO VERIFICADO | PARCIAL |
| Agents/Mesh/Wearable | IMPLEMENTADO (servicio) | STUB | PARCIAL | NO VERIFICADO | STUB |
| Planning OPORD | IMPLEMENTADO | IMPLEMENTADO | PARCIAL | NO VERIFICADO | PARCIAL |
| Logistics | IMPLEMENTADO (memoria) | PARCIAL | IMPLEMENTADO | NO VERIFICADO | PARCIAL |
| Messaging | IMPLEMENTADO (memoria) | PARCIAL | IMPLEMENTADO | NO VERIFICADO | PARCIAL |
| AAR | IMPLEMENTADO (memoria) | PARCIAL | IMPLEMENTADO | NO VERIFICADO | PARCIAL |
| Reports | IMPLEMENTADO (memoria) | PARCIAL | IMPLEMENTADO | NO VERIFICADO | PARCIAL |
| Fusion JDL | IMPLEMENTADO (heurístico) | IMPLEMENTADO | PARCIAL | PARCIAL | EXPERIMENTAL |
| Prediction | IMPLEMENTADO | IMPLEMENTADO | IMPLEMENTADO | NO VERIFICADO | PARCIAL |
| Terrain | IMPLEMENTADO | IMPLEMENTADO | IMPLEMENTADO | IMPLEMENTADO | IMPLEMENTADO |
| Map | IMPLEMENTADO | IMPLEMENTADO | IMPLEMENTADO | NO VERIFICADO | PARCIAL |
| Voice | IMPLEMENTADO | IMPLEMENTADO | IMPLEMENTADO | NO VERIFICADO | PARCIAL |
| Maven / Vision | PARCIAL | IMPLEMENTADO | IMPLEMENTADO | PARCIAL | EXPERIMENTAL |
| COA v3 | IMPLEMENTADO | IMPLEMENTADO | PARCIAL | NO VERIFICADO | PARCIAL |
| Graph/Neo4j | PARCIAL | NO IMPLEMENTADO | NO IMPLEMENTADO | NO VERIFICADO | PARCIAL |
| LLM | PARCIAL | PARCIAL | — | NO VERIFICADO | PARCIAL |
| Event bus | IMPLEMENTADO | — | — | IMPLEMENTADO | IMPLEMENTADO |
| Observability | IMPLEMENTADO | IMPLEMENTADO | NO IMPLEMENTADO | IMPLEMENTADO | IMPLEMENTADO |
| Frontend COP | — | — | IMPLEMENTADO | NO VERIFICADO | PARCIAL |
| Mobile COP | — | — | IMPLEMENTADO | IMPLEMENTADO | IMPLEMENTADO |
| Offline mesh | EXPERIMENTAL | — | IMPLEMENTADO | IMPLEMENTADO | PARCIAL |
| Docker | — | — | — | NO VERIFICADO | PARCIAL |
| CI/CD | — | — | — | NO VERIFICADO | PLANNED |
| Compliance | PARCIAL | — | — | NO VERIFICADO | PARCIAL |

---

## 2. Autenticación y sesión

### F-01 — Login con JWT

| Campo | Valor |
| :--- | :--- |
| Veredicto | `IMPLEMENTADO` |
| Servicio | `app/core/security.py`, `app/api/auth.py` |
| API | `POST /api/v1/auth/login` |
| Persistencia | `users` (PostgreSQL; tests con SQLite) |
| Evidencia | `test_auth.py` (7 tests) |
| Comando | `pytest backend/tests/test_auth.py -q` |
| Limitación | No se probó contra PostgreSQL real |

**Comportamiento:** valida usuario activo, verifica bcrypt, emite access (15 min) y refresh (7 días) con claims `sub`, `username`, `role`, `clearance`.

### F-02 — Refresh con rotación

| Campo | Valor |
| :--- | :--- |
| Veredicto | `IMPLEMENTADO` |
| API | `POST /api/v1/auth/refresh` |
| Evidencia | `revoke_jti`, `is_jti_revoked`, `test_auth.py` |
| Limitación | Redis real no probado; fallback en memoria |

**Comportamiento:** decodifica el refresh con `is_refresh=True`, comprueba `jti` no revocado, revoca el usado y emite un par nuevo. Reutilizar un refresh devuelve 401.

### F-03 — Logout con revocación

| Campo | Valor |
| :--- | :--- |
| Veredicto | `IMPLEMENTADO` |
| API | `POST /api/v1/auth/logout` |
| Evidencia | `revoke_jti` |
| Limitación | Si Redis cae, la revocación no persiste |

### F-04 — Identidad actual

| Campo | Valor |
| :--- | :--- |
| Veredicto | `IMPLEMENTADO` |
| API | `GET /api/v1/auth/me` |
| Evidencia | `app/api/auth.py` |
| Limitación | — |

### F-05 — Registro de usuario

| Campo | Valor |
| :--- | :--- |
| Veredicto | `IMPLEMENTADO` |
| API | `POST /api/v1/auth/register` |
| Evidencia | `test_auth.py` |
| Limitación | El usuario nace inactivo; no hay flujo de aprobación automatizado |

### F-06 — MFA TOTP OSINT

| Campo | Valor |
| :--- | :--- |
| Veredicto | `NO IMPLEMENTADO` (a nivel de producto) |
| Servicio | `IMPLEMENTADO` — `services/intel/auth/mfa.py`, `api/osint/auth.py` |
| API | `MUERTO` — router no montado |
| Evidencia | `grep -n "osint/auth" backend/app/main.py` → sin resultados |
| Test | `test_mfa_security.py` prueba cifrado y tipo, no el flujo HTTP |
| Impacto | La promesa de MFA OSINT no es accesible |

### F-07 — MFA Intel L3

| Campo | Valor |
| :--- | :--- |
| Veredicto | `NO IMPLEMENTADO` (a nivel de producto) |
| Servicio | `PARCIAL` — `api/intel/auth.py` |
| API | `MUERTO` |
| Evidencia | Router no incluido en `main.py` |
| Limitación | WebAuthn devuelve 501 por diseño |

### F-08 — Revocación de tokens

| Campo | Valor |
| :--- | :--- |
| Veredicto | `PARCIAL` |
| Evidencia | `revoke_jti`, `is_jti_revoked` |
| Limitación | Depende de Redis; sin Redis usa fallback local no distribuido |

---

## 3. Autorización y clasificación

### F-10 — Clearance jerárquico

| Campo | Valor |
| :--- | :--- |
| Veredicto | `IMPLEMENTADO` |
| Niveles | `OPEN < RESTRICTED < CONFIDENTIAL < SECRET < TOP_SECRET` |
| Evidencia | `CLEARANCE_ORDER`, `require_clearance` |
| Test | `test_clearance_enforcement.py` (5) |
| Cobertura | 19 routers, 109 referencias en v1 |
| Limitación | v2 sin matriz de introspección |

### F-11 — ABAC

| Campo | Valor |
| :--- | :--- |
| Veredicto | `PARCIAL` |
| Evidencia | `ABACEngine` en `security.py` |
| Limitación | No hay tests específicos de atributos (tenant, compartimento) |

### F-12 — Clearance router-level

| Campo | Valor |
| :--- | :--- |
| Veredicto | `IMPLEMENTADO` |
| Evidencia | `_CLEARANCE_DEPS` en 19 routers |
| Test | `test_v1_clearance_matrix.py` (5), 141 rutas, 0 gaps |
| Limitación | Sólo v1/v3 |

### F-13 — Etiquetado STANAG/TLP

| Campo | Valor |
| :--- | :--- |
| Veredicto | `PARCIAL` |
| Evidencia | `classification.py` (`TLPMarker`, `STANAG4774`) |
| Limitación | No se aplica en respuestas HTTP ni en serialización |

### F-14 — IDOR / ownership

| Campo | Valor |
| :--- | :--- |
| Veredicto | `PARCIAL` |
| Evidencia | Algunos handlers filtran por usuario; no hay patrón uniforme |
| Limitación | Sin tests sistemáticos de acceso cruzado |
| Riesgo | R-006 |

---

## 4. Auditoría

### F-20 — Cadena SHA-256

| Campo | Valor |
| :--- | :--- |
| Veredicto | `IMPLEMENTADO` |
| Evidencia | `AuditChain.record`, `_compute_hash`, `verify_chain` |
| Test | `test_audit_persistence.py` (3), `test_audit_unified.py` (3) |
| Persistencia | `audit_log` |
| Limitación | Lock por proceso; sin WORM |

### F-21 — Detección de manipulación

| Campo | Valor |
| :--- | :--- |
| Veredicto | `IMPLEMENTADO` |
| Evidencia | `verify_chain` detecta hash y orden |
| Test | tamper por detalle y reordenación |
| Limitación | No hay endpoint HTTP de verificación montado para operadores |

### F-22 — Concurrencia

| Campo | Valor |
| :--- | :--- |
| Veredicto | `PARCIAL` |
| Evidencia | `asyncio.Lock` + test de 10 tareas |
| Limitación | No distribuido entre réplicas |
| Riesgo | R-007 |

### F-23 — Auditoría de accesos clasificados

| Campo | Valor |
| :--- | :--- |
| Veredicto | `PARCIAL` |
| Evidencia | `record_security_event`, `clearance_denied` |
| Limitación | No todas las lecturas generan entrada |

---

## 5. Seguridad de red y aplicación

### F-30 — SSRF IPv4

| Campo | Valor |
| :--- | :--- |
| Veredicto | `IMPLEMENTADO` |
| Evidencia | `is_safe_url_async`, `_resolve_validated_ips` |
| Test | `test_ssrf.py` |
| Cobertura | loopback, 10/8, 192.168/16, metadatos |

### F-31 — SSRF IPv6

| Campo | Valor |
| :--- | :--- |
| Veredicto | `IMPLEMENTADO` |
| Evidencia | mismas funciones |
| Test | loopback, ULA, link-local, IPv4-mapped |

### F-32 — IP pinning

| Campo | Valor |
| :--- | :--- |
| Veredicto | `IMPLEMENTADO` |
| Evidencia | `_PinnedDNS`, peer check |
| Test | `test_pinned_dns_returns_validated_ip`, `test_pinned_dns_restores_resolver` |

### F-33 — SSRF en descarga de imágenes

| Campo | Valor |
| :--- | :--- |
| Veredicto | `IMPLEMENTADO` |
| Evidencia | `services/vision/analyst.py` |
| Test | `test_vision_ssrf.py` (10) |

### F-34 — Rate limit por ventana

| Campo | Valor |
| :--- | :--- |
| Veredicto | `IMPLEMENTADO` |
| Evidencia | `SlidingWindowRateLimiter` |
| Test | `test_rate_limit.py` (6) |
| Limitación | Redis falso en tests |

### F-35 — Lockout de fuerza bruta

| Campo | Valor |
| :--- | :--- |
| Veredicto | `IMPLEMENTADO` |
| Evidencia | claves path-aware, ZSET |
| Test | `TestDistributedBruteForce` (4) |
| Limitación | No probado con dos procesos reales |

### F-36 — Circuit breaker de rate limit

| Campo | Valor |
| :--- | :--- |
| Veredicto | `IMPLEMENTADO` (decisión fail-open) |
| Evidencia | `CircuitBreaker` |
| Limitación | Fail-open aceptado |

### F-37 — Cabeceras de seguridad

| Campo | Valor |
| :--- | :--- |
| Veredicto | `IMPLEMENTADO` |
| Evidencia | `infra/nginx.conf` |
| Cobertura | HSTS, XFO, XCTO, CSP, Referrer, Permissions, X-Permitted |
| Limitación | No probado con `curl -I` real |

### F-38 — Hardening de producción

| Campo | Valor |
| :--- | :--- |
| Veredicto | `IMPLEMENTADO` |
| Evidencia | `validate_production_hardening` |
| Test | `validate_all.py` invariante 3 |
| Limitación | No se arrancó en producción real |

### SEC-FIX — Endurecimiento FASE 3

| Fix | Estado | Evidencia |
| :--- | :--- | :--- |
| SEC-FIX-001 — fail-closed | CORREGIDO | `SECURITY_FAIL_MODE` closed en staging/prod; 503 en rate-limit/`is_jti_revoked`; abort sin Redis; métrica `sesis_security_fail_open_total` |
| SEC-FIX-002 — SSRF visión | CORREGIDO | `services/vision/analyst.py` + `test_vision_ssrf.py` |
| SEC-FIX-003 — credenciales | CORREGIDO | Defaults y validación de producción |
| SEC-FIX-004 — IP de cliente | CORREGIDO | `resolve_client_ip` + `TRUSTED_PROXIES`; bucket por `sub` |
| SEC-FIX-005 — lockout login | CORREGIDO | Redis path-aware en `/api/v1/auth/login`, 429 + `Retry-After`, auditoría |
| SEC-FIX-006 — SCA/pins | PARCIAL | Pins actualizados; torch/ultralytics fuera del runtime; `pip-audit` 0 con allowlist; `npm audit` en CI |
| SEC-FIX-007 | ABIERTO (MEDIUM) | Auditoría adversarial |
| SEC-FIX-008 | ABIERTO (MEDIUM) | Auditoría adversarial |

Test: `test_security_core.py` (34), `test_rate_limit_hardening.py` (7), `test_login_lockout.py` (2), `test_vision_yolo_integrity.py` (5).

---

## 6. C2 y inteligencia

### F-40 — Registro de activos

| Campo | Valor |
| :--- | :--- |
| Veredicto | `IMPLEMENTADO` |
| API | `POST /api/v1/c2/register`, `GET /api/v1/c2/`, `GET /api/v1/c2/{id}` |
| Evidencia | `v1/assets.py`, `Asset` |
| Persistencia | DB |
| Test | No específico; DB refs verificadas |
| Limitación | Sin paginación |

### F-41 — Alertas

| Campo | Valor |
| :--- | :--- |
| Veredicto | `IMPLEMENTADO` |
| API | `v1/alerts.py` |
| Evidencia | DB refs (5), `require_clearance` |
| Test | No específico |
| Limitación | Sin test de contrato de alerta |

### F-42 — Eventos y timeline

| Campo | Valor |
| :--- | :--- |
| Veredicto | `IMPLEMENTADO` |
| API | `v1/ingestion.py`, `v1/timeline.py` |
| Evidencia | `EventStore` |
| Test | `test_intel_api.py` |
| Limitación | Ingesta no probada contra NATS real |

### F-43 — PIR y productos de inteligencia

| Campo | Valor |
| :--- | :--- |
| Veredicto | `IMPLEMENTADO` |
| API | `/api/v1/c2/pir`, `/api/v1/c2/products` |
| Evidencia | `v1/intel.py` (357 LOC, 15 DB refs) |
| Test | `test_intel_api.py` (3) |
| Limitación | Sin LLM real en tests |

### F-44 — Fusión de informes

| Campo | Valor |
| :--- | :--- |
| Veredicto | `PARCIAL` |
| API | `POST /api/v1/c2/fuse`, `/api/v1/fusion/*` |
| Evidencia | `services/fusion/engine.py`, `jdl_fusion.py` |
| Test | No específico |
| Limitación | Heurístico; sin datos reales |

### F-45 — Briefing estratégico

| Campo | Valor |
| :--- | :--- |
| Veredicto | `PARCIAL` |
| API | `POST /api/v1/c2/strategic-briefing` |
| Evidencia | `llm_orchestrator` |
| Limitación | Requiere Ollama/modelo |

### F-46 — Grafo de inteligencia

| Campo | Valor |
| :--- | :--- |
| Veredicto | `PARCIAL` |
| Servicio | `services/osint/graph_intel.py`, `agents/neo4j_service.py` |
| API | No montada |
| Evidencia | Código Neo4j |
| Limitación | Sin runtime Neo4j ni endpoint |

---

## 7. OSINT

### F-50 — Herramientas web

| Campo | Valor |
| :--- | :--- |
| Veredicto | `IMPLEMENTADO` (servicio) |
| Evidencia | `services/osint/tools/web_tools.py` (SSRF) |
| Test | `test_ssrf.py` |
| API | **STUB** |

### F-51 — DNS/WHOIS/certificados

| Campo | Valor |
| :--- | :--- |
| Veredicto | `IMPLEMENTADO` (servicio) |
| Evidencia | `dns_tools.py`, `whois_tools.py`, `cert_tools.py` |
| Test | No específico |
| API | **STUB** |

### F-52 — Redes sociales y documentos

| Campo | Valor |
| :--- | :--- |
| Veredicto | `PARCIAL` |
| Evidencia | `social_tools.py`, `document_tools.py`, `archive_tools.py` |
| Limitación | Depende de APIs externas y HTML cambiante |
| API | **STUB** |

### F-53 — Wrappers de enriquecimiento

| Campo | Valor |
| :--- | :--- |
| Veredicto | `PARCIAL` |
| Evidencia | Hunter, HIBP, Shodan, VirusTotal |
| Limitación | Claves opcionales; no probados |
| API | No montada |

### F-54 — Casos y entidades OSINT

| Campo | Valor |
| :--- | :--- |
| Veredicto | `STUB` |
| API | `GET /api/v1/osint/cases`, `/entities` |
| Evidencia | `return {"cases": [], "total": 0}` |
| Impacto | La UI puede mostrar vacíos que parecen "sin datos" |

### F-55 — Jobs OSINT

| Campo | Valor |
| :--- | :--- |
| Veredicto | `STUB` |
| API | `GET /api/v1/osint/jobs` |
| Evidencia | lista vacía |

---

## 8. Satellite / IMINT

### F-60 — Análisis de imagen satelital

| Campo | Valor |
| :--- | :--- |
| Veredicto | `STUB` (API) / `PARCIAL` (servicio) |
| API | `POST /api/v1/satellite/analyze` → `{"status": "queued"}` |
| Servicio | `services/satellite/annotator.py`, `detector.py`, `ollama_analyst.py` |
| Limitación | No hay cola ni worker que procese el "queued" |

### F-61 — Detección de cambios

| Campo | Valor |
| :--- | :--- |
| Veredicto | `PARCIAL` (servicio) |
| Evidencia | `change_detection.py` |
| API | No montada |
| Limitación | Requiere imágenes y modelo |

### F-62 — TLEs y tracking

| Campo | Valor |
| :--- | :--- |
| Veredicto | `PARCIAL` |
| Evidencia | `sentinel.py`, Celestrak config |
| Limitación | Sin red en tests |
| API | No montada en `/api/v1/satellite` |

### F-63 — GDELT

| Campo | Valor |
| :--- | :--- |
| Veredicto | `PARCIAL` |
| Evidencia | `gdelt.py` |
| Limitación | Sin prueba de red |

---

## 9. Táctico

### F-70 — OPORD

| Campo | Valor |
| :--- | :--- |
| Veredicto | `IMPLEMENTADO` |
| API | `/api/v1/tactical/opord/*`, `/api/v1/planning/*` |
| Servicio | `opord_generator.py`, `opord_enhanced.py` |
| Limitación | Persistencia en memoria en planning |

### F-71 — Wargaming

| Campo | Valor |
| :--- | :--- |
| Veredicto | `IMPLEMENTADO` (heurístico) |
| API | `/api/v1/tactical/wargaming/*` |
| Evidencia | `wargaming.py` |
| Limitación | No es simulación física; es modelo de puntuación |

### F-72 — BDA

| Campo | Valor |
| :--- | :--- |
| Veredicto | `IMPLEMENTADO` (heurístico) |
| API | `/api/v1/tactical/bda/*` |
| Evidencia | `bda.py` |
| Limitación | Requiere datos de entrada válidos; no valida imágenes reales |

### F-73 — Joint Fires

| Campo | Valor |
| :--- | :--- |
| Veredicto | `PARCIAL` |
| API | `/api/v1/tactical/fires/*` |
| Evidencia | `joint_fires.py` |
| Limitación | Cálculos geométricos; sin integración de armas real |

### F-74 — PSYOPS

| Campo | Valor |
| :--- | :--- |
| Veredicto | `PARCIAL` |
| API | `/api/v1/tactical/psyops/*` |
| Evidencia | `psyops.py` |
| Limitación | Generación de mensajes; sin evaluación de efecto |

### F-75 — COA v3

| Campo | Valor |
| :--- | :--- |
| Veredicto | `IMPLEMENTADO` |
| API | `/api/v3/coa/*` |
| Evidencia | `coa_engine.py` |
| Limitación | Heurístico; sin validación operativa |

### F-76 — Planning enriquecido

| Campo | Valor |
| :--- | :--- |
| Veredicto | `PARCIAL` |
| API | `/api/v1/planning/*` (11) |
| Evidencia | `opord_enhanced.py` |
| Limitación | En memoria |

---

## 10. Agentes y mesh

### F-80 — Estado de agentes

| Campo | Valor |
| :--- | :--- |
| Veredicto | `STUB` |
| API | `GET /api/v1/agents/status` |
| Evidencia | `return {"module": "agents", "status": "operational"}` |

### F-81 — Mesh broadcast/nodes

| Campo | Valor |
| :--- | :--- |
| Veredicto | `STUB` |
| API | `/api/v1/agents/mesh/*` |
| Servicio | `services/agents/agent_sync.py` |
| Limitación | No conectado |

### F-82 — Sensores mesh

| Campo | Valor |
| :--- | :--- |
| Veredicto | `PARCIAL` |
| API | `/api/v1/agents/sensors/*` |
| Evidencia | `sensor_mesh_api.py` → `sensor_mesh` |
| Test | No específico |
| Limitación | Estado en memoria; sin dispositivo real |

### F-83 — Wearable

| Campo | Valor |
| :--- | :--- |
| Veredicto | `STUB` |
| API | `/api/v1/agents/wearable/*` |
| Evidencia | 10 LOC de router |

### F-84 — Steganografía

| Campo | Valor |
| :--- | :--- |
| Veredicto | `STUB` |
| API | `/api/v1/agents/stego/*` |
| Evidencia | 10 LOC de router |

### F-85 — Data diode / kill switch / Link16

| Campo | Valor |
| :--- | :--- |
| Veredicto | `PARCIAL` (servicio) |
| Evidencia | `data_diode.py`, `kill_switch.py`, `link16_service.py` |
| API | No montada |
| Limitación | Sin hardware |

### F-86 — Wiper remoto

| Campo | Valor |
| :--- | :--- |
| Veredicto | `STUB` |
| API | `POST /api/v1/agents/mobile/wipe/{device_id}` |
| Evidencia | router mínimo |
| Riesgo | Si se implementa sin autorización fuerte, es peligroso |

---

## 11. Logística, mensajería y reportes

### F-90 — Logística v1

| Campo | Valor |
| :--- | :--- |
| Veredicto | `PARCIAL` |
| API | `/api/v1/logistics/*` (7) |
| Evidencia | `services/logistics/service.py` |
| Limitación | Memoria |

### F-91 — Logística v2

| Campo | Valor |
| :--- | :--- |
| Veredicto | `IMPLEMENTADO` |
| API | `/api/v2/logistics/*` (4) |
| Evidencia | DB refs (13) |
| Limitación | Duplica dominio con v1 |

### F-92 — Mensajería

| Campo | Valor |
| :--- | :--- |
| Veredicto | `PARCIAL` |
| API | `/api/v1/messaging/*` (6) |
| Evidencia | `messaging_service` |
| Limitación | Memoria; sin entrega real |

### F-93 — AAR

| Campo | Valor |
| :--- | :--- |
| Veredicto | `PARCIAL` |
| API | `/api/v1/aar/*` (6) |
| Evidencia | `aar_service` |
| Limitación | Memoria |

### F-94 — Reportes

| Campo | Valor |
| :--- | :--- |
| Veredicto | `PARCIAL` |
| API | `/api/v1/reports/*` (6) |
| Evidencia | `reports_service` |
| Limitación | Memoria; sin PDF |

### F-95 — Predicción de amenazas

| Campo | Valor |
| :--- | :--- |
| Veredicto | `PARCIAL` |
| API | `/api/v1/prediction/*` (5) |
| Evidencia | Kalman + DB |
| Limitación | Calibración no validada |

---

## 12. Geografía, mapa y voz

### F-100 — Terreno

| Campo | Valor |
| :--- | :--- |
| Veredicto | `IMPLEMENTADO` |
| API | `/api/v1/terrain/*` (5) |
| Evidencia | Open Elevation + caché |
| Test | `test_terrain.py` (2) |
| Limitación | Sin red real |

### F-101 — Mapa táctico

| Campo | Valor |
| :--- | :--- |
| Veredicto | `PARCIAL` |
| API | `/api/v1/map/*` (8) |
| Evidencia | `tactical_map.py` |
| Limitación | Sin PostGIS real |

### F-102 — Voz

| Campo | Valor |
| :--- | :--- |
| Veredicto | `PARCIAL` |
| API | `/api/v1/voice/*` (3) |
| Evidencia | `voice_service` |
| Limitación | Sin STT real |

---

## 13. Maven, visión y ML

### F-110 — YOLO

| Campo | Valor |
| :--- | :--- |
| Veredicto | `EXPERIMENTAL` |
| Evidencia | `yolo_loader.py`, `torch`, `ultralytics` |
| Limitación | Sin pesos ni GPU; no probado |

### F-111 — Análisis de frame de dron

| Campo | Valor |
| :--- | :--- |
| Veredicto | `EXPERIMENTAL` |
| API | `POST /api/v3/vision/drone-frame` |
| Evidencia | `drone_processor.py` |
| Limitación | Requiere modelo |

### F-112 — Cambio en satélite

| Campo | Valor |
| :--- | :--- |
| Veredicto | `EXPERIMENTAL` |
| API | `POST /api/v3/vision/detect-changes` |
| Evidencia | `analyst.py` |
| Limitación | Depende de imágenes válidas |

### F-113 — Fusión Maven

| Campo | Valor |
| :--- | :--- |
| Veredicto | `PARCIAL` |
| API | `/api/v3/fusion/*` |
| Evidencia | `v3/router.py` (5 imports) |
| Limitación | Sin datos reales |

### F-114 — Anomalías ML

| Campo | Valor |
| :--- | :--- |
| Veredicto | `EXPERIMENTAL` |
| Evidencia | `ml/anomalies.py`, `isolation_forest.py` |
| API | No directa |
| Limitación | Sin entrenamiento |

### F-115 — Correlación ML

| Campo | Valor |
| :--- | :--- |
| Veredicto | `EXPERIMENTAL` |
| Evidencia | `ml/correlation.py`, `correlation_engine.py` |
| Limitación | Reglas + heurística |

### F-116 — Briefing

| Campo | Valor |
| :--- | :--- |
| Veredicto | `PARCIAL` |
| Evidencia | `ml/briefing.py`, LLM |
| Limitación | Requiere modelo |

---

## 14. LLM

### F-120 — Ollama local

| Campo | Valor |
| :--- | :--- |
| Veredicto | `PARCIAL` |
| Evidencia | `services/intel/ollama.py`, `llm_orchestrator.py` |
| Limitación | Modelo no descargado en el entorno |

### F-121 — Fallback OpenRouter/vLLM

| Campo | Valor |
| :--- | :--- |
| Veredicto | `PARCIAL` |
| Evidencia | `openrouter.py`, `vllm.py` |
| Limitación | Claves opcionales; no probado |

### F-122 — RAG

| Campo | Valor |
| :--- | :--- |
| Veredicto | `PARCIAL` |
| Evidencia | `rag.py` |
| Limitación | Sin vector store real (pgvector no ejecutado) |

### F-123 — Prompt injection

| Campo | Valor |
| :--- | :--- |
| Veredicto | `NO IMPLEMENTADO` |
| Evidencia | Sin validación específica |
| Riesgo | R-015 |

---

## 15. Eventos e integración

### F-130 — NATS con DLQ

| Campo | Valor |
| :--- | :--- |
| Veredicto | `IMPLEMENTADO` |
| Evidencia | `core/events.py` |
| Test | `test_events_dlq.py` (3) |
| Limitación | Fallback en memoria; sin NATS real |

### F-131 — Idempotencia

| Campo | Valor |
| :--- | :--- |
| Veredicto | `IMPLEMENTADO` |
| Evidencia | `nats:idem:*`, SETNX + TTL |
| Test | `test_events_dlq.py` |

### F-132 — Ack/Nak

| Campo | Valor |
| :--- | :--- |
| Veredicto | `IMPLEMENTADO` |
| Evidencia | `_deliver` |
| Limitación | Sin broker real |

### F-133 — Celery workers

| Campo | Valor |
| :--- | :--- |
| Veredicto | `PARCIAL` |
| Evidencia | `workers/celery_app.py`, compose |
| Limitación | No arrancado; tareas no inventariadas en detalle |

---

## 16. Observabilidad

### F-140 — Métricas

| Campo | Valor |
| :--- | :--- |
| Veredicto | `IMPLEMENTADO` |
| Evidencia | `core/metrics.py`, `/metrics` |
| Test | `/metrics` en `app/main.py` + 7 dashboards + 8 alertas |
| Limitación | Scrape Prometheus real pendiente de Docker |

### F-141 — Dashboards

| Campo | Valor |
| :--- | :--- |
| Veredicto | `PARCIAL` |
| Evidencia | 7 JSON, 56 paneles |
| Limitación | No provisionados en runtime |

### F-142 — Alertas

| Campo | Valor |
| :--- | :--- |
| Veredicto | `PARCIAL` |
| Evidencia | 8 reglas |
| Limitación | No evaluadas por Prometheus real |

### F-143 — Logs estructurados

| Campo | Valor |
| :--- | :--- |
| Veredicto | `NO IMPLEMENTADO` |
| Evidencia | `logging` básico |
| Limitación | Sin agregación ni correlación |

### F-144 — Trazas

| Campo | Valor |
| :--- | :--- |
| Veredicto | `NO IMPLEMENTADO` |
| Evidencia | Sin OpenTelemetry |

---

## 17. Frontend

### F-150 — COP web

| Campo | Valor |
| :--- | :--- |
| Veredicto | `PARCIAL` |
| Evidencia | 24 componentes COP, 45 archivos |
| Build | **VERIFICADO** en copia con Node 20.18: `tsc` 0, `next build` OK, 4 rutas, `npm audit --omit=dev` 0 |
| Limitación | Sin tests; algunos paneles dependen de stubs |

### F-151 — Login web

| Campo | Valor |
| :--- | :--- |
| Veredicto | `IMPLEMENTADO` |
| Evidencia | `login/page.tsx` |
| Limitación | Sin test E2E |

### F-152 — Estados UX

| Campo | Valor |
| :--- | :--- |
| Veredicto | `PARCIAL` |
| Evidencia | `Skeleton`, `EmptyState`, `useApiData` |
| Limitación | No todas las vistas los usan |

### F-153 — Design tokens

| Campo | Valor |
| :--- | :--- |
| Veredicto | `IMPLEMENTADO` |
| Evidencia | `globals.css` |
| Limitación | Documentación previa desalineada (corregida) |

### F-154 — Responsive

| Campo | Valor |
| :--- | :--- |
| Veredicto | `PARCIAL` |
| Evidencia | Tailwind breakpoints |
| Limitación | Sin verificación visual 375/768/1440 |

### F-155 — Accesibilidad

| Campo | Valor |
| :--- | :--- |
| Veredicto | `PARCIAL` |
| Evidencia | `aria-live`, `role=status`, `aria-busy` |
| Limitación | Sin auditoría axe/WCAG AA |

---

## 18. Móvil

### F-160 — Navegación

| Campo | Valor |
| :--- | :--- |
| Veredicto | `IMPLEMENTADO` |
| Evidencia | `main.dart`, 7 rutas; `flutter analyze` 0 errores |
| Limitación | Mesh en dispositivos pendiente |

### F-161 — Tema táctico

| Campo | Valor |
| :--- | :--- |
| Veredicto | `IMPLEMENTADO` |
| Evidencia | `app_theme.dart`, `colors.dart`; `CardTheme` corregido |
| Limitación | Tema no auditado visualmente |

### F-162 — Cliente API

| Campo | Valor |
| :--- | :--- |
| Veredicto | `PARCIAL` |
| Evidencia | `api_client.dart` |
| Limitación | Sin tests de integración de API |

### F-163 — Offline queue

| Campo | Valor |
| :--- | :--- |
| Veredicto | `IMPLEMENTADO` |
| Evidencia | `core/storage/offline_queue.dart` (138 LOC); `mesh_service.dart` la usa |
| Test | Flujo cubierto por tests de protocolo; persistencia no aislada |

### F-164 — Mesh

| Campo | Valor |
| :--- | :--- |
| Veredicto | `PARCIAL` |
| Evidencia | `mesh_protocol.dart`, `mesh_service.dart`, 11 tests |
| Limitación | Sin dispositivos reales; `nearby_connections` no probado |

### F-165 — Duress

| Campo | Valor |
| :--- | :--- |
| Veredicto | `PARCIAL` |
| Evidencia | `duress_screen.dart` |
| Limitación | Sin política de borrado verificada |

### F-166 — Secure storage

| Campo | Valor |
| :--- | :--- |
| Veredicto | `PARCIAL` |
| Evidencia | `flutter_secure_storage` declarado |
| Limitación | No probado en dispositivo |

---

## 19. Plataforma, infra y docs

### F-170 — Docker Compose

| Campo | Valor |
| :--- | :--- |
| Veredicto | `PARCIAL` |
| Evidencia | 12 servicios, 12 healthchecks |
| Limitación | No ejecutado |

### F-171 — Nginx

| Campo | Valor |
| :--- | :--- |
| Veredicto | `IMPLEMENTADO` (config) |
| Evidencia | TLS, CSP, rate limit, healthz |
| Limitación | Sin `nginx -t` |

### F-172 — CI/CD

| Campo | Valor |
| :--- | :--- |
| Veredicto | `PLANNED` |
| Evidencia | `.github/workflows/ci.yml` |
| Limitación | No ejecutado en GitHub; frontend advisory |

### F-173 — Scripts

| Campo | Valor |
| :--- | :--- |
| Veredicto | `PARCIAL` |
| Evidencia | `validate_all.py` ejecutado; seed/demo no |

### F-174 — Documentación

| Campo | Valor |
| :--- | :--- |
| Veredicto | `PARCIAL` (en reparación) |
| Evidencia | Este paquete de 8 docs |
| Limitación | El resto de docs puede seguir desactualizado |

### F-175 — Compliance

| Campo | Valor |
| :--- | :--- |
| Veredicto | `PARCIAL` |
| Evidencia | `compliance/*.md` |
| Limitación | Declaraciones no verificadas externamente |

---

## 20. Resumen cuantitativo

### 20.1 Conteo por veredicto (nivel producto)

| Veredicto | Cantidad | Ejemplos |
| :--- | ---: | :--- |
| `IMPLEMENTADO` | 40 | Auth, clearance, auditoría, SSRF, rate limit, terreno, NATS, metrics, móvil, offline queue |
| `PARCIAL` | 46 | C2 intel, tactical, sensors, logistics, messaging, AAR, reports, prediction, map, voice, COA, frontend, Docker |
| `EXPERIMENTAL` | 5 | YOLO, anomalías, correlación, Maven, mesh |
| `STUB` | 8 | OSINT, Intel, Satellite, Agents, wearables, stego |
| `NO IMPLEMENTADO` | 5 | MFA producto, prompt injection, logs, trazas |
| `PLANNED` | 1 | CI/CD operativo |
| `MUERTO` | 0 | El código muerto (`media.py`, auth OSINT/Intel) se registra como NO MONTADO en las fichas |
| **Total** | **105** | |

> El conteo es sobre las 105 fichas `F-XX`, no sobre endpoints. Un endpoint puede ser `STUB` y su servicio `IMPLEMENTADO`; la ficha lo explicita.

### 20.2 Lectura correcta

- **Lo que funciona hoy:** autenticación básica, autorización por clearance en v1/v3, auditoría, SSRF, rate limit, C2 con DB, táctico heurístico, terreno, eventos, frontend COP, móvil (0 errores, 11 tests).
- **Lo que no funciona hoy:** MFA expuesto, OSINT/Intel/Satellite/Agents por HTTP, uploads.
- **Lo que no se ha probado:** Docker, PostgreSQL, Redis, NATS, Neo4j, LLM, proveedores externos, cobertura del backend completo al 80% (~73% agregado), accesibilidad. La cobertura de las 6 suites de seguridad es 88%, el build Next 16 está verificado y el móvil pasa 11 tests.

---

## 21. Prioridad de cierre

| Prioridad | Fichas | Acción |
| ---: | :--- | :--- |
| P0 | F-50..F-55, F-60 | Montar OSINT/Satellite o despublicarlos |
| P0 | F-06, F-07 | Montar MFA o retirar la promesa |
| P1 | F-90..F-94, F-76 | Persistir dominios en memoria |
| P1 | F-162, F-164 | Tests de integración de API y mesh en dispositivos |
| P1 | F-140..F-142 | Probar observabilidad en runtime y cerrar SEC-FIX-007/008 |
| P1 | F-170 | Validar Docker |
| P2 | F-110..F-116 | Definir alcance de ML/Maven |
| P2 | F-143, F-144 | Logs y trazas |
| P3 | F-150..F-155 | Tests UI y accesibilidad |

---

## 22. Conclusión

La matriz muestra un producto **asimétrico**: el núcleo de seguridad, el C2 y el móvil están construidos y verificados; la periferia (OSINT, satélite, agentes) sigue sin API real. La documentación anterior ocultaba esa asimetría al listar rutas sin estado.

Con esta matriz, cualquier decisión (demo, venta, auditoría, roadmap) puede tomarse sabiendo exactamente qué existe. Esa es la función de una matriz de funcionalidades: no lucir, sino permitir decidir.
