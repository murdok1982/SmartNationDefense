-- =============================================================================
-- SESIS v3 — Migración 003: Mejoras Militares Críticas
-- 10 módulos: Mensajería, Fusión JDL, Terreno, Logística, AAR,
--             Reportes, Predicción, Mapa Táctico, Voz, Planificación NATO
-- Ejecutar después de 002_intel.sql
-- =============================================================================

-- -----------------------------------------------------------------------------
-- 1. MENSAJERÍA TÁCTICA
-- Sistema de mensajería con QoS militar, encriptación E2E y priority queue
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS tactical_messages (
    id                  TEXT PRIMARY KEY,
    sender_id           TEXT NOT NULL,
    recipient_ids       JSONB NOT NULL DEFAULT '[]',
    message_type        TEXT NOT NULL CHECK (message_type IN ('TEXT', 'COMMAND', 'ALERT', 'STATUS', 'LOCATION')),
    priority            TEXT NOT NULL CHECK (priority IN ('CRITICAL', 'HIGH', 'MEDIUM', 'LOW')),
    subject             TEXT,
    content             TEXT NOT NULL,
    encrypted_content   TEXT,
    timestamp           TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    acknowledged_by     JSONB DEFAULT '[]',
    delivered_to        JSONB DEFAULT '[]',
    thread_id           TEXT,
    classification      TEXT NOT NULL DEFAULT 'CONFIDENTIAL',
    expires_at          TIMESTAMPTZ,
    is_read             BOOLEAN DEFAULT FALSE,
    parent_id           TEXT
);

