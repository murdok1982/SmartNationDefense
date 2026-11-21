# ADVERSARIAL SECURITY AUDIT REPORT (FACTORY)

- **Audit Status:** `FAIL (OPEN HIGH FINDINGS)` — re-auditoría adversarial FASE 3 sobre `HEAD 0f8f3cb` + working tree. **Aviso de concurrencia:** otro subagente trabajó en el mismo working tree durante la auditoría (añadió `tests/test_crypto_quantum.py`, `test_mfa_core.py`, `test_security_core.py`, `test_web_tools_core.py` a las 17:58-17:59 y creó el commit `0f8f3cb`); todos los hallazgos `OPEN` fueron **re-verificados contra el árbol final** y siguen vigentes. Quedan sin commitear mis fixes de 3 archivos + 1 test.
- **Auditor Agent:** `@redteam-auditor`
- **Target:** `0f8f3cb` + cambios de auditoría sin commitear (`backend/app/api/v3/router.py`, `backend/app/core/config.py`, `backend/app/services/vision/analyst.py`, `backend/tests/test_vision_ssrf.py`)
- **Metodología:** lectura adversarial del código real, introspección de la app FastAPI (172 rutas), ejecución de la suite, validación de producción, y consulta a la API **OSV.dev** (`/v1/querybatch`) para PyPI (34 pins de `requirements.txt`) y npm (469 paquetes de `package-lock.json`).
- **Summary Counts (FASE 3 — estado honesto):**
  - `CRITICAL`: **0 abiertos** (2 históricos `FIXED`: VULN-001, VULN-002)
  - `HIGH`: **7 totales** → `FIXED` 3 (VULN-003, 004, 005) / **`OPEN` 4** (VULN-006, 007, 008, 009)
  - `MEDIUM`: **15 totales** → `FIXED` 2 / `PARTIAL` 3 / **`OPEN` 10**
  - `LOW`: **7 totales** → `OPEN` 4 / `ACCEPTED-RISK` 3

> **EXIT GATE RULE:** El proyecto NO puede darse por finalizado mientras exista cualquier hallazgo `CRITICAL` o `HIGH` en estado `OPEN`. Quedan **4 HIGH abiertos** → veredicto `BLOCKED` y tareas `SEC-FIX-XXX` en `.factory/TASKS.md`.

---

## 1. ATTACK SURFACE & THREAT MODEL

**Rutas realmente registradas por `app.main:app`: 172** (introspección ejecutada, ver §4).

- **Puntos de entrada públicos (confirmados por introspección de dependencias):**
  - `POST /api/v1/auth/login`, `POST /api/v1/auth/register`, `POST /api/v1/auth/refresh`
  - `GET /api/v1/health`, `GET /`, `GET /metrics`, `GET /docs`, `GET /redoc`, `GET /openapi.json`
- **Puntos de entrada autenticados:** todo el resto (`/api/v1/c2/*`, `/api/v1/{messaging,terrain,logistics,aar,reports,fusion,prediction,map,voice,planning,satellite,osint,intel,agents,tactical}/*`, `/api/v2/*`, `/api/v3/*`).
- **Enforcement de clasificación:** **0 endpoints con autenticación y sin `require_clearance`** (script de introspección, §4). El control v1/v2/v3 es homogéneo: `Depends(require_clearance("RESTRICTED"|"CONFIDENTIAL"))` + `_AUTH_DEPS = [Depends(get_current_user)]` a nivel de router.
- **Autenticación:** JWT HS256 (`access` + `refresh`), `aud`/`iss` verificados, `type` verificado, `jti` con blacklist Redis. MFA TOTP (secreto AES-256-GCM en reposo) implementado en `app/api/osint/auth.py` — **router no montado** (ver VULN-022).
- **Activos sensibles:** `SECRET_KEY` (firma JWT + firma de uploads + fallback de tickets MFA), `MFA_ENCRYPTION_KEY`, `ADMIN_INITIAL_PASSWORD`, credenciales Postgres/Neo4j/Redis/NATS/Grafana, `fernet.key`, datos de clasificación hasta `TOP_SECRET`.
- **Fronteras de confianza:** Navegador (Next.js 3000) → Nginx (443/80) → FastAPI (8000) → Postgres/Redis/NATS/Neo4j/Ollama. Flutter → FastAPI. Backend → Internet (OSINT, visión, LLM).
- **Superficie de red (compose):** solo `nginx` publica en `0.0.0.0` (80/443); el resto de servicios están bindeados a `127.0.0.1` (correcto).

---

## 2. MANDATORY APPSEC VERIFICATION CHECKLIST

### 2.1 Injection & Input Validation
- [x] **SQLi — VERIFICADO LIMPIO.** Cero SQL crudo interpolado: `grep -rn 'execute(f"|text(f"|f"SELECT'` → 0 coincidencias; todo usa SQLAlchemy `select()/update()` con bind params. `sqlite3` de satélite usa solo `connect()`; sin queries construidas en `database.py`.
- [x] **Command Injection — VERIFICADO LIMPIO.** `eval/exec/os.system/subprocess/shell=True/pickle.loads/yaml.load` → **0 coincidencias** en `backend/app` y `frontend/src`.
- [x] **XSS — Sin `dangerouslySetInnerHTML` ni `eval` en frontend** (`grep` → 0). Riesgo residual por almacenamiento de tokens (§VULN-016).
- [x] **Path Traversal — VERIFICADO en endpoints implementados:** `yFiles` normalizados (`os.path.basename`, regex `[^A-Za-z0-9._-]`, `lstrip(".")`) + doble comprobación `os.path.commonpath([root, realpath])` en `app/api/osint/evidence.py:142-149`, `app/api/osint/reports.py:99-102`, `app/api/v1/media.py:86-95`, y `Path.resolve()` + `parents` en `app/services/osint/tools/document_tools.py:49-55`.
- [x] **NoSQL/Graph injection —** Neo4j se usa solo con drivers parametrizados; sin Cypher construido con input.
- [x] **Validación de entrada** — Pydantic v2 en todos los modelos de body; límites `ge/le/min_length/max_length` presentes en auth, evidence, media, sensores.

