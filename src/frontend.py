from pathlib import Path
from typing import Callable

from kivy.app import App
from kivy.graphics import Color, RoundedRectangle
from kivy.lang import Builder
from kivy.properties import StringProperty, NumericProperty
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from src.utils import AppError

DEFAULT_PDF_PATH: Path = Path("output.pdf")
DEFAULT_XLSX_PATH: Path = Path("output.xlsx")


# ================== FILE PICKER POPUP ==================
class FilePickerPopup(Popup):
    def __init__(self, callback: Callable[[Path], None], **kwargs) -> None:
        super().__init__(**kwargs)
        self._callback: Callable[[Path], None] = callback

    def select(self, selection: list[str]) -> None:
        if selection:
            self._callback(Path(selection[0]))
            self.dismiss()


# ================== GŁÓWNY WIDGET ==================
class MainWidget(BoxLayout):
    # --- wartości do UI (string) ---
    pdf_path_str = StringProperty(str(DEFAULT_PDF_PATH))
    xlsx_path_str = StringProperty(str(DEFAULT_XLSX_PATH))

    # --- wartości logiczne ---
    start_index = NumericProperty(0)

    # --- ścieżki logiczne ---
    pdf_path: Path = DEFAULT_PDF_PATH
    xlsx_path: Path = DEFAULT_XLSX_PATH

    # ---------- POPUPY ----------
    def _show_popup(self, title: str, text: str) -> None:
        content = Label(
            text=text,
            color=(0.1, 0.1, 0.1, 1),
            halign="left",
            valign="middle",
            padding=(20, 20),
        )

        popup = Popup(
            title=title,
            content=content,
            size_hint=(0.7, 0.5),
            background="",
        )

        with popup.canvas.before:
            Color(1, 1, 1, 1)
            popup.bg = RoundedRectangle(radius=[12])

        def _update_bg(*_):
            popup.bg.pos = popup.pos
            popup.bg.size = popup.size

        popup.bind(pos=_update_bg, size=_update_bg)
        popup.open()


    def show_info(self, text: str) -> None:
        self._show_popup("Informacja", text)

    def show_warning(self, text: str) -> None:
        self._show_popup("Ostrzeżenie", text)

    def show_error(self, text: str) -> None:
        self._show_popup("Błąd", text)

    # ---------- FILE PICKER ----------
    def open_file_picker(self, target: str) -> None:
        popup = FilePickerPopup(
            callback=lambda path: self._set_path(target, path),
            title="Wybierz plik",
            size_hint=(0.9, 0.9),
        )
        popup.open()

    def _set_path(self, target: str, path: Path) -> None:
        if target == "pdf":
            self.pdf_path = path
            self.pdf_path_str = str(path)
        elif target == "xlsx":
            self.xlsx_path = path
            self.xlsx_path_str = str(path)

    # ---------- GŁÓWNA LOGIKA ----------
    def run(self) -> None:
        try:
            self._validate_inputs()

            query: str = self.ids.query_input.text.strip()
            if not query:
                self.show_warning("Zapytanie jest puste")

            self._generate_files(query)

            self.show_info("Pliki PDF i Excel zostały wygenerowane poprawnie.")

        except AppError as exc:
            self.show_error(str(exc))

    # ---------- WALIDACJA ----------
    def _validate_inputs(self) -> None:
        if self.start_index < 0:
            raise AppError("Numer pola początkowego musi być dodatni.")

        if self.pdf_path.suffix.lower() != ".pdf":
            raise AppError("Plik wyjściowy PDF musi mieć rozszerzenie .pdf")

        if self.xlsx_path.suffix.lower() != ".xlsx":
            raise AppError("Plik wyjściowy Excel musi mieć rozszerzenie .xlsx")

    # ---------- PLACEHOLDER LOGIKI ----------
    def _generate_files(self, query: str) -> None:
        """
        Tu docelowo:
        - generowanie Excela
        - generowanie PDF
        """
        pass


class MyApp(App):
    def build(self) -> MainWidget:
        Builder.load_file("src/layout.kv")
        return MainWidget()
