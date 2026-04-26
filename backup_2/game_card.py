import pathlib

from PyQt6.QtWidgets import QFrame, QLabel, QVBoxLayout
from PyQt6.QtGui import QFont, QPainter, QColor, QCursor, QPixmap
from PyQt6.QtCore import Qt, pyqtSignal
from .theme import Theme
from .config import get_absolute_path
from .widgets import EMOJIS

class GameCard(QFrame):
    clicked_sig = pyqtSignal(str)

    def __init__(self, game: dict):
        super().__init__()

        if game is None:
            game = {
                'id': 'placeholder',
                'name': 'Unknown Game',
                'type': 'custom',
                'emoji': '🎮'
            }

        self.game = game
        self.gid  = game['id']
        self._hovered  = False
        self._focused  = False
        self.setFixedWidth(148)
        self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self._build()

    def _build(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(0)

        self.art = QLabel()
        self.art.setFixedSize(132, 132)
        self.art.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.art.setFont(QFont("Segoe UI Emoji", 42))
        self.art.setStyleSheet("border-radius: 6px; background: rgba(0,0,0,0.3);")

        if self.game.get('img'):
            img_path = get_absolute_path(self.game['img'])
            if img_path and pathlib.Path(img_path).exists():
                pix = QPixmap(img_path)
                if not pix.isNull():
                    self.art.setPixmap(pix.scaled(132, 132,
                        Qt.AspectRatioMode.KeepAspectRatioByExpanding,
                        Qt.TransformationMode.SmoothTransformation))
                else:
                    self.art.setText(self.game.get('emoji', '🎮'))
            else:
                self.art.setText(self.game.get('emoji', '🎮'))
        else:
            self.art.setText(self.game.get('emoji', '🎮'))

        layout.addWidget(self.art)

        info = QFrame()
        info.setFixedHeight(48)
        il = QVBoxLayout(info)
        il.setContentsMargins(2, 4, 2, 2)
        il.setSpacing(2)

        title = QLabel(self.game.get('name', ''))
        title.setFont(QFont("Exo 2", 11, QFont.Weight.Medium))
        title.setStyleSheet(f"color: {Theme.c(Theme.text_primary)};")
        title.setWordWrap(False)
        fm = title.fontMetrics()
        title.setText(fm.elidedText(self.game.get('name',''), Qt.TextElideMode.ElideRight, 130))
        il.addWidget(title)

        layout.addWidget(info)
        self._refresh_style()

    def _refresh_style(self):
        t = Theme

        if self._hovered or self._focused:
            self.setStyleSheet(f"""
                GameCard {{
                    background: {t.c(t.bg_card_hover)};
                    border: 1px solid rgba(255, 255, 255, 0.1);
                    border-radius: 6px;
                }}
            """)
        else:
            self.setStyleSheet(f"""
                GameCard {{
                    background: {t.c(t.bg_card)};
                    border: 1px solid rgba(255, 255, 255, 0.06);
                    border-radius: 6px;
                }}
            """)

    def enterEvent(self, event):
        self._hovered = True;  self._refresh_style()

    def leaveEvent(self, a0):
        self._hovered = False; self._refresh_style()

    def focusInEvent(self, a0):
        self._focused = True;  self._refresh_style()

    def focusOutEvent(self, a0):
        self._focused = False; self._refresh_style()

    def mousePressEvent(self, a0):
        if a0 and a0.button() == Qt.MouseButton.LeftButton:
            self.clicked_sig.emit(self.gid)

    def keyPressEvent(self, a0):
        if a0 and a0.key() in (Qt.Key.Key_Return, Qt.Key.Key_Space):
            self.clicked_sig.emit(self.gid)
        else:
            super().keyPressEvent(a0)

    def paintEvent(self, a0):
        super().paintEvent(a0)
        if self._hovered or self._focused:
            p = QPainter(self)
            p.setRenderHint(QPainter.RenderHint.Antialiasing)
            accent = Theme.accent
            glow = QColor(accent.red(), accent.green(), accent.blue(), 40)
            p.setBrush(glow)
            p.setPen(Qt.PenStyle.NoPen)
            p.drawRoundedRect(self.rect().adjusted(1, 1, -1, -1), 6, 6)


from PyQt6.QtGui import QPixmap, QDragEnterEvent, QDropEvent
from PyQt6.QtCore import QMimeType, QMimeData

class DropDesktopCard(QFrame):
    clicked_sig = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self.setFixedWidth(148)
        self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self._hovered = False
        self._focused = False
        self._build()

    def _build(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(0)

        self.art = QLabel("📁")
        self.art.setFixedSize(132, 132)
        self.art.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.art.setFont(QFont("Segoe UI Emoji", 42))
        self.art.setStyleSheet("border-radius: 6px; background: rgba(0,0,0,0.3);")
        layout.addWidget(self.art)

        info = QFrame()
        info.setFixedHeight(48)
        il = QVBoxLayout(info)
        il.setContentsMargins(2, 4, 2, 2)
        il.setSpacing(2)

        title = QLabel("Drop Desktop")
        title.setFont(QFont("Exo 2", 11, QFont.Weight.Medium))
        title.setStyleSheet(f"color: {Theme.c(Theme.text_primary)};")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        fm = title.fontMetrics()
        title.setText(fm.elidedText("Drop Desktop", Qt.TextElideMode.ElideRight, 130))
        il.addWidget(title)

        layout.addWidget(info)
        self.setAcceptDrops(True)
        self._refresh_style()

    def _refresh_style(self):
        t = Theme
        if self._hovered or self._focused:
            self.setStyleSheet(f"""
                QFrame {{
                    background: {t.c(t.bg_card_hover)};
                    border: 2px dashed {t.c(t.accent)};
                    border-radius: 6px;
                }}
            """)
        else:
            self.setStyleSheet(f"""
                QFrame {{
                    background: {t.c(t.bg_card)};
                    border: 2px dashed {t.c(t.border)};
                    border-radius: 6px;
                }}
            """)

    def enterEvent(self, event):
        self._hovered = True
        self._refresh_style()

    def leaveEvent(self, event):
        self._hovered = False
        self._refresh_style()

    def focusInEvent(self, event):
        self._focused = True
        self._refresh_style()

    def focusOutEvent(self, event):
        self._focused = False
        self._refresh_style()

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
            self._hovered = True
            self._refresh_style()

    def dragLeaveEvent(self, event):
        self._hovered = False
        self._refresh_style()

    def dropEvent(self, event):
        self._hovered = False
        self._refresh_style()
        urls = event.mimeData().urls()
        for url in urls:
            if url.isLocalFile():
                path = url.toLocalFile()
                if path.endswith('.desktop'):
                    self.clicked_sig.emit(path)
                    return