### 2.2 Authentication, Sessions & Access Control
- [x] **Passwords** — bcrypt vía passlib (`CryptContext(schemes=["bcrypt"])`). OK.
- [x] **JWT** — algoritmos **fijados a `["HS256"]`** (`app/core/security.py:137-143`), `aud`+`iss`+`type` verificados; `mfa_challenge` rechazado en `get_current_user`.
- [x] **Autorización/IDOR** — `require_clearance` en el 100 % de rutas no públicas; `assert_resource_access` en OSINT (owner + clasificación); filtro por `classification` en `/api/v1/intel`. **Sin IDOR detectado en rutas montadas.**
- [ ] **Brute-force / lockout de la ruta de login VIVA — FALLA.** El lockout (`_BruteForceProtector`) vive en `app/api/osint/auth.py`, que **no está montado**; `/api/v1/auth/login` no tiene lockout por cuenta. → **VULN-006 (HIGH, OPEN)**
- [ ] **Fail-open de controles con Redis caído — FALLA.** Rate limit, blacklist `jti` y tickets MFA fallan abiertos y el arranque continúa sin Redis. → **VULN-007 (HIGH, OPEN)**
- [ ] **Rate-limit por cliente real — FALLA detrás de Nginx.** `request.client.host` es la IP de Nginx (uvicorn `forwarded_allow_ips=127.0.0.1` por defecto; Nginx llega desde red Docker) → un único bucket global. → **VULN-008 (HIGH, OPEN)**
- [x] **MFA challenge isolation (unitario)** — `type` estricto, `alg` verificado tras decode, ticket de un solo uso con `jti` revocado (`test_mfa_security.py` 3 passed). **Riesgo residual:** fallback de secreto y replay si Redis cae (§VULN-014).
- [x] **Refresh rotation + revocación** — `refresh` valida `type`, blacklist `jti` y revoca el token usado.

### 2.3 Secrets, Configuration & HTTP Hardening
- [ ] **Secretos por defecto — CORREGIDO EN ESTA AUDITORÍA.** `SECRET_KEY` y `ADMIN_INITIAL_PASSWORD` publicados en `.env.example`, y `admin123` en `docker-compose.demo.yml` → eliminados/forzados a explícitos (§VULN-003).
- [x] **CORS** — orígenes explícitos desde `CORS_ORIGINS` (nunca `*`), `allow_credentials=True`, métodos y headers acotados. `grep allow_origins` → lista, no wildcard. **PASS.**
- [x] **Cabeceras en la API (Nginx)** — HSTS 2 años + preload, XFO DENY, XCTO nosniff, Referrer-Policy, CSP sin `unsafe-eval`, Permissions-Policy, X-Permitted-Cross-Domain-Policies. **PASS** en `location /`.
- [ ] **Cabeceras en el frontend — FALLA.** Nginx **no** tiene upstream al frontend (`location /` → `api:8000`); `next.config.mjs` no define `headers()` → el UI (3000) se sirve sin CSP/HSTS/XFO. → **VULN-016**
- [ ] **Cabeceras no heredadas** en `location = /healthz` y `location @rate_limit` (Nginx: un `add_header` en el bloque anula los del `server`). → **VULN-017**
- [x] **Mensajes de error** — `DEBUG=false`; handlers de auth devuelven mensajes genéricos. **Parcial:** 17 `detail=str(e)` en módulos de negocio (§VULN-021).
- [x] **Superficie de secretos en git** — `.env` y `fernet.key` están en `.gitignore` (`.gitignore:231-232`); `git ls-files` solo expone `.env.example` (plantilla). **No hay secretos reales commiteados.**

### 2.4 SSRF, File Handling & Dependencies
- [x] **SSRF OSINT (`web_tools`)** — allowlist de esquemas, denylist de redes (privadas, CGNAT, link-local, metadata, IPv6 ULA/link-local/v4-mapped), **IP pinning** con `socket.getaddrinfo` fijado, verificación de peer post-conexión y validación en cada salto de redirección. `test_ssrf.py` → **18 passed**.
- [x] **SSRF en visión/Maven — CORREGIDO EN ESTA AUDITORÍA.** `SatelliteAnalyst._download_image` y `/api/v3/vision/drone-frame` descargaban URLs arbitrarias con `follow_redirects=True` sin validación (§VULN-005).
- [x] **Uploads** — límite `max_file_size_bytes` (50 MB) + whitelist de nombre + contención de path en evidence/media. `media` **no está montado** (§VULN-020).
- [ ] **Dependencias** — OSV: **6 paquetes PyPI** y **15 paquetes npm** con advisories sobre los pins actuales; 2 CRITICAL (`torch`, `next`) sin parche en la rama fijada. → **VULN-009 (HIGH, OPEN)**

---

## 3. VULNERABILITY FINDINGS LOG

### [VULN-001] CRITICAL-01 — Almacenamiento en claro de secretos MFA/TOTP
- **Severity:** `CRITICAL` · **Categoría:** Storage at rest
- **Ubicación:** `backend/app/services/intel/auth/mfa.py` (cifrado), consumido por `backend/app/api/osint/auth.py:_encrypt_secret`
- **Estado:** `FIXED` (FASE 0)
- **Verificación ejecutada:** `pytest backend/tests/test_mfa_security.py -q` → `3 passed` (`test_mfa_secret_encryption_at_rest` compara cifrado≠plano y round-trip).
- **Nota honesta:** el módulo que lo usa (`osint/auth.py`) no está montado (§VULN-022), así que este control **hoy no protege ninguna ruta viva**; el cifrado es correcto pero la superficie real de MFA es inexistente.

### [VULN-002] CRITICAL-02 — Confusión de tipo de token MFA
- **Severity:** `CRITICAL` · **Categoría:** Token confusion
- **Ubicación:** `backend/app/core/security.py:53-104` (`create_mfa_challenge_token`, `decode_mfa_token`), `backend/app/core/security.py:178-190` (`get_current_user`)
- **Estado:** `FIXED`
- **Verificación ejecutada:** `pytest tests/test_mfa_security.py -q` → 3 passed, incluido `test_mfa_challenge_cannot_access_protected_routes` (`/api/v1/c2/` → 401 con ticket MFA).

