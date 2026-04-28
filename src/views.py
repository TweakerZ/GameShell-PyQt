from PyQt6.QtWidgets import (
    QScrollArea, QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QPushButton, QFrame, QSizePolicy
)
from PyQt6.QtGui import QFont, QCursor
from PyQt6.QtCore import Qt, pyqtSignal, QTimer
from datetime import datetime
from .theme import Theme
from .game_card import GameCard
from .now_playing import NowPlayingCard
from .widgets import StyledButton


class GameGrid(QScrollArea):
    card_clicked = pyqtSignal(str)
    card_right_clicked = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self.setWidgetResizable(True)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setStyleSheet("QScrollArea { border: none; background: transparent; } QScrollBar:vertical, QScrollBar:horizontal { border: none; background: transparent; }")

        self._container = QWidget()
        self._container.setStyleSheet("background: transparent;")
        self._grid = QGridLayout(self._container)
        self._grid.setSpacing(14)
        self._grid.setContentsMargins(0, 0, 0, 0)
        self._grid.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignCenter)
        self.setWidget(self._container)

        self._cards = []
        self._focused_idx = -1

    def set_games(self, games, cols=6, show_add=False, show_row_header=None):
        while self._grid.count():
            item = self._grid.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        self._cards = []
        self._focused_idx = -1

        row = 0; col = 0

        def next_cell():
            nonlocal row, col
            if col >= cols:
                col = 0; row += 1

        def maybe_header(idx):
            nonlocal row, col
            if show_row_header and idx == show_row_header[0]:
                if col > 0:
                    col = 0; row += 1
                hdr = QLabel(show_row_header[1])
                hdr.setFont(QFont("Rajdhani", 14, QFont.Weight.Bold))
                hdr.setStyleSheet(f"""
                    color: {Theme.c(Theme.text_secondary)};
                    border-top: 1px solid {Theme.c(Theme.border)};
                    padding-top: 10px; letter-spacing: 1px;
                """)
                self._grid.addWidget(hdr, row, 0, 1, cols)
                row += 1

        for i, g in enumerate(games):
            maybe_header(i)
            next_cell()
            card = GameCard(g)
            card.clicked_sig.connect(self.card_clicked)
            card.right_clicked_sig.connect(self.card_right_clicked)
            self._grid.addWidget(card, row, col)
            self._cards.append(card)
            col += 1

        if show_add:
            next_cell()
            add = self._make_add_card()
            self._grid.addWidget(add, row, col)
            col += 1

    def _make_add_card(self):
        btn = QFrame()
        btn.setFixedWidth(148)
        btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        btn.setStyleSheet(f"""
            QFrame {{
                background: transparent;
                border: 2px dashed {Theme.c(Theme.border)};
                border-radius: 6px;
            }}
            QFrame:hover {{
                border-color: {Theme.c(Theme.accent)};
                background: rgba(26,159,255,0.05);
            }}
        """)
        btn.setFixedHeight(206)
        bl = QVBoxLayout(btn)
        bl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon = QLabel("➕")
        icon.setFont(QFont("Segoe UI Emoji", 28))
        icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl = QLabel("Add Game")
        lbl.setFont(QFont("Exo 2", 11))
        lbl.setStyleSheet(f"color: {Theme.c(Theme.text_dim)};")
        lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        bl.addWidget(icon); bl.addWidget(lbl)
        btn.mousePressEvent = lambda a0: self.card_clicked.emit("__add__")
        return btn

    def focus_card(self, idx):
        if 0 <= self._focused_idx < len(self._cards):
            self._cards[self._focused_idx]._focused = False
            self._cards[self._focused_idx]._refresh_style()
        self._focused_idx = max(0, min(idx, len(self._cards)-1))
        if self._cards:
            c = self._cards[self._focused_idx]
            c._focused = True
            c._refresh_style()
            c.setFocus()
            self.ensureWidgetVisible(c)

    def activate_focused(self):
        if 0 <= self._focused_idx < len(self._cards):
            self._cards[self._focused_idx].clicked_sig.emit(
                self._cards[self._focused_idx].gid)

    def right_click_focused(self):
        card = self._focused_idx
        if 0 <= card < len(self._cards):
            gid = self._cards[card].gid
            if gid and not gid.startswith('__'):
                self.card_right_clicked.emit(gid)

    def get_cols(self):
        if not self._cards:
            return 6
        if self._grid.count() == 0:
            return 6
        cols = 0
        for i in range(self._grid.count()):
            item = self._grid.itemAt(i)
            if item:
                r, c, _, _ = self._grid.getItemPosition(i)
                if r == 0:
                    cols = max(cols, c + 1)
        return max(1, cols)

    def nav_up(self):
        cols = self.get_cols()
        new = self._focused_idx - cols
        if new >= 0:
            self.focus_card(new)

    def nav_down(self):
        cols = self.get_cols()
        new = self._focused_idx + cols
        if new < len(self._cards):
            self.focus_card(new)

    def nav_left(self):
        if self._focused_idx > 0:
            self.focus_card(self._focused_idx - 1)
            return True
        return False

    def nav_right(self):
        if self._focused_idx < len(self._cards) - 1:
            self.focus_card(self._focused_idx + 1)


