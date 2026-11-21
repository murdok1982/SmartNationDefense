# VALIDATION_PLAN.md — Plan de validación y criterios de aceptación

**Doc ID:** VAL-2026-SND-001
**Proyecto:** SmartNationDefense / SESIS-FEDERATION
**Fecha:** 2026-11-21
**Ámbito:** cómo se valida el sistema, con qué comandos, qué evidencia se exige y qué está pendiente.
**Autor:** `@architect` (TASK-045) sobre la práctica real de `@qa-verifier`.

> Principio: **un criterio de aceptación no está cumplido porque alguien lo diga, sino porque un comando reproducible lo demuestra.** Este plan convierte cada `AC-XX` en una comprobación.

---

## 1. Objetivos

1. Verificar que el código compila, importa y arranca en lo que sea posible en el entorno.
2. Verificar que los controles de seguridad funcionan (no sólo existen).
3. Verificar que los criterios `AC-XX` de `.factory/SPEC.md` tienen evidencia.
4. Detectar regresiones antes de que lleguen a producción.
5. Separar lo verificado de lo bloqueado, sin ambigüedad.
6. Producir artefactos (`reports/validation.json`, logs) que puedan auditarse.

---

## 2. Alcance y niveles

| Nivel | Qué valida | Herramienta | Estado en este entorno |
| :--- | :--- | :--- | :--- |
| L0 — Sintaxis | Importación y compilación | `compileall`, `py_compile` | VERIFICADO |
| L1 — Unitario | Funciones y servicios | `pytest` | VERIFICADO |
| L2 — Integración | Routers + DB SQLite | `pytest` + `aiosqlite` | VERIFICADO |
| L3 — Contrato | OpenAPI vs app | `pytest test_contracts.py` | VERIFICADO |
| L4 — Seguridad | Auth, clearance, SSRF, auditoría, rate limit | `pytest` + `validate_all.py` | VERIFICADO (con dobles) |
| L5 — Frontend | Tipos y build | `tsc`, `next build` | VERIFICADO (copia Node 20.18) |
| L6 — Móvil | Análisis y tests | `flutter analyze`, `flutter test` | VERIFICADO (0 errores, 11 tests) |
| L7 — Infra | Compose, healthchecks | `docker compose config` | BLOQUEADO (sin Docker) |
| L8 — Observabilidad | Scrape, dashboards | Prometheus/Grafana | BLOQUEADO (sin runtime) |
| L9 — E2E | Flujo completo | Navegador/HTTP real | NO VERIFICADO |

---

## 3. Entornos

| Entorno | Uso | Requisitos | Estado |
| :--- | :--- | :--- | :--- |
| Local de tests | Suite backend | Python 3.12+ (aquí 3.14), SQLite, dobles Redis/NATS | DISPONIBLE |
| Local completo | Arranque real | Docker, 12 servicios | NO DISPONIBLE |
| Staging | Validación pre-producción | Secretos reales, TLS | NO DISPONIBLE |
| Producción | Operación | Secretos fuertes, backups | NO DISPONIBLE |

---

## 4. Herramientas y configuración

### 4.1 Backend

| Herramienta | Versión | Uso |
| :--- | :--- | :--- |
| Python | 3.14.10 (entorno actual); CI 3.12 | Runtime |
| pytest | 8.3.4 | Tests |
| pytest-asyncio | 0.25.0 | Tests async |
| aiosqlite | 0.21.0 | DB de test |
| `compileall` | stdlib | Sintaxis |
| `validate_all.py` | propio | Gate de seguridad |

### 4.2 Frontend

| Herramienta | Versión | Uso | Disponibilidad |
| :--- | :--- | :--- | :--- |
| Node.js | 20.18 en copia `/tmp/opencode/fe_verify`; ausente en PATH | Build | VERIFICADO (copia) |
| TypeScript | ^5.3.0 | Tipos | vía npm |
| Next.js | ^16.4.6 + React 19 | Build | Node 20.18 en copia |

### 4.3 Móvil

| Herramienta | Ruta | Uso |
| :--- | :--- | :--- |
| Flutter SDK | `/tmp/opencode/flutter/bin/flutter` | Analyze/test |

