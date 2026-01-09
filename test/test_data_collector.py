import unittest

import pandas as pd

from src.aggregation import DataCollectorService, DBValidationError


class BaseDataCollectorTest(unittest.TestCase):
    def setUp(self):
        self.df = pd.DataFrame(
            {
                "title": ["Book A", "Book B", "Book C"],
                "author": ["Author X", "Author Y", "Author Z"],
                "publisher": ["Pub1", "Pub2", "Pub3"],
                "callnumber": ["K5/5-001", "K4/11-101", "B1/1-023"],
                "quantity": [2, 1, 3],
            }
        )
        self.collector = DataCollectorService


class TestValidateUniqueCallnumbers(BaseDataCollectorTest):
    def test_unique_callnumbers(self):
        self.collector.validate_unique_callnumbers(self.df)

    def test_duplicate_callnumbers(self):
        df_dup = self.df.copy()
        df_dup.loc[1, "callnumber"] = "K5/5-001"
        with self.assertRaises(DBValidationError):
            self.collector.validate_unique_callnumbers(df_dup)


class TestValidateCallnumberFormat(BaseDataCollectorTest):
    def test_valid_callnumber_format(self):
        self.collector.validate_callnumber_format(self.df)

    def test_invalid_callnumber_format(self):
        df_invalid = self.df.copy()
        df_invalid.loc[0, "callnumber"] = "InvalidCN"
        with self.assertRaises(DBValidationError):
            self.collector.validate_callnumber_format(df_invalid)


class TestGetCallnumberList(BaseDataCollectorTest):
    def test_list_repeats_by_quantity_and_sorted(self):
        result = self.collector.get_callnumber_list(self.df)
        expected_order = sorted(["K5/5-001"] * 2 + ["K4/11-101"] * 1 + ["B1/1-023"] * 3)
        self.assertEqual(result, expected_order)

    def test_zero_quantity_ignored(self):
        df_zero = self.df.copy()
        df_zero.loc[0, "quantity"] = 0
        result = self.collector.get_callnumber_list(df_zero)
        self.assertNotIn("K5/5-001", result)
