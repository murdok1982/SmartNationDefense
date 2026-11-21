# ADVERSARIAL SECURITY AUDIT REPORT (FACTORY)

- **Audit Status:** `PASS (0 CRITICAL / 0 HIGH abiertos)` — **re-auditoría de cierre** de los 4 HIGH (VULN-006/007/008/009) sobre `HEAD dc40049` + fixes de esta sesión.
- **Auditor Agent:** `@redteam-auditor`
- **Target:** `dc40049` + cambios de auditoría sin commitear: `backend/app/core/rate_limit.py`, `backend/app/core/auth_middleware.py`, `backend/app/api/auth.py`, `backend/app/api/osint/auth.py`, `backend/app/main.py`, `backend/tests/test_rate_limit_identity.py` (nuevo).
- **Metodología:** lectura adversarial + **búsqueda activa de bypasses** de los propios fixes (Host poisoning, spoofing de IP, variantes de username, cabeceras controladas por el cliente, agujeros de fail-closed), introspección de la app (180 rutas), ejecución de la suite (169 passed), SCA real (`npm audit`, `pip-audit`, OSV), y prueba empírica del borde Nginx (nginx 1.30.4 local).
- **Summary Counts (estado honesto al cierre):**
  - `CRITICAL`: **0 abiertos** (2 históricos `FIXED`: VULN-001, VULN-002)
  - `HIGH`: **8 totales** → **`FIXED` 8 / `OPEN` 0** (incluye VULN-032, bypass HIGH encontrado y corregido en esta sesión)
  - `MEDIUM`: **23 totales** → `FIXED` 5 / `PARTIAL` 2 / `ACCEPTED-RISK` 2 / **`OPEN` 14**
  - `LOW`: **7 totales** → `OPEN` 4 / `ACCEPTED-RISK` 3

> **EXIT GATE RULE:** El proyecto NO puede darse por finalizado mientras exista cualquier hallazgo `CRITICAL` o `HIGH` en estado `OPEN`. **Hoy: 0 abiertos → `APPROVED`**, con 14 MEDIUM + 4 LOW abiertos documentados (§5) y dos bypasses nuevos (`VULN-032` HIGH, `VULN-033` MEDIUM) corregidos con test de regresión.

---

## 1. ATTACK SURFACE & THREAT MODEL

**Rutas realmente registradas por `app.main:app`: 180 `APIRoute`** (introspección ejecutada, ver §4).

- **Puntos de entrada públicos (confirmados por introspección de dependencias):**
  - `POST /api/v1/auth/login`, `POST /api/v1/auth/register`, `POST /api/v1/auth/refresh`
  - `GET /api/v1/health`, `GET /`, `GET /metrics` (token **opcional**: público si `METRICS_TOKEN` está vacío), `GET /docs`, `GET /redoc`, `GET /openapi.json`
  - `GET /metrics`, `/docs`, `/redoc`, `/openapi.json` no pasan por `AuthMiddleware.PUBLIC_PATHS` salvo docs/openapi; `/metrics` se autentica sólo si hay token configurado.
- **Puntos de entrada autenticados:** todo el resto (`/api/v1/c2/*`, `/api/v1/{messaging,terrain,logistics,aar,reports,fusion,prediction,map,voice,planning,satellite,osint,intel,agents,tactical}/*`, `/api/v2/*`, `/api/v3/*`).
- **Enforcement de clasificación:** **2 endpoints con autenticación y sin `require_clearance`** (`/api/v1/auth/logout`, `/api/v1/auth/me`: self-service, sin datos clasificados) y **0** que expongan datos de módulo sin clearance (script de introspección, §4). El control v1/v2/v3 es homogéneo: `Depends(require_clearance("RESTRICTED"|"CONFIDENTIAL"))` + `_AUTH_DEPS = [Depends(get_current_user)]` a nivel de router.
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
- [x] **Brute-force / lockout de la ruta de login VIVA — CORREGIDO Y RE-VERIFICADO.** `/api/v1/auth/login` usa `BruteForceProtector` (Redis, path-aware): 429 + `Retry-After: 60`, `record_failure`/`record_success` y auditoría persistente (`test_login_lockout.py` → 2 passed). Bypasses probados: variantes de mayúsculas/espacios (lookup SQL case-sensitive → no autentican), Host poisoning (corregido, §VULN-033) y buckets por `X-API-Key` (bypass real encontrado → §VULN-032). Residual: DoS por bloqueo de cuenta (§VULN-036). → **VULN-006 (HIGH, FIXED)**
- [x] **Fail-open de controles con Redis caído — CORREGIDO.** `SECURITY_FAIL_MODE` (derivado dev=open / staging+prod=closed), rate-limit 503 + `Retry-After: 30`, `is_jti_revoked` 503, `lifespan` aborta el arranque y el lockout deniega (`test_rate_limit_hardening.py` 7 passed, `test_security_core.py` 34 passed). Se encontró y corrigió un `NameError` en la rama closed del lockout (§VULN-034). Residuales: `revoke_jti` write fail-open (§VULN-037), NATS in-memory (LOW). → **VULN-007 (HIGH, FIXED)**
- [x] **Rate-limit por cliente real — CORREGIDO.** `resolve_client_ip()` sólo acepta `X-Real-IP`/`X-Forwarded-For` si el peer está en `TRUSTED_PROXIES` (IP inválida → peer) y añade bucket `{limit}:sub:{sub}` por identidad JWT (`test_rate_limit_hardening.py` → 4 tests de spoofing). Nginx sobrescribe `X-Real-IP` (medido, §4). Residual: cualquier peer RFC1918 es “confiable” (§VULN-038). → **VULN-008 (HIGH, FIXED)**
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
- [x] **Dependencias — CORREGIDO.** `torch`/`ultralytics` fuera del runtime base (`requirements-vision.txt`, `torch>=2.6.0`), `python-multipart 0.0.34`, `python-jose 3.5.0`, `cryptography 50.0.2`, `lxml 6.1.3`, `passlib 1.7.4`, Next 16.4.6/React 19.3.1. `npm audit --omit=dev --audit-level=high` → **found 0 vulnerabilities** (exit 0). OSV sobre los 32 pins directos → sólo `python-jose` (sin fix upstream) y `pytest` (dev), ambos en la allowlist. Residual starlette 0.41.3 (§VULN-039). → **VULN-009 (HIGH, FIXED)**

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

