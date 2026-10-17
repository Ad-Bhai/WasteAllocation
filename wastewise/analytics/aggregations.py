"""Aggregation calculations for charts and category/supplier breakdowns."""
from typing import List, Optional
import pandas as pd
import numpy as np


class AnalyticsAggregator:
    """Computes multidimensional breakdowns from enriched analytics data."""

    @staticmethod
    def filter_data(
        df: pd.DataFrame,
        categories: Optional[List[str]] = None,
        suppliers: Optional[List[str]] = None,
        risk_levels: Optional[List[str]] = None
    ) -> pd.DataFrame:
        """Filters the analytics DataFrame by user-selected dimensions."""
        if df.empty:
            return df

        filtered = df.copy()
        if categories and "category" in filtered.columns:
            filtered = filtered[filtered["category"].isin(categories)]

        if suppliers and "supplier" in filtered.columns:
            filtered = filtered[filtered["supplier"].isin(suppliers)]

        if risk_levels and "expiry_risk_category" in filtered.columns:
            filtered = filtered[filtered["expiry_risk_category"].isin(risk_levels)]

        return filtered

    @staticmethod
    def category_breakdown(df: pd.DataFrame) -> pd.DataFrame:
        """Aggregates metrics by product category."""
        if df.empty or "category" not in df.columns:
            return pd.DataFrame()

        agg = df.groupby("category").agg(
            total_stock=("current_stock", "sum"),
            total_sold=("total_units_sold", "sum"),
            estimated_waste_units=("estimated_waste_units", "sum"),
            cost_loss=("estimated_cost_loss", "sum"),
            retail_loss=("estimated_retail_loss", "sum"),
            batch_count=("batch_id", "count")
        ).reset_index()

        throughput = agg["total_sold"] + agg["total_stock"]
        agg["waste_rate_pct"] = np.where(throughput > 0, ((agg["estimated_waste_units"] / throughput) * 100).round(2), 0.0)
        return agg.sort_values(by="cost_loss", ascending=False).reset_index(drop=True)

    @staticmethod
    def supplier_breakdown(df: pd.DataFrame) -> pd.DataFrame:
        """Aggregates metrics by supplier."""
        if df.empty or "supplier" not in df.columns:
            return pd.DataFrame()

        agg = df.groupby("supplier").agg(
            products_count=("product_id", "nunique"),
            total_stock=("current_stock", "sum"),
            estimated_waste_units=("estimated_waste_units", "sum"),
            cost_loss=("estimated_cost_loss", "sum"),
            retail_loss=("estimated_retail_loss", "sum")
        ).reset_index()

        return agg.sort_values(by="cost_loss", ascending=False).reset_index(drop=True)

    @staticmethod
    def risk_distribution(df: pd.DataFrame) -> pd.DataFrame:
        """Aggregates counts and loss value by expiry risk category."""
        if df.empty or "expiry_risk_category" not in df.columns:
            return pd.DataFrame()

        risk_order = [
            "Expired",
            "Critical (<=2d)",
            "High Risk (3-5d)",
            "Medium Risk (6-10d)",
            "Safe (>10d)",
            "Date Missing"
        ]

        agg = df.groupby("expiry_risk_category").agg(
            batches_count=("batch_id", "count"),
            units_at_risk=("current_stock", "sum"),
            estimated_waste_units=("estimated_waste_units", "sum"),
            cost_loss=("estimated_cost_loss", "sum")
        ).reset_index()

        # Reorder cleanly
        agg["order"] = agg["expiry_risk_category"].apply(lambda x: risk_order.index(x) if x in risk_order else 99)
        return agg.sort_values(by="order").drop(columns=["order"]).reset_index(drop=True)

    @staticmethod
    def top_wasted_products(df: pd.DataFrame, top_n: int = 10) -> pd.DataFrame:
        """Returns the top products ranked by financial cost loss and waste units."""
        if df.empty:
            return pd.DataFrame()

        cols = [
            "product_id", "product_name", "category", "supplier",
            "current_stock", "days_to_expiry", "expiry_risk_category",
            "estimated_waste_units", "estimated_cost_loss", "estimated_retail_loss",
            "waste_rate_pct", "reorder_recommendation"
        ]
        available_cols = [c for c in cols if c in df.columns]
        return df[available_cols].sort_values(by="estimated_cost_loss", ascending=False).head(top_n).reset_index(drop=True)

    @staticmethod
    def sales_vs_stock_trend(sales_df: pd.DataFrame, inventory_df: pd.DataFrame) -> pd.DataFrame:
        """Builds time-series daily trend of sales vs on-hand stock."""
        if sales_df.empty or "transaction_date" not in sales_df.columns:
            return pd.DataFrame()

        # Daily sales trend
        daily_sales = sales_df.groupby("transaction_date").agg(
            daily_units_sold=("units_sold", "sum"),
            daily_revenue=("total_revenue", "sum")
        ).reset_index().rename(columns={"transaction_date": "date"})

        daily_sales["date"] = pd.to_datetime(daily_sales["date"])
        daily_sales = daily_sales.sort_values(by="date")

        return daily_sales
