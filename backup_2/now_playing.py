import pathlib

from PyQt6.QtWidgets import QDialog, QLabel, QVBoxLayout, QHBoxLayout, QFrame, QWidget
from PyQt6.QtGui import QFont, QPixmap, QCursor
from PyQt6.QtCore import Qt, pyqtSignal, QTimer
from .theme import Theme
from .config import get_absolute_path
from .widgets import StyledButton

class NowPlayingDialog(QDialog):
    kill_sig = pyqtSignal()

    def __init__(self, parent, game):
        super().__init__(parent)
        self.game = game
        self.setModal(False)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Dialog)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setFixedSize(800, 600)
        self._build()

        self._timer = QTimer(self)
        self._timer.timeout.connect(self._update_time)
        self._timer.start(1000)

    def _build(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)

        self.setStyleSheet("""
            QDialog {
                background-color: rgba(7, 10, 15, 0.85);
            }
        """)

        center_widget = QWidget()
        center_layout = QVBoxLayout(center_widget)
        center_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        outer.addWidget(center_widget, alignment=Qt.AlignmentFlag.AlignCenter)

        panel = QFrame()
        panel.setFixedWidth(600)
        panel.setStyleSheet(f"""
            QFrame {{
                background: {Theme.c(Theme.bg_panel)};
                border: 1px solid {Theme.c(Theme.border)};
                border-radius: 6px;
            }}
        """)
        center_layout.addWidget(panel)

        pl = QVBoxLayout(panel)
        pl.setContentsMargins(0, 0, 0, 0)
        pl.setSpacing(0)

        hero = QFrame()
        hero.setFixedHeight(160)
        hero.setStyleSheet("background: qlineargradient(x1:0,y1:0,x2:1,y2:1, stop:0 #0d1f1a, stop:1 #0a1a24); border-radius: 6px 6px 0 0;")
        hl = QHBoxLayout(hero)
        hl.setAlignment(Qt.AlignmentFlag.AlignCenter)

        if self.game.get('img'):
            import pathlib
            img_path = get_absolute_path(self.game['img'])
            if img_path and pathlib.Path(img_path).exists():
                pix = QPixmap(img_path)
                if not pix.isNull():
                    img_lbl = QLabel()
                    img_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
                    img_lbl.setPixmap(pix.scaled(130, 130,
                        Qt.AspectRatioMode.IgnoreAspectRatio,
                        Qt.TransformationMode.SmoothTransformation))
                    img_lbl.setStyleSheet("background: transparent;")
                    hl.addWidget(img_lbl)
                else:
                    em = QLabel(self.game.get('emoji','🎮'))
                    em.setFont(QFont("Segoe UI Emoji", 60))
                    hl.addWidget(em)
            else:
                em = QLabel(self.game.get('emoji','🎮'))
                em.setFont(QFont("Segoe UI Emoji", 60))
                hl.addWidget(em)
        else:
            em = QLabel(self.game.get('emoji','🎮'))
            em.setFont(QFont("Segoe UI Emoji", 60))
            hl.addWidget(em)
        pl.addWidget(hero)

        body = QWidget()
        bl = QVBoxLayout(body)
        bl.setContentsMargins(24, 16, 24, 24)
        bl.setSpacing(8)

        np_lbl = QLabel("● NOW PLAYING")
        np_lbl.setFont(QFont("Exo 2", 10, QFont.Weight.Bold))
        np_lbl.setStyleSheet(f"color: {Theme.c(Theme.green)}; letter-spacing: 2px;")
        bl.addWidget(np_lbl)

        name_lbl = QLabel(self.game['name'])
        name_lbl.setFont(QFont("Rajdhani", 24, QFont.Weight.Bold))
        name_lbl.setStyleSheet(f"color: {Theme.c(Theme.text_primary)};")
        bl.addWidget(name_lbl)

        self.timer_lbl = QLabel("00:00")
        self.timer_lbl.setFont(QFont("Rajdhani", 42, QFont.Weight.Bold))
        self.timer_lbl.setStyleSheet(f"color: {Theme.c(Theme.green)};")
        bl.addWidget(self.timer_lbl)

        acts = QHBoxLayout(); acts.setSpacing(10)
        close_btn = StyledButton("✕  Close Window")
        close_btn.clicked.connect(self.hide)

        kill_btn = StyledButton("⏹  Force Quit", danger=True)
        kill_btn.clicked.connect(self._kill)

        acts.addWidget(close_btn)
        acts.addWidget(kill_btn)
        bl.addLayout(acts)
        pl.addWidget(body)

    def _update_time(self):
        from .game_manager import game_mgr
        self.timer_lbl.setText(game_mgr.elapsed())

    def _kill(self):
        self.kill_sig.emit()
        self.hide()

    def show_centered(self, parent_rect):
        self.adjustSize()
        x = parent_rect.x() + (parent_rect.width() - self.width()) // 2
        y = parent_rect.y() + (parent_rect.height() - self.height()) // 2
        self.move(x, y)
        self.show()


