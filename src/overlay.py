"""Screenshot overlay window (T07 + T08).

T07: Fullscreen semi-transparent dark overlay, closes on ESC.
T08: Mouse drag selection — left-click starts, drag updates, release
finalizes. Selection rectangle drawn with cut-out effect (transparent
inside, dark outside).

T08 does NOT include: confirm/cancel (T09), capture (T10),
clipboard/saver integration (T11).
"""
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QGuiApplication, QPainter, QPen
from PySide6.QtWidgets import QWidget

from src import selection
from src.logger import get_logger

log = get_logger(__name__)


class OverlayWindow(QWidget):
    """Fullscreen translucent dark overlay with drag selection."""

    def __init__(self) -> None:
        super().__init__()
        self._start = None
        self._end = None
        self._is_dragging = False
        self._setup_window()

    def _setup_window(self) -> None:
        flags = (
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool
        )
        self.setWindowFlags(flags)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setCursor(Qt.CursorShape.CrossCursor)

        screen = QGuiApplication.primaryScreen()
        self.setGeometry(screen.virtualGeometry())

    def paintEvent(self, event) -> None:
        painter = QPainter(self)

        if self._start is None:
            painter.fillRect(self.rect(), QColor(0, 0, 0, 128))
            return

        x, y, w, h = selection.normalize(
            (self._start.x(), self._start.y()),
            (self._end.x(), self._end.y()),
        )

        if w <= 0 or h <= 0:
            painter.fillRect(self.rect(), QColor(0, 0, 0, 128))
            return

        # Cut-out: draw dark overlay in 4 strips around the selection,
        # leaving the selection interior transparent.
        painter.fillRect(0, 0, self.width(), y, QColor(0, 0, 0, 128))
        painter.fillRect(0, y + h, self.width(),
                         self.height() - y - h, QColor(0, 0, 0, 128))
        painter.fillRect(0, y, x, h, QColor(0, 0, 0, 128))
        painter.fillRect(x + w, y, self.width() - x - w, h,
                         QColor(0, 0, 0, 128))

        # Selection border
        painter.setPen(QPen(QColor(255, 255, 255, 200), 1))
        painter.drawRect(x, y, w, h)

    def mousePressEvent(self, event) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            self._start = event.position().toPoint()
            self._end = self._start
            self._is_dragging = True
            self.update()

    def mouseMoveEvent(self, event) -> None:
        if self._is_dragging:
            self._end = event.position().toPoint()
            self.update()

    def mouseReleaseEvent(self, event) -> None:
        if event.button() == Qt.MouseButton.LeftButton and self._is_dragging:
            self._end = event.position().toPoint()
            self._is_dragging = False
            self.update()

    def keyPressEvent(self, event) -> None:
        if event.key() == Qt.Key.Key_Escape:
            log.info("Overlay closed by ESC")
            self.close()
        else:
            super().keyPressEvent(event)

    def get_selection_rect(self) -> tuple[int, int, int, int] | None:
        """Return normalized selection rectangle.

        Returns:
            (x, y, width, height) in TL-origin form, or None if no
            drag has started yet.
        """
        if self._start is None or self._end is None:
            return None
        return selection.normalize(
            (self._start.x(), self._start.y()),
            (self._end.x(), self._end.y()),
        )