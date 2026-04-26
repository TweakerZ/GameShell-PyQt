from PyQt6.QtWidgets import (
    QDialog, QLineEdit, QLabel, QVBoxLayout, QHBoxLayout, QGridLayout,
    QPushButton, QCheckBox, QComboBox, QScrollArea, QWidget, QFileDialog,
    QMessageBox, QFrame, QGroupBox
)
from PyQt6.QtGui import QFont, QCursor, QDragEnterEvent, QDropEvent
from PyQt6.QtCore import Qt, pyqtSignal
from .theme import Theme
from .config import get_absolute_path
from .widgets import StyledButton, EMOJIS
from .data import uid
import time
import os


class DropLineEdit(QLineEdit):
    def __init__(self, placeholder="", parent=None):
        super().__init__(placeholder, parent)
        self.setAcceptDrops(True)
        self._refresh_style()

    def _refresh_style(self):
        self._base_style = """
            background: %s;
            border: 1px solid rgba(255,255,255,0.08);
            border-radius: 6px;
            padding: 12px 14px;
            color: %s;
            font-family: 'Exo 2';
            font-size: 13px;
        """ % (Theme.c(Theme.bg_card), Theme.c(Theme.text_primary))
        self.setStyleSheet(self._base_style)

    def dragEnterEvent(self, e):
        if e.mimeData().hasUrls():
            e.acceptProposedAction()
            self.setStyleSheet(self._base_style + "border: 2px solid #1a9fff;")

    def dragLeaveEvent(self, e):
        self.setStyleSheet(self._base_style)
        super().dragLeaveEvent(e)

    def dropEvent(self, e):
        urls = e.mimeData().urls()
        if urls:
            path = urls[0].toLocalFile()
            if path:
                self.setText(path)
                self.setCursorPosition(0)
        e.accept()


