"""Synthetic industrial data generator for SmartMaint."""

import csv
import random
from datetime import date, datetime, timedelta
from pathlib import Path

EQUIPMENT_TYPES = ["PUMP", "COMPRESSOR", "MOTOR", "FAN", "CONVEYOR"]
CRITICALITY_LEVELS = ["LOW", "MEDIUM", "HIGH", "CRITICAL"]
EQUIPMENT_STATUSES = ["ACTIVE", "MAINTENANCE", "OUT_OF_SERVICE"]

SITES = [
    ("SITE-001", "Casablanca Plant"),
    ("SITE-002", "Jorf Lasfar Plant"),
    ("SITE-003", "Safi Plant"),
]
SENSOR_BASELINES = {
    "PUMP": {
        "temperature_c": 60.0,
        "vibration_mm_s": 3.0,
        "pressure_bar": 12.0,
        "power_kw": 90.0,
    },
    "COMPRESSOR": {
        "temperature_c": 75.0,
        "vibration_mm_s": 4.0,
        "pressure_bar": 20.0,
        "power_kw": 180.0,
    },
    "MOTOR": {
        "temperature_c": 65.0,
        "vibration_mm_s": 3.5,
        "pressure_bar": 5.0,
        "power_kw": 120.0,
    },
    "FAN": {
        "temperature_c": 50.0,
        "vibration_mm_s": 2.5,
        "pressure_bar": 3.0,
        "power_kw": 60.0,
    },
    "CONVEYOR": {
        "temperature_c": 55.0,
        "vibration_mm_s": 3.0,
        "pressure_bar": 2.0,
        "power_kw": 80.0,
    },
}

MANUFACTURERS = [
    "Siemens",
    "Schneider Electric",
    "ABB",
    "Atlas Copco",
    "Grundfos",
]

MAINTENANCE_TYPES = ["CORRECTIVE", "PREVENTIVE", "PREDICTIVE"]

FAILURE_TYPES = [
    "MECHANICAL",
    "ELECTRICAL",
    "OVERHEATING",
    "VIBRATION",
    "PRESSURE",
    "OTHER",
]

MAINTENANCE_STATUSES = [
    "OPEN",
    "IN_PROGRESS",
    "COMPLETED",
    "CANCELLED",
]


def generate_equipment(
    count: int = 100,
    seed: int = 42,
) -> list[dict[str, object]]:
    """Generate deterministic synthetic industrial equipment records."""
    rng = random.Random(seed)

    installation_start = date(2015, 1, 1)
    installation_end = date(2025, 12, 31)
    installation_range = (installation_end - installation_start).days

    equipment_records = []

    for index in range(1, count + 1):
        equipment_type = rng.choice(EQUIPMENT_TYPES)
        site_id, site_name = rng.choice(SITES)
        manufacturer = rng.choice(MANUFACTURERS)

        equipment_records.append(
            {
                "equipment_id": f"EQ-{index:04d}",
                "equipment_name": f"{equipment_type.title()} {index:03d}",
                "equipment_type": equipment_type,
                "site_id": site_id,
                "site_name": site_name,
                "manufacturer": manufacturer,
                "model": f"{manufacturer[:3].upper()}-{rng.randint(100, 999)}",
                "installation_date": installation_start
                + timedelta(days=rng.randint(0, installation_range)),
                "criticality": rng.choice(CRITICALITY_LEVELS),
                "status": rng.choices(
                    EQUIPMENT_STATUSES,
                    weights=[85, 10, 5],
                    k=1,
                )[0],
            }
        )

    return equipment_records