### 4.4 Infra

| Herramienta | Estado |
| :--- | :--- |
| Docker | **AUSENTE** |
| `docker compose` | **AUSENTE** |
| `yamllint` | No instalado |
| `python3-yaml` | Disponible |

---

## 5. Estrategia por nivel

### 5.1 L0 — Sintaxis e importación

**Objetivo:** detectar errores de importación antes de ejecutar tests.

Comandos:

```bash
python3 -m compileall -q backend
cd backend && SECRET_KEY="test-secret-key-32-chars-minimum!!!" python3 -c "import app.main"
```

Criterio: exit 0 y sin `ImportError`.

Estado: **VERIFICADO** (los tests importan `app.main`).

### 5.2 L1/L2 — Unitario e integración

**Objetivo:** comportamiento de servicios y routers.

Comando:

```bash
SECRET_KEY="test-secret-key-32-chars-minimum!!!" python3 -m pytest backend/tests -q
```

Criterio: 0 fallos, 0 errores.

Estado: **157 passed** (2026-11-21).

Limitación: SQLite y dobles. Los tests no prueban PostgreSQL, Redis, NATS ni Neo4j reales.

### 5.3 L3 — Contrato

**Objetivo:** el contrato no se aleja de la app.

Comando:

```bash
SECRET_KEY="test-secret-key-32-chars-minimum!!!" python3 -m pytest backend/tests/test_contracts.py -q
```

Criterio: 5 passed; cada path `/api/v1` del contrato existe en la app viva.

Estado: **VERIFICADO**.

Limitación: valida presencia, no semántica de respuesta.

### 5.4 L4 — Seguridad

**Objetivo:** los controles fallan cerrado y los tests lo demuestran.

Comandos:

```bash
SECRET_KEY="test-secret-key-32-chars-minimum!!!" python3 -m pytest \
  backend/tests/test_auth.py \
  backend/tests/test_clearance_enforcement.py \
  backend/tests/test_v1_clearance_matrix.py \
  backend/tests/test_mfa_security.py \
  backend/tests/test_ssrf.py \
  backend/tests/test_vision_ssrf.py \
  backend/tests/test_audit_persistence.py \
  backend/tests/test_audit_unified.py \
  backend/tests/test_rate_limit.py \
  backend/tests/test_events_dlq.py   backend/tests/test_security_core.py   backend/tests/test_mfa_core.py   backend/tests/test_web_tools_core.py   backend/tests/test_crypto_quantum.py   backend/tests/test_login_lockout.py   backend/tests/test_rate_limit_hardening.py   backend/tests/test_vision_yolo_integrity.py -q

python3 scripts/validate_all.py

# Cobertura de las suites de seguridad
python3 -m pytest backend/tests -q \
  --cov=backend/app/core/security.py \
  --cov=backend/app/services/intel/auth/mfa.py \
  --cov=backend/app/services/osint/tools/web_tools.py \
  --cov=backend/app/core/audit.py \
  --cov=backend/app/core/rate_limit.py \
  --cov=backend/app/core/crypto_quantum.py \
  --cov-report=term
```

Criterio: todos verdes + `Overall Status: VALIDATED` + 4 invariantes PASS.

Estado: **VERIFICADO** (157 passed, VALIDATED, exit 0). Cobertura de las **6 suites/módulos de seguridad**: **88%** (`security.py` 97%, `mfa.py` 99%, `web_tools.py` 87%, `audit.py` 87%, `rate_limit.py` 82%, `crypto_quantum.py` 62%). El backend completo no está medido al 80% (≈73% agregado).

### 5.5 L5 — Frontend

**Objetivo:** tipos y build sin errores.

Comandos (requieren Node):

```bash
cd frontend
npm ci
npx tsc --noEmit
npm run build
```

Criterio: `tsc` 0 errores; `next build` OK; rutas `/`, `/login`, `/maven`, `/_not-found`.

