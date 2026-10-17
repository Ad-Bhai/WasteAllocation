"""Inventory recommendation engine generating transparent, data-backed actions."""
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
import pandas as pd


@dataclass
class RecommendationItem:
    rec_id: str
    rec_type: str  # "IMMEDIATE_CLEARANCE", "CURTAIL_ORDER", "DEAD_STOCK", "CATEGORY_ALERT"
    urgency: str   # "CRITICAL", "HIGH", "MEDIUM", "INFORMATIONAL"
    target_name: str
    target_id: str
    category: str
    headline: str
    action_plan: str
    supporting_data: Dict[str, Any]
    calculation_breakdown: str
    potential_loss_at_risk: float


class RecommendationEngine:
    """Produces actionable, auditable inventory and waste reduction recommendations."""

    @staticmethod
    def generate_recommendations(analytics_df: pd.DataFrame) -> List[RecommendationItem]:
        if analytics_df.empty:
            return []

        recommendations: List[RecommendationItem] = []
        rec_counter = 1

        # 1. Immediate Clearance: Products Expired or Nearing Expiry (<= 2 days)
        critical_df = analytics_df[analytics_df["expiry_risk_category"].isin(["Expired", "Critical (<=2d)"])]
        for _, row in critical_df.iterrows():
            days = row.get("days_to_expiry")
            is_expired = days is not None and days < 0
            urgency = "CRITICAL"
            stock = row["current_stock"]
            cost_loss = row["estimated_cost_loss"]
            daily_sales = row.get("avg_daily_sales", 0.0)

            if is_expired:
                headline = f"Audit & Remove Expired Batch: {row['product_name']}"
                action = (
                    f"Immediate physical pull required for batch {row.get('batch_id', 'N/A')}. "
                    f"Quarantine {stock} units from shelf display to prevent customer purchase of expired product. "
                    "Log shrink write-off and review supplier delivery lead times."
                )
                breakdown = (
                    f"Product expired ({abs(days)} day(s) ago). "
                    f"Entire stock ({stock} units) is spoiled. Sunk procurement loss = {stock} units × ${row['unit_cost']:.2f} = ${cost_loss:.2f}."
                )
            else:
                headline = f"Priority Clearance Markdown: {row['product_name']}"
                suggested_discount = 30 if days <= 1 else 20
                action = (
                    f"Apply immediate {suggested_discount}% promotional discount today. "
                    f"Relocate {stock} units from {row.get('location', 'shelf')} to the Quick-Sale / Clearance Bin. "
                    "Enforce FIFO (First-In, First-Out) rotation on remaining backroom stock."
                )
                breakdown = (
                    f"Batch has only {days} day(s) remaining before expiration. "
                    f"Current sales velocity is {daily_sales:.1f} units/day. At this pace, {max(0, stock - (daily_sales * max(0, days))):.0f} "
                    f"units will remain unsold and spoil unless accelerated. Sunk capital at risk: ${cost_loss:.2f}."
                )

            recommendations.append(RecommendationItem(
                rec_id=f"REC-{rec_counter:03d}",
                rec_type="IMMEDIATE_CLEARANCE",
                urgency=urgency,
                target_name=row["product_name"],
                target_id=row["product_id"],
                category=row.get("category", "General"),
                headline=headline,
                action_plan=action,
                supporting_data={
                    "Batch ID": row.get("batch_id", "N/A"),
                    "Current Stock": f"{stock} units",
                    "Days to Expiry": f"{days} days",
                    "Daily Sales Run Rate": f"{daily_sales:.1f} units/day",
                    "Unit Cost": f"${row['unit_cost']:.2f}",
                    "Potential Cost Loss": f"${cost_loss:.2f}"
                },
                calculation_breakdown=breakdown,
                potential_loss_at_risk=cost_loss
            ))
            rec_counter += 1

        # 2. Curtail Order: Repeatedly Overstocked Products
        overstock_df = analytics_df[
            (analytics_df["is_overstocked"] == True) &
            (~analytics_df["expiry_risk_category"].isin(["Expired", "Critical (<=2d)"]))
        ]
        for _, row in overstock_df.iterrows():
            stock = row["current_stock"]
            daily_sales = max(0.1, row.get("avg_daily_sales", 1.0))
            days_stock = row.get("days_of_stock", 0.0)
            days_exp = row.get("days_to_expiry", 0.0)
            cost_loss = row["estimated_cost_loss"]

            # Calculate safe order size (3 days of demand)
            target_stock = round(daily_sales * min(5, days_exp if days_exp > 0 else 5))
            reduction_qty = max(0, stock - target_stock)

            headline = f"Reduce Next Order: {row['product_name']}"
            action = (
                f"Curtail next procurement purchase order. With {days_stock:.0f} days of inventory on hand but only "
                f"{days_exp:.0f} days until expiration, current stock will exceed shelf-life. "
                f"Suspend incoming reorders until stock drops below {row.get('reorder_threshold', 10)} units."
            )
            breakdown = (
                f"Current stock ({stock} units) exceeds projected sales demand before expiration date by ~{reduction_qty} units. "
                f"Formula: Days of Stock ({days_stock:.1f}d) > Expiry Days ({days_exp:.1f}d) × 1.3 buffer. "
                f"Procurement capital at risk: ${cost_loss:.2f}."
            )

            recommendations.append(RecommendationItem(
                rec_id=f"REC-{rec_counter:03d}",
                rec_type="CURTAIL_ORDER",
                urgency="HIGH",
                target_name=row["product_name"],
                target_id=row["product_id"],
                category=row.get("category", "General"),
                headline=headline,
                action_plan=action,
                supporting_data={
                    "Current Stock": f"{stock} units",
                    "Days of Stock": f"{days_stock:.1f} days",
                    "Days to Expiry": f"{days_exp:.0f} days",
                    "Daily Sales Run Rate": f"{daily_sales:.1f} units/day",
                    "Suggested Order Curtailment": f"Hold orders; surplus ~{reduction_qty} units",
                    "Capital at Risk": f"${cost_loss:.2f}"
                },
                calculation_breakdown=breakdown,
                potential_loss_at_risk=cost_loss
            ))
            rec_counter += 1

        # 3. Dead Stock / Stagnant Inventory Investigation
        stagnant_df = analytics_df[
            (analytics_df["avg_daily_sales"] <= 1.0) &
            (analytics_df["current_stock"] >= 15) &
            (~analytics_df["is_overstocked"]) &
            (~analytics_df["expiry_risk_category"].isin(["Expired", "Critical (<=2d)"]))
        ]
        for _, row in stagnant_df.iterrows():
            stock = row["current_stock"]
            sunk_val = round(stock * row["unit_cost"], 2)
            headline = f"Investigate Stagnant Inventory: {row['product_name']}"
            action = (
                f"Audit shelf placement at {row.get('location', 'store floor')}. "
                "Investigate why sales velocity is near zero (<= 1 unit/day). Verify facing visibility, "
                "check price tags, or bundle with faster-moving complementary items."
            )
            breakdown = (
                f"Item has {stock} units in inventory but an average sales velocity of only {row.get('avg_daily_sales', 0):.1f} unit/day. "
                f"Total capital tied up: ${sunk_val:.2f}."
            )

            recommendations.append(RecommendationItem(
                rec_id=f"REC-{rec_counter:03d}",
                rec_type="DEAD_STOCK",
                urgency="MEDIUM",
                target_name=row["product_name"],
                target_id=row["product_id"],
                category=row.get("category", "General"),
                headline=headline,
                action_plan=action,
                supporting_data={
                    "Location": row.get("location", "Floor"),
                    "Current Stock": f"{stock} units",
                    "Daily Sales Run Rate": f"{row.get('avg_daily_sales', 0):.1f} units/day",
                    "Capital Tied Up": f"${sunk_val:.2f}"
                },
                calculation_breakdown=breakdown,
                potential_loss_at_risk=sunk_val
            ))
            rec_counter += 1

        # 4. Department / Category High Shrink Alert
        cat_summary = analytics_df.groupby("category").agg(
            cost_loss=("estimated_cost_loss", "sum"),
            stock=("current_stock", "sum")
        ).reset_index()

        high_loss_cats = cat_summary[cat_summary["cost_loss"] > 50.0]
        for _, cat_row in high_loss_cats.iterrows():
            cat = cat_row["category"]
            c_loss = cat_row["cost_loss"]
            headline = f"Department Shrink Alert: {cat}"
            action = (
                f"Conduct department-level ordering review for {cat}. "
                "Audit shelf cooler temperatures, vendor minimum order quantities (MOQ), and pack sizes. "
                "Negotiate smaller, more frequent delivery batches with suppliers."
            )
            breakdown = (
                f"The {cat} department accounts for ${c_loss:.2f} in total estimated waste loss across on-hand inventory. "
                "High perishable velocity requires tighter delivery scheduling."
            )

            recommendations.append(RecommendationItem(
                rec_id=f"REC-{rec_counter:03d}",
                rec_type="CATEGORY_ALERT",
                urgency="MEDIUM",
                target_name=f"{cat} Category",
                target_id=cat,
                category=cat,
                headline=headline,
                action_plan=action,
                supporting_data={
                    "Category": cat,
                    "Current Stock": f"{cat_row['stock']} units",
                    "Total Department Stock": f"{cat_row['stock']} units",
                    "Aggregate Cost Loss": f"${c_loss:.2f}"
                },
                calculation_breakdown=breakdown,
                potential_loss_at_risk=c_loss
            ))
            rec_counter += 1

        # Sort recommendations by urgency (CRITICAL -> HIGH -> MEDIUM) then by potential loss
        urgency_weights = {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2, "INFORMATIONAL": 3}
        recommendations.sort(key=lambda r: (urgency_weights.get(r.urgency, 9), -r.potential_loss_at_risk))

        return recommendations
