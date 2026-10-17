"""Sample grocery dataset generation and persistence."""
from pathlib import Path
from typing import Dict
import pandas as pd

from wastewise.config import SAMPLE_DATA_DIR


def generate_sample_datasets() -> Dict[str, pd.DataFrame]:
    """Generates realistic sample datasets for food waste grocery analysis."""

    # 1. Products catalog
    products_data = [
        {"product_id": "PRD-001", "product_name": "Organic Whole Milk 1L", "category": "Dairy", "supplier": "Horizon Dairy Co.", "unit_cost": 2.10, "unit_price": 3.49, "reorder_threshold": 30},
        {"product_id": "PRD-002", "product_name": "Greek Yogurt Plain 500g", "category": "Dairy", "supplier": "Horizon Dairy Co.", "unit_cost": 2.50, "unit_price": 4.29, "reorder_threshold": 20},
        {"product_id": "PRD-003", "product_name": "Artisan Sourdough Loaf", "category": "Bakery", "supplier": "Golden Crust Bakery", "unit_cost": 1.80, "unit_price": 4.99, "reorder_threshold": 15},
        {"product_id": "PRD-004", "product_name": "Brioche Hamburger Buns 4pk", "category": "Bakery", "supplier": "Golden Crust Bakery", "unit_cost": 1.40, "unit_price": 3.29, "reorder_threshold": 15},
        {"product_id": "PRD-005", "product_name": "Organic Baby Spinach 250g", "category": "Produce", "supplier": "Valley Fresh Farms", "unit_cost": 1.60, "unit_price": 2.99, "reorder_threshold": 25},
        {"product_id": "PRD-006", "product_name": "Ripe Hass Avocados 4pk", "category": "Produce", "supplier": "Valley Fresh Farms", "unit_cost": 2.80, "unit_price": 4.99, "reorder_threshold": 20},
        {"product_id": "PRD-007", "product_name": "Strawberries Clamshell 400g", "category": "Produce", "supplier": "Valley Fresh Farms", "unit_cost": 2.20, "unit_price": 3.99, "reorder_threshold": 20},
        {"product_id": "PRD-008", "product_name": "Free-Range Chicken Breast 500g", "category": "Meat", "supplier": "Prairie Ranch Meats", "unit_cost": 4.50, "unit_price": 7.99, "reorder_threshold": 15},
        {"product_id": "PRD-009", "product_name": "Grass-Fed Ground Beef 450g", "category": "Meat", "supplier": "Prairie Ranch Meats", "unit_cost": 4.80, "unit_price": 8.49, "reorder_threshold": 15},
        {"product_id": "PRD-010", "product_name": "Fresh Atlantic Salmon Fillet 300g", "category": "Meat", "supplier": "Coast Seafoods", "unit_cost": 6.20, "unit_price": 10.99, "reorder_threshold": 10},
        {"product_id": "PRD-011", "product_name": "Oat Milk Barista Edition 1L", "category": "Dairy", "supplier": "Pure Plant Beverages", "unit_cost": 2.40, "unit_price": 4.49, "reorder_threshold": 25},
        {"product_id": "PRD-012", "product_name": "Cheddar Cheese Block 400g", "category": "Dairy", "supplier": "Horizon Dairy Co.", "unit_cost": 3.10, "unit_price": 5.89, "reorder_threshold": 15},
        {"product_id": "PRD-013", "product_name": "Gourmet Hummus Dip 200g", "category": "Pantry", "supplier": "Mediterranean Flavors", "unit_cost": 1.75, "unit_price": 3.79, "reorder_threshold": 15},
        {"product_id": "PRD-014", "product_name": "Fresh Guacamole Bowl 225g", "category": "Pantry", "supplier": "Valley Fresh Farms", "unit_cost": 2.20, "unit_price": 4.59, "reorder_threshold": 10},
        {"product_id": "PRD-015", "product_name": "Artisan French Baguette", "category": "Bakery", "supplier": "Golden Crust Bakery", "unit_cost": 0.90, "unit_price": 2.49, "reorder_threshold": 20},
        {"product_id": "PRD-016", "product_name": "Organic Honeycrisp Apples 1kg", "category": "Produce", "supplier": "Valley Fresh Farms", "unit_cost": 2.50, "unit_price": 4.99, "reorder_threshold": 25},
    ]
    products_df = pd.DataFrame(products_data)

    # 2. Inventory data
    inventory_data = [
        {"inventory_id": "INV-1001", "product_id": "PRD-001", "batch_id": "BAT-MLK-01", "stock_date": "2026-10-15", "current_stock": 28, "location": "Cooler 1 - Shelf A"},
        {"inventory_id": "INV-1002", "product_id": "PRD-002", "batch_id": "BAT-YOG-01", "stock_date": "2026-10-15", "current_stock": 24, "location": "Cooler 1 - Shelf B"},
        {"inventory_id": "INV-1003", "product_id": "PRD-003", "batch_id": "BAT-SRD-01", "stock_date": "2026-10-16", "current_stock": 18, "location": "Bakery Display A"},
        {"inventory_id": "INV-1004", "product_id": "PRD-004", "batch_id": "BAT-BUN-01", "stock_date": "2026-10-15", "current_stock": 35, "location": "Bakery Display B"},
        {"inventory_id": "INV-1005", "product_id": "PRD-005", "batch_id": "BAT-SPN-01", "stock_date": "2026-10-16", "current_stock": 22, "location": "Produce Cooler 2"},
        {"inventory_id": "INV-1006", "product_id": "PRD-006", "batch_id": "BAT-AVO-01", "stock_date": "2026-10-16", "current_stock": 42, "location": "Produce Table 1"},
        {"inventory_id": "INV-1007", "product_id": "PRD-007", "batch_id": "BAT-STR-01", "stock_date": "2026-10-16", "current_stock": 16, "location": "Produce Cooler 1"},
        {"inventory_id": "INV-1008", "product_id": "PRD-008", "batch_id": "BAT-CHK-01", "stock_date": "2026-10-15", "current_stock": 19, "location": "Meat Case A"},
        {"inventory_id": "INV-1009", "product_id": "PRD-009", "batch_id": "BAT-BEF-01", "stock_date": "2026-10-15", "current_stock": 14, "location": "Meat Case B"},
        {"inventory_id": "INV-1010", "product_id": "PRD-010", "batch_id": "BAT-SAL-01", "stock_date": "2026-10-16", "current_stock": 12, "location": "Seafood Case"},
        {"inventory_id": "INV-1011", "product_id": "PRD-011", "batch_id": "BAT-OAT-01", "stock_date": "2026-10-14", "current_stock": 45, "location": "Aisle 4 - Shelf C"},
        {"inventory_id": "INV-1012", "product_id": "PRD-012", "batch_id": "BAT-CHD-01", "stock_date": "2026-10-14", "current_stock": 30, "location": "Dairy Walk-in"},
        {"inventory_id": "INV-1013", "product_id": "PRD-013", "batch_id": "BAT-HUM-01", "stock_date": "2026-10-15", "current_stock": 25, "location": "Deli Cooler"},
        {"inventory_id": "INV-1014", "product_id": "PRD-014", "batch_id": "BAT-GUA-01", "stock_date": "2026-10-16", "current_stock": 15, "location": "Deli Cooler"},
        {"inventory_id": "INV-1015", "product_id": "PRD-015", "batch_id": "BAT-BAG-01", "stock_date": "2026-10-16", "current_stock": 26, "location": "Bakery Bin 1"},
        {"inventory_id": "INV-1016", "product_id": "PRD-016", "batch_id": "BAT-APL-01", "stock_date": "2026-10-15", "current_stock": 50, "location": "Produce Table 2"},
    ]
    inventory_df = pd.DataFrame(inventory_data)

    # 3. Expiry dates data (assumes current date around 2026-10-17)
    expiry_data = [
        # Expired or Critical
        {"batch_id": "BAT-SRD-01", "product_id": "PRD-003", "received_date": "2026-10-13", "expiry_date": "2026-10-17", "batch_quantity": 30, "status": "Active"}, # Expiring Today (0 days)
        {"batch_id": "BAT-BAG-01", "product_id": "PRD-015", "received_date": "2026-10-14", "expiry_date": "2026-10-16", "batch_quantity": 40, "status": "Expired"}, # Expired (-1 days)
        {"batch_id": "BAT-STR-01", "product_id": "PRD-007", "received_date": "2026-10-14", "expiry_date": "2026-10-18", "batch_quantity": 35, "status": "Active"}, # Critical (1 day)
        {"batch_id": "BAT-SAL-01", "product_id": "PRD-010", "received_date": "2026-10-14", "expiry_date": "2026-10-19", "batch_quantity": 20, "status": "Active"}, # Critical (2 days)
        {"batch_id": "BAT-GUA-01", "product_id": "PRD-014", "received_date": "2026-10-13", "expiry_date": "2026-10-19", "batch_quantity": 25, "status": "Active"}, # Critical (2 days)
        # High Risk (3 - 5 days)
        {"batch_id": "BAT-SPN-01", "product_id": "PRD-005", "received_date": "2026-10-13", "expiry_date": "2026-10-21", "batch_quantity": 40, "status": "Active"}, # 4 days
        {"batch_id": "BAT-CHK-01", "product_id": "PRD-008", "received_date": "2026-10-14", "expiry_date": "2026-10-21", "batch_quantity": 30, "status": "Active"}, # 4 days
        {"batch_id": "BAT-BEF-01", "product_id": "PRD-009", "received_date": "2026-10-14", "expiry_date": "2026-10-22", "batch_quantity": 25, "status": "Active"}, # 5 days
        {"batch_id": "BAT-BUN-01", "product_id": "PRD-004", "received_date": "2026-10-12", "expiry_date": "2026-10-22", "batch_quantity": 50, "status": "Active"}, # 5 days (Overstocked!)
        # Medium Risk (6 - 10 days)
        {"batch_id": "BAT-MLK-01", "product_id": "PRD-001", "received_date": "2026-10-12", "expiry_date": "2026-10-24", "batch_quantity": 60, "status": "Active"}, # 7 days
        {"batch_id": "BAT-AVO-01", "product_id": "PRD-006", "received_date": "2026-10-13", "expiry_date": "2026-10-25", "batch_quantity": 70, "status": "Active"}, # 8 days (Overstocked!)
        {"batch_id": "BAT-HUM-01", "product_id": "PRD-013", "received_date": "2026-10-10", "expiry_date": "2026-10-26", "batch_quantity": 40, "status": "Active"}, # 9 days
        # Safe (> 10 days)
        {"batch_id": "BAT-YOG-01", "product_id": "PRD-002", "received_date": "2026-10-10", "expiry_date": "2026-11-02", "batch_quantity": 50, "status": "Active"}, # 16 days
        {"batch_id": "BAT-APL-01", "product_id": "PRD-016", "received_date": "2026-10-10", "expiry_date": "2026-11-05", "batch_quantity": 80, "status": "Active"}, # 19 days
        {"batch_id": "BAT-CHD-01", "product_id": "PRD-012", "received_date": "2026-10-05", "expiry_date": "2026-11-15", "batch_quantity": 45, "status": "Active"}, # 29 days
        {"batch_id": "BAT-OAT-01", "product_id": "PRD-011", "received_date": "2026-10-01", "expiry_date": "2026-12-10", "batch_quantity": 60, "status": "Active"}, # 54 days
    ]
    expiry_df = pd.DataFrame(expiry_data)

    # 4. Sales transactions over 10 days (2026-10-06 to 2026-10-16)
    sales_records = []
    txn_id = 9001
    
    # Sales profiles: (product_id, daily_avg, discount)
    profiles = [
        ("PRD-001", 6, 0.0),   # Milk: high steady sales (6/day)
        ("PRD-002", 3, 0.0),   # Yogurt: steady (3/day)
        ("PRD-003", 2, 0.15),  # Sourdough: low turnover (2/day)
        ("PRD-004", 2, 0.0),   # Buns: low turnover (2/day) vs 35 in stock (overstocked!)
        ("PRD-005", 4, 0.0),   # Spinach: 4/day
        ("PRD-006", 3, 0.0),   # Avocados: 3/day vs 42 stock
        ("PRD-007", 5, 0.10),  # Strawberries: 5/day
        ("PRD-008", 3, 0.0),   # Chicken: 3/day
        ("PRD-009", 2, 0.0),   # Beef: 2/day
        ("PRD-010", 2, 0.0),   # Salmon: 2/day
        ("PRD-011", 2, 0.0),   # Oat milk: 2/day
        ("PRD-012", 2, 0.0),   # Cheese: 2/day
        ("PRD-013", 2, 0.0),   # Hummus: 2/day
        ("PRD-014", 2, 0.20),  # Guacamole: 2/day
        ("PRD-015", 3, 0.30),  # Baguette: 3/day
        ("PRD-016", 4, 0.0),   # Apples: 4/day
    ]
    
    price_map = {p["product_id"]: p["unit_price"] for p in products_data}
    
    dates = pd.date_range(start="2026-10-06", end="2026-10-16", freq="D")
    for d in dates:
        d_str = d.strftime("%Y-%m-%d")
        for pid, base_qty, disc in profiles:
            # Vary sales quantity slightly by day of week
            qty = max(1, int(base_qty + (1 if d.weekday() in [4, 5, 6] else 0)))
            unit_price = price_map[pid]
            rev = round(qty * unit_price * (1 - disc), 2)
            sales_records.append({
                "transaction_id": f"TXN-{txn_id}",
                "product_id": pid,
                "transaction_date": d_str,
                "units_sold": qty,
                "discount_applied": disc * 100,
                "total_revenue": rev
            })
            txn_id += 1

    sales_df = pd.DataFrame(sales_records)

    return {
        "products": products_df,
        "inventory": inventory_df,
        "expiry": expiry_df,
        "sales": sales_df
    }


def save_sample_datasets() -> None:
    """Saves sample datasets as CSV and Parquet files in data/sample/."""
    datasets = generate_sample_datasets()
    parquet_dir = SAMPLE_DATA_DIR / "parquet"
    parquet_dir.mkdir(parents=True, exist_ok=True)

    for name, df in datasets.items():
        # Save CSV
        csv_path = SAMPLE_DATA_DIR / f"{name}.csv"
        df.to_csv(csv_path, index=False)

        # Save Parquet
        parquet_path = parquet_dir / f"{name}.parquet"
        df.to_parquet(parquet_path, engine="pyarrow", compression="snappy", index=False)


def load_sample_datasets() -> Dict[str, pd.DataFrame]:
    """Loads sample datasets from disk or generates them if not present."""
    csv_files = {name: SAMPLE_DATA_DIR / f"{name}.csv" for name in ["products", "inventory", "expiry", "sales"]}
    if all(p.exists() for p in csv_files.values()):
        return {name: pd.read_csv(p) for name, p in csv_files.items()}

    # Generate and save if missing
    datasets = generate_sample_datasets()
    save_sample_datasets()
    return datasets
