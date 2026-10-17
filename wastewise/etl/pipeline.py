"""Main ETL Pipeline orchestrator for WasteWise."""
from dataclasses import dataclass, field
from datetime import datetime
import time
from typing import Dict, List, Optional, Any
import pandas as pd

from wastewise.validation.validator import DataValidator, DatasetValidationReport, RelationalValidationReport
from wastewise.etl.cleaner import DataCleaner, CleaningAudit
from wastewise.etl.transformer import DataTransformer
from wastewise.etl.parquet_store import ParquetStore
from wastewise.etl.pyspark_pipeline import is_spark_available, PySparkETLPipeline
from wastewise.config import PROCESSED_DATA_DIR


@dataclass
class PipelineResult:
    status: str  # "SUCCESS", "WARNING", "FAILED"
    duration_seconds: float
    total_records_ingested: int
    total_records_processed: int
    total_records_skipped: int
    engine_used: str
    spark_available: bool
    spark_message: str
    validation_reports: Dict[str, DatasetValidationReport] = field(default_factory=dict)
    relational_report: Optional[RelationalValidationReport] = None
    cleaning_audits: Dict[str, CleaningAudit] = field(default_factory=dict)
    skipped_rows_log: List[str] = field(default_factory=list)
    analytics_df: Optional[pd.DataFrame] = None
    clean_tables: Dict[str, pd.DataFrame] = field(default_factory=dict)
    parquet_saved: bool = False
    error_message: Optional[str] = None
    execution_timestamp: str = field(default_factory=lambda: datetime.now().strftime("%Y-%m-%d %H:%M:%S"))