class GameDialog(QDialog):
    def __init__(self, parent, game=None):
        super().__init__(parent)
        self.game = game
        self.result_game = None
        self.selected_emoji = game.get('emoji', '🎮') if game else '🎮'
        self.setWindowTitle("Edit Game" if game else "Add Game")
        self.setModal(True)
        self.setFixedSize(1000, 700)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Dialog)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setStyleSheet(f"""
            QDialog {{ background: rgba(0,0,0,0.6); }}
            QLabel {{ color: {Theme.c(Theme.text_primary)}; }}

            QLineEdit, QComboBox {{
                background: {Theme.c(Theme.bg_card)};
                border: 1px solid rgba(255,255,255,0.08);
                border-radius: 6px;
                padding: 12px 14px;
                color: {Theme.c(Theme.text_primary)};
                font-family: 'Exo 2';
                font-size: 13px;
            }}

            QLineEdit:focus, QComboBox:focus {{
                border: 1px solid {Theme.c(Theme.accent)};
            }}

            QComboBox::drop-down {{ border: none; }}

            QComboBox QAbstractItemView {{
                background: {Theme.c(Theme.bg_panel)};
                color: {Theme.c(Theme.text_primary)};
                selection-background-color: {Theme.c(Theme.accent_dim)};
                border-radius: 6px;
                border: 1px solid rgba(255,255,255,0.08);
            }}

            QScrollArea {{ border: none; background: transparent; }}
        """)
        self._build()

    def _build(self):
        t = Theme
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        center_widget = QWidget()
        center_layout = QVBoxLayout(center_widget)
        center_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        outer.addWidget(center_widget, alignment=Qt.AlignmentFlag.AlignCenter)

        panel = QFrame()
        panel.setFixedWidth(520)
        panel.setStyleSheet(f"""
            QFrame {{
                background: {Theme.c(Theme.bg_panel)};
                border: 1px solid rgba(255,255,255,0.08);
                border-radius: 6px;
            }}
        """)
        center_layout.addWidget(panel)

        pl = QVBoxLayout(panel)
        pl.setContentsMargins(28, 24, 28, 24)
        pl.setSpacing(14)

        title_lbl = QLabel("Edit Game" if self.game else "Add Game")
        title_lbl.setFont(QFont("Rajdhani", 20, QFont.Weight.Bold))
        title_lbl.setStyleSheet(f"color: {t.c(t.accent)};")
        pl.addWidget(title_lbl)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setStyleSheet("QScrollArea { border: none; background: transparent; } QScrollArea > QWidget > QWidget { background: transparent; } QScrollBar:vertical, QScrollBar:horizontal { border: none; background: transparent; }")
        inner = QWidget()
        form = QVBoxLayout(inner)
        form.setSpacing(12)
        form.setContentsMargins(0, 0, 12, 0)
        scroll.setWidget(inner)
        pl.addWidget(scroll, 1)

        def field(lbl_text, widget):
            w = QWidget()
            vl = QVBoxLayout(w)
            vl.setContentsMargins(0,0,0,0); vl.setSpacing(4)
            lbl = QLabel(lbl_text.upper())
            lbl.setFont(QFont("Exo 2", 10, QFont.Weight.Bold))
            lbl.setStyleSheet(f"color: {t.c(t.text_secondary)}; letter-spacing: 1px;")
            vl.addWidget(lbl); vl.addWidget(widget)
            return w

        def divider(text):
            lbl = QLabel(text.upper())
            lbl.setFont(QFont("Exo 2", 10, QFont.Weight.Bold))
            lbl.setStyleSheet(f"color: {t.c(t.text_secondary)}; letter-spacing: 3px; padding: 8px 0 4px;")
            lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            form.addWidget(lbl)

        CB_STYLE = f"color: {t.c(t.text_secondary)}; padding: 4px 0;"

        def cb(text, checked=False):
            c = QCheckBox(text)
            c.setChecked(checked)
            c.setStyleSheet(CB_STYLE)
            return c

        lo   = (self.game or {}).get("launchOpts") or {}
        gs   = lo.get("gamescope") or {}
        lsfg = lo.get("lsfg") or {}

        self.f_name = QLineEdit(self.game.get("name","") if self.game else "")
        self.f_name.setPlaceholderText("Game name")
        form.addWidget(field("Name *", self.f_name))

        exec_container = QWidget()
        exec_layout = QHBoxLayout(exec_container)
        exec_layout.setContentsMargins(0,0,0,0)
        exec_layout.setSpacing(6)
        self.f_exec = DropLineEdit("/usr/bin/game or steam://rungameid/12345")
        self.f_exec.setText(self.game.get("exec","") if self.game else "")
        from PyQt6.QtWidgets import QSizePolicy
        self.f_exec.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        exec_layout.addWidget(self.f_exec, 1)
        form.addWidget(field("Exec / Command *", exec_container))

        self.f_desc = QLineEdit(self.game.get("desc","") if self.game else "")
        self.f_desc.setPlaceholderText("Short description (optional)")
        form.addWidget(field("Description", self.f_desc))

        self.f_img = DropLineEdit("/path/to/cover.png (optional)")
        self.f_img.setText(self.game.get("img","") if self.game else "")
        self.f_img.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        form.addWidget(field("Cover Image", self.f_img))

        emoji_lbl = QLabel("ICON")
        emoji_lbl.setFont(QFont("Exo 2", 10, QFont.Weight.Bold))
        emoji_lbl.setStyleSheet(f"color: {t.c(t.text_secondary)}; letter-spacing: 1px;")
        form.addWidget(emoji_lbl)
        emoji_grid = QGridLayout(); emoji_grid.setSpacing(4)
        self.emoji_btns = []
        for i, em in enumerate(EMOJIS):
            btn = QPushButton(em)
            btn.setFixedSize(36, 36)
            btn.setFont(QFont("Segoe UI Emoji", 16))
            btn.setCheckable(True); btn.setChecked(em == self.selected_emoji)
            btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
            btn.clicked.connect(lambda _, e=em: self._pick_emoji(e))
            self._style_emoji_btn(btn, em == self.selected_emoji)
            emoji_grid.addWidget(btn, i // 8, i % 8)
            self.emoji_btns.append((em, btn))
        eg_w = QWidget(); eg_w.setLayout(emoji_grid)
        form.addWidget(eg_w)

        divider("Launch Options")

        self.f_mh   = cb("MangoHUD — FPS overlay & performance metrics", bool(lo.get("mangohud")))
        self.f_wfsr = cb("Wine FSR — WINE_FULLSCREEN_FSR upscaling",     bool(lo.get("winefsr")))
        form.addWidget(self.f_mh)
        form.addWidget(self.f_wfsr)

        self.f_lsfg = cb("LSFG-VK Frame Generation", bool(lsfg))
        form.addWidget(self.f_lsfg)

        self.f_lsfg_legacy = cb("Legacy mode — LSFG_PROCESS", bool(lsfg.get("legacy")))
        form.addWidget(self.f_lsfg_legacy)

        self.f_lsfg_profile = QLineEdit(lsfg.get("profile",""))
        self.f_lsfg_profile.setPlaceholderText("LSFGVK_PROFILE (e.g. default)")
        form.addWidget(field("  LSFGVK Profile", self.f_lsfg_profile))

        self.f_lsfg_legacy_profile = QLineEdit(lsfg.get("legacyProfile",""))
        self.f_lsfg_legacy_profile.setPlaceholderText("LSFG_PROCESS profile name")
        form.addWidget(field("  LSFG_PROCESS Profile", self.f_lsfg_legacy_profile))

        divider("Environment Variables")

        self.env_rows_widget = QWidget()
        self.env_rows_layout = QVBoxLayout(self.env_rows_widget)
        self.env_rows_layout.setContentsMargins(0,0,0,0)
        self.env_rows_layout.setSpacing(6)
        self._env_rows = []
        form.addWidget(self.env_rows_widget)

        for pair in (lo.get("env") or []):
            self._add_env_row(pair.get("k",""), pair.get("v",""))

        add_env_btn = StyledButton("+ Add Variable")
        add_env_btn.clicked.connect(lambda: self._add_env_row())
        form.addWidget(add_env_btn)

        divider("Gamescope")

        self.f_gs = cb("Enable Gamescope — Wayland compositor scaling & filters", bool(gs))
        form.addWidget(self.f_gs)

        res_row = QHBoxLayout()
        self.f_gw = QLineEdit(str(gs.get("gw",""))); self.f_gw.setPlaceholderText("Game W")
        self.f_gh = QLineEdit(str(gs.get("gh",""))); self.f_gh.setPlaceholderText("Game H")
        self.f_ww = QLineEdit(str(gs.get("ww",""))); self.f_ww.setPlaceholderText("Win W")
        self.f_wh = QLineEdit(str(gs.get("wh",""))); self.f_wh.setPlaceholderText("Win H")
        for f_ in [self.f_gw, self.f_gh, self.f_ww, self.f_wh]:
            res_row.addWidget(f_)
        res_w = QWidget(); res_w.setLayout(res_row)
        form.addWidget(field("  Resolution  Game W/H · Window W/H", res_w))

        self.f_gs_fs  = cb("  Fullscreen  (-f)",                        bool(gs.get("fs")))
        self.f_gs_gk  = cb("  Grab Keyboard  (--grab)",                 bool(gs.get("gk")))
        self.f_gs_gc  = cb("  Grab Cursor  (--force-grab-cursor)",      bool(gs.get("gc")))
        self.f_gs_ma  = cb("  MangoApp  (--mangoapp)",                  bool(gs.get("ma")))
        self.f_gs_wsi = cb("  Gamescope WSI  (uncheck = ENABLE_GAMESCOPE_WSI=0)",
                            gs.get("wsi", True) if gs else True)
        for w in [self.f_gs_fs, self.f_gs_gk, self.f_gs_gc, self.f_gs_ma, self.f_gs_wsi]:
            form.addWidget(w)

        self.f_gs_filter = QComboBox()
        for fv, fn in [("","None"),("fsr","FSR"),("nis","NIS"),("pixel","Pixel"),("linear","Linear")]:
            self.f_gs_filter.addItem(fn, fv)
        fi = self.f_gs_filter.findData(gs.get("filter",""))
        if fi >= 0: self.f_gs_filter.setCurrentIndex(fi)
        form.addWidget(field("  Filter", self.f_gs_filter))

        actions = QHBoxLayout(); actions.setSpacing(20)
        if self.game:
            del_btn = StyledButton("Delete", danger=True)
            del_btn.clicked.connect(self._delete)
            del_btn.setFixedSize(100, 45)
            actions.addWidget(del_btn)
        actions.addStretch()
        cancel = StyledButton("Cancel"); cancel.clicked.connect(self.reject)
        cancel.setFixedSize(100, 45)
        save   = StyledButton("Save"); save.clicked.connect(self._save)
        save.setFixedSize(100, 45)
        actions.addWidget(cancel); actions.addWidget(save)
        pl.addLayout(actions)

    def _add_env_row(self, k='', v=''):
        row_w = QWidget()
        row_l = QHBoxLayout(row_w)
        row_l.setContentsMargins(0,0,0,0); row_l.setSpacing(6)
        k_inp = QLineEdit(k); k_inp.setPlaceholderText("KEY")
        v_inp = QLineEdit(v); v_inp.setPlaceholderText("value")
        del_btn = QPushButton("✕")
        del_btn.setFixedSize(28, 28)
        del_btn.setStyleSheet(f"""
            QPushButton {{
                background: rgba(255,68,102,0.10); color: {Theme.c(Theme.red)};
                border: 1px solid rgba(255,68,102,0.3); border-radius: 4px; font-size: 13px;
            }}
            QPushButton:hover {{ background: rgba(255,68,102,0.22); }}
        """)
        del_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        row_l.addWidget(k_inp); row_l.addWidget(v_inp); row_l.addWidget(del_btn)
        self.env_rows_layout.addWidget(row_w)
        entry = (k_inp, v_inp, row_w)
        self._env_rows.append(entry)
        del_btn.clicked.connect(lambda: self._remove_env_row(entry))

    def _remove_env_row(self, entry):
        k_inp, v_inp, row_w = entry
        row_w.setParent(None)
        if entry in self._env_rows:
            self._env_rows.remove(entry)

    def _style_emoji_btn(self, btn, selected):
        t = Theme
        if selected:
            btn.setStyleSheet(f"background: rgba(26,159,255,0.2); border: 2px solid {t.c(t.accent)}; border-radius:6px;")
        else:
            btn.setStyleSheet(f"background: rgba(255,255,255,0.03); border: 2px solid transparent; border-radius:6px;")

    def _pick_emoji(self, em):
        self.selected_emoji = em
        for e, btn in self.emoji_btns:
            btn.setChecked(e == em)
            self._style_emoji_btn(btn, e == em)

    def _save(self):
        name  = self.f_name.text().strip()
        exec_ = self.f_exec.text().strip()
        if not name:
            QMessageBox.warning(self, "Missing Name", "Please enter a game name.")
            return
        if not exec_:
            QMessageBox.warning(self, "Missing Command", "Please enter an exec command.")
            return

        gs = None
        if self.f_gs.isChecked():
            gs = {
                'gw': self.f_gw.text().strip(), 'gh': self.f_gh.text().strip(),
                'ww': self.f_ww.text().strip(), 'wh': self.f_wh.text().strip(),
                'fs': self.f_gs_fs.isChecked(),
                'gk': self.f_gs_gk.isChecked(),
                'gc': self.f_gs_gc.isChecked(),
                'ma': self.f_gs_ma.isChecked(),
                'wsi': self.f_gs_wsi.isChecked(),
                'filter': self.f_gs_filter.currentData(),
            }

        lsfg = None
        if self.f_lsfg.isChecked():
            lsfg = {
                'profile': self.f_lsfg_profile.text().strip(),
                'legacy':  self.f_lsfg_legacy.isChecked(),
                'legacyProfile': self.f_lsfg_legacy_profile.text().strip(),
            }

        env = [
            {'k': k_inp.text().strip(), 'v': v_inp.text().strip()}
            for k_inp, v_inp, _ in self._env_rows
            if k_inp.text().strip()
        ]

        self.result_game = {
            'id':     self.game['id'] if self.game else uid(),
            'name':   name,
            'exec':   exec_,
            'desc':   self.f_desc.text().strip(),
            'img':    self.f_img.text().strip(),
            'type':   self.game.get('type', 'native') if self.game else 'native',
            'emoji':  self.selected_emoji,
            'fav':    self.game.get('fav', False) if self.game else False,
            'played': self.game.get('played', 0) if self.game else 0,
            '_added': self.game.get('_added', int(time.time() * 1000)) if self.game else int(time.time() * 1000),
            'launchOpts': {
                'gamescope': gs,
                'mangohud':  self.f_mh.isChecked(),
                'winefsr':   self.f_wfsr.isChecked(),
                'lsfg':      lsfg,
                'env':       env,
            }
        }
        self.accept()

    def _delete(self):
        if QMessageBox.question(self, "Delete Game",
            f"Remove \"{self.game['name']}\" from library?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        ) == QMessageBox.StandardButton.Yes:
            self.result_game = None
            self.done(2)


class DetailDialog(QDialog):
    launch_sig = pyqtSignal(dict)
    edit_sig   = pyqtSignal(dict)
    fav_sig    = pyqtSignal(str)

    def __init__(self, parent, game):
        super().__init__(parent)
        self.game = game
        self.setModal(True)
        self.setFixedSize(800, 600)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Dialog)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setStyleSheet("QDialog { background: rgba(7, 10, 15, 0.85); }")
        self._build()

    def _build(self):
        t = Theme
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

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
        hero.setFixedHeight(200)
        hero.setStyleSheet("background: qlineargradient(x1:0,y1:0,x2:1,y2:1, stop:0 #1a2540, stop:1 #0f1525); border-radius: 6px 6px 0 0;")
        hl = QHBoxLayout(hero)
        hl.setAlignment(Qt.AlignmentFlag.AlignCenter)

        art_container = QWidget()
        art_container.setFixedSize(540, 180)
        art_layout = QVBoxLayout(art_container)
        art_layout.setContentsMargins(0, 0, 0, 0)
        art_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        from PyQt6.QtGui import QPixmap
        if self.game.get('img'):
            import pathlib
            img_path = get_absolute_path(self.game['img'])
            if img_path and pathlib.Path(img_path).exists():
                pix = QPixmap(img_path)
                if not pix.isNull():
                    img_lbl = QLabel()
                    img_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
                    img_lbl.setPixmap(pix.scaled(540, 180,
                        Qt.AspectRatioMode.KeepAspectRatio,
                        Qt.TransformationMode.SmoothTransformation))
                    img_lbl.setStyleSheet("background: transparent;")
                    art_layout.addWidget(img_lbl)
                else:
                    em = QLabel(self.game.get('emoji','🎮'))
                    em.setFont(QFont("Segoe UI Emoji", 64))
                    em.setAlignment(Qt.AlignmentFlag.AlignCenter)
                    art_layout.addWidget(em)
            else:
                em = QLabel(self.game.get('emoji','🎮'))
                em.setFont(QFont("Segoe UI Emoji", 64))
                em.setAlignment(Qt.AlignmentFlag.AlignCenter)
                art_layout.addWidget(em)
        else:
            em = QLabel(self.game.get('emoji','🎮'))
            em.setFont(QFont("Segoe UI Emoji", 64))
            em.setAlignment(Qt.AlignmentFlag.AlignCenter)
            art_layout.addWidget(em)
        
        hl.addWidget(art_container)
        pl.addWidget(hero)

        body = QWidget()
        bl = QVBoxLayout(body)
        bl.setContentsMargins(28, 20, 28, 24)
        bl.setSpacing(12)

        name_lbl = QLabel(self.game['name'])
        name_lbl.setFont(QFont("Rajdhani", 26, QFont.Weight.Bold))
        name_lbl.setWordWrap(True)
        bl.addWidget(name_lbl)

        if self.game.get('desc'):
            desc = QLabel(self.game['desc'])
            desc.setStyleSheet(f"color: {Theme.c(Theme.text_secondary)};")
            desc.setWordWrap(True)
            bl.addWidget(desc)

        acts = QHBoxLayout()
        acts.setSpacing(20)
        acts.setContentsMargins(0, 8, 0, 0)
        acts.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.launch_btn = StyledButton("▶  LAUNCH")
        self.launch_btn.setFont(QFont("Exo 2", 11, QFont.Weight.DemiBold))
        self.launch_btn.clicked.connect(lambda: (self.launch_sig.emit(self.game), self.accept()))
        self.launch_btn.setFixedSize(130, 55)

        fav_text = "★  Unstar" if self.game.get('fav') else "☆  Star"
        self.fav_btn = StyledButton(fav_text)
        self.fav_btn.clicked.connect(lambda: (self.fav_sig.emit(self.game['id']), self.accept()))
        self.fav_btn.setFixedSize(130, 55)

        self.edit_btn = StyledButton("✎  Edit")
        self.edit_btn.clicked.connect(lambda: (self.edit_sig.emit(self.game), self.accept()))
        self.edit_btn.setFixedSize(130, 55)

        self.close_btn = StyledButton("Close")
        self.close_btn.clicked.connect(self.reject)
        self.close_btn.setFixedSize(130, 55)

        acts.addWidget(self.launch_btn)
        acts.addWidget(self.fav_btn)
        acts.addWidget(self.edit_btn)
        acts.addWidget(self.close_btn)
        bl.addLayout(acts)
        pl.addWidget(body)

        self._buttons = [self.launch_btn, self.fav_btn, self.edit_btn, self.close_btn]
        for btn in self._buttons:
            btn.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.launch_btn.setFocus()
        self._update_button_focus_states()

    def _update_button_focus_states(self):
        current = self.focusWidget()
        for btn in self._buttons:
            is_focused = (btn == current)
            btn.set_focused(is_focused)

    def handle_controller_nav(self, direction):
        if not hasattr(self, '_buttons') or not self._buttons:
            return
        current = self.focusWidget()
        idx = 0
        try:
            if current in self._buttons:
                idx = self._buttons.index(current)
            else:
                idx = 0
        except TypeError:
            idx = 0

        if direction == "left":
            idx = max(0, idx - 1)
        elif direction == "right":
            idx = min(len(self._buttons) - 1, idx + 1)
        else:
            return
        new_btn = self._buttons[idx]
        new_btn.setFocus()
        self._update_button_focus_states()

    def handle_controller_button(self, btn):
        if btn == 'a':
            focused = self.focusWidget()
            if focused and hasattr(focused, 'click') and focused in self._buttons:
                focused.click()
        elif btn == 'b':
            self.reject()

    def focusInEvent(self, a0):
        super().focusInEvent(a0)
        self._update_button_focus_states()