from __future__ import annotations

import operator
import re
from abc import ABC, abstractmethod
from collections import namedtuple
from dataclasses import astuple, dataclass
from functools import partial, reduce
from pathlib import Path
from typing import TypedDict, cast

import pandas as pd
from openpyxl.styles import Alignment, Font
from openpyxl.worksheet.worksheet import Worksheet

from src.fetching import SQLiteClient
from src.utils import AppError, arg_tuple_not_none

INPUT_PARTS_SEPARATOR = ";"
INPUT_RANGE_SEPARATOR = "--"


class CallnumberParseError(AppError): ...


class DBValidationError(AppError): ...


CallnumberTuple = namedtuple(
    "CallnumberTuple", ["room_", "bookcase_", "shelf_", "book_"]
)


class CallnumberGroupsDict(TypedDict):
    room: str
    bookcase: int | None
    shelf: int | None
    book: int | None


class Condition(ABC):
    @abstractmethod
    def assess(self, callnumber_tuple: CallnumberTuple) -> bool:
        pass


@dataclass
class CallnumberCondition(Condition):
    """The 'room' parameter is unordered literal, the rest are ordered integers"""

    room: str
    bookcase: int | None = None
    shelf: int | None = None
    book: int | None = None

    def __post_init__(self) -> None:
        for field in ("bookcase", "shelf", "book"):
            value = getattr(self, field)
            if value is not None:
                setattr(self, field, int(value))

    PATTERN = re.compile(
        r"^(?P<room>[A-Z])(?P<bookcase>\d+)/(?P<shelf>\d+)-(?P<book>\d{3})$"
    )
    PARTIAL_PATTERNS = [
        re.compile(PATTERN),
        re.compile(r"^(?P<room>[A-Z])(?P<bookcase>\d+)/(?P<shelf>\d+)$"),
        re.compile(r"^(?P<room>[A-Z])(?P<bookcase>\d+)$"),
        re.compile(r"^(?P<room>[A-Z])$"),
    ]

    @property
    def maxlevel(self) -> int:
        if self.book:
            return 4
        if self.shelf:
            return 3
        if self.bookcase:
            return 2
        return 1

    @arg_tuple_not_none
    def assess(self, callnumber_tuple: CallnumberTuple) -> bool:
        field_values = callnumber_tuple
        condition_values = astuple(self)
        return condition_values[: self.maxlevel] == field_values[: self.maxlevel]

    @classmethod
    def from_text(cls, text: str) -> CallnumberCondition:
        for pattern in cls.PARTIAL_PATTERNS:
            if callnumber := cls._parse(pattern, text):
                return callnumber
        raise CallnumberParseError(f"Nieprawidłowy wzór: {text}")

    @staticmethod
    def _parse(pattern: re.Pattern, text: str) -> CallnumberCondition | None:
        result = pattern.search(text)
        if result is None:
            return None
        groups = cast(CallnumberGroupsDict, result.groupdict())
        return CallnumberCondition(
            room=groups["room"],
            bookcase=groups.get("bookcase"),
            shelf=groups.get("shelf"),
            book=groups.get("book"),
        )

    @classmethod
    def parse_full(cls, text: str) -> CallnumberTuple | tuple[None, None, None, None]:
        result = cls.PATTERN.search(text.upper())
        if (not result) or (result.lastindex != 4):
            return (None,) * 4
        groups = cast(CallnumberGroupsDict, result.groupdict())
        return CallnumberTuple(*astuple(CallnumberCondition(**groups)))


@dataclass
class CallnumberRangeCondition(Condition):
    start: CallnumberCondition
    end: CallnumberCondition

    # TODO: add a method to initialize from two strings with no need to give ready CallnumberCondition objects

    def __post_init__(self) -> None:
        _start_room = self.start.room
        _end_room = self.end.room
        if _start_room != _end_room:
            raise CallnumberParseError(
                f"Pojedynczy zakres nie może obejmować więcej niż jednego pomieszczenia: {_start_room}-{_end_room}"
            )

    @property
    def room(self) -> str:
        return self.start.room

    @arg_tuple_not_none
    def assess(self, callnumber_tuple: CallnumberTuple) -> bool:
        field_values = callnumber_tuple[1:]
        _result_left = (
            astuple(self.start)[1 : self.start.maxlevel]
            <= field_values[: self.start.maxlevel]
        )
        _result_right = (
            astuple(self.end)[1 : self.end.maxlevel]
            >= field_values[: self.end.maxlevel]
        )
        _result_room = self.room == callnumber_tuple.room_
        if _result_room and _result_left and _result_right:
            return True
        return False