Estado: **VERIFICADO** en copia limpia (`rsync` a `/tmp/opencode/fe_verify`) con Node 20.18: `npm ci` OK, `npx tsc --noEmit` 0 errores, `next build` OK, 4 rutas, `npm audit --omit=dev --audit-level=high` → 0 vulnerabilidades de producción.

### 5.6 L6 — Móvil

**Objetivo:** 0 errores de análisis y tests verdes.

Comandos (Flutter 3.24.5 portable sobre copia en `/tmp`):

```bash
cd mobile/sesis_cop
flutter analyze
flutter test
```

Criterio: `No issues found!` y tests PASS.

Estado: **VERIFICADO**.

```text
Analyzing sesis_cop...
No issues found! (ran in 18.6s)

00:02 +11: All tests passed!
```

Correcciones aplicadas: `core/storage/offline_queue.dart` creado (138 LOC), `CardThemeData` → `CardTheme`, y `test/mesh_protocol_test.dart` con 11 tests.

### 5.7 L7 — Infraestructura

**Objetivo:** compose válido, servicios sanos, puertos correctos.

Comandos (requieren Docker):

```bash
docker compose config
docker compose up -d --build
docker compose ps
docker compose ps --format json | jq '.[] | select(.Health != "healthy")'
curl -sk https://localhost/healthz
curl -s http://localhost:8000/api/v1/health
```

Criterio: `config` exit 0; 12/12 healthy; healthz 200; API 200.

Estado: **BLOQUEADO**. Validación estática: YAML parse OK, 12 servicios, 12 healthchecks.

### 5.8 L8 — Observabilidad

**Objetivo:** métricas reales y dashboards con datos.

Comandos (requieren runtime):

```bash
curl -s http://localhost:8000/metrics | grep sesis_http_requests_total
curl -s http://localhost:9090/api/v1/targets
curl -s http://localhost:9093/-/healthy
curl -s http://localhost:3001/api/health
```

Criterio: series presentes, targets UP, Alertmanager healthy, Grafana healthy.

Estado: **BLOQUEADO**. Evidencia de código: `/metrics` responde 200 y expone las series (verificado históricamente con TestClient).

### 5.9 L9 — E2E

**Objetivo:** flujo login → COP → datos → logout.

Herramienta propuesta: Playwright.

Criterio: flujo completo sin errores de consola; datos visibles; logout invalida sesión.

Estado: **NO VERIFICADO**. No hay tests E2E en el repositorio.

### 5.10 Tabla de evidencia actual (post SEC-FIX + FASE 7)

| Evidencia | Comando | Resultado | Estado |
| :--- | :--- | :--- | :--- |
| Suite backend | `pytest backend/tests -q` | **157 passed**, 0 failed | VERIFICADO |
| Validación global | `python3 scripts/validate_all.py` | `VALIDATED`, exit 0, 4 invariantes PASS | VERIFICADO |
| Cobertura de seguridad (6 módulos) | `pytest --cov=... --cov-report=term` | **88%** (security 97%, mfa 99%, web_tools 87%, audit 87%, rate_limit 82%, crypto_quantum 62%) | VERIFICADO (reportado) |
| Cobertura backend completo | `pytest --cov=app` | ≈73% agregado; no alcanza 80% | NO VERIFICADO al 80% |
| Móvil analyze | `cd mobile/sesis_cop && flutter analyze` | `No issues found!` | VERIFICADO |
| Móvil tests | `cd mobile/sesis_cop && flutter test` | **11 passed** | VERIFICADO |
| SCA backend | `pip-audit` con `SCA_ALLOWLIST.md` | **0 vulnerabilidades** | VERIFICADO |
| SCA frontend | `npm audit --omit=dev --audit-level=high` | 0 vulnerabilidades de producción; residual dev `brace-expansion` (eslint) | VERIFICADO |
| Build frontend | `tsc --noEmit` + `next build` | 0 errores, 4 rutas (`/`, `/_not-found`, `/login`, `/maven`) | VERIFICADO |
| Contrato | `app.openapi()` | 168 paths / 177 operaciones | VERIFICADO |
| Infra compose | `docker compose config` | Docker ausente | BLOQUEADO |

---

## 6. Matriz de criterios de aceptación (AC-XX)

