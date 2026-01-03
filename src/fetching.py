from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any

import pandas as pd


class SQLiteClient:
    def __init__(self, config_path: Path):
        self.db_path = self._load_db_path_from_json(config_path)
        self.connection: sqlite3.Connection | None = None

    def _load_db_path_from_json(self, config_path: Path) -> Path:
        with open(config_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        db_path_str = data.get("db", {}).get("path")
        if not db_path_str:
            raise ValueError("Database path not found in the provided JSON file.")
        return Path(db_path_str)

    def connect(self) -> None:
        if not self.db_path:
            raise ValueError("Database path must be provided to connect.")
        self.connection = sqlite3.connect(self.db_path)
        self.connection.row_factory = sqlite3.Row

    def close(self) -> None:
        if self.connection:
            self.connection.close()
            self.connection = None

    def dataframe_from_sql_file(self, sql_file_path: str) -> pd.DataFrame:
        if not self.connection:
            raise RuntimeError("Database connection is not established.")

        sql_path = Path(sql_file_path)
        if not sql_path.exists():
            raise FileNotFoundError(f"SQL file not found: {sql_file_path}")

        query = sql_path.read_text(encoding="utf-8")

        return pd.read_sql_query(query, self.connection)

    def __enter__(self) -> SQLiteClient:
        self.connect()
        return self

    def __exit__(self, exc_type: Any, exc_value: Any, traceback: Any) -> None:
        self.close()
