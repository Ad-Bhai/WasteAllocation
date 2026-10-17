"""High-level KPI and summary metric calculations for WasteWise."""
from dataclasses import dataclass
from typing import Optional, Dict, Any
import pandas as pd


@dataclass
class KPISummary:
    total_stock_units: float = 0.0
    total_units_sold: float = 0.0
    total_waste_units: float = 0.0
    total_cost_loss: float = 0.0
    total_retail_loss: float = 0.0
    overall_waste_rate_pct: float = 0.0
    expired_batches_count: int = 0
    critical_batches_count: int = 0
    high_risk_batches_count: int = 0
    overstocked_products_count: int = 0
    total_products_tracked: int = 0
    is_empty: bool = True


def compute_kpis(df: Optional[pd.DataFrame]) -> KPISummary:
    """Calculates executive summary KPIs from the enriched analytics DataFrame."""
    if df is None or df.empty:
        return KPISummary(is_empty=True)

    total_stock = float(df["current_stock"].sum()) if "current_stock" in df.columns else 0.0
    total_sold = float(df["total_units_sold"].sum()) if "total_units_sold" in df.columns else 0.0
    waste_units = float(df["estimated_waste_units"].sum()) if "estimated_waste_units" in df.columns else 0.0
    cost_loss = float(df["estimated_cost_loss"].sum()) if "estimated_cost_loss" in df.columns else 0.0
    retail_loss = float(df["estimated_retail_loss"].sum()) if "estimated_retail_loss" in df.columns else 0.0

    total_flow = total_sold + total_stock
    waste_rate = round((waste_units / total_flow) * 100, 2) if total_flow > 0 else 0.0

    risk_cats = df["expiry_risk_category"].value_counts() if "expiry_risk_category" in df.columns else pd.Series()
    expired = int(risk_cats.get("Expired", 0))
    critical = int(risk_cats.get("Critical (<=2d)", 0))
    high_risk = int(risk_cats.get("High Risk (3-5d)", 0))

    overstock_count = int(df["is_overstocked"].sum()) if "is_overstocked" in df.columns else 0
    unique_products = int(df["product_id"].nunique()) if "product_id" in df.columns else 0

    return KPISummary(
        total_stock_units=round(total_stock, 1),
        total_units_sold=round(total_sold, 1),
        total_waste_units=round(waste_units, 1),
        total_cost_loss=round(cost_loss, 2),
        total_retail_loss=round(retail_loss, 2),
        overall_waste_rate_pct=waste_rate,
        expired_batches_count=expired,
        critical_batches_count=critical,
        high_risk_batches_count=high_risk,
        overstocked_products_count=overstock_count,
        total_products_tracked=unique_products,
        is_empty=False
    )
