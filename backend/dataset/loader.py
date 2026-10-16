import os
import json
import pandas as pd
from typing import Tuple, Dict, Any

class DatasetLoader:
    """Multi-format dataset loader supporting CSV, JSON, and JSONL."""

    SUPPORTED_FORMATS = {".csv", ".json", ".jsonl"}

    @classmethod
    def load(cls, file_path: str, max_rows: int = None) -> Tuple[pd.DataFrame, Dict[str, Any]]:
        """Load dataset from file into pandas DataFrame with metadata.
        
        Args:
            file_path: Absolute or relative path to data file.
            max_rows: Optional row limit for inspection previews.
            
        Returns:
            Tuple of (DataFrame, metadata_dict)
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Dataset file not found: {file_path}")

        file_size_bytes = os.path.getsize(file_path)
        if file_size_bytes == 0:
            raise ValueError("Dataset file is empty (0 bytes).")

        ext = os.path.splitext(file_path)[1].lower()
        if ext not in cls.SUPPORTED_FORMATS:
            raise ValueError(f"Unsupported file format '{ext}'. Supported: {', '.join(cls.SUPPORTED_FORMATS)}")

        try:
            if ext == ".csv":
                # Try UTF-8 first, fallback to latin-1
                try:
                    df = pd.read_csv(file_path, nrows=max_rows, encoding="utf-8")
                except UnicodeDecodeError:
                    df = pd.read_csv(file_path, nrows=max_rows, encoding="latin-1")
            elif ext == ".json":
                with open(file_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                if isinstance(data, list):
                    df = pd.DataFrame(data[:max_rows] if max_rows else data)
                elif isinstance(data, dict):
                    # Handle records orientation
                    if "records" in data and isinstance(data["records"], list):
                        df = pd.DataFrame(data["records"][:max_rows] if max_rows else data["records"])
                    elif "data" in data and isinstance(data["data"], list):
                        df = pd.DataFrame(data["data"][:max_rows] if max_rows else data["data"])
                    else:
                        df = pd.DataFrame([data])
                else:
                    raise ValueError("JSON file root structure must be an array or object of records.")
            elif ext == ".jsonl":
                records = []
                with open(file_path, "r", encoding="utf-8") as f:
                    for i, line in enumerate(f):
                        if max_rows and i >= max_rows:
                            break
                        line_str = line.strip()
                        if line_str:
                            records.append(json.loads(line_str))
                df = pd.DataFrame(records)
            else:
                raise ValueError(f"Unsupported extension: {ext}")
        except Exception as e:
            raise ValueError(f"Failed to parse dataset file: {str(e)}")

        if df.empty:
            raise ValueError("Parsed dataset resulted in an empty table with 0 records.")

        metadata = {
            "file_path": file_path,
            "filename": os.path.basename(file_path),
            "format": ext.lstrip("."),
            "file_size_bytes": file_size_bytes,
            "loaded_rows": len(df),
            "loaded_columns": len(df.columns),
            "column_names": list(df.columns)
        }

        return df, metadata
