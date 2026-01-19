import unittest
from unittest.mock import MagicMock, patch

import pandas as pd
from parameterized import parameterized

from src.aggregation import (
    CallnumberCondition,
    CallnumberFilteringService,
    CallnumberParseError,
    CallnumberRangeCondition,
    CallnumberTuple,
)


class TestCallnumberCondition(unittest.TestCase):

    def test_initialization_casts_ints(self):
        cond = CallnumberCondition(room="A", bookcase="12", shelf="3", book="2")
        self.assertEqual(cond.bookcase, 12)
        self.assertEqual(cond.shelf, 3)
        self.assertEqual(cond.book, 2)

    def test_initialization_requires_room(self):
        with self.assertRaises(TypeError):
            CallnumberCondition(bookcase=1)  # room missing

    @parameterized.expand(
        [
            ("A", ("A", None, None, None)),
            ("A12", ("A", 12, None, None)),
            ("A12/3", ("A", 12, 3, None)),
            ("B14/4-002", ("B", 14, 4, 2)),
        ],
    )
    def test_from_text_valid_patterns(self, text, expected):
        cond = CallnumberCondition.from_text(text)
        self.assertEqual(tuple(cond.__dict__.values()), expected)

    @parameterized.expand(
        [
            "12/3-012",
            "B12-022",
            "A1/2-0229",
        ],
    )
    def test_from_text_invalid_patterns(self, text):
        with self.assertRaises(CallnumberParseError):
            CallnumberCondition.from_text(text)

    def test_parse_full_valid(self):
        result = CallnumberCondition.parse_full("a12/3-002")
        self.assertEqual(tuple(result), CallnumberTuple("A", 12, 3, 2))

    def test_parse_full_invalid(self):
        result = CallnumberCondition.parse_full("A12-002")
        self.assertEqual(result, (None, None, None, None))

    @parameterized.expand(
        [
            (
                CallnumberCondition(room="A"),
                CallnumberTuple("A", 1, 1, 1),
                True,
            ),
            (
                CallnumberCondition(room="A", bookcase=2),
                CallnumberTuple("A", 2, 9, 9),
                True,
            ),
            (
                CallnumberCondition(room="A", bookcase=2, shelf=3),
                CallnumberTuple("A", 2, 3, 9),
                True,
            ),
            (
                CallnumberCondition(room="A", bookcase=2, shelf=3, book=4),
                CallnumberTuple("A", 2, 3, 4),
                True,
            ),
            (
                CallnumberCondition(room="A", bookcase=2),
                CallnumberTuple("B", 2, 1, 1),
                False,
            ),
        ],
    )
    def test_assess_for_different_levels(self, condition, callnumber, expected):
        self.assertEqual(condition.assess(callnumber), expected)


class TestCallnumberRangeCondition(unittest.TestCase):

    def test_init_same_room_required(self):
        start = CallnumberCondition.from_text("A11/2-002")
        end = CallnumberCondition.from_text("B3/2-932")

        with self.assertRaises(CallnumberParseError):
            CallnumberRangeCondition(start=start, end=end)

    @parameterized.expand(
        [
            (
                "A10",
                "A20",
                CallnumberTuple("A", 15, 1, 1),
                True,
            ),
            (
                "A10/2",
                "A10/4",
                CallnumberTuple("A", 10, 3, 1),
                True,
            ),
            (
                "A10/2-001",
                "A10/2-010",
                CallnumberTuple("A", 10, 2, 5),
                True,
            ),
            (
                "A10",
                "A20",
                CallnumberTuple("B", 15, 1, 1),
                False,
            ),
        ],
    )
    def test_assess_range(self, start, end, callnumber, expected):
        condition = CallnumberRangeCondition(
            start=CallnumberCondition.from_text(start),
            end=CallnumberCondition.from_text(end),
        )
        self.assertEqual(condition.assess(callnumber), expected)


class TestCallnumberFilteringService(unittest.TestCase):

    @parameterized.expand(
        [
            ("A11/2-002", 1),
            ("A11/2-002--A12/3-123", 1),
            ("A11/2-002;B1/2-002", 2),
            ("A11/2-002;B1/2-002--B2/1-010", 2),
        ],
    )
    def test_decompose_query_valid(self, query_text, expected_count):
        conditions = CallnumberFilteringService._decompose_query(query_text)
        self.assertEqual(len(conditions), expected_count)

    def test_decompose_query_invalid(self):
        with self.assertRaises(CallnumberParseError):
            CallnumberFilteringService._decompose_query(
                "A11/2-002--A13/2-002--A14/2-002"
            )

    @patch("src.aggregation.CallnumberTuple")
    def test_apply_conditions_mocked(self, mock_tuple):
        mock_condition = MagicMock()
        mock_condition.assess.return_value = True
        mock_cols_obj = pd.Series(("A", 1, 2, 3))
        result = CallnumberFilteringService.apply_conditions(
            [mock_condition], mock_cols_obj
        )

        self.assertTrue(result)
        mock_condition.assess.assert_called_once()


class TestCallnumberFilteringServiceFilter(unittest.TestCase):

    @patch.object(CallnumberFilteringService, "_decompose_query")
    @patch.object(CallnumberFilteringService, "_parse_df_callnumber")
    @patch.object(CallnumberFilteringService, "apply_conditions")
    def test_filter_method(
        self,
        mock_apply,
        mock_parse_df,
        mock_decompose,
    ):
        df = pd.DataFrame(
            {
                "id": [1, 2],
                "callnumber": ["A12/3-002", "B1/2-003"],
            }
        )

        mock_decompose.return_value = [MagicMock()]
        mock_parse_df.return_value = pd.DataFrame(
            [
                ("A", 12, 3, 2),
                ("B", 1, 2, 3),
            ],
            columns=CallnumberTuple._fields,
        )

        mock_apply.side_effect = [True, False]

        result = CallnumberFilteringService.filter(df, "A12")

        self.assertEqual(len(result), 1)
        self.assertEqual(result.iloc[0]["id"], 1)
