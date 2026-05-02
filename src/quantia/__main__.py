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

    app = QuantiaApp(sys.argv)
    app.apply_theme(Theme.LIGHT)

    window = MainWindow()
    window.show()

    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
