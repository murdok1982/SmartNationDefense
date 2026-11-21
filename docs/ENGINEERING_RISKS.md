# ENGINEERING_RISKS.md — Registro de riesgos de ingeniería

**Doc ID:** RISK-2026-SND-001
**Proyecto:** SmartNationDefense / SESIS-FEDERATION
**Fecha:** 2026-11-21
**Base:** `docs/ARCHITECTURE_CURRENT.md`, `docs/AUDIT.md`, `docs/FEATURE_MATRIX.md`, `docs/FINAL_VALIDATION_REPORT.md`
**Autor:** `@architect`
**Revisión:** FASE 9

> Un riesgo no es un fallo: es algo que **puede** ocurrir y cuyo impacto merece una decisión. Este registro sólo incluye riesgos con evidencia en el repositorio. No hay riesgos genéricos de "la IA puede fallar".

---

## 1. Metodología

### 1.1 Escala de probabilidad

| Valor | Etiqueta | Criterio |
| ---: | :--- | :--- |
| 5 | Casi seguro | Ya ocurre o se reproduce en cada ejecución |
| 4 | Probable | Ocurre en condiciones normales |
| 3 | Posible | Ocurre en algunas condiciones |
| 2 | Improbable | Requiere condiciones específicas |
| 1 | Raro | Requiere una combinación excepcional |

### 1.2 Escala de impacto

| Valor | Etiqueta | Criterio |
| ---: | :--- | :--- |
| 5 | Crítico | Pérdida de datos, brecha de seguridad, producto inutilizable |
| 4 | Alto | Funcionalidad clave no entregada, incumplimiento |
| 3 | Medio | Degradación, deuda que frena el roadmap |
| 2 | Bajo | Molestia operativa |
| 1 | Mínimo | Cosmético |

### 1.3 Severidad

`Severidad = Probabilidad × Impacto`

| Rango | Nivel | Acción |
| :--- | :--- | :--- |
| 20–25 | CRÍTICO | Mitigación inmediata; bloquea release |
| 12–19 | ALTO | Plan obligatorio antes de release |
| 6–11 | MEDIO | Plan en el ciclo |
| 1–5 | BAJO | Aceptar y revisar |

### 1.4 Estados

| Estado | Significado |
| :--- | :--- |
| `ABIERTO` | Sin mitigación aplicada |
| `EN MITIGACIÓN` | Hay trabajo en curso |
| `MITIGADO` | Control aplicado y verificado |
| `ACEPTADO` | Se decide convivir con el riesgo |
| `CERRADO` | Ya no aplica |

---

## 2. Mapa de calor

| Probabilidad \ Impacto | 1 | 2 | 3 | 4 | 5 |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **5** | — | — | R-017 | — | R-001 |
| **4** | — | R-012, R-013 | R-018 | R-003, R-008 | R-004 |
| **3** | — | — | R-009, R-014, R-015, R-021, R-022, R-024 | R-006, R-007, R-011 | — |
| **2** | — | R-005, R-016, R-020 | — | R-019 | — |
| **1** | — | R-002, R-010, R-023 | — | — | — |

| Zona | Riesgos |
| :--- | :--- |
| Crítico (20–25) | R-001, R-004 |
| Alto (12–19) | R-003, R-006, R-007, R-008, R-011, R-017, R-018 |
| Medio (6–11) | R-009, R-012, R-013, R-014, R-015, R-019, R-021, R-022, R-024 |
| Bajo (1–5) | R-002, R-005, R-010, R-016, R-020, R-023 |

---

## 3. Registro de riesgos

### R-001 — Stubs de API presentados como funcionalidad

| Campo | Valor |
| :--- | :--- |
| Categoría | Producto / Veracidad |
| Probabilidad | 5 (ocurre hoy) |
| Impacto | 5 (decisiones y demos sobre capacidades inexistentes) |
| Severidad | **25 — CRÍTICO** |
| Estado | ABIERTO |
| Evidencia | `api/osint/router.py` devuelve listas vacías; `api/satellite/router.py` devuelve `queued`; `api/intel/router.py` listas vacías; `api/agents/*` estado fijo |
| Afecta | OSINT, Intel, Satellite, Agents, frontend, documentación |
| Disparador | Un cliente o evaluador usa OpenAPI y espera datos |
| Consecuencia | Pérdida de credibilidad; integraciones que fallan en silencio |
| Mitigación | Montar routers reales o retirarlos del OpenAPI público; marcar `deprecated` si se mantienen |
| Plan | FASE 10 propuesta: decidir por dominio, implementar o despublicar |
| Responsable | `@architect` (decisión) + `@builder` (implementación) |
| Verificación de cierre | Tests de integración que devuelvan datos reales, no `[]` |

