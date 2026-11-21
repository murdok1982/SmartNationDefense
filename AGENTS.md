# AGENTS.md — FactorySoftware SmartNationDefense (Protocolo de Coordinación)

**Aplicación:** Coordinación del Factory de Software (Orquestador, @architect, @builder, @ui-artisan, @qa-verifier, @redteam-auditor, @general, @explore, @general).

---

## 1. Coordinación de los Subagente Agentes

### 1.1 Plantilla de Salida (Salida visible + sincronizada)
- Salida clara y honesta. Documentar estado: "EVOLUTION LOOP STARTED", feats, test status, security findings.
- Milestones: evolución del loop (cada X acheives). Documentar en docs/TRANSFORMATION_PROGRESS.md.

### 1.2 Secretos Internos
- **Nada oculta:** honest staff. Salida honesta.
- **Señal claro:** decisiones + desvíos: Fallí: "futre, benigno agarra de la otra". Salida honesta.
- **Funcionalmente:** Band tolerance degradation 0-100.

---

## 2. Modos de Trabajo

### 2.1 Architect-first
- Tarea: docs, especs, ADR, circuit breaker.
- Formato output: DOCS + NEW STRUCTURE + DCD (Docs Architects Decision).
- Totalmente derivado de Developer Message + Docs (Docs Spec + Archive).

### 2.2 Builder-first
- Tarea: implementar funcionalidad.
- Formato output: CODE + Test Cases + Verification (Commit/Check/CI tests).
- Zero-placeholder.

### 2.3 QA-first
- Tarea: verificación (unit/integration/E2E/security/build).
- Formato output: Test Reports + Bug Reports + Recomendation (Refactoring).

### 2.4 Redteam-first
- Tarea: auditoría adversarial.
- Formato output: PoC Security findings + severity + remediación + reglas.

### 2.5 DevOps-first (Goperative)
- Tarea: infra, secrets, exports, deployments.

---

## 3. Verificación del Criterio de Aceptación (AC)

- **Validación:** tests verde. Si falla, reportar honestamente + reintentar.
- **Evidencia:** Comando ejecutado + resultado real + Salida de tests.
- **No fake:** No modificar tests para pasar (red flags).
- **ACDSS ("Circuit Breaker"):** Auto-evolución de rol cada vez que se hace.
- **Critical:** 2er intento de señalizar mitigación.

---

## 4. Sprint análogo

| Rol | Responsabilidad |
| :--- | :--- | :--- |
| Orchestrator | Líder | Coordinación, verificación del Plan, reporting al usuario, Circuit Breaker, Exit Gate |
| @architect | Arquitecto | Design y Redesign |
| @builder | Constructor | Implementación técnica |
| @ui-artisan | Diseñador | Estética y UX |
| @qa-verifier | Verificador | Tests y Verificación |
| @redteam-auditor | Auditor | Seguridad adversarial |
| @general | General | Tarea compleja, debugging |
| @explore | Explorador | Búsqueda en codebase |

---

## 5. Cheatsheet Rápido

| Comando/Acción | Resultado | Acción |
| :--- | :--- | :--- |
| `ORCH_START` | "EVOLUTION LOOP STARTED — Milestone 1/5" | docs/TRANSFORMATION_PROGRESS.md updated |
| `TEST_PASS` | "tests PASS" | @qa-verifier: aprobar |
| `TEST_FAIL` | "tests FAIL" | @builder: reintentar + evidence |
| `BUG_REPORT` | "Bug Report — X" | @redteam: ticket + PR |
| `AUDIT_REPORT` | "Audit Report" | @redteam: reporte + Security Audit |
| `CIRCUIT_BREAKER` | "CIRCUIT BREAKER — Retry 3/3 — Arch plan" | @architect: diagnose + plan |
| `EXIT_GATE` | "Exit Gate — ALL PASS" | Orchestrator: reporte final al usuario |
| `SALIDO_FAST` | "SOFIY FAST — PENDING ASK" | Honest, luego seguir a buena vista |
| `PAUSA_CICLO` | "PAUSE — max attempts reached" | Orchestrator: forzarstop + ask |

---

## 6. Stand By (Disponibilidad Real)

- Cada fase termina con milestones de evolución visible: docs/TRANSFORMATION_PROGRESS.md — FASE 0 terminada, FASE 1 terminada, FASE 2-9 en espera (leer TASKS.md).
- El Orchestrator actualiza TRANSFORMATION_PROGRESS.md tras cada tarea: estado, evidencia real, timestamps.
- Registro de decisiones de arquitectura en `docs/TECHNICAL_DECISIONS.md` — incluye "Decisiones correctas + Incorrectas" documentadas.
- En caso de ambigüedad, architect encuestará al usuario antes de implementar (para tareas de riesgo).
- En verificación: cualquier FAIL real se reporta honestamente + se hace retry + evidence real.

---

## 7. Nota final (New Instrucciones)

- Documentación real que se genere: DOCUMENTOS DOCUMENTADOS vs CODE REAL — incluyendo honestidad en código real (código sin presupuestos).
- Validación exhaustiva vs Real. No fake: no modificar tests para pasar.
- Mantener a lo largo del tiempo: auditoría adversarial + security invariants + chaos testing.
- Cada cambio arquitectónico (ADR) requiere documentar decisiones + alternativas + recomendación + señal de scope.
- Rules for evolution: circuit breakers → cambio de arquitectura (ADR) + refactor tareas.
- BOOM (Breaking change): notificar al Orchestrator + documentar riesgo.
- Spectro aceptado por Enola (no se rompa, se mejora gradualmente).
- FACTORY y en los sprint análogos: resumen del loop + evolución + documentación + milestone + test pass y acción (goto PENDING + status).