> Fuente: `.factory/SPEC.md` §3. Los estados se basan en la evidencia de este entorno, no en lo que el SPEC marca.

| AC | Requisito | Evidencia exigida | Estado real | Nota |
| :--- | :--- | :--- | :--- | :--- |
| AC-01 | Inventario real (stacks, APIs, módulos) | `docs/audit/REPOSITORY_AUDIT.md` + este paquete | VERIFICADO | FASE 0 + FASE 9 |
| AC-02 | Hallazgos CRITICAL/HIGH/MEDIUM/LOW reales | `docs/audit/SECURITY_AUDIT.md`, `docs/AUDIT.md` | VERIFICADO | Con hallazgos abiertos |
| AC-03 | Matriz de funcionalidades con veredictos | `docs/FEATURE_MATRIX.md` | VERIFICADO | 105 fichas |
| AC-04 | SYSTEM_OVERVIEW documenta ADR-001 | `docs/architecture/SYSTEM_OVERVIEW.md` | VERIFICADO | — |
| AC-05 | ADR-001..013 con alternativas | `ARCHITECTURE_DECISIONS.md` | VERIFICADO | 13 ADR |
| AC-06 | DATA_FLOW con Mermaid | `docs/architecture/DATA_FLOW.md` | VERIFICADO | ≥ 4 diagramas |
| AC-07 | SECURITY/DEPLOYMENT architecture | `docs/architecture/*` | VERIFICADO | — |
| AC-08 | User unificado | `grep __tablename__ users` = 1 | VERIFICADO | 1 tabla |
| AC-09 | Clearance v1 | `test_clearance_enforcement.py` + matriz | VERIFICADO | 141 rutas, 0 gaps |
| AC-10 | EncryptedField fail-closed | `persistence.py` L42/L54 | VERIFICADO | ValueError |
| AC-11 | Rate limit path-aware | `get_limiter_key` + tests | VERIFICADO | 6 tests |
| AC-12 | X-XSS eliminado | `grep -c X-XSS` = 0 | VERIFICADO | — |
| AC-13 | Legacy archivado | `migrations/archived/` | VERIFICADO | 2 archivos |
| AC-14 | infra/ssl | `openssl x509` | VERIFICADO | Cert local |
| AC-15 | fernet.key | `ls fernet.key` | VERIFICADO | 44 bytes |
| AC-16 | healthz nginx | `location = /healthz` | VERIFICADO | Estático |
| AC-17 | Guardian quarantined | `scripts/archived/guardian/` | VERIFICADO | 6 entradas |
| AC-18 | Credenciales fuertes staging | `.env.example` + compose | PARCIAL | Código OK; staging no desplegado |
| AC-19 | SSRF IP pinning | `_PinnedDNS` + 28 tests | VERIFICADO | — |
| AC-20 | Auditoría persistente | `test_audit_persistence.py` | VERIFICADO | 3 tests |
| AC-21 | Crypto labels honestos | `fernet-aes128-cbc-hmac-sha256` | VERIFICADO | Sin pqcrypto |
| AC-22 | Security suites + coverage 80 % | pytest + `pytest-cov` | VERIFICADO | 88% en 6 módulos de seguridad; backend completo ~73%, no al 80% |
| AC-23 | Dashboards | 7 JSON | PARCIAL | Estático, sin runtime |
| AC-24 | Alertmanager + alertas | 8 reglas | PARCIAL | Estático, sin runtime |
| AC-25 | `flutter analyze` 0 + `flutter test` | Flutter 3.24.5 | VERIFICADO | 0 errores; 11 tests |
| AC-26 | Docs regenerados + coherencia | este paquete + verificación | EN CURSO | TASK-045/046 |

### 6.1 Resumen

| Estado | AC |
| :--- | ---: |
| VERIFICADO | 22 |
| PARCIAL | 3 (AC-18, AC-23, AC-24) |
| FALLA | 0 |
| EN CURSO | 1 (AC-26) |
| NO VERIFICADO | 0 |

> El SPEC marca AC-01..AC-07 y AC-18..AC-26 como `[ ]` pese a tener evidencia. Esta tabla corrige la discrepancia; la actualización del SPEC corresponde al orquestador, no a este documento.

