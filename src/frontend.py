import json
from functools import partial
from pathlib import Path
from typing import Callable

import gi

from src.aggregation import INPUT_PARTS_SEPARATOR, INPUT_RANGE_SEPARATOR

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")

from gi.repository import Adw, Gio, Gtk

INITIAL_CELL_INFO: str = """Naklejki generowane są na siatce numerowanej
od lewej do prawej w kolejnych wierszach, np.:
1   |   2   |   3
4  |   5   |   6
...

Ten parametr pozwala ustawić umiejscowienie pierwszej komórki na siatce.
To przydatne w przypadku, gdy do drukowania używa się papieru naklejkowego
wykorzystanego już do pewnego momentu.
"""
QUERY_INFO: str = f"""Zakres książek. Znak "{INPUT_PARTS_SEPARATOR}" symbolizuje kolejne zakresy,
a "{INPUT_RANGE_SEPARATOR}" używa się do włączenia wszystkich pozycji z przedziału.
Można podawać pojedyncze pokoje, regały, półki lub książki bądź przedziały.
Nie można zaś wybierać zakresu łączącego dwa pomieszczenia, np.: 'K1-B2'.

Przykłady poprawnych zapytań to: 'B1', 'K1/2-003', 'K1/2-002--K2/3-004', 'K2/3;K1/3-002--K1/3-004',
'B1/2;K1;B2/2-002'
"""


def _add_info_icon(row: Adw.ActionRow, text: str) -> None:
    info_button: Gtk.Button = Gtk.Button()
    info_button.add_css_class("circular")
    info_image: Gtk.Image = Gtk.Image.new_from_icon_name("dialog-information")
    info_button.set_child(info_image)
    popover: Gtk.Popover = Gtk.Popover()
    popover.set_child(Gtk.Label(label=text, wrap=True, xalign=0))
    popover.set_has_arrow(True)
    popover.set_parent(info_button)
    info_button.connect("clicked", lambda w: popover.popup())
    row.add_suffix(info_button)