### R-002 — Build móvil (mitigado)

| Campo | Valor |
| :--- | :--- |
| Categoría | Entrega |
| Probabilidad | 1 (residual) |
| Impacto | 2 (mesh en dispositivos no probado) |
| Severidad | **2 — BAJO** |
| Estado | MITIGADO |
| Evidencia | `flutter analyze` → `No issues found!`; `flutter test` → 11 passed; `offline_queue.dart` implementado |
| Afecta | `mobile/sesis_cop`, offline-first, duress, mesh |
| Disparador | Cambio de SDK o regresión |
| Consecuencia | Build roto si no se fija Flutter en CI |
| Mitigación | Flutter 3.24.5 fijado; tests en CI |
| Plan | FASE 7 cerrada |
| Responsable | `@builder` + `@qa-verifier` |
| Verificación de cierre | `flutter analyze` 0 y `flutter test` 11 |

### R-003 — Docker nunca ejecutado

| Campo | Valor |
| :--- | :--- |
| Categoría | Despliegue |
| Probabilidad | 4 (no hay Docker en el entorno) |
| Impacto | 4 (no hay evidencia de arranque) |
| Severidad | **16 — ALTO** |
| Estado | ABIERTO |
| Evidencia | `which docker` vacío; compose validado sólo con YAML |
| Afecta | 12 servicios, nginx, migraciones, healthchecks |
| Disparador | Primer despliegue real |
| Consecuencia | Fallos de red, volúmenes, dependencias o migraciones no detectados |
| Mitigación | Ejecutar `docker compose config`, `up -d`, `ps`, smoke tests en host/CI |
| Plan | FASE 13 propuesta |
| Responsable | DevOps / `@builder` |
| Verificación de cierre | 12/12 healthy y smoke tests verdes |

### R-004 — Auditoría adversarial sin cierre formal

| Campo | Valor |
| :--- | :--- |
| Categoría | Seguridad / Gobernanza |
| Probabilidad | 4 (TASK-029/030 abiertas) |
| Impacto | 5 (Exit Gate exige 0 CRITICAL/HIGH) |
| Severidad | **20 — CRÍTICO** |
| Estado | ABIERTO |
| Evidencia | `TASKS.md` TASK-029/030 pendientes; `.factory/SECURITY_AUDIT.md` en reescritura |
| Afecta | Release, compliance |
| Disparador | Gate de release |
| Consecuencia | No se puede declarar producción |
| Mitigación | Completar re-run adversarial, registrar hallazgos y remediaciones |
| Plan | FASE 3 cierre |
| Responsable | `@redteam-auditor` + `@qa-verifier` |
| Verificación de cierre | Informe firmado con 0 CRITICAL/HIGH abiertos |

### R-005 — Cobertura global no fijada

| Campo | Valor |
| :--- | :--- |
| Categoría | Calidad |
| Probabilidad | 2 |
| Impacto | 2 |
| Severidad | **4 — BAJO** |
| Estado | MITIGADO (suites de seguridad) |
| Evidencia | `pytest-cov` → **88%** en 6 módulos de seguridad; backend completo ≈73%, sin umbral 80% |
| Afecta | Backend |
| Disparador | Cambio en código no cubierto |
| Consecuencia | Regresiones fuera de las suites de seguridad |
| Mitigación | Fijar umbral global y por módulo |
| Plan | FASE 12 propuesta |
| Responsable | `@qa-verifier` |
| Verificación de cierre | Reporte global con umbral |

### R-006 — IDOR / autorización por recurso no sistemática

| Campo | Valor |
| :--- | :--- |
| Categoría | Seguridad |
| Probabilidad | 3 (hay controles parciales) |
| Impacto | 4 (acceso a datos ajenos) |
| Severidad | **12 — ALTO** |
| Estado | ABIERTO |
| Evidencia | No hay patrón uniforme de ownership; no hay tests de acceso cruzado |
| Afecta | Recursos con `id` (assets, AAR, reports, messages) |
| Disparador | Usuario autenticado con ID ajeno |
| Consecuencia | Lectura/escritura indebida |
| Mitigación | Revisar cada handler con recurso; añadir tests de 403/404 |
| Plan | FASE 10/11 |
| Responsable | `@redteam-auditor` + `@builder` |
| Verificación de cierre | Tests de IDOR por recurso |