---

## 7. Gates de calidad

### 7.1 Gate de tarea

Una tarea se marca `[x]` sólo si:

1. El código compila/importa.
2. Los tests relevantes pasan.
3. El AC asociado tiene evidencia reproducible.
4. No introduce hallazgos CRITICAL/HIGH.
5. La documentación afectada se actualiza.

### 7.2 Gate de fase

| Fase | Gate |
| :--- | :--- |
| FASE 2 | pytest verde + AC-08..17 + validate_all |
| FASE 3 | 0 CRITICAL/HIGH + re-run adversarial |
| FASE 5 | Suites nuevas + validate_all |
| FASE 6 | Dashboards + alertas + `/metrics` |
| FASE 7 | `flutter analyze` 0 + `flutter test` |
| FASE 9 | 8 docs + coherencia |

### 7.3 Gate de release

| Condición | Obligatoria |
| :--- | :---: |
| pytest 100 % verde | Sí |
| `validate_all.py` VALIDATED | Sí |
| 0 CRITICAL/HIGH abiertos | Sí |
| Cobertura de las 6 suites de seguridad ≥ 80% | Sí (88%) |
| Cobertura del backend completo ≥ 80% | No (≈73%, sin umbral) |
| Frontend build Next 16 OK | Sí (verificado en copia) |
| Móvil analyze 0 / test verde | Sí (0 errores / 11 tests) |
| Docker smoke test | Sí (**bloqueado**) |
| Observabilidad verificada | Sí (**bloqueado**) |
| Documentación coherente | Sí (en curso) |

---

## 8. Evidencia y artefactos

| Artefacto | Ruta | Contenido |
| :--- | :--- | :--- |
| Reporte de validación | `reports/validation.json` | Commit, tests, seguridad, features, status |
| Salida de pytest | efímera | 157 passed, 1906 warnings |
| Cobertura | `backend/.coverage` | 88% en 6 módulos de seguridad; ~73% backend completo |
| SCA | `docs/security/SCA_ALLOWLIST.md` | `pip-audit` 0 |
| Contrato | `backend/contracts/openapi.json` | 168 paths |
| Dashboards | `infra/grafana/provisioning/dashboards/*.json` | 7 |
| Alertas | `infra/alertmanager/alerts.yml` | 8 |
| Documentación | `docs/*.md` | Este paquete |
| Estado de tareas | `.factory/TASKS.md` | 41/46 |

### 8.1 Formato de evidencia exigido

Toda tarea debe registrar:

```text
Comando: <comando exacto>
Resultado: <salida literal o resumen>
Exit code: <0|1>
Fecha: <ISO>
Limitación: <si aplica>
```

Sin esto, la tarea no es verificable.

---

## 9. Procedimiento de regresión

### 9.1 Antes de cada commit

```bash
SECRET_KEY="test-secret-key-32-chars-minimum!!!" python3 -m pytest backend/tests -q
python3 scripts/validate_all.py
```

### 9.2 Antes de cada release

```bash
# Backend
python3 -m compileall -q backend
SECRET_KEY="test-secret-key-32-chars-minimum!!!" python3 -m pytest backend/tests -q
python3 scripts/validate_all.py

# Frontend
cd frontend && npm ci && npx tsc --noEmit && npm run build

# Móvil
cd mobile/sesis_cop && flutter analyze && flutter test

# Infra
docker compose config
docker compose up -d --build
docker compose ps

# Humo
curl -sk https://localhost/healthz
curl -s http://localhost:8000/api/v1/health
curl -s http://localhost:8000/metrics | head
```

### 9.3 Criterio de bloqueo

Si falla cualquiera de los pasos obligatorios, no se libera. Se registra en `ENGINEERING_RISKS.md` y se abre tarea de remediación.

---

## 10. Procedimiento de fallo y reintento

| Intento | Acción |
| :--- | :--- |
| 1 | Diagnóstico del stack trace; corrección mínima |
| 2 | Revisión de causa raíz; test de regresión |
| 3 | Si persiste, `[!]` y ADR de replanteo |
| 3/3 | `@architect` replanifica; no se insiste a ciegas |

