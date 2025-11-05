#!/usr/bin/env python3
"""
Minimal Kivy demo to test FileChooserListView scaling on high-DPI displays.

Usage (macOS/zsh):
  # Try a lower density to make rows smaller
  KIVY_METRICS_DENSITY=1.0 python3 examples/filechooser_demo.py

  # Or slightly larger fonts with the same density
  KIVY_METRICS_DENSITY=1.2 pianoTAB_FONT_SCALE=1.1 python3 examples/filechooser_demo.py

Environment variables:
  - KIVY_METRICS_DENSITY: float. Lower -> smaller dp sizes. Higher -> larger dp sizes.
  - pianoTAB_FONT_SCALE: float. Optional multiplier applied to sp font sizes in this demo.
"""
import os
import sys

# Ensure project root is on path for local imports (if needed)
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

# Default a reasonable density if user didn't set one
os.environ.setdefault("KIVY_METRICS_DENSITY", "1.0")

from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.filechooser import FileChooserListView
from kivy.uix.button import Button
from kivy.clock import Clock
from kivy.metrics import Metrics

class FileChooserDemo(App):
    def build(self):
        font_scale = float(os.environ.get("pianoTAB_FONT_SCALE", "1.0"))
        root = BoxLayout(orientation="vertical", padding=8, spacing=8)

        info = Label(
            text=(
                f"KIVY_METRICS_DENSITY={os.environ.get('KIVY_METRICS_DENSITY')}\n"
                f"Metrics.density={Metrics.density:.2f}  Metrics.fontscale={Metrics.fontscale:.2f}\n"
                f"pianoTAB_FONT_SCALE={font_scale} (demo-only)"
            ),
            size_hint_y=None,
            height=60,
        )
        root.add_widget(info)

        # Basic FileChooserListView (no custom templates)
        self.fc = FileChooserListView(path=os.path.expanduser("~"))
        root.add_widget(self.fc)

        # Button row
        buttons = BoxLayout(size_hint_y=None, height=44, spacing=8)
        buttons.add_widget(Button(text="Close", on_release=lambda *_: self.stop()))
        root.add_widget(buttons)

        # Apply optional demo font scaling after widgets exist
        if font_scale != 1.0:
            Clock.schedule_once(lambda dt: self._apply_font_scale(root, font_scale), 0)

        return root

    def _apply_font_scale(self, widget, scale):
        # Walk the widget tree and multiply font_size for Label and Button
        try:
            if hasattr(widget, "font_size"):
                widget.font_size = widget.font_size * scale
        except Exception:
            pass
        if hasattr(widget, "children"):
            for child in widget.children:
                self._apply_font_scale(child, scale)

if __name__ == "__main__":
    FileChooserDemo().run()
