"""Icon loading utility for Feather SVG icons."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from PySide6.QtCore import QSize
from PySide6.QtGui import QIcon, QPixmap
from PySide6.QtSvg import QSvgRenderer
from PySide6.QtGui import QPainter, QColor, QImage

# Feather icons are at reference/logo/feather-icons/ relative to project root.
# At runtime we resolve from the package location.
_PROJECT_ROOT = Path(__file__).parent.parent.parent.parent
_ICON_DIR = _PROJECT_ROOT / "reference" / "logo" / "feather-icons"


@lru_cache(maxsize=256)
def feather_icon(name: str, color: str = "#2D3E50", size: int = 18) -> QIcon:
    """Load a Feather SVG icon, recoloured to the given hex colour.

    Args:
        name: Icon name without extension, e.g. "file", "play", "save".
        color: Hex colour string to tint the icon.
        size: Pixel size (square).

    Returns:
        QIcon ready for use in toolbars, buttons, tree items, etc.
    """
    svg_path = _ICON_DIR / f"{name}.svg"
    if not svg_path.exists():
        return QIcon()

    # Read SVG and replace the stroke colour
    svg_content = svg_path.read_text(encoding="utf-8")
    # Feather icons use stroke="currentColor" — replace with our colour
    svg_content = svg_content.replace('stroke="currentColor"', f'stroke="{color}"')

    # Render to QPixmap
    renderer = QSvgRenderer(svg_content.encode("utf-8"))
    image = QImage(QSize(size, size), QImage.Format.Format_ARGB32_Premultiplied)
    image.fill(QColor(0, 0, 0, 0))

    painter = QPainter(image)
    renderer.render(painter)
    painter.end()

    pixmap = QPixmap.fromImage(image)
    return QIcon(pixmap)
