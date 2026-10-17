# 🥑 WasteWise — Food Waste Analytics & ETL Pipeline

**WasteWise** is a production-grade, end-to-end data analytics and ETL platform designed for grocery retailers to spot perishable food waste, minimize financial losses, optimize inventory run rates, and make data-backed procurement decisions.

---

## 📑 Table of Contents
- [Architecture & Engine Design](#architecture--engine-design)
- [Core Features](#core-features)
- [Quick Start Guide](#quick-start-guide)
- [Running Automated Tests](#running-automated-tests)
- [Data Model & Schema Specifications](#data-model--schema-specifications)
- [Formulas, Metrics & Business Assumptions](#formulas-metrics--business-assumptions)
- [PySpark Distributed Engine Guide](#pyspark-distributed-engine-guide)
- [Project Directory Structure](#project-directory-structure)
- [Limitations & Production Roadmap](#limitations--production-roadmap)

---

## 🏛️ Architecture & Engine Design

WasteWise utilizes a dual-path analytics engine:
1. **Primary Vectorized Engine (Pandas + PyArrow + DuckDB):**
   - High-performance, low-latency in-memory data processing.
   - Fully embedded ANSI SQL query engine via **DuckDB** that directly queries DataFrames and Parquet files.
   - Columnar persistence with **Apache Arrow / Parquet** (snappy compression).
   - Zero-dependency configuration that runs out of the box on Windows, macOS, and Linux without requiring a Java runtime.
2. **Distributed Engine (Apache PySpark):**
   - Implements PySpark DataFrame transformations and Parquet partition writes.
   - Includes automatic JVM detection (`is_spark_available()`). If Java or PySpark is missing, it fails over seamlessly to the primary DuckDB engine with an informative setup guide.

---

## 🚀 Core Features

### 1. Data Ingestion & Schema Validation
- **Formats:** Supports both **CSV** (with automatic encoding detection: UTF-8, UTF-8-SIG, Latin-1, CP1252) and **Parquet** files.
- **Master Datasets:** Products catalog, inventory stock levels, batch expiry dates, and historical sales transactions.
- **Pre-packaged Sample Data:** Built-in realistic grocery datasets across Dairy, Produce, Bakery, Meat, and Pantry categories.
- **Validation Engine:** Rigorous schema verification checking for mandatory columns, unparseable dates, negative numeric quantities, and orphaned foreign keys.

### 2. Reliable ETL Pipeline
- **Column Normalization:** Sanitizes headers into lowercase snake_case.
- **Deterministic Cleaning:** Handles missing optional fields with documented defaults (`supplier` → "General Supplier", `location` → "Main Floor", `reorder_threshold` → 10).
- **Deduplication:** Automatic deduplication on primary keys, retaining the latest record while logging audit counts.
- **Audit Logging:** Reports total ingested, clean, and skipped rows with explicit failure reasons.
- **Columnar Persistence:** Writes sanitized tables and joined analytical models to `data/processed/*.parquet`.

### 3. Analytics Dashboard
- **Executive KPIs:** Total on-hand units, historical sales, estimated waste volume, sunk procurement cost loss ($), lost retail revenue ($), and overall waste rate (%).
- **Interactive Plotly Visualizations:**
  - Expiry Risk Distribution (Capital at risk by urgency tier).
  - Department / Category Losses Comparison (Cost loss vs. retail value).
  - Top 10 Most Wasted Products ranking.
  - Daily Sales Volume Trend over time.
- **Dynamic Filtering:** Filter across categories, suppliers, and expiry risk levels.
- **Direct Export:** Instant export of filtered datasets to CSV or Parquet.

### 4. Interactive SQL Insights Workbench
- Powered by an embedded **DuckDB** local engine.
- **6 Pre-built Actionable Queries:**
  1. Products with Highest Waste / Expiry Risk
  2. Department / Category Loss Breakdown
  3. Repeatedly Overstocked Products
  4. Sales vs Stock Run Rate Comparison
  5. Dead Inventory Audit (High Stock, Low Sales)
  6. Supplier Waste Contribution Scorecard
- **Custom SQL Editor:** Write arbitrary ANSI SQL queries with sub-second response times.
- **Schema Inspector:** View table columns and data types directly in the UI.

### 5. Transparent Inventory Recommendations
- **Action Categories:**
  - `⚡ PRIORITY CLEARANCE / MARKDOWN`: Immediate 20-30% price reduction for items expiring in ≤ 2 days.
  - `📉 CURTAIL NEXT ORDER`: Suspend or reduce procurement orders when days of stock exceed remaining shelf life.
  - `🔍 DEAD STOCK AUDIT`: Identify slow-moving items with high capital tied up on the floor.
  - `⚠️ DEPARTMENT SHRINK ALERT`: Highlight categories generating disproportionate waste.
- **Complete Transparency:** Every recommendation includes an operational data table and mathematical formula breakdown.
- **No Guaranteed Savings Claim:** All estimates are clearly marked as *Potential Procurement Capital at Risk*.

---

## 🛠️ Quick Start Guide

### Prerequisites
- Python 3.9+ (tested on Python 3.9, 3.10, 3.11, 3.12, and 3.13)
- Windows, macOS, or Linux

### 1. Clone & Navigate to Repository
```bash
git clone <repo-url>
cd WasteAllocation
```

### 2. Create and Activate Virtual Environment (Recommended)
```bash
# Windows
python -m venv .venv
.venv\Scripts\activate

# macOS / Linux
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Run the Web Application
```bash
streamlit run app.py
```
Open your browser at `http://localhost:8501`. The application will automatically initialize the sample grocery datasets, run the ETL pipeline, and load the dashboard.

---

## 🧪 Running Automated Tests

WasteWise includes a comprehensive test suite covering schema validation, cleaning rules, transformations, the DuckDB SQL engine, and recommendation algorithms:

```bash
pytest
```
*Expected output: `20 passed`*

---

## 📊 Data Model & Schema Specifications

### 1. Products Catalog (`products.csv` / `products.parquet`)
| Column | Type | Required | Description |
|---|---|---|---|
| `product_id` | String | **Yes (PK)** | Unique product identifier (e.g., `PRD-001`) |
| `product_name` | String | **Yes** | Commercial product title |
| `category` | String | **Yes** | Department (e.g., `Dairy`, `Produce`, `Bakery`, `Meat`, `Pantry`) |
| `unit_cost` | Float | **Yes** | Direct procurement cost per unit ($) |
| `unit_price` | Float | **Yes** | Retail selling price per unit ($) |
| `supplier` | String | No | Vendor or distributor name |
| `reorder_threshold` | Integer | No | Minimum units required before reorder trigger (default: 10) |

### 2. Inventory (`inventory.csv` / `inventory.parquet`)
| Column | Type | Required | Description |
|---|---|---|---|
| `inventory_id` | String | **Yes (PK)** | Unique stock record identifier |
| `product_id` | String | **Yes (FK)** | References `products.product_id` |
| `batch_id` | String | **Yes** | Lot identifier matching expiry records |
| `stock_date` | Date | **Yes** | Date count was audited (`YYYY-MM-DD`) |
| `current_stock` | Float | **Yes** | Available on-hand quantity |
| `location` | String | No | Physical location in store |

### 3. Expiry Records (`expiry.csv` / `expiry.parquet`)
| Column | Type | Required | Description |
|---|---|---|---|
| `batch_id` | String | **Yes (PK)** | Batch / Lot code (e.g., `BAT-MLK-01`) |
| `product_id` | String | **Yes (FK)** | References `products.product_id` |
| `expiry_date` | Date | **Yes** | Expiration / Best-by date (`YYYY-MM-DD`) |
| `received_date` | Date | No | Inbound receiving date |
| `batch_quantity` | Float | No | Initial received quantity |
| `status` | String | No | Batch status (`Active`, `Expired`, `Quarantined`) |

### 4. Sales Transactions (`sales.csv` / `sales.parquet`)
| Column | Type | Required | Description |
|---|---|---|---|
| `transaction_id` | String | **Yes (PK)** | Transaction reference (e.g., `TXN-9001`) |
| `product_id` | String | **Yes (FK)** | References `products.product_id` |
| `transaction_date` | Date | **Yes** | Date of sale (`YYYY-MM-DD`) |
| `units_sold` | Float | **Yes** | Quantity purchased |
| `discount_applied` | Float | No | Discount percentage (0.0 to 100.0) |
| `total_revenue` | Float | No | Net transaction revenue |

---

## 📐 Formulas, Metrics & Business Assumptions

### 1. Days to Expiry
$$\text{Days to Expiry} = \text{Date}(\text{expiry\_date}) - \text{Date}(\text{reference\_date})$$
- Reference date defaults to the latest inventory/sales date or today's date.
- **Risk Tiers:**
  - **Expired:** $\text{Days} < 0$
  - **Critical (≤ 2d):** $0 \le \text{Days} \le 2$
  - **High Risk (3–5d):** $3 \le \text{Days} \le 5$
  - **Medium Risk (6–10d):** $6 \le \text{Days} \le 10$
  - **Safe (> 10d):** $\text{Days} > 10$

### 2. Daily Sales Velocity (Run Rate)
$$\text{Average Daily Sales} = \frac{\sum \text{units\_sold}}{\max(1, \text{distinct\_sales\_days})}$$

### 3. Days of Stock Remaining (Runout Time)
$$\text{Days of Stock} = \frac{\text{current\_stock}}{\text{Average Daily Sales}}$$
*(If daily sales = 0 and stock > 0, days of stock is flagged as 999.0 to signify dead stock).*

### 4. Estimated Waste Units
For batches with expiration dates:
- If $\text{Days to Expiry} < 0$ (Expired):
  $$\text{Waste Units} = \text{current\_stock}$$
- If $\text{Days to Expiry} \ge 0$:
  $$\text{Projected Sales} = \text{Average Daily Sales} \times \text{Days to Expiry}$$
  $$\text{Waste Units} = \min\left(\text{current\_stock}, \max\left(0, \text{current\_stock} - \text{Projected Sales}\right)\right)$$

### 5. Financial Loss Breakdown
- **Sunk Procurement Cost Loss ($):** Direct procurement capital unrecoverable due to spoilage:
  $$\text{Cost Loss} = \text{Waste Units} \times \text{unit\_cost}$$
- **Lost Retail Revenue ($):** Potential gross retail revenue forfeited:
  $$\text{Retail Loss} = \text{Waste Units} \times \text{unit\_price}$$

### 6. Waste Rate Percentage
$$\text{Waste Rate (\%)} = \frac{\sum \text{estimated\_waste\_units}}{\sum \text{units\_sold} + \sum \text{current\_stock}} \times 100$$

### 7. Overstock Condition
A product is flagged as overstocked when:
$$\text{Days of Stock} > (\text{Days to Expiry} \times 1.3) \quad \text{AND} \quad \text{current\_stock} > 10$$

---

## ⚡ PySpark Distributed Engine Guide

WasteWise includes an enterprise PySpark DataFrame pipeline (`wastewise/etl/pyspark_pipeline.py`).

### How to Enable PySpark:
1. **Install Java 11 or 17 LTS:**
   - Download OpenJDK (e.g. Eclipse Temurin) from [Adoptium](https://adoptium.net).
   - Set the `JAVA_HOME` environment variable (e.g., `C:\Program Files\Eclipse Adoptium\jdk-17...`).
   - Add `%JAVA_HOME%\bin` (or `$JAVA_HOME/bin`) to your system `PATH`.
2. **Install PySpark:**
   ```bash
   pip install pyspark>=3.5.0
   ```
3. **Restart WasteWise:**
   - Run `streamlit run app.py`.
   - The app will automatically detect PySpark and display **PySpark Active** on the top status pill.
   - You can toggle between the Pandas and PySpark execution paths in the **ETL Pipeline & Storage** tab.

*If PySpark or Java is absent, the application gracefully utilizes the built-in DuckDB/Pandas engine with zero downtime.*

---

## 📁 Project Directory Structure

```
c:\WasteAllocation\
├── app.py                      # Main Streamlit web application & routing
├── pyproject.toml              # Build config, metadata, and pytest settings
├── requirements.txt            # Python dependencies
├── README.md                   # Comprehensive documentation & reference
├── data/
│   ├── sample/                 # Pre-packaged CSV & Parquet datasets
│   │   ├── products.csv
│   │   ├── inventory.csv
│   │   ├── expiry.csv
│   │   ├── sales.csv
│   │   ├── parquet/            # Parquet versions of sample data
│   │   └── corrupted/          # Test files for validating error reporting
│   └── processed/              # Parquet files generated by ETL pipeline
├── wastewise/
│   ├── __init__.py
│   ├── config.py               # Constants, file paths, business thresholds
│   ├── ingestion/
│   │   ├── __init__.py
│   │   ├── loader.py           # Safe CSV & Parquet reader with format sniffing
│   │   └── samples.py          # Sample dataset generator & disk persistence
│   ├── validation/
│   │   ├── __init__.py
│   │   ├── schema.py           # Expected columns, types, and constraints
│   │   └── validator.py        # Schema checks, date validation, and foreign keys
│   ├── etl/
│   │   ├── __init__.py
│   │   ├── pipeline.py         # Main reproducible ETL pipeline orchestrator
│   │   ├── cleaner.py          # Normalization, missing values, deduplication
│   │   ├── transformer.py      # Joins, expiry calculations, waste metrics
│   │   ├── parquet_store.py    # Snappy Parquet reader/writer with metadata
│   │   └── pyspark_pipeline.py # Spark DataFrame ETL with JVM detection
│   ├── analytics/
│   │   ├── __init__.py
│   │   ├── metrics.py          # Executive KPIs, waste rates, batch counts
│   │   └── aggregations.py     # Category, supplier, risk, and sales trends
│   ├── sql/
│   │   ├── __init__.py
│   │   ├── engine.py           # Local DuckDB SQL execution engine
│   │   └── queries.py          # Predefined business queries & assumptions
│   ├── recommendations/
│   │   ├── __init__.py
│   │   └── engine.py           # Data-backed transparent inventory actions
│   └── ui/
│       ├── __init__.py
│       ├── components.py       # Reusable cards, metric tiles, empty states
│       ├── styles.py           # Custom luxury dark mode CSS & typography
│       └── views/
│           ├── dashboard_view.py       # KPIs, Plotly charts, filters, export
│           ├── import_view.py          # File uploaders, schema guides, checks
│           ├── etl_view.py             # Pipeline runner, audits, Parquet viewer
│           ├── sql_view.py             # Interactive DuckDB query workbench
│           └── recommendations_view.py # Action plans & calculation breakdown
└── tests/
    ├── __init__.py
    ├── test_ingestion.py       # Tests for CSV/Parquet loaders & corrupt files
    ├── test_validation.py      # Tests for schema rules, dates, foreign keys
    ├── test_cleaner.py         # Tests for normalization, defaults, dedup
    ├── test_transformer.py     # Tests for joins, expiry risk, waste formulas
    ├── test_pipeline.py        # End-to-end ETL pipeline tests
    ├── test_sql_engine.py      # Tests for DuckDB queries and preset templates
    └── test_recommendations.py # Tests for recommendation logic & transparency
```

---

## 🔮 Limitations & Production Roadmap

1. **POS API Streaming:** Currently ingests batch CSV and Parquet files. Future iterations can integrate Kafka / Webhook listeners for real-time POS transaction streams.
2. **Machine Learning Demand Forecasting:** Sales velocity currently leverages a moving average run rate. Future modules can incorporate ARIMA or LightGBM models for day-of-week and seasonal elasticity.
3. **Multi-Store Warehouse Hierarchy:** Supports store-level inventory. Central distribution center (DC) cross-docking logic can be added for regional supermarket chains.