### R-007 — Lock de auditoría no distribuido

| Campo | Valor |
| :--- | :--- |
| Categoría | Integridad |
| Probabilidad | 3 (si hay >1 réplica) |
| Impacto | 4 (cadena inconsistente) |
| Severidad | **12 — ALTO** |
| Estado | ABIERTO |
| Evidencia | `asyncio.Lock` en `AuditChain`; sin `SELECT FOR UPDATE` |
| Afecta | `audit_log`, cumplimiento |
| Disparador | Dos instancias escribiendo a la vez |
| Consecuencia | `prev_hash` divergente; `verify_chain` falla |
| Mitigación | Bloqueo DB/Redis distribuido; una sola ruta de escritura |
| Plan | Antes de escalar a >1 réplica |
| Responsable | `@architect` + `@builder` |
| Verificación de cierre | Test con dos procesos/conexiones |

### R-008 — `MFA_CHALLENGE_SECRET` con fallback a `SECRET_KEY`

| Campo | Valor |
| :--- | :--- |
| Categoría | Seguridad / Configuración |
| Probabilidad | 4 (warning en tests) |
| Impacto | 4 (aislamiento de ticket debilitado) |
| Severidad | **16 — ALTO** |
| Estado | EN MITIGACIÓN |
| Evidencia | 1906 warnings: `MFA_CHALLENGE_SECRET no esta configurado` |
| Afecta | MFA, aislamiento de tokens |
| Disparador | Entorno sin la variable |
| Consecuencia | Un token de un contexto podría reutilizarse en otro si se compromete la clave |
| Mitigación | Exigir `MFA_CHALLENGE_SECRET` en producción (validador) y generarlo en `.env` |
| Plan | FASE 3/10 |
| Responsable | `@builder` |
| Verificación de cierre | Test que falle si la variable falta en producción |

### R-009 — Dos escalas de clasificación

| Campo | Valor |
| :--- | :--- |
| Categoría | Corrección |
| Probabilidad | 3 |
| Impacto | 3 |
| Severidad | **9 — MEDIO** |
| Estado | ABIERTO |
| Evidencia | `classification.py` (minúsculas) vs `security.CLEARANCE_ORDER` (mayúsculas) |
| Afecta | Autorización, etiquetado |
| Disparador | Uso de la escala equivocada |
| Consecuencia | Comparaciones incorrectas |
| Mitigación | Fuente única + test de equivalencia |
| Plan | FASE 10 |
| Responsable | `@architect` |
| Verificación de cierre | Test que mapea ambas escalas |

### R-010 — Lockfile móvil desalineado con el SDK

| Campo | Valor |
| :--- | :--- |
| Categoría | Build |
| Probabilidad | 1 |
| Impacto | 2 |
| Severidad | **2 — BAJO** |
| Estado | MITIGADO |
| Evidencia | Lock alineado con Flutter 3.24.5; `flutter analyze` 0 |
| Afecta | Reproducibilidad del build móvil |
| Disparador | `flutter pub get` con otro SDK |
| Consecuencia | Builds distintos |
| Mitigación | Fijar Flutter 3.24.5 en CI |
| Plan | FASE 7 |
| Responsable | `@builder` |
| Verificación de cierre | `flutter pub get --enforce-lockfile` OK |

### R-011 — Hardening de producción depende de variables correctas

| Campo | Valor |
| :--- | :--- |
| Categoría | Configuración |
| Probabilidad | 3 |
| Impacto | 4 |
| Severidad | **12 — ALTO** |
| Estado | MITIGADO (en código) |
| Evidencia | `validate_production_hardening` |
| Afecta | Arranque en producción |
| Disparador | `.env` incompleto |
| Consecuencia | El servicio no arranca (fail-fast, correcto) o arranca mal si se salta |
| Mitigación | Validador + documentación + tests |
| Plan | Mantener |
| Responsable | `@architect` |
| Verificación de cierre | Test de arranque con env débil → error |

### R-012 — Falta de paginación uniforme