class NowPlayingCard(QFrame):
    clicked_sig = pyqtSignal()

    def __init__(self, game_info: dict):
        super().__init__()
        self.game_info = game_info
        self.gid = "__nowplaying__"
        self._hovered = False
        self._focused = False
        self.setFixedWidth(148)
        self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self._build()

    def _build(self):
        t = Theme
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(0)

        art_container = QWidget()
        art_container.setFixedSize(132, 132)
        art_grid = QGridLayout(art_container)
        art_grid.setContentsMargins(0, 0, 0, 0)
        art_grid.setSpacing(0)

        art_lbl = QLabel()
        art_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        art_lbl.setFont(QFont("Segoe UI Emoji", 42))
        if self.game_info.get('img'):
            import pathlib
            img_path = get_absolute_path(self.game_info['img'])
            if img_path and pathlib.Path(img_path).exists():
                pix = QPixmap(img_path)
                if not pix.isNull():
                    art_lbl.setPixmap(pix.scaled(132, 132,
                        Qt.AspectRatioMode.KeepAspectRatioByExpanding,
                        Qt.TransformationMode.SmoothTransformation))
                else:
                    art_lbl.setText(self.game_info.get('emoji', '🎮'))
            else:
                art_lbl.setText(self.game_info.get('emoji', '🎮'))
        art_lbl.setStyleSheet("border-radius: 6px;")
        art_grid.addWidget(art_lbl, 0, 0, Qt.AlignmentFlag.AlignCenter)

        overlay = QLabel("▶  Now Playing")
        overlay.setFont(QFont("Exo 2", 8, QFont.Weight.Bold))
        overlay.setStyleSheet("""
            color: #000;
            background: #00d4aa;
            border-radius: 6px;
            padding: 2px 8px;
            letter-spacing: 1px;
        """)
        overlay.setFixedHeight(20)
        overlay.setAlignment(Qt.AlignmentFlag.AlignCenter)
        art_grid.addWidget(overlay, 0, 0, Qt.AlignmentFlag.AlignCenter)

        self.tint_overlay = QWidget(art_container)
        self.tint_overlay.setGeometry(0, 0, 132, 132)
        self.tint_overlay.setStyleSheet("background: rgba(0, 212, 170, 0.25); border-radius: 6px;")
        self.tint_overlay.hide()

        layout.addWidget(art_container)

        info = QFrame()
        info.setFixedHeight(48)
        il = QVBoxLayout(info)
        il.setContentsMargins(2, 4, 2, 2)
        il.setSpacing(2)

        name = self.game_info.get("name", "")
        title = QLabel(name)
        title.setFont(QFont("Exo 2", 11, QFont.Weight.Medium))
        title.setStyleSheet(f"color: {Theme.c(Theme.text_primary)};")
        fm = title.fontMetrics()
        title.setText(fm.elidedText(name, Qt.TextElideMode.ElideRight, 130))
        il.addWidget(title)

        self.timer_lbl = QLabel("00:00")
        self.timer_lbl.setFont(QFont("Rajdhani", 11))
        self.timer_lbl.setStyleSheet(f"color: {Theme.c(Theme.green)};")
        il.addWidget(self.timer_lbl)
        layout.addWidget(info)
        self._refresh_style()

    def update_time(self, elapsed: str):
        if hasattr(self, "timer_lbl"):
            self.timer_lbl.setText(elapsed)

    def _refresh_style(self):
        t = Theme
        self.tint_overlay.setVisible(self._hovered or self._focused)
        self.setStyleSheet(f"""
            NowPlayingCard {{
                background: qlineargradient(x1:0,y1:0,x2:0,y2:1,
                    stop:0 {t.c(t.bg_card_hover)}, stop:1 rgba(20,20,20,0.8));
                border-radius: 6px;
            }}
        """)

    def enterEvent(self, event):   self._hovered=True;  self._refresh_style()
    def leaveEvent(self, a0):   self._hovered=False; self._refresh_style()
    def focusInEvent(self, a0):   self._focused=True;  self._refresh_style()
    def focusOutEvent(self, a0):  self._focused=False; self._refresh_style()
    def mousePressEvent(self, a0):
        if a0 and a0.button() == Qt.MouseButton.LeftButton:
            self.clicked_sig.emit()
    def keyPressEvent(self, a0):
        if a0 and a0.key() in (Qt.Key.Key_Return, Qt.Key.Key_Space):
            self.clicked_sig.emit()
        else:
            super().keyPressEvent(a0)


from PyQt6.QtWidgets import QGridLayout