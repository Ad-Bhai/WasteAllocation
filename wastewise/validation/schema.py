"""Schema definitions and expectations for grocery food waste datasets."""
from typing import Dict, List, Any

DATASET_SCHEMAS: Dict[str, Dict[str, Any]] = {
    "products": {
        "display_name": "Products & Categories",
        "description": "Master catalog of products, categories, suppliers, cost, and pricing.",
        "primary_key": "product_id",
        "required_columns": [
            "product_id",
            "product_name",
            "category",
            "unit_cost",
            "unit_price"
        ],
        "optional_columns": [
            "supplier",
            "reorder_threshold"
        ],
        "column_types": {
            "product_id": "string",
            "product_name": "string",
            "category": "string",
            "supplier": "string",
            "unit_cost": "numeric",
            "unit_price": "numeric",
            "reorder_threshold": "numeric"
        },
        "value_constraints": {
            "unit_cost": {"min": 0.0, "allow_null": False},
            "unit_price": {"min": 0.0, "allow_null": False},
            "reorder_threshold": {"min": 0.0, "allow_null": True}
        }
    },
    "inventory": {
        "display_name": "Inventory & Stock Levels",
        "description": "Current on-hand store inventory counts by batch and location.",
        "primary_key": "inventory_id",
        "foreign_keys": {"product_id": "products.product_id"},
        "required_columns": [
            "inventory_id",
            "product_id",
            "batch_id",
            "stock_date",
            "current_stock"
        ],
        "optional_columns": [
            "location"
        ],
        "column_types": {
            "inventory_id": "string",
            "product_id": "string",
            "batch_id": "string",
            "stock_date": "date",
            "current_stock": "numeric",
            "location": "string"
        },
        "value_constraints": {
            "current_stock": {"min": 0.0, "allow_null": False}
        }
    },
    "expiry": {
        "display_name": "Product Expiry Dates",
        "description": "Batch received dates, expiration dates, and initial batch volume.",
        "primary_key": "batch_id",
        "foreign_keys": {"product_id": "products.product_id"},
        "required_columns": [
            "batch_id",
            "product_id",
            "expiry_date"
        ],
        "optional_columns": [
            "received_date",
            "batch_quantity",
            "status"
        ],
        "column_types": {
            "batch_id": "string",
            "product_id": "string",
            "received_date": "date",
            "expiry_date": "date",
            "batch_quantity": "numeric",
            "status": "string"
        },
        "value_constraints": {
            "batch_quantity": {"min": 0.0, "allow_null": True}
        }
    },
    "sales": {
        "display_name": "Sales Transactions",
        "description": "Customer purchase transaction history with units sold and revenue.",
        "primary_key": "transaction_id",
        "foreign_keys": {"product_id": "products.product_id"},
        "required_columns": [
            "transaction_id",
            "product_id",
            "transaction_date",
            "units_sold"
        ],
        "optional_columns": [
            "discount_applied",
            "total_revenue"
        ],
        "column_types": {
            "transaction_id": "string",
            "product_id": "string",
            "transaction_date": "date",
            "units_sold": "numeric",
            "discount_applied": "numeric",
            "total_revenue": "numeric"
        },
        "value_constraints": {
            "units_sold": {"min": 0.0, "allow_null": False},
            "discount_applied": {"min": 0.0, "max": 100.0, "allow_null": True},
            "total_revenue": {"min": 0.0, "allow_null": True}
        }
    }
}
