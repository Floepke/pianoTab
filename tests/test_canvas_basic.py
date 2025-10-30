"""
Smoke test for utils.canvas.Canvas drawing primitives.

Draws: rectangle (fill/outline), oval (fill/outline), line (solid/dashed),
and polygon (fill/outline). Exports a PNG for quick visual verification.
"""

import os
import sys
from pathlib import Path

# Ensure project root is on sys.path when running this file directly
THIS_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = THIS_DIR.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.clock import Clock

from utils.canvas import Canvas


class CanvasSmokeTestApp(App):
    def build(self):
        root = BoxLayout()
        # Logical A4 page, will scale-to-width in the available space
        self.cv = Canvas(width_mm=210.0, height_mm=148.0,  # landscape-ish to fit more items
                         background_color=(1, 1, 1, 1),
                         border_color=(0, 0, 0, 1),
                         border_width_px=1.0,
                         keep_aspect=True,
                         scale_to_width=True)
        root.add_widget(self.cv)
        Clock.schedule_once(self._draw, 0)
        return root

    def _draw(self, _dt):
        cv = self.cv
        cv.clear()

        # Rectangle: filled red with blue outline
        cv.add_rectangle(10, 10, 60, 40, fill=True, fill_color="#FF0000",
                         outline=True, outline_color="#0000FF", outline_width_mm=0.5)
        # Rectangle: outline only
        cv.add_rectangle(70, 10, 120, 40, fill=False, outline=True,
                         outline_color="#333333", outline_width_mm=0.5)

        # Oval: filled green with dark outline
        cv.add_oval(130, 10, 190, 40, fill=True, fill_color="#00AA00",
                    outline=True, outline_color="#222222", outline_width_mm=0.5)
        # Oval: outline only
        cv.add_oval(10, 50, 60, 80, fill=False, outline=True,
                    outline_color="#000000", outline_width_mm=0.5)

        # Line: solid
        cv.add_line(70, 50, 120, 80, stroke_color="#000000", stroke_width_mm=0.5, stroke_dash=False)
        # Line: dashed
        cv.add_line(70, 65, 120, 65, stroke_color="#000000", stroke_width_mm=0.5, stroke_dash=True, stroke_dash_pattern_mm=(2.0, 2.0))

        # Polygon: filled yellow with black outline (triangle)
        cv.add_polygon([130, 50, 160, 80, 190, 50], fill=True, fill_color="#FFDD00",
                       outline=True, outline_color="#000000", outline_width_mm=0.5)
        # Polygon: outline only (pentagon)
        cv.add_polygon([10, 90, 30, 110, 50, 100, 60, 85, 35, 80], fill=False,
                       outline=True, outline_color="#000000", outline_width_mm=0.5)

        # Save a snapshot for manual verification
        Clock.schedule_once(self._export, 0.2)

    def _export(self, _dt):
        out_dir = os.path.join(os.path.dirname(__file__), 'output')
        os.makedirs(out_dir, exist_ok=True)
        png_path = os.path.join(out_dir, 'canvas_smoketest.png')
        # Export the root window area of the Canvas widget
        self.cv.export_to_png(png_path)
        print(f"Exported canvas smoke test to: {png_path}")
        # Auto-exit after exporting so the test doesn't hang
        self.stop()


if __name__ == '__main__':
    CanvasSmokeTestApp().run()