class TopNavBar(QFrame):
    view_changed   = pyqtSignal(str)
    add_game       = pyqtSignal()
    import_desktop = pyqtSignal()
    np_clicked     = pyqtSignal()
    power_off      = pyqtSignal()

    VIEWS = [
        ("🏠", "Home",      "home"),
        ("🎮", "All Games", "library"),
        ("🕐", "Recent",    "recent"),
        ("⭐", "Favorites", "favorites"),
        ("⚙️", "Settings",  "settings"),
    ]

    def __init__(self):
        super().__init__()
        self.setFixedHeight(56)
        self._nav_btns = []
        self._focused_idx = 0
        self._build()
        self._clock_timer = QTimer(self)
        self._clock_timer.timeout.connect(self._update_clock)
        self._clock_timer.start(10000)
        self._update_clock()

    def _build(self):
        t = Theme
        self.setStyleSheet(f"""
            TopNavBar {{
                background: {t.c(t.bg_panel)};
                border-bottom: 1px solid {t.c(t.border)};
            }}
        """)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        left_container = QWidget()
        left_layout = QHBoxLayout(left_container)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(0)
        left_layout.setAlignment(Qt.AlignmentFlag.AlignVCenter)
        logo = QLabel("⬡  GameShell")
        logo.setFont(QFont("Rajdhani", 18, QFont.Weight.Bold))
        logo.setStyleSheet(f"color: {t.c(t.accent)}; padding-right: 12px;")
        left_layout.addWidget(logo)
        self.clock = QLabel("00:00")
        self.clock.setFont(QFont("Rajdhani", 16))
        self.clock.setStyleSheet(f"color: {t.c(t.text_secondary)}; padding-right: 20px;")
        left_layout.addWidget(self.clock)

        center_container = QWidget()
        center_layout = QHBoxLayout(center_container)
        center_layout.setContentsMargins(0, 0, 0, 0)
        center_layout.setSpacing(0)
        center_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        for icon, name, view in self.VIEWS:
            btn = QPushButton(name)
            btn.setFont(QFont("Exo 2", 11))
            btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
            btn.setCheckable(True)
            btn.setFixedHeight(32)
            btn.setFixedWidth(120)
            btn.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
            btn._view = view
            btn.clicked.connect(lambda _, v=view: self.view_changed.emit(v))
            self._nav_btns.append(btn)
            self._style_tab(btn, False)
            center_layout.addWidget(btn)

        right_container = QWidget()
        right_layout = QHBoxLayout(right_container)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(0)
        right_layout.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)

        self.add_btn = self._icon_action_btn("➕")
        self.add_btn.clicked.connect(self.add_game)
        right_layout.addWidget(self.add_btn)

        right_layout.addSpacing(10)

        self.imp_btn = self._icon_action_btn("📂")
        self.imp_btn.clicked.connect(self.import_desktop)
        right_layout.addWidget(self.imp_btn)

        right_layout.addSpacing(10)

        self.close_btn = self._action_btn("❌")
        self.close_btn.clicked.connect(self.power_off)
        t = Theme
        self.close_btn.setStyleSheet(f"""
            QPushButton {{
                background: rgba(255,68,102,0.12);
                color: {t.c(t.red)};
                border: 1px solid rgba(255,68,102,0.3);
                border-radius: 6px;
                padding: 0 12px;
                margin: 0 3px;
            }}
            QPushButton:hover {{
                background: rgba(255,68,102,0.22);
                color: {t.c(t.red)};
                border-color: {t.c(t.red)};
            }}
        """)
        right_layout.addWidget(self.close_btn)

        right_layout.addSpacing(10)

        left_hint = left_container.sizeHint()
        right_hint = right_container.sizeHint()
        max_side_width = max(left_hint.width(), right_hint.width())
        left_container.setMinimumWidth(max_side_width)
        right_container.setMinimumWidth(max_side_width)

        left_container.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        right_container.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        center_container.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)

        layout.addWidget(left_container, stretch=1)
        layout.addWidget(center_container, stretch=0)
        layout.addWidget(right_container, stretch=1)

    def _action_btn(self, text):
        t = Theme
        btn = QPushButton(text)
        btn.setFont(QFont("Exo 2", 11))
        btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        btn.setFixedHeight(32)
        btn.setFixedWidth(50)
        btn.setStyleSheet(f"""
            QPushButton {{
                background: rgba(255,255,255,0.04);
                color: {t.c(t.text_secondary)};
                border: 1px solid {t.c(t.border)};
                border-radius: 6px;
                padding: 0 12px;
                margin: 0 3px;
            }}
            QPushButton:hover {{
                background: rgba(255,255,255,0.08);
                color: {t.c(t.text_primary)};
            }}
        """)
        return btn

    def _icon_action_btn(self, icon):
        t = Theme
        btn = QPushButton(icon)
        btn.setFont(QFont("Exo 2", 14))
        btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        btn.setFixedHeight(32)
        btn.setFixedWidth(50)
        btn.setStyleSheet(f"""
            QPushButton {{
                background: rgba(255,255,255,0.04);
                color: {t.c(t.text_secondary)};
                border: 1px solid {t.c(t.border)};
                border-radius: 6px;
                padding: 0;
                margin: 0 3px;
            }}
            QPushButton:hover {{
                background: rgba(255,255,255,0.08);
                color: {t.c(t.text_primary)};
            }}
        """)
        return btn

    def _style_tab(self, btn, active):
        t = Theme
        if active:
            btn.setStyleSheet(f"""
                QPushButton {{
                    background: {t.c(t.accent)};
                    color: white;
                    border: none;
                    border-radius: 6px;
                    padding: 0 16px;
                    margin: 0 2px;
                    font-weight: bold;
                }}
                QPushButton:hover {{
                    background: {t.c(t.accent.lighter(110))};
                }}
            """)
        else:
            btn.setStyleSheet(f"""
                QPushButton {{
                    background: transparent;
                    color: {t.c(t.text_secondary)};
                    border: none;
                    border-radius: 6px;
                    padding: 0 16px;
                    margin: 0 2px;
                }}
                QPushButton:hover {{
                    background: rgba(255,255,255,0.06);
                    color: {t.c(t.text_primary)};
                }}
            """)

    def set_active(self, view_name):
        for btn in self._nav_btns:
            active = btn._view == view_name
            btn.setChecked(active)
            self._style_tab(btn, active)

    def focus_tab(self, idx):
        idx = max(0, min(idx, len(self._nav_btns) - 1))
        self._focused_idx = idx
        self._nav_btns[idx].setFocus()

    def activate_focused(self):
        self._nav_btns[self._focused_idx].click()

    def _update_clock(self):
        self.clock.setText(datetime.now().strftime("%H:%M"))

    def set_now_playing(self, name, elapsed):
        self._np_name = name or ""
        self._np_elapsed = elapsed or ""

    def refresh_styles(self):
        t = Theme
        self.setStyleSheet(f"""
            TopNavBar {{
                background: {t.c(t.bg_panel)};
                border-bottom: 1px solid {t.c(t.border)};
            }}
        """)
        self.clock.setStyleSheet(f"color: {t.c(t.text_secondary)}; padding-right: 20px;")
        for btn in self._nav_btns:
            self._style_tab(btn, btn.isChecked())
        
        self.add_btn.setStyleSheet(f"""
            QPushButton {{
                background: rgba(255,255,255,0.04);
                color: {t.c(t.text_secondary)};
                border: 1px solid {t.c(t.border)};
                border-radius: 6px;
                padding: 0;
            }}
            QPushButton:hover {{
                background: rgba(255,255,255,0.08);
                color: {t.c(t.text_primary)};
            }}
        """)
        self.imp_btn.setStyleSheet(f"""
            QPushButton {{
                background: rgba(255,255,255,0.04);
                color: {t.c(t.text_secondary)};
                border: 1px solid {t.c(t.border)};
                border-radius: 6px;
                padding: 0;
            }}
            QPushButton:hover {{
                background: rgba(255,255,255,0.08);
                color: {t.c(t.text_primary)};
            }}
        """)
        self.close_btn.setStyleSheet(f"""
            QPushButton {{
                background: rgba(255,68,102,0.12);
                color: {t.c(t.red)};
                border: 1px solid rgba(255,68,102,0.3);
                border-radius: 6px;
                padding: 0 12px;
                margin: 0 3px;
            }}
            QPushButton:hover {{
                background: rgba(255,68,102,0.22);
                color: {t.c(t.red)};
                border-color: {t.c(t.red)};
            }}
        """)


