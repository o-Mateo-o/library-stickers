from pathlib import Path

from src.aggregation import CallnumberParseError
from src.aggregation import DataCollectorService as dcs
from src.frontend import MyApp
from src.tiling import DesignConfig, PdfCreator, validate_template_ratio
from src.utils import AppError

CONFIG_PATH = Path("config.json")


def run() -> None:
    MyApp().run()
    #
    #
    #


def runnn():
    config = DesignConfig.load_from_json(CONFIG_PATH)
    config.set_initial_cell(row=1, col=2)
    pdf_creator = PdfCreator(config)

    is_valid, (sticker_ratio, template_ratio) = validate_template_ratio(pdf_creator)
    if not is_valid:
        print(
            "The sticker template ratio does not match the configured sticker size ratio: "
            f"{sticker_ratio:.2f} vs {template_ratio:.2f}"
        )  # FIXME: should be a log-warning
    # FIXME: catch all AppErrors as log-error (and file-not-found like)

    data = dcs.get_data(CONFIG_PATH)
    #################
    user_input = ""  # "B1/4-002--B1/5"
    _out_path_excel = Path(
        "/home/postulat/Desktop/biblioteka-export.xlsx",
    )
    _out_path_pdf = Path("/home/postulat/Desktop/biblioteka-naklejki.pdf")
    # FIXME: load default paths from json
    ####################
    # validate data
    dcs.validate_unique_callnumbers(data)
    dcs.validate_callnumber_format(data)
    if not user_input:
        raise CallnumberParseError("Puste zapytanie")
    filtered_data = dcs.filter_data(data, user_input)
    contents = dcs.get_callnumber_list(filtered_data)

    _info = pdf_creator.generate_pdf(contents, _out_path_pdf)
    print(f"Generated PDF with info: {_info}")
    dcs.get_excel_export(filtered_data, _out_path_excel)
