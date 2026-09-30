"""Tests for the SmartMaint synthetic data generator."""

from datetime import datetime

from smartmaint.data_generation.generator import (
    CRITICALITY_LEVELS,
    EQUIPMENT_STATUSES,
    EQUIPMENT_TYPES,
    FAILURE_TYPES,
    MAINTENANCE_STATUSES,
    MAINTENANCE_TYPES,
    export_to_csv,
    generate_equipment,
    generate_maintenance_events,
    generate_sensor_measurements,
)


def test_generate_equipment_returns_requested_count() -> None:
    """Generator should return the requested number of equipment records."""
    records = generate_equipment(count=10)

    assert len(records) == 10


def test_equipment_ids_are_unique() -> None:
    """Every equipment must have a unique identifier."""
    records = generate_equipment(count=100)

    equipment_ids = [record["equipment_id"] for record in records]

    assert len(equipment_ids) == len(set(equipment_ids))


def test_equipment_values_respect_contract() -> None:
    """Generated categorical values must respect the data contract."""
    records = generate_equipment(count=100)

    for record in records:
        assert record["equipment_type"] in EQUIPMENT_TYPES
        assert record["criticality"] in CRITICALITY_LEVELS
        assert record["status"] in EQUIPMENT_STATUSES


def test_equipment_generation_is_reproducible() -> None:
    """Using the same seed must generate identical records."""
    first_run = generate_equipment(count=10, seed=42)
    second_run = generate_equipment(count=10, seed=42)

    assert first_run == second_run


def test_maintenance_events_reference_existing_equipment() -> None:
    """Every maintenance event must reference an existing equipment."""
    equipment = generate_equipment(count=20)
    events = generate_maintenance_events(equipment)

    equipment_ids = {record["equipment_id"] for record in equipment}

    assert all(event["equipment_id"] in equipment_ids for event in events)


def test_maintenance_event_ids_are_unique() -> None:
    """Every maintenance event must have a unique identifier."""
    equipment = generate_equipment(count=20)
    events = generate_maintenance_events(equipment)

    event_ids = [event["maintenance_id"] for event in events]

    assert len(event_ids) == len(set(event_ids))


def test_maintenance_values_respect_contract() -> None:
    """Generated maintenance values must respect the data contract."""
    equipment = generate_equipment(count=20)
    events = generate_maintenance_events(equipment)

    for event in events:
        assert event["maintenance_type"] in MAINTENANCE_TYPES
        assert event["status"] in MAINTENANCE_STATUSES

        if event["failure_type"] is not None:
            assert event["failure_type"] in FAILURE_TYPES


def test_corrective_maintenance_has_failure_type() -> None:
    """Corrective maintenance events must identify a failure type."""
    equipment = generate_equipment(count=50)
    events = generate_maintenance_events(equipment)

    corrective_events = [
        event for event in events if event["maintenance_type"] == "CORRECTIVE"
    ]

    assert corrective_events
    assert all(event["failure_type"] is not None for event in corrective_events)


def test_completed_maintenance_has_valid_duration() -> None:
    """Completed interventions must have an end time and positive downtime."""
    equipment = generate_equipment(count=20)
    events = generate_maintenance_events(equipment)

    completed_events = [event for event in events if event["status"] == "COMPLETED"]

    assert completed_events

    for event in completed_events:
        assert event["ended_at"] is not None
        assert event["ended_at"] >= event["started_at"]
        assert event["downtime_minutes"] > 0


def test_sensor_measurements_reference_existing_equipment() -> None:
    """Sensor measurements must reference existing equipment."""
    equipment = generate_equipment(count=3)
    events = generate_maintenance_events(equipment)

    measurements = generate_sensor_measurements(
        equipment,
        events,
        start_at=datetime(2026, 9, 1),
        end_at=datetime(2026, 9, 1, 2),
    )

    equipment_ids = {record["equipment_id"] for record in equipment}

    assert all(
        measurement["equipment_id"] in equipment_ids for measurement in measurements
    )


def test_sensor_measurement_ids_are_unique() -> None:
    """Every sensor measurement must have a unique identifier."""
    equipment = generate_equipment(count=3)
    events = generate_maintenance_events(equipment)

    measurements = generate_sensor_measurements(
        equipment,
        events,
        start_at=datetime(2026, 9, 1),
        end_at=datetime(2026, 9, 1, 2),
    )

    measurement_ids = [measurement["measurement_id"] for measurement in measurements]

    assert len(measurement_ids) == len(set(measurement_ids))


def test_sensor_values_respect_contract_ranges() -> None:
    """Sensor values must remain within data contract ranges."""
    equipment = generate_equipment(count=3)
    events = generate_maintenance_events(equipment)

    measurements = generate_sensor_measurements(
        equipment,
        events,
        start_at=datetime(2026, 9, 1),
        end_at=datetime(2026, 9, 1, 2),
    )

    for measurement in measurements:
        assert -20 <= measurement["temperature_c"] <= 150
        assert 0 <= measurement["vibration_mm_s"] <= 100
        assert 0 <= measurement["pressure_bar"] <= 50
        assert 0 <= measurement["humidity_pct"] <= 100
        assert 0 <= measurement["power_kw"] <= 1000


def test_sensor_generation_is_reproducible() -> None:
    """Using the same seed must generate identical sensor measurements."""
    equipment = generate_equipment(count=2)
    events = generate_maintenance_events(equipment)

    first_run = generate_sensor_measurements(
        equipment,
        events,
        start_at=datetime(2026, 9, 1),
        end_at=datetime(2026, 9, 1, 1),
        seed=44,
    )

    second_run = generate_sensor_measurements(
        equipment,
        events,
        start_at=datetime(2026, 9, 1),
        end_at=datetime(2026, 9, 1, 1),
        seed=44,
    )

    assert first_run == second_run


def test_export_to_csv_creates_file(tmp_path) -> None:
    """CSV export should create a file containing the generated records."""
    records = generate_equipment(count=5)
    output_path = tmp_path / "equipment.csv"

    export_to_csv(records, output_path)

    assert output_path.exists()

    lines = output_path.read_text(encoding="utf-8").splitlines()

    assert len(lines) == 6
    assert "equipment_id" in lines[0]
    assert "EQ-0001" in lines[1]
