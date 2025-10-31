from typing import List, Tuple, Optional, Dict, Any, Iterable
import math

from kivy.uix.widget import Widget
from kivy.graphics import Color, Rectangle, Line, Ellipse, Mesh, InstructionGroup, PushMatrix, PopMatrix, Rotate, Translate
from kivy.core.text import Label as CoreLabel
from kivy.graphics.scissor_instructions import ScissorPush, ScissorPop
from kivy.clock import Clock


class Canvas(Widget):
    """
    Tkinter-like Canvas for Kivy using millimeters and top-left origin.

    - Drawable area in mm: width_mm x height_mm
    - Top-left origin (0,0) is top-left of the drawable area (like Tkinter)
    - Auto-fit to widget size with aspect ratio preserved (letterboxing)
    - Background color and border
    - id/IDs like Tkinter
    - Click detection, returns top-most item id

    Units:
    - All coordinates/sizes passed to add_* are in millimeters (mm) relative to top-left.

    Events:
    - bind(on_item_click=callback) -> callback(self, item_id, touch, pos_mm)
    """

    __events__ = ('on_item_click',)

    def __init__(
        self,
        width_mm: float = 210.0,
        height_mm: float = 297.0,
        background_color: Tuple[float, float, float, float] = (1, 1, 1, 1),
        border_color: Tuple[float, float, float, float] = (0, 0, 0, 1),
        border_width_px: float = 1.0,
        keep_aspect: bool = True,
        scale_to_width: bool = True,
        **kwargs
    ):
        super().__init__(**kwargs)

        # Public attributes
        self.width_mm: float = float(width_mm)
        self.height_mm: float = float(height_mm)
        self.background_color: Tuple[float, float, float, float] = background_color
        self.border_color: Tuple[float, float, float, float] = border_color
        self.border_width_px: float = border_width_px
        self.keep_aspect: bool = keep_aspect
        self.scale_to_width: bool = scale_to_width

        # Viewport (in device px) where the mm-canvas is rendered
        self._view_x: int = 0
        self._view_y: int = 0
        self._view_w: int = 0
        self._view_h: int = 0

        # Scaling (px per mm)
        self._px_per_mm: float = 1.0

        # Vertical scroll (in px) when content height exceeds widget height in scale_to_width mode
        self._scroll_px: float = 0.0

        # Drawing containers
        with self.canvas:
            # Clipping to view area
            self._scissor = ScissorPush(x=0, y=0, width=0, height=0)

            # Background for visible viewport (widget area)
            self._bg_color_instr = Color(*self.background_color)
            self._bg_rect = Rectangle(pos=(0, 0), size=(0, 0))

            # Parent group for items
            self._items_group = InstructionGroup()
            self.canvas.add(self._items_group)

            # Border drawn inside scissor (so it clips)
            self._border_color_instr = Color(*self.border_color)
            self._border_line = Line(rectangle=(0, 0, 0, 0), width=self.border_width_px)

            # Close clipping
            self._scissor_pop = ScissorPop()

        # Items and id
        self._next_id: int = 1
        self._items: Dict[int, Dict[str, Any]] = {}
        self._id: Dict[str, set] = {}
        self._draw_order: List[int] = []  # z-order (append = on top)

        # Defer expensive redraws during resize
        self._resched = None
        self.bind(pos=self._schedule_layout, size=self._schedule_layout)

        # Initial layout
        self._update_layout_and_redraw()

    # ---------- Public API (Tkinter-like) ----------

    def clear(self):
        """Remove all items."""
        self._items_group.clear()
        self._items.clear()
        self._id.clear()
        self._draw_order.clear()

    def add_rectangle(
        self,
        x1_mm: float,
        y1_mm: float,
        x2_mm: float,
        y2_mm: float,
        *,
        fill: bool = False,
        fill_color: str = "#000000",
        outline: bool = True,
        outline_color: str = "#000000",
        outline_width_mm: float = 0.25,
        id: Optional[Iterable[str]] = None,
    ) -> int:
        """Add a rectangle by two corners (top-left and bottom-right) in mm.

        Colors are hex strings like '#RRGGBB' (alpha assumed 1.0).
        """
        item_id = self._new_item_id()
        group = InstructionGroup()
        self._items_group.add(group)

        # Normalize to top-left (x,y) and size
        x_min = float(min(x1_mm, x2_mm))
        y_min = float(min(y1_mm, y2_mm))
        w_mm = abs(float(x2_mm) - float(x1_mm))
        h_mm = abs(float(y2_mm) - float(y1_mm))

        self._items[item_id] = {
            'type': 'rectangle',
            'group': group,
            'x_mm': x_min,
            'y_mm': y_min,
            'w_mm': w_mm,
            'h_mm': h_mm,
            'fill': bool(fill),
            'fill_color': self._parse_color(fill_color),
            'outline': bool(outline),
            'outline_color': self._parse_color(outline_color),
            'outline_w_mm': float(outline_width_mm),
            'id': set(id or []),
        }
        self._register_id(item_id)
        self._draw_order.append(item_id)
        self._redraw_item(item_id)
        return item_id

    def add_oval(
        self,
        x1_mm: float,
        y1_mm: float,
        x2_mm: float,
        y2_mm: float,
        *,
        fill: bool = False,
        fill_color: str = "#000000",
        outline: bool = True,
        outline_color: str = "#000000",
        outline_width_mm: float = 0.25,
        id: Optional[Iterable[str]] = None,
    ) -> int:
        """Add an oval (ellipse) inscribed in the rectangle defined by two corners in mm.

        Colors are hex strings like '#RRGGBB' (alpha assumed 1.0).
        """
        item_id = self._new_item_id()
        group = InstructionGroup()
        self._items_group.add(group)

        x_min = float(min(x1_mm, x2_mm))
        y_min = float(min(y1_mm, y2_mm))
        w_mm = abs(float(x2_mm) - float(x1_mm))
        h_mm = abs(float(y2_mm) - float(y1_mm))

        self._items[item_id] = {
            'type': 'oval',
            'group': group,
            'x_mm': x_min,
            'y_mm': y_min,
            'w_mm': w_mm,
            'h_mm': h_mm,
            'fill': bool(fill),
            'fill_color': self._parse_color(fill_color),
            'outline': bool(outline),
            'outline_color': self._parse_color(outline_color),
            'outline_w_mm': float(outline_width_mm),
            'id': set(id or []),
        }
        self._register_id(item_id)
        self._draw_order.append(item_id)
        self._redraw_item(item_id)
        return item_id

    def add_line(
        self,
        x1_mm: float,
        y1_mm: float,
        x2_mm: float,
        y2_mm: float,
        *,
        stroke_color: str = "#000000",
        stroke_width_mm: float = 0.25,
        stroke_dash: bool = False,
        stroke_dash_pattern_mm: Tuple[float, float] = (2.0, 2.0),
        id: Optional[Iterable[str]] = None,
    ) -> int:
        """Add a straight line segment between two points in mm.

        Colors are hex strings like '#RRGGBB'. Dash pattern is in mm.
        """
        item_id = self._new_item_id()
        group = InstructionGroup()
        self._items_group.add(group)

        self._items[item_id] = {
            'type': 'line',
            'group': group,
            'points_mm': [float(x1_mm), float(y1_mm), float(x2_mm), float(y2_mm)],
            'color': self._parse_color(stroke_color),
            'w_mm': float(stroke_width_mm),
            'smooth': False,
            'close': False,
            'dash': bool(stroke_dash),
            'dash_mm': (float(stroke_dash_pattern_mm[0]), float(stroke_dash_pattern_mm[1])),
            'id': set(id or []),
        }
        self._register_id(item_id)
        self._draw_order.append(item_id)
        self._redraw_item(item_id)
        return item_id

    def add_polyline(
        self,
        points_mm: Iterable[float],
        *,
        color: str = "#000000",
        width_mm: float = 0.25,
        dash: bool = False,
        dash_pattern_mm: Tuple[float, float] = (2.0, 2.0),
        id: Optional[Iterable[str]] = None,
    ) -> int:
        """Add a polyline/path defined by a list of mm points [x0,y0,x1,y1,...].

        Raises ValueError if points list length is odd or < 4.
        """
        pts = list(map(float, points_mm))
        if len(pts) < 4 or len(pts) % 2 != 0:
            raise ValueError("add_path requires an even-length list with at least two points")
        item_id = self._new_item_id()
        group = InstructionGroup()
        self._items_group.add(group)

        self._items[item_id] = {
            'type': 'path',
            'group': group,
            'points_mm': pts,
            'color': self._parse_color(color),
            'w_mm': float(width_mm),
            'dash': bool(dash),
            'dash_mm': (float(dash_pattern_mm[0]), float(dash_pattern_mm[1])),
            'id': set(id or []),
        }
        self._register_id(item_id)
        self._draw_order.append(item_id)
        self._redraw_item(item_id)
        return item_id

    def add_polygon(
        self,
        points_mm: Iterable[float],
        *,
        fill: bool = False,
        fill_color: str = "#000000",
        outline: bool = True,
        outline_color: str = "#000000",
        outline_width_mm: float = 0.25,
        id: Optional[Iterable[str]] = None,
    ) -> int:
        """
        Add a polygon. Points in mm [x0,y0, x1,y1, ...].
        Fill uses a triangle fan (suitable for convex polygons).
        """
        pts = list(map(float, points_mm))
        if len(pts) < 6:
            raise ValueError("add_polygon requires at least 3 points")
        item_id = self._new_item_id()
        group = InstructionGroup()
        self._items_group.add(group)

        self._items[item_id] = {
            'type': 'polygon',
            'group': group,
            'points_mm': pts,
            'fill': bool(fill),
            'fill_color': self._parse_color(fill_color),
            'outline': bool(outline),
            'outline_color': self._parse_color(outline_color),
            'outline_w_mm': float(outline_width_mm),
            'id': set(id or []),
        }
        self._register_id(item_id)
        self._draw_order.append(item_id)
        self._redraw_item(item_id)
        return item_id

    def add_text(
        self,
        text: str,
        x_mm: float,
        y_mm: float,
        font_size_pt: float,
        angle_deg: float = 0.0,
        anchor: str = "top_left",
        color: str = "#000000",
        id: Optional[Iterable[str]] = None,
    ) -> int:
        """Add a text label.

        Parameters
        - text: string content
        - x_mm, y_mm: anchor position in mm (top-left origin, like other add_* calls)
        - font_size_pt: font size in points (pt)
        - angle_deg: rotation in degrees (clockwise in the canvas' top-left system)
        - anchor: where the (x,y) refers to. Supported values (case-insensitive):
            'top_left', 'top', 'top_right', 'left', 'center', 'right',
            'bottom_left', 'bottom', 'bottom_right'. Abbreviations like 'tl', 'tc', 'tr',
            'cl', 'cc', 'cr', 'bl', 'bc', 'br' are also accepted.
        - color: hex string like '#RRGGBB' or '#RRGGBBAA'

        Notes
        - Font is fixed to 'Courier New' in pianoTab. you can only use one good readable font.
        - Hit-testing uses the un-rotated bounding box (rotation ignored for clicks).
        """
        item_id = self._new_item_id()
        group = InstructionGroup()
        self._items_group.add(group)

        self._items[item_id] = {
            'type': 'text',
            'group': group,
            'text': str(text),
            'x_mm': float(x_mm),
            'y_mm': float(y_mm),
            'font_pt': float(font_size_pt),
            'angle_deg': float(angle_deg),
            'anchor': str(anchor or 'top_left'),
            'color': self._parse_color(color),
            'id': set(id or []),
        }
        self._register_id(item_id)
        self._draw_order.append(item_id)
        self._redraw_item(item_id)
        return item_id

    # ----- id/IDs -----

    def find_by_id(self, item_id: int) -> Optional[Dict[str, Any]]:
        """Return the stored item dict by id."""
        return self._items.get(item_id)

    def add_tag(self, item_id: int, tag: str):
        if item_id in self._items:
            self._items[item_id]['id'].add(tag)
            self._id.setdefault(tag, set()).add(item_id)

    def remove_by_id(self, item_id: int, tag: str):
        if item_id in self._items:
            self._items[item_id]['id'].discard(tag)
        if tag in self._id:
            self._id[tag].discard(item_id)
            if not self._id[tag]:
                del self._id[tag]

    def find_by_tag(self, tag: str) -> List[int]:
        return sorted(self._id.get(tag, set()))

    def delete(self, item_id: int):
        """Delete an item by id."""
        item = self._items.pop(item_id, None)
        if not item:
            return
        group: InstructionGroup = item['group']
        self._items_group.remove(group)
        for tag in list(item.get('id', [])):
            self.remove_by_id(item_id, tag)
        if item_id in self._draw_order:
            self._draw_order.remove(item_id)

    # ----- Background / properties -----

    def set_background_color(self, rgba: Tuple[float, float, float, float]):
        self.background_color = rgba
        self._bg_color_instr.rgba = rgba

    def set_border(self, color: Tuple[float, float, float, float], width_px: float = 1.0):
        self.border_color = color
        self.border_width_px = width_px
        self._border_color_instr.rgba = color
        self._border_line.width = width_px

    def set_size_mm(self, width_mm: float, height_mm: float, *, reset_scroll: bool = False):
        """Change the logical canvas size (in mm) and relayout/redraw.

        If reset_scroll is True, vertical scroll offset resets to 0.
        """
        self.width_mm = float(width_mm)
        self.height_mm = float(height_mm)
        if reset_scroll:
            self._scroll_px = 0.0
        self._update_layout_and_redraw()

    def set_scale_to_width(self, enabled: bool):
        """Enable/disable scale-to-width + vertical scrolling behavior."""
        self.scale_to_width = bool(enabled)
        if not self.scale_to_width:
            # Reset scroll when disabling
            self._scroll_px = 0.0
        self._update_layout_and_redraw()

    # ----- Events -----

    def on_item_click(self, item_id: Optional[int], touch, pos_mm: Tuple[float, float]):
        """Default handler (no-op). Bind to this event to handle clicks."""
        pass

    def on_touch_down(self, touch):
        # Only handle if inside our widget and within the view area
        if not self.collide_point(*touch.pos):
            return super().on_touch_down(touch)

        if not self._point_in_view_px(*touch.pos):
            return super().on_touch_down(touch)

        # Mouse wheel vertical scrolling in scale_to_width mode
        if self.scale_to_width and hasattr(touch, 'button') and touch.button in ('scrollup', 'scrolldown'):
            content_h = self._content_height_px()
            if content_h > self._view_h:  # scrolling only if content taller than viewport
                step = 40  # px per wheel notch
                max_scroll = max(0.0, content_h - self._view_h)
                if touch.button == 'scrollup':
                    # macOS natural: scroll up gesture moves content down (show lower parts)
                    self._scroll_px = min(max_scroll, self._scroll_px + step)
                elif touch.button == 'scrolldown':
                    self._scroll_px = max(0.0, self._scroll_px - step)
                # Redraw items and border with new scroll
                self._redraw_all()
                self._update_border()
            return True

        # Convert to mm (top-left origin)
        mm = self._px_to_mm(*touch.pos)

        # Hit test in reverse draw order (top-most first)
        for item_id in reversed(self._draw_order):
            if self._hit_test(item_id, mm):
                self.dispatch('on_item_click', item_id, touch, mm)
                return True

        # Clicked empty space inside canvas
        self.dispatch('on_item_click', None, touch, mm)
        return True

    # ---------- Internal: layout / transforms ----------

    def _schedule_layout(self, *args):
        if self._resched:
            return
        self._resched = Clock.schedule_once(self._update_layout_and_redraw, 0)

    def _update_layout_and_redraw(self, *args):
        self._resched = None
        # Compute view rect keeping aspect ratio
        if self.width <= 0 or self.height <= 0 or self.width_mm <= 0 or self.height_mm <= 0:
            return

        if self.scale_to_width and self.width_mm > 0 and self.height_mm > 0:
            # Scale based on width only; enable vertical scrolling if content > viewport
            self._px_per_mm = max(1e-6, self.width / self.width_mm)
            view_w = int(round(self.width))
            content_h = self._content_height_px()
            
            # Center vertically if content is smaller than widget height
            if content_h <= self.height:
                view_h = content_h
                self._view_x = int(self.x)
                self._view_y = int(round(self.y + (self.height - content_h) / 2))
                self._view_w = view_w
                self._view_h = view_h
                self._scroll_px = 0.0
            else:
                # Content larger than viewport - enable scrolling
                view_h = int(round(self.height))
                self._view_x = int(self.x)
                self._view_y = int(self.y)
                self._view_w = view_w
                self._view_h = view_h
                # Clamp scroll to content bounds
                max_scroll = max(0, content_h - self._view_h)
                if self._scroll_px < 0:
                    self._scroll_px = 0.0
                elif self._scroll_px > max_scroll:
                    self._scroll_px = float(max_scroll)
        elif self.keep_aspect:
            scale_x = self.width / self.width_mm
            scale_y = self.height / self.height_mm
            self._px_per_mm = min(scale_x, scale_y)
            view_w = int(round(self.width_mm * self._px_per_mm))
            view_h = int(round(self.height_mm * self._px_per_mm))
            self._view_x = int(round(self.x + (self.width - view_w) / 2))
            self._view_y = int(round(self.y + (self.height - view_h) / 2))
            self._view_w = view_w
            self._view_h = view_h
            self._scroll_px = 0.0
        else:
            self._px_per_mm = min(
                max(1e-6, self.width / self.width_mm),
                max(1e-6, self.height / self.height_mm),
            )
            self._view_x = int(self.x)
            self._view_y = int(self.y)
            self._view_w = int(self.width)
            self._view_h = int(self.height)
            self._scroll_px = 0.0

        # Update scissor and background rect
        self._scissor.x = int(self._view_x)
        self._scissor.y = int(self._view_y)
        self._scissor.width = int(self._view_w)
        self._scissor.height = int(self._view_h)

        # Background covers the visible widget area
        self._bg_rect.pos = (self._view_x, self._view_y)
        self._bg_rect.size = (self._view_w, self._view_h)
        self._bg_color_instr.rgba = self.background_color

        # Border (around the full logical page/content); computed separately
        self._update_border()

        # Redraw all items with new scale
        self._redraw_all()

    def _mm_to_px_point(self, x_mm: float, y_mm_top: float) -> Tuple[float, float]:
        """Convert a top-left mm point to Kivy bottom-left px point."""
        x_px = self._view_x + x_mm * self._px_per_mm
        # Anchor at viewport top, positive scroll moves content up (showing lower parts)
        anchor_px = self._view_y + self._view_h + (self._scroll_px if self.scale_to_width else 0.0)
        y_px = anchor_px - y_mm_top * self._px_per_mm
        return x_px, y_px

    def _px_to_mm(self, x_px: float, y_px: float) -> Tuple[float, float]:
        """Convert a Kivy px point to top-left mm coordinates."""
        mm_x = (x_px - self._view_x) / self._px_per_mm
        anchor_px = self._view_y + self._view_h + (self._scroll_px if self.scale_to_width else 0.0)
        mm_y = (anchor_px - y_px) / self._px_per_mm
        return mm_x, mm_y

    def _point_in_view_px(self, x_px: float, y_px: float) -> bool:
        return (self._view_x <= x_px <= self._view_x + self._view_w) and (
            self._view_y <= y_px <= self._view_y + self._view_h
        )

    # ---------- Internal: drawing ----------

    def _new_item_id(self) -> int:
        nid = self._next_id
        self._next_id += 1
        return nid

    def _register_id(self, item_id: int):
        for tag in self._items[item_id]['id']:
            self._id.setdefault(tag, set()).add(item_id)

    def _redraw_all(self):
        for item_id in self._items.keys():
            self._redraw_item(item_id)

    def _content_height_px(self) -> int:
        """Height in pixels of the logical content at current scale."""
        return int(round(max(0.0, self.height_mm * self._px_per_mm)))

    def _update_border(self):
        """Update border color/width and rectangle position according to current layout and scroll."""
        self._border_color_instr.rgba = self.border_color
        self._border_line.width = self.border_width_px
        if self.scale_to_width:
            content_h = self._content_height_px()
            # Bottom-left of the full content rectangle adjusted by scroll
            bottom_y = self._view_y + self._view_h + self._scroll_px - content_h
            self._border_line.rectangle = (self._view_x, bottom_y, self._view_w, content_h)
        else:
            # Border equals current view rect
            self._border_line.rectangle = (self._view_x, self._view_y, self._view_w, self._view_h)

    def _redraw_item(self, item_id: int):
        item = self._items.get(item_id)
        if not item:
            return
        g: InstructionGroup = item['group']
        g.clear()

        t = item['type']
        if t == 'rectangle':
            self._draw_rectangle_instr(g, item)
        elif t == 'oval':
            self._draw_oval_instr(g, item)
        elif t == 'line':
            self._draw_line_instr(g, item)
        elif t == 'path':
            self._draw_path_instr(g, item)
        elif t == 'polygon':
            self._draw_polygon_instr(g, item)
        elif t == 'text':
            self._draw_text_instr(g, item)

    def _draw_rectangle_instr(self, g: InstructionGroup, item: Dict[str, Any]):
        x_mm, y_mm, w_mm, h_mm = item['x_mm'], item['y_mm'], item['w_mm'], item['h_mm']
        # Kivy uses bottom-left for pos; convert using y+height
        pos = self._mm_to_px_point(x_mm, y_mm + h_mm)
        size = (w_mm * self._px_per_mm, h_mm * self._px_per_mm)

        if item['fill']:
            g.add(Color(*item['fill_color']))
            g.add(Rectangle(pos=pos, size=size))

        if item['outline'] and item['outline_w_mm'] > 0:
            g.add(Color(*item['outline_color']))
            g.add(Line(rectangle=(*pos, *size), width=max(1.0, item['outline_w_mm'] * self._px_per_mm)))

    def _draw_oval_instr(self, g: InstructionGroup, item: Dict[str, Any]):
        x_mm, y_mm, w_mm, h_mm = item['x_mm'], item['y_mm'], item['w_mm'], item['h_mm']
        pos = self._mm_to_px_point(x_mm, y_mm + h_mm)
        size = (w_mm * self._px_per_mm, h_mm * self._px_per_mm)

        if item['fill']:
            g.add(Color(*item['fill_color']))
            g.add(Ellipse(pos=pos, size=size))

        if item['outline'] and item['outline_w_mm'] > 0:
            g.add(Color(*item['outline_color']))
            g.add(Line(ellipse=(*pos, *size), width=max(1.0, item['outline_w_mm'] * self._px_per_mm)))

    def _draw_line_instr(self, g: InstructionGroup, item: Dict[str, Any]):
        pts_px = []
        pts_mm = item['points_mm']
        for i in range(0, len(pts_mm), 2):
            x_mm, y_mm = pts_mm[i], pts_mm[i + 1]
            pts_px += list(self._mm_to_px_point(x_mm, y_mm))
        g.add(Color(*item['color']))
        width_px = max(1.0, item['w_mm'] * self._px_per_mm)
        if item.get('dash'):
            on_px = max(1.0, item['dash_mm'][0] * self._px_per_mm)
            off_px = max(1.0, item['dash_mm'][1] * self._px_per_mm)
            self._draw_dashed_polyline(g, pts_px, width_px, on_px, off_px)
        else:
            g.add(Line(points=pts_px, width=width_px, close=item.get('close', False)))

    def _draw_path_instr(self, g: InstructionGroup, item: Dict[str, Any]):
        pts_px = []
        pts_mm = item['points_mm']
        for i in range(0, len(pts_mm), 2):
            x_mm, y_mm = pts_mm[i], pts_mm[i + 1]
            pts_px += list(self._mm_to_px_point(x_mm, y_mm))
        g.add(Color(*item['color']))
        width_px = max(1.0, item['w_mm'] * self._px_per_mm)
        if item.get('dash'):
            on_px = max(1.0, item['dash_mm'][0] * self._px_per_mm)
            off_px = max(1.0, item['dash_mm'][1] * self._px_per_mm)
            self._draw_dashed_polyline(g, pts_px, width_px, on_px, off_px)
        else:
            g.add(Line(points=pts_px, width=width_px))

    def _draw_polygon_instr(self, g: InstructionGroup, item: Dict[str, Any]):
        pts_mm = item['points_mm']

        # Fill first (triangle fan), then outline on top
        if item['fill']:
            # Convert to px vertices
            verts: List[Tuple[float, float]] = []
            for i in range(0, len(pts_mm), 2):
                verts.append(self._mm_to_px_point(pts_mm[i], pts_mm[i + 1]))

            if len(verts) >= 3:
                # Use default Mesh vertex format (x, y, u, v); color via Color instruction
                vertices: List[float] = []
                indices: List[int] = []
                # Triangle fan about verts[0]
                for i in range(1, len(verts) - 1):
                    i0 = 0
                    i1 = i
                    i2 = i + 1
                    indices += [i0, i1, i2]
                for (x, y) in verts:
                    vertices += [x, y, 0.0, 0.0]
                g.add(Color(*item['fill_color']))
                g.add(Mesh(vertices=vertices, indices=indices, mode='triangles'))

        # Outline on top
        if item['outline'] and item['outline_w_mm'] > 0:
            pts_px: List[float] = []
            for i in range(0, len(pts_mm), 2):
                pts_px += list(self._mm_to_px_point(pts_mm[i], pts_mm[i + 1]))
            g.add(Color(*item['outline_color']))
            g.add(Line(points=pts_px, width=max(1.0, item['outline_w_mm'] * self._px_per_mm), close=True))

    def _draw_text_instr(self, g: InstructionGroup, item: Dict[str, Any]):
        # Prepare label (Courier New, size in px converted from pt)
        text = item['text']
        color_rgba = item['color']
        # Convert pt -> mm -> px (1 pt = 1/72 inch = 25.4/72 mm)
        px_per_mm = max(1e-6, self._px_per_mm)
        font_px = max(1.0, (item['font_pt'] * 25.4 / 72.0) * px_per_mm)

        # Build CoreLabel for texture
        lbl = CoreLabel(text=text, font_name='Courier New', font_size=font_px, color=color_rgba)
        lbl.refresh()
        tex = lbl.texture
        if not tex:
            return
        w_px, h_px = tex.size

        # Anchor point in px (global coordinates)
        ax_px, ay_px = self._mm_to_px_point(item['x_mm'], item['y_mm'])

        # Offsets from anchor to rectangle bottom-left
        off_x, off_y = self._anchor_offsets(item.get('anchor', 'top_left'), w_px, h_px)

        # Draw with local transform around anchor point
        g.add(PushMatrix())
        g.add(Translate(ax_px, ay_px))
        # Positive angle in our top-left system should rotate clockwise; negate for Kivy's CCW
        ang = float(item.get('angle_deg', 0.0))
        if abs(ang) > 1e-9:
            g.add(Rotate(angle=-ang))
        # Ensure texture draws with its own color (avoid multiplying by previous color)
        g.add(Color(1.0, 1.0, 1.0, 1.0))
        g.add(Rectangle(texture=tex, pos=(off_x, off_y), size=(w_px, h_px)))
        g.add(PopMatrix())

    # ---------- Internal: hit testing ----------

    def _hit_test(self, item_id: int, pos_mm: Tuple[float, float]) -> bool:
        item = self._items[item_id]
        t = item['type']
        x, y = pos_mm

        if t == 'rectangle':
            x0 = item['x_mm']
            y0 = item['y_mm']
            x1 = x0 + item['w_mm']
            y1 = y0 + item['h_mm']
            # Filled or outline thickness detection
            if item.get('fill'):
                return (x0 <= x <= x1) and (y0 <= y <= y1)
            ow = item.get('outline_w_mm', 0.25)
            tol = max(ow, 0.5)
            on_left = abs(x - x0) <= tol and (y0 - tol <= y <= y1 + tol)
            on_right = abs(x - x1) <= tol and (y0 - tol <= y <= y1 + tol)
            on_top = abs(y - y0) <= tol and (x0 - tol <= x <= x1 + tol)
            on_bottom = abs(y - y1) <= tol and (x0 - tol <= x <= x1 + tol)
            return on_left or on_right or on_top or on_bottom

        if t == 'oval':
            rx = item['w_mm'] / 2.0
            ry = item['h_mm'] / 2.0
            cx = item['x_mm'] + rx
            cy = item['y_mm'] + ry
            if rx <= 0 or ry <= 0:
                return False
            val = ((x - cx) / rx) ** 2 + ((y - cy) / ry) ** 2
            if item.get('fill'):
                return val <= 1.0
            # Outline detection: within ring thickness
            ow = item.get('outline_w_mm', 0.25)
            # Convert thickness to normalized radius space (approx)
            tnorm = ow / max(rx, ry)
            return 1.0 - tnorm <= val <= 1.0 + tnorm

        if t == 'line':
            pts = item['points_mm']
            w = max(0.1, item.get('w_mm', 0.25))
            tol = max(0.3, w / 2.0)
            # Distance from point to each segment
            for i in range(0, len(pts) - 2, 2):
                x1, y1 = pts[i], pts[i + 1]
                x2, y2 = pts[i + 2], pts[i + 3]
                if self._dist_point_to_segment(x, y, x1, y1, x2, y2) <= tol:
                    return True
            if item.get('close', False):
                x1, y1 = pts[0], pts[1]
                x2, y2 = pts[-2], pts[-1]
                if self._dist_point_to_segment(x, y, x1, y1, x2, y2) <= tol:
                    return True
            return False

        if t == 'path':
            # Treat like a polyline for hit-testing
            pts = item['points_mm']
            w = max(0.1, item.get('w_mm', 0.25))
            tol = max(0.3, w / 2.0)
            for i in range(0, len(pts) - 2, 2):
                x1, y1 = pts[i], pts[i + 1]
                x2, y2 = pts[i + 2], pts[i + 3]
                if self._dist_point_to_segment(x, y, x1, y1, x2, y2) <= tol:
                    return True
            return False

        if t == 'polygon':
            pts = item['points_mm']
            if item.get('fill'):
                return self._point_in_polygon(x, y, pts)
            # Outline only: near any edge
            w = item.get('outline_w_mm', 0.25)
            tol = max(0.3, w / 2.0)
            for i in range(0, len(pts), 2):
                x1, y1 = pts[i], pts[i + 1]
                x2, y2 = pts[(i + 2) % len(pts)], pts[(i + 3) % len(pts)]
                if self._dist_point_to_segment(x, y, x1, y1, x2, y2) <= tol:
                    return True
            return False

        if t == 'text':
            # Simple AABB hit test ignoring rotation.
            # Compute bottom-left of the text box from the anchor and compare.
            # Convert anchor point to px, then to mm for comparison with current (x,y) mm.
            px_per_mm = max(1e-6, self._px_per_mm)
            # Build texture metrics similar to draw (pt -> px)
            font_px = max(1.0, (item['font_pt'] * 25.4 / 72.0) * px_per_mm)
            lbl = CoreLabel(text=item['text'], font_name='Courier New', font_size=font_px)
            lbl.refresh()
            tex = lbl.texture
            if not tex:
                return False
            w_px, h_px = tex.size
            ax_px, ay_px = self._mm_to_px_point(item['x_mm'], item['y_mm'])
            off_x, off_y = self._anchor_offsets(item.get('anchor', 'top_left'), w_px, h_px)
            bl_x_px = ax_px + off_x
            bl_y_px = ay_px + off_y
            # Convert current test point (x,y) mm to px for comparison
            tx_px, ty_px = self._mm_to_px_point(x, y)
            return (bl_x_px <= tx_px <= bl_x_px + w_px) and (bl_y_px <= ty_px <= bl_y_px + h_px)

        return False

    @staticmethod
    def _anchor_offsets(anchor: str, w_px: float, h_px: float) -> Tuple[float, float]:
        """Return bottom-left offsets (dx, dy) from the given anchor to the text box.

        Anchor names (case-insensitive):
        - 'top_left'|'tl', 'top'|'tc', 'top_right'|'tr'
        - 'left'|'cl', 'center'|'cc', 'right'|'cr'
        - 'bottom_left'|'bl', 'bottom'|'bc', 'bottom_right'|'br'
        """
        a = (anchor or 'top_left').strip().lower()
        mapping = {
            'top_left': (0.0, -h_px), 'tl': (0.0, -h_px),
            'top': (-w_px / 2.0, -h_px), 'tc': (-w_px / 2.0, -h_px),
            'top_right': (-w_px, -h_px), 'tr': (-w_px, -h_px),
            'left': (0.0, -h_px / 2.0), 'cl': (0.0, -h_px / 2.0),
            'center': (-w_px / 2.0, -h_px / 2.0), 'cc': (-w_px / 2.0, -h_px / 2.0),
            'right': (-w_px, -h_px / 2.0), 'cr': (-w_px, -h_px / 2.0),
            'bottom_left': (0.0, 0.0), 'bl': (0.0, 0.0),
            'bottom': (-w_px / 2.0, 0.0), 'bc': (-w_px / 2.0, 0.0),
            'bottom_right': (-w_px, 0.0), 'br': (-w_px, 0.0),
        }
        return mapping.get(a, (0.0, -h_px))

    @staticmethod
    def _dist_point_to_segment(px, py, x1, y1, x2, y2) -> float:
        """Distance from point P to segment AB (in mm)."""
        vx, vy = x2 - x1, y2 - y1
        wx, wy = px - x1, py - y1
        c1 = vx * wx + vy * wy
        if c1 <= 0:
            return math.hypot(px - x1, py - y1)
        c2 = vx * vx + vy * vy
        if c2 <= c1:
            return math.hypot(px - x2, py - y2)
        b = c1 / c2
        bx, by = x1 + b * vx, y1 + b * vy
        return math.hypot(px - bx, py - by)

    @staticmethod
    def _point_in_polygon(px: float, py: float, pts: List[float]) -> bool:
        """Ray casting algorithm (mm)."""
        inside = False
        n = len(pts) // 2
        for i in range(n):
            x1, y1 = pts[2 * i], pts[2 * i + 1]
            x2, y2 = pts[2 * ((i + 1) % n)], pts[2 * ((i + 1) % n) + 1]
            if ((y1 > py) != (y2 > py)):
                xinters = (x2 - x1) * (py - y1) / (y2 - y1 + 1e-12) + x1
                if px < xinters:
                    inside = not inside
        return inside

    # ---------- Helpers ----------

    @staticmethod
    def _parse_color(color: str) -> Tuple[float, float, float, float]:
        """Parse a '#RRGGBB' or '#RRGGBBAA' hex color into RGBA floats."""
        if not isinstance(color, str) or not color.startswith('#'):
            # Fallback to black
            return (0.0, 0.0, 0.0, 1.0)
        hexval = color.lstrip('#')
        if len(hexval) == 6:
            r = int(hexval[0:2], 16) / 255.0
            g = int(hexval[2:4], 16) / 255.0
            b = int(hexval[4:6], 16) / 255.0
            a = 1.0
            return (r, g, b, a)
        if len(hexval) == 8:
            r = int(hexval[0:2], 16) / 255.0
            g = int(hexval[2:4], 16) / 255.0
            b = int(hexval[4:6], 16) / 255.0
            a = int(hexval[6:8], 16) / 255.0
            return (r, g, b, a)
        # Unsupported format
        return (0.0, 0.0, 0.0, 1.0)

    def _draw_dashed_polyline(self, g: InstructionGroup, pts_px: List[float], width_px: float,
                               on_px: float, off_px: float):
        """Render a dashed polyline given points in px using on/off dash lengths."""
        if len(pts_px) < 4:
            return
        # Iterate segments
        on = True
        remaining = on_px
        cx, cy = pts_px[0], pts_px[1]
        for i in range(2, len(pts_px), 2):
            nx, ny = pts_px[i], pts_px[i + 1]
            dx = nx - cx
            dy = ny - cy
            seg_len = max(1e-6, (dx*dx + dy*dy) ** 0.5)
            ux = dx / seg_len
            uy = dy / seg_len
            pos = 0.0
            while pos < seg_len:
                run = min(remaining, seg_len - pos)
                if on:
                    x1 = cx + ux * pos
                    y1 = cy + uy * pos
                    x2 = cx + ux * (pos + run)
                    y2 = cy + uy * (pos + run)
                    g.add(Line(points=[x1, y1, x2, y2], width=width_px))
                pos += run
                # flip on/off and reset remaining
                on = not on
                remaining = (on_px if on else off_px)
            # carry over remainder into next segment
            # compute overshoot: if pos > seg_len slightly
            if pos > seg_len:
                overshoot = pos - seg_len
                remaining = max(1e-6, (on_px if on else off_px) - overshoot)
            cx, cy = nx, ny