### [VULN-003] HIGH-02 — Credenciales por defecto publicadas en el repositorio
- **Severity:** `HIGH` · **Categoría:** Secrets — Defaults
- **Ubicación (antes del fix):** `.env.example:8` (`SECRET_KEY=32b20a19…`), `.env.example:72` (`ADMIN_INITIAL_PASSWORD=SESIS_ADMIN_2026_Str0ng_P4ss!`), `docker-compose.yml:23` (mismo password), `docker-compose.demo.yml:39` (`admin123`), `backend/app/core/config.py:16` (`CHANGE_ME_IMMEDIATELY`)
- **Estado:** `FIXED` (en esta auditoría, SEC-FIX-003)
- **PoC (antes del fix):** cualquiera con acceso al repo forjaba JWT válidos (`HS256`, `aud=sesis-c2`, `iss=sesis-auth-server`) con `SECRET_KEY` pública → **suplantación total de cualquier `sub`/`clearance`**. El validador de producción **no** bloqueaba ese hex (no contiene `change`), así que un despliegue copiando `.env.example` arrancaba con la clave pública.
- **Remediación aplicada:**
  1. `.env.example`: `SECRET_KEY=CHANGE_ME_GENERATE_WITH_openssl_rand_hex_32` (rechazado en production) y `ADMIN_INITIAL_PASSWORD=CHANGE_ME_SET_A_UNIQUE_ADMIN_PASSWORD`.
  2. `docker-compose.yml` y `docker-compose.demo.yml`: `${ADMIN_INITIAL_PASSWORD:?...}` (sin default inseguro).
  3. `config.py`: se añade el hex histórico a la blocklist y se exige `ADMIN_INITIAL_PASSWORD` ≥10 caracteres, distinto de placeholders (sin `change`).
- **Prueba de verificación ejecutada:**
  - `grep -n admin123 docker-compose.yml docker-compose.demo.yml .env.example` → **exit 1 (0 coincidencias)**.
  - `ENVIRONMENT=production SECRET_KEY=CHANGE_ME_… ADMIN_INITIAL_PASSWORD=CHANGE_ME_… python -c "Settings()"` → **refuses to start** (`Insecure or default SECRET_KEY`, `Insecure or missing ADMIN_INITIAL_PASSWORD`).
  - `pytest tests -q` → **142 passed** (medido sobre el árbol final; ver §4 — 74 passed justo tras los fixes, antes de que otro subagente añadiera 4 archivos de test).

### [VULN-004] HIGH-03 — SSRF TOCTOU (DNS rebinding) en herramientas OSINT
- **Severity:** `HIGH` · **Categoría:** SSRF
- **Ubicación:** `backend/app/services/osint/tools/web_tools.py:109-235` (`_resolve_validated_ips`, `_PinnedDNS`, verificación de peer)
- **Estado:** `FIXED` (TASK-025)
- **Verificación ejecutada:** `pytest tests/test_ssrf.py -q` → **18 passed** (incluye rebinding, IPv6, v4-mapped, metadata, redirecciones).
- **Riesgo residual:** `_PinnedDNS` parchea `socket.getaddrinfo` **globalmente** durante la petición (§VULN-019).

### [VULN-005] HIGH-04 — Bypass de la protección SSRF en visión/Maven (`/api/v3/vision/*`)
- **Severity:** `HIGH` · **Categoría:** SSRF (control esquivado)
- **Ubicación (antes del fix):** `backend/app/services/vision/analyst.py:58-64` (`httpx.AsyncClient(follow_redirects=True).get(url)`), `backend/app/api/v3/router.py:36-46` (`analyze-satellite`), `:60-70` (`detect-changes`), `:99-105` (`drone-frame`)
- **Estado:** `FIXED` (en esta auditoría, SEC-FIX-002)
- **PoC (antes del fix):** con un JWT válido de cualquier operador activo:
  ```
  POST /api/v3/vision/analyze-satellite?image_url=http://169.254.169.254/latest/meta-data/iam/security-credentials/
  POST /api/v3/vision/drone-frame?frame_url=http://redis:6379/
  ```
  `follow_redirects=True` permitía además saltar a `http://127.0.0.1:8000/metrics` o a metadata cloud (respuesta reflejada/registrada en logs de error). El propio endpoint devolvía `detail=str(e)` (ahora corregido).
- **Remediación aplicada:** toda descarga pasa por `safe_http_get` (validación por salto + IP pinning + peer check), `follow_redirects=False`, límite duro de 25 MB, y mapeo `ValueError → 400` + `500` genérico sin `str(e)`.
- **Prueba de verificación ejecutada:**
  - `pytest tests/test_vision_ssrf.py -q` → **10 passed** (`169.254.169.254`, `metadata.google.internal`, `127.0.0.1`, `10.0.0.5`, `192.168.1.1`, `[::1]`, `localhost`, `file://`, `gopher://`, `[::ffff:169.254.169.254]`).
  - `python -m compileall app` → exit 0.

### [VULN-006] HIGH-01 — Brute-force: el lockout existe sólo en un router NO montado
- **Severity:** `HIGH` · **Categoría:** Authentication / Brute force
- **Ubicación:** `backend/app/api/osint/auth.py:121-204` (protector), `backend/app/api/auth.py:61-95` (login VIVO sin lockout), `backend/app/api/osint/router.py` (stub de 6 rutas: **no incluye `auth`**)
- **Estado:** `OPEN`
- **Evidencia de que el fix previo no aplica:** introspección de rutas → `app.routes` contiene `/api/v1/auth/{login,register,refresh,logout,me}` y **ninguna** ruta `/api/v1/osint/auth/mfa/verify`. `grep -rn "osint.auth" backend/app` sólo devuelve auto-referencias; `main.py:129` monta `app.api.osint.router` (stub).
- **PoC:** `for p in $(seq 1 1000); do curl -s -o /dev/null -w "%{http_code}\n" -X POST https://host/api/v1/auth/login -H 'Content-Type: application/json' -d "{\"username\":\"admin\",\"password\":\"pw$p\"}"; done` desde IPs rotativas → no hay bloqueo por cuenta; el único freno es el rate-limit por IP (que además falla abierto, VULN-007, y es global, VULN-008).
- **Remediación:** implementar el lockout por `(username, path)` en `/api/v1/auth/login` (reutilizar `_BruteForceProtector` y `get_limiter_key`), registrar auditoría de intentos fallidos y forzar MFA en roles `admin`.
- **Verificación requerida:** `pytest tests/test_brute_force.py` (nuevo) con N fallos → 429; `test_auth.py` sin regresión.

