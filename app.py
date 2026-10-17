"""WasteWise — Food Waste Analytics & ETL Pipeline
Main Application Entry Point
"""
import streamlit as st
import pandas as pd

from wastewise.ui.styles import CUSTOM_CSS
from wastewise.ui.components import render_header
from wastewise.ui.views.dashboard_view import render_dashboard_view
from wastewise.ui.views.import_view import render_import_view
from wastewise.ui.views.etl_view import render_etl_view
from wastewise.ui.views.sql_view import render_sql_view
from wastewise.ui.views.recommendations_view import render_recommendations_view
from wastewise.ingestion.samples import load_sample_datasets
from wastewise.etl.pipeline import WasteWisePipeline
from wastewise.etl.parquet_store import ParquetStore
from wastewise.etl.pyspark_pipeline import is_spark_available

# Streamlit Page Configuration
st.set_page_config(
    page_title="WasteWise — Food Waste Analytics & ETL",
    page_icon="🥑",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Inject Custom CSS Design System
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)


def initialize_app_state():
    """Initializes session state with sample datasets and runs the initial pipeline if not already executed."""
    if "raw_products" not in st.session_state:
        # Load sample data
        samples = load_sample_datasets()
        st.session_state["raw_products"] = samples["products"]
        st.session_state["raw_inventory"] = samples["inventory"]
        st.session_state["raw_expiry"] = samples["expiry"]
        st.session_state["raw_sales"] = samples["sales"]

    # If analytics_df is not yet built, attempt loading from Parquet or run initial pipeline
    if "analytics_df" not in st.session_state:
        cached_analytics = ParquetStore.load_analytics_model()
        if cached_analytics is not None and not cached_analytics.empty:
            st.session_state["analytics_df"] = cached_analytics
            tables = ParquetStore.load_all_clean_tables()
            st.session_state["clean_inventory"] = tables.get("inventory", pd.DataFrame())
            st.session_state["clean_sales"] = tables.get("sales", pd.DataFrame())
            st.session_state["clean_products"] = tables.get("products", pd.DataFrame())
            st.session_state["clean_expiry"] = tables.get("expiry", pd.DataFrame())
        else:
            # Run initial pipeline on sample data
            pipeline = WasteWisePipeline(preferred_engine="pandas")
            result = pipeline.run(
                products_raw=st.session_state["raw_products"],
                inventory_raw=st.session_state["raw_inventory"],
                expiry_raw=st.session_state["raw_expiry"],
                sales_raw=st.session_state["raw_sales"],
                save_parquet=True
            )
            st.session_state["last_pipeline_result"] = result
            if result.analytics_df is not None:
                st.session_state["analytics_df"] = result.analytics_df
                st.session_state["clean_inventory"] = result.clean_tables.get("inventory")
                st.session_state["clean_sales"] = result.clean_tables.get("sales")
                st.session_state["clean_products"] = result.clean_tables.get("products")
                st.session_state["clean_expiry"] = result.clean_tables.get("expiry")


initialize_app_state()

# Navigation Sidebar
with st.sidebar:
    st.markdown("""
    <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 20px;">
        <span style="font-size: 28px;">🥑</span>
        <div>
            <div style="font-size: 20px; font-weight: 800; color: #f8fafc; font-family: 'Outfit';">WasteWise</div>
            <div style="font-size: 11px; color: #94a3b8; font-weight: 500;">Retail Food Waste Intelligence</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    nav_selection = st.radio(
        "Navigation",
        options=[
            "📈 Analytics Dashboard",
            "📥 Data Import & Schema",
            "⚙️ ETL Pipeline & Storage",
            "🔎 SQL Insights Workbench",
            "💡 Inventory Recommendations"
        ],
        index=0,
        label_visibility="collapsed"
    )

    st.markdown("---")
    st.caption("Quick Actions")
    if st.button("🔄 Reset to Default Samples", use_container_width=True):
        samples = load_sample_datasets()
        st.session_state["raw_products"] = samples["products"]
        st.session_state["raw_inventory"] = samples["inventory"]
        st.session_state["raw_expiry"] = samples["expiry"]
        st.session_state["raw_sales"] = samples["sales"]
        st.session_state["trigger_pipeline_run"] = True
        st.toast("Reset to default sample datasets!", icon="🥑")
        st.rerun()

    st.markdown("---")
    spark_ok, _ = is_spark_available()
    spark_pill = "🟢 PySpark Active" if spark_ok else "⚪ Spark Inactive (Pandas/DuckDB Active)"
    st.markdown(f"""
    <div style="font-size: 11px; color: #64748b;">
        <b>Engine Status:</b><br>{spark_pill}<br><br>
        <b>Storage:</b> Local Parquet (Snappy)<br>
        <b>SQL:</b> DuckDB In-Memory<br>
        <b>Environment:</b> Production Ready
    </div>
    """, unsafe_allow_html=True)

# Top Hero Banner
analytics_df = st.session_state.get("analytics_df", pd.DataFrame())
total_records = len(analytics_df) if analytics_df is not None else 0
render_header(spark_ok=spark_ok, total_records=total_records)

# Routing Views
clean_inv = st.session_state.get("clean_inventory", pd.DataFrame())
clean_sales = st.session_state.get("clean_sales", pd.DataFrame())
clean_prod = st.session_state.get("clean_products", pd.DataFrame())
clean_exp = st.session_state.get("clean_expiry", pd.DataFrame())

if nav_selection == "📈 Analytics Dashboard":
    render_dashboard_view(analytics_df=analytics_df, sales_df=clean_sales, inventory_df=clean_inv)
elif nav_selection == "📥 Data Import & Schema":
    render_import_view()
elif nav_selection == "⚙️ ETL Pipeline & Storage":
    render_etl_view()
elif nav_selection == "🔎 SQL Insights Workbench":
    render_sql_view(
        analytics_df=analytics_df,
        products_df=clean_prod,
        inventory_df=clean_inv,
        expiry_df=clean_exp,
        sales_df=clean_sales
    )
elif nav_selection == "💡 Inventory Recommendations":
    render_recommendations_view(analytics_df=analytics_df)
