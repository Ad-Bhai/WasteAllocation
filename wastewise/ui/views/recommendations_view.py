"""Recommendations view displaying transparent, data-backed inventory reduction actions."""
import streamlit as st
import pandas as pd

from wastewise.recommendations.engine import RecommendationEngine, RecommendationItem
from wastewise.ui.components import render_empty_state


def render_recommendations_view(analytics_df: pd.DataFrame):
    st.subheader("💡 Transparent Inventory & Waste Recommendations")
    st.markdown(
        "Data-backed action plans to curtail excess reorders, prioritize clearance markdowns, and eliminate dead stock."
    )

    if analytics_df is None or analytics_df.empty:
        clicked = render_empty_state(
            title="Recommendations Unavailable",
            description="Run the ETL pipeline or load the sample datasets to generate automated data-backed inventory recommendations.",
            button_label="Run Pipeline to Generate Recommendations",
            button_key="btn_rec_init"
        )
        if clicked:
            st.session_state["trigger_pipeline_run"] = True
            st.rerun()
        return

    # Generate recommendations
    all_recs = RecommendationEngine.generate_recommendations(analytics_df)

    if not all_recs:
        st.success("🎉 All inventory levels and expiry dates are currently in a healthy state with zero critical waste risks!")
        return

    # Transparency & Disclaimer Banner
    st.markdown("""
    <div class="ww-notice">
        <b>⚖️ Estimation Transparency & Disclaimer:</b>
        Recommendations are calculated deterministically using observed sales velocity, batch expiration dates, and current stock counts.
        Values labeled as <i>Potential Loss at Risk</i> represent unrecoverable procurement capital if no corrective action is taken; they are decision-support estimates rather than guaranteed savings.
    </div>
    """, unsafe_allow_html=True)

    # Top summary metrics
    total_recs = len(all_recs)
    critical_recs = sum(1 for r in all_recs if r.urgency == "CRITICAL")
    high_recs = sum(1 for r in all_recs if r.urgency == "HIGH")
    total_capital_at_risk = sum(r.potential_loss_at_risk for r in all_recs)

    sc1, sc2, sc3, sc4 = st.columns(4)
    with sc1:
        st.metric("Total Recommendations", f"{total_recs} actions")
    with sc2:
        st.metric("Critical Immediate Actions", f"{critical_recs} items", delta="Urgent", delta_color="inverse")
    with sc3:
        st.metric("High Priority Curtailments", f"{high_recs} items")
    with sc4:
        st.metric("Total Procurement Loss at Risk", f"${total_capital_at_risk:,.2f}")

    st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)

    # Filters
    fcol1, fcol2 = st.columns([1, 1])
    with fcol1:
        urgency_filter = st.multiselect(
            "Filter by Urgency Level:",
            options=["CRITICAL", "HIGH", "MEDIUM", "INFORMATIONAL"],
            default=None,
            placeholder="All urgency levels"
        )
    with fcol2:
        type_filter = st.multiselect(
            "Filter by Recommendation Type:",
            options=["IMMEDIATE_CLEARANCE", "CURTAIL_ORDER", "DEAD_STOCK", "CATEGORY_ALERT"],
            format_func=lambda x: {
                "IMMEDIATE_CLEARANCE": "⚡ Immediate Markdown / Clearance",
                "CURTAIL_ORDER": "📉 Curtail / Reduce Reorder",
                "DEAD_STOCK": "🔍 Dead Stock Investigation",
                "CATEGORY_ALERT": "⚠️ Department Shrink Alert"
            }.get(x, x),
            default=None,
            placeholder="All recommendation types"
        )

    filtered_recs = all_recs
    if urgency_filter:
        filtered_recs = [r for r in filtered_recs if r.urgency in urgency_filter]
    if type_filter:
        filtered_recs = [r for r in filtered_recs if r.rec_type in type_filter]

    st.markdown(f"**Displaying {len(filtered_recs)} Action Plans:**")

    # Render each recommendation card
    urgency_badge_classes = {
        "CRITICAL": "ww-badge-critical",
        "HIGH": "ww-badge-high",
        "MEDIUM": "ww-badge-info",
        "INFORMATIONAL": "ww-badge-safe"
    }

    type_icons = {
        "IMMEDIATE_CLEARANCE": "⚡ Priority Clearance",
        "CURTAIL_ORDER": "📉 Curtail Next Order",
        "DEAD_STOCK": "🔍 Dead Stock Audit",
        "CATEGORY_ALERT": "⚠️ Department Alert"
    }

    for rec in filtered_recs:
        u_class = urgency_badge_classes.get(rec.urgency, "ww-badge-info")
        type_str = type_icons.get(rec.rec_type, rec.rec_type)

        with st.container():
            st.markdown(f"""
            <div class="ww-rec-card">
                <div class="ww-rec-title">
                    <span>{rec.headline}</span>
                    <div>
                        <span class="ww-badge {u_class}">{rec.urgency}</span>
                        <span class="ww-badge ww-badge-info">{type_str}</span>
                    </div>
                </div>
                <div class="ww-action-box">
                    <b>Suggested Action:</b> {rec.action_plan}
                </div>
            </div>
            """, unsafe_allow_html=True)

            with st.expander(f"📊 Supporting Data & Calculation Rationale ({rec.target_name})", expanded=False):
                # Data metrics table
                st.markdown("**Underlying Operational Data:**")
                table_rows = "".join([
                    f"<tr><th>{k}</th><td>{v}</td></tr>" for k, v in rec.supporting_data.items()
                ])
                st.markdown(f"""
                <table class="ww-data-table">
                    {table_rows}
                </table>
                """, unsafe_allow_html=True)

                st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)
                st.markdown(f"**Mathematical Reasoning:**\n\n{rec.calculation_breakdown}")
