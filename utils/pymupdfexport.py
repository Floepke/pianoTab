"""
PyMuPDF-backed Canvas that mirrors drawing operations to a vector PDF.

- Subclasses utils.canvas.Canvas so all Kivy rendering remains unchanged.
- When pdf_mode is True and a page is active (via new_page()), every add_* call
    also draws on the current PDF page using PyMuPDF (fitz).
- Coordinates are in mm with a top-left origin (same as Canvas). Converted to
    PDF points (1/72 in) with a top-left origin as well (no Y inversion).

Notes:
- We keep paths vector and avoid implicit closure by drawing open segments.
- Alpha channels are currently ignored (PDF colors are opaque by default).
- Dashed lines are supported for line and path using on/off lengths in mm.
- Stroke thickness in PDF is scaled by a fixed factor (2.0) to match Canvas.

Usage:
        from utils.pymupdfexport import PyMuPDFCanvas
        cv = PyMuPDFCanvas(width_mm=210.0, height_mm=297.0)
        cv.pdf_mode = True
        cv.new_page()
        cv.add_line(10, 10, 100, 10, stroke_width_mm=0.5)
        cv.add_rectangle(10, 20, 60, 50, outline_color="#FF0000")
        cv.save_pdf("output.pdf")
"""
from __future__ import annotations
from typing import Iterable, List, Tuple, Optional, Dict, Any

try:
    import fitz  # PyMuPDF
except Exception:  # pragma: no cover - optional at runtime until installed
    fitz = None  # type: ignore

from utils.canvas import Canvas


def _mm_to_pt(v_mm: float) -> float:
    return float(v_mm) * 72.0 / 25.4


def _hex_to_rgb(color_hex: str) -> Tuple[float, float, float]:
    # Reuse Canvas parsing to get RGBA, then drop alpha
    r, g, b, _ = Canvas._parse_color(color_hex)
    return r, g, b