### [VULN-007] N-02 — Fail-open de controles de seguridad cuando Redis no está disponible
- **Severity:** `HIGH` · **Categoría:** Availability / Fail-open
- **Ubicación:** `backend/app/core/rate_limit.py:105-111` (excepción → `call_next`), `backend/app/core/security.py:166-176` (`is_jti_revoked` → `False`), `backend/app/main.py:24-50` (lifespan continúa sin Redis), `backend/app/core/events.py:_claim_idempotency` (fallback memoria)
- **Estado:** `OPEN`
- **PoC:** con Redis caído (`docker compose stop redis`) la API arranca, sirve login sin rate limiting, y **acepta tokens revocados** (`logout` no tiene efecto) → un token filtrado sigue siendo válido hasta `exp` (15 min) pese a la revocación.
- **Evidencia adicional (preocupante):** el commit `0f8f3cb` añade `tests/test_security_core.py::test_revoke_without_redis_fails_open`, que **fija como comportamiento esperado** el fail-open (`assert` de que sin Redis no se considera revocado). Es decir, el fallo está codificado en la suite: cerrarlo exige cambiar ese test, no solo el código.
- **Remediación:** modo `FAIL_CLOSED` configurable para `ENVIRONMENT=production`: si Redis no responde en el arranque → abortar; en `is_jti_revoked` → 503/401 (deny) si no se puede consultar; `CircuitBreaker` con estado explícito y métrica `security_fail_open_total`.
- **Verificación requerida:** test con cliente Redis que lanza excepción → `is_jti_revoked` deniega; test de arranque en production sin Redis → excepción.

### [VULN-008] HIGH-05 — Rate-limit global por IP de proxy (bucket único) → DoS trivial
- **Severity:** `HIGH` · **Categoría:** Rate limiting / DoS
- **Ubicación:** `backend/app/core/rate_limit.py:87-92` (`client_ip = request.client.host`), `docker-compose.yml` (command uvicorn sin `--forwarded-allow-ips`), `infra/nginx.conf:28-32` (pasa `X-Forwarded-For`)
- **Estado:** `OPEN`
- **Evidencia:** uvicorn 0.53 `proxy_headers=True` con `forwarded_allow_ips` por defecto `127.0.0.1`; Nginx llega desde la red Docker (p. ej. `172.18.0.x`) → `X-Forwarded-For` **no se confía** → `request.client.host` = IP de Nginx para *todos* los clientes. Con `DEFAULT_LIMITS["default"]=(100,60)` el bucket es **global para toda la plataforma** (y `login` = **5 req/min globales**).
- **PoC:** un atacante anónimo envía 101 req/min a cualquier endpoint → 429 para todos los operadores (DoS de plataforma). Inversamente, para el brute-force, la key no aísla al atacante.
- **Remediación:** `uvicorn ... --forwarded-allow-ips=<subred nginx>` + `ProxyHeadersMiddleware` verificado, o derivar la IP de `X-Real-IP` sólo si el peer es el proxy conocido; añadir límites por `sub` autenticado además de por IP; test que simule XFF.
- **Verificación requerida:** test con `X-Forwarded-For` distinto → keys distintas en Redis (`ZRANGE ratelimit:*`).

### [VULN-009] HIGH-06 — Dependencias con advisories HIGH/CRITICAL sin parche aplicado
- **Severity:** `HIGH` · **Categoría:** Supply chain (SCA)
- **Ubicación:** `backend/requirements.txt:11,12,15,25,37`; `frontend/package.json:16` / `frontend/package-lock.json` (next 14.2.35)
- **Estado:** `OPEN`
- **Método:** `pip-audit`/`npm audit` **no disponibles** en el entorno (`command not found`, exit 127). Sustituto ejecutado: `POST https://api.osv.dev/v1/querybatch` con los 34 pins PyPI y los 469 paquetes del lockfile → exit 0.
- **Hallazgos relevantes (OSV):**

  | Paquete | Pin | Advisory | Sev. | Fix | Explotabilidad real en este código |
  | :--- | :--- | :--- | :--- | :--- | :--- |
  | `torch` | 2.5.1 | GHSA-53q9-r3pm-6pq6 (CVE-2025-32434) / GHSA-63cw-57p8-fm3p | CRITICAL/HIGH | ≥2.6.0 / ≥2.10.0 | `torch.load` vía `YOLO("yolov8n.pt")` con pesos descargados de red sin hash pinning (`yolo_loader.py:48-56`) → RCE si se compromete el artefacto |
  | `next` | 14.2.35 | GHSA-2464, GHSA-2xp9, GHSA-p293, GHSA-89xv, GHSA-c4j6, GHSA-p9j2 (…26 advisories) | CRITICAL/HIGH | **sólo 15.5.x / 16.x** | Rama 14 EOL: no hay parche. RCE de Image Optimization no explotable (no se usa `next/image`); SSRF de rewrites no explotable (destino es env, no input) |
  | `python-multipart` | 0.0.18 | GHSA-5rvq, GHSA-pp6c (DoS headers multipart), GHSA-mj87 | HIGH | ≥0.0.30 | **Sí** en `/api/osint/evidence/upload` (si se monta) — requiere JWT válido; Nginx limita body a 100 MB |
  | `cryptography` | 44.0.0 | GHSA-537c / GHSA-jwv3 / GHSA-r6ph (OpenSSL wheels, path-building) | HIGH | ≥48.0.1 | No se usan PKCS#7/curvas SECT → no explotable; higiene obligatoria |
  | `lxml` | 5.3.0 | GHSA-vfmq-68hx-4jfw (XXE en `iterparse`) | HIGH | ≥6.1.0 | Sólo se usa como parser HTML de BeautifulSoup → XXE no alcanzable |
  | `python-jose` | 3.3.0 | GHSA-3qf3 / GHSA-6c5p (alg confusion), GHSA-cjwg (DoS JWE) | CRITICAL/MODERATE | ≥3.4.0 | `algorithms=["HS256"]` fijo y sin JWE → no explotable; debe actualizarse igualmente |
  | npm | — | 15 paquetes (brace-expansion, minimatch, js-yaml, nanoid, postcss, glob, next…) | HIGH/MOD | varios | Mayoría dev/transitivas de build |

- **Remediación:** (1) subir `python-jose>=3.4.0`, `python-multipart>=0.0.30`, `cryptography>=48.0.1`, `lxml>=6.1.0`, `torch>=2.6.0` (ideal ≥2.10) o eliminar torch/ultralytics del runtime de API; (2) plan de upgrade Next 15/16 con `next build` verificado; (3) pinear hash del modelo YOLO (`sha256`) antes de `torch.load`; (4) añadir `pip-audit`/`npm audit` a CI con `--audit-level=high`.
- **Verificación requerida:** `pip-audit -r backend/requirements.txt` → 0 HIGH/CRITICAL; `npm audit --audit-level=high` → 0; `pytest tests -q` verde.

