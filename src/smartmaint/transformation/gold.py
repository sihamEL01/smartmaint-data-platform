from pathlib import Path

from pyspark.sql import DataFrame, SparkSession
from pyspark.sql import functions as F
from pyspark.sql.window import Window


def build_daily_sensor_metrics(sensors: DataFrame) -> DataFrame:
    """Aggregate daily sensor readings for each equipment."""

    return (
        sensors.withColumn("measurement_date", F.to_date("measured_at"))
        .groupBy("equipment_id", "measurement_date")
        .agg(
            F.count("*").alias("measurement_count"),
            F.round(F.avg("temperature_c"), 2).alias("avg_temperature_c"),
            F.round(F.max("temperature_c"), 2).alias("max_temperature_c"),
            F.round(F.avg("vibration_mm_s"), 2).alias("avg_vibration_mm_s"),
            F.round(F.max("vibration_mm_s"), 2).alias("max_vibration_mm_s"),
        )
    )


def build_maintenance_kpis(maintenance: DataFrame) -> DataFrame:
    """Calculate maintenance KPIs for each equipment."""

    completed_corrective = (
        (F.col("maintenance_type") == "CORRECTIVE")
        & (F.col("status") == "COMPLETED")
        & F.col("downtime_minutes").isNotNull()
    )

    return maintenance.groupBy("equipment_id").agg(
        F.count("*").alias("maintenance_count"),
        F.sum(F.when(F.col("maintenance_type") == "CORRECTIVE", 1).otherwise(0)).alias(
            "corrective_count"
        ),
        F.sum("downtime_minutes").alias("total_downtime_minutes"),
        F.round(
            F.avg(F.when(completed_corrective, F.col("downtime_minutes"))),
            2,
        ).alias("mttr_minutes"),
    )


def build_equipment_health(
    equipment: DataFrame,
    maintenance_kpis: DataFrame,
    sensors: DataFrame,
) -> DataFrame:
    """Combine equipment information, maintenance KPIs and latest readings."""

    latest_window = Window.partitionBy("equipment_id").orderBy(
        F.col("measured_at").desc(),
        F.col("measurement_id").desc(),
    )

    latest_sensors = (
        sensors.withColumn("row_number", F.row_number().over(latest_window))
        .filter(F.col("row_number") == 1)
        .select(
            "equipment_id",
            F.col("measured_at").alias("last_measured_at"),
            F.col("temperature_c").alias("last_temperature_c"),
            F.col("vibration_mm_s").alias("last_vibration_mm_s"),
        )
    )

    return (
        equipment.select(
            "equipment_id",
            "equipment_name",
            "equipment_type",
            "site_id",
            "site_name",
            "criticality",
            "status",
        )
        .join(maintenance_kpis, on="equipment_id", how="left")
        .join(latest_sensors, on="equipment_id", how="left")
        .fillna(
            {
                "maintenance_count": 0,
                "corrective_count": 0,
                "total_downtime_minutes": 0,
            }
        )
    )


def main() -> None:
    """Build and save the Gold analytical datasets."""

    spark = (
        SparkSession.builder.appName("SmartMaintGold").master("local[*]").getOrCreate()
    )

    silver_path = Path("data/lake/silver")
    gold_path = Path("data/lake/gold")

    try:
        equipment = spark.read.parquet(str(silver_path / "equipment"))
        maintenance = spark.read.parquet(str(silver_path / "maintenance_events"))
        sensors = spark.read.parquet(str(silver_path / "sensor_measurements"))

        daily_metrics = build_daily_sensor_metrics(sensors)
        maintenance_kpis = build_maintenance_kpis(maintenance)
        equipment_health = build_equipment_health(equipment, maintenance_kpis, sensors)

        datasets = {
            "daily_sensor_metrics": daily_metrics,
            "maintenance_kpis": maintenance_kpis,
            "equipment_health": equipment_health,
        }

        for name, dataframe in datasets.items():
            output_path = gold_path / name
            dataframe.write.mode("overwrite").parquet(str(output_path))
            print(f"Gold {name}: {dataframe.count():,} rows")

    finally:
        spark.stop()


if __name__ == "__main__":
    main()
