"""Local analytical SQL engine powered by DuckDB over DataFrames and Parquet."""
import time
from typing import Dict, Tuple, Optional, Any
import duckdb
import pandas as pd


class SQLEngine:
    """Analytical SQL engine running on in-memory DuckDB with access to clean tables and Parquet."""

    def __init__(self):
        self._con = duckdb.connect(database=":memory:")
        self._registered_tables: Dict[str, int] = {}

    def register_tables(
        self,
        analytics_df: Optional[pd.DataFrame] = None,
        products_df: Optional[pd.DataFrame] = None,
        inventory_df: Optional[pd.DataFrame] = None,
        expiry_df: Optional[pd.DataFrame] = None,
        sales_df: Optional[pd.DataFrame] = None
    ) -> None:
        """Registers pandas DataFrames as DuckDB relational tables/views."""
        tables = {
            "analytics": analytics_df,
            "products": products_df,
            "inventory": inventory_df,
            "expiry": expiry_df,
            "sales": sales_df
        }
        for name, df in tables.items():
            if df is not None and not df.empty:
                self._con.register(name, df)
                self._registered_tables[name] = len(df)

    def get_registered_tables(self) -> Dict[str, int]:
        return self._registered_tables.copy()

    def get_table_schema(self, table_name: str) -> pd.DataFrame:
        """Returns column names and types for a registered table."""
        try:
            return self._con.execute(f"DESCRIBE {table_name}").df()
        except Exception:
            return pd.DataFrame()

    def execute_query(self, query: str) -> Tuple[Optional[pd.DataFrame], float, Optional[str]]:
        """
        Executes a SQL query against the registered tables.
        Returns (result_df, execution_time_ms, error_message).
        """
        start = time.time()
        try:
            # DuckDB query execution
            res_df = self._con.execute(query).df()
            elapsed_ms = round((time.time() - start) * 1000, 2)
            return res_df, elapsed_ms, None
        except Exception as e:
            elapsed_ms = round((time.time() - start) * 1000, 2)
            return None, elapsed_ms, str(e)
