"""Data cleaner for normalizing column names, datatypes, missing values, and duplicates."""
from dataclasses import dataclass, field
from typing import Dict, List, Tuple, Any
import pandas as pd
import numpy as np


@dataclass
class CleaningAudit:
    dataset_name: str
    raw_rows: int
    cleaned_rows: int
    dropped_rows: int
    deduped_rows: int
    dropped_reasons: List[str] = field(default_factory=list)


class DataCleaner:
    """Performs standardized data cleaning, normalization, and deduplication."""

    @staticmethod
    def normalize_column_names(df: pd.DataFrame) -> pd.DataFrame:
        """Standardizes column names to lowercase with single underscores."""
        clean_df = df.copy()
        clean_df.columns = (
            clean_df.columns.astype(str)
            .str.strip()
            .str.lower()
            .str.replace(" ", "_")
            .str.replace("-", "_")
        )
        return clean_df

    @staticmethod
    def clean_products(df: pd.DataFrame) -> Tuple[pd.DataFrame, CleaningAudit]:
        raw_rows = len(df)
        audit = CleaningAudit(dataset_name="products", raw_rows=raw_rows, cleaned_rows=0, dropped_rows=0, deduped_rows=0)

        df = DataCleaner.normalize_column_names(df)

        # Drop rows with null or whitespace-only product_id
        valid_id_mask = df["product_id"].notna() & (df["product_id"].astype(str).str.strip() != "")
        dropped_ids = raw_rows - valid_id_mask.sum()
        if dropped_ids > 0:
            audit.dropped_reasons.append(f"Dropped {dropped_ids} rows with missing product_id.")
        df = df[valid_id_mask].copy()

        # String stripping
        for col in ["product_id", "product_name", "category", "supplier"]:
            if col in df.columns:
                df[col] = df[col].astype(str).str.strip()

        # Defaults for optional columns
        if "supplier" not in df.columns or df["supplier"].isna().all():
            df["supplier"] = "General Supplier"
        else:
            df["supplier"] = df["supplier"].replace({"nan": "General Supplier", "": "General Supplier"}).fillna("General Supplier")

        if "category" not in df.columns or df["category"].isna().all():
            df["category"] = "Uncategorized"
        else:
            df["category"] = df["category"].replace({"nan": "Uncategorized", "": "Uncategorized"}).fillna("Uncategorized")

        # Numeric conversions
        df["unit_cost"] = pd.to_numeric(df["unit_cost"], errors="coerce")
        df["unit_price"] = pd.to_numeric(df["unit_price"], errors="coerce")
        if "reorder_threshold" in df.columns:
            df["reorder_threshold"] = pd.to_numeric(df["reorder_threshold"], errors="coerce").fillna(10).astype(int)
        else:
            df["reorder_threshold"] = 10

        # Drop rows where cost or price is NaN or negative
        valid_pricing_mask = (df["unit_cost"].notna()) & (df["unit_cost"] >= 0) & (df["unit_price"].notna()) & (df["unit_price"] >= 0)
        invalid_pricing = len(df) - valid_pricing_mask.sum()
        if invalid_pricing > 0:
            audit.dropped_reasons.append(f"Dropped {invalid_pricing} rows with invalid/negative cost or price.")
        df = df[valid_pricing_mask].copy()

        # Deduplicate on product_id (keep last)
        before_dedup = len(df)
        df = df.drop_duplicates(subset=["product_id"], keep="last")
        audit.deduped_rows = before_dedup - len(df)
        if audit.deduped_rows > 0:
            audit.dropped_reasons.append(f"Removed {audit.deduped_rows} duplicate product_id entries (kept latest).")

        audit.cleaned_rows = len(df)
        audit.dropped_rows = raw_rows - audit.cleaned_rows
        return df.reset_index(drop=True), audit

    @staticmethod
    def clean_inventory(df: pd.DataFrame) -> Tuple[pd.DataFrame, CleaningAudit]:
        raw_rows = len(df)
        audit = CleaningAudit(dataset_name="inventory", raw_rows=raw_rows, cleaned_rows=0, dropped_rows=0, deduped_rows=0)

        df = DataCleaner.normalize_column_names(df)

        # Drop rows with null inventory_id or product_id
        valid_mask = (
            df["inventory_id"].notna() & (df["inventory_id"].astype(str).str.strip() != "") &
            df["product_id"].notna() & (df["product_id"].astype(str).str.strip() != "")
        )
        dropped_ids = raw_rows - valid_mask.sum()
        if dropped_ids > 0:
            audit.dropped_reasons.append(f"Dropped {dropped_ids} rows with missing inventory_id or product_id.")
        df = df[valid_mask].copy()

        # String stripping
        for col in ["inventory_id", "product_id", "batch_id", "location"]:
            if col in df.columns:
                df[col] = df[col].astype(str).str.strip()

        if "location" not in df.columns or df["location"].isna().all():
            df["location"] = "Main Floor"
        else:
            df["location"] = df["location"].replace({"nan": "Main Floor", "": "Main Floor"}).fillna("Main Floor")

        if "batch_id" not in df.columns or df["batch_id"].isna().all():
            df["batch_id"] = "DEFAULT_BATCH"
        else:
            df["batch_id"] = df["batch_id"].replace({"nan": "DEFAULT_BATCH", "": "DEFAULT_BATCH"}).fillna("DEFAULT_BATCH")

        # Convert date
        df["stock_date"] = pd.to_datetime(df["stock_date"], errors="coerce")
        bad_dates = df["stock_date"].isna().sum()
        if bad_dates > 0:
            audit.dropped_reasons.append(f"Dropped {bad_dates} rows with unparseable stock_date.")
            df = df.dropna(subset=["stock_date"]).copy()

        # Convert numeric stock
        df["current_stock"] = pd.to_numeric(df["current_stock"], errors="coerce")
        valid_stock_mask = df["current_stock"].notna() & (df["current_stock"] >= 0)
        bad_stock = len(df) - valid_stock_mask.sum()
        if bad_stock > 0:
            audit.dropped_reasons.append(f"Dropped {bad_stock} rows with invalid/negative stock numbers.")
        df = df[valid_stock_mask].copy()

        # Deduplicate on inventory_id
        before_dedup = len(df)
        df = df.drop_duplicates(subset=["inventory_id"], keep="last")
        audit.deduped_rows = before_dedup - len(df)
        if audit.deduped_rows > 0:
            audit.dropped_reasons.append(f"Removed {audit.deduped_rows} duplicate inventory_id entries.")

        audit.cleaned_rows = len(df)
        audit.dropped_rows = raw_rows - audit.cleaned_rows
        return df.reset_index(drop=True), audit

    @staticmethod
    def clean_expiry(df: pd.DataFrame) -> Tuple[pd.DataFrame, CleaningAudit]:
        raw_rows = len(df)
        audit = CleaningAudit(dataset_name="expiry", raw_rows=raw_rows, cleaned_rows=0, dropped_rows=0, deduped_rows=0)

        df = DataCleaner.normalize_column_names(df)

        # Drop rows with null batch_id or product_id
        valid_mask = (
            df["batch_id"].notna() & (df["batch_id"].astype(str).str.strip() != "") &
            df["product_id"].notna() & (df["product_id"].astype(str).str.strip() != "")
        )
        dropped_ids = raw_rows - valid_mask.sum()
        if dropped_ids > 0:
            audit.dropped_reasons.append(f"Dropped {dropped_ids} rows with missing batch_id or product_id.")
        df = df[valid_mask].copy()

        for col in ["batch_id", "product_id", "status"]:
            if col in df.columns:
                df[col] = df[col].astype(str).str.strip()

        if "status" not in df.columns:
            df["status"] = "Active"
        else:
            df["status"] = df["status"].replace({"nan": "Active", "": "Active"}).fillna("Active")

        # Dates
        df["expiry_date"] = pd.to_datetime(df["expiry_date"], errors="coerce")
        bad_exp = df["expiry_date"].isna().sum()
        if bad_exp > 0:
            audit.dropped_reasons.append(f"Dropped {bad_exp} rows with unparseable expiry_date.")
            df = df.dropna(subset=["expiry_date"]).copy()

        if "received_date" in df.columns:
            df["received_date"] = pd.to_datetime(df["received_date"], errors="coerce")
        else:
            df["received_date"] = pd.NaT

        if "batch_quantity" in df.columns:
            df["batch_quantity"] = pd.to_numeric(df["batch_quantity"], errors="coerce").fillna(0)
            df = df[df["batch_quantity"] >= 0].copy()
        else:
            df["batch_quantity"] = 0

        # Deduplicate on batch_id
        before_dedup = len(df)
        df = df.drop_duplicates(subset=["batch_id"], keep="last")
        audit.deduped_rows = before_dedup - len(df)
        if audit.deduped_rows > 0:
            audit.dropped_reasons.append(f"Removed {audit.deduped_rows} duplicate batch_id entries.")

        audit.cleaned_rows = len(df)
        audit.dropped_rows = raw_rows - audit.cleaned_rows
        return df.reset_index(drop=True), audit

    @staticmethod
    def clean_sales(df: pd.DataFrame, products_df: pd.DataFrame = None) -> Tuple[pd.DataFrame, CleaningAudit]:
        raw_rows = len(df)
        audit = CleaningAudit(dataset_name="sales", raw_rows=raw_rows, cleaned_rows=0, dropped_rows=0, deduped_rows=0)

        df = DataCleaner.normalize_column_names(df)

        # Drop rows with null transaction_id or product_id
        valid_mask = (
            df["transaction_id"].notna() & (df["transaction_id"].astype(str).str.strip() != "") &
            df["product_id"].notna() & (df["product_id"].astype(str).str.strip() != "")
        )
        dropped_ids = raw_rows - valid_mask.sum()
        if dropped_ids > 0:
            audit.dropped_reasons.append(f"Dropped {dropped_ids} rows with missing transaction_id or product_id.")
        df = df[valid_mask].copy()

        for col in ["transaction_id", "product_id"]:
            df[col] = df[col].astype(str).str.strip()

        # Dates
        df["transaction_date"] = pd.to_datetime(df["transaction_date"], errors="coerce")
        bad_dates = df["transaction_date"].isna().sum()
        if bad_dates > 0:
            audit.dropped_reasons.append(f"Dropped {bad_dates} rows with unparseable transaction_date.")
            df = df.dropna(subset=["transaction_date"]).copy()

        # Units sold
        df["units_sold"] = pd.to_numeric(df["units_sold"], errors="coerce")
        valid_units = df["units_sold"].notna() & (df["units_sold"] >= 0)
        bad_units = len(df) - valid_units.sum()
        if bad_units > 0:
            audit.dropped_reasons.append(f"Dropped {bad_units} rows with negative or invalid units_sold.")
        df = df[valid_units].copy()

        # Discount
        if "discount_applied" in df.columns:
            df["discount_applied"] = pd.to_numeric(df["discount_applied"], errors="coerce").fillna(0.0)
            df["discount_applied"] = df["discount_applied"].clip(lower=0.0, upper=100.0)
        else:
            df["discount_applied"] = 0.0

        # Revenue
        if "total_revenue" in df.columns:
            df["total_revenue"] = pd.to_numeric(df["total_revenue"], errors="coerce")
        else:
            df["total_revenue"] = np.nan

        # Deduplicate on transaction_id
        before_dedup = len(df)
        df = df.drop_duplicates(subset=["transaction_id"], keep="last")
        audit.deduped_rows = before_dedup - len(df)
        if audit.deduped_rows > 0:
            audit.dropped_reasons.append(f"Removed {audit.deduped_rows} duplicate transaction_id entries.")

        audit.cleaned_rows = len(df)
        audit.dropped_rows = raw_rows - audit.cleaned_rows
        return df.reset_index(drop=True), audit
