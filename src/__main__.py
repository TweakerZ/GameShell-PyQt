import sys

from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QFontDatabase, QPalette
from src.theme import Theme
from src.main_window import MainWindow


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("gameshell")

    for font_name in ["Rajdhani", "Exo 2"]:
        QFontDatabase.addApplicationFont(font_name)

    palette = QPalette()
    palette.setColor(QPalette.ColorRole.Window,      Theme.bg_deep)
    palette.setColor(QPalette.ColorRole.WindowText,  Theme.text_primary)
    palette.setColor(QPalette.ColorRole.Base,        Theme.bg_card)
    palette.setColor(QPalette.ColorRole.Text,        Theme.text_primary)
    palette.setColor(QPalette.ColorRole.Button,      Theme.bg_panel)
    palette.setColor(QPalette.ColorRole.ButtonText,  Theme.text_primary)
    palette.setColor(QPalette.ColorRole.Highlight,   Theme.accent)
    app.setPalette(palette)

    win = MainWindow()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()