class SettingsView(QWidget):
    hue_changed = pyqtSignal(int)

    def __init__(self):
        super().__init__()
        self.setStyleSheet("background: transparent;")
        self._build()

    def _build(self):
        t = Theme
        outer_layout = QVBoxLayout(self)
        outer_layout.setContentsMargins(32, 28, 32, 32)
        outer_layout.setSpacing(16)

        hdr = QHBoxLayout()
        hdr.setContentsMargins(0, 0, 0, 0)
        hdr.setSpacing(0)

        hdr.addStretch()

        self.title_lbl = QLabel("Settings")
        self.title_lbl.setFont(QFont("Rajdhani", 22, QFont.Weight.Bold))
        self.title_lbl.setStyleSheet(f"color: {t.c(t.text_primary)};")
        self.title_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        hdr.addWidget(self.title_lbl)

        hdr.addStretch()

        outer_layout.addLayout(hdr)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setStyleSheet("QScrollArea { border: none; background: transparent; } QScrollBar:vertical, QScrollBar:horizontal { border: none; background: transparent; }")

        inner = QWidget()
        inner.setStyleSheet("background: transparent;")

        content_outer = QHBoxLayout(inner)
        content_outer.setContentsMargins(0, 0, 0, 0)
        content_outer.addStretch()

        col = QWidget()
        col.setFixedWidth(540)
        content_layout = QVBoxLayout(col)
        content_layout.setContentsMargins(0, 0, 0, 40)
        content_layout.setSpacing(0)
        content_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        content_outer.addWidget(col)
        content_outer.addStretch()

        def section(text):
            lbl = QLabel(text.upper())
            lbl.setFont(QFont("Exo 2", 10, QFont.Weight.Bold))
            lbl.setStyleSheet(f"""
                color: {t.c(t.text_secondary)};
                letter-spacing: 3px;
                padding: 20px 0 12px;
            """)
            content_layout.addWidget(lbl)

        def row_lbl(text, dim=False):
            l = QLabel(text)
            l.setFont(QFont("Exo 2", 12))
            l.setStyleSheet(f"color: {t.c(t.text_dim if dim else t.text_secondary)};")
            return l

        section("UI Theme")

        accent_lbl = QLabel("Accent Colour")
        accent_lbl.setFont(QFont("Exo 2", 12))
        accent_lbl.setStyleSheet(f"color: {t.c(t.text_secondary)}; padding: 4px 0 8px;")
        content_layout.addWidget(accent_lbl)

        palette_grid = QGridLayout()
        palette_grid.setSpacing(8)
        PALETTE_HUES = [0, 30, 60, 90, 120, 150, 180, 210, 240, 270, 300, 330]
        self.palette_buttons = []
        for i, hue in enumerate(PALETTE_HUES):
            btn = QPushButton()
            btn.setFixedSize(36, 36)
            btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
            base_color = Theme.hsl(hue, 80, 55)
            btn.setStyleSheet(f"""
                QPushButton {{
                    background: {base_color.name()};
                    border: none;
                    border-radius: 6px;
                }}
                QPushButton:hover {{
                    background: {base_color.lighter(115).name()};
                }}
            """)
            btn.clicked.connect(lambda checked, h=hue: self.hue_changed.emit(h))
            palette_grid.addWidget(btn, i // 6, i % 6)
            self.palette_buttons.append((btn, hue))

        swatch_row = QHBoxLayout()
        swatch_row.setSpacing(10)
        self.hue_swatch = QLabel()
        self.hue_swatch.setFixedSize(36, 36)
        self.hue_swatch.setStyleSheet(f"background: {Theme.c(Theme.accent)}; border-radius: 6px;")
        swatch_row.addWidget(self.hue_swatch)

        self.reset_btn = QPushButton("Reset")
        self.reset_btn.setFont(QFont("Exo 2", 11))
        self.reset_btn.setFixedSize(64, 36)
        self.reset_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.reset_btn.setStyleSheet(f"""
            QPushButton {{
                background: {t.c(t.bg_card)};
                color: {t.c(t.text_secondary)};
                border: none;
                border-radius: 6px;
            }}
            QPushButton:hover {{
                background: {t.c(t.bg_card_hover)};
                color: {t.c(t.text_primary)};
            }}
        """)
        self.reset_btn.clicked.connect(lambda: self.hue_changed.emit(207))
        swatch_row.addWidget(self.reset_btn)

        container = QHBoxLayout()
        container.setSpacing(20)
        container.addLayout(palette_grid)
        container.addStretch()
        container.addLayout(swatch_row)
        content_layout.addLayout(container)

        hint = QLabel("Select a color preset. Saved automatically.")
        hint.setFont(QFont("Exo 2", 11))
        hint.setStyleSheet(f"color: {t.c(t.text_dim)}; padding: 6px 0 4px;")
        content_layout.addWidget(hint)

        self.update_swatch(Theme.accent)

        from .config import LIBRARY_FILE
        section("Data Storage")
        storage = QLabel(f"Library saved to:  {LIBRARY_FILE}")
        storage.setFont(QFont("Exo 2", 12))
        storage.setStyleSheet(f"color: {t.c(t.text_secondary)};")
        storage.setWordWrap(True)
        content_layout.addWidget(storage)

        section("Credits")
        credits_frame = QFrame()
        credits_frame.setStyleSheet(f"""
            QFrame {{
                background: {t.c(t.bg_card)};
                border: 1px solid {t.c(t.border)};
                border-radius: 6px;
            }}
        """)
        cl = QVBoxLayout(credits_frame)
        cl.setContentsMargins(20, 16, 20, 16)
        cl.setSpacing(14)

        for role_icon, name, role in [
            ("[AI]",  "Claude (Anthropic)", "UI design, logic & development"),
            ("[AI]",  "big-pickle (opencode)", "UI styling & refinements"),
            ("[DEV]", "Ogochukwu Odumodu",  "Creator, vision & direction"),
        ]:
            row = QHBoxLayout()
            row.setSpacing(14)

            badge = QLabel(role_icon)
            badge.setFont(QFont("Exo 2", 10, QFont.Weight.Bold))
            badge.setFixedWidth(42)
            badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
            accent_col = t.accent if name == "Ogochukwu Odumodu" else t.accent2
            badge.setStyleSheet(f"""
                color: {t.c(accent_col)};
                background: rgba(26,159,255,0.10);
                border: 1px solid {t.c(t.border)};
                border-radius: 5px;
                padding: 3px 0;
            """)

            info = QVBoxLayout()
            info.setSpacing(2)
            n = QLabel(name)
            n.setFont(QFont("Rajdhani", 14, QFont.Weight.Bold))
            n.setStyleSheet(f"color: {t.c(accent_col)};")
            r = QLabel(role)
            r.setFont(QFont("Exo 2", 11))
            r.setStyleSheet(f"color: {t.c(t.text_secondary)};")
            info.addWidget(n)
            info.addWidget(r)

            row.addWidget(badge)
            row.addLayout(info)
            cl.addLayout(row)

            if role_icon == "[AI]":
                div = QFrame()
                div.setFixedHeight(1)
                div.setStyleSheet(f"background: {t.c(t.border)};")
                cl.addWidget(div)

        from datetime import date
        version = date.today().strftime("%y.%m.%d")
        footer = QLabel(f"gameshell v{version}  —  Built with passion on Linux")
        footer.setFont(QFont("Exo 2", 11))
        footer.setStyleSheet(f"color: {t.c(t.text_dim)};")
        footer.setAlignment(Qt.AlignmentFlag.AlignCenter)
        cl.addWidget(footer)
        content_layout.addWidget(credits_frame)
        content_layout.addSpacing(20)

        self._scroll = scroll
        scroll.setWidget(inner)
        self._content_layout = content_layout
        outer_layout.addWidget(scroll)

    def update_swatch(self, color: QColor):
        from PyQt6.QtGui import QColor
        self.title_lbl.setStyleSheet(f"color: {Theme.c(Theme.text_primary)};")
        self.hue_swatch.setStyleSheet(f"background: {color.name()}; border-radius: 6px;")
        current_hue = Theme.hue
        for btn, hue_val in self.palette_buttons:
            if hue_val == current_hue:
                btn.setStyleSheet(f"""
                    QPushButton {{
                        background: {Theme.c(Theme.accent)};
                        border: none;
                        border-radius: 6px;
                    }}
                    QPushButton:hover {{
                        background: {Theme.c(Theme.accent.lighter(110))};
                    }}
                """)
            else:
                base_color = Theme.hsl(hue_val, 80, 55)
                btn.setStyleSheet(f"""
                    QPushButton {{
                        background: {base_color.name()};
                        border: none;
                        border-radius: 6px;
                    }}
                    QPushButton:hover {{
                        background: {base_color.lighter(115).name()};
                    }}
                """)
        
        if hasattr(self, 'reset_btn'):
            self.reset_btn.setStyleSheet(f"""
                QPushButton {{
                    background: {Theme.c(Theme.bg_card)};
                    color: {Theme.c(Theme.text_secondary)};
                    border: none;
                    border-radius: 6px;
                }}
                QPushButton:hover {{
                    background: {Theme.c(Theme.bg_card_hover)};
                    color: {Theme.c(Theme.text_primary)};
                }}
            """)


class HintsBar(QFrame):
    def __init__(self):
        super().__init__()
        self.setFixedHeight(40)
        self._build()

    def _build(self):
        t = Theme
        self.setStyleSheet(f"""
            HintsBar {{
                background: transparent;
                border-top: 1px solid {t.c(t.border)};
            }}
        """)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)

        layout.addStretch()

        controller_hints = [
            ("L1", Theme.accent, "Prev View"),
            ("R1", Theme.accent, "Next View"),
            ("A", Theme.green, "Select"),
            ("B", Theme.red, "Back"),
            ("X", QColor(33, 150, 243), "Edit Game"),
            ("Y", Theme.yellow, "Favorite"),
        ]

        hint_sizes = []
        font_circle = QFont("Exo 2", 10, QFont.Weight.Bold)
        font_label = QFont("Exo 2", 10)
        for btn_txt, color, action in controller_hints:
            circle_width = 24
            label_width = QLabel(action).fontMetrics().horizontalAdvance(action) + 10
            total_width = circle_width + 8 + label_width + 20
            label_height = QLabel(action).fontMetrics().height() + 10
            total_height = max(24, label_height) + 12
            hint_sizes.append((total_width, total_height))

        max_width = max(w for w, _ in hint_sizes)
        max_height = max(h for _, h in hint_sizes)
        box_width = max(max_width, 100)
        base_height = max(max_height, 36)
        box_height = max(int(base_height * 0.80), 24)
        max_content = max_height - 12
        v_margin = max(2, (box_height - max_content) // 2)

        for (btn_txt, color, action), (w, h) in zip(controller_hints, hint_sizes):
            outer = QFrame()
            outer.setFixedSize(box_width, box_height)
            outer.setStyleSheet(f"""
                QFrame {{
                    background: rgba(255,255,255,0.04);
                    border: 1px solid {t.c(t.border)};
                    border-radius: 6px;
                }}
            """)

            outer_layout = QHBoxLayout(outer)
            outer_layout.setContentsMargins(10, v_margin, 10, v_margin)
            outer_layout.setSpacing(8)
            outer_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

            circle = QLabel(btn_txt)
            circle.setFixedSize(24, 24)
            circle.setFont(font_circle)
            circle.setAlignment(Qt.AlignmentFlag.AlignCenter)
            circle.setStyleSheet(f"""
                color: white;
                border: 1px solid {t.c(color)};
                border-radius: 6px;
                background: transparent;
                padding: 0px;
            """)

            lbl = QLabel(action)
            lbl.setFont(font_label)
            lbl.setStyleSheet(f"color: {t.c(t.text_dim)};")

            outer_layout.addWidget(circle)
            outer_layout.addWidget(lbl)

            layout.addWidget(outer, alignment=Qt.AlignmentFlag.AlignVCenter)

        layout.addStretch()


from PyQt6.QtGui import QColor