CREATE INDEX IF NOT EXISTS idx_tmsg_sender ON tactical_messages(sender_id);
CREATE INDEX IF NOT EXISTS idx_tmsg_timestamp ON tactical_messages(timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_tmsg_priority ON tactical_messages(priority);
CREATE INDEX IF NOT EXISTS idx_tmsg_type ON tactical_messages(message_type);
CREATE INDEX IF NOT EXISTS idx_tmsg_thread ON tactical_messages(thread_id);
CREATE INDEX IF NOT EXISTS idx_tmsg_classification ON tactical_messages(classification);

-- -----------------------------------------------------------------------------
-- 2. FUSIÓN JDL LEVEL 2 - Situational Assessment Records
-- Registro de evaluaciones de situación generadas por el motor de fusión
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS situation_assessments (
    id                  TEXT PRIMARY KEY,
    assessment_type     TEXT NOT NULL DEFAULT 'THREAT',
    threat_level        FLOAT NOT NULL DEFAULT 0.0,
    hostile_units       JSONB DEFAULT '[]',
    friendly_units      JSONB DEFAULT '[]',
    neutral_entities    JSONB DEFAULT '[]',
    threat_zones        JSONB DEFAULT '[]',
    recommended_actions JSONB DEFAULT '[]',
    relationship_graph  JSONB DEFAULT '{}',
    intention_analysis  JSONB DEFAULT '[]',
    source_events       JSONB DEFAULT '[]',
    classification      TEXT NOT NULL DEFAULT 'SECRET',
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_by          TEXT NOT NULL DEFAULT 'SYSTEM'
);

CREATE INDEX IF NOT EXISTS idx_sitassess_threat ON situation_assessments(threat_level DESC);
CREATE INDEX IF NOT EXISTS idx_sitassess_created ON situation_assessments(created_at DESC);

-- -----------------------------------------------------------------------------
-- 3. ANÁLISIS DE TERRENO
-- Resultados de análisis de terreno, LOS, rutas y obstáculos
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS terrain_analyses (
    id                  TEXT PRIMARY KEY,
    analysis_type       TEXT NOT NULL CHECK (analysis_type IN ('LOS', 'ROUTE', 'TERRAIN', 'ELEVATION', 'OBSTACLE')),
    parameters          JSONB NOT NULL DEFAULT '{}',
    results             JSONB NOT NULL DEFAULT '{}',
    vehicle_type        TEXT,
    difficulty          TEXT,
    classification      TEXT NOT NULL DEFAULT 'CONFIDENTIAL',
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_by          TEXT NOT NULL DEFAULT 'SYSTEM'
);

CREATE INDEX IF NOT EXISTS idx_terrain_type ON terrain_analyses(analysis_type);
CREATE INDEX IF NOT EXISTS idx_terrain_created ON terrain_analyses(created_at DESC);

-- -----------------------------------------------------------------------------
-- 4. LOGÍSTICA MILITAR - Suministros, Solicitudes y MEDEVAC
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS military_supplies (
    id                  TEXT PRIMARY KEY,
    supply_type         TEXT NOT NULL CHECK (supply_type IN ('AMMO', 'FUEL', 'RATION', 'MEDICAL', 'EQUIPMENT', 'WATER', 'COMMS')),
    quantity            FLOAT NOT NULL DEFAULT 0,
    unit                TEXT NOT NULL DEFAULT 'UNITS',
    location_id         TEXT,
    location            JSONB DEFAULT '{}',
    status              TEXT NOT NULL DEFAULT 'AVAILABLE' CHECK (status IN ('AVAILABLE', 'REQUESTED', 'IN_TRANSIT', 'DELIVERED', 'DEPLETED')),
    priority            TEXT NOT NULL DEFAULT 'MEDIUM',
    min_threshold       FLOAT DEFAULT 0,
    classification      TEXT NOT NULL DEFAULT 'CONFIDENTIAL',
    requested_by        TEXT,
    eta                 TIMESTAMPTZ,
    last_updated        TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_milsup_type ON military_supplies(supply_type);
CREATE INDEX IF NOT EXISTS idx_milsup_status ON military_supplies(status);
CREATE INDEX IF NOT EXISTS idx_milsup_location ON military_supplies(location_id);

CREATE TABLE IF NOT EXISTS supply_requests (
    id                  TEXT PRIMARY KEY,
    supply_type         TEXT NOT NULL,
    quantity            FLOAT NOT NULL,
    unit                TEXT NOT NULL DEFAULT 'UNITS',
    requested_by        TEXT NOT NULL,
    delivery_location   JSONB DEFAULT '{}',
    priority            TEXT NOT NULL DEFAULT 'MEDIUM',
    status              TEXT NOT NULL DEFAULT 'REQUESTED' CHECK (status IN ('REQUESTED', 'APPROVED', 'IN_TRANSIT', 'DELIVERED', 'CANCELLED')),
    justification       TEXT,
    eta                 TIMESTAMPTZ,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    fulfilled_at        TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS idx_supreq_status ON supply_requests(status);
CREATE INDEX IF NOT EXISTS idx_supreq_priority ON supply_requests(priority);
CREATE INDEX IF NOT EXISTS idx_supreq_created ON supply_requests(created_at DESC);

CREATE TABLE IF NOT EXISTS medevac_requests (
    id                  TEXT PRIMARY KEY,
    casualty_id         TEXT NOT NULL,
    casualty_name       TEXT,
    location            JSONB NOT NULL DEFAULT '{}',
    urgency             TEXT NOT NULL DEFAULT 'ROUTINE' CHECK (urgency IN ('URGENT', 'PRIORITY', 'ROUTINE')),
    evac_type           TEXT NOT NULL DEFAULT 'MEDEVAC' CHECK (evac_type IN ('HOIST', 'MEDEVAC', 'EVAC')),
    equipment_needed    JSONB DEFAULT '[]',
    security_at_site    TEXT NOT NULL DEFAULT 'N' CHECK (security_at_site IN ('N', 'P', 'H', 'E')),
    marked              BOOLEAN DEFAULT FALSE,
    casualty_count      INTEGER NOT NULL DEFAULT 1,
    special_equipment   TEXT,
    casualty_status     TEXT,
    terrain_description TEXT,
    radio_freq          TEXT,
    lines               JSONB DEFAULT '{}',
    status              TEXT NOT NULL DEFAULT 'REQUESTED' CHECK (status IN ('REQUESTED', 'APPROVED', 'EN_ROUTE', 'COMPLETED', 'CANCELLED')),
    classification      TEXT NOT NULL DEFAULT 'SECRET',
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    completed_at        TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS idx_medevac_urgency ON medevac_requests(urgency);
CREATE INDEX IF NOT EXISTS idx_medevac_status ON medevac_requests(status);
CREATE INDEX IF NOT EXISTS idx_medevac_created ON medevac_requests(created_at DESC);

CREATE TABLE IF NOT EXISTS military_personnel (
    id                  TEXT PRIMARY KEY,
    name                TEXT NOT NULL,
    rank                TEXT NOT NULL,
    unit                TEXT NOT NULL,
    status              TEXT NOT NULL DEFAULT 'ACTIVE' CHECK (status IN ('ACTIVE', 'WIA', 'KIA', 'MIA', 'OFF_DUTY', 'RESERVE')),
    location            JSONB DEFAULT '{}',
    last_checkin        TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    medical_status      TEXT NOT NULL DEFAULT 'FIT',
    role                TEXT,
    classification      TEXT NOT NULL DEFAULT 'CONFIDENTIAL'
);

CREATE INDEX IF NOT EXISTS idx_milpers_status ON military_personnel(status);
CREATE INDEX IF NOT EXISTS idx_milpers_unit ON military_personnel(unit);

CREATE TABLE IF NOT EXISTS maintenance_reports (
    id                  TEXT PRIMARY KEY,
    equipment_id        TEXT NOT NULL,
    equipment_type      TEXT NOT NULL,
    issue_type          TEXT NOT NULL,
    severity            TEXT NOT NULL DEFAULT 'MEDIUM' CHECK (severity IN ('LOW', 'MEDIUM', 'HIGH', 'CRITICAL')),
    description         TEXT,
    reported_by         TEXT NOT NULL,
    location            JSONB DEFAULT '{}',
    status              TEXT NOT NULL DEFAULT 'REPORTED' CHECK (status IN ('REPORTED', 'IN_PROGRESS', 'RESOLVED', 'CLOSED')),
    priority            TEXT NOT NULL DEFAULT 'MEDIUM',
    estimated_repair_h  FLOAT,
    parts_needed        JSONB DEFAULT '[]',
    reported_at         TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    resolved_at         TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS idx_maint_status ON maintenance_reports(status);
CREATE INDEX IF NOT EXISTS idx_maint_severity ON maintenance_reports(severity);
CREATE INDEX IF NOT EXISTS idx_maint_equipment ON maintenance_reports(equipment_id);

-- -----------------------------------------------------------------------------
-- 5. AFTER ACTION REVIEW (AAR)
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS after_action_reviews (
    id                  TEXT PRIMARY KEY,
    operation_id        TEXT NOT NULL,
    operation_name      TEXT NOT NULL,
    start_time          TIMESTAMPTZ NOT NULL,
    end_time            TIMESTAMPTZ,
    participants        JSONB DEFAULT '[]',
    timeline            JSONB DEFAULT '[]',
    objectives          JSONB DEFAULT '[]',
    outcomes            JSONB DEFAULT '[]',
    lessons_learned     JSONB DEFAULT '[]',
    recommendations     JSONB DEFAULT '[]',
    performance_metrics JSONB DEFAULT '{}',
    summary             JSONB DEFAULT '{}',
    status              TEXT NOT NULL DEFAULT 'IN_PROGRESS' CHECK (status IN ('IN_PROGRESS', 'FINALIZED')),
    classification      TEXT NOT NULL DEFAULT 'CONFIDENTIAL',
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_by          TEXT NOT NULL DEFAULT 'SYSTEM',
    finalized_at        TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS idx_aar_operation ON after_action_reviews(operation_id);
CREATE INDEX IF NOT EXISTS idx_aar_status ON after_action_reviews(status);
CREATE INDEX IF NOT EXISTS idx_aar_created ON after_action_reviews(created_at DESC);

-- -----------------------------------------------------------------------------
-- 6. REPORTES AUTOMÁTICOS (SITREP, SPOTREP, SALUTE, MEDEVAC)
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS military_reports (
    id                  TEXT PRIMARY KEY,
    report_type         TEXT NOT NULL CHECK (report_type IN ('SITREP', 'SPOTREP', 'SALUTE', 'MEDEVAC', 'INTELSUM', 'BDA')),
    title               TEXT NOT NULL,
    content             JSONB NOT NULL DEFAULT '{}',
    classification      TEXT NOT NULL DEFAULT 'CONFIDENTIAL',
    distribution_list   JSONB DEFAULT '[]',
    digital_signature   TEXT,
    auto_generated      BOOLEAN DEFAULT FALSE,
    source_data         JSONB DEFAULT '{}',
    operation_id        TEXT,
    status              TEXT NOT NULL DEFAULT 'DRAFT' CHECK (status IN ('DRAFT', 'FINAL', 'DISTRIBUTED', 'ARCHIVED')),
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_by          TEXT NOT NULL DEFAULT 'SYSTEM'
);

CREATE INDEX IF NOT EXISTS idx_milrep_type ON military_reports(report_type);
CREATE INDEX IF NOT EXISTS idx_milrep_status ON military_reports(status);
CREATE INDEX IF NOT EXISTS idx_milrep_created ON military_reports(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_milrep_operation ON military_reports(operation_id);

-- -----------------------------------------------------------------------------
-- 7. PREDICCIÓN DE AMENAZAS ML
-- Historial de posiciones y predicciones generadas
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS threat_predictions (
    id                  TEXT PRIMARY KEY,
    enemy_unit_id       TEXT NOT NULL,
    current_location    JSONB NOT NULL DEFAULT '{}',
    predicted_location  JSONB NOT NULL DEFAULT '{}',
    confidence          FLOAT NOT NULL DEFAULT 0.0,
    time_horizon_min    INTEGER NOT NULL DEFAULT 60,
    movement_pattern    TEXT,
    threat_level        FLOAT NOT NULL DEFAULT 0.0,
    recommended_action  TEXT,
    trajectory_points   JSONB DEFAULT '[]',
    anomaly_score       FLOAT DEFAULT 0.0,
    generated_at        TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_threatpred_unit ON threat_predictions(enemy_unit_id);
CREATE INDEX IF NOT EXISTS idx_threatpred_threat ON threat_predictions(threat_level DESC);
CREATE INDEX IF NOT EXISTS idx_threatpred_generated ON threat_predictions(generated_at DESC);

CREATE TABLE IF NOT EXISTS pattern_of_life (
    id                  TEXT PRIMARY KEY,
    unit_id             TEXT NOT NULL,
    observations        INTEGER NOT NULL DEFAULT 0,
    pattern_type        TEXT,
    area_of_operations  JSONB DEFAULT '{}',
    movement_stats      JSONB DEFAULT '{}',
    predictability      FLOAT DEFAULT 0.0,
    routine_detected    BOOLEAN DEFAULT FALSE,
    analyzed_at         TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_pol_unit ON pattern_of_life(unit_id);
CREATE INDEX IF NOT EXISTS idx_pol_analyzed ON pattern_of_life(analyzed_at DESC);

-- -----------------------------------------------------------------------------
-- 8. MAPA TÁCTICO - Overlays y tracking de unidades
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS map_overlays (
    id                  TEXT PRIMARY KEY,
    name                TEXT NOT NULL,
    layer_type          TEXT NOT NULL DEFAULT 'TACTICAL',
    geojson             JSONB DEFAULT '{}',
    style               JSONB DEFAULT '{}',
    visible             BOOLEAN DEFAULT TRUE,
    metadata            JSONB DEFAULT '{}',
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_by          TEXT NOT NULL DEFAULT 'SYSTEM'
);

CREATE INDEX IF NOT EXISTS idx_overlay_type ON map_overlays(layer_type);
CREATE INDEX IF NOT EXISTS idx_overlay_created ON map_overlays(created_at DESC);

CREATE TABLE IF NOT EXISTS unit_tracking (
    id                  BIGSERIAL PRIMARY KEY,
    unit_id             TEXT NOT NULL,
    lat                 DOUBLE PRECISION NOT NULL,
    lon                 DOUBLE PRECISION NOT NULL,
    altitude            DOUBLE PRECISION DEFAULT 0,
    heading             DOUBLE PRECISION DEFAULT 0,
    speed               DOUBLE PRECISION DEFAULT 0,
    status              TEXT NOT NULL DEFAULT 'ACTIVE',
    timestamp           TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_unittrack_unit ON unit_tracking(unit_id);
CREATE INDEX IF NOT EXISTS idx_unittrack_ts ON unit_tracking(timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_unittrack_unit_ts ON unit_tracking(unit_id, timestamp DESC);

-- -----------------------------------------------------------------------------
-- 9. COMANDOS DE VOZ - Historial de comandos procesados
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS voice_command_history (
    id                  TEXT PRIMARY KEY,
    user_id             TEXT NOT NULL,
    language            TEXT NOT NULL DEFAULT 'es',
    transcript          TEXT NOT NULL,
    command_type        TEXT NOT NULL,
    command_params      JSONB DEFAULT '{}',
    execution_result    JSONB DEFAULT '{}',
    confidence          FLOAT DEFAULT 0.0,
    processed_at        TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_voice_user ON voice_command_history(user_id);
CREATE INDEX IF NOT EXISTS idx_voice_type ON voice_command_history(command_type);
CREATE INDEX IF NOT EXISTS idx_voice_processed ON voice_command_history(processed_at DESC);

-- -----------------------------------------------------------------------------
-- 10. PLANIFICACIÓN NATO MEJORADA (OPORD 5 Párrafos)
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS enhanced_opords (
    id                      TEXT PRIMARY KEY,
    operation_name          TEXT NOT NULL,
    classification          TEXT NOT NULL DEFAULT 'SECRET',
    paragraph_1_situation   JSONB DEFAULT '{}',
    paragraph_2_mission     JSONB DEFAULT '{}',
    paragraph_3_execution   JSONB DEFAULT '{}',
    paragraph_4_sustainment JSONB DEFAULT '{}',
    paragraph_5_command_signal JSONB DEFAULT '{}',
    annexes                 JSONB DEFAULT '[]',
    status                  TEXT NOT NULL DEFAULT 'DRAFT' CHECK (status IN ('DRAFT', 'APPROVED', 'DISTRIBUTED', 'EXECUTING', 'COMPLETE')),
    created_at              TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_by              TEXT NOT NULL DEFAULT 'SYSTEM',
    approved_at             TIMESTAMPTZ,
    approved_by             TEXT,
    distributed_at          TIMESTAMPTZ,
    parent_opord_id         TEXT
);

CREATE INDEX IF NOT EXISTS idx_eopord_status ON enhanced_opords(status);
CREATE INDEX IF NOT EXISTS idx_eopord_created ON enhanced_opords(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_eopord_parent ON enhanced_opords(parent_opord_id);

CREATE TABLE IF NOT EXISTS coa_comparisons (
    id                  TEXT PRIMARY KEY,
    opord_id            TEXT,
    coa_list            JSONB NOT NULL DEFAULT '[]',
    comparison_matrix   JSONB DEFAULT '{}',
    recommendation      TEXT,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_by          TEXT NOT NULL DEFAULT 'SYSTEM'
);

CREATE INDEX IF NOT EXISTS idx_coa_opord ON coa_comparisons(opord_id);
CREATE INDEX IF NOT EXISTS idx_coa_created ON coa_comparisons(created_at DESC);

CREATE TABLE IF NOT EXISTS risk_assessments (
    id                  TEXT PRIMARY KEY,
    opord_id            TEXT NOT NULL,
    risks               JSONB NOT NULL DEFAULT '[]',
    overall_risk_level  TEXT NOT NULL DEFAULT 'MODERATE',
    risk_matrix         JSONB DEFAULT '{}',
    recommendations     JSONB DEFAULT '[]',
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_risk_opord ON risk_assessments(opord_id);
CREATE INDEX IF NOT EXISTS idx_risk_level ON risk_assessments(overall_risk_level);

-- -----------------------------------------------------------------------------
-- Vistas útiles para operaciones
-- -----------------------------------------------------------------------------
CREATE OR REPLACE VIEW v_active_threats AS
    SELECT tp.*
    FROM threat_predictions tp
    WHERE tp.threat_level > 60
      AND tp.generated_at > NOW() - INTERVAL '1 hour'
    ORDER BY tp.threat_level DESC;

CREATE OR REPLACE VIEW v_pending_medevac AS
    SELECT mr.*
    FROM medevac_requests mr
    WHERE mr.status IN ('REQUESTED', 'APPROVED')
    ORDER BY
        CASE mr.urgency
            WHEN 'URGENT' THEN 1
            WHEN 'PRIORITY' THEN 2
            WHEN 'ROUTINE' THEN 3
        END,
        mr.created_at;

CREATE OR REPLACE VIEW v_pending_supply_requests AS
    SELECT sr.*
    FROM supply_requests sr
    WHERE sr.status IN ('REQUESTED', 'APPROVED')
    ORDER BY
        CASE sr.priority
            WHEN 'CRITICAL' THEN 1
            WHEN 'HIGH' THEN 2
            WHEN 'MEDIUM' THEN 3
            WHEN 'LOW' THEN 4
        END,
        sr.created_at;

CREATE OR REPLACE VIEW v_critical_supplies AS
    SELECT ms.*
    FROM military_supplies ms
    WHERE ms.min_threshold > 0
      AND ms.quantity < ms.min_threshold
      AND ms.status = 'AVAILABLE';

CREATE OR REPLACE VIEW v_active_opords AS
    SELECT eo.*
    FROM enhanced_opords eo
    WHERE eo.status IN ('APPROVED', 'DISTRIBUTED', 'EXECUTING')
    ORDER BY eo.created_at DESC;