### [VULN-006] HIGH-01 — Brute-force en el login real (SEC-FIX-005)
- **Severity:** `HIGH` · **Categoría:** Authentication / Brute force
- **Ubicación del fix:** `backend/app/api/auth.py:60-120` (login), `backend/app/api/osint/auth.py:121-210` (`BruteForceProtector` + `get_limiter_key`), `backend/app/core/rate_limit.py`
- **Estado:** **`FIXED`** (re-verificado en esta sesión)
- **Remediación implementada:** `/api/v1/auth/login` consulta `BruteForceProtector.is_locked(username, path)` antes de verificar la contraseña (429 + `Retry-After: 60`, 5 intentos / 300 s), registra `record_failure`/`record_success` en Redis **path-aware** y persiste cada intento fallido en la cadena de auditoría (`_log_audit(..., db_session=db)`), con métrica `auth_failure`.
- **Bypasses probados por el auditor:**
  - **Mayúsculas/espacios en el username:** `SELECT username='admin'` frente a `'Admin'`, `'ADMIN'`, `'admin '`, `' admin'` → **sin match** (probado en SQL: sólo `'admin'` coincide) ⇒ una variante no autentica, así que no evita el lockout para adivinar la contraseña. *(Hallazgo colateral MEDIUM: `Admin` puede registrarse como cuenta distinta → §VULN-040.)*
  - **Host poisoning del path (CVE-2026-48710):** en starlette 0.41.3 el path se reconstruye como `{scheme}://{Host}{path}`; con `Host: x` el key de lockout cambiaba por variante. **Corregido** usando `scope["path"]` (§VULN-033) y, además, **no alcanzable por el borde**: nginx 1.30.4 responde **400** a `Host: api.sesis.local/x` (medido, §4) y `%2F` viaja literal sin cambiar el path.
  - **Bucket por `X-API-Key`:** el bypass real encontrado (§VULN-032) permitía saltarse el límite por IP; corregido (el bucket ya no depende de cabeceras del cliente).
- **Evidencia ejecutada:** `pytest tests/test_login_lockout.py -q` → **2 passed** (429 tras 5 fallos + `AuditLog` persistido); `pytest tests/test_rate_limit_identity.py -q` → **8 passed**; `pytest tests -q` → **169 passed**.
- **Residual (documentado, no HIGH):** el lockout por cuenta permite DoS de la cuenta víctima (§VULN-036); MFA sigue sin aplicarse en el login (§VULN-035).

### [VULN-007] N-02 — Fail-open de controles de seguridad cuando Redis no está disponible (SEC-FIX-001)
- **Severity:** `HIGH` · **Categoría:** Availability / Fail-open
- **Ubicación del fix:** `backend/app/core/config.py:60-70` (`SECURITY_FAIL_MODE` + `security_fail_closed` derivado), `backend/app/core/rate_limit.py:130-175` (`_unavailable` → 503 + `Retry-After: 30` + `sesis_security_fail_open_total{component}`), `backend/app/core/security.py:166-184` (`is_jti_revoked` → 503), `backend/app/main.py:37-60` (aborta arranque), `backend/app/api/osint/auth.py:145-152` (lockout deniega)
- **Estado:** **`FIXED`** (re-verificado en esta sesión)
- **PoC original (ya no aplica):** con `docker compose stop redis` la API arrancaba, servía login sin rate limiting y aceptaba tokens revocados. Hoy: en staging/production el arranque **falla**; si Redis cae en caliente, rate-limit y revocación devuelven **503** (deny).
- **Verificación ejecutada:**
  - `pytest tests/test_rate_limit_hardening.py -q` → **7 passed** (closed → 503 sin llamar a `call_next`, `Retry-After: 30`; open → 200).
  - `pytest tests/test_security_core.py -q` → **34 passed** (`test_revoke_without_redis_fails_open_in_dev`, `..._fails_closed_in_production` con 503; el test que codificaba el fail-open fue sustituido por dos).
  - `pytest tests/test_rate_limit_identity.py -q` → **8 passed** (incluye lockout closed/deny y open/allow con Redis caído).
  - Sonda directa `BruteForceProtector.is_locked` con Redis caído: dev/open → `False`; prod/closed → `True` tras corregir §VULN-034.
- **Residuales documentados:** `revoke_jti` (escritura) sigue fail-open → el `logout` puede ser un no-op silencioso (§VULN-037, MEDIUM); idempotencia NATS cae a memoria (§VULN-007-LOW incluido en §3 LOW); y el modo por defecto del compose es `development` → fail-closed **apagado** salvo configuración explícita (§VULN-040).

### [VULN-008] HIGH-05 — Rate-limit global por IP de proxy (bucket único) → DoS trivial (SEC-FIX-004)
- **Severity:** `HIGH` · **Categoría:** Rate limiting / DoS
- **Ubicación del fix:** `backend/app/core/rate_limit.py:36-63` (`resolve_client_ip`, `TRUSTED_PROXIES`), `:150-200` (bucket `sub`), `backend/app/core/config.py:63-66`
- **Estado:** **`FIXED`** (re-verificado en esta sesión)
- **Remediación implementada:** `resolve_client_ip()` usa `X-Real-IP`/primer `X-Forwarded-For` **sólo si el peer pertenece a `TRUSTED_PROXIES`** (default `127.0.0.1,::1,10/8,172.16/12,192.168/16`), valida la IP (inválida → peer) y añade un bucket independiente `{limit}:sub:{sub}` para identidades JWT verificadas.
- **Bypasses probados por el auditor:**
  - Peer no confiable (`198.51.100.7`) con `X-Real-IP: 1.2.3.4` → se usa el peer (test).
  - `X-Real-IP` inválido → fallback al peer (test).
  - **`X-API-Key` aleatorio por petición:** *bypass real* — el bucket incluía `sha256(X-API-Key)`; 3 peticiones con 3 valores distintos generaron **3 buckets distintos** (medido). Corregido en §VULN-032.
  - Borde Nginx: `proxy_set_header X-Real-IP $remote_addr` **sobrescribe** la cabecera del cliente (verificado en la config y en la prueba local con nginx 1.30.4, §4).
