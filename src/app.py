from pathlib import Path

from src.tiling import DesignConfig, PdfCreator, validate_template_ratio

CONFIG_PATH = Path("config.json")


def run() -> None:
    config = DesignConfig.load_from_json(CONFIG_PATH)
    config.set_initial_cell(row=1, col=2)
    pdf_creator = PdfCreator(config)

    is_valid, (sticker_ratio, template_ratio) = validate_template_ratio(pdf_creator)
    if not is_valid:
        print(
            "The sticker template ratio does not match the configured sticker size ratio: "
            f"{sticker_ratio:.2f} vs {template_ratio:.2f}"
        )

    sample_texts: list[str | None] = [f"Sticker {i + 1}" for i in range(50)]
    _info = pdf_creator.generate_pdf(
        sample_texts, Path.home() / Path("Desktop/output_stickers.pdf")
    )
    print(f"Generated PDF with info: {_info}")
