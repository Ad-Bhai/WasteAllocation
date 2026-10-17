"""Data Import view for uploading CSV/Parquet datasets, schema guides, and live validation."""
import streamlit as st
import pandas as pd

from wastewise.validation.schema import DATASET_SCHEMAS
from wastewise.validation.validator import DataValidator
from wastewise.ingestion.loader import DataLoader
from wastewise.ingestion.samples import load_sample_datasets


def render_import_view():
    st.subheader("📥 Data Import & Schema Validation")
    st.markdown(
        "Upload your grocery CSV or Parquet datasets below, or initialize the pre-packaged sample datasets to test immediately."
    )

    # Quick Actions
    qa_col1, qa_col2, qa_col3 = st.columns([1.5, 1.5, 2])
    with qa_col1:
        if st.button("🔄 Reset to Default Sample Data", use_container_width=True, type="secondary"):
            samples = load_sample_datasets()
            st.session_state["raw_products"] = samples["products"]
            st.session_state["raw_inventory"] = samples["inventory"]
            st.session_state["raw_expiry"] = samples["expiry"]
            st.session_state["raw_sales"] = samples["sales"]
            st.session_state["trigger_pipeline_run"] = True
            st.toast("✅ Reset to default sample grocery datasets and running pipeline!", icon="🥑")
            st.rerun()

    with qa_col2:
        if st.button("🚀 Run Pipeline on Staged Data", use_container_width=True, type="primary"):
            st.session_state["trigger_pipeline_run"] = True
            st.rerun()

    st.markdown("<div style='height: 14px;'></div>", unsafe_allow_html=True)

    # Tabs for the 4 core datasets
    tab_prod, tab_inv, tab_exp, tab_sales = st.tabs([
        "🏷️ Products & Catalog",
        "📦 Inventory & Stock",
        "⏳ Expiry Dates",
        "🛒 Sales Transactions"
    ])

    def render_dataset_uploader(dataset_key: str, tab_title: str):
        schema = DATASET_SCHEMAS[dataset_key]
        raw_key = f"raw_{dataset_key}"

        st.markdown(f"#### {schema['display_name']}")
        st.caption(schema["description"])

        col_up, col_info = st.columns([1.5, 1])

        with col_up:
            uploaded = st.file_uploader(
                f"Upload {schema['display_name']} (.csv or .parquet)",
                type=["csv", "parquet"],
                key=f"uploader_{dataset_key}"
            )
            if uploaded is not None:
                df, err = DataLoader.load_file(uploaded, filename=uploaded.name)
                if err:
                    st.error(f"❌ Upload Failed: {err}")
                elif df is not None:
                    st.session_state[raw_key] = df
                    st.success(f"Uploaded {uploaded.name} ({len(df):,} rows)")

        with col_info:
            with st.expander("📖 Expected Schema & Column Rules", expanded=False):
                req = ", ".join([f"`{c}`" for c in schema["required_columns"]])
                opt = ", ".join([f"`{c}`" for c in schema.get("optional_columns", [])])
                st.markdown(f"**Required Columns:**\n{req}")
                if opt:
                    st.markdown(f"**Optional Columns:**\n{opt}")
                st.markdown(f"**Primary Key:** `{schema.get('primary_key', 'None')}`")
                
                # Download sample CSV
                sample_data = st.session_state.get(raw_key)
                if sample_data is not None and not sample_data.empty:
                    csv_bytes = sample_data.head(5).to_csv(index=False).encode('utf-8')
                    st.download_button(
                        f"⬇️ Download Sample {schema['display_name']} CSV",
                        data=csv_bytes,
                        file_name=f"sample_{dataset_key}.csv",
                        mime="text/csv",
                        use_container_width=True
                    )

        # Validation status on current in-memory raw dataframe
        current_df = st.session_state.get(raw_key)
        if current_df is not None and not current_df.empty:
            report = DataValidator.validate_dataset(current_df, dataset_key)
            
            # Show summary pill
            v_col1, v_col2, v_col3, v_col4 = st.columns(4)
            with v_col1:
                st.metric("Total Ingested Rows", f"{report.total_rows:,}")
            with v_col2:
                st.metric("Clean Rows Passed", f"{report.valid_rows:,}")
            with v_col3:
                st.metric("Rows with Schema Issues", f"{report.invalid_rows:,}")
            with v_col4:
                status_color = "🟢 Valid" if report.is_valid else "🔴 Schema Errors"
                st.metric("Validation Status", status_color)

            if report.has_errors:
                for err in report.errors:
                    st.error(f"**Error in `{err.column or 'Dataset'}`:** {err.message}")

            if report.warnings:
                for warn in report.warnings:
                    st.warning(f"**Warning in `{warn.column or 'Dataset'}`:** {warn.message}")

            # Preview Data
            with st.expander(f"👀 Preview Loaded Data ({len(current_df)} rows)", expanded=False):
                st.dataframe(current_df.head(20), use_container_width=True)
        else:
            st.info(f"No data currently staged for {schema['display_name']}. Please upload a file or click 'Reset to Default Sample Data'.")

    with tab_prod:
        render_dataset_uploader("products", "Products")
    with tab_inv:
        render_dataset_uploader("inventory", "Inventory")
    with tab_exp:
        render_dataset_uploader("expiry", "Expiry")
    with tab_sales:
        render_dataset_uploader("sales", "Sales")