class MainWindow(Adw.ApplicationWindow):
    def __init__(self, app: Adw.Application) -> None:
        super().__init__(application=app)

        # header
        self.set_title("Generator Naklejek Bibliotecznych")
        self.set_default_size(700, 420)
        content: Adw.Clamp = Adw.Clamp(margin_top=24, margin_bottom=24)
        self.set_content(content)
        box: Gtk.Box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=16)
        content.set_child(box)

        # title
        title_label: Gtk.Label = Gtk.Label(label="Generator Nakelejek Bibliotecznych")
        title_label.set_xalign(0.5)
        title_label.add_css_class("title-1")
        title_label.set_margin_bottom(16)
        box.append(title_label)

        # initial cell input
        init_cell_row: Adw.ActionRow = Adw.ActionRow(title="Komórka początkowa")
        self.init_cell: Gtk.SpinButton = Gtk.SpinButton.new_with_range(1, 100, 1)
        self.init_cell.set_value(1)
        init_cell_row.add_suffix(self.init_cell)
        _add_info_icon(init_cell_row, INITIAL_CELL_INFO)
        box.append(init_cell_row)

        # query input
        query_row: Adw.ActionRow = Adw.ActionRow(title="Zakres")
        self.query_entry: Gtk.Entry = Gtk.Entry()
        self.query_entry.set_placeholder_text("Podaj zapytanie...")
        self.query_entry.set_hexpand(True)
        self.query_entry.set_halign(Gtk.Align.FILL)
        query_row.add_suffix(self.query_entry)
        _add_info_icon(query_row, QUERY_INFO)
        box.append(query_row)

        # excel output file selector
        excel_row: Adw.ActionRow = Adw.ActionRow(title="Ścieżka skoroszytu")
        self.excel_label: Gtk.Label = Gtk.Label(xalign=0)
        excel_button: Gtk.Button = Gtk.Button(label="Wybierz..")
        excel_button.connect("clicked", self.choose_excel)
        excel_row.add_suffix(self.excel_label)
        excel_row.add_suffix(excel_button)
        box.append(excel_row)

        # pdf output file selector
        pdf_row: Adw.ActionRow = Adw.ActionRow(title="Ścieżka arkusza naklejek")
        self.pdf_label: Gtk.Label = Gtk.Label(xalign=0)
        pdf_button: Gtk.Button = Gtk.Button(label="Wybierz...")
        pdf_button.connect("clicked", self.choose_pdf)
        pdf_row.add_suffix(self.pdf_label)
        pdf_row.add_suffix(pdf_button)
        box.append(pdf_row)

        # BUTTONS
        buttons_row: Adw.ActionRow = Adw.ActionRow()
        buttons_row.set_selectable(False)
        container: Gtk.Box = Gtk.Box(spacing=12)
        container.set_hexpand(True)
        # run button
        self.run_button: Gtk.Button = Gtk.Button(label="Generuj")
        self.run_button.add_css_class("suggested-action")
        self.run_button.set_hexpand(True)
        self.run_button.set_halign(Gtk.Align.FILL)
        self.run_button.connect(
            "clicked", partial(self.get_application().run_processing, self)
        )
        # close button
        close_button: Gtk.Button = Gtk.Button(label="Zamknij")
        close_button.set_hexpand(True)
        close_button.set_halign(Gtk.Align.FILL)
        close_button.connect("clicked", lambda _: self.close())

        container.append(self.run_button)
        container.append(close_button)
        buttons_row.add_suffix(container)
        box.append(buttons_row)

        self._set_default_paths()

    def _set_default_paths(self) -> None:
        with open(self.get_application().config_path, "r", encoding="utf-8") as f:
            full_data = json.load(f)
        data = full_data.get("output-default", {})
        self.excel_path = Path(data.get("excel", "~/output.xlsx")).expanduser()
        self.pdf_path = Path(data.get("pdf", "~/output.pdf")).expanduser()
        self.excel_label.set_text(str(self.excel_path))
        self.pdf_label.set_text(str(self.pdf_path))

    def choose_excel(self, _: Gtk.Button) -> None:
        self.save_file(
            title="Ścieżka pliku skoroszytu",
            filter_name="Plik .xlsx",
            patterns=["*.xlsx"],
            callback=self.set_excel_path,
        )

    def choose_pdf(self, _: Gtk.Button) -> None:
        self.save_file(
            title="Ścieżka pliku naklejek",
            filter_name="Plik .pdf",
            patterns=["*.pdf"],
            callback=self.set_pdf_path,
        )

    def save_file(
        self,
        title: str,
        filter_name: str,
        patterns: list[str],
        callback: Callable[[str], None],
    ) -> None:
        dialog: Gtk.FileChooserNative = Gtk.FileChooserNative(
            title=title,
            action=Gtk.FileChooserAction.SAVE,
            transient_for=self,
            modal=True,
        )

        file_filter: Gtk.FileFilter = Gtk.FileFilter()
        file_filter.set_name(filter_name)
        for p in patterns:
            file_filter.add_pattern(p)
        dialog.add_filter(file_filter)

        dialog.connect("response", self.on_file_chosen, callback)
        dialog.show()

    def on_file_chosen(
        self,
        dialog: Gtk.FileChooserNative,
        response: int,
        callback: Callable[[str], None],
    ) -> None:
        if response == Gtk.ResponseType.ACCEPT:
            file: Gio.File = dialog.get_file()
            if file is not None:
                callback(file.get_path())
        dialog.destroy()

    def set_excel_path(self, path: str) -> None:
        if not path.lower().endswith(".xlsx"):
            path += ".xlsx"
        self.excel_path = Path(path)
        self.excel_label.set_text(path)

    def set_pdf_path(self, path: str) -> None:
        if not path.lower().endswith(".pdf"):
            path += ".pdf"
        self.pdf_path = Path(path)
        self.pdf_label.set_text(path)

    def show_error(self, message: str) -> None:
        self.show_dialog("Błąd", message, "destructive-action")

    def show_warning(self, message: str) -> None:
        self.show_dialog("Ostrzeżenie", message, "warning")

    def show_info(self, title: str, message: str) -> None:
        self.show_dialog(title, message, "suggested-action")

    def show_dialog(self, title: str, message: str, appearance: str) -> None:
        dialog: Adw.MessageDialog = Adw.MessageDialog(
            transient_for=self,
            modal=True,
            heading=title,
            body=message,
        )

        dialog.add_response("ok", "OK")
        dialog.set_default_response("ok")

        if appearance == "destructive-action":
            dialog.set_response_appearance("ok", Adw.ResponseAppearance.DESTRUCTIVE)
        elif appearance == "suggested-action":
            dialog.set_response_appearance("ok", Adw.ResponseAppearance.SUGGESTED)
        else:
            dialog.set_response_appearance("ok", Adw.ResponseAppearance.DEFAULT)

        dialog.present()


class App(Adw.Application):
    def __init__(
        self, proccesing_method: Callable[[MainWindow], None], config_path: Path
    ) -> None:
        super().__init__(application_id="com.example.GtkProcessingApp")
        self.processing_method: Callable[[MainWindow], None] = proccesing_method
        self.config_path = config_path

    def run_processing(self, window: MainWindow, _: object) -> None:
        self.processing_method(window)

    def do_activate(self) -> None:
        win: MainWindow = MainWindow(self)
        win.present()