| Campo | Valor |
| :--- | :--- |
| Categoría | Escalabilidad |
| Probabilidad | 4 |
| Impacto | 2 |
| Severidad | **8 — MEDIO** |
| Estado | ABIERTO |
| Evidencia | Listados devuelven todo |
| Afecta | C2, assets, reports |
| Disparador | Muchos registros |
| Consecuencia | Latencia y memoria |
| Mitigación | `limit`/`offset` + total |
| Plan | FASE 11 |
| Responsable | `@builder` |
| Verificación de cierre | Tests de paginación |

### R-013 — `/metrics` expuesto sin autenticación

| Campo | Valor |
| :--- | :--- |
| Categoría | Seguridad / Información |
| Probabilidad | 4 |
| Impacto | 2 |
| Severidad | **8 — MEDIO** |
| Estado | ABIERTO |
| Evidencia | `/metrics` sin dependencia de auth |
| Afecta | Reconocimiento |
| Disparador | Acceso directo al puerto 8000 |
| Consecuencia | Fuga de rutas y volúmenes |
| Mitigación | Restringir a red interna o auth |
| Plan | FASE 10 |
| Responsable | DevOps |
| Verificación de cierre | 401/403 desde red externa |

### R-014 — Doble prefijo `/api/v1` en el demo

| Campo | Valor |
| :--- | :--- |
| Categoría | Integración |
| Probabilidad | 3 |
| Impacto | 3 |
| Severidad | **9 — MEDIO** |
| Estado | ABIERTO |
| Evidencia | `docker-compose.demo.yml` define `NEXT_PUBLIC_API_URL=https://localhost/api/v1`; `api.ts` añade `/api/v1` en endpoints |
| Afecta | Demo frontend |
| Disparador | Uso del compose demo |
| Consecuencia | 404 en llamadas |
| Mitigación | Base sin `/api/v1` o cliente que no lo añada |
| Plan | FASE 9/10 |
| Responsable | `@builder` |
| Verificación de cierre | Smoke test de login en demo |

### R-015 — Prompt injection en LLM

| Campo | Valor |
| :--- | :--- |
| Categoría | Seguridad IA |
| Probabilidad | 3 |
| Impacto | 3 |
| Severidad | **9 — MEDIO** |
| Estado | ABIERTO |
| Evidencia | Sin validación específica de entrada/salida |
| Afecta | Briefings, análisis, chat |
| Disparador | Contenido externo malicioso |
| Consecuencia | Salida manipulada; fuga de contexto |
| Mitigación | Sanitización, límites, instrucciones de sistema, validación de salida |
| Plan | FASE 10 |
| Responsable | `@architect` |
| Verificación de cierre | Tests de inyección conocidos |

### R-016 — Dependencias y SCA

| Campo | Valor |
| :--- | :--- |
| Categoría | Cadena de suministro |
| Probabilidad | 2 |
| Impacto | 2 |
| Severidad | **4 — BAJO** |
| Estado | MITIGADO (backend) / EN MITIGACIÓN (frontend) |
| Evidencia | `pip-audit` 0 con allowlist; `npm audit --omit=dev` 0; CI bloqueante; residual dev `brace-expansion` (eslint) |
| Afecta | Backend, frontend |
| Disparador | CVE en dependencia o allowlist caducada |
| Consecuencia | Vulnerabilidad conocida en producción |
| Mitigación | Revisión periódica de allowlist y parches |
| Plan | FASE 12/14 |
| Responsable | DevOps |
| Verificación de cierre | CI falla con CVE alto y `npm audit` limpio |

### R-017 — Persistencia en memoria en dominios clave

| Campo | Valor |
| :--- | :--- |
| Categoría | Datos |
| Probabilidad | 5 (ocurre hoy) |
| Impacto | 3 |
| Severidad | **15 — ALTO** |
| Estado | ABIERTO |
| Evidencia | `reports_service._reports`, `messaging_service`, `aar_service` usan `Dict` |
| Afecta | AAR, reportes, mensajería, planning |
| Disparador | Reinicio del proceso |
| Consecuencia | Pérdida de datos |
| Mitigación | Tablas + repositorios |
| Plan | FASE 11 |
| Responsable | `@builder` |
| Verificación de cierre | Test de persistencia tras reinicio |

### R-018 — Observabilidad sin operar

