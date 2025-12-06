from __future__ import annotations

from typing import Optional
from kivy.uix.widget import Widget
from kivy.graphics import Color, Rectangle, Ellipse
from kivy.clock import Clock

from gui.colors import DARK, LIGHT, LIGHT_DARKER, ACCENT
from utils.CONSTANTS import BLACK_KEYS


class KeyboardPanel(Widget):
    """Bottom keyboard panel that draws above the editor, separate from culling.

    It uses Kivy canvas instructions (pixels) and updates positions on resize/scroll.
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.size_hint_y = None
        self.height = 100
        self._editor = None
        self._bg_rect = None
        self._top_border_color = None
        self._top_border_rect = None
        self._key_rects = {}
        self._refresh_ev = None
        self._cursor_rect = None
        self._last_cursor_pitch = None
        self._key_w_px = None
        self._key_h_px = None
        self._bottom_margin_px = None
        with self.canvas:
            # Background color (light)
            self._bg_color = Color(*LIGHT_DARKER)  # #E5E5EA
            self._bg_rect = Rectangle(pos=self.pos, size=(self.width, self.height))
        with self.canvas:
            # Thin top border that acts like a non-moveable sash
            self._top_border_color = Color(*DARK)
            self._top_border_rect = Rectangle(pos=self.pos, size=(self.width, 2))
        self.bind(pos=self._sync_bg, size=self._sync_bg)

    def attach_editor(self, editor):
        self._editor = editor
        # initial draw
        self.refresh()
        # Periodically refresh to follow scroll/zoom until explicit events exist
        if self._refresh_ev is None:
            self._refresh_ev = Clock.schedule_interval(lambda dt: self.refresh(), 0.1)

    def set_height_px(self, h: int):
        self.height = max(0, int(h))
        self.refresh()

    def _sync_bg(self, *args):
        if self._bg_rect is not None:
            self._bg_rect.pos = self.pos
            self._bg_rect.size = (self.width, self.height)
        # keep keys in sync when the panel itself resizes/moves
        self.refresh()

    def refresh(self):
        ed = self._editor
        if ed is None or not hasattr(ed, 'canvas'):
            return
        cv = ed.canvas
        px_per_mm = float(getattr(cv, '_px_per_mm', 0.0) or 0.0)
        view_x = float(getattr(cv, '_view_x', 0) or 0)
        view_w = float(getattr(cv, '_view_w', 0) or 0)
        if px_per_mm <= 0.0 or view_w <= 0.0:
            return

        # Stretch background to match editor view width plus scrollbar, anchored left
        extra_w = 0
        try:
            sb = getattr(cv, 'custom_scrollbar', None)
            if sb is not None:
                extra_w = int(getattr(sb, 'scrollbar_width', 0) or 0)
        except Exception:
            extra_w = 0
        self._bg_rect.pos = (view_x, self.y)
        self._bg_rect.size = (view_w + extra_w, self.height)

        # Update top border to span the same width and sit at the panel's top
        if self._top_border_rect is not None:
            self._top_border_rect.pos = (view_x, self.y + self.height - self._top_border_rect.size[1])
            self._top_border_rect.size = (view_w + extra_w, self._top_border_rect.size[1])

        # Draw/update black keys as rectangles within this panel
        # Key width derived from editor spacing (slightly wider for clarity)
        semitone_w_mm = float(getattr(ed, 'semitone_width', 3.0))
        key_w_px = (semitone_w_mm * px_per_mm if px_per_mm > 0 else 12.0) * 1.15
        key_h_px = int(self.height / 3 * 2)
        bottom_margin_px = self.height - key_h_px
        y = self.y + bottom_margin_px
        # cache geometry for fast cursor updates
        self._key_w_px = key_w_px
        self._key_h_px = key_h_px
        self._bottom_margin_px = bottom_margin_px

            # Cursor highlight is updated by the active tool on mouse move

        # Create or update key rectangles
        # Silent refresh; remove debug logs
        for pitch in BLACK_KEYS:
            try:
                cx_mm = ed.pitch_to_x(pitch)
            except Exception:
                continue
            cx_px, _ = cv._mm_to_px_point(cx_mm, 0.0)
            x1_px = float(cx_px) - (key_w_px / 2.0)
            rect = self._key_rects.get(pitch)
            if rect is None:
                with self.canvas:
                    Color(*DARK)
                    rect = Rectangle(pos=(x1_px, y), size=(key_w_px, key_h_px))
                    self._key_rects[pitch] = rect
            else:
                rect.pos = (x1_px, y)
                rect.size = (key_w_px, key_h_px)

        # Do not update cursor here; active tool triggers it on mouse move

    def _update_cursor(self):
        ed = self._editor
        if ed is None:
            return
        
        cv = ed.canvas
        px_per_mm = float(getattr(cv, '_px_per_mm', 0.0) or 0.0)
        view_x = float(getattr(cv, '_view_x', 0) or 0)
        if px_per_mm <= 0.0:
            return

        # Update cursor position based on editor's current pitch
        cursor_pitch = getattr(ed, 'cursor_pitch', None)
        if cursor_pitch is None:
            return
        # fast path: only update on pitch change
        if self._last_cursor_pitch == cursor_pitch:
            return
        
        # Calculate cursor key-sized highlight position
        try:
            cursor_x_mm = ed.pitch_to_x(cursor_pitch)
        except Exception:
            return
        cursor_x_px, _ = cv._mm_to_px_point(cursor_x_mm, 0.0)
        key_w_px = self._key_w_px if self._key_w_px is not None else (float(getattr(ed, 'semitone_width', 3.0)) * px_per_mm if px_per_mm > 0 else 12.0) * 1.15
        key_h_px = self._key_h_px if self._key_h_px is not None else int(self.height * (2.0 / 3.0))
        cursor_y = self.y + (self._bottom_margin_px if self._bottom_margin_px is not None else (self.height - key_h_px))
        x1_px = float(cursor_x_px) - (key_w_px / 2.0)

        # Update cursor key highlight rectangle
        if self._cursor_rect is None:
            with self.canvas:
                Color(*ACCENT)
                self._cursor_rect = Rectangle(pos=(x1_px, cursor_y), size=(key_w_px, key_h_px))
        else:
            self._cursor_rect.pos = (x1_px, cursor_y)
            self._cursor_rect.size = (key_w_px, key_h_px)

        self._last_cursor_pitch = cursor_pitch