"""Bronze layer batch ingestion for SmartMaint."""

import os
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
import psycopg
from dotenv import load_dotenv
from psycopg.rows import dict_row
from psycopg.sql import SQL, Identifier

load_dotenv()
PROJECT_ROOT = Path(__file__).resolve().parents[3]
SENSOR_SOURCE_PATH = PROJECT_ROOT / "data" / "generated" / "sensor_measurements.csv"
BRONZE_DIR = PROJECT_ROOT / "data" / "lake" / "bronze"


def get_postgres_connection() -> psycopg.Connection:
    """Create a connection to the SmartMaint PostgreSQL database."""
    return psycopg.connect(
        host=os.getenv("POSTGRES_HOST", "localhost"),
        port=os.getenv("POSTGRES_PORT", "5433"),
        dbname=os.getenv("POSTGRES_DB"),
        user=os.getenv("POSTGRES_USER"),
        password=os.getenv("POSTGRES_PASSWORD"),
    )


def extract_postgres_table(table_name: str) -> pd.DataFrame:
    """Extract a source table from PostgreSQL into a pandas DataFrame."""
    query = SQL("SELECT * FROM source.{}").format(Identifier(table_name))

    with get_postgres_connection() as connection:
        with connection.cursor(row_factory=dict_row) as cursor:
            cursor.execute(query)
            records = cursor.fetchall()

    return pd.DataFrame(records)


def extract_csv(file_path: Path) -> pd.DataFrame:
    """Extract a CSV source into a pandas DataFrame."""
    if not file_path.exists():
        raise FileNotFoundError(f"Source file not found: {file_path}")

    return pd.read_csv(file_path)


def add_ingestion_metadata(
    dataframe: pd.DataFrame,
    source: str,
    ingested_at: datetime,
) -> pd.DataFrame:
    """Add technical ingestion metadata to a dataset."""
    result = dataframe.copy()

    result["_source"] = source
    result["_ingested_at"] = ingested_at

    return result


def write_bronze(dataframe: pd.DataFrame, dataset_name: str) -> Path:
    """Write a dataset to the Bronze layer in Parquet format."""
    output_dir = BRONZE_DIR / dataset_name
    output_dir.mkdir(parents=True, exist_ok=True)

    output_path = output_dir / f"{dataset_name}.parquet"

    dataframe.to_parquet(
        output_path,
        engine="pyarrow",
        index=False,
    )

    return output_path


def main() -> None:
    """Ingest SmartMaint source datasets into the Bronze layer."""
    equipment = extract_postgres_table("equipment")
    maintenance_events = extract_postgres_table("maintenance_events")
    sensor_measurements = extract_csv(SENSOR_SOURCE_PATH)

    ingested_at = datetime.now(timezone.utc)

    equipment = add_ingestion_metadata(
        equipment,
        "postgresql.source.equipment",
        ingested_at,
    )

    maintenance_events = add_ingestion_metadata(
        maintenance_events,
        "postgresql.source.maintenance_events",
        ingested_at,
    )

    sensor_measurements = add_ingestion_metadata(
        sensor_measurements,
        "csv.sensor_measurements",
        ingested_at,
    )

    equipment_path = write_bronze(equipment, "equipment")
    maintenance_path = write_bronze(
        maintenance_events,
        "maintenance_events",
    )
    sensors_path = write_bronze(
        sensor_measurements,
        "sensor_measurements",
    )

    print(f"Equipment ingested: {len(equipment):,} rows -> {equipment_path}")
    print(
        f"Maintenance events ingested: "
        f"{len(maintenance_events):,} rows -> {maintenance_path}"
    )
    print(
        f"Sensor measurements ingested: "
        f"{len(sensor_measurements):,} rows -> {sensors_path}"
    )


if __name__ == "__main__":
    main()
