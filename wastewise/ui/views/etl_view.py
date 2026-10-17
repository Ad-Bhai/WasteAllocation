"""ETL Pipeline management view for running transformations, auditing records, and inspecting Parquet files."""
from datetime import datetime
from pathlib import Path
import streamlit as st
import pandas as pd

from wastewise.etl.pipeline import WasteWisePipeline, PipelineResult
from wastewise.etl.pyspark_pipeline import is_spark_available
from wastewise.etl.parquet_store import ParquetStore
from wastewise.config import PROCESSED_DATA_DIR


def render_etl_view():
    st.subheader("⚙️ ETL Pipeline & Parquet Storage")
    st.markdown(
        "Execute the end-to-end cleaning, normalization, foreign key validation, and analytics model enrichment."
    )

    spark_ok, spark_msg = is_spark_available()

    # 1. Engine Configuration & Spark Status
    with st.container():
        st.markdown("##### ⚡ Processing Engine Architecture")
        eng_col1, eng_col2 = st.columns([1.5, 1])

        with eng_col1:
            st.markdown("""
            WasteWise features dual-path data processing architecture:
            - **Local Analytical Engine (Active):** High-performance vector processing with Pandas, PyArrow, and DuckDB.
            - **Distributed PySpark Engine:** Scalable Spark DataFrame execution path for multi-gigabyte grocery retail operations.
            """)
            
            engine_pref = st.radio(
                "Preferred Execution Engine:",
                options=["Pandas & DuckDB (Recommended)", "PySpark (Scalable)"],
                index=0,
                horizontal=True
            )

        with eng_col2:
            if spark_ok:
                st.success(f"🟢 **PySpark Available:** {spark_msg}")
            else:
                st.info(f"ℹ️ **PySpark Status: Inactive**\n\n{spark_msg}")
                with st.expander("🛠️ How to Enable PySpark Engine", expanded=False):
                    st.markdown("""
                    **3-Step Activation Guide:**
                    1. **Install Java 11 or 17 LTS:** Download OpenJDK from [Adoptium](https://adoptium.net) and set `JAVA_HOME`.
                    2. **Install PySpark:** Run `pip install pyspark` in your Python environment.
                    3. **Restart the App:** PySpark will automatically be detected and enabled for distributed DataFrame jobs.
                    """)

    st.markdown("<div style='height: 14px;'></div>", unsafe_allow_html=True)

    # 2. Pipeline Controls
    st.markdown("##### 🚀 Pipeline Parameters & Execution")
    p_col1, p_col2, p_col3 = st.columns([1.5, 1.5, 1])

    with p_col1:
        use_custom_date = st.checkbox("Override Reference Date for Expiry Evaluation", value=False)
        if use_custom_date:
            eval_date = st.date_input("Evaluation Date", value=datetime(2026, 10, 17))
        else:
            eval_date = None
            st.caption("Default: Evaluates expiry against the latest inventory/sales date in dataset.")

    with p_col2:
        persist_parquet = st.checkbox("Save Enriched Output to Parquet", value=True)
        st.caption("Persists snappy-compressed `.parquet` tables to `data/processed/`.")

    with p_col3:
        st.markdown("<div style='height: 24px;'></div>", unsafe_allow_html=True)
        run_clicked = st.button("▶️ Run ETL Pipeline", type="primary", use_container_width=True)

    # Execute pipeline if button clicked or triggered via session state
    if run_clicked or st.session_state.get("trigger_pipeline_run", False):
        st.session_state["trigger_pipeline_run"] = False

        raw_prod = st.session_state.get("raw_products")
        raw_inv = st.session_state.get("raw_inventory")
        raw_exp = st.session_state.get("raw_expiry")
        raw_sales = st.session_state.get("raw_sales")

        if any(df is None or df.empty for df in [raw_prod, raw_inv, raw_exp, raw_sales]):
            st.error("❌ Cannot run pipeline: One or more datasets are missing. Go to 'Data Import' and load sample data or upload files.")
            return

        with st.spinner("Running WasteWise ETL Pipeline (Cleaning, Joining & Metric Enrichment)..."):
            chosen_engine = "pyspark" if "PySpark" in engine_pref and spark_ok else "pandas"
            pipeline = WasteWisePipeline(preferred_engine=chosen_engine)
            
            result: PipelineResult = pipeline.run(
                products_raw=raw_prod,
                inventory_raw=raw_inv,
                expiry_raw=raw_exp,
                sales_raw=raw_sales,
                reference_date=eval_date,
                save_parquet=persist_parquet
            )
            st.session_state["last_pipeline_result"] = result
            if result.analytics_df is not None:
                st.session_state["analytics_df"] = result.analytics_df
                st.session_state["clean_inventory"] = result.clean_tables.get("inventory")
                st.session_state["clean_sales"] = result.clean_tables.get("sales")
                st.session_state["clean_products"] = result.clean_tables.get("products")
                st.session_state["clean_expiry"] = result.clean_tables.get("expiry")

    # 3. Pipeline Run Summary Display
    result: PipelineResult = st.session_state.get("last_pipeline_result")
    if result:
        st.markdown("<div style='height: 16px;'></div>", unsafe_allow_html=True)
        st.markdown("##### 📊 Latest Pipeline Execution Results")

        if result.status == "SUCCESS":
            st.success(f"✅ **ETL Pipeline Completed Successfully!** Processed {result.total_records_processed:,} inventory records in {result.duration_seconds:.2f} seconds ({result.engine_used}).")
        elif result.status == "WARNING":
            st.warning(f"⚠️ **ETL Pipeline Completed with Warnings.** {result.total_records_processed:,} records processed, {result.total_records_skipped:,} rows adjusted/skipped in {result.duration_seconds:.2f} seconds.")
        else:
            st.error(f"❌ **ETL Pipeline Failed:** {result.error_message}")

        # Metrics cards
        c1, c2, c3, c4 = st.columns(4)
        with c1:
            st.metric("Total Ingested Rows", f"{result.total_records_ingested:,}")
        with c2:
            st.metric("Clean Processed Rows", f"{result.total_records_processed:,}")
        with c3:
            st.metric("Skipped / Dropped Rows", f"{result.total_records_skipped:,}")
        with c4:
            st.metric("Runtime Duration", f"{result.duration_seconds * 1000:.0f} ms")

        # Cleaning Audits Breakdown
        st.markdown("###### 🔍 Cleaning & Deduplication Audits by Table")
        t_col1, t_col2, t_col3, t_col4 = st.columns(4)
        tables = [("Products", "products"), ("Inventory", "inventory"), ("Expiry", "expiry"), ("Sales", "sales")]
        cols = [t_col1, t_col2, t_col3, t_col4]

        for (name, key), col in zip(tables, cols):
            audit = result.cleaning_audits.get(key)
            with col:
                if audit:
                    st.markdown(f"""
                    <div style="background: rgba(30,41,59,0.5); padding: 12px; border-radius: 10px; border: 1px solid rgba(255,255,255,0.06);">
                        <div style="font-weight: 700; color: #f8fafc; font-size: 13px;">{name}</div>
                        <div style="font-size: 11px; color: #94a3b8; margin-top: 2px;">Clean: <b>{audit.cleaned_rows}</b> | Dropped: <b>{audit.dropped_rows}</b> | Deduped: <b>{audit.deduped_rows}</b></div>
                    </div>
                    """, unsafe_allow_html=True)

        # Skipped Rows & Attention Log
        if result.skipped_rows_log:
            with st.expander(f"⚠️ Skipped Rows & Audit Log ({len(result.skipped_rows_log)} entries)", expanded=False):
                for item in result.skipped_rows_log:
                    st.text(item)

    # 4. Parquet Files on Disk Inspector
    st.markdown("<div style='height: 20px;'></div>", unsafe_allow_html=True)
    st.markdown("##### 📁 Parquet Storage Inspector (`data/processed/`)")

    parquet_files = list(PROCESSED_DATA_DIR.glob("*.parquet"))
    if parquet_files:
        p_info = []
        for p in parquet_files:
            size_kb = round(p.stat().st_size / 1024, 2)
            try:
                row_count = len(pd.read_parquet(p))
            except Exception:
                row_count = -1
            p_info.append({
                "Filename": p.name,
                "Size (KB)": size_kb,
                "Row Count": f"{row_count:,}" if row_count >= 0 else "N/A",
                "Last Modified": datetime.fromtimestamp(p.stat().st_mtime).strftime("%Y-%m-%d %H:%M:%S")
            })

        st.dataframe(pd.DataFrame(p_info), use_container_width=True)
    else:
        st.info("No Parquet files found in `data/processed/`. Run the pipeline above to generate them.")
