from kivy.uix.widget import Widget
from kivy.graphics import Color, Ellipse
from gui.colors import ACCENT


class KeyboardCursorOverlay(Widget):
    """Transparent overlay above the keyboard panel that draws a single cursor rectangle.

    Rendered as a widget layered after the keyboard panel to ensure it appears on top.
    The rectangle is updated via set_cursor_px(x_px, y_px, w_px, h_px) and reused.
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.size_hint_y = None
        self.height = 0  # overlay height follows parent; pos/size set per update
        self._circle = None
        self._color = None

    def set_cursor_circle(self, x_px: float, y_px: float, diameter_px: float):
        if self._circle is None:
            with self.canvas:
                self._color = Color(*ACCENT)
                self._circle = Ellipse(pos=(x_px, y_px), size=(diameter_px, diameter_px))
        else:
            self._circle.pos = (x_px, y_px)
            self._circle.size = (diameter_px, diameter_px)

__all__ = ["KeyboardCursorOverlay"]
