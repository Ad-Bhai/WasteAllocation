"""Parquet storage manager for saving and loading processed datasets."""
import json
from pathlib import Path
from typing import Dict, Optional, Tuple, Any
from datetime import datetime
import pandas as pd

from wastewise.config import (
    PROCESSED_DATA_DIR,
    PARQUET_ANALYTICS,
    PARQUET_PRODUCTS,
    PARQUET_INVENTORY,
    PARQUET_EXPIRY,
    PARQUET_SALES,
    PARQUET_PIPELINE_METRICS,
)


class ParquetStore:
    """Manages reading and writing of processed Parquet datasets and execution metadata."""

    @staticmethod
    def save_processed_tables(
        analytics_df: pd.DataFrame,
        products_df: Optional[pd.DataFrame] = None,
        inventory_df: Optional[pd.DataFrame] = None,
        expiry_df: Optional[pd.DataFrame] = None,
        sales_df: Optional[pd.DataFrame] = None,
        run_metadata: Optional[Dict[str, Any]] = None
    ) -> Tuple[bool, Optional[str]]:
        """Persists processed DataFrames as Parquet with snappy compression."""
        try:
            PROCESSED_DATA_DIR.mkdir(parents=True, exist_ok=True)

            if analytics_df is not None and not analytics_df.empty:
                analytics_df.to_parquet(PARQUET_ANALYTICS, engine="pyarrow", compression="snappy", index=False)

            if products_df is not None and not products_df.empty:
                products_df.to_parquet(PARQUET_PRODUCTS, engine="pyarrow", compression="snappy", index=False)

            if inventory_df is not None and not inventory_df.empty:
                inventory_df.to_parquet(PARQUET_INVENTORY, engine="pyarrow", compression="snappy", index=False)

            if expiry_df is not None and not expiry_df.empty:
                expiry_df.to_parquet(PARQUET_EXPIRY, engine="pyarrow", compression="snappy", index=False)

            if sales_df is not None and not sales_df.empty:
                sales_df.to_parquet(PARQUET_SALES, engine="pyarrow", compression="snappy", index=False)

            # Save metadata
            if run_metadata:
                with open(PARQUET_PIPELINE_METRICS, "w", encoding="utf-8") as f:
                    json.dump(run_metadata, f, indent=2, default=str)

            return True, None
        except Exception as e:
            return False, f"Error saving Parquet tables: {str(e)}"

    @staticmethod
    def load_analytics_model() -> Optional[pd.DataFrame]:
        """Loads the joined analytics parquet file if it exists."""
        if PARQUET_ANALYTICS.exists():
            try:
                return pd.read_parquet(PARQUET_ANALYTICS, engine="pyarrow")
            except Exception:
                return None
        return None

    @staticmethod
    def load_all_clean_tables() -> Dict[str, pd.DataFrame]:
        """Loads all clean parquet tables if present."""
        tables = {}
        paths = {
            "products": PARQUET_PRODUCTS,
            "inventory": PARQUET_INVENTORY,
            "expiry": PARQUET_EXPIRY,
            "sales": PARQUET_SALES,
            "analytics": PARQUET_ANALYTICS
        }
        for name, p in paths.items():
            if p.exists():
                try:
                    tables[name] = pd.read_parquet(p, engine="pyarrow")
                except Exception:
                    pass
        return tables

    @staticmethod
    def load_run_metadata() -> Optional[Dict[str, Any]]:
        """Loads execution metadata for the last ETL run."""
        if PARQUET_PIPELINE_METRICS.exists():
            try:
                with open(PARQUET_PIPELINE_METRICS, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                return None
        return None
