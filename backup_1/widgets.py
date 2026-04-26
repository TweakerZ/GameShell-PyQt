from PyQt6.QtWidgets import QLabel, QPushButton
from PyQt6.QtGui import QFont, QCursor
from PyQt6.QtCore import Qt
from .theme import Theme

EMOJIS = ['🎮','🕹️','👾','🚀','⚔️','🧙','🔫','🏎️','⚽','🎯','🧩','🐉',
          '💀','🤖','🌍','🏰','🔥','💎','🌌','🦊','🦸','🥷','🛡️','🪄']

def label(text, size=13, bold=False, color=None):
    l = QLabel(text)
    f = QFont("Exo 2", size)
    f.setBold(bold)
    l.setFont(f)
    if color:
        l.setStyleSheet(f"color: {Theme.c(color)};")
    return l

def rajdhani(text, size=16, bold=True):
    l = QLabel(text)
    f = QFont("Rajdhani", size)
    f.setBold(bold)
    l.setFont(f)
    return l

class StyledButton(QPushButton):
    def __init__(self, text, primary=False, danger=False, parent=None):
        super().__init__(text, parent)
        self.primary = primary
        self.danger  = danger
        self._focused = False
        self.setFont(QFont("Exo 2", 11, QFont.Weight.DemiBold))
        self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self._refresh()

    def _refresh(self):
        t = Theme
        if self.primary:
            if self._focused:
                self.setStyleSheet(f"""
                    QPushButton {{
                        background: {t.c(t.accent)};
                        color: white;
                        border: none;
                        border-radius: 6px;
                        padding: 10px 24px;
                        font-weight: bold;
                    }}
                    QPushButton:hover {{
                        background: {t.c(t.accent.lighter(115))};
                    }}
                """)
            else:
                self.setStyleSheet(f"""
                    QPushButton {{
                        background: {t.c(t.accent)};
                        color: white;
                        border: none;
                        border-radius: 6px;
                        padding: 10px 24px;
                    }}
                    QPushButton:hover {{
                        background: {t.c(t.accent.lighter(110))};
                    }}
                """)
        elif self.danger:
            if self._focused:
                self.setStyleSheet(f"""
                    QPushButton {{
                        background: {t.c(t.red)};
                        color: white;
                        border: none;
                        border-radius: 6px;
                        padding: 10px 24px;
                    }}
                    QPushButton:hover {{
                        background: {t.c(t.red.lighter(115))};
                    }}
                """)
            else:
                self.setStyleSheet(f"""
                    QPushButton {{
                        background: transparent;
                        color: {t.c(t.red)};
                        border: 1px solid {t.c(t.red)};
                        border-radius: 6px;
                        padding: 10px 24px;
                    }}
                    QPushButton:hover {{
                        background: rgba({t.red.red()},{t.red.green()},{t.red.blue()},0.15);
                    }}
                """)
        else:
            if self._focused:
                self.setStyleSheet(f"""
                    QPushButton {{
                        background: {t.c(t.accent)};
                        color: white;
                        border: none;
                        border-radius: 6px;
                        padding: 10px 24px;
                    }}
                    QPushButton:hover {{
                        background: {t.c(t.accent.lighter(115))};
                    }}
                """)
            else:
                self.setStyleSheet(f"""
                    QPushButton {{
                        background: {t.c(t.bg_card)};
                        color: {t.c(t.text_primary)};
                        border: none;
                        border-radius: 6px;
                        padding: 10px 24px;
                    }}
                    QPushButton:hover {{
                        background: {t.c(t.bg_card_hover)};
                    }}
                """)

    def set_focused(self, focused):
        self._focused = focused
        self._refresh()

class NavItem(QPushButton):
    def __init__(self, icon, text, view_name):
        super().__init__(f"  {icon}  {text}")
        self.view_name = view_name
        self.setFont(QFont("Exo 2", 12, QFont.Weight.Medium))
        self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.setCheckable(True)
        self._refresh(False)

    def _refresh(self, active):
        t = Theme
        if active:
            self.setStyleSheet(f"""
                QPushButton {{
                    background: qlineargradient(x1:0,y1:0,x2:1,y2:0,
                        stop:0 rgba(26,159,255,0.15), stop:1 transparent);
                    color: {t.c(t.accent)};
                    border: none;
                    border-left: 4px solid {t.c(t.accent)};
                    padding: 12px 24px;
                    text-align: left;
                    font-weight: bold;
                }}
            """)
        else:
            self.setStyleSheet(f"""
                QPushButton {{
                    background: transparent;
                    color: {t.c(t.text_secondary)};
                    border: none;
                    border-left: 4px solid transparent;
                    padding: 12px 24px;
                    text-align: left;
                }}
                QPushButton:hover {{
                    background: rgba(255, 255, 255, 0.02);
                    color: {t.c(t.text_primary)};
                    border-left: 4px solid {t.c(t.accent.darker(150))};
                }}
            """)