def generate_maintenance_events(
    equipment_records: list[dict[str, object]],
    min_events: int = 2,
    max_events: int = 6,
    seed: int = 43,
) -> list[dict[str, object]]:
    """Generate synthetic maintenance events for industrial equipment."""
    rng = random.Random(seed)

    period_start = datetime(2026, 1, 1)
    period_end = datetime(2026, 9, 30)
    period_minutes = int((period_end - period_start).total_seconds() // 60)

    maintenance_records = []
    event_number = 1

    for equipment in equipment_records:
        event_count = rng.randint(min_events, max_events)

        for _ in range(event_count):
            maintenance_type = rng.choices(
                MAINTENANCE_TYPES,
                weights=[35, 50, 15],
                k=1,
            )[0]

            started_at = period_start + timedelta(
                minutes=rng.randint(0, period_minutes)
            )

            status = rng.choices(
                MAINTENANCE_STATUSES,
                weights=[3, 5, 90, 2],
                k=1,
            )[0]

            failure_type = (
                rng.choice(FAILURE_TYPES) if maintenance_type == "CORRECTIVE" else None
            )

            if status == "COMPLETED":
                downtime_minutes = rng.randint(30, 720)
                ended_at = started_at + timedelta(minutes=downtime_minutes)
            else:
                downtime_minutes = None
                ended_at = None

            maintenance_records.append(
                {
                    "maintenance_id": f"MNT-{event_number:06d}",
                    "equipment_id": equipment["equipment_id"],
                    "maintenance_type": maintenance_type,
                    "failure_type": failure_type,
                    "started_at": started_at,
                    "ended_at": ended_at,
                    "downtime_minutes": downtime_minutes,
                    "status": status,
                    "technician_id": f"TECH-{rng.randint(1, 20):03d}",
                    "description": (
                        f"{maintenance_type.title()} maintenance intervention"
                    ),
                }
            )

            event_number += 1

    return maintenance_records


def generate_sensor_measurements(
    equipment_records: list[dict[str, object]],
    maintenance_events: list[dict[str, object]],
    start_at: datetime = datetime(2026, 9, 1),
    end_at: datetime = datetime(2026, 9, 30, 23, 30),
    interval_minutes: int = 30,
    seed: int = 44,
) -> list[dict[str, object]]:
    """Generate time-series IoT measurements for industrial equipment."""
    rng = random.Random(seed)

    corrective_events_by_equipment: dict[str, list[dict[str, object]]] = {}

    for event in maintenance_events:
        if event["maintenance_type"] == "CORRECTIVE":
            equipment_id = str(event["equipment_id"])
            corrective_events_by_equipment.setdefault(equipment_id, []).append(event)

    measurements = []
    measurement_number = 1

    for equipment in equipment_records:
        equipment_id = str(equipment["equipment_id"])
        equipment_type = str(equipment["equipment_type"])
        baseline = SENSOR_BASELINES[equipment_type]

        equipment_failures = corrective_events_by_equipment.get(equipment_id, [])

        measured_at = start_at

        while measured_at <= end_at:
            temperature = baseline["temperature_c"] + rng.uniform(-3.0, 3.0)
            vibration = baseline["vibration_mm_s"] + rng.uniform(-0.8, 0.8)
            pressure = baseline["pressure_bar"] + rng.uniform(-1.0, 1.0)
            power = baseline["power_kw"] + rng.uniform(-10.0, 10.0)
            humidity = rng.uniform(35.0, 75.0)

            for failure in equipment_failures:
                failure_time = failure["started_at"]

                if not isinstance(failure_time, datetime):
                    continue

                hours_before_failure = (
                    failure_time - measured_at
                ).total_seconds() / 3600

                if 0 <= hours_before_failure <= 6:
                    failure_type = failure["failure_type"]

                    if failure_type == "OVERHEATING":
                        temperature += 25.0
                    elif failure_type == "VIBRATION":
                        vibration += 7.0
                    elif failure_type == "PRESSURE":
                        pressure += 10.0
                    elif failure_type == "MECHANICAL":
                        temperature += 8.0
                        vibration += 5.0
                    elif failure_type == "ELECTRICAL":
                        temperature += 10.0
                        power += 100.0
                    else:
                        temperature += 5.0
                        vibration += 2.0

            measurements.append(
                {
                    "measurement_id": f"MSR-{measurement_number:09d}",
                    "equipment_id": equipment_id,
                    "measured_at": measured_at,
                    "temperature_c": round(
                        min(max(temperature, -20.0), 150.0),
                        2,
                    ),
                    "vibration_mm_s": round(
                        min(max(vibration, 0.0), 100.0),
                        2,
                    ),
                    "pressure_bar": round(
                        min(max(pressure, 0.0), 50.0),
                        2,
                    ),
                    "humidity_pct": round(
                        min(max(humidity, 0.0), 100.0),
                        2,
                    ),
                    "power_kw": round(
                        min(max(power, 0.0), 1000.0),
                        2,
                    ),
                }
            )

            measurement_number += 1
            measured_at += timedelta(minutes=interval_minutes)

    return measurements


def export_to_csv(
    records: list[dict[str, object]],
    output_path: Path,
) -> None:
    """Export generated records to a CSV file."""
    if not records:
        raise ValueError("Cannot export an empty dataset.")

    output_path.parent.mkdir(parents=True, exist_ok=True)

    fieldnames = list(records[0].keys())

    with output_path.open(
        "w",
        newline="",
        encoding="utf-8",
    ) as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
        writer.writeheader()

        for record in records:
            serialized_record = {
                key: (
                    value.isoformat() if isinstance(value, (date, datetime)) else value
                )
                for key, value in record.items()
            }

            writer.writerow(serialized_record)


def main() -> None:
    """Generate the SmartMaint synthetic source datasets."""
    output_directory = Path("data/generated")

    print("Generating equipment...")
    equipment = generate_equipment(count=100)

    print("Generating maintenance events...")
    maintenance_events = generate_maintenance_events(equipment)

    print("Generating IoT sensor measurements...")
    sensor_measurements = generate_sensor_measurements(
        equipment,
        maintenance_events,
    )

    export_to_csv(
        equipment,
        output_directory / "equipment.csv",
    )
    export_to_csv(
        maintenance_events,
        output_directory / "maintenance_events.csv",
    )
    export_to_csv(
        sensor_measurements,
        output_directory / "sensor_measurements.csv",
    )

    print()
    print("SmartMaint synthetic data generated successfully.")
    print(f"Equipment: {len(equipment):,}")
    print(f"Maintenance events: {len(maintenance_events):,}")
    print(f"Sensor measurements: {len(sensor_measurements):,}")
    print(f"Output directory: {output_directory.resolve()}")


if __name__ == "__main__":
    main()
