"""Bronze to Silver transformations for SmartMaint."""

from pathlib import Path

from pyspark.sql import DataFrame, SparkSession
from pyspark.sql import functions as F

PROJECT_ROOT = Path(__file__).resolve().parents[3]
BRONZE_DIR = PROJECT_ROOT / "data" / "lake" / "bronze"
SILVER_DIR = PROJECT_ROOT / "data" / "lake" / "silver"


def create_spark_session() -> SparkSession:
    """Create the Spark session used by Silver transformations."""
    return (
        SparkSession.builder.master("local[*]")
        .appName("SmartMaintSilver")
        .getOrCreate()
    )


def transform_equipment(dataframe: DataFrame) -> DataFrame:
    """Clean and validate equipment data for the Silver layer."""
    allowed_equipment_types = [
        "PUMP",
        "COMPRESSOR",
        "MOTOR",
        "FAN",
        "CONVEYOR",
    ]
    allowed_criticalities = [
        "LOW",
        "MEDIUM",
        "HIGH",
        "CRITICAL",
    ]
    allowed_statuses = [
        "ACTIVE",
        "MAINTENANCE",
        "OUT_OF_SERVICE",
    ]

    return (
        dataframe.dropDuplicates(["equipment_id"])
        .filter(F.col("equipment_id").isNotNull())
        .filter(F.col("equipment_name").isNotNull())
        .filter(F.col("site_id").isNotNull())
        .filter(F.col("installation_date").isNotNull())
        .filter(F.col("equipment_type").isin(allowed_equipment_types))
        .filter(F.col("criticality").isin(allowed_criticalities))
        .filter(F.col("status").isin(allowed_statuses))
    )


def transform_maintenance_events(dataframe: DataFrame) -> DataFrame:
    """Clean and validate maintenance events for the Silver layer."""
    allowed_maintenance_types = [
        "CORRECTIVE",
        "PREVENTIVE",
        "PREDICTIVE",
    ]

    allowed_failure_types = [
        "MECHANICAL",
        "ELECTRICAL",
        "OVERHEATING",
        "VIBRATION",
        "PRESSURE",
        "OTHER",
    ]

    allowed_statuses = [
        "OPEN",
        "IN_PROGRESS",
        "COMPLETED",
        "CANCELLED",
    ]

    return (
        dataframe.dropDuplicates(["maintenance_id"])
        .withColumn(
            "downtime_minutes",
            F.col("downtime_minutes").cast("integer"),
        )
        .filter(F.col("maintenance_id").isNotNull())
        .filter(F.col("equipment_id").isNotNull())
        .filter(F.col("started_at").isNotNull())
        .filter(F.col("maintenance_type").isin(allowed_maintenance_types))
        .filter(F.col("status").isin(allowed_statuses))
        .filter(
            F.col("failure_type").isNull()
            | F.col("failure_type").isin(allowed_failure_types)
        )
        .filter(
            (F.col("maintenance_type") != "CORRECTIVE")
            | F.col("failure_type").isNotNull()
        )
        .filter(F.col("downtime_minutes").isNull() | (F.col("downtime_minutes") >= 0))
        .filter(F.col("ended_at").isNull() | (F.col("ended_at") >= F.col("started_at")))
    )


def transform_sensor_measurements(dataframe: DataFrame) -> DataFrame:
    """Clean and validate IoT sensor measurements for the Silver layer."""
    return (
        dataframe.dropDuplicates(["measurement_id"])
        .withColumn(
            "measured_at",
            F.to_timestamp(
                F.col("measured_at"),
                "yyyy-MM-dd'T'HH:mm:ss",
            ),
        )
        .filter(F.col("measurement_id").isNotNull())
        .filter(F.col("equipment_id").isNotNull())
        .filter(F.col("measured_at").isNotNull())
        .filter(F.col("temperature_c").isNotNull())
        .filter(F.col("vibration_mm_s").isNotNull())
        .filter(F.col("temperature_c").between(-20, 150))
        .filter(F.col("vibration_mm_s").between(0, 100))
        .filter(F.col("pressure_bar").isNull() | F.col("pressure_bar").between(0, 50))
        .filter(F.col("humidity_pct").isNull() | F.col("humidity_pct").between(0, 100))
        .filter(F.col("power_kw").isNull() | F.col("power_kw").between(0, 1000))
    )


def write_silver(
    dataframe: DataFrame,
    dataset_name: str,
) -> Path:
    """Write a transformed dataset to the Silver layer in Parquet format."""
    output_path = SILVER_DIR / dataset_name

    dataframe.write.mode("overwrite").parquet(str(output_path))

    return output_path


def main() -> None:
    """Run SmartMaint Bronze to Silver transformations."""
    spark = create_spark_session()
    spark.sparkContext.setLogLevel("ERROR")

    try:
        # -------------------------
        # Equipment
        # -------------------------
        equipment_path = BRONZE_DIR / "equipment" / "equipment.parquet"

        bronze_equipment = spark.read.parquet(str(equipment_path))

        silver_equipment = transform_equipment(bronze_equipment)

        equipment_output = write_silver(
            silver_equipment,
            "equipment",
        )

        print("\n========== EQUIPMENT ==========")
        print(f"Bronze equipment: {bronze_equipment.count():,}")
        print(f"Silver equipment: {silver_equipment.count():,}")
        print(f"Written to: {equipment_output}")

        # -------------------------
        # Maintenance events
        # -------------------------
        maintenance_path = (
            BRONZE_DIR / "maintenance_events" / "maintenance_events.parquet"
        )

        bronze_maintenance = spark.read.parquet(str(maintenance_path))

        silver_maintenance = transform_maintenance_events(bronze_maintenance)

        maintenance_output = write_silver(
            silver_maintenance,
            "maintenance_events",
        )

        print("\n========== MAINTENANCE EVENTS ==========")
        print(f"Bronze maintenance: {bronze_maintenance.count():,}")
        print(f"Silver maintenance: {silver_maintenance.count():,}")
        print(f"Written to: {maintenance_output}")

        # -------------------------
        # Sensor measurements
        # -------------------------
        sensors_path = (
            BRONZE_DIR / "sensor_measurements" / "sensor_measurements.parquet"
        )

        bronze_sensors = spark.read.parquet(str(sensors_path))

        silver_sensors = transform_sensor_measurements(bronze_sensors)

        sensors_output = write_silver(
            silver_sensors,
            "sensor_measurements",
        )

        print("\n========== SENSOR MEASUREMENTS ==========")
        print(f"Bronze sensors: {bronze_sensors.count():,}")
        print(f"Silver sensors: {silver_sensors.count():,}")
        print(f"Written to: {sensors_output}")

    finally:
        spark.stop()


if __name__ == "__main__":
    main()
