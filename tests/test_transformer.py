"""Tests for data transformation, joins, expiry risk, and waste formulas."""
from datetime import datetime
import pandas as pd
import pytest
from wastewise.etl.transformer import DataTransformer
from wastewise.ingestion.samples import generate_sample_datasets


@pytest.fixture
def sample_clean_tables():
    from wastewise.etl.cleaner import DataCleaner
    raw = generate_sample_datasets()
    return {
        "products": DataCleaner.clean_products(raw["products"])[0],
        "inventory": DataCleaner.clean_inventory(raw["inventory"])[0],
        "expiry": DataCleaner.clean_expiry(raw["expiry"])[0],
        "sales": DataCleaner.clean_sales(raw["sales"])[0]
    }


def test_build_analytics_model(sample_clean_tables):
    ref_date = datetime(2026, 10, 17)
    analytics_df = DataTransformer.build_analytics_model(
        clean_products=sample_clean_tables["products"],
        clean_inventory=sample_clean_tables["inventory"],
        clean_expiry=sample_clean_tables["expiry"],
        clean_sales=sample_clean_tables["sales"],
        reference_date=ref_date
    )
    assert not analytics_df.empty
    assert "estimated_waste_units" in analytics_df.columns
    assert "estimated_cost_loss" in analytics_df.columns
    assert "estimated_retail_loss" in analytics_df.columns
    assert "days_to_expiry" in analytics_df.columns
    assert "expiry_risk_category" in analytics_df.columns
    assert "waste_rate_pct" in analytics_df.columns

    # Verify no NaN in essential metrics
    assert analytics_df["current_stock"].isna().sum() == 0
    assert analytics_df["avg_daily_sales"].isna().sum() == 0


def test_expired_batch_waste_calculation():
    """An already expired batch should have 100% of current stock marked as waste."""
    products = pd.DataFrame([{"product_id": "P1", "product_name": "Test", "category": "Dairy", "unit_cost": 2.0, "unit_price": 4.0, "reorder_threshold": 10}])
    inventory = pd.DataFrame([{"inventory_id": "I1", "product_id": "P1", "batch_id": "B1", "stock_date": pd.to_datetime("2026-10-15"), "current_stock": 20, "location": "Floor"}])
    expiry = pd.DataFrame([{"batch_id": "B1", "product_id": "P1", "received_date": pd.to_datetime("2026-10-10"), "expiry_date": pd.to_datetime("2026-10-14"), "batch_quantity": 20, "status": "Expired"}])
    sales = pd.DataFrame([{"transaction_id": "T1", "product_id": "P1", "transaction_date": pd.to_datetime("2026-10-14"), "units_sold": 2, "discount_applied": 0, "total_revenue": 8.0}])

    ref_date = datetime(2026, 10, 17) # 3 days after expiry date
    res = DataTransformer.build_analytics_model(products, inventory, expiry, sales, reference_date=ref_date)

    row = res.iloc[0]
    assert row["days_to_expiry"] == -3
    assert row["expiry_risk_category"] == "Expired"
    assert row["estimated_waste_units"] == 20.0
    assert row["estimated_cost_loss"] == 40.0  # 20 * 2.0
    assert row["estimated_retail_loss"] == 80.0  # 20 * 4.0


def test_overstocked_flag_detection():
    """Identifies when days of stock drastically exceed remaining shelf-life."""
    products = pd.DataFrame([{"product_id": "P1", "product_name": "Rolls", "category": "Bakery", "unit_cost": 1.0, "unit_price": 2.0, "reorder_threshold": 5}])
    # 50 units in stock, but selling only 1 unit per day (50 days of stock) with 5 days until expiry!
    inventory = pd.DataFrame([{"inventory_id": "I1", "product_id": "P1", "batch_id": "B1", "stock_date": pd.to_datetime("2026-10-15"), "current_stock": 50, "location": "Floor"}])
    expiry = pd.DataFrame([{"batch_id": "B1", "product_id": "P1", "received_date": pd.to_datetime("2026-10-12"), "expiry_date": pd.to_datetime("2026-10-22"), "batch_quantity": 50, "status": "Active"}])
    sales = pd.DataFrame([
        {"transaction_id": f"T{i}", "product_id": "P1", "transaction_date": pd.to_datetime(f"2026-10-1{i}"), "units_sold": 1, "discount_applied": 0, "total_revenue": 2.0}
        for i in range(5)
    ])

    ref_date = datetime(2026, 10, 17) # 5 days remaining
    res = DataTransformer.build_analytics_model(products, inventory, expiry, sales, reference_date=ref_date)
    row = res.iloc[0]

    assert row["is_overstocked"] is True or row["is_overstocked"] == 1
    assert "Curtail Reorder" in row["reorder_recommendation"]
