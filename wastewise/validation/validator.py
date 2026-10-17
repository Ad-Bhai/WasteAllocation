"""Data validation engine for grocery inventory, sales, and expiry data."""
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set, Any
import pandas as pd
import numpy as np

from wastewise.validation.schema import DATASET_SCHEMAS


@dataclass
class ValidationIssue:
    severity: str  # "ERROR" or "WARNING"
    column: Optional[str]
    message: str
    row_count: int = 1
    sample_indices: List[int] = field(default_factory=list)


@dataclass
class DatasetValidationReport:
    dataset_name: str
    is_valid: bool
    total_rows: int
    valid_rows: int
    invalid_rows: int
    errors: List[ValidationIssue] = field(default_factory=list)
    warnings: List[ValidationIssue] = field(default_factory=list)
    missing_columns: List[str] = field(default_factory=list)
    present_columns: List[str] = field(default_factory=list)

    @property
    def has_errors(self) -> bool:
        return len(self.errors) > 0


@dataclass
class RelationalValidationReport:
    is_valid: bool
    orphaned_inventory_products: Set[str] = field(default_factory=set)
    orphaned_sales_products: Set[str] = field(default_factory=set)
    orphaned_expiry_products: Set[str] = field(default_factory=set)
    orphaned_inventory_batches: Set[str] = field(default_factory=set)
    warnings: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)