Regla: nunca se modifica un test para que pase si el comportamiento es incorrecto. Un test que oculta un fallo es peor que no tenerlo.

---

## 11. Pruebas de seguridad específicas

### 11.1 SSRF

| Caso | Esperado | Test |
| :--- | :--- | :--- |
| `http://127.0.0.1` | Bloqueo | `test_rejects_private_ip_127` |
| `http://10.0.0.1` | Bloqueo | `test_rejects_private_ip_10` |
| `http://192.168.1.1` | Bloqueo | `test_rejects_private_ip_192_168` |
| `http://169.254.169.254` | Bloqueo | `test_rejects_metadata_hostname` |
| IP pública | Permiso | `test_accepts_public_ip` |
| DNS rebinding | Permiso sólo a IP validada | `test_pinned_dns_returns_validated_ip` |
| IPv6 loopback | Bloqueo | `test_rejects_ipv6_loopback` |
| IPv6 ULA | Bloqueo | `test_rejects_ipv6_unique_local` |
| IPv4-mapped | Bloqueo | `test_rejects_ipv4_mapped_ipv6_loopback` |

### 11.2 Autenticación

| Caso | Esperado | Test |
| :--- | :--- | :--- |
| Login correcto | 200 + tokens | `test_auth.py` |
| Password incorrecta | 401 | `test_auth.py` |
| Refresh rotado | 200 + nuevo par | `test_auth.py` |
| Refresh reutilizado | 401 | `test_auth.py` |
| MFA como bearer | 401 | `test_mfa_security.py` |
| Sin token | 401 | `test_clearance_enforcement.py` |

### 11.3 Clearance

| Caso | Esperado | Test |
| :--- | :--- | :--- |
| Nivel suficiente | 200 | `test_clearance_enforcement.py` |
| Nivel insuficiente | 403 | `test_clearance_enforcement.py` |
| Ruta v1 sin clearance | 0 offenders | `test_v1_clearance_matrix.py` |
| Media montado sin clearance | 0 | `test_media_dead_router_not_exposed` |

### 11.4 Auditoría

| Caso | Esperado | Test |
| :--- | :--- | :--- |
| Cadena válida | `verify_chain` True | `test_audit_persistence.py` |
| Hash alterado | False | `test_audit_persistence.py` |
| Orden alterado | False | `test_audit_persistence.py` |
| 10 tareas concurrentes | Cadena válida | `test_audit_persistence.py` |

### 11.5 Rate limit

| Caso | Esperado | Test |
| :--- | :--- | :--- |
| Límite excedido | 429 | `test_rate_limit.py` |
| Path login vs MFA | Aislamiento | `test_rate_limit.py` |
| Estado visible entre workers | Sí | `TestDistributedBruteForce` |
| Éxito resetea | Sí | `test_rate_limit.py` |

---

## 12. Pruebas de contrato y datos

### 12.1 Contrato

| Caso | Esperado | Test |
| :--- | :--- | :--- |
| Archivo existe | Sí | `test_contract_openapi_file_exists` |
| Mínimo de paths | ≥ umbral | `test_contract_openapi_has_minimum_paths` |
| JSON válido | Sí | `test_contract_openapi_is_valid` |
| App con rutas | ≥ umbral | `test_app_has_minimum_routes` |
| v1 ⊆ app viva | Sí | `test_contract_v1_paths_in_live_app` |

### 12.2 Datos

| Caso | Esperado | Estado |
| :--- | :--- | :--- |
| Migración 001..004 aplica | `alembic upgrade head` | BLOQUEADO |
| User único | 1 tabla | VERIFICADO |
| AuditLog único | 1 tabla | VERIFICADO |
| FK OSINT → User | correcta | VERIFICADO (código) |
| Índices | existen | NO VERIFICADO (runtime) |

---

## 13. Pruebas de frontend (propuesta)

