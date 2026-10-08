"""Unit tests for SmartMaint Silver transformations."""

from datetime import date, datetime

import pytest
from pyspark.sql import SparkSession
from pyspark.sql.types import (
    DateType,
    DoubleType,
    StringType,
    StructField,
    StructType,
    TimestampType,
)

from smartmaint.transformation.silver import (
    transform_equipment,
    transform_maintenance_events,
    transform_sensor_measurements,
)


@pytest.fixture(scope="module")
def spark():
    """Create a Spark session for Silver transformation tests."""
    session = (
        SparkSession.builder.master("local[1]")
        .appName("SmartMaintSilverTests")
        .getOrCreate()
    )
    session.sparkContext.setLogLevel("ERROR")

    yield session

    session.stop()


def test_equipment_removes_duplicates_and_invalid_types(spark):
    """Keep valid equipment and remove duplicates."""
    schema = StructType(
        [
            StructField("equipment_id", StringType()),
            StructField("equipment_name", StringType()),
            StructField("equipment_type", StringType()),
            StructField("site_id", StringType()),
            StructField("installation_date", DateType()),
            StructField("criticality", StringType()),
            StructField("status", StringType()),
        ]
    )

    rows = [
        ("EQ-001", "Pump A", "PUMP", "SITE-01", date(2020, 1, 1), "HIGH", "ACTIVE"),
        ("EQ-001", "Pump A", "PUMP", "SITE-01", date(2020, 1, 1), "HIGH", "ACTIVE"),
        ("EQ-002", "Unknown", "INVALID", "SITE-01", date(2020, 1, 1), "LOW", "ACTIVE"),
    ]

    dataframe = spark.createDataFrame(rows, schema)
    result = transform_equipment(dataframe)

    assert result.count() == 1
    assert result.first()["equipment_id"] == "EQ-001"


def test_maintenance_rejects_negative_downtime(spark):
    """Reject negative downtime and cast valid downtime to integer."""
    schema = StructType(
        [
            StructField("maintenance_id", StringType()),
            StructField("equipment_id", StringType()),
            StructField("maintenance_type", StringType()),
            StructField("failure_type", StringType()),
            StructField("started_at", TimestampType()),
            StructField("ended_at", TimestampType()),
            StructField("downtime_minutes", DoubleType()),
            StructField("status", StringType()),
        ]
    )

    start = datetime(2026, 9, 1, 10, 0)
    end = datetime(2026, 9, 1, 11, 0)

    rows = [
        ("MT-001", "EQ-001", "CORRECTIVE", "MECHANICAL", start, end, 60.0, "COMPLETED"),
        (
            "MT-002",
            "EQ-001",
            "CORRECTIVE",
            "MECHANICAL",
            start,
            end,
            -10.0,
            "COMPLETED",
        ),
    ]

    dataframe = spark.createDataFrame(rows, schema)
    result = transform_maintenance_events(dataframe)

    assert result.count() == 1
    assert result.first()["maintenance_id"] == "MT-001"
    assert result.schema["downtime_minutes"].dataType.simpleString() == "int"


def test_sensors_reject_invalid_temperature_and_cast_timestamp(spark):
    """Reject invalid temperatures and convert measurement timestamps."""
    schema = StructType(
        [
            StructField("measurement_id", StringType()),
            StructField("equipment_id", StringType()),
            StructField("measured_at", StringType()),
            StructField("temperature_c", DoubleType()),
            StructField("vibration_mm_s", DoubleType()),
            StructField("pressure_bar", DoubleType()),
            StructField("humidity_pct", DoubleType()),
            StructField("power_kw", DoubleType()),
        ]
    )

    rows = [
        ("MS-001", "EQ-001", "2026-09-01T10:00:00", 65.0, 3.0, 5.0, 50.0, 20.0),
        ("MS-002", "EQ-001", "2026-09-01T10:30:00", 200.0, 3.0, 5.0, 50.0, 20.0),
    ]

    dataframe = spark.createDataFrame(rows, schema)
    result = transform_sensor_measurements(dataframe)

    assert result.count() == 1
    assert result.first()["measurement_id"] == "MS-001"
    assert result.schema["measured_at"].dataType.simpleString() == "timestamp"