class PyMuPDFCanvas(Canvas):
    """Canvas subclass that mirrors drawing to a PDF using PyMuPDF.

    pdf_mode: when True, drawing operations mirror to PDF.
    new_page(): creates a new PDF page using current width_mm/height_mm.
    save_pdf(path): saves the PDF document.
    close_pdf(): closes the PDF document handle.
    """

    def __init__(
        self,
        *,
        pdf_mode: bool = False,
        **kwargs: Any,
    ):
        super().__init__(**kwargs)
        self.pdf_mode: bool = bool(pdf_mode)
        self._doc = fitz.open() if fitz else None
        self._page = None  # type: ignore
        self._pending_cmds: List[Dict[str, Any]] = []
        self._auto_draw: bool = True  # draw immediately when page exists
        # Visual parity tweak: PDF stroke widths can look thinner than Kivy's
        # 1px minimum. Clamp to a configurable minimum point width.
        self.pdf_min_stroke_pt: float = 1.0
        # Fixed: scale all PDF stroke widths to match on-screen appearance.
        # 2.0 empirically matches Canvas rendering thickness.
        self.pdf_stroke_scale: float = 2.0
        # Optional fine-tune for baseline alignment in points (applied to bl_y)
        # Keep default 0.0; adjust if a consistent offset is observed across viewers.
        self.pdf_text_baseline_adjust_pt: float = 0.0

    def _scale_width(self, width_pt: float) -> float:
        """Apply global PDF stroke scaling and minimum width clamp."""
        try:
            scale = float(getattr(self, 'pdf_stroke_scale', 1.0))
        except Exception:
            scale = 1.0
        return max(self.pdf_min_stroke_pt, width_pt * scale)

    # ----- PDF lifecycle -----

    def new_page(self):
        """Create and activate a new PDF page matching current mm size."""
        if not fitz:
            return None
        if self._doc is None:
            self._doc = fitz.open()
        # Flush any pending commands to previous page before switching
        if self._page is not None and self._pending_cmds:
            self._render_commands(self._page, self._pending_cmds)
            self._pending_cmds.clear()
        w_pt = _mm_to_pt(self.width_mm)
        h_pt = _mm_to_pt(self.height_mm)
        self._page = self._doc.new_page(width=w_pt, height=h_pt)
        return self._page

    def save_pdf(self, path: str) -> Optional[str]:
        if not fitz or self._doc is None:
            return None
        # Render any pending commands to current page
        if self._page is not None and self._pending_cmds:
            self._render_commands(self._page, self._pending_cmds)
            self._pending_cmds.clear()
        self._doc.save(path)
        return path

    def close_pdf(self):
        if self._doc is not None:
            try:
                self._doc.close()
            finally:
                self._doc = None
                self._page = None
                self._pending_cmds.clear()

    # ----- Coordinate conversion -----

    def _xy_mm_to_pdf_pt(self, x_mm: float, y_mm_top: float) -> Tuple[float, float]:
        """Convert top-left mm coordinates to PDF points with bottom-left origin."""
        # PyMuPDF page coordinates are top-left origin with y increasing downwards.
        # So we do NOT invert Y: keep top-left mm -> top-left PDF points.
        return _mm_to_pt(x_mm), _mm_to_pt(y_mm_top)

    def _pts_mm_to_pdf(self, pts_mm: Iterable[float]) -> List[Tuple[float, float]]:
        pts = list(map(float, pts_mm))
        out: List[Tuple[float, float]] = []
        for i in range(0, len(pts), 2):
            out.append(self._xy_mm_to_pdf_pt(pts[i], pts[i + 1]))
        return out

    # ----- Overrides that mirror to PDF -----

    def add_rectangle(self, *args, **kwargs) -> int:  # type: ignore[override]
        item_id = super().add_rectangle(*args, **kwargs)
        if not self.pdf_mode:
            return item_id
        x1, y1, x2, y2 = map(float, args[:4])
        fill = bool(kwargs.get('fill', False))
        outline = bool(kwargs.get('outline', True))
        fill_color = kwargs.get('fill_color', '#000000')
        outline_color = kwargs.get('outline_color', '#000000')
        outline_w_mm = float(kwargs.get('outline_width_mm', 0.25))
        cmd = {
            'type': 'rectangle',
            'x1': x1, 'y1': y1, 'x2': x2, 'y2': y2,
            'fill': fill,
            'fill_color': fill_color,
            'outline': outline,
            'outline_color': outline_color,
            'outline_w_mm': outline_w_mm,
        }
        self._mirror(cmd)
        return item_id

    def add_oval(self, *args, **kwargs) -> int:  # type: ignore[override]
        item_id = super().add_oval(*args, **kwargs)
        if not self.pdf_mode:
            return item_id
        x1, y1, x2, y2 = map(float, args[:4])
        fill = bool(kwargs.get('fill', False))
        outline = bool(kwargs.get('outline', True))
        fill_color = kwargs.get('fill_color', '#000000')
        outline_color = kwargs.get('outline_color', '#000000')
        outline_w_mm = float(kwargs.get('outline_width_mm', 0.25))
        cmd = {
            'type': 'oval',
            'x1': x1, 'y1': y1, 'x2': x2, 'y2': y2,
            'fill': fill,
            'fill_color': fill_color,
            'outline': outline,
            'outline_color': outline_color,
            'outline_w_mm': outline_w_mm,
        }
        self._mirror(cmd)
        return item_id

    def add_line(self, *args, **kwargs) -> int:  # type: ignore[override]
        item_id = super().add_line(*args, **kwargs)
        if not self.pdf_mode:
            return item_id
        x1, y1, x2, y2 = map(float, args[:4])
        color = kwargs.get('stroke_color', '#000000')
        width_mm = float(kwargs.get('stroke_width_mm', 0.25))
        dash = bool(kwargs.get('stroke_dash', False))
        dash_mm = tuple(kwargs.get('stroke_dash_pattern_mm', (2.0, 2.0)))
        cmd = {
            'type': 'path',
            'points': [x1, y1, x2, y2],
            'color': color,
            'width_mm': width_mm,
            'dash': dash,
            'dash_mm': dash_mm,
            'close': False,
        }
        self._mirror(cmd)
        return item_id

    def add_polyline(self, points_mm: Iterable[float], *, color: str = '#000000', width_mm: float = 0.25,
                 dash: bool = False, dash_pattern_mm: Tuple[float, float] = (2.0, 2.0), id: Optional[Iterable[str]] = None) -> int:
        item_id = super().add_polyline(points_mm, color=color, width_mm=width_mm, dash=dash,
                                   dash_pattern_mm=dash_pattern_mm, id=id)
        if not self.pdf_mode:
            return item_id
        cmd = {
            'type': 'path',
            'points': list(map(float, points_mm)),
            'color': color,
            'width_mm': float(width_mm),
            'dash': bool(dash),
            'dash_mm': (float(dash_pattern_mm[0]), float(dash_pattern_mm[1])),
            'close': False,
        }
        self._mirror(cmd)
        return item_id

    def add_polygon(self, points_mm: Iterable[float], *, fill: bool = False, fill_color: str = '#000000',
                    outline: bool = True, outline_color: str = '#000000', outline_width_mm: float = 0.25,
                    id: Optional[Iterable[str]] = None) -> int:
        item_id = super().add_polygon(points_mm, fill=fill, fill_color=fill_color, outline=outline,
                                      outline_color=outline_color, outline_width_mm=outline_width_mm, id=id)
        if not self.pdf_mode:
            return item_id
        cmd = {
            'type': 'polygon',
            'points': list(map(float, points_mm)),
            'fill': bool(fill),
            'fill_color': fill_color,
            'outline': bool(outline),
            'outline_color': outline_color,
            'outline_w_mm': float(outline_width_mm),
        }
        self._mirror(cmd)
        return item_id

    def add_text(self, text: str, x_mm: float, y_mm: float, font_size_pt: float, angle_deg: float = 0.0,
                 anchor: str = 'top_left', color: str = '#000000', id: Optional[Iterable[str]] = None) -> int:  # type: ignore[override]
        item_id = super().add_text(text, x_mm, y_mm, font_size_pt, angle_deg, anchor, color, id)
        if not self.pdf_mode:
            return item_id
        cmd = {
            'type': 'text',
            'text': str(text),
            'x': float(x_mm),
            'y': float(y_mm),
            'font_pt': float(font_size_pt),
            'angle_deg': float(angle_deg),
            'anchor': str(anchor or 'top_left'),
            'color': color,
        }
        self._mirror(cmd)
        return item_id

    # ----- Internal: mirroring -----

    def _mirror(self, cmd: Dict[str, Any]):
        # Always buffer
        self._pending_cmds.append(cmd)
        # Optionally draw immediately if a page exists
        if self.pdf_mode and self._auto_draw and self._page is not None and fitz:
            try:
                self._render_commands(self._page, [cmd])
            except Exception:
                # Soft-fail to keep UI drawing
                pass

    def _render_commands(self, page, cmds: List[Dict[str, Any]]):
        if not fitz:
            return
        # We'll create shapes per logical operation group
        page_h_pt = _mm_to_pt(self.height_mm)

        for c in cmds:
            t = c['type']
            if t == 'rectangle':
                shape = page.new_shape()
                x1, y1 = self._xy_mm_to_pdf_pt(c['x1'], c['y1'])
                x2, y2 = self._xy_mm_to_pdf_pt(c['x2'], c['y2'])
                # Normalize to bottom-left (x,y) and size in pt
                x_min = min(x1, x2)
                y_min = min(y1, y2)
                w = abs(x2 - x1)
                h = abs(y2 - y1)
                rect = fitz.Rect(x_min, y_min, x_min + w, y_min + h)
                shape.draw_rect(rect)
                stroke_rgb = _hex_to_rgb(c['outline_color']) if c.get('outline', True) else None
                fill_rgb = _hex_to_rgb(c['fill_color']) if c.get('fill', False) else None
                width_pt = _mm_to_pt(c.get('outline_w_mm', 0.25))
                shape.finish(color=stroke_rgb, fill=fill_rgb, width=self._scale_width(width_pt), lineCap=1)
                shape.commit()
            elif t == 'oval':
                shape = page.new_shape()
                x1, y1 = self._xy_mm_to_pdf_pt(c['x1'], c['y1'])
                x2, y2 = self._xy_mm_to_pdf_pt(c['x2'], c['y2'])
                x_min = min(x1, x2)
                y_min = min(y1, y2)
                w = abs(x2 - x1)
                h = abs(y2 - y1)
                rect = fitz.Rect(x_min, y_min, x_min + w, y_min + h)
                shape.draw_oval(rect)
                stroke_rgb = _hex_to_rgb(c['outline_color']) if c.get('outline', True) else None
                fill_rgb = _hex_to_rgb(c['fill_color']) if c.get('fill', False) else None
                width_pt = _mm_to_pt(c.get('outline_w_mm', 0.25))
                shape.finish(color=stroke_rgb, fill=fill_rgb, width=self._scale_width(width_pt), lineCap=1)
                shape.commit()
            elif t == 'path':
                pts_pairs = self._pts_mm_to_pdf(c['points'])
                if not pts_pairs:
                    continue
                stroke_rgb = _hex_to_rgb(c.get('color', '#000000'))
                width_pt = _mm_to_pt(c.get('width_mm', 0.25))
                if c.get('dash'):
                    dm = c.get('dash_mm', (2.0, 2.0))
                    on_pt, off_pt = _mm_to_pt(dm[0]), _mm_to_pt(dm[1])
                    self._pdf_draw_dashed_polyline(page, pts_pairs, stroke_rgb, width_pt, on_pt, off_pt, close=c.get('close', False))
                else:
                    # Draw each segment directly with page.draw_line using round caps.
                    for i in range(len(pts_pairs) - 1):
                        p1 = pts_pairs[i]
                        p2 = pts_pairs[i + 1]
                        page.draw_line(fitz.Point(*p1), fitz.Point(*p2), color=stroke_rgb, width=self._scale_width(width_pt), lineCap=1)
            elif t == 'polygon':
                shape = page.new_shape()
                pts = self._pts_mm_to_pdf(c['points'])
                if len(pts) < 3:
                    continue
                shape.draw_polyline(pts)
                # Close polygon
                shape.draw_line(fitz.Point(*pts[-1]), fitz.Point(*pts[0]))
                stroke_rgb = _hex_to_rgb(c['outline_color']) if c.get('outline', True) else None
                fill_rgb = _hex_to_rgb(c['fill_color']) if c.get('fill', False) else None
                width_pt = _mm_to_pt(c.get('outline_w_mm', 0.25))
                shape.finish(color=stroke_rgb, fill=fill_rgb, width=self._scale_width(width_pt), lineCap=1)
                shape.commit()
            elif t == 'text':
                # Compute text metrics in pt for anchoring
                txt = c.get('text', '')
                font_pt = float(c.get('font_pt', 12.0))
                color_rgb = _hex_to_rgb(c.get('color', '#000000'))
                # Measure actual text bbox using a temporary TextWriter to get accurate height
                try:
                    font_obj = fitz.Font("cour")
                except Exception:
                    font_obj = None
                try:
                    tw_measure = fitz.TextWriter(page.rect)
                    # place baseline at y=font_pt to ensure positive rect
                    tw_measure.append(fitz.Point(0, font_pt), txt, font=font_obj, fontsize=font_pt)
                    measure_rect = tw_measure.text_rect
                    w_pt = float(measure_rect.width)
                    h_pt = float(measure_rect.height)
                except Exception:
                    try:
                        w_pt = float(page.get_text_length(txt, fontname="courier", fontsize=font_pt))
                    except Exception:
                        w_pt = max(0.0, len(txt) * font_pt * 0.6)
                    h_pt = font_pt
                # Anchor point (top-left coordinate system)
                ax_pt, ay_pt = self._xy_mm_to_pdf_pt(c.get('x', 0.0), c.get('y', 0.0))
                # Offset from anchor to top-left of unrotated text box
                off_x, off_y = self._anchor_offsets_pt(c.get('anchor', 'top_left'), w_pt, h_pt)
                tl_x = ax_pt + off_x
                tl_y = ay_pt + off_y
                # TextWriter expects baseline bottom-left position
                bl_x = tl_x
                bl_y = tl_y + h_pt
                rot = float(c.get('angle_deg', 0.0))
                try:
                    # Prepare a TextWriter for arbitrary-angle rotation via morph
                    tw = fitz.TextWriter(page.rect)
                    bl_y_adj = bl_y + float(getattr(self, 'pdf_text_baseline_adjust_pt', 0.0))
                    tw.append(fitz.Point(bl_x, bl_y_adj), txt, font=font_obj, fontsize=font_pt)
                    # Rotate clockwise by angle_deg around the anchor point (note: PyMuPDF uses CCW)
                    m = fitz.Matrix(1, 0, 0, 1).prerotate(-rot)
                    tw.write_text(page, color=color_rgb, morph=(fitz.Point(ax_pt, ay_pt), m))
                except Exception as _e:
                    # Fallback: no rotation, draw at baseline
                    page.insert_text(fitz.Point(bl_x, bl_y), txt, fontsize=font_pt, fontname="courier", color=color_rgb)

    # ----- Dashed polyline drawing (manual) -----

    def _pdf_draw_dashed_polyline(self, page, pts: List[Tuple[float, float]], color: Tuple[float, float, float], width_pt: float,
                               on_pt: float, off_pt: float, *, close: bool = False):
        """Draw dashed polyline with continuous dash phase across segments."""
        if len(pts) < 2:
            return
        # If dash pattern is invalid, draw solid
        if on_pt <= 0 or off_pt < 0:
            for i in range(len(pts) - 1):
                p1, p2 = pts[i], pts[i + 1]
                page.draw_line(fitz.Point(*p1), fitz.Point(*p2), color=color, width=self._scale_width(width_pt), lineCap=1)
            if close:
                p1, p2 = pts[-1], pts[0]
                page.draw_line(fitz.Point(*p1), fitz.Point(*p2), color=color, width=self._scale_width(width_pt), lineCap=1)
            return

        points = list(pts)
        if close:
            points = points + [points[0]]

        eps = 1e-9
        dash_on = True
        dash_remaining = on_pt  # remaining length in the current on/off run

        for i in range(len(points) - 1):
            x1, y1 = points[i]
            x2, y2 = points[i + 1]
            dx = x2 - x1
            dy = y2 - y1
            seg_len = (dx * dx + dy * dy) ** 0.5
            if seg_len <= eps:
                continue
            ux = dx / seg_len
            uy = dy / seg_len

            pos = 0.0
            while pos < seg_len - eps:
                run = min(dash_remaining, seg_len - pos)
                if dash_on and run > eps:
                    sx = x1 + ux * pos
                    sy = y1 + uy * pos
                    ex = x1 + ux * (pos + run)
                    ey = y1 + uy * (pos + run)
                    page.draw_line(
                        fitz.Point(sx, sy),
                        fitz.Point(ex, ey),
                        color=color,
                        width=self._scale_width(width_pt),
                        lineCap=1
                    )
                pos += run
                dash_remaining -= run
                if dash_remaining <= eps:
                    dash_on = not dash_on
                    dash_remaining = on_pt if dash_on else off_pt

    @staticmethod
    def _anchor_offsets_pt(anchor: str, w_pt: float, h_pt: float) -> Tuple[float, float]:
        """Offsets from anchor point to top-left of a text rectangle in PDF points.

        Coordinates use top-left origin with Y increasing downward.
        """
        a = (anchor or 'top_left').strip().lower()
        mapping = {
            'top_left': (0.0, 0.0), 'tl': (0.0, 0.0),
            'top': (-w_pt / 2.0, 0.0), 'tc': (-w_pt / 2.0, 0.0),
            'top_right': (-w_pt, 0.0), 'tr': (-w_pt, 0.0),
            'left': (0.0, -h_pt / 2.0), 'cl': (0.0, -h_pt / 2.0),
            'center': (-w_pt / 2.0, -h_pt / 2.0), 'cc': (-w_pt / 2.0, -h_pt / 2.0),
            'right': (-w_pt, -h_pt / 2.0), 'cr': (-w_pt, -h_pt / 2.0),
            'bottom_left': (0.0, -h_pt), 'bl': (0.0, -h_pt),
            'bottom': (-w_pt / 2.0, -h_pt), 'bc': (-w_pt / 2.0, -h_pt),
            'bottom_right': (-w_pt, -h_pt), 'br': (-w_pt, -h_pt),
        }
        return mapping.get(a, (0.0, 0.0))
