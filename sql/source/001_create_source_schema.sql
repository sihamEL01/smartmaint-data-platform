CREATE SCHEMA IF NOT EXISTS source;


CREATE TABLE IF NOT EXISTS source.equipment (
    equipment_id VARCHAR(20) PRIMARY KEY,
    equipment_name VARCHAR(100) NOT NULL,
    equipment_type VARCHAR(20) NOT NULL,
    site_id VARCHAR(20) NOT NULL,
    site_name VARCHAR(100) NOT NULL,
    manufacturer VARCHAR(100),
    model VARCHAR(100),
    installation_date DATE NOT NULL,
    criticality VARCHAR(20) NOT NULL,
    status VARCHAR(20) NOT NULL,

    CONSTRAINT chk_equipment_type
        CHECK (
            equipment_type IN (
                'PUMP',
                'COMPRESSOR',
                'MOTOR',
                'FAN',
                'CONVEYOR'
            )
        ),

    CONSTRAINT chk_equipment_criticality
        CHECK (
            criticality IN (
                'LOW',
                'MEDIUM',
                'HIGH',
                'CRITICAL'
            )
        ),

    CONSTRAINT chk_equipment_status
        CHECK (
            status IN (
                'ACTIVE',
                'MAINTENANCE',
                'OUT_OF_SERVICE'
            )
        )
);


CREATE TABLE IF NOT EXISTS source.maintenance_events (
    maintenance_id VARCHAR(20) PRIMARY KEY,
    equipment_id VARCHAR(20) NOT NULL,
    maintenance_type VARCHAR(20) NOT NULL,
    failure_type VARCHAR(20),
    started_at TIMESTAMP NOT NULL,
    ended_at TIMESTAMP,
    downtime_minutes INTEGER,
    status VARCHAR(20) NOT NULL,
    technician_id VARCHAR(20),
    description TEXT,

    CONSTRAINT fk_maintenance_equipment
        FOREIGN KEY (equipment_id)
        REFERENCES source.equipment(equipment_id),

    CONSTRAINT chk_maintenance_type
        CHECK (
            maintenance_type IN (
                'CORRECTIVE',
                'PREVENTIVE',
                'PREDICTIVE'
            )
        ),

    CONSTRAINT chk_failure_type
        CHECK (
            failure_type IS NULL
            OR failure_type IN (
                'MECHANICAL',
                'ELECTRICAL',
                'OVERHEATING',
                'VIBRATION',
                'PRESSURE',
                'OTHER'
            )
        ),

    CONSTRAINT chk_downtime_minutes
        CHECK (
            downtime_minutes IS NULL
            OR downtime_minutes >= 0
        ),

    CONSTRAINT chk_maintenance_status
        CHECK (
            status IN (
                'OPEN',
                'IN_PROGRESS',
                'COMPLETED',
                'CANCELLED'
            )
        )
);