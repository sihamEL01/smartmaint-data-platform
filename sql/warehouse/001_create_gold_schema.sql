
-- Create the analytical schema
CREATE SCHEMA IF NOT EXISTS gold;

-- Daily sensor metrics: one row per equipment and day
CREATE TABLE IF NOT EXISTS gold.daily_sensor_metrics (
    equipment_id VARCHAR(50) NOT NULL,
    measurement_date DATE NOT NULL,
    measurement_count BIGINT NOT NULL,
    avg_temperature_c DOUBLE PRECISION,
    max_temperature_c DOUBLE PRECISION,
    avg_vibration_mm_s DOUBLE PRECISION,
    max_vibration_mm_s DOUBLE PRECISION,
    PRIMARY KEY (equipment_id, measurement_date)
);

-- Maintenance KPIs: one row per equipment
CREATE TABLE IF NOT EXISTS gold.maintenance_kpis (
    equipment_id VARCHAR(50) PRIMARY KEY,
    maintenance_count BIGINT NOT NULL,
    corrective_count BIGINT NOT NULL,
    total_downtime_minutes BIGINT,
    mttr_minutes DOUBLE PRECISION
);

-- Equipment health: one row per equipment
CREATE TABLE IF NOT EXISTS gold.equipment_health (
    equipment_id VARCHAR(50) PRIMARY KEY,
    equipment_name TEXT,
    equipment_type VARCHAR(50),
    site_id VARCHAR(50),
    site_name TEXT,
    criticality VARCHAR(20),
    status VARCHAR(30),
    maintenance_count BIGINT,
    corrective_count BIGINT,
    total_downtime_minutes BIGINT,
    mttr_minutes DOUBLE PRECISION,
    last_measured_at TIMESTAMP,
    last_temperature_c DOUBLE PRECISION,
    last_vibration_mm_s DOUBLE PRECISION
);
