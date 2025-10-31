"""
Generate a PDF that compares line cap styles and polyline fluency.

Output:
- tests/output/cap_styles_suite.pdf: visual comparison of caps and polylines
- Prints a color → cap-style mapping and layout legend to stdout

Cap styles:
- 0 (butt/flat)   → red
- 1 (round)       → blue
- 2 (projecting)  → green

Sections:
1) Single long lines (thick) with endpoint markers
2) Multi-segment zig-zag polylines built from individual segments
3) A thick open path rendered via PyMuPDFCanvas (round caps) for parity check

Run directly:
    python -m tests.render_cap_styles_suite
"""
from __future__ import annotations
import os
import fitz  # PyMuPDF

# Colors (RGB)
RED = (1, 0, 0)
BLUE = (0, 0, 1)
GREEN = (0, 0.6, 0)
BLACK = (0, 0, 0)
GRAY = (0.5, 0.5, 0.5)

CAP_COLOR_MAP = {
    0: (RED, "red"),
    1: (BLUE, "blue"),
    2: (GREEN, "green"),
}


def draw_endpoint_markers(page, x, y, r=3, color=(0, 0, 0)):
    page.draw_circle(fitz.Point(x, y), r, color=color, fill=color)


def section_title(page, y, text):
    page.insert_text(fitz.Point(40, y), text, fontsize=10, color=BLACK)


def draw_single_lines(page, y_start, width=12):
    section_title(page, y_start - 15, "1) Single long lines (with endpoint markers)")
    y = y_start
    for cap, (color, name) in CAP_COLOR_MAP.items():
        page.draw_line(fitz.Point(60, y), fitz.Point(340, y), color=color, width=width, lineCap=cap)
        draw_endpoint_markers(page, 60, y, r=3, color=GRAY)
        draw_endpoint_markers(page, 340, y, r=3, color=GRAY)
        page.insert_text(fitz.Point(350, y - 3), f"cap={cap} ({name})", fontsize=9, color=BLACK)
        y += 30


def draw_polyline_segments(page, y_start, width=12):
    section_title(page, y_start - 15, "2) Multi-segment polylines (built from individual segments)")
    # polyline points (zig-zag)
    pts = [
        (80, y_start +  0),
        (160, y_start + 20),
        (240, y_start +  0),
        (320, y_start + 20),
    ]
    for i, (cap, (color, name)) in enumerate(CAP_COLOR_MAP.items()):
        y_offset = i * 40
        for a, b in zip(pts[:-1], pts[1:]):
            (x1, y1), (x2, y2) = a, b
            page.draw_line(fitz.Point(x1, y1 + y_offset), fitz.Point(x2, y2 + y_offset),
                           color=color, width=width, lineCap=cap)
        page.insert_text(fitz.Point(350, y_start + y_offset - 3), f"cap={cap} ({name})", fontsize=9, color=BLACK)


def draw_exporter_roundcap_preview(page, y, width_mm=1.2):
    """Approximate our exporter behavior using round-capped segments.
    This is a reference row that should look fluent if round caps are correct.
    """
    section_title(page, y - 15, "3) Exporter-style open path (round-capped segments)")
    import math
    # polyline like above but thicker path width
    pts = [
        (80, y +  0),
        (160, y + 20),
        (240, y +  0),
        (320, y + 20),
    ]
    # Convert mm to pt (1 mm ≈ 2.83465 pt), then apply our exporter 2x scale
    width_pt = float(width_mm) * 72.0 / 25.4
    width_pt *= 2.0
    for (x1, y1), (x2, y2) in zip(pts[:-1], pts[1:]):
        page.draw_line(fitz.Point(x1, y1), fitz.Point(x2, y2), color=(0.2, 0.2, 0.2), width=width_pt, lineCap=1)
    page.insert_text(fitz.Point(350, y - 3), f"round caps (exporter-ref), width_mm={width_mm}", fontsize=9, color=BLACK)


def generate_pdf(out_path: str):
    doc = fitz.open()
    page = doc.new_page(width=420, height=360)

    draw_single_lines(page, y_start=60, width=14)
    draw_polyline_segments(page, y_start=150, width=14)
    draw_exporter_roundcap_preview(page, y=260, width_mm=1.6)

    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    doc.save(out_path)
    return out_path


def main():
    print("Cap style color mapping:")
    for cap, (_, name) in CAP_COLOR_MAP.items():
        print(f"  cap={cap} → color={name}")
    out = os.path.join(os.path.dirname(__file__), 'output', 'cap_styles_suite.pdf')
    path = generate_pdf(out)
    print("Generated:", path)
    print("Legend:")
    print("  1) Single long lines with endpoint markers: compare cap shapes vs markers")
    print("  2) Multi-segment polylines: check fluency at joins for each cap style")
    print("  3) Exporter-style polyline (round caps, scaled width): target fluent look")


if __name__ == '__main__':
    main()