### [VULN-010] MEDIUM-01 — Cadena de auditoría: persistencia best-effort, multi-proceso y callers en código no montado
- **Severity:** `MEDIUM` · **Categoría:** Auditoría / Integridad
- **Ubicación:** `backend/app/core/audit.py:41-101` (rehidratación por proceso, `except → logger.error` al persistir), `backend/app/api/osint/auth.py:321-352` (único caller con `db_session`)
- **Estado:** `PARTIAL` (el fix de TASK-027 existe y los tests pasan, pero **no hay ninguna ruta viva que lo invoque**)
- **Verificación ejecutada:** `pytest tests/test_audit_persistence.py tests/test_audit_unified.py -q` → **6 passed**. `grep -rn "_log_audit" backend/app/api` → sólo `osint/auth.py` (no montado).
- **Riesgo:** la cadena es tamper-evident en un proceso, pero con N workers/celery cada proceso mantiene su propio `last_hash` → cadenas ramificadas que rompen `verify_chain`; un fallo de DB se traga el evento (pérdida silenciosa de evidencia).
- **Remediación:** head único en DB con `SELECT … FOR UPDATE` (o tabla `audit_head`), `record()` transaccional estricto (sin swallow), y llamada obligatoria en `/api/v1/auth/login|refresh|logout` y mutaciones sensibles.
- **Verificación requerida:** test multi-proceso (dos `AuditChain` contra la misma DB) con cadena lineal; test que simule fallo de commit → excepción propagada.

### [VULN-011] MEDIUM-02 — Etiquetas criptográficas engañosas ("post-quantum")
- **Severity:** `MEDIUM` · **Categoría:** Crypto labeling
- **Ubicación:** `backend/app/core/crypto_quantum.py:26-38`
- **Estado:** `FIXED`
- **Verificación ejecutada:** `grep -n "fernet-aes128-cbc-hmac-sha256\|NOT post-quantum" backend/app/core/crypto_quantum.py` → label honesto en L38 y warning explícito en L27-29; `sign/verify` lanzan `QuantumCryptoUnavailable` en lugar de simular PQC.

### [VULN-012] N-04 — `settings.MULTI_TENANT` / `DEFAULT_TENANT_ID` ausentes (defecto latente)
- **Severity:** `MEDIUM` · **Categoría:** Latent defect
- **Ubicación:** `backend/app/core/config.py:53-54`, `backend/app/api/osint/deps.py:211-212`
- **Estado:** `FIXED`
- **Verificación:** `grep -n "MULTI_TENANT\|DEFAULT_TENANT_ID" backend/app/core/config.py backend/app/api/osint/deps.py` → definidos (default `False`/`"default"`) y consumidos con `getattr` seguro.

### [VULN-013] N-06 — Rate-limit path-aware: implementado pero desconectado
- **Severity:** `MEDIUM` · **Categoría:** Rate limiting
- **Ubicación:** `backend/app/core/rate_limit.py:132-146` (`get_limiter_key`), `backend/app/core/rate_limit.py:95-100` (middleware con `endswith("/auth/login")`), consumidores sólo en `backend/app/api/osint/auth.py:128,150,160,186` (no montado)
- **Estado:** `PARTIAL`
- **Observación:** el middleware clasifica correctamente `/api/v1/auth/login` (login=5/60) y también `/api/v1/osint/auth/login`, pero **no** `/mfa/verify` ni `/refresh`; y el lockout por `(usuario,path)` no se usa en rutas vivas.
- **Remediación:** aplicar `get_limiter_key` en el middleware/`/auth/login` y añadir límites específicos a `mfa/verify` y `refresh`.

### [VULN-014] MEDIUM-03 — Ticket MFA: fallback de secreto y replay si Redis falla
- **Severity:** `MEDIUM` · **Categoría:** Session / MFA
- **Ubicación:** `backend/app/core/security.py:74-78,86` (fallback `SECRET_KEY`), `backend/app/api/osint/auth.py:216-233` (`is_mfa_ticket_used`/`_mark_mfa_ticket_used` silencian excepciones), `docker-compose.yml`/`.env.example` (sin `MFA_CHALLENGE_SECRET`)
- **Estado:** `OPEN`
- **PoC:** con Redis caído, un ticket MFA capturado se reutiliza dentro del TTL (300 s) porque `is_mfa_ticket_used` devuelve `False` y el marcado falla en silencio. Además el ticket se firma con la misma clave que los access tokens (key reuse, §VULN-024).
- **Remediación:** `MFA_CHALLENGE_SECRET` obligatorio en production (validator), fail-closed si no hay almacén de un solo uso (o migrar a `jti` en DB con `UNIQUE`).

### [VULN-015] MEDIUM-04 — `/metrics` y documentación OpenAPI públicos a través de Nginx
- **Severity:** `MEDIUM` · **Categoría:** Information disclosure
- **Ubicación:** `backend/app/main.py:134-136` (`@app.get("/metrics")` sin auth), `backend/app/main.py:55-60` (`FastAPI(docs_url` por defecto)`, `backend/app/core/auth_middleware.py:PUBLIC_PATHS` (`/docs`, `/redoc`, `/openapi.json`), `infra/nginx.conf:26-27` (proxy de `/` → `:8000`)
- **Estado:** `OPEN`
- **PoC:** `curl -s https://host/metrics | head` → métricas Prometheus; `curl -s https://host/openapi.json | jq '.paths|keys|length'` → inventario completo de endpoints.
- **Remediación:** `docs_url=None, redoc_url=None, openapi_url=None` en production; `/metrics` con `Depends(verify_metrics_token)` o `deny all` en Nginx salvo red de scraping.

### [VULN-016] MEDIUM-05 — Frontend: tokens en `localStorage` y sin cabeceras de seguridad
- **Severity:** `MEDIUM` · **Categoría:** XSS/Session
- **Ubicación:** `frontend/src/lib/api.ts:8-35` (`localStorage.getItem/setItem("sesis_access_token")`), `frontend/next.config.mjs` (sin `headers()`), `frontend/Dockerfile` (`CMD ["npm","run","dev"]`)
- **Estado:** `OPEN`
- **Impacto:** cualquier XSS o dependencia comprometida exfiltra el refresh token (7 días) → persistencia. El UI no recibe CSP/HSTS/XFO porque Nginx no lo sirve.
- **Remediación:** mover tokens a cookies `HttpOnly; Secure; SameSite=Strict` (o BFF Next con cookie), añadir `headers()` con CSP/HSTS/XFO en `next.config.mjs`, y servir `next start` (build standalone) en lugar de `next dev`.

