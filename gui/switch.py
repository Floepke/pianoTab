from kivy.uix.widget import Widget
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.properties import BooleanProperty, ObjectProperty
from kivy.graphics import Color, RoundedRectangle
from kivy.metrics import dp

from gui.colors import DARK, DARK_LIGHTER, LIGHT_DARKER, ACCENT, LIGHT


class MySwitch(BoxLayout):
    """A stylable on/off switch built with Kivy canvas.

    Styling:
    - Off background: DARK_LIGHTER (opposite side color)
    - On background: ACCENT
    - Off text color: DARK
    - On text color: LIGHT_DARKER

    Behavior:
    - Toggles on any tap inside the widget
    - Exposes `active` BooleanProperty and `on_change` callback
    """

    active = BooleanProperty(False)
    on_change = ObjectProperty(None, allownone=True)

    def __init__(self, text_on: str = 'ON', text_off: str = 'FREE', **kwargs):
        super().__init__(orientation='horizontal', size_hint_y=None, height=dp(37), padding=0, spacing=0, **kwargs)
        self.text_on = text_on
        self.text_off = text_off

        # Background container with rounded corners
        with self.canvas.before:
            # Start with off state colors
            self._bg_color = Color(*DARK_LIGHTER)
            self._bg_rect = RoundedRectangle(pos=self.pos, size=self.size, radius=[6])
        self.bind(pos=self._update_bg, size=self._update_bg)

        # Labels for both states (we show one at a time by color styling)
        self._label = Label(text=self.text_off, color=DARK, font_size='16sp', bold=True, halign='center', valign='middle')
        self._label.bind(size=self._sync_label_text_size)
        self.add_widget(self._label)

        # Initial style
        self._apply_style()

        # Toggle on tap
        self.bind(on_touch_down=self._on_touch_down)
        # React to active changes
        self.bind(active=lambda *_: self._apply_style())

    def _update_bg(self, *args):
        self._bg_rect.pos = self.pos
        self._bg_rect.size = self.size

    def _sync_label_text_size(self, *args):
        self._label.text_size = (self._label.width, None)

    def _on_touch_down(self, instance, touch):
        if self.collide_point(*touch.pos):
            self.active = not self.active
            cb = self.on_change
            if cb and callable(cb):
                try:
                    cb(self.active)
                except Exception:
                    pass
            return True
        return False

    def _apply_style(self):
        if self.active:
            # On state styling
            self._bg_color.rgba = ACCENT
            self._label.color = LIGHT
        else:
            # Off state styling
            self._bg_color.rgba = DARK_LIGHTER
            self._label.color = LIGHT_DARKER
        # Update label text to reflect state
        try:
            # Convert current text to appropriate label
            # Keep simple ON/OFF text unless customized
            self._label.text = self.text_on if self.active else self.text_off
        except Exception:
            pass

__all__ = ['MySwitch']