- **Evidencia ejecutada:** `pytest tests/test_rate_limit_hardening.py -q` → **7 passed** (4 de spoofing/resolución + 3 de fail-mode); `pytest tests/test_rate_limit_identity.py -q` → **8 passed** (incluye “random api-key ⇒ un solo bucket”).
- **Residual:** `TRUSTED_PROXIES` por defecto incluye **todo RFC1918**: cualquier contenedor de la red Docker puede falsificar `X-Real-IP` (§VULN-038, MEDIUM/ACCEPTED).

### [VULN-009] HIGH-06 — Dependencias con advisories HIGH/CRITICAL sin parche aplicado (SEC-FIX-006)
- **Severity:** `HIGH` · **Categoría:** Supply chain (SCA)
- **Ubicación del fix:** `backend/requirements.txt`, `backend/requirements-vision.txt` (nuevo), `backend/app/services/vision/yolo_loader.py:55-105`, `frontend/package.json` / `frontend/package-lock.json`, `.github/workflows/ci.yml:54-74`, `docs/security/SCA_ALLOWLIST.md`
- **Estado:** **`FIXED`** (re-verificado en esta sesión)
- **Cambios verificados:** `torch`/`ultralytics` **fuera del runtime base** (`requirements-vision.txt` con `torch>=2.6.0`); `python-multipart 0.0.34` (OSV: sin advisories), `python-jose 3.5.0`, `cryptography 50.0.2`, `lxml 6.1.3`, `passlib 1.7.4`; `YOLOLoader._verify_integrity` exige `YOLO_MODEL_SHA256` y prohíbe descarga automática en production; Next **16.4.6** / React 19.3.1.
- **Evidencia ejecutada:**
  - `npm audit --omit=dev --audit-level=high` → **exit 0**, `found 0 vulnerabilities`.
  - Los 9 pins nuevos existen en PyPI (consulta a `pypi.org/pypi/<pkg>/json`: `python-multipart 0.0.34`, `python-jose 3.5.0`, `passlib 1.7.4`, `cryptography 50.0.2`, `lxml 6.1.3`… → `latest` coincide) — corrige el riesgo de CI roto por versión inexistente.
  - OSV sobre los **32 pins directos** → sólo `python-jose 3.5.0` (PYSEC-2026-4298, **sin fix upstream**, mitigado por `algorithms=["HS256"]`) y `pytest 8.3.4` (dev). Ambos en `docs/security/SCA_ALLOWLIST.md` y en los `--ignore-vuln` de CI.
  - `pytest tests/test_vision_yolo_integrity.py -q` → **5 passed** (hash correcto, hash alterado, production sin hash, dev sin hash, descarga deshabilitada).
- **Gate SCA ejecutado de verdad:** `python -m pip_audit -r backend/requirements.txt` con los 10 `--ignore-vuln` de CI → **exit 0**, `No known vulnerabilities found, 19 ignored` (~18 min; un primer intento con `timeout 400` abortó con **124**, por eso también se usó OSV por pin como verificación independiente).
- **Residual:** `starlette 0.41.3` (transitiva de `fastapi 0.115.6`) mantiene 7 advisories PYSEC/GHSA aceptados con justificación (§VULN-039, MEDIUM/ACCEPTED-RISK), incluido un DoS HIGH por `Range` en `FileResponse` cuyo único consumidor está en módulos **no montados**.

### [VULN-010] MEDIUM-01 — Cadena de auditoría: persistencia best-effort, multi-proceso y callers en código no montado
- **Severity:** `MEDIUM` · **Categoría:** Auditoría / Integridad
- **Ubicación:** `backend/app/core/audit.py:41-101` (rehidratación por proceso, `except → logger.error` al persistir), `backend/app/api/osint/auth.py:321-352` (helper), ahora invocado por la ruta viva `backend/app/api/auth.py:96-110`
- **Estado:** `PARTIAL` (mejora real: el login fallido **ya persiste** en `audit_log`; sigue sin head único multi-proceso)
- **Verificación ejecutada:** `pytest tests/test_login_lockout.py -q` → 2 passed (`test_failed_login_records_attempt_and_audit` verifica filas `AuditLog` con `action=LOGIN`, `success=False`); `pytest tests/test_audit_persistence.py tests/test_audit_unified.py -q` → 6 passed.
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

### [VULN-013] N-06 — Rate-limit path-aware: implementado y ahora conectado
- **Severity:** `MEDIUM` · **Categoría:** Rate limiting
- **Ubicación:** `backend/app/core/rate_limit.py:132-146` (`get_limiter_key`) y `:149-170` (clasificación `endswith("/auth/login")`), consumidor vivo en `backend/app/api/auth.py:74-90`
- **Estado:** **`FIXED`**
- **Observación:** el lockout por `(usuario, path)` ya se usa en la ruta viva de login (path derivado de `scope["path"]`); el middleware mantiene el bucket `login` = 5/60 y añade el bucket por `sub`. Residual: `mfa/verify` no existe montado y `refresh` cae en el bucket `default` (adecuado, pero conviene un límite propio).

### [VULN-014] MEDIUM-03 — Ticket MFA: fallback de secreto y replay si Redis falla
- **Severity:** `MEDIUM` · **Categoría:** Session / MFA
- **Ubicación:** `backend/app/core/security.py:74-78,86` (fallback `SECRET_KEY`), `backend/app/api/osint/auth.py:216-233` (`is_mfa_ticket_used`/`_mark_mfa_ticket_used` silencian excepciones), `docker-compose.yml`/`.env.example` (sin `MFA_CHALLENGE_SECRET`)
- **Estado:** `OPEN`
- **PoC:** con Redis caído, un ticket MFA capturado se reutiliza dentro del TTL (300 s) porque `is_mfa_ticket_used` devuelve `False` y el marcado falla en silencio. Además el ticket se firma con la misma clave que los access tokens (key reuse, §VULN-024).
- **Remediación:** `MFA_CHALLENGE_SECRET` obligatorio en production (validator), fail-closed si no hay almacén de un solo uso (o migrar a `jti` en DB con `UNIQUE`).

