"""Tests for data loader, format detection, and file error handling."""
import io
import pytest
import pandas as pd
from wastewise.ingestion.loader import DataLoader


def test_load_csv_from_buffer():
    csv_bytes = b"product_id,product_name\nPRD-1,Milk\nPRD-2,Bread\n"
    df, err = DataLoader.load_file(csv_bytes, filename="products.csv")
    assert err is None
    assert df is not None
    assert len(df) == 2
    assert "product_id" in df.columns


def test_load_parquet_from_buffer():
    orig_df = pd.DataFrame([{"product_id": "P1", "val": 100}])
    buf = io.BytesIO()
    orig_df.to_parquet(buf, engine="pyarrow")
    buf.seek(0)

    loaded_df, err = DataLoader.load_file(buf, filename="data.parquet")
    assert err is None
    assert loaded_df is not None
    assert len(loaded_df) == 1
    assert loaded_df.iloc[0]["product_id"] == "P1"


def test_unreadable_file_handling():
    corrupt_bytes = b"\x00\x01\x02\x03\xff\xfe\xfd"
    df, err = DataLoader.load_file(corrupt_bytes, filename="bad.parquet")
    assert df is None
    assert err is not None