class WasteWisePipeline:
    """End-to-end reproducible ETL pipeline for grocery waste analytics."""

    def __init__(self, preferred_engine: str = "auto"):
        self.preferred_engine = preferred_engine

    def run(
        self,
        products_raw: pd.DataFrame,
        inventory_raw: pd.DataFrame,
        expiry_raw: pd.DataFrame,
        sales_raw: pd.DataFrame,
        reference_date: Optional[datetime] = None,
        save_parquet: bool = True
    ) -> PipelineResult:
        start_time = time.time()
        spark_ok, spark_msg = is_spark_available()
        skipped_log: List[str] = []

        total_ingested = (
            (len(products_raw) if products_raw is not None else 0) +
            (len(inventory_raw) if inventory_raw is not None else 0) +
            (len(expiry_raw) if expiry_raw is not None else 0) +
            (len(sales_raw) if sales_raw is not None else 0)
        )

        # 1. Validation Step
        val_reports = {}
        for name, df in [
            ("products", products_raw),
            ("inventory", inventory_raw),
            ("expiry", expiry_raw),
            ("sales", sales_raw)
        ]:
            report = DataValidator.validate_dataset(df, name)
            val_reports[name] = report
            if report.has_errors:
                for err in report.errors:
                    skipped_log.append(f"[{name.upper()} ERROR] {err.message}")

        # Check for catastrophic validation failure (missing required columns or all datasets empty)
        critical_errors = [
            r for r in val_reports.values()
            if any("Missing mandatory column" in e.message for e in r.errors)
        ]
        if critical_errors:
            duration = round(time.time() - start_time, 3)
            return PipelineResult(
                status="FAILED",
                duration_seconds=duration,
                total_records_ingested=total_ingested,
                total_records_processed=0,
                total_records_skipped=total_ingested,
                engine_used="Pandas/DuckDB",
                spark_available=spark_ok,
                spark_message=spark_msg,
                validation_reports=val_reports,
                skipped_rows_log=skipped_log,
                error_message="Pipeline halted due to schema errors (missing mandatory columns)."
            )

        # Relational check
        rel_report = DataValidator.validate_relationships(
            products_raw, inventory_raw, sales_raw, expiry_raw
        )
        for warn in rel_report.warnings:
            skipped_log.append(f"[RELATIONAL WARNING] {warn}")

        # 2. Cleaning & Normalization Step
        clean_tables: Dict[str, pd.DataFrame] = {}
        cleaning_audits: Dict[str, CleaningAudit] = {}

        try:
            prod_clean, prod_audit = DataCleaner.clean_products(products_raw)
            clean_tables["products"] = prod_clean
            cleaning_audits["products"] = prod_audit

            inv_clean, inv_audit = DataCleaner.clean_inventory(inventory_raw)
            clean_tables["inventory"] = inv_clean
            cleaning_audits["inventory"] = inv_audit

            exp_clean, exp_audit = DataCleaner.clean_expiry(expiry_raw)
            clean_tables["expiry"] = exp_clean
            cleaning_audits["expiry"] = exp_audit

            sales_clean, sales_audit = DataCleaner.clean_sales(sales_raw)
            clean_tables["sales"] = sales_clean
            cleaning_audits["sales"] = sales_audit

            for audit in cleaning_audits.values():
                for reason in audit.dropped_reasons:
                    skipped_log.append(f"[{audit.dataset_name.upper()} AUDIT] {reason}")

        except Exception as e:
            duration = round(time.time() - start_time, 3)
            return PipelineResult(
                status="FAILED",
                duration_seconds=duration,
                total_records_ingested=total_ingested,
                total_records_processed=0,
                total_records_skipped=total_ingested,
                engine_used="Pandas/DuckDB",
                spark_available=spark_ok,
                spark_message=spark_msg,
                validation_reports=val_reports,
                relational_report=rel_report,
                skipped_rows_log=skipped_log,
                error_message=f"Cleaning step failed: {str(e)}"
            )

        # 3. Choose Engine and Run Transformations
        engine_to_use = "Pandas/DuckDB"
        if self.preferred_engine == "pyspark" and spark_ok:
            engine_to_use = "PySpark"

        try:
            analytics_df = DataTransformer.build_analytics_model(
                clean_products=clean_tables["products"],
                clean_inventory=clean_tables["inventory"],
                clean_expiry=clean_tables["expiry"],
                clean_sales=clean_tables["sales"],
                reference_date=reference_date
            )
        except Exception as e:
            duration = round(time.time() - start_time, 3)
            return PipelineResult(
                status="FAILED",
                duration_seconds=duration,
                total_records_ingested=total_ingested,
                total_records_processed=0,
                total_records_skipped=total_ingested,
                engine_used=engine_to_use,
                spark_available=spark_ok,
                spark_message=spark_msg,
                validation_reports=val_reports,
                relational_report=rel_report,
                cleaning_audits=cleaning_audits,
                skipped_rows_log=skipped_log,
                error_message=f"Transformation step failed: {str(e)}"
            )

        # 4. Save Parquet
        parquet_saved = False
        duration = round(time.time() - start_time, 3)
        total_skipped = sum(a.dropped_rows for a in cleaning_audits.values())
        total_processed = len(analytics_df)

        if save_parquet:
            run_metadata = {
                "timestamp": datetime.now().isoformat(),
                "duration_seconds": duration,
                "engine": engine_to_use,
                "total_records_ingested": total_ingested,
                "total_records_processed": total_processed,
                "total_records_skipped": total_skipped,
                "status": "SUCCESS" if total_skipped == 0 else "WARNING"
            }
            saved_ok, save_err = ParquetStore.save_processed_tables(
                analytics_df=analytics_df,
                products_df=clean_tables["products"],
                inventory_df=clean_tables["inventory"],
                expiry_df=clean_tables["expiry"],
                sales_df=clean_tables["sales"],
                run_metadata=run_metadata
            )
            parquet_saved = saved_ok
            if save_err:
                skipped_log.append(f"[PARQUET STORE WARNING] {save_err}")

        status = "SUCCESS"
        if total_skipped > 0 or len(rel_report.warnings) > 0:
            status = "WARNING"

        return PipelineResult(
            status=status,
            duration_seconds=duration,
            total_records_ingested=total_ingested,
            total_records_processed=total_processed,
            total_records_skipped=total_skipped,
            engine_used=engine_to_use,
            spark_available=spark_ok,
            spark_message=spark_msg,
            validation_reports=val_reports,
            relational_report=rel_report,
            cleaning_audits=cleaning_audits,
            skipped_rows_log=skipped_log,
            analytics_df=analytics_df,
            clean_tables=clean_tables,
            parquet_saved=parquet_saved
        )
