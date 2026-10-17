"""Configuration and constants for WasteWise Food Waste Analytics & ETL Pipeline."""
from pathlib import Path

# Base Paths
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
SAMPLE_DATA_DIR = DATA_DIR / "sample"
PROCESSED_DATA_DIR = DATA_DIR / "processed"

# Ensure directories exist
SAMPLE_DATA_DIR.mkdir(parents=True, exist_ok=True)
PROCESSED_DATA_DIR.mkdir(parents=True, exist_ok=True)

# Parquet file paths
PARQUET_PRODUCTS = PROCESSED_DATA_DIR / "products.parquet"
PARQUET_INVENTORY = PROCESSED_DATA_DIR / "inventory.parquet"
PARQUET_EXPIRY = PROCESSED_DATA_DIR / "expiry.parquet"
PARQUET_SALES = PROCESSED_DATA_DIR / "sales.parquet"
PARQUET_ANALYTICS = PROCESSED_DATA_DIR / "wastewise_analytics.parquet"
PARQUET_PIPELINE_METRICS = PROCESSED_DATA_DIR / "pipeline_run_metadata.json"

# Business Rules Thresholds
CRITICAL_EXPIRY_DAYS = 2    # <= 2 days: critical immediate clearance
HIGH_RISK_EXPIRY_DAYS = 5   # 3-5 days: high risk markdown
MEDIUM_RISK_EXPIRY_DAYS = 10 # 6-10 days: monitor closely
SAFE_EXPIRY_DAYS = 10       # > 10 days: healthy stock

# Overstock factor: if days of stock > days to expiry * OVERSTOCK_RATIO
OVERSTOCK_RATIO = 1.3
# Dead stock threshold: items in stock with 0 or near 0 sales for >= DEAD_STOCK_DAYS
DEAD_STOCK_DAYS = 7

# Supported File Formats
SUPPORTED_EXTENSIONS = [".csv", ".parquet"]
