"""Data ingestion module for loading CSV and Parquet files safely."""
import io
from pathlib import Path
from typing import Union, Tuple, Optional
import pandas as pd


class DataLoader:
    """Safe ingestion handler for CSV and Parquet files with format sniffing."""

    @staticmethod
    def load_file(
        source: Union[str, Path, io.BytesIO, bytes],
        filename: Optional[str] = None
    ) -> Tuple[Optional[pd.DataFrame], Optional[str]]:
        """
        Loads a DataFrame from a file path, file buffer, or byte stream.
        Returns (DataFrame, error_message).
        """
        try:
            # Determine extension
            ext = ""
            if isinstance(source, (str, Path)):
                path_obj = Path(source)
                ext = path_obj.suffix.lower()
                if not path_obj.exists():
                    return None, f"File does not exist: {path_obj}"
            elif filename:
                ext = Path(filename).suffix.lower()

            # Handle Parquet
            if ext == ".parquet":
                if isinstance(source, (str, Path)):
                    df = pd.read_parquet(source)
                else:
                    if isinstance(source, bytes):
                        source = io.BytesIO(source)
                    df = pd.read_parquet(source)
                return df, None

            # Handle CSV (with encoding fallbacks)
            encodings = ["utf-8", "utf-8-sig", "latin-1", "cp1252"]
            last_err = None

            for enc in encodings:
                try:
                    if isinstance(source, (str, Path)):
                        df = pd.read_csv(source, encoding=enc)
                        return df, None
                    else:
                        # Reset buffer position if seekable
                        if hasattr(source, "seek"):
                            source.seek(0)
                        elif isinstance(source, bytes):
                            source = io.BytesIO(source)
                        df = pd.read_csv(source, encoding=enc)
                        return df, None
                except (UnicodeDecodeError, pd.errors.ParserError) as e:
                    last_err = str(e)
                    continue

            return None, f"Failed to parse CSV file with supported encodings. Detail: {last_err}"

        except Exception as e:
            return None, f"Error reading file: {str(e)}"

    @staticmethod
    def export_parquet(df: pd.DataFrame, target_path: Union[str, Path]) -> Tuple[bool, Optional[str]]:
        """Saves DataFrame as Parquet with snappy compression."""
        try:
            target_path = Path(target_path)
            target_path.parent.mkdir(parents=True, exist_ok=True)
            df.to_parquet(target_path, engine="pyarrow", compression="snappy", index=False)
            return True, None
        except Exception as e:
            return False, f"Failed to export Parquet: {str(e)}"
