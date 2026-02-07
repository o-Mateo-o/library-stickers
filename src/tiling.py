from __future__ import annotations

import json
import math
from dataclasses import dataclass
from pathlib import Path
from typing import Sequence

from PIL import Image, ImageDraw, ImageFont
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

from src.utils import with_temp_dir

TEMP_DIR = Path(".temp")


@dataclass
class DesignConfig:
    template_path: str

    font_path: str
    font_size: int
    text_color: str
    text_y_align: float
    # NOTE:LAYOUT: if the template has horizontal, not vertical orientation,
    # change `text_y_align` to `text_x_align` and modify `_fill_sticker_template`

    grid_columns: int
    grid_rows: int

    start_row: int = 1
    start_col: int = 1

    @staticmethod
    def load_from_json(config_path: Path) -> DesignConfig:
        with open(config_path, "r", encoding="utf-8") as f:
            full_data = json.load(f)

        data = full_data.get("design", {})
        font = data.get("font", {})
        grid = data.get("grid", {})

        if not data["template"]:
            raise ValueError("Template path must be specified in the configuration.")
        if not font.get("path"):
            raise ValueError("Font path must be specified in the configuration.")

        return DesignConfig(
            template_path=data["template"],
            font_path=font["path"],
            font_size=font.get("size", 80),
            text_color=font.get("color", "#000000"),
            text_y_align=font.get("text-y-align", 0.5),
            grid_columns=grid.get("columns", 3),
            grid_rows=grid.get("rows", 7),
        )

    def set_initial_cell(self, row: int, col: int) -> None:
        self.start_row = row
        self.start_col = col

    def set_initial_cell_ordinal(self, ordinal: int) -> None:
        row = (ordinal - 1) // self.grid_columns + 1
        col = (ordinal - 1) % self.grid_columns + 1
        self.set_initial_cell(row, col)

    @property
    def initall_cell_oridinal(self) -> int:
        return self.grid_columns * (self.start_row - 1) + self.start_col

    @property
    def max_cell_ordinal(self) -> int:
        return self.grid_columns * self.grid_rows


class PdfCreator:
    PAGE_SIZE = A4
    PAGE_WIDTH, PAGE_HEIGHT = PAGE_SIZE

    def __init__(self, config: DesignConfig) -> None:
        self.config = config
        self._load_assets()

    def _load_assets(self) -> None:
        self.sticker_template = Image.open(self.config.template_path).convert("RGBA")
        self.font = ImageFont.truetype(self.config.font_path, self.config.font_size)

    @property
    def sticker_size(self) -> tuple[float, float]:
        return (
            self.PAGE_WIDTH / self.config.grid_columns,
            self.PAGE_HEIGHT / self.config.grid_rows,
        )

    def build_sticker(self, text: str | None = None) -> Image.Image:
        template_img = self.sticker_template.copy()
        if text:
            self._fill_sticker_template(text, template_img)
        return template_img

    def _fill_sticker_template(self, text: str, template_img: Image.Image) -> None:
        img_width, img_height = template_img.size
        draw = ImageDraw.Draw(template_img)
        draw.text(
            (img_width // 2, int(img_height * self.config.text_y_align)),
            text,
            fill=self.config.text_color,
            font=self.font,
            anchor="mt",  # middle-top
        )

    @with_temp_dir(TEMP_DIR)
    def generate_pdf(self, texts: Sequence[str | None], output: Path) -> dict[str, int]:
        canvas_ = canvas.Canvas(str(output), pagesize=self.PAGE_SIZE)

        layout = self._calculate_layout()
        total_pages = self._calculate_total_pages(len(texts), layout)
        _left_last_page = self._calculate_left_last_page(
            len(texts), total_pages, layout
        )

        idx = 0

        for page in range(total_pages):
            idx = self._render_page(
                canvas_=canvas_,
                texts=texts,
                start_idx=idx,
                layout=layout,
                page_number=page,
            )
            canvas_.showPage()

        canvas_.save()

        return {"total_pages": total_pages, "left_last_page": _left_last_page}

    def _calculate_layout(self) -> dict[str, int | float]:
        sticker_width = self.PAGE_WIDTH / self.config.grid_columns
        sticker_height = self.PAGE_HEIGHT / self.config.grid_rows

        return {
            "rows": self.config.grid_rows,
            "cols": self.config.grid_columns,
            "sticker_w": sticker_width,
            "sticker_h": sticker_height,
            "per_page": self.config.grid_rows * self.config.grid_columns,
        }

    def _calculate_total_pages(
        self, total_stickers: int, layout: dict[str, int | float]
    ) -> int:
        _blank_cells = self.config.initall_cell_oridinal - 1
        total_cells = total_stickers + _blank_cells
        if per_page := layout.get("per_page"):
            return math.ceil(total_cells / per_page)
        return 0

    def _calculate_left_last_page(
        self, total_stickers: int, total_pages: int, layout: dict[str, int | float]
    ) -> int:
        _blank_cells = self.config.initall_cell_oridinal - 1
        first_page_capacity = layout["per_page"] - _blank_cells

        if total_pages == 1:
            return int(first_page_capacity - total_stickers)

        remaining = total_stickers - first_page_capacity
        stickers_last_page = remaining % layout["per_page"] or layout["per_page"]

        return int(layout["per_page"] - stickers_last_page)

    def _render_page(
        self,
        canvas_: canvas.Canvas,
        texts: Sequence[str | None],
        start_idx: int,
        layout: dict[str, int | float],
        page_number: int,
    ) -> int:
        idx = start_idx

        for row in range(int(layout["rows"])):
            for col in range(int(layout["cols"])):

                if self._should_skip_cell(page_number, row, col):
                    continue

                if idx >= len(texts):
                    return idx

                self._draw_sticker(
                    canvas_=canvas_,
                    text=texts[idx],
                    idx=idx,
                    row=row,
                    col=col,
                    layout=layout,
                )
                idx += 1

        return idx

    def _should_skip_cell(self, page: int, row: int, col: int) -> bool:
        if page != 0:
            return False

        _start_row = self.config.start_row - 1
        _start_col = self.config.start_col - 1

        return row < _start_row or (row == _start_row and col < _start_col)

    def _draw_sticker(
        self,
        canvas_: canvas.Canvas,
        text: str | None,
        idx: int,
        row: int,
        col: int,
        layout: dict[str, int | float],
    ) -> None:
        sticker = self.build_sticker(text)

        x = col * layout["sticker_w"]
        y = self.PAGE_HEIGHT - (row + 1) * layout["sticker_h"]

        temp_path = Path(TEMP_DIR / f"_tmp_{idx}.png")
        sticker.save(temp_path)

        canvas_.drawImage(
            str(temp_path),
            x,
            y,
            width=layout["sticker_w"],
            height=layout["sticker_h"],
            mask="auto",
        )


def validate_template_ratio(
    pdf_creator: PdfCreator,
) -> tuple[bool, tuple[float, float]]:
    sticker_w, sticker_h = pdf_creator.sticker_size
    template_w, template_h = pdf_creator.sticker_template.size
    sticker_ratio, template_ratio = sticker_w / sticker_h, template_w / template_h
    validation_result = math.isclose(sticker_ratio, template_ratio, rel_tol=1e-1)
    return validation_result, (sticker_ratio, template_ratio)
