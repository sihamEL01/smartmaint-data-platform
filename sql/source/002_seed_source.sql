BEGIN;

TRUNCATE TABLE
    source.maintenance_events,
    source.equipment;

COPY source.equipment (
    equipment_id,
    equipment_name,
    equipment_type,
    site_id,
    site_name,
    manufacturer,
    model,
    installation_date,
    criticality,
    status
)
FROM '/data/generated/equipment.csv'
WITH (
    FORMAT CSV,
    HEADER TRUE
);

COPY source.maintenance_events (
    maintenance_id,
    equipment_id,
    maintenance_type,
    failure_type,
    started_at,
    ended_at,
    downtime_minutes,
    status,
    technician_id,
    description
)
FROM '/data/generated/maintenance_events.csv'
WITH (
    FORMAT CSV,
    HEADER TRUE,
    NULL ''
);

COMMIT;