### [VULN-015] MEDIUM-04 — `/metrics` y documentación OpenAPI públicos a través de Nginx
- **Severity:** `MEDIUM` · **Categoría:** Information disclosure
- **Ubicación:** `backend/app/main.py:148-160` (`/metrics` con token **opcional**), `backend/app/core/config.py:62` (`METRICS_TOKEN` default `""`), `backend/app/main.py:82-88` (FastAPI con `docs_url`/`openapi_url` por defecto), `backend/app/core/auth_middleware.py:PUBLIC_PATHS` (`/docs`, `/redoc`, `/openapi.json`), `infra/nginx.conf:26-27`
- **Estado:** **`OPEN`** (parcialmente mitigado)
- **Verificación ejecutada:** introspección → `/metrics`, `/docs`, `/redoc`, `/openapi.json` siguen registrados y públicos; el handler sólo compara `METRICS_TOKEN` **si está definido** (`if expected:`), y el validador de producción **no** exige ese token.
- **PoC:** `curl -s https://host/metrics | head` y `curl -s https://host/openapi.json | jq '.paths|keys|length'` sin credenciales.
- **Remediación:** exigir `METRICS_TOKEN` en production (validator) o `deny all` en Nginx salvo la red de scraping; `docs_url=None, redoc_url=None, openapi_url=None` cuando `ENVIRONMENT=production`.

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
- **Estado:** `ACCEPTED-RISK` — tras SEC-FIX-006 sólo queda `python-jose 3.5.0` (PYSEC-2026-4298, **sin fix upstream**; `algorithms=["HS256"]` fijo y sin JWE ⇒ no explotable) y su transitiva `ecdsa` (no se usa). `lxml 6.1.3`, `cryptography 50.0.2` y `python-multipart 0.0.34` ya están actualizados y sin advisories conocidos (OSV por pin).

---

### [VULN-032] HIGH-07 (BYPASS REAL) — Bucket de rate-limit derivado de `X-API-Key` del cliente
- **Severity:** `HIGH` (bypass de un control HIGH recién corregido) · **Categoría:** Rate limiting / DoS
- **Ubicación (antes del fix):** `backend/app/core/rate_limit.py:143-148` — `api_key = request.headers.get("X-API-Key","")` y `key_parts.append(sha256(api_key)[:16])`
- **Estado:** **`FIXED`** en esta sesión
- **Por qué es HIGH:** `X-API-Key` es una cabecera **arbitraria del cliente** y no se valida en ningún middleware (`AuthMiddleware` sólo mira `Authorization`). Al formar parte de la clave del bucket, un atacante anónimo obtenía un bucket **nuevo por petición**:
  - anulación práctica del límite `login` (5/min) y del límite `default` (100/min) → fuerza bruta/abuso a la velocidad del borde (30 r/s/IP) y crecimiento ilimitado de claves en Redis (`ratelimit:*`) hasta agotar memoria, lo que en producción activa el fail-closed → **503 para todos**;
  - el `sub` bucket de SEC-FIX-004 no ayudaba: se aplica **además**, no en lugar del bucket por IP.
- **PoC medido (antes del fix):** 3 peticiones desde la misma IP (`203.0.113.50`) a `/api/v1/auth/login` con `X-API-Key: garbage-{0,1,2}` →
  `['login:203.0.113.50:6d633e…', 'login:203.0.113.50:927910…', 'login:203.0.113.50:65f9ff…']` → **3 buckets distintos**.
- **Remediación aplicada:** el bucket se compone sólo de `resolve_client_ip()` + (si hay JWT verificado) `sub`; se eliminó el uso de `X-API-Key` y el `import hashlib` sobrante.
- **Prueba de verificación ejecutada:** `pytest tests/test_rate_limit_identity.py -q` → **8 passed**, incluido `test_random_api_key_does_not_create_new_bucket` (3 cabeceras distintas ⇒ **1** bucket) y `test_login_bucket_is_still_classified_as_login`.
- **Nota para el orchestrator:** si en el futuro se quiere rate-limit **por API key**, la clave debe validarse contra `settings.OPERATOR_API_KEYS` **antes** de usarla como identidad.

### [VULN-033] MEDIUM-14 — `request.url.path` (Host poisoning, CVE-2026-48710) usado en decisiones de seguridad
- **Severity:** `MEDIUM` · **Categoría:** AuthZ/Rate-limiting — input no confiable
- **Ubicación (antes del fix):** `backend/app/core/auth_middleware.py:33` (`PUBLIC_PATHS`), `backend/app/core/rate_limit.py:149` (clasificación), `backend/app/api/auth.py:75` (clave de lockout), `backend/app/api/osint/auth.py:370,409,489` (mismo patrón), `backend/app/main.py:123`
- **Estado:** **`FIXED`** en esta sesión
- **Evidencia del mecanismo (ejecutada):** con el pin real `starlette==0.41.3` (venv aislado), `URL(scope=...)` construye `f"{scheme}://{Host}{path}"`:
  `Host='api.sesis.local'` → `url.path='/api/v1/auth/login'`; `Host='api.sesis.local/x'` → `url.path='/x/api/v1/auth/login'` (mientras `scope["path"]` no cambia). Consecuencia: la **clave de lockout** (`f"{username}:{request.url.path}"`) cambiaba por variante de Host ⇒ fuerza bruta sin lockout, y `PUBLIC_PATHS` se evaluaba sobre un valor influenciable.