class DataValidator:
    """Validates grocery datasets against predefined schemas and relational integrity."""

    @staticmethod
    def validate_dataset(df: pd.DataFrame, dataset_name: str) -> DatasetValidationReport:
        if dataset_name not in DATASET_SCHEMAS:
            return DatasetValidationReport(
                dataset_name=dataset_name,
                is_valid=False,
                total_rows=len(df) if df is not None else 0,
                valid_rows=0,
                invalid_rows=len(df) if df is not None else 0,
                errors=[ValidationIssue(severity="ERROR", column=None, message=f"Unknown dataset type: {dataset_name}")]
            )

        schema = DATASET_SCHEMAS[dataset_name]
        errors: List[ValidationIssue] = []
        warnings: List[ValidationIssue] = []

        if df is None or df.empty:
            return DatasetValidationReport(
                dataset_name=dataset_name,
                is_valid=False,
                total_rows=0,
                valid_rows=0,
                invalid_rows=0,
                errors=[ValidationIssue(severity="ERROR", column=None, message="Dataset is completely empty (0 rows).")]
            )

        total_rows = len(df)
        invalid_row_indices: Set[int] = set()

        # 1. Normalize column names (strip whitespace, lowercase for check)
        raw_cols = list(df.columns)
        normalized_cols = {col.strip().lower(): col for col in raw_cols}

        # Check required columns
        missing_required = []
        for req_col in schema["required_columns"]:
            if req_col.lower() not in normalized_cols:
                missing_required.append(req_col)

        if missing_required:
            errors.append(ValidationIssue(
                severity="ERROR",
                column=", ".join(missing_required),
                message=f"Missing mandatory column(s): {', '.join(missing_required)}"
            ))
            return DatasetValidationReport(
                dataset_name=dataset_name,
                is_valid=False,
                total_rows=total_rows,
                valid_rows=0,
                invalid_rows=total_rows,
                errors=errors,
                missing_columns=missing_required,
                present_columns=raw_cols
            )

        # 2. Check Primary Key uniqueness & nullability
        pk_col_name = schema.get("primary_key")
        if pk_col_name and pk_col_name.lower() in normalized_cols:
            actual_pk_col = normalized_cols[pk_col_name.lower()]
            pk_series = df[actual_pk_col]

            # Null PKs
            null_pk_mask = pk_series.isna() | (pk_series.astype(str).str.strip() == "")
            null_pks = df[null_pk_mask]
            if not null_pks.empty:
                errors.append(ValidationIssue(
                    severity="ERROR",
                    column=pk_col_name,
                    message=f"Primary key '{pk_col_name}' contains {len(null_pks)} null/empty value(s).",
                    row_count=len(null_pks),
                    sample_indices=null_pks.index.tolist()[:5]
                ))
                invalid_row_indices.update(null_pks.index.tolist())

            # Duplicate PKs
            valid_pks = pk_series[~null_pk_mask]
            dupes = valid_pks[valid_pks.duplicated(keep=False)]
            if not dupes.empty:
                warnings.append(ValidationIssue(
                    severity="WARNING",
                    column=pk_col_name,
                    message=f"Found {len(dupes)} duplicate primary key values in '{pk_col_name}'. Deduplication rule will retain the latest record.",
                    row_count=len(dupes),
                    sample_indices=dupes.index.tolist()[:5]
                ))

        # 3. Check Data Types & Constraints
        column_types = schema.get("column_types", {})
        constraints = schema.get("value_constraints", {})

        for norm_name, actual_col in normalized_cols.items():
            col_type = column_types.get(norm_name)
            if not col_type:
                continue

            series = df[actual_col]

            # Date validation
            if col_type == "date":
                # Attempt to parse non-null dates
                non_nulls = series.dropna()
                # Skip already converted datetime
                if not pd.api.types.is_datetime64_any_dtype(non_nulls):
                    bad_dates = []
                    for idx, val in non_nulls.items():
                        try:
                            pd.to_datetime(val)
                        except Exception:
                            bad_dates.append(idx)
                    if bad_dates:
                        errors.append(ValidationIssue(
                            severity="ERROR",
                            column=actual_col,
                            message=f"Column '{actual_col}' contains {len(bad_dates)} unparseable date values (expected YYYY-MM-DD or standard date format).",
                            row_count=len(bad_dates),
                            sample_indices=bad_dates[:5]
                        ))
                        invalid_row_indices.update(bad_dates)

            # Numeric validation
            elif col_type == "numeric":
                # Convert to numeric, finding coercible issues
                num_series = pd.to_numeric(series, errors='coerce')
                non_null_original = series[series.notna() & (series.astype(str).str.strip() != "")]
                malformed_nums = non_null_original[num_series.isna()].index.tolist()
                if malformed_nums:
                    errors.append(ValidationIssue(
                        severity="ERROR",
                        column=actual_col,
                        message=f"Column '{actual_col}' contains {len(malformed_nums)} non-numeric/corrupted values.",
                        row_count=len(malformed_nums),
                        sample_indices=malformed_nums[:5]
                    ))
                    invalid_row_indices.update(malformed_nums)

                # Value constraint checks (e.g. min >= 0)
                rule = constraints.get(norm_name)
                if rule and "min" in rule:
                    min_val = rule["min"]
                    below_min = num_series[num_series < min_val].index.tolist()
                    if below_min:
                        errors.append(ValidationIssue(
                            severity="ERROR",
                            column=actual_col,
                            message=f"Column '{actual_col}' contains {len(below_min)} values below allowed minimum ({min_val}). Negative values are invalid for quantities/costs.",
                            row_count=len(below_min),
                            sample_indices=below_min[:5]
                        ))
                        invalid_row_indices.update(below_min)

        valid_count = total_rows - len(invalid_row_indices)
        is_valid = len(errors) == 0

        return DatasetValidationReport(
            dataset_name=dataset_name,
            is_valid=is_valid,
            total_rows=total_rows,
            valid_rows=max(0, valid_count),
            invalid_rows=len(invalid_row_indices),
            errors=errors,
            warnings=warnings,
            missing_columns=[],
            present_columns=raw_cols
        )

    @staticmethod
    def validate_relationships(
        products_df: Optional[pd.DataFrame],
        inventory_df: Optional[pd.DataFrame],
        sales_df: Optional[pd.DataFrame],
        expiry_df: Optional[pd.DataFrame]
    ) -> RelationalValidationReport:
        """Validates foreign keys and cross-dataset integrity."""
        warnings: List[str] = []
        errors: List[str] = []

        if products_df is None or products_df.empty:
            errors.append("Products dataset is missing. Relational integrity cannot be validated.")
            return RelationalValidationReport(is_valid=False, errors=errors)

        prod_id_col = next((c for c in products_df.columns if c.strip().lower() == "product_id"), None)
        if not prod_id_col:
            errors.append("Products dataset does not have 'product_id' column.")
            return RelationalValidationReport(is_valid=False, errors=errors)

        valid_product_ids = set(products_df[prod_id_col].dropna().astype(str).str.strip())

        orphaned_inv: Set[str] = set()
        orphaned_sales: Set[str] = set()
        orphaned_expiry: Set[str] = set()

        if inventory_df is not None and not inventory_df.empty:
            inv_prod_col = next((c for c in inventory_df.columns if c.strip().lower() == "product_id"), None)
            if inv_prod_col:
                inv_pids = set(inventory_df[inv_prod_col].dropna().astype(str).str.strip())
                orphaned_inv = inv_pids - valid_product_ids
                if orphaned_inv:
                    warnings.append(
                        f"Inventory references {len(orphaned_inv)} product_id(s) not found in Products catalog: {list(orphaned_inv)[:3]}"
                    )

        if sales_df is not None and not sales_df.empty:
            sales_prod_col = next((c for c in sales_df.columns if c.strip().lower() == "product_id"), None)
            if sales_prod_col:
                sales_pids = set(sales_df[sales_prod_col].dropna().astype(str).str.strip())
                orphaned_sales = sales_pids - valid_product_ids
                if orphaned_sales:
                    warnings.append(
                        f"Sales transactions reference {len(orphaned_sales)} product_id(s) not found in Products catalog: {list(orphaned_sales)[:3]}"
                    )

        if expiry_df is not None and not expiry_df.empty:
            exp_prod_col = next((c for c in expiry_df.columns if c.strip().lower() == "product_id"), None)
            if exp_prod_col:
                exp_pids = set(expiry_df[exp_prod_col].dropna().astype(str).str.strip())
                orphaned_expiry = exp_pids - valid_product_ids
                if orphaned_expiry:
                    warnings.append(
                        f"Expiry table references {len(orphaned_expiry)} product_id(s) not found in Products catalog: {list(orphaned_expiry)[:3]}"
                    )

        is_valid = len(errors) == 0
        return RelationalValidationReport(
            is_valid=is_valid,
            orphaned_inventory_products=orphaned_inv,
            orphaned_sales_products=orphaned_sales,
            orphaned_expiry_products=orphaned_expiry,
            warnings=warnings,
            errors=errors
        )