### [VULN-017] MEDIUM-06 — Hardening Nginx incompleto
- **Severity:** `MEDIUM` · **Categoría:** HTTP hardening
- **Ubicación:** `infra/nginx.conf:1` (zona `auth` 1r/s **nunca usada**), `:37-45` (`add_header` en `location` anula herencia), `:8` (`client_max_body_size 100M` global), ausencia de `server_tokens off`, `ssl_stapling`, `ssl_dhparam`
- **Estado:** `OPEN`
- **PoC:** `curl -sI https://host/healthz` y `curl -sI https://host/api/v1/auth/login` tras 429 → sin `Strict-Transport-Security`/`X-Frame-Options`; `curl -sI https://host/ | grep -i server` → versión de Nginx expuesta.
- **Remediación:** `limit_req zone=auth burst=3 nodelay;` en `location ~ ^/api/v1/(osint/)?auth/(login|refresh)`; repetir cabeceras en bloques con `add_header` local; `server_tokens off`; `ssl_stapling on`.

### [VULN-018] MEDIUM-07 — Redis y NATS sin autenticación en compose
- **Severity:** `MEDIUM` · **Categoría:** Infrastructure
- **Ubicación:** `docker-compose.yml:57-70` (`redis-server --appendonly yes`, sin `requirepass`), `:72-84` (`nats:2-alpine` `["-js"]` sin `--user/--pass`), `.env.example:31-36` declara `NATS_USER/PASSWORD` que **nadie aplica**
- **Estado:** `OPEN`
- **Impacto:** ambos bindeados a `127.0.0.1`, pero cualquier SSRF/otro contenedor comprometido accede sin credenciales; el rate limit y la blacklist JWT dependen de Redis (un `FLUSHALL` los anula).
- **Remediación:** `--requirepass ${REDIS_PASSWORD}` + `REDIS_URL` con password; `nats --user/--pass` y URL autenticada; fallar el arranque si faltan.

### [VULN-019] MEDIUM-08 — `_PinnedDNS` parchea `socket.getaddrinfo` globalmente
- **Severity:** `MEDIUM` · **Categoría:** Concurrency / Integrity
- **Ubicación:** `backend/app/services/osint/tools/web_tools.py:150-190`
- **Estado:** `OPEN`
- **Impacto:** durante la petición se sustituye la función global del proceso: dos peticiones concurrentes a hosts distintos pueden restaurar/anular el parche (condición de carrera), dejando una petición sin pinning o fallando resolución de servicios internos (DB/LLM). El control SSRF puede degradarse bajo carga.
- **Remediación:** usar transporte custom de httpx (`AsyncHTTPTransport` con `local_address`/resolución fija) o `httpx` con `transport` que resuelva a la IP validada + cabecera `Host`, sin monkeypatch global.

### [VULN-020] MEDIUM-09 — Upload presignado (`media.py`) latente: PUT sin auth y HMAC con `SECRET_KEY`
- **Severity:** `MEDIUM` · **Categoría:** File upload / AuthZ
- **Ubicación:** `backend/app/api/v1/media.py:22-28,58-110`; **router no montado** (`main.py` no incluye `media`)
- **Estado:** `OPEN` (riesgo latente)
- **Observación:** el path traversal está bien resuelto (realpath + commonpath + nombre saneado) y hay TTL; pero el PUT no exige autenticación (por diseño presignado), la firma no liga `content_type` ni el tamaño, y usa la misma `SECRET_KEY` que los JWT. Cualquiera con una URL firmada filtra da (dentro del TTL de 1 h) escribe archivos arbitrarios en `MEDIA_STORAGE_PATH`; no hay endpoint de descarga que fuerce `Content-Disposition`.
- **Remediación antes de montarlo:** clave HMAC dedicada (`MEDIA_SIGNING_KEY`), bind de `content_type`+`max_size` en la firma, validación de MIME por magic bytes y descarga con `Content-Disposition: attachment`/`X-Content-Type-Options`.

### [VULN-021] MEDIUM-10 — Filtración de mensajes internos vía `detail=str(e)`
- **Severity:** `MEDIUM` · **Categoría:** Error handling
- **Ubicación:** 17 ocurrencias en `backend/app/api/v1/{planning,aar,messaging}.py` y `backend/app/api/v3/router.py` (p. ej. `planning.py:69,81,93,105,117,136,147,158`; `aar.py:78,90,101,113`; `messaging.py:53,91,117`)
- **Estado:** `PARTIAL` (v3 corregido en esta auditoría; el resto sigue exponiendo `str(e)`)
- **PoC:** entradas inválidas en `/api/v1/planning/{opord_id}` devuelven el mensaje de la excepción interna (nombres de campos, estados, rutas).
- **Remediación:** mensajes de dominio + `request_id`; log del detalle en servidor.

### [VULN-022] MEDIUM-11 — Módulos OSINT/CASOS/EVIDENCIA no montados: controles auditados que no aplican
- **Severity:** `MEDIUM` · **Categoría:** Integrity / Coverage
- **Ubicación:** `backend/app/api/osint/router.py` (stub de 6 endpoints), `backend/app/main.py:128-129`
- **Estado:** `OPEN`
- **Evidencia:** introspección → rutas registradas `/api/v1/osint/{status,cases,entities,jobs,reports,health}` devuelven datos vacíos; **no existen** `/api/v1/osint/auth/*`, `/cases/{id}/evidence`, `/audit`, `/reports/{id}/download`. Por tanto: MFA, brute-force, cadena de auditoría persistente, custodia de evidencia y control de scopes **no protegen ninguna ruta real** hoy.
- **Impacto:** riesgo de falsa sensación de seguridad (los tests unitarios pasan porque prueban funciones, no rutas). Si se montan sin revisar, se activan VULN-006/010/014/020.
- **Remediación:** decidir explícitamente (montar con los fixes previos, o eliminar el código muerto); añadir un test que verifique que cada router declarado está montado.

