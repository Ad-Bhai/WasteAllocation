"""Reusable UI presentation components for WasteWise."""
import streamlit as st
from typing import Optional, Dict, Any


def render_header(spark_ok: bool = False, total_records: int = 0):
    """Renders the top application hero banner with active engine pill and record indicator."""
    engine_badge = (
        '<span class="ww-badge ww-badge-safe">⚡ PySpark Engine Active</span>'
        if spark_ok else
        '<span class="ww-badge ww-badge-info">⚡ Pandas & DuckDB Engine Active</span>'
    )
    
    st.markdown(f"""
    <div class="ww-hero-banner">
        <div>
            <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 4px;">
                <span style="font-size: 26px;">🥑</span>
                <span class="ww-hero-title">WasteWise</span>
                <span class="ww-badge ww-badge-info">v1.0 Production</span>
                {engine_badge}
            </div>
            <div class="ww-hero-subtitle">
                Food Waste Analytics, Expiry Risk Detection & Scalable ETL Pipeline for Modern Grocery Retail
            </div>
        </div>
        <div style="text-align: right;">
            <div style="font-size: 11px; text-transform: uppercase; color: #64748b; letter-spacing: 0.05em; font-weight: 600;">Inventory Pipeline Status</div>
            <div style="font-size: 18px; font-weight: 700; color: #38bdf8;">
                {total_records:,} Records In Model
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)


def render_metric_card(
    label: str,
    value: str,
    subtext: str,
    icon: str = "📊",
    accent_color: str = "#6366f1"
):
    """Renders a glassmorphism metric tile."""
    st.markdown(f"""
    <div class="ww-metric-card" style="border-top: 3px solid {accent_color};">
        <div class="ww-metric-label">
            <span>{icon}</span> {label}
        </div>
        <div class="ww-metric-value">{value}</div>
        <div class="ww-metric-subtext">{subtext}</div>
    </div>
    """, unsafe_allow_html=True)


def render_empty_state(
    title: str = "No Analytics Data Loaded",
    description: str = "Please run the ETL pipeline or load the included sample grocery datasets to explore waste metrics, SQL insights, and inventory recommendations.",
    button_label: Optional[str] = "Load Sample Data & Run Pipeline",
    button_key: str = "btn_empty_load"
) -> bool:
    """Renders a clean empty state card with an optional quick-action button."""
    st.markdown(f"""
    <div style="text-align: center; padding: 48px 24px; background: rgba(30, 41, 59, 0.4); border-radius: 16px; border: 1px dashed rgba(255, 255, 255, 0.15); margin: 30px 0;">
        <div style="font-size: 48px; margin-bottom: 12px;">📦</div>
        <h3 style="color: #f1f5f9; margin-bottom: 8px;">{title}</h3>
        <p style="color: #94a3b8; max-width: 550px; margin: 0 auto 20px auto; font-size: 14px; line-height: 1.6;">
            {description}
        </p>
    </div>
    """, unsafe_allow_html=True)

    if button_label:
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            return st.button(button_label, type="primary", use_container_width=True, key=button_key)
    return False


def render_schema_help(dataset_name: str, schema_dict: Dict[str, Any]):
    """Renders the expected schema requirements for a given dataset."""
    st.markdown(f"**Expected format for `{dataset_name}`:**")
    st.write(schema_dict.get("description", ""))

    req = ", ".join([f"`{c}`" for c in schema_dict.get("required_columns", [])])
    opt = ", ".join([f"`{c}`" for c in schema_dict.get("optional_columns", [])])
    
    st.markdown(f"- **Mandatory columns:** {req}")
    if opt:
        st.markdown(f"- **Optional columns:** {opt}")
