from PyQt6.QtGui import QColor

class Theme:
    hue = 207

    @classmethod
    def hsl(cls, h, s, l):
        s /= 100; l /= 100
        a = s * min(l, 1 - l)
        def f(n):
            k = (n + h / 30) % 12
            return round(255 * (l - a * max(-1, min(k - 3, 9 - k, 1))))
        return QColor(f(0), f(8), f(4))

    @classmethod
    def apply(cls, h=None):
        if h is not None:
            cls.hue = int(h)
        h = cls.hue
        cls.accent       = cls.hsl(h, 80, 60)
        cls.accent2      = cls.hsl((h + 153) % 360, 70, 55)
        cls.accent_dim   = cls.hsl(h, 70, 35)
        cls.bg_deep      = cls.hsl(h, 45, 7)
        cls.bg_panel     = cls.hsl(h, 40, 10)
        cls.bg_card      = cls.hsl(h, 38, 13)
        cls.bg_card_hover= cls.hsl(h, 38, 17)
        cls.border       = cls.hsl(h, 42, 20)
        cls.text_primary = QColor(232, 240, 255)
        cls.text_secondary=QColor(122, 141, 176)
        cls.text_dim     = cls.hsl(h, 25, 34)
        cls.red          = QColor(255, 68, 102)
        cls.green        = QColor(0, 212, 170)
        cls.yellow       = QColor(255, 204, 0)

    @classmethod
    def c(cls, color: QColor) -> str:
        return color.name()

Theme.apply(207)
