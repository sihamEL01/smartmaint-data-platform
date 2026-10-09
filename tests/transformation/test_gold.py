import pytest
from pyspark.sql import SparkSession

from smartmaint.transformation.gold import (
    build_daily_sensor_metrics,
    build_equipment_health,
    build_maintenance_kpis,
)


@pytest.fixture(scope="module")
def spark():
    session = SparkSession.builder.master("local[1]").appName("GoldTests").getOrCreate()
    yield session
    session.stop()


def test_daily_sensor_metrics(spark):
    sensors = spark.createDataFrame(
        [
            ("EQ-001", "2026-09-01 08:00:00", 20.0, 2.0),
            ("EQ-001", "2026-09-01 09:00:00", 30.0, 4.0),
        ],
        ["equipment_id", "measured_at", "temperature_c", "vibration_mm_s"],
    ).selectExpr(
        "equipment_id",
        "cast(measured_at as timestamp) as measured_at",
        "temperature_c",
        "vibration_mm_s",
    )

    result = build_daily_sensor_metrics(sensors).collect()

    assert len(result) == 1
    assert result[0]["measurement_count"] == 2
    assert result[0]["avg_temperature_c"] == 25.0
    assert result[0]["max_temperature_c"] == 30.0
    assert result[0]["avg_vibration_mm_s"] == 3.0
    assert result[0]["max_vibration_mm_s"] == 4.0


def test_maintenance_kpis(spark):
    maintenance = spark.createDataFrame(
        [
            ("EQ-001", "CORRECTIVE", "COMPLETED", 60),
            ("EQ-001", "CORRECTIVE", "COMPLETED", 120),
            ("EQ-001", "PREVENTIVE", "COMPLETED", 30),
        ],
        [
            "equipment_id",
            "maintenance_type",
            "status",
            "downtime_minutes",
        ],
    )

    result = build_maintenance_kpis(maintenance).collect()

    assert len(result) == 1
    assert result[0]["maintenance_count"] == 3
    assert result[0]["corrective_count"] == 2
    assert result[0]["total_downtime_minutes"] == 210
    assert result[0]["mttr_minutes"] == 90.0


def test_equipment_health(spark):
    equipment = spark.createDataFrame(
        [
            ("EQ-001", "Pump A", "PUMP", "SITE-01", "Factory A", "HIGH", "ACTIVE"),
            ("EQ-002", "Motor B", "MOTOR", "SITE-01", "Factory A", "LOW", "ACTIVE"),
        ],
        [
            "equipment_id",
            "equipment_name",
            "equipment_type",
            "site_id",
            "site_name",
            "criticality",
            "status",
        ],
    )

    maintenance_kpis = spark.createDataFrame(
        [("EQ-001", 3, 2, 180, 90.0)],
        [
            "equipment_id",
            "maintenance_count",
            "corrective_count",
            "total_downtime_minutes",
            "mttr_minutes",
        ],
    )

    sensors = spark.createDataFrame(
        [
            ("M-001", "EQ-001", "2026-09-01 08:00:00", 25.0, 2.0),
            ("M-002", "EQ-001", "2026-09-01 10:00:00", 30.0, 3.0),
        ],
        [
            "measurement_id",
            "equipment_id",
            "measured_at",
            "temperature_c",
            "vibration_mm_s",
        ],
    ).selectExpr(
        "measurement_id",
        "equipment_id",
        "cast(measured_at as timestamp) as measured_at",
        "temperature_c",
        "vibration_mm_s",
    )

    result = {
        row["equipment_id"]: row
        for row in build_equipment_health(
            equipment, maintenance_kpis, sensors
        ).collect()
    }

    assert len(result) == 2

    assert result["EQ-001"]["maintenance_count"] == 3
    assert result["EQ-001"]["last_temperature_c"] == 30.0
    assert result["EQ-001"]["last_vibration_mm_s"] == 3.0

    assert result["EQ-002"]["maintenance_count"] == 0
    assert result["EQ-002"]["corrective_count"] == 0
    assert result["EQ-002"]["last_measured_at"] is None
    assert result["EQ-002"]["mttr_minutes"] is None
