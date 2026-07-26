CREATE TABLE IF NOT EXISTS intelligence_products (
    id                  TEXT PRIMARY KEY,
    product_type        TEXT NOT NULL,
    content             TEXT NOT NULL,
    classification_level TEXT NOT NULL DEFAULT 'CONFIDENTIAL',
    source_data         JSONB DEFAULT '{}',
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_by          TEXT NOT NULL DEFAULT 'SYSTEM'
);

CREATE INDEX IF NOT EXISTS idx_intel_products_type ON intelligence_products (product_type);
CREATE INDEX IF NOT EXISTS idx_intel_products_created ON intelligence_products (created_at DESC);
CREATE INDEX IF NOT EXISTS idx_intel_products_classification ON intelligence_products (classification_level);

CREATE TABLE IF NOT EXISTS priority_intelligence_requirements (
    id                  TEXT PRIMARY KEY,
    title               TEXT NOT NULL,
    description         TEXT NOT NULL,
    priority            INTEGER NOT NULL CHECK (priority BETWEEN 1 AND 5),
    collection_methods  JSONB DEFAULT '[]',
    due_date            TIMESTAMPTZ,
    classification_level TEXT NOT NULL DEFAULT 'CONFIDENTIAL',
    created_by          TEXT NOT NULL,
    is_active           BOOLEAN NOT NULL DEFAULT TRUE,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_pir_active ON priority_intelligence_requirements (is_active, priority);

CREATE TABLE IF NOT EXISTS sensor_sources (
    id                  TEXT PRIMARY KEY,
    sensor_id           TEXT NOT NULL UNIQUE,
    sensor_type         TEXT NOT NULL,
    status              TEXT NOT NULL DEFAULT 'ACTIVE',
    classification_level TEXT NOT NULL DEFAULT 'CONFIDENTIAL',
    first_seen          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    last_seen           TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    metadata            JSONB DEFAULT '{}'
);

CREATE INDEX IF NOT EXISTS idx_sensor_sources_type ON sensor_sources (sensor_type, status);
CREATE INDEX IF NOT EXISTS idx_sensor_sources_last_seen ON sensor_sources (last_seen DESC);

CREATE TABLE IF NOT EXISTS intel_fusion_records (
    id                  TEXT PRIMARY KEY,
    entity_id           TEXT,
    fusion_score        FLOAT NOT NULL,
    source_count        INTEGER NOT NULL DEFAULT 0,
    correlated_count    INTEGER NOT NULL DEFAULT 0,
    assessment          JSONB DEFAULT '{}',
    classification_level TEXT NOT NULL DEFAULT 'CONFIDENTIAL',
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_fusion_entity ON intel_fusion_records (entity_id);
CREATE INDEX IF NOT EXISTS idx_fusion_score ON intel_fusion_records (fusion_score DESC);
CREATE INDEX IF NOT EXISTS idx_fusion_created ON intel_fusion_records (created_at DESC);

CREATE TABLE IF NOT EXISTS satellite_products (
    id                  TEXT PRIMARY KEY,
    satellite_id        TEXT NOT NULL,
    product_type        TEXT NOT NULL,
    capture_time        TIMESTAMPTZ NOT NULL,
    area_of_interest    JSONB NOT NULL,
    resolution_m        FLOAT,
    classification_level TEXT NOT NULL DEFAULT 'SECRET',
    storage_url         TEXT,
    ai_tags             JSONB DEFAULT '[]',
    metadata            JSONB DEFAULT '{}',
    ingested_at         TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    ingested_by         TEXT NOT NULL DEFAULT 'SYSTEM'
);

CREATE INDEX IF NOT EXISTS idx_sat_products_capture ON satellite_products (capture_time DESC);
CREATE INDEX IF NOT EXISTS idx_sat_products_satellite ON satellite_products (satellite_id);

CREATE TABLE IF NOT EXISTS sigint_reports (
    id                  TEXT PRIMARY KEY,
    sensor_id           TEXT NOT NULL,
    sensor_type         TEXT NOT NULL,
    ts                  TIMESTAMPTZ NOT NULL,
    frequency_mhz       FLOAT,
    bearing_deg         FLOAT,
    signal_strength_dbm FLOAT,
    emitter_id          TEXT,
    latitude            DOUBLE PRECISION,
    longitude           DOUBLE PRECISION,
    classification_level TEXT NOT NULL DEFAULT 'SECRET',
    raw_data            JSONB DEFAULT '{}',
    analysis            TEXT,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_sigint_ts ON sigint_reports (ts DESC);
CREATE INDEX IF NOT EXISTS idx_sigint_emitter ON sigint_reports (emitter_id);

CREATE TABLE IF NOT EXISTS humint_reports (
    id                  TEXT PRIMARY KEY,
    operator_id         TEXT NOT NULL,
    mission_id          TEXT NOT NULL,
    ts                  TIMESTAMPTZ NOT NULL,
    latitude            DOUBLE PRECISION,
    longitude           DOUBLE PRECISION,
    size                TEXT,
    activity            TEXT,
    location_description TEXT,
    unit_identified     TEXT,
    time_observed       TIMESTAMPTZ,
    equipment           TEXT,
    classification_level TEXT NOT NULL DEFAULT 'CONFIDENTIAL',
    confidence          FLOAT DEFAULT 0.5,
    raw_report          JSONB DEFAULT '{}',
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_humint_ts ON humint_reports (ts DESC);
CREATE INDEX IF NOT EXISTS idx_humint_operator ON humint_reports (operator_id);
CREATE INDEX IF NOT EXISTS idx_humint_mission ON humint_reports (mission_id);