| Caso | Herramienta | Estado |
| :--- | :--- | :--- |
| Login renderiza | Testing Library | NO IMPLEMENTADO |
| Error de login visible | Testing Library | NO IMPLEMENTADO |
| Loading de COP | Testing Library | NO IMPLEMENTADO |
| Empty state | Testing Library | NO IMPLEMENTADO |
| Error state + retry | Testing Library | NO IMPLEMENTADO |
| Navegación `/` → `/login` | Playwright | NO IMPLEMENTADO |
| Responsive 375/768/1440 | Playwright | NO IMPLEMENTADO |
| Accesibilidad | axe | NO IMPLEMENTADO |

---

## 14. Pruebas de móvil (propuesta)

| Caso | Herramienta | Estado |
| :--- | :--- | :--- |
| Login | flutter test | NO IMPLEMENTADO |
| Navegación | flutter test | NO IMPLEMENTADO |
| Cola offline | flutter test | PARCIAL (flujo cubierto por tests de protocolo) |
| Duress borra datos | flutter test | NO IMPLEMENTADO |
| Mesh protocol | flutter test | VERIFICADO (11 tests) |
| Mesh en dispositivos | integración | NO VERIFICADO |

---

## 15. Pruebas de infraestructura

| Caso | Comando | Estado |
| :--- | :--- | :--- |
| Compose válido | `docker compose config` | BLOQUEADO |
| 12 servicios | `docker compose ps` | BLOQUEADO |
| 12 healthy | `docker compose ps` | BLOQUEADO |
| API responde | `curl /api/v1/health` | BLOQUEADO |
| Nginx TLS | `curl -k https://localhost` | BLOQUEADO |
| Healthz | `curl /healthz` | BLOQUEADO |
| Métricas | `curl /metrics` | BLOQUEADO |
| Prometheus targets | `curl :9090/api/v1/targets` | BLOQUEADO |
| Alertmanager | `curl :9093/-/healthy` | BLOQUEADO |
| Grafana | `curl :3001/api/health` | BLOQUEADO |

---

## 16. Criterios de salida por fase

### FASE 7 (móvil)

- [x] `flutter analyze` → `No issues found!`
- [x] `flutter test` → 11 passed
- [x] Cola offline implementada (`offline_queue.dart`, 138 LOC)
- [x] `CardThemeData` → `CardTheme`

### FASE 9 (docs)

- [x] 8 documentos regenerados
- [x] Cifras con comando
- [x] Veredictos con evidencia
- [ ] Verificación de coherencia docs↔código (TASK-046)

### Cierre de release

- [ ] Todos los AC en VERIFICADO
- [ ] 0 CRITICAL/HIGH
- [ ] Docker smoke test
- [x] Cobertura de seguridad medida (88%)
- [x] Móvil compilando y con tests

---

## 17. Riesgos del propio plan

| Riesgo | Impacto | Mitigación |
| :--- | :--- | :--- |
| Tests con dobles dan falsa confianza | Alto | Añadir integración real |
| Cobertura global no fijada | Medio | Añadir umbral global además del 88% de seguridad |
| No probar Docker | Alto | Host con Docker en CI |
| No probar frontend | Medio | Añadir Node al CI |
| Mesh móvil sin dispositivos | Medio | Matriz de dispositivos / integración |
| Warnings ignorados | Medio | `-W error` selectivo |
| Documentos se desactualizan | Medio | Regenerar por fase |

---

## 18. Conclusión

El plan es exigente donde importa: seguridad, contrato, autorización, auditoría y móvil tienen pruebas reales. Sigue siendo débil donde el entorno no alcanza: Docker, PostgreSQL y frontend.

La validación actual permite afirmar con evidencia:

- El backend importa y pasa 157 tests.
- Los controles de seguridad principales funcionan.
- El contrato tiene 168 paths y no se aleja de la app.
- El móvil compila (`No issues found!`) y pasa 11 tests.
- La cobertura de las 6 suites de seguridad es 88%; el backend completo no está medido al 80% (~73%).
- El frontend Next 16 compila y pasa `tsc`/`next build` con 0 vulnerabilidades de producción.
- La infraestructura **no** se ha ejecutado (Docker ausente).

Eso es suficiente para un estado honesto de FASE 9. No es suficiente para un release.
