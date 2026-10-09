-- ============================================
-- Database
-- ============================================
CREATE DATABASE IF NOT EXISTS soc_dashboard;

USE soc_dashboard;

-- ============================================
-- raw_events
-- Everything lands here first, from Vector.
-- High volume, append-only, short-to-medium retention.
-- ============================================
CREATE TABLE IF NOT EXISTS raw_events
(
    event_id        UUID            DEFAULT generateUUIDv4(),
    timestamp       DateTime64(3)   DEFAULT now64(3),
    source_type     LowCardinality(String),   -- e.g. 'firewall', 'siem', 'endpoint', 'dns'
    host            String,
    raw_payload     String                     -- store as JSON string; parse at query time or in the app layer
)
ENGINE = MergeTree
PARTITION BY toYYYYMMDD(timestamp)
ORDER BY (timestamp, source_type, host)
TTL toDateTime(timestamp) + INTERVAL 30 DAY   -- adjust/remove if you need longer retention for your demo
SETTINGS index_granularity = 8192;

-- ============================================
-- alerts
-- Generated from raw_events via detection logic / Sigma rules.
-- Lower volume, needs frequent UPDATEs (status, assigned_analyst, verdict) —
-- ClickHouse MergeTree doesn't do cheap UPDATEs, so use ReplacingMergeTree.
-- ============================================
CREATE TABLE IF NOT EXISTS alerts
(
    id                  UUID            DEFAULT generateUUIDv4(),
    timestamp           DateTime64(3),
    severity            Enum8('low' = 1, 'medium' = 2, 'high' = 3, 'critical' = 4),
    category             LowCardinality(String),   -- e.g. 'Lateral Movement', 'Exfiltration'
    mitre_technique     LowCardinality(String),    -- e.g. 'T1110'
    status              Enum8('new' = 1, 'in_progress' = 2, 'escalated' = 3, 'closed' = 4),
    assigned_analyst    String          DEFAULT '',
    source_event_ids    Array(UUID),               -- links back to raw_events.event_id
    rule_name           String          DEFAULT '',
    verdict             Enum8('unreviewed' = 0, 'true_positive' = 1, 'false_positive' = 2) DEFAULT 0,
    acknowledged_at     Nullable(DateTime64(3)),    -- needed for MTTR calc
    contained_at        Nullable(DateTime64(3)),    -- needed for MTTC calc
    updated_at          DateTime64(3)   DEFAULT now64(3),
    version             UInt64          DEFAULT 1   -- required by ReplacingMergeTree
)
ENGINE = ReplacingMergeTree(version)
PARTITION BY toYYYYMM(timestamp)
ORDER BY (id)
SETTINGS index_granularity = 8192;

-- ============================================
-- assets
-- Slowly-changing reference data. Small table, updated occasionally.
-- ============================================
CREATE TABLE IF NOT EXISTS assets
(
    id                  UUID            DEFAULT generateUUIDv4(),
    hostname            String,
    ip                  IPv4,
    criticality_tier    Enum8('tier1_crown_jewel' = 1, 'tier2_standard' = 2, 'tier3_test' = 3),
    owner               String          DEFAULT '',
    discovered_at       DateTime64(3)   DEFAULT now64(3),
    version             UInt64          DEFAULT 1
)
ENGINE = ReplacingMergeTree(version)
ORDER BY (id);

-- ============================================
-- iocs
-- Threat intel enrichment cache. Updated on each new lookup;
-- ReplacingMergeTree lets you re-insert the same indicator with fresh data.
-- ============================================
CREATE TABLE IF NOT EXISTS iocs
(
    indicator           String,                    -- IP, domain, or hash value
    type                 Enum8('ip' = 1, 'domain' = 2, 'hash' = 3),
    confidence           UInt8,                     -- 0–100
    source_feed          LowCardinality(String),    -- 'AbuseIPDB', 'AlienVault OTX'
    threat_actor         String          DEFAULT '',
    last_seen             DateTime64(3)   DEFAULT now64(3),
    version               UInt64          DEFAULT 1
)
ENGINE = ReplacingMergeTree(version)
ORDER BY (indicator, type);

-- ClickHouse minstance to create the telemetry table for pipeline metrics.
CREATE TABLE IF NOT EXISTS soc_dashboard.pipeline_health
(
    snapshot_time   DateTime64(3)   DEFAULT now64(3),
    events_per_sec  Float64,
    lag_seconds     Float64,
    error_count     UInt64,
    buffer_size     UInt64
)
ENGINE = MergeTree
ORDER BY snapshot_time;