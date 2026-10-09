import os
from pathlib import Path

import psycopg
import pyarrow.dataset as ds
from dotenv import load_dotenv
from psycopg import sql

GOLD_PATH = Path("data/lake/gold")

TABLES = {
    "daily_sensor_metrics": [
        "equipment_id",
        "measurement_date",
        "measurement_count",
        "avg_temperature_c",
        "max_temperature_c",
        "avg_vibration_mm_s",
        "max_vibration_mm_s",
    ],
    "maintenance_kpis": [
        "equipment_id",
        "maintenance_count",
        "corrective_count",
        "total_downtime_minutes",
        "mttr_minutes",
    ],
    "equipment_health": [
        "equipment_id",
        "equipment_name",
        "equipment_type",
        "site_id",
        "site_name",
        "criticality",
        "status",
        "maintenance_count",
        "corrective_count",
        "total_downtime_minutes",
        "mttr_minutes",
        "last_measured_at",
        "last_temperature_c",
        "last_vibration_mm_s",
    ],
}


def load_table(cursor, table_name: str, columns: list[str]) -> int:
    dataset_path = GOLD_PATH / table_name

    if not dataset_path.is_dir():
        raise FileNotFoundError(f"Gold dataset not found: {dataset_path}")

    dataset = ds.dataset(dataset_path, format="parquet")

    missing_columns = set(columns) - set(dataset.schema.names)
    if missing_columns:
        raise ValueError(f"Missing columns in {table_name}: {sorted(missing_columns)}")

    insert_query = sql.SQL("INSERT INTO {} ({}) VALUES ({})").format(
        sql.Identifier("gold", table_name),
        sql.SQL(", ").join(map(sql.Identifier, columns)),
        sql.SQL(", ").join(sql.Placeholder() for _ in columns),
    )

    row_count = 0

    for batch in dataset.to_batches(columns=columns, batch_size=1000):
        records = batch.to_pylist()

        if not records:
            continue

        values = [tuple(record[column] for column in columns) for record in records]

        cursor.executemany(insert_query, values)
        row_count += len(values)

    return row_count


def main() -> None:
    load_dotenv()

    connection_params = {
        "host": os.getenv("POSTGRES_HOST", "localhost"),
        "port": int(os.getenv("POSTGRES_PORT", "5433")),
        "dbname": os.getenv("POSTGRES_DB", "smartmaint"),
        "user": os.getenv("POSTGRES_USER", "smartmaint_user"),
        "password": os.getenv("POSTGRES_PASSWORD"),
    }

    with psycopg.connect(**connection_params) as connection:
        with connection.transaction():
            with connection.cursor() as cursor:
                for table_name in TABLES:
                    cursor.execute(
                        sql.SQL("TRUNCATE TABLE {}").format(
                            sql.Identifier("gold", table_name)
                        )
                    )

                for table_name, columns in TABLES.items():
                    count = load_table(cursor, table_name, columns)
                    print(f"Loaded gold.{table_name}: {count:,} rows")

    print("Gold warehouse load completed successfully.")


if __name__ == "__main__":
    main()
