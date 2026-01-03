import re
from pathlib import Path

import pandas as pd

from src.fetching import SQLiteClient


class DataCollector:
    CALLNUMBER_REGEX = re.compile(r"^[A-Z]\d+/\d+-\d{3}$")

    @staticmethod
    def get_data(config_path: Path) -> pd.DataFrame:
        with SQLiteClient(config_path) as db:
            books_df = db.dataframe_from_sql_file("src/query.sql")
        return books_df

    def validate_unique_callnumbers(self, df: pd.DataFrame) -> bool:
        return df["callnumber"].is_unique

    def validate_callnumber_format(self, df: pd.DataFrame) -> bool:
        return bool(
            df["callnumber"]
            .apply(lambda cn: bool(self.CALLNUMBER_REGEX.match(cn)))
            .all()
        )

    # def filter_by_callnumber_prefix(self, df: pd.DataFrame, prefix: str) -> pd.DataFrame:
    #     return df[df['callnumber'].str.startswith(prefix)]

    def get_callnumber_list(self, df: pd.DataFrame) -> list[str]:
        callnumbers = (
            df.sort_values("callnumber").loc[:, ["callnumber", "quantity"]].values,
        )[0]
        result = []
        for callnumber, quantity in callnumbers:
            result.extend([callnumber] * int(quantity))
        return result

    def get_excel_export(self, df: pd.DataFrame, output_path: Path) -> None:
        excel_df = df[
            ["callnumber", "quantity", "title", "author", "publisher"]
        ].sort_values("callnumber")
        excel_df.to_excel(output_path, index=False)