| Campo | Valor |
| :--- | :--- |
| Categoría | Operaciones |
| Probabilidad | 4 |
| Impacto | 3 |
| Severidad | **12 — ALTO** |
| Estado | ABIERTO |
| Evidencia | No hay scrape real; `sesis_module_up` es snapshot |
| Afecta | Diagnóstico, alertas |
| Disparador | Incidente en producción |
| Consecuencia | Detección tardía |
| Mitigación | Smoke test de Prometheus/Grafana; healthchecks activos |
| Plan | FASE 13 |
| Responsable | DevOps |
| Verificación de cierre | Targets UP y alerta de prueba disparada |

### R-019 — Secretos en filesystem

| Campo | Valor |
| :--- | :--- |
| Categoría | Seguridad |
| Probabilidad | 2 |
| Impacto | 4 |
| Severidad | **8 — MEDIO** |
| Estado | ACEPTADO (con controles) |
| Evidencia | `fernet.key` local, montado `:ro` |
| Afecta | Cifrado |
| Disparador | Acceso al host |
| Consecuencia | Descifrado de campos |
| Mitigación | KMS/HSM, permisos, rotación |
| Plan | FASE 12 |
| Responsable | `@architect` |
| Verificación de cierre | Clave en secret manager |

### R-020 — `WebAuthn` declarado pero no implementado

| Campo | Valor |
| :--- | :--- |
| Categoría | Producto |
| Probabilidad | 2 |
| Impacto | 2 |
| Severidad | **4 — BAJO** |
| Estado | ABIERTO |
| Evidencia | Endpoint devuelve 501; modelo placeholder |
| Afecta | MFA avanzado |
| Disparador | Cliente que intente WebAuthn |
| Consecuencia | Error claro (501), no engaña |
| Mitigación | Documentar como no soportado o implementar |
| Plan | FASE 10 |
| Responsable | `@builder` |
| Verificación de cierre | Documento y contrato coherentes |

### R-021 — SEC-FIX-007 (MEDIUM) abierto

| Campo | Valor |
| :--- | :--- |
| Categoría | Seguridad |
| Probabilidad | 3 |
| Impacto | 3 |
| Severidad | **9 — MEDIO** |
| Estado | ABIERTO |
| Evidencia | Auditoría adversarial en curso; TASK-029/030 pendientes |
| Afecta | Gate de release |
| Disparador | Cierre de auditoría |
| Consecuencia | No se puede declarar 0 MEDIUM |
| Mitigación | Remediar y verificar con test |
| Plan | FASE 3 cierre |
| Responsable | `@redteam-auditor` + `@builder` |
| Verificación de cierre | Hallazgo cerrado con evidencia |

### R-022 — SEC-FIX-008 (MEDIUM) abierto

| Campo | Valor |
| :--- | :--- |
| Categoría | Seguridad |
| Probabilidad | 3 |
| Impacto | 3 |
| Severidad | **9 — MEDIO** |
| Estado | ABIERTO |
| Evidencia | Auditoría adversarial en curso |
| Afecta | Gate de release |
| Disparador | Cierre de auditoría |
| Consecuencia | No se puede declarar 0 MEDIUM |
| Mitigación | Remediar y verificar con test |
| Plan | FASE 3 cierre |
| Responsable | `@redteam-auditor` + `@builder` |
| Verificación de cierre | Hallazgo cerrado con evidencia |

### R-023 — Build de Next 16.4.6 + React 19

| Campo | Valor |
| :--- | :--- |
| Categoría | Frontend |
| Probabilidad | 1 |
| Impacto | 2 |
| Severidad | **2 — BAJO** |
| Estado | MITIGADO |
| Evidencia | Copia limpia con Node 20.18: `npm ci` OK, `tsc` 0 errores, `next build` OK (4 rutas), `npm audit --omit=dev --audit-level=high` → 0 |
| Afecta | Web COP |
| Disparador | Cambios breaking futuros de Next/React |
| Consecuencia | Build roto en una actualización posterior |
| Mitigación | Build reproducible en CI; lockfile |
| Plan | FASE 14 cerrada |
| Responsable | `@builder` + `@ui-artisan` |
| Verificación de cierre | `tsc` 0, `next build` OK, 4 rutas, 0 vulnerabilidades prod |
| Residual | Advisory dev de `brace-expansion` vía eslint (no producción) |

### R-024 — Advisories de Starlette aceptadas con allowlist