### [VULN-023] MEDIUM-12 — Integridad de despliegue: bind mounts mutables y frontend en modo dev
- **Severity:** `MEDIUM` · **Categoría:** Deployment
- **Ubicación:** `docker-compose.yml` (`api`/`celery-worker`/`frontend` montan `./backend:/app`, `./frontend:/app`), `frontend/Dockerfile` (`npm install --legacy-peer-deps`, `CMD npm run dev`)
- **Estado:** `OPEN`
- **Impacto:** el código en ejecución es el del host (cualquier escritura en el host altera el runtime); `npm install` sin `npm ci` no respeta el lockfile → dependencias no reproducibles; `next dev` no es soportado en producción.
- **Remediación:** en producción usar imágenes inmutables sin bind mounts de código (solo volumen para `fernet.key`), `npm ci` + `next build` + `next start`.

### [VULN-024] MEDIUM-13 — Reutilización de `SECRET_KEY` para JWT, tickets MFA y firma de uploads
- **Severity:** `MEDIUM` · **Categoría:** Key management
- **Ubicación:** `backend/app/core/security.py:49,74,86,108` (JWT + fallback MFA), `backend/app/api/v1/media.py:26-28` (HMAC de uploads)
- **Estado:** `OPEN`
- **Impacto:** una filtración de `SECRET_KEY` compromete simultáneamente sesiones, tickets MFA y URLs de subida; sin `kid` ni rotación no hay migración sin invalidar todo.
- **Remediación:** claves separadas (`JWT_SIGNING_KEY`, `MFA_CHALLENGE_SECRET`, `MEDIA_SIGNING_KEY`), `kid` en el header y soporte de rotación (clave actual + anterior).

### [VULN-025] N-09 — `X-XSS-Protection` (cabecera obsoleta)
- **Severity:** `LOW` · **Categoría:** Compliance/HTTP
- **Ubicación:** `infra/nginx.conf` (no se envía; correcto según MDN)
- **Estado:** `ACCEPTED-RISK` — **no** enviar la cabecera es la práctica recomendada; CSP la sustituye.

### [VULN-026] LOW-01 — `/` revela entorno y modelo LLM
- **Severity:** `LOW` · **Categoría:** Information disclosure
- **Ubicación:** `backend/app/main.py:200-210` (`environment`, `llm`)
- **Estado:** `OPEN` · **Remediación:** devolver solo `{"status":"ok","service":...}` en production.

### [VULN-027] LOW-02 — Enumeración de usuarios por timing en login
- **Severity:** `LOW` · **Categoría:** Auth
- **Ubicación:** `backend/app/api/auth.py:67-73` (`if not user or not verify_password(...)` cortocircuita sin comparación dummy de bcrypt)
- **Estado:** `OPEN` · **Remediación:** ejecutar `verify_password` contra un hash dummy cuando el usuario no existe.

### [VULN-028] LOW-03 — `fernet.key` presente en el árbol de trabajo
- **Severity:** `LOW` · **Categoría:** Secrets handling
- **Ubicación:** `./fernet.key` (44 bytes), `.gitignore:231`
- **Estado:** `ACCEPTED-RISK` — ignorado por git (`git ls-files` no lo incluye) y montado `:ro`; requiere que cada despliegue genere su propia clave (`scripts/generate_keys.py`) y permisos `600`.

### [VULN-029] LOW-04 — `TrustedHostMiddleware` con host fijo
- **Severity:** `LOW` · **Categoría:** Configuration
- **Ubicación:** `backend/app/main.py:68-69` (`allowed_hosts=["api.sesis.local"]` sólo en production)
- **Estado:** `OPEN` · **Remediación:** `ALLOWED_HOSTS` por entorno; documentar (hoy un despliegue con otro dominio devuelve 400).

### [VULN-030] LOW-05 — Registro público sin anti-abuso
- **Severity:** `LOW` · **Categoría:** Abuse
- **Ubicación:** `backend/app/api/auth.py:86-120` (crea usuario `is_active=False`)
- **Estado:** `OPEN` · **Remediación:** rate limit específico + verificación de email/captcha; hoy sólo infla la tabla de usuarios inactivos (no concede acceso).

### [VULN-031] LOW-06 — Advisories no explotables con el uso actual (lxml/python-jose/cryptography)
- **Severity:** `LOW` · **Categoría:** Supply chain (residual)
- **Ubicación:** ver VULN-009 (tabla)
- **Estado:** `ACCEPTED-RISK` **temporal** — justificación: `lxml` sólo parsea HTML (no `iterparse`), `python-jose` fija `HS256` y no procesa JWE, `cryptography` no usa PKCS#7/SECT. **No exime** de la actualización (VULN-009 sigue `OPEN`).

---

## 4. AUTOMATED SECURITY TOOLING LOG

