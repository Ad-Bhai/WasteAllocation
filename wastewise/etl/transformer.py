"""Data transformer for joins, expiry risk calculation, and waste metric formulas."""
from datetime import datetime
from typing import Optional
import pandas as pd
import numpy as np

from wastewise.config import (
    CRITICAL_EXPIRY_DAYS,
    HIGH_RISK_EXPIRY_DAYS,
    MEDIUM_RISK_EXPIRY_DAYS,
    OVERSTOCK_RATIO,
)


class DataTransformer:
    """Combines cleaned grocery datasets into an enriched analytics model."""

    @staticmethod
    def build_analytics_model(
        clean_products: pd.DataFrame,
        clean_inventory: pd.DataFrame,
        clean_expiry: pd.DataFrame,
        clean_sales: pd.DataFrame,
        reference_date: Optional[datetime] = None
    ) -> pd.DataFrame:
        """
        Integrates products, inventory, expiry, and sales into an enriched analysis-ready model.
        """
        if clean_inventory.empty:
            return pd.DataFrame()

        # Determine reference date
        if reference_date is None:
            # Pick the most recent date available in sales or inventory, or today
            dates = []
            if not clean_sales.empty and "transaction_date" in clean_sales.columns:
                dates.append(clean_sales["transaction_date"].max())
            if not clean_inventory.empty and "stock_date" in clean_inventory.columns:
                dates.append(clean_inventory["stock_date"].max())
            
            if dates:
                ref_dt = pd.to_datetime(max(dates))
            else:
                ref_dt = pd.Timestamp.now().normalize()
        else:
            ref_dt = pd.to_datetime(reference_date).normalize()

        # 1. Aggregate Sales by Product
        if not clean_sales.empty:
            sales_days = max(1, clean_sales["transaction_date"].nunique())
            sales_agg = clean_sales.groupby("product_id").agg(
                total_units_sold=("units_sold", "sum"),
                total_sales_revenue=("total_revenue", "sum"),
                sales_transactions_count=("transaction_id", "count")
            ).reset_index()
            sales_agg["avg_daily_sales"] = (sales_agg["total_units_sold"] / sales_days).round(2)
        else:
            sales_agg = pd.DataFrame(columns=[
                "product_id", "total_units_sold", "total_sales_revenue",
                "sales_transactions_count", "avg_daily_sales"
            ])

        # 2. Prepare Expiry Information (prefer match on batch_id, fallback to product_id)
        # Expiry per batch
        exp_lookup = clean_expiry.copy()

        # 3. Join Inventory with Products
        merged = clean_inventory.merge(clean_products, on="product_id", how="left")

        # 4. Join with Expiry on batch_id and product_id
        if not exp_lookup.empty:
            if "batch_id" in merged.columns and "batch_id" in exp_lookup.columns:
                merged = merged.merge(
                    exp_lookup[["batch_id", "product_id", "received_date", "expiry_date", "batch_quantity", "status"]],
                    on=["batch_id", "product_id"],
                    how="left"
                )
            else:
                merged = merged.merge(
                    exp_lookup[["product_id", "received_date", "expiry_date", "batch_quantity", "status"]],
                    on="product_id",
                    how="left"
                )
        else:
            merged["received_date"] = pd.NaT
            merged["expiry_date"] = pd.NaT
            merged["batch_quantity"] = np.nan
            merged["status"] = "Unknown"

        # 5. Join with Sales Aggregation
        merged = merged.merge(sales_agg, on="product_id", how="left")
        merged["total_units_sold"] = merged["total_units_sold"].fillna(0)
        merged["total_sales_revenue"] = merged["total_sales_revenue"].fillna(0.0)
        merged["sales_transactions_count"] = merged["sales_transactions_count"].fillna(0).astype(int)
        merged["avg_daily_sales"] = merged["avg_daily_sales"].fillna(0.0)

        # Fill missing product attributes if product wasn't found in catalog or column omitted
        if "product_name" not in merged.columns:
            merged["product_name"] = merged["product_id"]
        else:
            merged["product_name"] = merged["product_name"].fillna(merged["product_id"])

        if "category" not in merged.columns:
            merged["category"] = "Uncategorized"
        else:
            merged["category"] = merged["category"].fillna("Uncategorized")

        if "supplier" not in merged.columns:
            merged["supplier"] = "Unknown"
        else:
            merged["supplier"] = merged["supplier"].fillna("Unknown")

        if "unit_cost" not in merged.columns:
            merged["unit_cost"] = 0.0
        else:
            merged["unit_cost"] = merged["unit_cost"].fillna(0.0)

        if "unit_price" not in merged.columns:
            merged["unit_price"] = 0.0
        else:
            merged["unit_price"] = merged["unit_price"].fillna(0.0)

        if "reorder_threshold" not in merged.columns:
            merged["reorder_threshold"] = 10
        else:
            merged["reorder_threshold"] = merged["reorder_threshold"].fillna(10)

        # 6. Calculate Expiry Metrics
        # Days to expiry relative to ref_dt
        has_expiry = merged["expiry_date"].notna()
        days_to_exp = (merged["expiry_date"] - ref_dt).dt.days

        merged["reference_date"] = ref_dt.strftime("%Y-%m-%d")
        merged["days_to_expiry"] = np.where(has_expiry, days_to_exp, np.nan)

        # Expiry Risk Category
        def classify_risk(days):
            if pd.isna(days):
                return "Date Missing"
            if days < 0:
                return "Expired"
            if days <= CRITICAL_EXPIRY_DAYS:
                return "Critical (<=2d)"
            if days <= HIGH_RISK_EXPIRY_DAYS:
                return "High Risk (3-5d)"
            if days <= MEDIUM_RISK_EXPIRY_DAYS:
                return "Medium Risk (6-10d)"
            return "Safe (>10d)"

        merged["expiry_risk_category"] = merged["days_to_expiry"].apply(classify_risk)

        # Days of Stock Remaining (Runout time)
        # current_stock / avg_daily_sales
        merged["days_of_stock"] = np.where(
            merged["avg_daily_sales"] > 0,
            (merged["current_stock"] / merged["avg_daily_sales"]).round(1),
            np.where(merged["current_stock"] > 0, 999.0, 0.0)  # 999 indicates no movement / dead stock
        )

        # 7. Estimated Waste Calculation
        # For expired items: all current stock is wasted
        # For non-expired: stock that cannot be sold before expiration date
        def compute_waste(row):
            stock = row["current_stock"]
            days = row["days_to_expiry"]
            velocity = row["avg_daily_sales"]

            if pd.isna(days):
                return 0.0
            if days < 0:
                return float(stock)
            
            projected_sales = velocity * max(0.0, float(days))
            waste = max(0.0, float(stock) - projected_sales)
            return round(min(float(stock), waste), 2)

        merged["estimated_waste_units"] = merged.apply(compute_waste, axis=1)

        # 8. Financial Loss Metrics
        # Cost Loss = Procurement sunk loss
        merged["estimated_cost_loss"] = (merged["estimated_waste_units"] * merged["unit_cost"]).round(2)
        # Retail Loss = Lost retail sales potential
        merged["estimated_retail_loss"] = (merged["estimated_waste_units"] * merged["unit_price"]).round(2)

        # 9. Waste Rate Percentage
        # waste_rate = estimated_waste_units / (total_units_sold + current_stock) * 100
        total_throughput = merged["total_units_sold"] + merged["current_stock"]
        merged["waste_rate_pct"] = np.where(
            total_throughput > 0,
            ((merged["estimated_waste_units"] / total_throughput) * 100).round(2),
            0.0
        )

        # 10. Overstock and Reorder Flags
        is_overstocked = (
            (merged["days_to_expiry"] > 0) &
            (merged["days_of_stock"] > (merged["days_to_expiry"] * OVERSTOCK_RATIO)) &
            (merged["current_stock"] > 10)
        )
        merged["is_overstocked"] = is_overstocked

        def determine_reorder(row):
            if row["is_overstocked"]:
                return "Overstocked - Curtail Reorder"
            if row["current_stock"] <= row["reorder_threshold"]:
                return "Reorder Required"
            if row["expiry_risk_category"] in ["Critical (<=2d)", "High Risk (3-5d)"]:
                return "Hold Reorder - Clear Batches"
            return "Healthy Stock"

        merged["reorder_recommendation"] = merged.apply(determine_reorder, axis=1)

        return merged