- **Alcance real medido (por eso MEDIUM y no HIGH):** en el borde desplegado **no es alcanzable**: nginx 1.30.4 responde **400 Bad Request** a `Host: api.sesis.local/x` (probado con una instancia local y un upstream que refleja cabeceras); `Host: api.sesis.local%2Fx` viaja literal (`api.sesis.local%2fx`) sin mover el path; y en `ENVIRONMENT=production` `TrustedHostMiddleware` sólo admite `api.sesis.local`. Era, por tanto, un defecto latente que se habría activado al cambiar el proxy o desplegar en staging.
- **Remediación aplicada:** helper `request_path(request)` (`scope["path"]` con fallback `/`) usado en `AuthMiddleware`, `RateLimitMiddleware`, `/api/v1/auth/login`, `main.py` y el módulo OSINT (código muerto incluido, para no dejar el patrón).
- **Prueba de verificación ejecutada:** `pytest tests/test_rate_limit_identity.py -q` → 8 passed (`test_host_header_with_path_cannot_change_routing_path`, `test_host_header_does_not_change_public_path_detection`, `test_empty_scope_path_falls_back_to_root`).

### [VULN-034] MEDIUM-15 (BYpass de fail-closed) — `NameError` en la rama “deny” del lockout
- **Severity:** `MEDIUM` · **Categoría:** Fail-closed / Correctness
- **Ubicación (antes del fix):** `backend/app/api/osint/auth.py:150` — `logger.error(...)` sin `logger` definido en el módulo
- **Estado:** **`FIXED`** en esta sesión
- **Cómo se encontró:** sonda directa `BruteForceProtector.is_locked` con Redis caído y `SECURITY_FAIL_MODE=closed` → `NameError: name 'logger' is not defined` (en vez de `return True`). El deny se cumplía “por accidente” vía 500, sin `Retry-After`, sin métrica y con traza en logs.
- **Remediación aplicada:** `import logging` + `logger = logging.getLogger(__name__)` en el módulo.
- **Prueba de verificación ejecutada:** `pytest tests/test_rate_limit_identity.py -q` → `TestBruteForceFailMode`: closed ⇒ `is_locked is True`; open ⇒ `False` (2 passed).

### [VULN-035] MEDIUM-16 — MFA no se aplica en ninguna ruta viva
- **Severity:** `MEDIUM` · **Categoría:** Autenticación / control ausente
- **Ubicación:** `backend/app/api/auth.py:60-120` (no consulta `two_factor_enabled` ni emite challenge), `backend/app/core/config.py:22` (**`MFA_ENABLED` definido y sin uso**: `grep -rn MFA_ENABLED backend/app` → sólo config), `backend/app/api/intel/deps_classified.py:32-92` (`require_mfa_verified_user` **sin consumidores**; `/api/v1/classified` no está montado — introspección: `[]`)
- **Estado:** `OPEN`
- **Impacto:** con usuario+contraseña correctos se emiten `access`+`refresh` con el `clearance` del usuario (el admin sembrado es `TOP_SECRET`) **sin segundo factor**. El flag por defecto `MFA_ENABLED=true` es decorativo.
- **PoC:** `curl -s -X POST https://host/api/v1/auth/login -d '{"username":"admin","password":"<válida>"}' -H 'Content-Type: application/json'` → tokens de acceso completos, sin challenge.
- **Remediación:** montar el flujo MFA (challenge de un solo uso + `/mfa/verify`) en `/api/v1/auth/*` y exigir `mfa_verified=true` para `clearance >= CONFIDENTIAL`; o montar `/api/v1/classified` con `require_mfa_verified_user`. Hasta entonces, **no anunciar MFA como control activo**.
- **Nota:** no lo clasifico HIGH porque requiere credencial válida y no es un bypass de los fixes auditados, pero **es el MEDIUM que priorizaría antes de exponer el sistema**.

### [VULN-036] MEDIUM-17 — DoS de cuenta vía lockout (bloqueo renovable)
- **Severity:** `MEDIUM` · **Categoría:** Availability
- **Ubicación:** `backend/app/api/osint/auth.py:121-152` (`MAX_ATTEMPTS=5`, `WINDOW=300`, `lockout` TTL `WINDOW*2`), consumido por `backend/app/api/auth.py:77-84`
- **Estado:** `OPEN`
- **PoC:** 5 `POST /api/v1/auth/login` fallidos contra `admin` cada 10 minutos → la cuenta queda bloqueada de forma sostenida para el usuario legítimo (el nombre `admin` es el sembrado por defecto). No requiere autenticación.
- **Remediación:** combinar lockout por cuenta con IP/reputación (bloquear la IP tras N cuentas distintas), backoff exponencial en lugar de bloqueo duro, CAPTCHA/proof-of-work tras 3 fallos y alerta a operaciones; desbloqueo administrativo.

### [VULN-037] MEDIUM-18 — `revoke_jti` (escritura) sigue fail-open: `logout` puede ser un no-op
- **Severity:** `MEDIUM` · **Categoría:** Session management
- **Ubicación:** `backend/app/core/security.py:155-163` (`except Exception: logger.warning(...)`, sin deny ni error al cliente)
- **Estado:** `OPEN`
- **Impacto:** si Redis falla al **escribir** (pero responde a lecturas), `logout` devuelve éxito sin revocar: el token sigue siendo aceptado (`is_jti_revoked` consulta Redis y no lo encuentra) hasta `exp` (15 min). La lectura ya es fail-closed (§VULN-007), la escritura no.
- **Remediación:** propagar el fallo (503) en modo closed; o escribir la revocación en DB como respaldo y reconciliar.
- **Verificación propuesta:** test que parchea `setex` con excepción → `logout` 503 en production.

