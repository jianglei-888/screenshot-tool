"""Screenshot overlay window (T07 skeleton).

Minimal fullscreen semi-transparent dark window that closes on ESC.
No mouse handling, no selection drawing, no capture integration —
those are T08+.
"""
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QGuiApplication, QPainter
from PySide6.QtWidgets import QWidget

from src.logger import get_logger

log = get_logger(__name__)


class OverlayWindow(QWidget):
    """Fullscreen translucent dark overlay. Closes on ESC."""

    def __init__(self) -> None:
        super().__init__()
        self._setup_window()

    def _setup_window(self) -> None:
        flags = (
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool
        )
        self.setWindowFlags(flags)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)

        screen = QGuiApplication.primaryScreen()
        self.setGeometry(screen.virtualGeometry())

    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        painter.fillRect(self.rect(), QColor(0, 0, 0, 128))

    def keyPressEvent(self, event) -> None:
        if event.key() == Qt.Key.Key_Escape:
            log.info("Overlay closed by ESC")
            self.close()
        else:
            super().keyPressEvent(event)