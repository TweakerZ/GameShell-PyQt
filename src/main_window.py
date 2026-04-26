from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QStackedWidget,
    QLabel, QDialog, QFileDialog, QMessageBox, QFrame, QScrollArea
)
from PyQt6.QtGui import QFont, QPalette, QColor
from PyQt6.QtCore import Qt, QTimer, QProcess
from PyQt6.QtWidgets import QSizePolicy
import subprocess, re, time

from .theme import Theme
from .data import read_json, write_json
from .config import LIBRARY_FILE, SETTINGS_FILE
from .game_manager import game_mgr
from .command_builder import build_cmd
from .controller import SDL2ControllerThread
from .widgets import StyledButton
from .game_card import GameCard, DropDesktopCard
from .dialogs import GameDialog, DetailDialog
from .now_playing import NowPlayingDialog, NowPlayingCard
from .views import GameGrid, TopNavBar, SettingsView, HintsBar


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.library      = []
        self.current_view = "home"
        self.nav_zone     = "topbar"
        self.grid_idx     = 0
        self.sidebar_idx  = 0
        self._np_dialog   = None
        self._active_dialog = None
        self._controller_blocked = False
        self._controller_thread = None

        self._load_library()
        self._load_settings()
        self._build_ui()
        self._apply_theme()
        self._start_timers()
        self._connect_controller()

        if self.current_view == "home":
            self.nav_zone = "grid"
            if self.view_home._grid._cards:
                self.view_home._grid.focus_card(0)

        self.setWindowTitle("GameShell")
        self.showFullScreen()
        self.topbar.np_clicked.connect(self._open_np_window)

    def _build_ui(self):
        t = Theme
        central = QWidget()
        central.setStyleSheet(f"background: {t.c(t.bg_deep)};")
        self.setCentralWidget(central)

        root = QVBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        self.topbar = TopNavBar()
        self.topbar.view_changed.connect(self._switch_view)
        self.topbar.add_game.connect(lambda: self._open_add_game())
        self.topbar.import_desktop.connect(self._import_desktop)
        self.topbar.np_clicked.connect(self._open_np_window)
        self.topbar.power_off.connect(self.close)
        root.addWidget(self.topbar)

        self.stack = QStackedWidget()
        self.stack.setStyleSheet(f"background: {t.c(t.bg_deep)};")

        self.view_home      = self._make_grid_view()
        self.view_library   = self._make_grid_view()
        self.view_recent    = self._make_grid_view()
        self.view_favorites = self._make_grid_view()
        self.view_settings  = SettingsView()
        self.view_settings.hue_changed.connect(self._on_hue_changed)

        for v in [self.view_home, self.view_library, self.view_recent,
                  self.view_favorites, self.view_settings]:
            self.stack.addWidget(v)

        root.addWidget(self.stack)

        self.hintsbar = HintsBar()
        root.addWidget(self.hintsbar)

        self.topbar.set_active("home")
        self._render_all()

    def _make_grid_view(self):
        w = QWidget()
        w.setStyleSheet("background: transparent;")
        l = QVBoxLayout(w)
        l.setContentsMargins(32, 28, 32, 32)
        l.setSpacing(16)
        hdr = QHBoxLayout()
        hdr.setContentsMargins(0, 0, 0, 0)
        hdr.setSpacing(0)

        hdr.addStretch()

        title_lbl = QLabel()
        title_lbl.setFont(QFont("Rajdhani", 22, QFont.Weight.Bold))
        title_lbl.setStyleSheet(f"color: {Theme.c(Theme.text_primary)};")
        title_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        hdr.addWidget(title_lbl)

        count_lbl = QLabel()
        count_lbl.setFont(QFont("Exo 2", 12))
        count_lbl.setStyleSheet(f"color: {Theme.c(Theme.text_dim)};")
        hdr.addStretch()
        hdr.addWidget(count_lbl)

        l.addLayout(hdr)
        grid = GameGrid()
        grid.card_clicked.connect(self._on_card_clicked)
        l.addWidget(grid)
        w._title = title_lbl
        w._count = count_lbl
        w._grid  = grid
        return w

    def _render_all(self):
        lib = self.library
        by_played = sorted([g for g in lib if g.get("played")],
                            key=lambda g: -g.get("played", 0))
        by_added  = sorted(lib, key=lambda g: -g.get("_added", 0))
        by_name   = sorted(lib, key=lambda g: g.get("name", "").lower())
        favs      = sorted([g for g in lib if g.get("fav")],
                            key=lambda g: g.get("name", "").lower())

        v = self.view_home
        v._title.setText("Home")
        v._count.setText("")

        gl = v._grid._grid
        while gl.count():
            item = gl.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        v._grid._cards = []
        v._grid._focused_idx = -1

        col = 0; row = 0
        cols = 6

        def place(widget, is_card=True):
            nonlocal row, col
            if col >= cols:
                col = 0; row += 1
            gl.addWidget(widget, row, col)
            if is_card:
                v._grid._cards.append(widget)
            col += 1

        self._np_card = None
        if game_mgr.running and game_mgr.game_info:
            matched = next((g for g in lib if g.get("name") == game_mgr.game_info["name"]), None)
            info = dict(game_mgr.game_info)
            if matched:
                info["emoji"] = matched.get("emoji", "🎮")
                info["img"] = matched.get("img")
            np_card = NowPlayingCard(info)
            np_card.clicked_sig.connect(self._open_np_window)
            place(np_card)
            self._np_card = np_card

        add_game_card = GameCard({'id': '__add__', 'name': 'Add Game', 'emoji': '➕'})
        add_game_card.clicked_sig.connect(self._open_add_game)
        add_game_card.setFixedWidth(148)
        place(add_game_card)

        drop_desktop_card = DropDesktopCard()
        drop_desktop_card.clicked_sig.connect(self._on_desktop_dropped)
        place(drop_desktop_card)

        kill_gs_card = GameCard({'id': '__kill_gs__', 'name': 'Kill Gamescope', 'emoji': '💀'})
        kill_gs_card.clicked_sig.connect(self._kill_gamescope)
        kill_gs_card.setFixedWidth(148)
        place(kill_gs_card)

        recently_added = by_added[:6]
        if recently_added:
            if col > 0:
                col = 0; row += 1
            hdr = QLabel("Recently Added")
            hdr.setFont(QFont("Rajdhani", 14, QFont.Weight.Bold))
            hdr.setStyleSheet(f"""
                color: {Theme.c(Theme.text_secondary)};
                border-top: 1px solid {Theme.c(Theme.border)};
                padding-top: 10px; letter-spacing: 1px;
            """)
            gl.addWidget(hdr, row, 0, 1, cols)
            row += 1; col = 0
            for g in recently_added:
                card = GameCard(g)
                card.clicked_sig.connect(self._on_card_clicked)
                place(card)

        v = self.view_library
        v._title.setText("All Games")
        v._count.setText("")
        v._grid.set_games(by_name, cols=6)

        v = self.view_recent
        v._title.setText("Recently Played")
        v._count.setText("")
        v._grid.set_games(by_played, cols=6)

        v = self.view_favorites
        v._title.setText("Favorites")
        v._count.setText("")
        v._grid.set_games(favs, cols=6)

    def _switch_view(self, name):
        self.current_view = name
        views = {
            "home": 0, "library": 1, "recent": 2,
            "favorites": 3, "settings": 4
        }
        self.stack.setCurrentIndex(views.get(name, 0))
        self.topbar.set_active(name)
        if name in ("home", "library", "recent", "favorites"):
            self.nav_zone = "grid"
            grid = self._get_current_grid()
            if grid._cards:
                grid.focus_card(0)
        else:
            self.nav_zone = "none"
        self.grid_idx = 0

    def _import_desktop(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Import .desktop File", "",
            "Desktop Files (*.desktop);;All Files (*)"
        )
        if not path:
            return
        try:
            with open(path) as f:
                content = f.read()
            from .data import uid
            name = re.search(r'^Name\s*=\s*(.+)$', content, re.MULTILINE)
            exec_ = re.search(r'^Exec\s*=\s*(.+)$', content, re.MULTILINE)
            icon = re.search(r'^Icon\s*=\s*(.+)$', content, re.MULTILINE)
            comment = re.search(r'^Comment\s*=\s*(.+)$', content, re.MULTILINE)
            if name and exec_:
                g = {
                    'id':    uid(),
                    'name':  name.group(1).strip(),
                    'exec':  exec_.group(1).strip().split('%')[0].strip(),
                    'desc':  comment.group(1).strip() if comment else '',
                    'img':   icon.group(1).strip() if icon else '',
                    'type':  'native',
                    'emoji': '🎮',
                    'fav':   False, 'played': 0,
                    '_added': int(time.time() * 1000),
                    'launchOpts': {}
                }
                self.library.append(g)
                self._save_library()
                self._render_all()
                QMessageBox.information(self, "Imported", f'"{g["name"]}" added to library.')
            else:
                QMessageBox.warning(self, "Parse Error", "Could not find Name or Exec in the .desktop file.")
        except Exception as ex:
            QMessageBox.warning(self, "Error", str(ex))

    def _kill_gamescope(self):
        dlg = QDialog(self)
        dlg.setWindowTitle("Kill Gamescope")
        dlg.setModal(True)
        dlg.setFixedSize(500, 300)
        dlg.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Dialog)
        dlg.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        dlg.setStyleSheet("QDialog { background: rgba(7, 10, 15, 0.85); }")

        outer = QVBoxLayout(dlg)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        center_widget = QWidget()
        center_layout = QVBoxLayout(center_widget)
        center_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        outer.addWidget(center_widget, alignment=Qt.AlignmentFlag.AlignCenter)

        panel = QFrame()
        panel.setFixedWidth(400)
        panel.setStyleSheet(f"""
            QFrame {{
                background: {Theme.c(Theme.bg_panel)};
                border: 1px solid {Theme.c(Theme.border)};
                border-radius: 6px;
            }}
        """)
        center_layout.addWidget(panel)

        pl = QVBoxLayout(panel)
        pl.setContentsMargins(28, 24, 28, 24)
        pl.setSpacing(16)

        title = QLabel("⚠️  Kill Gamescope")
        title.setFont(QFont("Rajdhani", 20, QFont.Weight.Bold))
        title.setStyleSheet(f"color: {Theme.c(Theme.accent)};")
        pl.addWidget(title)

        msg = QLabel(
            "This will forcefully terminate all gamescope, gamescope-wl, "
            "and gamescopereaper processes.\n\nAre you sure?"
        )
        msg.setWordWrap(True)
        msg.setStyleSheet(f"color: {Theme.c(Theme.text_primary)}; font-family: 'Exo 2'; font-size: 13px;")
        pl.addWidget(msg)

        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(12)
        btn_layout.setContentsMargins(0, 8, 0, 0)

        cancel_btn = StyledButton("Cancel")
        cancel_btn.setFixedSize(120, 45)
        cancel_btn.clicked.connect(dlg.reject)

        confirm_btn = StyledButton("Kill")
        confirm_btn.setFixedSize(120, 45)
        confirm_btn.setStyleSheet(confirm_btn.styleSheet() + """
            StyledButton { background: #c92a2a; border-color: #c92a2a; }
            StyledButton:hover { background: #e03131; border-color: #e03131; }
            StyledButton:pressed { background: #a61e1e; border-color: #a61e1e; }
        """)
        confirm_btn.clicked.connect(dlg.accept)

        btn_layout.addStretch()
        btn_layout.addWidget(cancel_btn)
        btn_layout.addWidget(confirm_btn)
        pl.addLayout(btn_layout)

        if dlg.exec() != QDialog.DialogCode.Accepted:
            return

        try:
            result = subprocess.run(
                ['killall', '-9', 'gamescope', 'gamescope-wl', 'gamescopereaper'],
                capture_output=True,
                text=True
            )
            if result.returncode == 0:
                self._show_info_dialog("Success", "Gamescope processes terminated.")
            else:
                msg = result.stderr.strip() or "No gamescope processes found."
                self._show_info_dialog("Done", msg)
        except Exception as e:
            self._show_error_dialog("Error", f"Failed to kill gamescope: {e}")

    def _show_info_dialog(self, title, message):
        dlg = QDialog(self)
        dlg.setWindowTitle(title)
        dlg.setModal(True)
        dlg.setFixedSize(400, 250)
        dlg.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Dialog)
        dlg.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        dlg.setStyleSheet("QDialog { background: rgba(7, 10, 15, 0.85); }")

        outer = QVBoxLayout(dlg)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        center_widget = QWidget()
        center_layout = QVBoxLayout(center_widget)
        center_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        outer.addWidget(center_widget, alignment=Qt.AlignmentFlag.AlignCenter)

        panel = QFrame()
        panel.setFixedWidth(340)
        panel.setStyleSheet(f"""
            QFrame {{
                background: {Theme.c(Theme.bg_panel)};
                border: 1px solid {Theme.c(Theme.border)};
                border-radius: 6px;
            }}
        """)
        center_layout.addWidget(panel)

        pl = QVBoxLayout(panel)
        pl.setContentsMargins(28, 24, 28, 24)
        pl.setSpacing(16)

        title_lbl = QLabel("✓  " + title)
        title_lbl.setFont(QFont("Rajdhani", 20, QFont.Weight.Bold))
        title_lbl.setStyleSheet(f"color: {Theme.c(Theme.accent)};")
        pl.addWidget(title_lbl)

        msg_lbl = QLabel(message)
        msg_lbl.setWordWrap(True)
        msg_lbl.setStyleSheet(f"color: {Theme.c(Theme.text_primary)}; font-family: 'Exo 2'; font-size: 13px;")
        pl.addWidget(msg_lbl)

        btn = StyledButton("OK")
        btn.setFixedSize(120, 45)
        btn.clicked.connect(dlg.accept)

        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        btn_layout.addWidget(btn)
        btn_layout.addStretch()
        pl.addLayout(btn_layout)

        dlg.exec()

    def _show_error_dialog(self, title, message):
        dlg = QDialog(self)
        dlg.setWindowTitle(title)
        dlg.setModal(True)
        dlg.setFixedSize(400, 250)
        dlg.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Dialog)
        dlg.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        dlg.setStyleSheet("QDialog { background: rgba(7, 10, 15, 0.85); }")

        outer = QVBoxLayout(dlg)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        center_widget = QWidget()
        center_layout = QVBoxLayout(center_widget)
        center_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        outer.addWidget(center_widget, alignment=Qt.AlignmentFlag.AlignCenter)

        panel = QFrame()
        panel.setFixedWidth(340)
        panel.setStyleSheet(f"""
            QFrame {{
                background: {Theme.c(Theme.bg_panel)};
                border: 1px solid #c92a2a;
                border-radius: 6px;
            }}
        """)
        center_layout.addWidget(panel)

        pl = QVBoxLayout(panel)
        pl.setContentsMargins(28, 24, 28, 24)
        pl.setSpacing(16)

        title_lbl = QLabel("✗  " + title)
        title_lbl.setFont(QFont("Rajdhani", 20, QFont.Weight.Bold))
        title_lbl.setStyleSheet(f"color: #c92a2a;")
        pl.addWidget(title_lbl)

        msg_lbl = QLabel(message)
        msg_lbl.setWordWrap(True)
        msg_lbl.setStyleSheet(f"color: {Theme.c(Theme.text_primary)}; font-family: 'Exo 2'; font-size: 13px;")
        pl.addWidget(msg_lbl)

        btn = StyledButton("OK")
        btn.setFixedSize(120, 45)
        btn.clicked.connect(dlg.accept)

        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        btn_layout.addWidget(btn)
        btn_layout.addStretch()
        pl.addLayout(btn_layout)

        dlg.exec()

    def _on_card_clicked(self, gid):
        if gid == "__add__":
            self._open_add_game()
            return
        if gid == "__kill_gs__":
            self._kill_gamescope()
            return
        g = next((x for x in self.library if x['id'] == gid), None)
        if not g:
            return
        dlg = DetailDialog(self, g)
        dlg.launch_sig.connect(self._launch_game)
        dlg.edit_sig.connect(self._open_edit_game)
        dlg.fav_sig.connect(self._toggle_fav)
        self._active_dialog = dlg
        try:
            dlg.exec()
        finally:
            self._active_dialog = None

    def _launch_game(self, g):
        cmd = build_cmd(g)
        game_mgr.on_exit = self._on_game_exit
        game_mgr.launch(cmd, g['name'])
        g['played'] = int(time.time() * 1000)
        self._save_library()
        self._render_all()
        self._open_np_window()

    def _on_game_exit(self):
        QTimer.singleShot(0, self._game_exited)

    def _game_exited(self):
        self.topbar.set_now_playing(None, "")
        if self._np_dialog and self._np_dialog.isVisible():
            self._np_dialog.hide()
        self.showFullScreen()
        self.activateWindow()
        self._render_all()
        self._controller_blocked = False

    def _open_np_window(self):
        if not game_mgr.running:
            return
        g = next((x for x in self.library if x['name'] == game_mgr.game_info['name']), None)
        game = g.copy() if g else {'name': game_mgr.game_info['name'], 'emoji': '🎮'}
        if self._np_dialog:
            self._np_dialog.close()
        self._np_dialog = NowPlayingDialog(self, game)
        self._np_dialog.kill_sig.connect(self._force_quit_game)
        self._controller_blocked = True
        self._np_dialog.finished.connect(lambda: setattr(self, '_controller_blocked', False))
        self._np_dialog.show_centered(self.geometry())

    def _force_quit_game(self):
        game_mgr.kill()
        self._game_exited()

    def _open_add_game(self):
        dlg = GameDialog(self)
        if dlg.exec() == QDialog.DialogCode.Accepted and dlg.result_game:
            self.library.append(dlg.result_game)
            self._save_library()
            self._render_all()

    def _on_desktop_dropped(self, path):
        import configparser
        cfg = configparser.ConfigParser()
        try:
            cfg.read(path, encoding='utf-8')
        except:
            return
        
        section = None
        for s in cfg.sections():
            if 'desktop' in s.lower() or cfg.has_option(s, 'exec'):
                section = s
                break
        
        if not section:
            for s in cfg.sections():
                if cfg.has_option(s, 'exec') and cfg.has_option(s, 'name'):
                    section = s
                    break
        
        if not section:
            return
        
        name = cfg.get(section, 'name', fallback='Unknown')
        exec_cmd = cfg.get(section, 'exec', fallback='')
        icon = cfg.get(section, 'icon', fallback='')
        comment = cfg.get(section, 'comment', fallback='')
        categories = cfg.get(section, 'categories', fallback='')
        
        import shlex
        import uuid
        args = shlex.split(exec_cmd) if exec_cmd else []
        exe = args[0] if args else ''
        launch_opts = ' '.join(args[1:]) if len(args) > 1 else ''
        
        game = {
            'id': str(uuid.uuid4())[:8],
            'name': name,
            'exec': exe,
            'launchOpts': launch_opts,
            'type': 'custom',
            'img': icon if icon else '',
            'fav': False,
            'played': 0,
            '_added': int(time.time()),
        }
        
        if categories:
            game['categories'] = categories
        
        dlg = GameDialog(self, game)
        if dlg.exec() == QDialog.DialogCode.Accepted and dlg.result_game:
            self.library.append(dlg.result_game)
            self._save_library()
            self._render_all()

    def _open_edit_game(self, g):
        dlg = GameDialog(self, g)
        result = dlg.exec()
        if result == QDialog.DialogCode.Accepted and dlg.result_game:
            idx = next((i for i,x in enumerate(self.library) if x['id']==g['id']), None)
            if idx is not None:
                self.library[idx] = dlg.result_game
            self._save_library()
            self._render_all()
        elif result == 2:
            self.library = [x for x in self.library if x['id'] != g['id']]
            self._save_library()
            self._render_all()

    def _toggle_fav(self, gid):
        g = next((x for x in self.library if x['id']==gid), None)
        if g:
            g['fav'] = not g.get('fav', False)
            self._save_library()
            self._render_all()

    def _load_library(self):
        data = read_json(LIBRARY_FILE, None)
        if data:
            self.library = data
        else:
            self.library = []

    def _save_library(self):
        write_json(LIBRARY_FILE, self.library)

    def _load_settings(self):
        s = read_json(SETTINGS_FILE, {})
        hue = s.get('hue', 207)
        Theme.apply(hue)

    def _save_settings(self):
        write_json(SETTINGS_FILE, {'hue': Theme.hue})

    def _on_hue_changed(self, val):
        Theme.apply(val)
        self._apply_theme()
        self.view_settings.update_swatch(Theme.accent)
        self._save_settings()

    def _apply_theme(self):
        t = Theme
        self.centralWidget().setStyleSheet(f"background: {t.c(t.bg_deep)};")
        self.stack.setStyleSheet(f"background: {t.c(t.bg_deep)};")
        self.topbar.refresh_styles()

        self.hintsbar.setStyleSheet(f"""
            HintsBar {{
                background: {t.c(t.bg_panel)};
                border-top: 1px solid {t.c(t.border)};
            }}
        """)

        for view in [self.view_home, self.view_library,
                     self.view_recent, self.view_favorites]:
            if hasattr(view, '_grid'):
                for card in view._grid._cards:
                    card._refresh_style()
                view._grid.setStyleSheet("QScrollArea { border: none; background: transparent; } QScrollBar:vertical, QScrollBar:horizontal { border: none; background: transparent; }")

        if hasattr(self, '_np_card') and self._np_card is not None:
            self._np_card._refresh_style()

        for widget in self.findChildren(StyledButton):
            widget._refresh()

        for widget in self.findChildren(GameCard):
            widget._refresh_style()

        for widget in self.findChildren(NowPlayingCard):
            widget._refresh_style()

        if hasattr(self.view_settings, 'update_swatch'):
            self.view_settings.update_swatch(Theme.accent)

    def _connect_controller(self):
        try:
            self._controller_thread = SDL2ControllerThread()
            self._controller_thread.nav_signal.connect(self._on_controller_nav)
            self._controller_thread.button_signal.connect(self._on_controller_button)
            self._controller_thread.start()
        except Exception as e:
            print(f"[gameshell] Controller not available: {e}")

    def _on_controller_nav(self, direction):
        if self._active_dialog and hasattr(self._active_dialog, 'handle_controller_nav'):
            self._active_dialog.handle_controller_nav(direction)
            return
        if self._controller_blocked:
            return
        if self.nav_zone != "grid":
            return
        g = self._get_current_grid()
        if direction == "up":
            g.nav_up()
        elif direction == "down":
            g.nav_down()
        elif direction == "left":
            g.nav_left()
        elif direction == "right":
            g.nav_right()

    def _on_controller_button(self, btn):
        if self._active_dialog and hasattr(self._active_dialog, 'handle_controller_button'):
            self._active_dialog.handle_controller_button(btn)
            return
        if self._controller_blocked:
            return
        if btn == 'a':
            if self.nav_zone == "grid":
                self._get_current_grid().activate_focused()
        elif btn == 'b':
            pass
        elif btn == 'x':
            self._open_add_game()
        elif btn == 'y':
            if self.nav_zone == "grid":
                g = self._get_current_grid()
                if 0 <= g._focused_idx < len(g._cards):
                    gid = g._cards[g._focused_idx].gid
                    self._toggle_fav(gid)
        elif btn == 'lb':
            views = ["home", "library", "recent", "favorites", "settings"]
            current_idx = views.index(self.current_view) if self.current_view in views else 0
            prev_idx = (current_idx - 1) % len(views)
            self._switch_view(views[prev_idx])
        elif btn == 'rb':
            views = ["home", "library", "recent", "favorites", "settings"]
            current_idx = views.index(self.current_view) if self.current_view in views else 0
            next_idx = (current_idx + 1) % len(views)
            self._switch_view(views[next_idx])
        elif btn == 'start':
            if self.nav_zone == "grid":
                g = self._get_current_grid()
                if 0 <= g._focused_idx < len(g._cards):
                    gid = g._cards[g._focused_idx].gid
                    self._on_card_clicked(gid)

    def _start_timers(self):
        self._np_timer = QTimer(self)
        self._np_timer.timeout.connect(self._update_np_bar)
        self._np_timer.start(1000)

    def _update_np_bar(self):
        if game_mgr.running:
            elapsed = game_mgr.elapsed()
            self.topbar.set_now_playing(game_mgr.game_info["name"], elapsed)
            if hasattr(self, "_np_card") and self._np_card is not None:
                try:
                    self._np_card.update_time(elapsed)
                except RuntimeError:
                    self._np_card = None
        else:
            was_running = self.topbar._np_name if hasattr(self.topbar, "_np_name") else ""
            self.topbar.set_now_playing(None, "")
            if was_running:
                self._render_all()

    def _get_current_grid(self) -> GameGrid:
        view_map = {
            "home": self.view_home,
            "library": self.view_library,
            "recent": self.view_recent,
            "favorites": self.view_favorites,
        }
        v = view_map.get(self.current_view, self.view_home)
        return v._grid

    def keyPressEvent(self, e):
        from PyQt6.QtGui import QKeyEvent
        if self._np_dialog and self._np_dialog.isVisible():
            if e.key() == Qt.Key.Key_Escape:
                self._np_dialog.hide()
            return

        key = e.key()
        if key == Qt.Key.Key_Escape:
            pass
        elif key == Qt.Key.Key_Q:
            views = ["home", "library", "recent", "favorites", "settings"]
            current_idx = views.index(self.current_view)
            if current_idx > 0:
                self._switch_view(views[current_idx - 1])
        elif key == Qt.Key.Key_E:
            views = ["home", "library", "recent", "favorites", "settings"]
            current_idx = views.index(self.current_view)
            if current_idx < len(views) - 1:
                self._switch_view(views[current_idx + 1])
        elif key in (Qt.Key.Key_Up, Qt.Key.Key_Down, Qt.Key.Key_Left, Qt.Key.Key_Right):
            if self.nav_zone == "grid":
                g = self._get_current_grid()
                if key == Qt.Key.Key_Up:
                    g.nav_up()
                elif key == Qt.Key.Key_Down:
                    g.nav_down()
                elif key == Qt.Key.Key_Left:
                    g.nav_left()
                elif key == Qt.Key.Key_Right:
                    g.nav_right()
        elif key in (Qt.Key.Key_Return, Qt.Key.Key_Space):
            if self.nav_zone == "topbar":
                self.topbar.activate_focused()
        else:
            super().keyPressEvent(e)

    def closeEvent(self, e):
        game_mgr.kill()
        if self._controller_thread:
            self._controller_thread.stop()
            self._controller_thread.wait()
        e.accept()