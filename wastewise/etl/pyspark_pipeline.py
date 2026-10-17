"""PySpark ETL processing path for scalable grocery food waste data transformation."""
import shutil
from typing import Tuple, Optional, Dict, Any
from pathlib import Path
import pandas as pd


def is_spark_available() -> Tuple[bool, str]:
    """
    Checks if PySpark and a functioning Java Virtual Machine (JVM) are available in the current environment.
    Returns (is_available, message).
    """
    # 1. Check if java executable is found on PATH
    java_exe = shutil.which("java")
    if not java_exe:
        return False, "Java Virtual Machine (JVM) not detected on PATH. Apache Spark requires Java 11 or 17."

    # 2. Check if pyspark library can be imported
    try:
        import pyspark
        from pyspark.sql import SparkSession
    except ImportError:
        return False, "PySpark package is not installed. Install via 'pip install pyspark'."

    # 3. Test SparkSession creation
    try:
        spark = SparkSession.builder \
            .appName("WasteWise-Check") \
            .master("local[1]") \
            .config("spark.ui.enabled", "false") \
            .getOrCreate()
        spark.stop()
        return True, f"PySpark {pyspark.__version__} is fully available with JVM runtime."
    except Exception as e:
        return False, f"PySpark is installed but failed to initialize JVM session: {str(e)}"


class PySparkETLPipeline:
    """
    Genuine PySpark scalable ETL pipeline for processing large-scale grocery datasets.
    Active when a valid JVM and PySpark are detected in the execution environment.
    """

    def __init__(self, master: str = "local[*]"):
        self.master = master
        self._spark = None

    def get_or_create_session(self):
        from pyspark.sql import SparkSession
        if self._spark is None:
            self._spark = SparkSession.builder \
                .appName("WasteWise-Scalable-ETL") \
                .master(self.master) \
                .config("spark.sql.execution.arrow.pyspark.enabled", "true") \
                .config("spark.ui.enabled", "false") \
                .getOrCreate()
        return self._spark

    def run_pipeline(
        self,
        products_df: pd.DataFrame,
        inventory_df: pd.DataFrame,
        expiry_df: pd.DataFrame,
        sales_df: pd.DataFrame,
        output_dir: Path
    ) -> Dict[str, Any]:
        """
        Executes distributed Spark DataFrame transformations and writes Parquet.
        """
        spark_ok, msg = is_spark_available()
        if not spark_ok:
            raise RuntimeError(
                f"PySpark engine cannot run: {msg}\n"
                "Please configure Java 11/17 (JDK) and run 'pip install pyspark', "
                "or use the built-in high-performance Pandas/DuckDB engine."
            )

        from pyspark.sql import functions as F
        from pyspark.sql.types import DoubleType, IntegerType, StringType, DateType

        spark = self.get_or_create_session()

        # Convert Pandas DataFrames into PySpark DataFrames
        sdf_prod = spark.createDataFrame(products_df)
        sdf_inv = spark.createDataFrame(inventory_df)
        sdf_exp = spark.createDataFrame(expiry_df)
        sdf_sales = spark.createDataFrame(sales_df)

        # Sales Aggregation in Spark
        sales_agg = sdf_sales.groupBy("product_id").agg(
            F.sum("units_sold").alias("total_units_sold"),
            F.sum("total_revenue").alias("total_sales_revenue"),
            F.count("transaction_id").alias("sales_transactions_count"),
            F.countDistinct("transaction_date").alias("distinct_sales_days")
        ).withColumn(
            "avg_daily_sales",
            F.round(F.col("total_units_sold") / F.greatest(F.col("distinct_sales_days"), F.lit(1)), 2)
        )

        # Join Inventory with Products
        merged = sdf_inv.join(sdf_prod, on="product_id", how="left")

        # Join with Expiry
        merged = merged.join(
            sdf_exp.select("batch_id", "product_id", "expiry_date", "batch_quantity", "status"),
            on=["batch_id", "product_id"],
            how="left"
        )

        # Join with Sales
        analytics_sdf = merged.join(sales_agg, on="product_id", how="left")

        # Write Parquet via Spark
        output_path = output_dir / "spark_wastewise_analytics.parquet"
        analytics_sdf.write.mode("overwrite").parquet(str(output_path))

        return {
            "engine": "PySpark",
            "spark_version": spark.version,
            "total_records": analytics_sdf.count(),
            "output_path": str(output_path),
            "status": "SUCCESS"
        }

    def stop(self):
        if self._spark:
            self._spark.stop()
            self._spark = None
