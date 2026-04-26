from PyQt6.QtGui import QColor, QPalette
from PyQt6.QtWidgets import QApplication

class Theme:
    @classmethod
    def apply(cls):
        accent_hue = 207
        cls.accent       = cls.hsl(accent_hue, 80, 60)
        cls.accent2      = cls.hsl((accent_hue + 153) % 360, 70, 55)
        cls.accent_dim   = cls.hsl(accent_hue, 70, 35)
        cls.bg_deep      = cls.hsl(accent_hue, 45, 7)
        cls.bg_panel     = cls.hsl(accent_hue, 40, 10)
        cls.bg_card      = cls.hsl(accent_hue, 38, 13)
        cls.bg_card_hover= cls.hsl(accent_hue, 38, 17)
        cls.border       = cls.hsl(accent_hue, 42, 20)
        
        app = QApplication.instance()
        if app:
            try:
                palette = app.palette()
                cls.text_primary = palette.color(QPalette.ColorRole.Text)
                cls.text_secondary = palette.color(QPalette.ColorRole.WindowText)
                cls.text_dim = palette.color(QPalette.ColorRole.PlaceholderText)
            except:
                cls.text_primary = QColor(232, 240, 255)
                cls.text_secondary = QColor(122, 141, 176)
                cls.text_dim = QColor(90, 100, 120)
        else:
            cls.text_primary = QColor(232, 240, 255)
            cls.text_secondary = QColor(122, 141, 176)
            cls.text_dim = QColor(90, 100, 120)
        
        cls.red          = QColor(255, 68, 102)
        cls.green        = QColor(0, 212, 170)
        cls.yellow       = QColor(255, 204, 0)

    @classmethod
    def hsl(cls, h, s, l):
        s /= 100; l /= 100
        a = s * min(l, 1 - l)
        def f(n):
            k = (n + h / 30) % 12
            return round(255 * (l - a * max(-1, min(k - 3, 9 - k, 1))))
        return QColor(f(0), f(8), f(4))

    @classmethod
    def c(cls, color: QColor) -> str:
        return color.name()

Theme.apply()