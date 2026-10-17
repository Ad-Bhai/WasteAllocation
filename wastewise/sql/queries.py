"""Predefined actionable SQL insight templates with transparent assumptions and formulas."""
from typing import Dict, List, Any

PRESET_QUERIES: Dict[str, Dict[str, Any]] = {
    "highest_waste_risk": {
        "title": "1. Products with Highest Waste or Expiry Risk",
        "description": "Ranks products facing immediate expiration and calculates potential procurement cost losses.",
        "assumptions": (
            "• Sunk Cost Loss = estimated_waste_units * unit_cost.\n"
            "• Critical risk applies when days_to_expiry <= 2 days or already expired.\n"
            "• Projected waste assumes average daily sales run rate remains constant."
        ),
        "sql": """
SELECT 
    product_id,
    product_name,
    category,
    batch_id,
    current_stock,
    days_to_expiry,
    expiry_risk_category,
    avg_daily_sales,
    estimated_waste_units,
    ROUND(estimated_cost_loss, 2) AS estimated_cost_loss,
    ROUND(estimated_retail_loss, 2) AS estimated_retail_loss
FROM analytics
WHERE expiry_risk_category IN ('Expired', 'Critical (<=2d)', 'High Risk (3-5d)')
ORDER BY estimated_cost_loss DESC, days_to_expiry ASC
LIMIT 15;
"""
    },
    "category_losses": {
        "title": "2. Categories Accounting for the Greatest Losses",
        "description": "Summarizes financial waste loss and aggregate waste rates across departments and categories.",
        "assumptions": (
            "• Category Waste Rate % = (Total Estimated Waste Units / (Total Sold + Current Stock)) * 100.\n"
            "• Procurement Loss represents unrecoverable capital tied to spoiled inventory."
        ),
        "sql": """
SELECT 
    category,
    COUNT(DISTINCT product_id) AS products_count,
    SUM(current_stock) AS total_stock_units,
    SUM(total_units_sold) AS total_units_sold,
    ROUND(SUM(estimated_waste_units), 1) AS total_waste_units,
    ROUND(SUM(estimated_cost_loss), 2) AS total_procurement_loss,
    ROUND(SUM(estimated_retail_loss), 2) AS total_lost_retail_value,
    ROUND(
        (SUM(estimated_waste_units) * 100.0) / 
        NULLIF(SUM(total_units_sold) + SUM(current_stock), 0), 
        2
    ) AS category_waste_rate_pct
FROM analytics
GROUP BY category
ORDER BY total_procurement_loss DESC;
"""
    },
    "repeatedly_overstocked": {
        "title": "3. Repeatedly Overstocked Products",
        "description": "Identifies items where days of stock far exceed shelf life, signaling excessive procurement orders.",
        "assumptions": (
            "• Overstocked when days_of_stock > days_to_expiry * 1.3 and current_stock > 10 units.\n"
            "• Days of stock = current_stock / avg_daily_sales."
        ),
        "sql": """
SELECT 
    product_id,
    product_name,
    category,
    supplier,
    current_stock,
    reorder_threshold,
    avg_daily_sales,
    days_of_stock,
    days_to_expiry,
    ROUND(estimated_waste_units, 1) AS surplus_waste_units,
    ROUND(estimated_cost_loss, 2) AS cost_at_risk,
    reorder_recommendation
FROM analytics
WHERE is_overstocked = TRUE
ORDER BY cost_at_risk DESC, days_of_stock DESC;
"""
    },
    "sales_vs_stock_trend": {
        "title": "4. Sales vs Stock Run Rate Comparison",
        "description": "Compares total sales velocity against current on-hand inventory to detect inventory imbalances.",
        "assumptions": (
            "• Turnover Ratio = total_units_sold / NULLIF(current_stock, 0).\n"
            "• Low Turnover (< 0.5) with short shelf life (< 10 days) indicates urgent clearance need."
        ),
        "sql": """
SELECT 
    product_id,
    product_name,
    category,
    current_stock,
    total_units_sold,
    avg_daily_sales,
    days_to_expiry,
    ROUND(total_units_sold / NULLIF(current_stock, 0), 2) AS turnover_ratio,
    expiry_risk_category,
    reorder_recommendation
FROM analytics
ORDER BY turnover_ratio ASC, current_stock DESC
LIMIT 20;
"""
    },
    "dead_inventory_audit": {
        "title": "5. Dead Inventory Audit (High Stock, Zero or Low Sales)",
        "description": "Surfaces capital locked in non-moving stock with minimal sales activity.",
        "assumptions": (
            "• Flagged when avg_daily_sales <= 1.0 unit/day and current_stock >= 15 units.\n"
            "• Sunk Capital = current_stock * unit_cost."
        ),
        "sql": """
SELECT 
    product_id,
    product_name,
    category,
    location,
    current_stock,
    avg_daily_sales,
    ROUND(unit_cost, 2) AS unit_cost,
    ROUND(current_stock * unit_cost, 2) AS sunk_capital_cost,
    days_to_expiry,
    expiry_risk_category
FROM analytics
WHERE avg_daily_sales <= 1.5 AND current_stock >= 15
ORDER BY sunk_capital_cost DESC;
"""
    },
    "supplier_scorecard": {
        "title": "6. Supplier Waste Contribution Scorecard",
        "description": "Evaluates which vendors contribute the highest dollar volume of food waste.",
        "assumptions": (
            "• Sunk Loss by vendor evaluates supply chain quality, batch sizing, and delivery transit freshness."
        ),
        "sql": """
SELECT 
    supplier,
    COUNT(DISTINCT product_id) AS products_supplied,
    SUM(current_stock) AS total_inventory_units,
    ROUND(SUM(estimated_waste_units), 1) AS wasted_units,
    ROUND(SUM(estimated_cost_loss), 2) AS total_procurement_loss,
    ROUND(
        (SUM(estimated_waste_units) * 100.0) / 
        NULLIF(SUM(current_stock) + SUM(total_units_sold), 0), 
        2
    ) AS supplier_waste_rate_pct
FROM analytics
GROUP BY supplier
ORDER BY total_procurement_loss DESC;
"""
    }
}
