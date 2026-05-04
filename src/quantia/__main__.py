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
    from PySide6.QtGui import QFontDatabase, QPixmap
    from PySide6.QtWidgets import QSplashScreen
    from PySide6.QtCore import Qt, QElapsedTimer
    from quantia.utils.resources import resource_path

    app = QuantiaApp(sys.argv)
    
    # Start timer to track splash duration
    startup_timer = QElapsedTimer()
    startup_timer.start()
    
    # Create and show splash screen
    logo_path = resource_path("reference/logo/Quantia_logo.png")
    pixmap = QPixmap(str(logo_path))
    # Scale if necessary, e.g., to width of 400px
    if not pixmap.isNull():
        pixmap = pixmap.scaledToWidth(400, Qt.SmoothTransformation)
    
    splash = QSplashScreen(pixmap)
    splash.show()
    app.processEvents()

    # Register bundled fonts
    splash.showMessage("Loading fonts...", Qt.AlignBottom | Qt.AlignCenter, Qt.white)
    app.processEvents()
    
    fonts_dir = resource_path("reference/fonts")
    if fonts_dir.exists():
        for font_file in fonts_dir.glob("*.ttf"):
            QFontDatabase.addApplicationFont(str(font_file))
        for font_file in fonts_dir.glob("*.otf"):
            QFontDatabase.addApplicationFont(str(font_file))

    splash.showMessage("Applying theme...", Qt.AlignBottom | Qt.AlignCenter, Qt.white)
    app.processEvents()
    app.apply_theme(Theme.LIGHT)

    splash.showMessage("Initializing UI...", Qt.AlignBottom | Qt.AlignCenter, Qt.white)
    app.processEvents()
    window = MainWindow()
    window.show()
    
    # Ensure splash screen stays for at least 3 seconds (3000 ms)
    while startup_timer.elapsed() < 3000:
        app.processEvents()

    splash.finish(window)

    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
