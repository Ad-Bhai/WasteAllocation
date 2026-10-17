"""Analytics Dashboard view presenting executive KPIs, charts, and breakdown trends."""
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from wastewise.analytics.metrics import compute_kpis
from wastewise.analytics.aggregations import AnalyticsAggregator
from wastewise.ui.components import render_metric_card, render_empty_state


def render_dashboard_view(analytics_df: pd.DataFrame, sales_df: pd.DataFrame, inventory_df: pd.DataFrame):
    st.subheader("📈 Executive Waste & Inventory Analytics")

    if analytics_df is None or analytics_df.empty:
        clicked = render_empty_state(
            title="Analytics Data Empty",
            description="The pipeline has not yet processed any inventory and sales records. Go to the Data Import tab or click below to populate sample datasets and execute the pipeline.",
            button_label="Initialize Sample Data & Run Pipeline",
            button_key="btn_dash_init"
        )
        if clicked:
            st.session_state["trigger_pipeline_run"] = True
            st.rerun()
        return

    # Filter Sidebar / Controls
    with st.expander("🔍 Filter Analytics by Category, Supplier & Risk Level", expanded=False):
        fcol1, fcol2, fcol3 = st.columns(3)

        categories = sorted(analytics_df["category"].dropna().unique().tolist()) if "category" in analytics_df.columns else []
        suppliers = sorted(analytics_df["supplier"].dropna().unique().tolist()) if "supplier" in analytics_df.columns else []
        risk_levels = [
            "Expired", "Critical (<=2d)", "High Risk (3-5d)", "Medium Risk (6-10d)", "Safe (>10d)"
        ]

        with fcol1:
            sel_cats = st.multiselect("Category", options=categories, default=None, placeholder="All categories")
        with fcol2:
            sel_sups = st.multiselect("Supplier", options=suppliers, default=None, placeholder="All suppliers")
        with fcol3:
            sel_risks = st.multiselect("Expiry Risk Level", options=risk_levels, default=None, placeholder="All risk levels")

    # Apply filters
    filtered_df = AnalyticsAggregator.filter_data(
        analytics_df,
        categories=sel_cats if sel_cats else None,
        suppliers=sel_sups if sel_sups else None,
        risk_levels=sel_risks if sel_risks else None
    )

    kpi = compute_kpis(filtered_df)

    # 1. Executive Metric Tiles
    mcol1, mcol2, mcol3, mcol4 = st.columns(4)
    with mcol1:
        render_metric_card(
            label="Total On-Hand Stock",
            value=f"{kpi.total_stock_units:,.0f} units",
            subtext=f"Across {kpi.total_products_tracked} tracked products",
            icon="📦",
            accent_color="#38bdf8"
        )
    with mcol2:
        render_metric_card(
            label="Historical Units Sold",
            value=f"{kpi.total_units_sold:,.0f} units",
            subtext="Over observed sales window",
            icon="🛒",
            accent_color="#10b981"
        )
    with mcol3:
        render_metric_card(
            label="Estimated Waste Units",
            value=f"{kpi.total_waste_units:,.0f} units",
            subtext=f"Overall Waste Rate: {kpi.overall_waste_rate_pct:.1f}%",
            icon="⚠️",
            accent_color="#f59e0b"
        )
    with mcol4:
        render_metric_card(
            label="Procurement Sunk Loss",
            value=f"${kpi.total_cost_loss:,.2f}",
            subtext=f"Lost Retail Rev: ${kpi.total_retail_loss:,.2f}",
            icon="💸",
            accent_color="#f43f5e"
        )

    st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)

    # Secondary KPI row
    s_col1, s_col2, s_col3, s_col4 = st.columns(4)
    with s_col1:
        render_metric_card(
            label="Expired Batches",
            value=f"{kpi.expired_batches_count} batches",
            subtext="Immediate pull required",
            icon="🛑",
            accent_color="#ef4444"
        )
    with s_col2:
        render_metric_card(
            label="Critical Expiry (<=2d)",
            value=f"{kpi.critical_batches_count} batches",
            subtext="Priority markdown candidates",
            icon="⏳",
            accent_color="#f97316"
        )
    with s_col3:
        render_metric_card(
            label="High Risk (3-5d)",
            value=f"{kpi.high_risk_batches_count} batches",
            subtext="Approaching expiration",
            icon="🔔",
            accent_color="#eab308"
        )
    with s_col4:
        render_metric_card(
            label="Overstocked Products",
            value=f"{kpi.overstocked_products_count} products",
            subtext="Days of stock > Expiry life",
            icon="📉",
            accent_color="#8b5cf6"
        )

    st.markdown("<div style='height: 20px;'></div>", unsafe_allow_html=True)

    # 2. Charts Row 1: Expiry Risk Distribution & Category Losses
    ch_col1, ch_col2 = st.columns([1, 1])

    risk_df = AnalyticsAggregator.risk_distribution(filtered_df)
    with ch_col1:
        st.markdown("##### ⏳ Expiry Risk Distribution & Capital at Risk")
        if not risk_df.empty:
            color_map = {
                "Expired": "#ef4444",
                "Critical (<=2d)": "#f97316",
                "High Risk (3-5d)": "#eab308",
                "Medium Risk (6-10d)": "#3b82f6",
                "Safe (>10d)": "#10b981",
                "Date Missing": "#64748b"
            }
            fig_risk = px.bar(
                risk_df,
                x="expiry_risk_category",
                y="cost_loss",
                color="expiry_risk_category",
                color_discrete_map=color_map,
                text="cost_loss",
                labels={"expiry_risk_category": "Risk Level", "cost_loss": "Cost Loss ($)"},
                title=None
            )
            fig_risk.update_traces(
                texttemplate='$%{text:,.2f}',
                textposition='outside',
                marker_line_color='rgba(255,255,255,0.15)',
                marker_line_width=1
            )
            fig_risk.update_layout(
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                font=dict(color='#cbd5e1', family="Plus Jakarta Sans"),
                margin=dict(l=20, r=20, t=20, b=40),
                showlegend=False,
                xaxis=dict(showgrid=False),
                yaxis=dict(showgrid=True, gridcolor='rgba(255,255,255,0.06)')
            )
            st.plotly_chart(fig_risk, use_container_width=True)
        else:
            st.info("No risk distribution data matches the current filters.")

    cat_df = AnalyticsAggregator.category_breakdown(filtered_df)
    with ch_col2:
        st.markdown("##### 🥩 Losses & Waste Rate by Category")
        if not cat_df.empty:
            fig_cat = go.Figure()
            fig_cat.add_trace(go.Bar(
                name="Sunk Cost Loss ($)",
                x=cat_df["category"],
                y=cat_df["cost_loss"],
                marker_color="#f43f5e"
            ))
            fig_cat.add_trace(go.Bar(
                name="Lost Retail Rev ($)",
                x=cat_df["category"],
                y=cat_df["retail_loss"],
                marker_color="#6366f1"
            ))
            fig_cat.update_layout(
                barmode='group',
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                font=dict(color='#cbd5e1', family="Plus Jakarta Sans"),
                margin=dict(l=20, r=20, t=20, b=40),
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
                xaxis=dict(showgrid=False),
                yaxis=dict(showgrid=True, gridcolor='rgba(255,255,255,0.06)')
            )
            st.plotly_chart(fig_cat, use_container_width=True)
        else:
            st.info("No category data matches the current filters.")

    # 3. Charts Row 2: Top Wasted Products & Sales Trend
    st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)
    r2_col1, r2_col2 = st.columns([1, 1])

    top_prod_df = AnalyticsAggregator.top_wasted_products(filtered_df, top_n=8)
    with r2_col1:
        st.markdown("##### 🚨 Top Products Facing Greatest Waste Loss")
        if not top_prod_df.empty:
            fig_top = px.bar(
                top_prod_df,
                x="estimated_cost_loss",
                y="product_name",
                orientation='h',
                color="estimated_cost_loss",
                color_continuous_scale="Reds",
                labels={"estimated_cost_loss": "Cost Loss ($)", "product_name": "Product"},
                text="estimated_cost_loss"
            )
            fig_top.update_traces(
                texttemplate='$%{text:,.2f}',
                textposition='outside'
            )
            fig_top.update_layout(
                yaxis=dict(autorange="reversed", showgrid=False),
                xaxis=dict(showgrid=True, gridcolor='rgba(255,255,255,0.06)'),
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                font=dict(color='#cbd5e1', family="Plus Jakarta Sans"),
                margin=dict(l=20, r=20, t=20, b=30),
                coloraxis_showscale=False
            )
            st.plotly_chart(fig_top, use_container_width=True)
        else:
            st.info("No product ranking data available.")

    trend_df = AnalyticsAggregator.sales_vs_stock_trend(sales_df, inventory_df)
    with r2_col2:
        st.markdown("##### 📊 Daily Sales Volume Trend Over Time")
        if not trend_df.empty:
            fig_trend = px.line(
                trend_df,
                x="date",
                y="daily_units_sold",
                markers=True,
                labels={"date": "Date", "daily_units_sold": "Units Sold"},
                title=None
            )
            fig_trend.update_traces(line_color="#10b981", line_width=3, marker_size=7)
            fig_trend.update_layout(
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                font=dict(color='#cbd5e1', family="Plus Jakarta Sans"),
                margin=dict(l=20, r=20, t=20, b=30),
                xaxis=dict(showgrid=False),
                yaxis=dict(showgrid=True, gridcolor='rgba(255,255,255,0.06)')
            )
            st.plotly_chart(fig_trend, use_container_width=True)
        else:
            st.info("Daily sales trend is unavailable (no sales date records).")

    # 4. Detailed Data Table with Parquet/CSV Export
    st.markdown("<div style='height: 15px;'></div>", unsafe_allow_html=True)
    st.markdown("##### 📋 Enriched Analysis Dataset")

    cols_to_show = [
        "product_id", "product_name", "category", "supplier", "current_stock",
        "avg_daily_sales", "days_of_stock", "days_to_expiry", "expiry_risk_category",
        "estimated_waste_units", "estimated_cost_loss", "estimated_retail_loss",
        "waste_rate_pct", "reorder_recommendation"
    ]
    avail_cols = [c for c in cols_to_show if c in filtered_df.columns]

    st.dataframe(
        filtered_df[avail_cols].style.format({
            "estimated_cost_loss": "${:,.2f}",
            "estimated_retail_loss": "${:,.2f}",
            "avg_daily_sales": "{:,.2f}",
            "waste_rate_pct": "{:.1f}%",
            "days_to_expiry": "{:.0f}"
        }, na_rep="N/A"),
        use_container_width=True,
        height=320
    )

    # Export Buttons
    exp_col1, exp_col2, _ = st.columns([1, 1, 2])
    with exp_col1:
        csv_data = filtered_df.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📥 Download as CSV",
            data=csv_data,
            file_name="wastewise_filtered_analytics.csv",
            mime="text/csv",
            use_container_width=True
        )
    with exp_col2:
        try:
            import io
            buf = io.BytesIO()
            filtered_df.to_parquet(buf, engine="pyarrow", compression="snappy", index=False)
            st.download_button(
                label="📦 Download as Parquet",
                data=buf.getvalue(),
                file_name="wastewise_filtered_analytics.parquet",
                mime="application/octet-stream",
                use_container_width=True
            )
        except Exception:
            pass
