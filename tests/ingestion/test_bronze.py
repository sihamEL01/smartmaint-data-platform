"""Tests for Bronze layer ingestion."""

from datetime import datetime, timezone

import pandas as pd

import smartmaint.ingestion.bronze as bronze


def test_add_ingestion_metadata() -> None:
    """Ingestion metadata should be added without losing source rows."""
    dataframe = pd.DataFrame(
        {
            "equipment_id": ["EQ-0001", "EQ-0002"],
            "equipment_type": ["PUMP", "MOTOR"],
        }
    )
    ingested_at = datetime(2026, 10, 1, 12, 0, tzinfo=timezone.utc)

    result = bronze.add_ingestion_metadata(
        dataframe,
        "postgresql.source.equipment",
        ingested_at,
    )

    assert len(result) == 2
    assert "_source" in result.columns
    assert "_ingested_at" in result.columns
    assert result["_source"].unique().tolist() == ["postgresql.source.equipment"]
    assert (result["_ingested_at"] == ingested_at).all()


def test_extract_csv(tmp_path) -> None:
    """CSV extraction should preserve all source rows."""
    source_path = tmp_path / "sensors.csv"

    pd.DataFrame(
        {
            "measurement_id": ["M-001", "M-002"],
            "temperature_c": [50.0, 55.0],
        }
    ).to_csv(source_path, index=False)

    result = bronze.extract_csv(source_path)

    assert len(result) == 2
    assert list(result.columns) == [
        "measurement_id",
        "temperature_c",
    ]


def test_write_bronze(tmp_path, monkeypatch) -> None:
    """Bronze writer should create a readable Parquet file."""
    monkeypatch.setattr(bronze, "BRONZE_DIR", tmp_path)

    dataframe = pd.DataFrame(
        {
            "equipment_id": ["EQ-0001", "EQ-0002"],
        }
    )

    output_path = bronze.write_bronze(dataframe, "equipment")

    assert output_path.exists()

    result = pd.read_parquet(output_path)

    assert len(result) == 2
    assert result["equipment_id"].tolist() == [
        "EQ-0001",
        "EQ-0002",
    ]
