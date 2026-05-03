"""Quantia entry point.

Usage:
    python -m quantia
    quantia  (if installed via pip)
"""

from __future__ import annotations

import sys


def main() -> int:
    """Launch the Quantia application."""
    from quantia.app import QuantiaApp
    from quantia.theme.palette import Theme
    from quantia.ui.main_window import MainWindow
    from PySide6.QtGui import QFontDatabase
    from quantia.utils.resources import resource_path

    app = QuantiaApp(sys.argv)
    
    # Register bundled fonts
    fonts_dir = resource_path("reference/fonts")
    if fonts_dir.exists():
        for font_file in fonts_dir.glob("*.ttf"):
            QFontDatabase.addApplicationFont(str(font_file))
        for font_file in fonts_dir.glob("*.otf"):
            QFontDatabase.addApplicationFont(str(font_file))

    app.apply_theme(Theme.LIGHT)

    window = MainWindow()
    window.show()

    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
