from pathlib import Path

from src.aggregation import CallnumberParseError
from src.aggregation import DataCollectorService as dcs
from src.frontend import App, MainWindow
from src.tiling import DesignConfig, PdfCreator, validate_template_ratio
from src.utils import AppError, errordialog

CONFIG_PATH = Path("config.json")


@errordialog(AppError)
def process(parent: MainWindow) -> None:
    # creator initialization
    config = DesignConfig.load_from_json(CONFIG_PATH)
    init_cell = int(parent.init_cell.get_value())
    if init_cell > config.max_cell_ordinal:
        raise AppError(
            f"Maksymalna pozycja pierwszej komórki to {config.max_cell_ordinal}"
        )
    config.set_initial_cell_ordinal(init_cell)
    pdf_creator = PdfCreator(config)

    # template ratio warning
    is_valid, (sticker_ratio, template_ratio) = validate_template_ratio(pdf_creator)

    # query load
    query = parent.query_entry.get_text()
    if not query:
        raise CallnumberParseError("Puste zapytanie")

    # get and validate data
    data = dcs.get_data(CONFIG_PATH)
    dcs.validate_unique_callnumbers(data)
    dcs.validate_callnumber_format(data)

    # process data
    filtered_data = dcs.filter_data(data, query)
    contents = dcs.get_callnumber_list(filtered_data)

    # generate files
    info = pdf_creator.generate_pdf(contents, parent.pdf_path)
    dcs.get_excel_export(filtered_data, parent.excel_path)

    # info
    parent.show_info(
        "Wygenerowano pliki",
        f"Arkusz z naklejkami zajął {info['total_pages']} stron.\n"
        f"Zaczęto od pola nr {init_cell} na pierwszej stronie,\n"
        f"na ostatniej stronie zostaje {info['left_last_page']} pól.\n\n"
        "W skoroszycie znajduje się wykaz książek odpowiadających naklejkom.",
    )
    if not is_valid:
        parent.show_warning(
            "Proporcje naklejek w arkuszu są inne od proporcji szablonu naklejki: "
            f"{sticker_ratio:.2f} vs {template_ratio:.2f}"
        )


def run() -> None:
    App(proccesing_method=process, config_path=CONFIG_PATH).run()
