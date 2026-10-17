"""Tests for dataset validation engine and schema compliance."""
import pytest
import pandas as pd
from wastewise.validation.validator import DataValidator
from wastewise.ingestion.samples import generate_sample_datasets


@pytest.fixture
def sample_data():
    return generate_sample_datasets()


def test_valid_datasets(sample_data):
    """Verifies that pre-packaged sample datasets pass validation with zero errors."""
    for name in ["products", "inventory", "expiry", "sales"]:
        df = sample_data[name]
        report = DataValidator.validate_dataset(df, name)
        assert report.is_valid is True, f"{name} should be valid but got errors: {report.errors}"
        assert report.total_rows > 0
        assert len(report.missing_columns) == 0


def test_missing_required_column():
    """Detects missing mandatory columns and reports an explicit error."""
    invalid_prod_df = pd.DataFrame([
        {"product_name": "Milk", "category": "Dairy", "unit_cost": 2.0} # missing product_id & unit_price
    ])
    report = DataValidator.validate_dataset(invalid_prod_df, "products")
    assert report.is_valid is False
    assert "product_id" in report.missing_columns
    assert "unit_price" in report.missing_columns
    assert any("Missing mandatory column" in e.message for e in report.errors)


def test_malformed_dates():
    """Detects invalid date strings in date columns."""
    bad_dates_df = pd.DataFrame([
        {"batch_id": "B1", "product_id": "P1", "expiry_date": "not-a-real-date"},
        {"batch_id": "B2", "product_id": "P1", "expiry_date": "2026-10-25"}
    ])
    report = DataValidator.validate_dataset(bad_dates_df, "expiry")
    assert report.is_valid is False
    assert any("unparseable date" in e.message for e in report.errors)


def test_negative_values():
    """Detects negative numeric values in cost or stock fields."""
    negative_stock_df = pd.DataFrame([
        {"inventory_id": "INV-1", "product_id": "P1", "batch_id": "B1", "stock_date": "2026-10-15", "current_stock": -15}
    ])
    report = DataValidator.validate_dataset(negative_stock_df, "inventory")
    assert report.is_valid is False
    assert any("below allowed minimum" in e.message for e in report.errors)


def test_relational_validation(sample_data):
    """Detects foreign key references to missing products."""
    orphaned_inv_df = pd.DataFrame([
        {"inventory_id": "INV-99", "product_id": "NON_EXISTENT_PRD", "batch_id": "B99", "stock_date": "2026-10-15", "current_stock": 10}
    ])
    rel_report = DataValidator.validate_relationships(
        products_df=sample_data["products"],
        inventory_df=orphaned_inv_df,
        sales_df=None,
        expiry_df=None
    )
    assert len(rel_report.orphaned_inventory_products) == 1
    assert "NON_EXISTENT_PRD" in rel_report.orphaned_inventory_products
    assert len(rel_report.warnings) > 0