| Campo | Valor |
| :--- | :--- |
| Categoría | Cadena de suministro |
| Probabilidad | 3 |
| Impacto | 3 |
| Severidad | **9 — MEDIO** |
| Estado | ACEPTADO |
| Evidencia | `pip-audit` 0 con allowlist; plan FastAPI ≥ 0.165 |
| Afecta | Backend |
| Disparador | CVE explotable en la versión fijada |
| Consecuencia | Riesgo aceptado temporalmente |
| Mitigación | Upgrade FastAPI/Starlette y retirar allowlist |
| Plan | FASE 12/14 |
| Responsable | `@architect` + DevOps |
| Verificación de cierre | Allowlist vacía y `pip-audit` 0 |

---

## 4. Top 5 riesgos

| # | Riesgo | Severidad | Por qué es top |
| ---: | :--- | :--- | :--- |
| 1 | R-001 — Stubs | 25 | Afecta la verdad del producto y todas las decisiones |
| 2 | R-004 — Auditoría sin cierre | 20 | Bloquea el gate de release |
| 3 | R-003 — Docker no probado | 16 | No hay evidencia de que arranque |
| 4 | R-008 — MFA secret fallback | 16 | Debilita un control de seguridad |
| 5 | R-017 — Persistencia en memoria | 15 | Pérdida de datos en dominios clave |

---

## 5. Distribución por severidad

| Nivel | Cantidad | Riesgos |
| :--- | ---: | :--- |
| CRÍTICO (20–25) | 2 | R-001 (25), R-004 (20) |
| ALTO (12–19) | 7 | R-003 (16), R-006 (12), R-007 (12), R-008 (16), R-011 (12), R-017 (15), R-018 (12) |
| MEDIO (6–11) | 9 | R-009 (9), R-012 (8), R-013 (8), R-014 (9), R-015 (9), R-019 (8), R-021 (9), R-022 (9), R-024 (9) |
| BAJO (1–5) | 6 | R-002 (2), R-005 (4), R-010 (2), R-016 (4), R-020 (4), R-023 (2) |
| **Total** | **24** | |

---

## 6. Riesgos aceptados

| Riesgo | Motivo de aceptación | Condición de revisión |
| :--- | :--- | :--- |
| R-019 (secretos en FS) | Despliegue single-host, clave `:ro`, sin KMS disponible | Al pasar a multi-host o cloud |
| Rate limit fail-open en desarrollo | En staging/prod `SECURITY_FAIL_MODE=closed`; sólo dev mantiene fail-open | Si se despliega dev a un entorno accesible |
| JDL heurístico | Se declara EXPERIMENTAL; no se usa para targeting real | Si se usa operativamente |
| MFA no montado | Trabajo en curso; no se anuncia en UI | Si se anuncia, pasa a R-001 |
| R-024 (Starlette allowlist) | `pip-audit` 0 con allowlist y plan FastAPI ≥ 0.165 | Si aparece exploit o vence la allowlist |

> "Aceptado" no significa "ignorado". Cada riesgo aceptado tiene una condición que lo reabre.

---

## 7. Riesgos emergentes (vigilancia)

| Riesgo | Señal temprana | Acción preventiva |
| :--- | :--- | :--- |
| Saturación de SQLite en tests | Tests lentos o bloqueos | Migrar a PostgreSQL en CI |
| Deriva del contrato | `test_contracts` falla | Regenerar OpenAPI |
| Crecimiento de warnings | > 600 | `-W error` selectivo |
| Aumento de superficie API | Nuevos paths sin tests | Gate de contrato |
| Dependencias sin mantenimiento | `pip check`/`npm outdated` | Revisión trimestral |
| Coste de `torch` | Imagen > 5 GB | Imagen separada para ML |
| Complejidad de `services/osint` | 36 archivos sin API | Decidir montar o archivar |

---

## 8. Plan de mitigación por horizonte

### 8.1 Inmediato (antes de cualquier demo)

| Acción | Riesgo | Esfuerzo |
| :--- | :--- | :--- |
| Marcar stubs como `deprecated` en OpenAPI | R-001 | Bajo |
| Documentar estado real en README | R-001 | Bajo |
| Corregir `NEXT_PUBLIC_API_URL` del demo | R-014 | Bajo |
| Restringir `/metrics` | R-013 | Bajo |

### 8.2 Corto plazo (FASE 7/9)

| Acción | Riesgo | Esfuerzo |
| :--- | :--- | :--- |
| ~~Implementar `offline_queue.dart`~~ | R-002 | HECHO |
| ~~Corregir `CardThemeData`~~ | R-002 | HECHO |
| Fijar Flutter 3.24.5 en CI | R-010 | Bajo |
| ~~Añadir `flutter test`~~ | R-002 | HECHO (11 tests) |
| Cerrar TASK-046 | R-001 | Bajo |

