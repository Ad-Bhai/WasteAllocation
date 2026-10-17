"""Tests for local DuckDB analytical SQL engine and predefined queries."""
import pytest
from wastewise.sql.engine import SQLEngine
from wastewise.sql.queries import PRESET_QUERIES
from wastewise.etl.pipeline import WasteWisePipeline
from wastewise.ingestion.samples import generate_sample_datasets


@pytest.fixture
def executed_pipeline_tables():
    raw = generate_sample_datasets()
    pipe = WasteWisePipeline(preferred_engine="pandas")
    res = pipe.run(raw["products"], raw["inventory"], raw["expiry"], raw["sales"], save_parquet=False)
    return res


def test_sql_engine_all_preset_queries(executed_pipeline_tables):
    """Executes every predefined business query to ensure valid SQL syntax and expected schema compatibility."""
    engine = SQLEngine()
    engine.register_tables(
        analytics_df=executed_pipeline_tables.analytics_df,
        products_df=executed_pipeline_tables.clean_tables["products"],
        inventory_df=executed_pipeline_tables.clean_tables["inventory"],
        expiry_df=executed_pipeline_tables.clean_tables["expiry"],
        sales_df=executed_pipeline_tables.clean_tables["sales"]
    )

    for q_key, q_data in PRESET_QUERIES.items():
        sql = q_data["sql"]
        res_df, duration_ms, err = engine.execute_query(sql)
        assert err is None, f"Query '{q_key}' failed with error: {err}"
        assert res_df is not None
        assert duration_ms >= 0


def test_sql_syntax_error_handling():
    """Confirms the engine safely catches SQL syntax errors without throwing unhandled exceptions."""
    engine = SQLEngine()
    res_df, duration_ms, err = engine.execute_query("SELECT * FROM non_existent_table WHERE")
    assert err is not None
    assert res_df is None