class CallnumberFilteringService:
    # TODO: get_conditions could be a separate function
    # to first check if the query is valid and then load the dataset
    @classmethod
    def filter(cls, df: pd.DataFrame, query: str) -> pd.DataFrame:
        query = query.strip().upper()
        conditions = cls._decompose_query(query)
        df = pd.concat([df, cls._parse_df_callnumber(df)], axis=1)
        df["_result"] = df[list(CallnumberTuple._fields)].apply(
            partial(cls.apply_conditions, conditions), axis=1
        )
        return df[df["_result"] == True]

    @staticmethod
    def _decompose_query(query: str) -> list[Condition]:
        parts = query.split(INPUT_PARTS_SEPARATOR)
        conditions: list[Condition] = []
        for part in parts:
            part_elements = list(filter(None, part.split(INPUT_RANGE_SEPARATOR)))
            if len(part_elements) == 1:
                conditions.append(CallnumberCondition.from_text(part_elements[0]))
            elif len(part_elements) == 2:
                _start = CallnumberCondition.from_text(part_elements[0])
                _end = CallnumberCondition.from_text(part_elements[1])
                conditions.append(CallnumberRangeCondition(start=_start, end=_end))
            else:
                raise CallnumberParseError(f"Nieprawidłowo zdefiniowany zakres: {part}")
        return conditions

    @staticmethod
    def apply_conditions(conditions: list[Condition], cols_obj: pd.Series) -> bool:
        return reduce(
            operator.or_,
            (condit.assess(CallnumberTuple(*cols_obj.values)) for condit in conditions),
        )

    @classmethod
    def _parse_df_callnumber(
        cls, df: pd.DataFrame, callnumber_col: str = "callnumber"
    ) -> pd.DataFrame:
        """Return columns with decomposed parts of a callnumber"""
        return pd.DataFrame(
            df[callnumber_col].map(CallnumberCondition.parse_full).tolist()
        )


EXPORT_COLUMN_NAMES = {
    "callnumber": "Sygnatura",
    "quantity": "Liczba sztuk",
    "title": "Tytuł",
    "author": "Autor",
    "publisher": "Wydawca",
}


class DataCollectorService:
    @staticmethod
    def get_data(config_path: Path) -> pd.DataFrame:
        with SQLiteClient(config_path) as db:
            books_df = db.dataframe_from_sql_file("src/basequery.sql")
        return books_df

    @staticmethod
    def validate_unique_callnumbers(df: pd.DataFrame) -> None:
        if not df["callnumber"].is_unique:
            raise DBValidationError("Sygnatury w bazie danych nie są unikalne")

    @staticmethod
    def validate_callnumber_format(df: pd.DataFrame) -> None:
        results = df["callnumber"].apply(
            lambda cn: bool(CallnumberCondition.PATTERN.match(cn))
        )
        if not results.all():
            invalid_values = df.loc[~results, "callnumber"].tolist()
            raise DBValidationError(
                f"Nieprawidłowe sygnatury w bazie danych: {invalid_values}"
            )

    @staticmethod
    def filter_data(df: pd.DataFrame, query: str) -> pd.DataFrame:
        """A simplified filtering solution; works fast only with small databases"""
        return CallnumberFilteringService.filter(df, query)

    @staticmethod
    def get_callnumber_list(df: pd.DataFrame) -> list[str]:
        callnumbers = (
            df.sort_values("callnumber").loc[:, ["callnumber", "quantity"]].values,
        )[0]
        result = []
        for callnumber, quantity in callnumbers:
            result.extend([callnumber] * int(quantity))
        return result

    @classmethod
    def get_excel_export(cls, df: pd.DataFrame, output_path: Path) -> None:
        excel_df = df[
            ["callnumber", "quantity", "title", "author", "publisher"]
        ].sort_values("callnumber")
        excel_df = excel_df.rename(columns=EXPORT_COLUMN_NAMES)

        with pd.ExcelWriter(output_path, engine="openpyxl") as writer:
            excel_df.to_excel(writer, index=False)
            worksheet = writer.sheets["Sheet1"]
            cls._format_worksheet(worksheet)

    @staticmethod
    def _format_worksheet(worksheet: Worksheet) -> None:
        # alignment
        for row in worksheet.iter_rows():
            for cell in row:
                cell.alignment = Alignment(horizontal="left")
        # header row
        for cell in worksheet[1]:
            cell.font = Font(bold=True)
        # column width
        for col in worksheet.columns:
            max_length = 0
            column = col[0].column_letter
            for cell in col:
                if cell.value is not None:
                    max_length = max(max_length, len(str(cell.value)))
            adjusted_width = max_length + 2
            worksheet.column_dimensions[column].width = adjusted_width
