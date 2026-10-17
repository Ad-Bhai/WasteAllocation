"""Interactive SQL Insights workbench with predefined questions, DuckDB execution, and schema inspector."""
import streamlit as st
import pandas as pd

from wastewise.sql.engine import SQLEngine
from wastewise.sql.queries import PRESET_QUERIES
from wastewise.ui.components import render_empty_state


def render_sql_view(
    analytics_df: pd.DataFrame,
    products_df: pd.DataFrame,
    inventory_df: pd.DataFrame,
    expiry_df: pd.DataFrame,
    sales_df: pd.DataFrame
):
    st.subheader("🔎 Actionable SQL Insights & Query Workbench")
    st.markdown(
        "Run ANSI SQL analytical queries against grocery food waste datasets using the local DuckDB SQL engine."
    )

    if analytics_df is None or analytics_df.empty:
        clicked = render_empty_state(
            title="SQL Data Tables Unavailable",
            description="The SQL engine requires processed datasets. Load sample data or run the ETL pipeline first to populate the relational tables.",
            button_label="Load Sample Data & Enable SQL Engine",
            button_key="btn_sql_init"
        )
        if clicked:
            st.session_state["trigger_pipeline_run"] = True
            st.rerun()
        return

    # Initialize SQL Engine in session state
    if "sql_engine" not in st.session_state:
        st.session_state["sql_engine"] = SQLEngine()

    engine: SQLEngine = st.session_state["sql_engine"]
    # Register/Refresh tables
    engine.register_tables(
        analytics_df=analytics_df,
        products_df=products_df,
        inventory_df=inventory_df,
        expiry_df=expiry_df,
        sales_df=sales_df
    )

    # 1. Preset Actionable Questions Selector
    st.markdown("##### 💡 Predefined Actionable Analysis Questions")
    preset_keys = list(PRESET_QUERIES.keys())
    preset_titles = [PRESET_QUERIES[k]["title"] for k in preset_keys]
    
    selected_idx = st.selectbox(
        "Select a core business question to analyze:",
        options=range(len(preset_keys)),
        format_func=lambda i: preset_titles[i],
        key="sql_preset_selector"
    )
    current_preset = PRESET_QUERIES[preset_keys[selected_idx]]

    # Show question description and assumptions
    col_desc, col_assume = st.columns([1.5, 1])
    with col_desc:
        st.info(f"**Business Purpose:** {current_preset['description']}")
    with col_assume:
        with st.expander("📝 Financial Assumptions & Logic", expanded=True):
            st.markdown(current_preset["assumptions"])

    # 2. SQL Query Editor & Schema Helper
    st.markdown("##### 💻 SQL Editor")

    col_editor, col_schema = st.columns([2.5, 1])

    with col_schema:
        st.markdown("**Available Tables:**")
        tables_dict = engine.get_registered_tables()
        for tbl_name, count in tables_dict.items():
            with st.expander(f"`{tbl_name}` ({count:,} rows)", expanded=False):
                schema_df = engine.get_table_schema(tbl_name)
                if not schema_df.empty:
                    st.dataframe(schema_df[["column_name", "column_type"]], use_container_width=True, height=140)

    # Allow custom SQL editing with preset as default
    default_sql = current_preset["sql"].strip()
    with col_editor:
        user_query = st.text_area(
            "SQL Query (DuckDB SQL dialect):",
            value=default_sql,
            height=180,
            key=f"query_box_{selected_idx}"
        )
        run_query = st.button("⚡ Execute Query", type="primary", use_container_width=True)

    # 3. Execute Query and Display Results
    if run_query or "last_sql_result" in st.session_state:
        query_to_run = user_query if run_query else st.session_state.get("last_sql_query", user_query)
        st.session_state["last_sql_query"] = query_to_run

        with st.spinner("Executing analytical query..."):
            res_df, duration_ms, err = engine.execute_query(query_to_run)

        st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)
        if err:
            st.error(f"❌ **SQL Execution Error:**\n```\n{err}\n```")
        elif res_df is not None:
            st.success(f"✅ Returned **{len(res_df):,}** rows in **{duration_ms} ms**.")

            st.dataframe(res_df, use_container_width=True, height=320)

            # Export Query Results
            d_col1, d_col2, _ = st.columns([1, 1, 2])
            with d_col1:
                csv_bytes = res_df.to_csv(index=False).encode('utf-8')
                st.download_button(
                    "📥 Export Result as CSV",
                    data=csv_bytes,
                    file_name="query_result.csv",
                    mime="text/csv",
                    use_container_width=True
                )
            with d_col2:
                try:
                    import io
                    buf = io.BytesIO()
                    res_df.to_parquet(buf, engine="pyarrow", compression="snappy", index=False)
                    st.download_button(
                        "📦 Export Result as Parquet",
                        data=buf.getvalue(),
                        file_name="query_result.parquet",
                        mime="application/octet-stream",
                        use_container_width=True
                    )
                except Exception:
                    pass
