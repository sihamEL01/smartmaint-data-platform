from unittest.mock import MagicMock

import pyarrow as pa
import pyarrow.parquet as pq
import pytest

from smartmaint.warehouse import load_gold


def test_load_table_inserts_records(tmp_path, monkeypatch):
    table_name = "test_metrics"
    dataset_path = tmp_path / table_name
    dataset_path.mkdir()

    table = pa.table(
        {
            "equipment_id": ["EQ-001", "EQ-002"],
            "measurement_count": [10, 20],
        }
    )
    pq.write_table(table, dataset_path / "part-00000.parquet")

    monkeypatch.setattr(load_gold, "GOLD_PATH", tmp_path)

    cursor = MagicMock()

    count = load_gold.load_table(
        cursor,
        table_name,
        ["equipment_id", "measurement_count"],
    )

    assert count == 2
    cursor.executemany.assert_called_once()

    query, records = cursor.executemany.call_args.args

    assert records == [
        ("EQ-001", 10),
        ("EQ-002", 20),
    ]
    assert query is not None


def test_load_table_rejects_missing_dataset(tmp_path, monkeypatch):
    monkeypatch.setattr(load_gold, "GOLD_PATH", tmp_path)

    cursor = MagicMock()

    with pytest.raises(FileNotFoundError):
        load_gold.load_table(
            cursor,
            "missing_table",
            ["equipment_id"],
        )

    cursor.executemany.assert_not_called()


def test_load_table_rejects_missing_columns(tmp_path, monkeypatch):
    dataset_path = tmp_path / "test_metrics"
    dataset_path.mkdir()

    table = pa.table({"equipment_id": ["EQ-001"]})
    pq.write_table(table, dataset_path / "part-00000.parquet")

    monkeypatch.setattr(load_gold, "GOLD_PATH", tmp_path)

    cursor = MagicMock()

    with pytest.raises(ValueError, match="Missing columns"):
        load_gold.load_table(
            cursor,
            "test_metrics",
            ["equipment_id", "measurement_count"],
        )

    cursor.executemany.assert_not_called()
