import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

from src.tiling import DesignConfig, PdfCreator


class BasePdfTest(unittest.TestCase):
    def setUp(self):
        self.config = DesignConfig(
            template_path="fake_template.png",
            font_path="fake_font.ttf",
            font_size=20,
            text_color="xxx",
            text_y_align=0.5,
            grid_columns=3,
            grid_rows=3,
        )

        with patch.object(PdfCreator, "_load_assets"):
            self.creator = PdfCreator(self.config)

        self.creator.build_sticker = MagicMock(return_value=MagicMock())

        self.layout: dict[str, int | float] = {
            "rows": 3,
            "cols": 3,
            "sticker_w": 100,
            "sticker_h": 100,
            "per_page": 9,
        }


class TestSkipBlankCells(BasePdfTest):
    def test_skip_cells_before_start_cell(self):
        self.config.set_initial_cell(row=2, col=2)

        self.assertTrue(self.creator._should_skip_cell(page=0, row=0, col=0))
        self.assertTrue(self.creator._should_skip_cell(page=0, row=1, col=0))
        self.assertFalse(self.creator._should_skip_cell(page=0, row=1, col=1))

    def test_start_cell_not_skipped(self):
        self.config.set_initial_cell(row=1, col=1)

        self.assertFalse(self.creator._should_skip_cell(page=0, row=0, col=0))

    def test_skip_only_applies_to_first_page(self):
        self.config.set_initial_cell(row=2, col=2)

        self.assertFalse(self.creator._should_skip_cell(page=1, row=0, col=0))
        self.assertFalse(self.creator._should_skip_cell(page=2, row=1, col=1))

    def test_skip_entire_first_row(self):
        self.config.set_initial_cell(row=2, col=1)

        for col in range(3):
            self.assertTrue(self.creator._should_skip_cell(page=0, row=0, col=col))


class TestRendering(BasePdfTest):
    def test_all_texts_drawn_single_page(self):
        texts: list[str | None] = ["A", "B", "C", "D"]
        self.creator._draw_sticker = MagicMock()

        final_idx = self.creator._render_page(
            canvas_=MagicMock(),
            texts=texts,
            start_idx=0,
            layout=self.layout,
            page_number=0,
        )

        self.assertEqual(final_idx, len(texts))
        self.assertEqual(self.creator._draw_sticker.call_count, len(texts))

    def test_skipped_cells_do_not_consume_texts(self):
        self.config.set_initial_cell(row=2, col=2)
        self.creator._draw_sticker = MagicMock()

        texts: list[str | None] = ["A", "B"]

        final_idx = self.creator._render_page(
            canvas_=MagicMock(),
            texts=texts,
            start_idx=0,
            layout=self.layout,
            page_number=0,
        )

        self.assertEqual(final_idx, 2)
        self.assertEqual(self.creator._draw_sticker.call_count, 2)

    def test_empty_text_list(self):
        self.creator._draw_sticker = MagicMock()

        final_idx = self.creator._render_page(
            canvas_=MagicMock(),
            texts=[],
            start_idx=0,
            layout=self.layout,
            page_number=0,
        )

        self.assertEqual(final_idx, 0)
        self.creator._draw_sticker.assert_not_called()


class TestGeneratePdf(BasePdfTest):
    def test_generate_pdf_calls_render_page_for_each_page(self):
        texts: list[str | None] = [f"T{i}" for i in range(20)]

        self.creator._calculate_layout = MagicMock(
            return_value={
                "rows": 2,
                "cols": 2,
                "sticker_w": 100,
                "sticker_h": 100,
                "per_page": 4,
            }
        )
        self.creator._calculate_total_pages = MagicMock(return_value=5)
        self.creator._render_page = MagicMock(side_effect=[4, 8, 12, 16, 20])

        with patch("src.tiling.canvas.Canvas"):
            self.creator.generate_pdf(texts, Path("fake.pdf"))

        self.assertEqual(self.creator._render_page.call_count, 5)


class TestLayoutCalculation(BasePdfTest):
    def test_layout_values(self):
        layout = self.creator._calculate_layout()

        self.assertEqual(layout["rows"], self.config.grid_rows)
        self.assertEqual(layout["cols"], self.config.grid_columns)
        self.assertEqual(
            layout["per_page"],
            self.config.grid_rows * self.config.grid_columns,
        )


class TestCalculateLeftLastPage(BasePdfTest):
    def setUp(self):
        super().setUp()
        self._layout: dict[str, int | float] = {
            "rows": 3,
            "cols": 3,
            "sticker_w": 100,
            "sticker_h": 100,
            "per_page": 9,
        }

    def test_single_page(self):
        self.config.set_initial_cell(row=1, col=1)

        left = self.creator._calculate_left_last_page(
            total_stickers=5,
            total_pages=1,
            layout=self._layout,
        )

        self.assertEqual(left, 4)

    def test_multiple_pages_partial_last_page(self):
        self.config.set_initial_cell(row=1, col=1)

        left = self.creator._calculate_left_last_page(
            total_stickers=14,
            total_pages=2,
            layout=self._layout,
        )

        self.assertEqual(left, 4)

    def test_multiple_pages_full_last_page(self):
        self.config.set_initial_cell(row=1, col=1)

        left = self.creator._calculate_left_last_page(
            total_stickers=18,
            total_pages=2,
            layout=self._layout,
        )

        self.assertEqual(left, 0)
