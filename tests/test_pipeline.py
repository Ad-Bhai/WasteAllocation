"""End-to-end tests for WasteWise ETL pipeline and Parquet persistence."""
import pytest
from pathlib import Path
from wastewise.etl.pipeline import WasteWisePipeline
from wastewise.ingestion.samples import generate_sample_datasets
from wastewise.config import PROCESSED_DATA_DIR


@pytest.fixture
def sample_datasets():
    return generate_sample_datasets()


def test_full_pipeline_run_success(sample_datasets):
    """Executes the pipeline end-to-end and validates Parquet output."""
    pipeline = WasteWisePipeline(preferred_engine="pandas")
    result = pipeline.run(
        products_raw=sample_datasets["products"],
        inventory_raw=sample_datasets["inventory"],
        expiry_raw=sample_datasets["expiry"],
        sales_raw=sample_datasets["sales"],
        save_parquet=True
    )
    assert result.status in ["SUCCESS", "WARNING"]
    assert result.total_records_processed > 0
    assert result.analytics_df is not None
    assert not result.analytics_df.empty
    assert result.parquet_saved is True
    assert (PROCESSED_DATA_DIR / "wastewise_analytics.parquet").exists()


def test_pipeline_catastrophic_failure_handling():
    """Verifies safe failure reporting when a required dataset is malformed."""
    import pandas as pd
    bad_prod = pd.DataFrame([{"invalid_col": 123}])
    pipeline = WasteWisePipeline(preferred_engine="pandas")
    result = pipeline.run(
        products_raw=bad_prod,
        inventory_raw=pd.DataFrame(),
        expiry_raw=pd.DataFrame(),
        sales_raw=pd.DataFrame()
    )
    assert result.status == "FAILED"
    assert result.error_message is not None
    assert "schema errors" in result.error_message.lower()