| # | Tool / Command | Scope | Exit Code | Resultado real |
| :--- | :--- | :--- | :--- | :--- |
| 1 | `cd backend && SECRET_KEY="test-secret-key-32-chars-minimum!!!" python3 -m pytest tests -q` | Suite completa (árbol final) | **0** | `142 passed, 1001 warnings in 13.97s` (incluye 4 archivos de test añadidos por trabajo concurrente) |
| 2 | Igual, inmediatamente después de mis fixes (antes del commit concurrente) | Suite post-fix | **0** | `74 passed, 522 warnings in 9.20s` |
| 3 | Igual, retirando `tests/test_vision_ssrf.py` (baseline en ese momento) | Suite pre-fix | **0** | `64 passed` — **el dato "49 passed" del contexto de la tarea corresponde al commit `9581712`; no es reproducible en el árbol actual** |
| 4 | `pytest tests/test_ssrf.py -q` | SSRF OSINT | **0** | `18 passed` (el contexto decía 12) |
| 5 | `pytest tests/test_audit_persistence.py tests/test_audit_unified.py -q` | Audit chain | **0** | `3 + 3 passed` |
| 6 | `pytest tests/test_mfa_security.py tests/test_rate_limit.py tests/test_events_dlq.py -q` | MFA/rate/DLQ | **0** | `3 + 6 + 3 passed` |
| 7 | `python3 -m compileall -q app` | Sintaxis backend | **0** | OK tras los fixes |
| 8 | `SECRET_KEY=… python3 ../scripts/validate_all.py` | Validador de proyecto | **0** | `Overall Status: VALIDATED` (`142 passed`, 4 invariantes PASS) |
| 9 | Introspección `app.routes` + walk de `route.dependant` | Cobertura authz | **0** | 172 rutas; **0** endpoints autenticados sin `require_clearance`; 6 públicos |
| 10 | `grep -rn "eval(\|exec(\|os.system\|shell=True\|pickle.loads\|yaml.load(" backend/app frontend/src` | RCE/Injection | **1** | 0 coincidencias (limpio) |
| 11 | `grep -rn 'execute(f"\|text(f"\|f"SELECT' backend/app` | SQLi | **1** | 0 coincidencias (limpio) |
| 12 | `grep -n admin123 docker-compose.yml docker-compose.demo.yml .env.example` | Credenciales default | **1** | 0 coincidencias (post-fix) |
| 13 | `ENVIRONMENT=production … python -c "Settings()"` con placeholders | Hardening prod | **1** (esperado) | `Refusing to start`: SECRET_KEY/ADMIN_INITIAL_PASSWORD inseguros |
| 14 | `python -c "SatelliteAnalyst()._download_image(<url interna>)"` | SSRF v3 | **0** | 4/4 URLs bloqueadas (`169.254.169.254`, `127.0.0.1`, `10.0.0.5`, `[::1]`) |
| 15 | `pytest tests/test_vision_ssrf.py -q` (nuevo) | Regresión SSRF visión | **0** | `10 passed` |
| 16 | `curl -sS https://api.osv.dev/v1/querybatch` (34 pins PyPI) | SCA Python | **0** | 6 paquetes con advisories (ver VULN-009) |
| 17 | `curl -sS https://api.osv.dev/v1/querybatch` (469 pkgs npm del lockfile) | SCA Node | **0** | 15 paquetes con advisories |
| 18 | `npm audit --audit-level=high` | SCA Node (oficial) | **127** | **No ejecutable:** `npm` no instalado en el entorno |
| 19 | `pip-audit -r backend/requirements.txt` | SCA Python (oficial) | **127** | **No ejecutable:** `pip-audit` no instalado |
| 20 | `docker compose config` | Compose válido | **127** | **No ejecutable:** `docker` no disponible |
| 21 | `bandit` / `semgrep` / `trivy` | SAST | **127** | No instalados → sustituido por revisión manual + greps dirigidos |
| 22 | `git diff -U0 backend/tests/ \| grep '^-[^-]'` | Integridad de tests | **1** | **0 líneas eliminadas en tests** por esta auditoría (no se han debilitado tests) |
| 23 | `git ls-files \| grep -Ei '\.env|fernet|\.key|\.pem'` | Secretos commiteados | **0** | Solo `.env.example` y `frontend/.env.local.example` (plantillas) |

> **Limitaciones declaradas:** sin `docker`, `npm`, `npm audit`, `pip-audit`, `bandit`, `semgrep` ni `trivy` en el entorno; el SCA se hizo contra OSV (fuente oficial de advisories) con los pins exactos. No se ejecutó la app en contenedores, por lo que los PoC de red (VULN-007/008/015/017) son derivados por inspección + configuración por defecto de uvicorn/Nginx, no por explotación en vivo.

---

## 5. FINAL RELEASE SIGN-OFF

- **All `CRITICAL` findings resolved & verified:** `YES` — 0 abiertos (VULN-001/002 `FIXED`; verificación unitaria reproducida).
- **All `HIGH` findings resolved & verified:** **`NO`** — 3 `FIXED` (VULN-003, VULN-004, VULN-005) y **4 `OPEN`**: VULN-006 (brute-force login vivo), VULN-007 (fail-open Redis), VULN-008 (rate-limit global tras proxy), VULN-009 (dependencias HIGH/CRITICAL).
- **Open MEDIUM:** 10 `OPEN` + 3 `PARTIAL` (VULN-010, 013, 021) → total 13 pendientes de MEDIUM.
- **Ready for Production Delivery:** **`BLOCKED`** — exit gate descalificado por 4 hallazgos `HIGH` abiertos; ver `SEC-FIX-001`, `SEC-FIX-004`, `SEC-FIX-005`, `SEC-FIX-006` en `.factory/TASKS.md`.

**Cambios de código aplicados por el auditor (solo fixes HIGH, sin tocar tests existentes):**

| Fix | Archivos | Verificación |
| :--- | :--- | :--- |
| SEC-FIX-002 (SSRF visión) | `backend/app/services/vision/analyst.py`, `backend/app/api/v3/router.py`, `backend/tests/test_vision_ssrf.py` (nuevo) | `pytest tests/test_vision_ssrf.py` → 10 passed; `pytest tests` → 142 passed |
| SEC-FIX-003 (credenciales) | `.env.example`, `docker-compose.yml`, `docker-compose.demo.yml`, `backend/app/core/config.py` | `grep admin123` → 0; `Settings()` en production → rechaza; `pytest tests` → 142 passed |

---

## 6. FUTURE SECURITY ROADMAP (Staged by FASE)

| FASE | Título | TAREA/ID(s) |
|---|---|---|
| FASE 3 (cierre) | Remediar los 4 HIGH abiertos | `SEC-FIX-001` (fail-open), `SEC-FIX-002` ✅, `SEC-FIX-003` ✅, `SEC-FIX-004` (rate-limit proxy), `SEC-FIX-005` (lockout vivo), `SEC-FIX-006` (dependencias) |
| FASE 3 | MEDIUM de hardening | VULN-015 (`/metrics`), VULN-016 (tokens/headers frontend), VULN-017 (Nginx), VULN-018 (Redis/NATS auth), VULN-024 (separación de claves) |
| FASE 3 | Integridad de auditoría | VULN-010 (head único en DB), VULN-022 (decidir montaje de OSINT), VULN-020 (media antes de montar) |
| FASE 5 | Testing de seguridad | suites: brute-force vivo, fail-closed Redis, SSRF visión (✅ añadida), XFF/rate-limit, headers Nginx, multi-worker audit chain |
| FASE 5 | SCA en CI | `pip-audit` + `npm audit --audit-level=high` bloqueantes; renovar `requirements.txt` y Next 15/16 |
| FASE 6 | Observabilidad de seguridad | alertas `security_fail_open_total`, `auth_failure_total`, `ssrf_block_total` |

**Registro de pendientes:** FASE 3: `SEC-FIX-001`, `SEC-FIX-004`, `SEC-FIX-005`, `SEC-FIX-006` + MEDIUM anteriores. FASE 5: suites de regresión y SCA bloqueante.

**Plan de descalificación del `BLOCKED`:** cerrar VULN-006/007/008/009 con evidencia ejecutable (tests nuevos + `pip-audit`/`npm audit` sin HIGH) y re-ejecutar este informe. Solo entonces `Ready for Production Delivery: APPROVED`.