### [VULN-038] MEDIUM-19 — `TRUSTED_PROXIES` incluye todo RFC1918: peer interno puede falsificar `X-Real-IP`
- **Severity:** `MEDIUM` · **Categoría:** Rate limiting / trust boundary
- **Ubicación:** `backend/app/core/config.py:63-66` (`127.0.0.1,::1,10/8,172.16/12,192.168/16`)
- **Estado:** `ACCEPTED-RISK` (con condición)
- **Análisis:** es necesario que nginx (red Docker `172.x`) sea “confiable”; el efecto colateral es que **cualquier** contenedor de la red (frontend, celery, ollama, un servicio comprometido o un SSRF con capacidad de petición interna) puede fijar `X-Real-IP` y elegir su bucket/lockout-key. No permite escalar privilegios ni evadir la autenticación; sólo afloja el rate-limit desde dentro de la red.
- **Remediación futura:** `TRUSTED_PROXIES=<IP fija de nginx>/32` por entorno (o `172.18.0.2/32`) y `deny` de `:8000` fuera de nginx.

### [VULN-039] MEDIUM-20 — Residuales SCA en `starlette 0.41.3` (allowlist)
- **Severity:** `MEDIUM` · **Categoría:** Supply chain (aceptado)
- **Ubicación:** `backend/requirements.txt:1` (`fastapi==0.115.6` → `starlette 0.41.3`), `docs/security/SCA_ALLOWLIST.md`, `.github/workflows/ci.yml:57-67`
- **Estado:** `ACCEPTED-RISK` (expira: FASE 10)
- **Inventario (OSV):** PYSEC-2026-1941/GHSA-2c2j (DoS multipart, MODERATE), **PYSEC-2026-1942/GHSA-7f5h (DoS `Range` en `FileResponse`, HIGH)**, PYSEC-2026-161/GHSA-86qp (“BadHost”: path reconstruido desde Host → cubierto en código por §VULN-033), PYSEC-2026-2281/GHSA-wqp7 (**Windows-only**, SSRF UNC en StaticFiles), PYSEC-2026-2280/GHSA-x746 (`HTTPEndpoint`), PYSEC-2026-249/GHSA-82w8 (DoS `urlencoded`), PYSEC-2026-248/GHSA-jp82 (path en authority).
- **Por qué se acepta:** `FileResponse` sólo existe en `app/api/osint/{evidence,reports}.py` (**no montados**); no hay `StaticFiles`; los formularios `urlencoded` no se usan en rutas vivas (los bodies son Pydantic JSON); el despliegue es Linux; `HTTPEndpoint` no se usa. **Condición de elevación:** montar OSINT evidence/reports, añadir `StaticFiles`, aceptar formularios en endpoints públicos o desplegar en Windows ⇒ estos advisories pasan a HIGH y bloquean el release.

### [VULN-040] MEDIUM-21 — `Admin` puede registrarse como cuenta distinta de `admin` (sin normalización)
- **Severity:** `MEDIUM` · **Categoría:** Identity / Audit integrity
- **Ubicación:** `backend/app/api/auth.py:86-120` (registro), `backend/app/db/models/persistence.py:353` (`username = Column(String, unique=True)` sin `citext`/normalización), login con igualdad exacta
- **Estado:** `OPEN`
- **Evidencia:** probado en SQL que `'Admin'`, `'ADMIN'`, `'admin '` **no** coinciden con `'admin'`; el registro público sólo comprueba igualdad exacta ⇒ se puede crear `Admin`/`admín` (confusable) sin colisión. No otorga privilegios (el nuevo usuario es `operator`/`RESTRICTED`/`is_active=False`), pero contamina auditoría y habilita phishing interno.
- **Remediación:** `username` normalizado (`strip().lower()`) + índice único funcional (`lower(username)`) + rechazo de homoglifos/espacios.

---

## 4. AUTOMATED SECURITY TOOLING LOG

