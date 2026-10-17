"""Tests for data cleaner, normalization, missing values, and deduplication."""
import pytest
import pandas as pd
from wastewise.etl.cleaner import DataCleaner


def test_column_name_normalization():
    df = pd.DataFrame(columns=[" Product ID ", "Product-Name", "Unit Cost", "CATEGORY"])
    clean_df = DataCleaner.normalize_column_names(df)
    assert list(clean_df.columns) == ["product_id", "product_name", "unit_cost", "category"]


def test_products_cleaning_and_deduplication():
    df = pd.DataFrame([
        {"product_id": "PRD-1", "product_name": "Milk", "category": "Dairy", "unit_cost": "2.10", "unit_price": "3.50", "supplier": "Farm A"},
        # Duplicate with updated price (should keep last)
        {"product_id": "PRD-1", "product_name": "Milk", "category": "Dairy", "unit_cost": "2.20", "unit_price": "3.60", "supplier": "Farm B"},
        # Row with missing product_id (should be dropped)
        {"product_id": "  ", "product_name": "Bad", "category": "Dairy", "unit_cost": 1.0, "unit_price": 2.0},
        # Row with negative cost (should be dropped)
        {"product_id": "PRD-2", "product_name": "Bread", "category": "Bakery", "unit_cost": -1.0, "unit_price": 2.5}
    ])
    clean_df, audit = DataCleaner.clean_products(df)
    assert len(clean_df) == 1
    assert clean_df.iloc[0]["product_id"] == "PRD-1"
    assert clean_df.iloc[0]["unit_cost"] == 2.20  # retained last
    assert audit.deduped_rows == 1
    assert audit.dropped_rows == 3


def test_inventory_cleaning_defaults():
    df = pd.DataFrame([
        {"inventory_id": "INV-1", "product_id": "PRD-1", "batch_id": "B1", "stock_date": "2026-10-15", "current_stock": "25", "location": None}
    ])
    clean_df, audit = DataCleaner.clean_inventory(df)
    assert len(clean_df) == 1
    assert clean_df.iloc[0]["location"] == "Main Floor"
    assert clean_df.iloc[0]["current_stock"] == 25.0
