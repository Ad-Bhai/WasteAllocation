"""Standalone CLI runner for the WasteWise ETL Pipeline."""
import sys

# Ensure UTF-8 console output on Windows
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from datetime import datetime
from wastewise.ingestion.samples import load_sample_datasets
from wastewise.etl.pipeline import WasteWisePipeline
from wastewise.analytics.metrics import compute_kpis
from wastewise.recommendations.engine import RecommendationEngine


def main():
    print("=" * 72)
    print(" WasteWise -- Food Waste Analytics & ETL Pipeline")
    print("=" * 72)

    # 1. Ingestion
    print("\n[1/4] Ingesting grocery datasets...")
    datasets = load_sample_datasets()
    for name, df in datasets.items():
        print(f"  * Loaded {name:12s}: {len(df):4d} records")

    # 2. Pipeline Execution
    print("\n[2/4] Executing ETL Pipeline (Cleaning, Joins & Metric Enrichment)...")
    pipeline = WasteWisePipeline(preferred_engine="pandas")
    result = pipeline.run(
        products_raw=datasets["products"],
        inventory_raw=datasets["inventory"],
        expiry_raw=datasets["expiry"],
        sales_raw=datasets["sales"],
        save_parquet=True
    )

    print(f"  * Pipeline Status     : {result.status}")
    print(f"  * Engine Used         : {result.engine_used}")
    print(f"  * Records Ingested    : {result.total_records_ingested:,}")
    print(f"  * Records Processed   : {result.total_records_processed:,}")
    print(f"  * Records Skipped     : {result.total_records_skipped:,}")
    print(f"  * Runtime Duration    : {result.duration_seconds * 1000:.1f} ms")
    print(f"  * Parquet Persisted   : {'Yes (data/processed/*.parquet)' if result.parquet_saved else 'No'}")

    # 3. Analytics KPIs
    print("\n[3/4] Computing Analytics & Financial KPIs...")
    kpis = compute_kpis(result.analytics_df)
    print(f"  * Total On-Hand Stock : {kpis.total_stock_units:,.0f} units")
    print(f"  * Historical Units Sold: {kpis.total_units_sold:,.0f} units")
    print(f"  * Estimated Waste     : {kpis.total_waste_units:,.0f} units ({kpis.overall_waste_rate_pct:.1f}% waste rate)")
    print(f"  * Procurement Cost Loss: ${kpis.total_cost_loss:,.2f}")
    print(f"  * Lost Retail Revenue : ${kpis.total_retail_loss:,.2f}")
    print(f"  * Expired Batches     : {kpis.expired_batches_count}")
    print(f"  * Critical Expiry(<=2d): {kpis.critical_batches_count}")
    print(f"  * Overstocked Items   : {kpis.overstocked_products_count}")

    # 4. Inventory Recommendations
    print("\n[4/4] Generating Data-Backed Action Plans...")
    recs = RecommendationEngine.generate_recommendations(result.analytics_df)
    print(f"  * Generated {len(recs)} prioritized recommendations:")
    for i, r in enumerate(recs[:4], start=1):
        print(f"\n    [{i}] [{r.urgency}] {r.headline}")
        print(f"        Action: {r.action_plan[:105]}...")
        print(f"        Potential Loss at Risk: ${r.potential_loss_at_risk:.2f}")

    print("\n" + "=" * 72)
    print(" Run Complete! Web Dashboard is active at: http://localhost:8501")
    print("=" * 72)


if __name__ == "__main__":
    main()