| # | Tool / Command | Scope | Exit Code | Resultado real (re-auditoría de cierre) |
| :--- | :--- | :--- | :--- | :--- |
| 1 | `cd backend && SECRET_KEY="test-secret-key-32-chars-minimum!!!" python3 -m pytest tests -q` | Suite completa | **0** | `169 passed, 1999 warnings in 56.25s` |
| 2 | `python3 ../scripts/validate_all.py` | Validador de proyecto | **0** | `169 passed` + `Overall Status: VALIDATED` |
| 3 | `python3 -m compileall -q app` | Sintaxis backend | **0** | OK (tras fixes de `rate_limit`, `auth_middleware`, `auth`, `osint/auth`, `main`) |
| 4 | `pytest tests/test_login_lockout.py -q` | SEC-FIX-005 (lockout vivo) | **0** | **2 passed** (429 + `Retry-After: 60`; `AuditLog` persistido) |
| 5 | `pytest tests/test_rate_limit_hardening.py -q` | SEC-FIX-001/004 | **0** | **7 passed** (4 spoofing/IP + 3 fail-mode 503/200) |
| 6 | `pytest tests/test_rate_limit_identity.py -q` (nuevo) | SEC-FIX-009/010 + bypasses | **0** | **8 passed** (Host poisoning, X-API-Key, fail-closed lockout) |
| 7 | `pytest tests/test_security_core.py -q` | JWT/revocación/fail-closed | **0** | **34 passed** (open dev / closed prod 503) |
| 8 | `pytest tests/test_vision_yolo_integrity.py -q` | SEC-FIX-006 (hash YOLO) | **0** | **5 passed** |
| 9 | `npm audit --omit=dev --audit-level=high` (`/tmp/opencode/node20/bin`) | SCA Node (oficial) | **0** | `found 0 vulnerabilities` |
| 10 | `python -m pip_audit -r backend/requirements.txt --ignore-vuln …` (10 IDs de allowlist) | SCA Python (oficial) | **0** | `No known vulnerabilities found, 19 ignored` (~18 min; un intento previo con `timeout 400` → **124**) |
| 11 | `pip-audit` sin ignores (diagnóstico) | SCA Python | **124** | timeout 400 s → se sustituye por OSV por pin (§12) |
| 12 | `POST https://api.osv.dev/v1/querybatch` (32 pins directos PyPI) | SCA Python | **0** | Sólo `python-jose 3.5.0` (sin fix upstream) y `pytest 8.3.4` (dev) → allowlist |
| 13 | `GET https://pypi.org/pypi/<pkg>/json` (9 pins nuevos) | Existencia de versiones | **0** | Todos existen (`multipart 0.0.34`, `jose 3.5.0`, `passlib 1.7.4`, `cryptography 50.0.2`, `lxml 6.1.3`…) |
| 14 | Introspección `app.routes` + walk de `route.dependant` | Cobertura authz | **0** | **180 `APIRoute`**; 6 públicas; 2 auth sin clearance (`/auth/logout`, `/auth/me`); `/api/v1/classified` **no montado** (`[]`) |
| 15 | Sonda `BruteForceProtector.is_locked` con Redis caído (dev/open vs prod/closed) | Fail-closed lockout | **0** | open → `False`; closed → `NameError` detectado (§VULN-034) → corregido → `True` |
| 16 | Sonda de bucket con `X-API-Key` aleatorio ×3 (antes del fix) | Bypass rate-limit | **0** | **3 buckets distintos** → §VULN-032 |
| 17 | `python -m venv /tmp/... && pip install starlette==0.41.3` + `Request.url.path` con Host manipulado | CVE-2026-48710 | **0** | `Host='x'` → `url.path='/x/api/v1/auth/login'` vs `scope['path']='/api/v1/auth/login'` |
| 18 | nginx 1.30.4 local + upstream que refleja cabeceras (`Host: api.sesis.local/x`, `%2Fx`, `.`) | Borde real | **0** | `/x` → **400**; `%2Fx` → host literal `api.sesis.local%2fx`; `.` → normalizado → **bypass no alcanzable** |
| 19 | SQLite: `SELECT … WHERE username=` con `admin`, `Admin`, `ADMIN`, `admin `, ` admin` | Bypass de lockout por case | **0** | Sólo `admin` coincide → no hay bypass de adivinación |
| 20 | `grep -rn "eval(\|exec(\|os.system\|shell=True\|pickle.loads\|yaml.load("` | RCE/Injection | **1** | 0 coincidencias (limpio) |
| 21 | `grep -rn 'execute(f"\|text(f"\|f"SELECT'` | SQLi | **1** | 0 coincidencias (limpio) |
| 22 | `grep -rn FileResponse\|StaticFiles backend/app` | Alcance advisories starlette | **0** | Sólo `osint/evidence.py` y `osint/reports.py` (**no montados**) |
| 23 | `pytest tests/test_ssrf.py -q` / `test_vision_ssrf.py -q` | SSRF | **0** | 18 passed / 10 passed |
| 24 | `pytest tests/test_audit_persistence.py tests/test_audit_unified.py -q` | Audit chain | **0** | 6 passed |
| 25 | `docker compose config` | Compose válido | **127** | **No ejecutable:** `docker` no disponible |
| 26 | `bandit` / `semgrep` / `trivy` | SAST | **127** | No instalados → revisión manual + greps dirigidos |
| 27 | `git diff -U0 backend/tests/ \| grep '^-[^-]'` | Integridad de tests | **1** | **0 líneas eliminadas** en tests existentes (solo se añaden suites nuevas) |
| 28 | `git ls-files \| grep -Ei '\.env|fernet|\.key|\.pem'` | Secretos commiteados | **0** | Solo `.env.example` y `frontend/.env.local.example` |

> **Limitaciones declaradas:** `docker`, `bandit`, `semgrep` y `trivy` **no** están disponibles; `npm audit` y `pip-audit` **sí** se ejecutaron (exit 0). Los PoC de red se validaron con instancias locales reales (nginx 1.30.4 + upstream reflector, venv con `starlette==0.41.3`) en lugar de con el stack completo en contenedores. `tsc`/`next build` **no** se reprodujeron (sin `node_modules`; el orquestador reporta OK). No se ha ejecutado explotación contra un despliegue vivo: todo es local/laboratorio.

---

## 5. FINAL RELEASE SIGN-OFF

- **All `CRITICAL` findings resolved & verified:** `YES` — 0 abiertos (VULN-001/002 `FIXED`).
- **All `HIGH` findings resolved & verified:** **`YES` — 0 abiertos.** 8 `HIGH` totales, todos `FIXED` con evidencia ejecutable:

| ID | HIGH | Estado | Evidencia de cierre (ejecutada) |
| :--- | :--- | :--- | :--- |
| VULN-003 | Credenciales por defecto publicadas | `FIXED` | `grep admin123` → 0; `Settings()` en production con placeholders → `Refusing to start` |
| VULN-004 | SSRF TOCTOU OSINT | `FIXED` | `pytest tests/test_ssrf.py` → 18 passed |
| VULN-005 | SSRF visión/Maven | `FIXED` | `pytest tests/test_vision_ssrf.py` → 10 passed |
| **VULN-006** | Brute-force login vivo | **`FIXED`** | `pytest tests/test_login_lockout.py` → 2 passed (429 + auditoría); bypasses de case/Host/API-key probados |
| **VULN-007** | Fail-open sin Redis | **`FIXED`** | `pytest tests/test_rate_limit_hardening.py` 7 / `test_security_core.py` 34 / `test_rate_limit_identity.py` 8 |
| **VULN-008** | IP real tras proxy | **`FIXED`** | 4 tests de spoofing + bucket `sub`; nginx sobrescribe `X-Real-IP` (medido) |
| **VULN-009** | Dependencias HIGH/CRITICAL | **`FIXED`** | `npm audit` → 0; `pip-audit` (gate CI) → `No known vulnerabilities found, 19 ignored`, exit 0 |
| **VULN-032** | Bypass rate-limit vía `X-API-Key` (nuevo) | **`FIXED`** | 3 buckets antes / **1** después (`test_random_api_key_does_not_create_new_bucket`) |

- **MEDIUM:** 23 totales → `FIXED` 5 · `PARTIAL` 2 (VULN-010, 021) · `ACCEPTED-RISK` 2 (VULN-038, 039) · **`OPEN` 14** (VULN-014, 015, 016, 017, 018, 019, 020, 022, 023, 024, 035, 036, 037, 040).
- **LOW:** 7 totales → `OPEN` 4 (VULN-026, 027, 029, 030) · `ACCEPTED-RISK` 3 (VULN-025, 028, 031).
- **Ready for Production Delivery:** **`APPROVED`** — 0 CRITICAL y 0 HIGH abiertos.

