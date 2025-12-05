"""
Standalone PianoKeyboard widget.

You can implement your own drawing logic here. This class is intentionally
minimal and provides a clean place to render a permanent piano keyboard view.
"""

from __future__ import annotations
from kivy.uix.widget import Widget

from kivy.graphics import Color, Rectangle, InstructionGroup
from kivy.properties import NumericProperty, ListProperty, ObjectProperty
from editor import editor
from file.SCORE import SCORE
from utils.canvas import Canvas
from gui.colors import LIGHT_DARKER
from utils.canvas import Canvas
from utils.CONSTANTS import BLACK_KEYS


class PianoKeyboard():
    """Permanent piano keyboard display container.
    """
    def __init__(self, editor: Canvas, score: SCORE, gui=None):
      # mm-based Canvas for keyboard drawing aligned with editor
        self.canvas: Canvas = Canvas(
            width_mm=210.0, height_mm=297.0,
            background_color=LIGHT_DARKER,
            border_color=(0, 0, 0, 1),
            border_width_px=1.0,
            keep_aspect=True,
            scale_to_width=True
        )
        # Ensure the canvas fills its container panel
        try:
            self.canvas.size_hint = (1, 1)
        except Exception:
            pass
        self.score: SCORE = score  # Will be initialized via new_score() or load_score()
        self.gui = gui
        self.editor_canvas: Canvas = editor

        # Align keyboard canvas mm width to editor for consistent x mapping
        try:
            self.canvas.set_size_mm(self.editor_canvas.width_mm, 20.0, reset_scroll=True)
            self.canvas.set_scale_to_width(True)
        except Exception:
            pass

        # Hide scrollbar for this keyboard canvas but keep the object for future width calculations
        try:
            if hasattr(self.canvas, 'custom_scrollbar') and self.canvas.custom_scrollbar:
                # Make it fully invisible and non-reserving
                self.canvas.custom_scrollbar.opacity = 0
                self.canvas.custom_scrollbar.scrollbar_width = 0
                # Ensure layout won't reserve space for an invisible scrollbar
                if hasattr(self.canvas, '_update_layout_and_redraw'):
                    self.canvas._update_layout_and_redraw()
        except Exception:
            pass

        # Keep keyboard canvas fitting the panel height on GUI resize
        try:
            from kivy.clock import Clock
            # Schedule periodic fit updates after layout changes
            def _fit_to_panel(*_):
                # Use current canvas view height to avoid one-frame lag
                view_h_px = float(getattr(self.canvas, '_view_h', 0) or 0)
                px_per_mm = float(getattr(self.canvas, '_px_per_mm', 0.0) or 0.0)
                if view_h_px > 0 and px_per_mm > 0:
                    target_h_mm = max(1.0, view_h_px / px_per_mm)
                    self.canvas.set_size_mm(self.editor_canvas.width_mm, target_h_mm, reset_scroll=True)
            # Bind to split size changes
            if hasattr(self.gui, 'center_split'):
                # Schedule after Kivy lays out sizes to avoid pre-layout values
                self.gui.center_split.bind(size=lambda *_: Clock.schedule_once(_fit_to_panel, 0))
            # Also react to keyboard canvas size changes
            self.canvas.bind(size=lambda *_: Clock.schedule_once(_fit_to_panel, 0))
        except Exception:
            pass

        # Initial draw
        self.redraw_black_keys()

    def redraw_black_keys(self):
        """Draw only black keys aligned with the editor's pitch_to_x in mm."""
        # Guard for editor mapping
        piano = getattr(self.editor_canvas, 'piano_roll_editor', None)
        if not piano or not hasattr(piano, 'pitch_to_x'):
            return

        # Clear previous keys
        self.canvas.delete_by_tag('keyboardBlackKey')

        # Use current canvas height_mm so keys always fill the panel
        key_height_mm = float(getattr(self.canvas, 'height_mm', 20.0))
        key_width_mm = getattr(piano, 'semitone_width', 3.0)
        for pitch in BLACK_KEYS:
            cx_mm = piano.pitch_to_x(pitch)
            x1_mm = cx_mm - (key_width_mm / 2.0)
            self.canvas.add_rectangle(
                x1_mm=x1_mm,
                y1_mm=4.0,
                x2_mm=x1_mm + key_width_mm,
                y2_mm=key_height_mm,
                fill=True,
                fill_color="#15151A",
                outline=False,
                tags=['keyboardBlackKey']
            )

        # draw rectangle around the keyboard no fill
        self.canvas.add_rectangle(
            x1_mm=0.0,
            y1_mm=0.0,
            x2_mm=self.canvas.width_mm,
            y2_mm=key_height_mm,
            fill=False,
            outline=True,
            outline_color="#000000",
            outline_width_px=10.0,
            tags=['keyboardBorder']
        )
        