### 8.3 Medio plazo (FASE 10/11)

| Acción | Riesgo | Esfuerzo |
| :--- | :--- | :--- |
| Montar o despublicar OSINT/Intel/Satellite | R-001 | Alto |
| Montar o retirar MFA | R-008 | Medio |
| Persistir AAR/reports/messaging | R-017 | Alto |
| Tests de IDOR | R-006 | Medio |
| Unificar escalas | R-009 | Bajo |
| Bloqueo distribuido de auditoría | R-007 | Medio |
| Cerrar SEC-FIX-007/008 | R-021, R-022 | Medio |
| ~~Verificar build de Next 16.4.6 + React 19~~ | R-023 | HECHO |

### 8.4 Largo plazo (FASE 12/13)

| Acción | Riesgo | Esfuerzo |
| :--- | :--- | :--- |
| Cobertura global con umbral | R-005 | Medio |
| ~~`pip-audit` en CI~~ | R-016 | HECHO (0 con allowlist) |
| ~~`npm audit` limpio tras upgrade~~ | R-016, R-023 | HECHO (0 prod) |
| Revisar advisory dev `brace-expansion` | R-016 | Bajo |
| Docker smoke test | R-003 | Medio |
| Observabilidad operada | R-018 | Medio |
| KMS/HSM | R-019 | Alto |
| Prompt injection | R-015 | Medio |
| FastAPI ≥ 0.165 y retirar allowlist Starlette | R-024 | Medio |

---

## 9. Indicadores de vigilancia

| Indicador | Umbral | Riesgo asociado |
| :--- | :--- | :--- |
| Tests fallidos | > 0 | Todos |
| Warnings | > 1900 | R-008 |
| Paths sin test | > 20 % | R-005 |
| Rutas sin clearance | > 0 en v1/v3 | Seguridad |
| Alertas disparadas sin dueño | > 0 | R-018 |
| Cobertura de seguridad | < 80 % | R-005 |
| CVEs altos | > 0 con allowlist vigente | R-016 |
| SEC-FIX MEDIUM abiertos | > 0 | R-021, R-022 |
| Errores de `flutter analyze` | > 0 | R-002 |
| Tests móvil | < 11 | R-002 |
| Servicios unhealthy | > 0 | R-003 |
| Diferencias docs↔código | > 0 | R-001 |

---

## 10. Responsabilidades

| Rol | Riesgos principales |
| :--- | :--- |
| `@architect` | R-001, R-007, R-009, R-015, R-019, R-024 |
| `@builder` | R-002, R-010, R-012, R-014, R-017, R-021, R-022 |
| `@qa-verifier` | R-005, R-011, R-023 |
| `@redteam-auditor` | R-004, R-006, R-008, R-013, R-016, R-021, R-022, R-024 |
| DevOps | R-003, R-018, R-019 |
| Orquestador | Aceptación y priorización |

---

## 11. Revisión y gobernanza

| Aspecto | Regla |
| :--- | :--- |
| Frecuencia | Cada fase y antes de release |
| Entrada | Cambios de código, incidentes, auditorías |
| Salida | Registro actualizado + decisiones |
| Trazabilidad | Cada riesgo enlaza evidencia |
| Cierre | Sólo con verificación reproducible |
| Excepción | Un riesgo aceptado requiere firma del orquestador |

---

## 12. Conclusión

El proyecto no tiene un problema de arquitectura; tiene un problema de **completitud y veracidad**. Los riesgos más altos ya no son de build móvil ni de cobertura de seguridad —ambos cerrados—, sino de producto y despliegue: prometer lo que no se entrega y no haber ejecutado nunca el stack completo.

La buena noticia es que los riesgos están acotados y tienen mitigaciones concretas. La mala es que varios bloquean cualquier release y no se resuelven con documentación: requieren código y un entorno real.

Prioridad absoluta:

1. R-001 (stubs) y R-004 (auditoría SEC-FIX-007/008).
2. R-003 (Docker) y R-017 (persistencia en memoria).
3. R-008 (MFA fallback) y R-021/R-022 (SEC-FIX MEDIUM).

R-002 (móvil), R-005 (cobertura), R-010 (lockfile), R-016 (SCA) y R-023 (Next 16) están mitigados y se mantienen bajo vigilancia.