**Condiciones que el despliegue DEBE cumplir para que este `APPROVED` sea válido** (si no, el veredicto no aplica):
1. `ENVIRONMENT=production` (o `staging`) y `PRODUCTION=true`; el modo fail-closed se deriva de ahí (§VULN-007). El `docker-compose.yml` por defecto es `development` ⇒ controles fail-closed **apagados** (§VULN-040).
2. `SECRET_KEY`, `ADMIN_INITIAL_PASSWORD` (≥10, sin placeholders), `MFA_ENCRYPTION_KEY` (64 hex), `NEO4J_PASSWORD`, `GRAFANA_ADMIN_PASSWORD` propios del despliegue (validador de arranque).
3. `METRICS_TOKEN` definido **o** `/metrics` y `/docs` bloqueados en Nginx (§VULN-015 sigue abierto).
4. `YOLO_MODEL_SHA256` fijado si se despliega el stack de visión.
5. **No** montar los módulos OSINT/CASES/EVIDENCE/`/api/v1/classified` sin cerrar antes VULN-014/020/022/035 (hoy están fuera del runtime y eso forma parte de por qué no hay HIGH abiertos).

**Cambios de código aplicados en esta re-auditoría (fixes pequeños + tests nuevos, sin tocar tests existentes):**

| Fix | Archivos | Verificación |
| :--- | :--- | :--- |
| SEC-FIX-009 (Host→path) | `backend/app/core/rate_limit.py` (`request_path`), `backend/app/core/auth_middleware.py`, `backend/app/api/auth.py`, `backend/app/api/osint/auth.py`, `backend/app/main.py` | `pytest tests/test_rate_limit_identity.py` → 8 passed |
| SEC-FIX-010 (bucket por `X-API-Key`) | `backend/app/core/rate_limit.py` | ídem (`test_random_api_key_does_not_create_new_bucket`) |
| SEC-FIX-001-bis (`logger` en fail-closed) | `backend/app/api/osint/auth.py` | ídem (`TestBruteForceFailMode`: closed⇒deny, open⇒allow) |

**Riesgos que NO oculto aunque el gate esté en verde:**
- **VULN-035 (MFA no aplicado):** el sistema anuncia MFA (`MFA_ENABLED=true`) pero **ninguna ruta lo exige**. Es el primer MEDIUM a cerrar antes de exponer el sistema a Internet.
- **VULN-015/016/017/018:** `/metrics` y `/docs` públicos, tokens en `localStorage`, frontend sin CSP/HSTS y Redis/NATS sin auth.
- **VULN-010/022:** la cadena de auditoría no es fiable multi-proceso y gran parte de los controles auditados (MFA, evidencia, custodia) viven en routers **no montados**.

---

## 6. FUTURE SECURITY ROADMAP (Staged by FASE)

| FASE | Título | TAREA/ID(s) |
|---|---|---|
| FASE 3 (cerrado) | 4 HIGH + bypass | `SEC-FIX-001` ✅, `SEC-FIX-002` ✅, `SEC-FIX-003` ✅, `SEC-FIX-004` ✅, `SEC-FIX-005` ✅, `SEC-FIX-006` ✅, `SEC-FIX-009` ✅, `SEC-FIX-010` ✅ |
| **FASE 3.b (prioridad máxima)** | MFA real | `SEC-FIX-011`: challenge + `/mfa/verify` en `/api/v1/auth/*`, `mfa_verified=true` para `clearance >= CONFIDENTIAL`; montar `/api/v1/classified` con `require_mfa_verified_user` (VULN-035) |
| FASE 3.b | Lockout sin DoS | `SEC-FIX-012`: backoff exponencial + bloqueo por IP/reputación, no bloqueo duro de cuenta; alerta (VULN-036) |
| FASE 3.b | Revocación fail-closed | `SEC-FIX-013`: `revoke_jti` propaga 503 en closed o persiste en DB (VULN-037) |
| FASE 3.b | Hardening perimetral | `SEC-FIX-007`: `/metrics`+`/docs` cerrados en production, `headers()` en Next, `next start`, `limit_req zone=auth`, `server_tokens off`, `requirepass` Redis/NATS (VULN-015/016/017/018) |
| FASE 3.b | Identidad | `SEC-FIX-014`: normalización de `username` + índice único `lower(username)` (VULN-040) |
| FASE 3.b | Auditoría | `SEC-FIX-008`: head único en DB + persistencia estricta + decisión sobre routers OSINT no montados (VULN-010/022) |
| FASE 5 | Testing de seguridad | ya añadidas: `test_rate_limit_identity.py` (8), `test_login_lockout.py` (2), `test_rate_limit_hardening.py` (7), `test_vision_yolo_integrity.py` (5), `test_vision_ssrf.py` (10) |
| FASE 5 | SCA en CI | gate bloqueante ya activo (`pip-audit` + `npm audit --omit=dev --audit-level=high`); revisar allowlist en FASE 10 |
| FASE 6 | Observabilidad | alertas sobre `sesis_security_fail_open_total{component}`, `auth_failure`, `ssrf_block_total` |

**Registro de pendientes:** MEDIUM abiertos: VULN-014, 015, 016, 017, 018, 019, 020, 022, 023, 024, 035, 036, 037, 040 (+ PARTIAL 010, 021). Aceptados con fecha de revisión: VULN-038 (IP fija de nginx), VULN-039 (starlette, FASE 10).

**Plan de reapertura del gate:** cualquier cambio que (a) monte `FileResponse`/`StaticFiles`/formularios públicos, (b) cambie el proxy de borde o desactive `TrustedHostMiddleware`, (c) añada una decisión de seguridad basada en `request.url.*`, (d) desactive el fail-closed o el lockout, o (e) degrade `ENVIRONMENT` a `development` en el despliegue, **invalida este `APPROVED`** y exige repetir esta auditoría.
