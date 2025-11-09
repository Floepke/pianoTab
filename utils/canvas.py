from typing import List, Tuple, Optional, Dict, Any, Iterable
import math
import os

from kivy.uix.widget import Widget
from kivy.graphics import Color, Rectangle, Line, Ellipse, Mesh, InstructionGroup, PushMatrix, PopMatrix, Rotate, Translate
from kivy.core.text import Label as CoreLabel
from kivy.graphics.scissor_instructions import ScissorPush, ScissorPop
from kivy.clock import Clock
from kivy.core.window import Window
from .embedded_font import get_embedded_monospace_font
from gui.colors import LIGHT, LIGHT_DARKER, DARK_LIGHTER, DARK, ACCENT_COLOR
from utils.CONSTANTS import DEFAULT_GRID_STEP_TICKS


class CustomScrollbar(Widget):
    '''
    Custom scrollbar widget for the Canvas that looks consistent across all platforms.
    Positioned on the right side of the Canvas, twice as wide as the sash width.
    '''
    
    def __init__(self, canvas_widget, **kwargs):
        super().__init__(**kwargs)
        self.canvas_widget = canvas_widget
        self.dragging = False
        self.hovering = False
        
        # Scrollbar dimensions (twice the sash width from SplitView)
        self.scrollbar_width = 40  # 2 * 20 (sash width)
        self.thumb_min_height = 20
        
        # Colors using system theme - logical color mapping
        self.track_color = LIGHT_DARKER       # Track: lighter version of light theme
        self.thumb_color = ACCENT_COLOR       # Thumb: accent color for better visibility
        self.thumb_hover_color = DARK         # Hover: full dark theme color
        self.thumb_drag_color = DARK          # Drag: same as hover for consistency
        
        # Graphics instructions
        with self.canvas:
            # Track background
            self.track_color_instr = Color(*self.track_color)
            self.track_rect = Rectangle()
            
            # Thumb (scrollbar handle)
            self.thumb_color_instr = Color(*self.thumb_color)
            self.thumb_rect = Rectangle()
        
        # Bind to mouse events for hover detection
        Window.bind(mouse_pos=self.on_mouse_pos)
        
        # Size and position properties
        self.size_hint = (None, None)
        self.width = self.scrollbar_width
         
        # Update layout when canvas properties change
        self.canvas_widget.bind(size=self.update_layout, pos=self.update_layout)
        
    def update_layout(self, *args):
        '''Update scrollbar position and thumb size based on canvas state.'''
        # Keep scrollbar visible even when not in scale_to_width mode
            
        # Position scrollbar adjacent to the canvas view rect (non-overlapping; reserve width in view)
        vx = int(self.canvas_widget._view_x)
        vy = int(self.canvas_widget._view_y)
        vw = int(self.canvas_widget._view_w)
        vh = int(self.canvas_widget._view_h)
        self.x = vx + vw
        self.y = vy
        self.height = vh
        
        # Update track
        self.track_rect.pos = (self.x, self.y)
        self.track_rect.size = (self.scrollbar_width, self.height)
        
        # Calculate thumb dimensions and position
        content_height = int(self.canvas_widget._content_height_px())
        viewport_height = int(self.canvas_widget._view_h)

        # Guard against zero/negative sizes (e.g., panel collapsed to 0 or view not laid out yet)
        if viewport_height <= 0 or content_height <= 0:
            # Hide scrollbar safely to avoid ZeroDivisionError and invalid geometry
            self.opacity = 0
            self.track_rect.pos = (self.x, self.y)
            self.track_rect.size = (0, 0)
            self.thumb_rect.pos = (self.x, self.y)
            self.thumb_rect.size = (0, 0)
            return
        
        # Always visible when geometry is valid; compute thumb even if content fits
        scrollable = content_height > viewport_height
        self.opacity = 1
            
        # Thumb height proportional to viewport/content ratio with vertical margins
        available_track_height = self.height - 10  # Reserve 5px margin top and bottom
        thumb_height = max(self.thumb_min_height,
                          (viewport_height / content_height) * available_track_height)
        # Clamp to track height so it never exceeds
        thumb_height = min(available_track_height, thumb_height)
        
        # Thumb position based on scroll offset with vertical margin
        max_scroll = content_height - viewport_height
        scroll_ratio = self.canvas_widget._scroll_px / max_scroll if max_scroll > 0 else 0
        max_thumb_y = available_track_height - thumb_height
        thumb_y = self.y + 5 + (max_thumb_y * (1 - scroll_ratio))  # 5px top margin + position
        
        # Update thumb rectangle with 5px margin on all sides
        self.thumb_rect.pos = (self.x + 5, thumb_y)  # 5px margin from edges
        self.thumb_rect.size = (self.scrollbar_width - 10, thumb_height)  # 5px margin on each side
        
    def on_mouse_pos(self, window, pos):
        '''Handle mouse hover for visual feedback.'''
        if self.dragging or self.opacity == 0:
            return

        # Determine if scrolling is possible
        content_height = self.canvas_widget._content_height_px()
        viewport_height = self.canvas_widget._view_h
        scrollable = self.canvas_widget.scale_to_width and (content_height > viewport_height)
             
        # Check if mouse is over the entire scrollbar area (full width)
        mouse_x, mouse_y = pos
        is_over_scrollbar = (self.x <= mouse_x <= self.x + self.scrollbar_width and
                            self.y <= mouse_y <= self.y + self.height)
         
        # Always set cursor based on current position
        # This prevents edge cases where transitions are missed
        if is_over_scrollbar:
            self.hovering = True
            self.thumb_color_instr.rgba = self.thumb_hover_color if scrollable else self.thumb_color
            Window.set_system_cursor('hand' if scrollable else 'arrow')
        else:
            if self.hovering:
                self.hovering = False
                self.thumb_color_instr.rgba = self.thumb_color
                # Don't set cursor to arrow - let other widgets handle it
            
    def on_touch_down(self, touch):
        '''Handle touch down for scrollbar dragging.'''
        if self.opacity == 0:
            return False
        # Inert when no scrolling is possible
        content_height = self.canvas_widget._content_height_px()
        viewport_height = self.canvas_widget._view_h
        scrollable = self.canvas_widget.scale_to_width and (content_height > viewport_height)
        if not scrollable:
            return False
             
        # Check if touch is within scrollbar area
        if not self.collide_point(*touch.pos):
            return False
            
        # Check if touch is on the thumb or in the thumb's vertical range (for easier dragging)
        thumb_x, thumb_y = self.thumb_rect.pos
        thumb_w, thumb_h = self.thumb_rect.size
        
        touch_x, touch_y = touch.pos
        is_on_thumb = (thumb_x <= touch_x <= thumb_x + thumb_w and 
                      thumb_y <= touch_y <= thumb_y + thumb_h)
        
        # Also allow dragging if clicking within the full scrollbar width in the thumb's vertical range
        is_in_thumb_range = (self.x <= touch_x <= self.x + self.scrollbar_width and
                            thumb_y <= touch_y <= thumb_y + thumb_h)
        
        if is_on_thumb or is_in_thumb_range:
            # Start dragging - maintain the relative position where the user clicked
            self.dragging = True
            # Calculate offset from the top of the thumb to the click point
            self.drag_offset = touch_y - thumb_y
            touch.grab(self)
            self.thumb_color_instr.rgba = self.thumb_drag_color
            return True
        else:
            # Click on track - jump to position
            self._jump_to_position(touch_y)
            return True
            
    def on_touch_move(self, touch):
        '''Handle thumb dragging.'''
        if touch.grab_current is self and self.dragging:
            self._drag_to_position(touch.pos[1])
            return True
        return False
        
    def on_touch_up(self, touch):
        '''Handle touch up - stop dragging.'''
        if touch.grab_current is self:
            self.dragging = False
            touch.ungrab(self)
            # Restore hover color if still hovering, otherwise normal color
            if self.hovering:
                self.thumb_color_instr.rgba = self.thumb_hover_color
            else:
                self.thumb_color_instr.rgba = self.thumb_color
            return True
        return False
        
    def _jump_to_position(self, touch_y):
        '''Jump scroll position to where user clicked on track.'''
        # Calculate which part of the track was clicked
        relative_y = touch_y - self.y
        ratio = relative_y / self.height
        
        # Convert to scroll position (inverted because we scroll top-to-bottom)
        content_height = self.canvas_widget._content_height_px()
        viewport_height = self.canvas_widget._view_h
        max_scroll = max(0, content_height - viewport_height)
        
        # Keep fractional scrolling when using the scrollbar handle / track
        new_scroll = max_scroll * (1 - ratio)
        self.canvas_widget._scroll_px = max(0, min(max_scroll, new_scroll))
        
        # Update canvas and scrollbar
        self.canvas_widget._redraw_all()
        self.canvas_widget._update_border()
        self.update_layout()
        
    def _drag_to_position(self, touch_y):
        '''Update scroll position based on thumb drag.'''
        # Calculate new thumb position to maintain the same relative offset
        new_thumb_y = touch_y - self.drag_offset
        
        # Calculate bounds for thumb movement
        thumb_height = self.thumb_rect.size[1]
        min_thumb_y = self.y
        max_thumb_y = self.y + self.height - thumb_height
        
        # Clamp thumb position
        clamped_thumb_y = max(min_thumb_y, min(max_thumb_y, new_thumb_y))
        
        # Convert thumb position to scroll ratio (inverted)
        if max_thumb_y > min_thumb_y:
            thumb_ratio = (clamped_thumb_y - min_thumb_y) / (max_thumb_y - min_thumb_y)
            scroll_ratio = 1 - thumb_ratio  # Invert for top-to-bottom scroll
        else:
            scroll_ratio = 0
            
        # Update canvas scroll
        content_height = self.canvas_widget._content_height_px()
        viewport_height = self.canvas_widget._view_h
        max_scroll = max(0, content_height - viewport_height)
        
        # Keep fractional scrolling when dragging the scrollbar handle
        raw = scroll_ratio * max_scroll
        self.canvas_widget._scroll_px = max(0, min(max_scroll, raw))
        
        # Update canvas and scrollbar
        self.canvas_widget._redraw_all()
        self.canvas_widget._update_border()
        self.update_layout()


class Canvas(Widget):
    '''
    Tkinter-like Canvas for Kivy using millimeters and top-left origin.

    - Drawable area in mm: width_mm x height_mm
    - Top-left origin (0,0) is top-left of the drawable area (like Tkinter)
    - Auto-fit to widget size with aspect ratio preserved (letterboxing)
    - Background color and border
    - Tag-based grouping and z-ordering
    - Click detection, returns top-most item handle (internal integer)

    Units:
    - All coordinates/sizes passed to add_* are in millimeters (mm) relative to top-left.

    Events:
    - bind(on_item_click=callback) -> callback(self, item_handle, touch, pos_mm)
    '''

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
        
        # Calculate system DPI for pixel-to-mm conversion
        self._mm_per_pixel: float = self._calculate_mm_per_pixel()
        
        # Quarter note spacing in mm for musical scrolling
        self._quarter_note_spacing_mm: float = 10.0  # Default fallback value

        # Editor feedback loop guard (set True when editor triggers canvas resizing)
        self._updating_from_editor: bool = False

        # Grid-based cursor snapping (cursor position state only)
        self._cursor_visible: bool = False
        self._cursor_x_mm: float = 0.0  # Cursor position in mm coordinates
        self._cursor_line_instr = None  # Will be created when needed

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

        # Items and tags
        self._next_id: int = 1
        self._items: Dict[int, Dict[str, Any]] = {}
        # Map tag -> set of item handles
        self._tag_index: Dict[str, set] = {}
        self._draw_order: List[int] = []  # z-order (append = on top)

        # Create and add custom scrollbar
        self.custom_scrollbar = CustomScrollbar(self)
        self.add_widget(self.custom_scrollbar)

        # Bind to mouse motion for cursor tracking
        Window.bind(mouse_pos=self.on_mouse_motion)

        # Defer expensive redraws during resize
        self._resched = None
        self.bind(pos=self._schedule_layout, size=self._schedule_layout)

        # Initial layout
        self._update_layout_and_redraw()

    def set_piano_roll_editor(self, editor):
        '''Set the piano roll editor reference for accessing score data.'''
        self.piano_roll_editor = editor
        
        # Bind canvas click events to editor tool system
        if editor is not None:
            self.bind(on_item_click=self._forward_click_to_editor)
            # Also bind touch up events for editor drag detection
            self._original_on_touch_up = self.on_touch_up
            self.on_touch_up = self._on_touch_up_with_editor_forward
        
        # As soon as the editor is wired, refresh zoom so the canvas' current
        # px-per-mm is reflected in the editor's mm-per-quarter spacing immediately.
        try:
            if editor is not None and hasattr(editor, 'zoom_refresh'):
                editor.zoom_refresh()
            elif editor is not None and hasattr(editor, '_calculate_layout'):
                editor._calculate_layout()
        except Exception as e:
            print(f'CANVAS: failed to sync editor layout on attach: {e}')

        # Update scrollbar layout now that content sizing may have changed
        if hasattr(self, 'custom_scrollbar') and self.custom_scrollbar:
            self.custom_scrollbar.update_layout()
    
    def _forward_click_to_editor(self, instance, item_id, touch, pos_mm):
        '''Forward click events to the editor's tool system.'''
        editor = getattr(self, 'piano_roll_editor', None)
        if editor is None or not hasattr(editor, 'handle_mouse_down'):
            return
        
        x_mm, y_mm = pos_mm
        button = getattr(touch, 'button', 'left')
        
        # Normalize button name
        if button in ('scrollup', 'scrolldown'):
            return  # Ignore scroll events
        
        # Map button to left/right
        if button == 'right':
            button_name = 'right'
        else:
            button_name = 'left'
        
        # Dispatch to editor
        if hasattr(touch, 'is_double_tap') and touch.is_double_tap:
            editor.handle_double_click(x_mm, y_mm)
        else:
            editor.handle_mouse_down(x_mm, y_mm, button_name)
    
    def _on_touch_up_with_editor_forward(self, touch):
        '''Wrap on_touch_up to forward mouse up events to editor tool system.'''
        # Call original on_touch_up first
        result = self._original_on_touch_up(touch)
        
        # Forward mouse up to editor if it has the handler
        editor = getattr(self, 'piano_roll_editor', None)
        if editor is not None and hasattr(editor, 'handle_mouse_up'):
            # Check if touch was within view area
            if self._point_in_view_px(*touch.pos):
                # Convert to mm
                mm_x, mm_y = self._px_to_mm(*touch.pos)
                button = getattr(touch, 'button', 'left')
                
                # Normalize button name
                if button in ('scrollup', 'scrolldown'):
                    # Ignore scroll events - don't dispatch to editor
                    return result
                elif button == 'right':
                    button_name = 'right'
                else:
                    button_name = 'left'
                
                # Dispatch to editor
                try:
                    editor.handle_mouse_up(mm_x, mm_y, button_name)
                except Exception as e:
                    print(f'CANVAS: mouse up dispatch failed: {e}')
        
        return result

    # ---------- Grid step source (editor -> grid_selector) ----------

    def _get_grid_step_ticks(self) -> float:
        '''Return current grid step in ticks from editor.grid_selector.

        Returns DEFAULT_GRID_STEP_TICKS as fallback when editor or grid_selector is not available.
        '''
        try:
            ed = getattr(self, 'piano_roll_editor', None)
            if ed is not None:
                # Preferred: editor.grid_selector.get_grid_step()
                gs = getattr(ed, 'grid_selector', None)
                if gs is not None and hasattr(gs, 'get_grid_step'):
                    ticks = gs.get_grid_step()
                    if isinstance(ticks, (int, float)) and ticks > 0:
                        return float(ticks)
                # Secondary: editor.get_grid_step()
                if hasattr(ed, 'get_grid_step'):
                    ticks = ed.get_grid_step()
                    if isinstance(ticks, (int, float)) and ticks > 0:
                        return float(ticks)
        except Exception as e:
            print(f'GRID DEBUG: failed to read grid step from editor: {e}')
        # Fallback to default from constants
        return DEFAULT_GRID_STEP_TICKS

    def _snap_scroll_to_grid(self, scroll_px: float) -> float:
        '''Snap scroll position to align with visual grid in the editor based on current grid step.
        
        Anchoring behavior:
        - Near the top (within the editor margin), allow snapping relative to 0.0 so the
          scroll can reach exactly 0 (full top margin visible).
        - Otherwise use anchor = editor_margin - one quarter spacing, snapping in grid steps.
        '''
        # Get editor margin (mm) and quarter note length (ticks)
        editor_margin_mm = 0.0  # Default fallback
        quarter_note_length = 256.0  # Default

        if hasattr(self, 'piano_roll_editor') and self.piano_roll_editor:
            # Get editor margin from the piano roll editor (not canvas)
            if hasattr(self.piano_roll_editor, 'editor_margin'):
                editor_margin_mm = self.piano_roll_editor.editor_margin

            # Get values from score
            if hasattr(self.piano_roll_editor, 'score') and self.piano_roll_editor.score:
                score = self.piano_roll_editor.score
                if hasattr(score, 'quarterNoteLength'):
                    quarter_note_length = score.quarterNoteLength

        # Calculate current grid step spacing in mm based on the canvas' content scale
        grid_step_ticks = self._get_grid_step_ticks()
        grid_step_quarters = grid_step_ticks / quarter_note_length
        mm_per_quarter = float(self._quarter_note_spacing_mm)
        grid_spacing_mm = grid_step_quarters * mm_per_quarter
        px_per_mm = max(1e-6, self._px_per_mm)
        quarter_spacing_mm = mm_per_quarter

        # Calculate anchor point in mm: editor_margin - one quarter spacing
        anchor_mm = editor_margin_mm - quarter_spacing_mm

        # Convert scroll position to mm (using current scale)
        scroll_mm = scroll_px / px_per_mm

        # Choose snapping strategy:
        # - If we're within the top margin area, prefer snapping relative to 0.0 so 0 is reachable.
        # - Otherwise, snap relative to the anchor (editor_margin - quarter_spacing).
        if grid_spacing_mm <= 1e-9:
            snapped_scroll_mm = max(0.0, scroll_mm)
            anchor_used_mm = 0.0
        elif scroll_mm <= editor_margin_mm:
            snapped_scroll_mm = max(0.0, round(scroll_mm / grid_spacing_mm) * grid_spacing_mm)
            anchor_used_mm = 0.0
        else:
            offset_from_anchor = scroll_mm - anchor_mm
            snapped_offset = round(offset_from_anchor / grid_spacing_mm) * grid_spacing_mm
            snapped_scroll_mm = anchor_mm + snapped_offset
            anchor_used_mm = anchor_mm

        # Convert back to pixels
        snapped_scroll_px = snapped_scroll_mm * px_per_mm

        # Bottom-edge snap: if near max scroll, snap exactly to max_scroll so full bottom margin is visible
        content_height = self._content_height_px()
        viewport_height = self._view_h
        max_scroll_px = max(0.0, content_height - viewport_height)
        grid_spacing_px = grid_spacing_mm * px_per_mm
        threshold_px = max(1.0, grid_spacing_px / 2.0) if grid_spacing_px > 1e-6 else 1.0
        if max_scroll_px > 0.0 and snapped_scroll_px >= max_scroll_px - threshold_px:
            snapped_scroll_px = max_scroll_px

        return snapped_scroll_px

    def update_scroll_step(self):
        '''Update scroll step calculation when score data changes (e.g., quarterNoteLength).'''
        if hasattr(self, 'custom_scrollbar') and self.custom_scrollbar:
            self.custom_scrollbar.update_layout()
            grid_step = self._get_grid_step_ticks()
            print(f'SCROLL STEP UPDATED: Grid step {grid_step} -> {self._calculate_grid_step_pixels():.1f} pixels')

    # ---------- Internal: font resolution ----------

    def _get_courier_bold_font(self) -> str:
        '''Return a reliable monospace font name/path for CoreLabel.

        Uses the embedded font manager to get a font that works
        across different systems without requiring specific fonts.
        '''
        return get_embedded_monospace_font()

    def _calculate_mm_per_pixel(self) -> float:
        '''Calculate millimeters per pixel based on system DPI.
        
        Returns:
            float: Millimeters per pixel conversion factor
        '''
        try:
            # Get system DPI from Kivy Window
            dpi = Window.dpi
            if dpi <= 0:
                # Fallback to common default DPI values by platform
                import platform
                system = platform.system().lower()
                if system == 'darwin':  # macOS
                    dpi = 72.0  # macOS default
                elif system == 'windows':  # Windows
                    dpi = 96.0  # Windows default
                else:  # Linux and others
                    dpi = 96.0  # Common Linux default
            
            # Convert DPI to mm/pixel: 1 inch = 25.4 mm
            mm_per_pixel = 25.4 / dpi
            
            return mm_per_pixel
            
        except Exception as e:
            print(f'CANVAS DPI: Error calculating DPI, using 96 DPI fallback: {e}')
            # Fallback to 96 DPI (0.264583 mm/pixel)
            return 25.4 / 96.0

    # ---------- Public API (Tkinter-like) ----------

    def clear(self):
        '''Remove all items.'''
        self._items_group.clear()
        self._items.clear()
        self._tag_index.clear()
        self._draw_order.clear()

    def add_rectangle(
        self,
        x1_mm: float,
        y1_mm: float,
        x2_mm: float,
        y2_mm: float,
        *,
        fill: bool = False,
        fill_color: str = '#000000',
        outline: bool = True,
        outline_color: str = '#000000',
        outline_width_mm: float = 0.25,
        tags: Optional[Iterable[str]] = None,
        # Deprecated: allow legacy callers to pass id=[...]
        id: Optional[Iterable[str]] = None,
    ) -> int:
        '''Add a rectangle by two corners (top-left and bottom-right) in mm.

        Colors are hex strings like '#RRGGBB' (alpha assumed 1.0).
        '''
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
            'tags': set(tags or id or []),
        }
        self._register_tags(item_id)
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
        fill_color: str = '#000000',
        outline: bool = True,
        outline_color: str = '#000000',
        outline_width_mm: float = 0.25,
        tags: Optional[Iterable[str]] = None,
        id: Optional[Iterable[str]] = None,
    ) -> int:
        '''Add an oval (ellipse) inscribed in the rectangle defined by two corners in mm.

        Colors are hex strings like '#RRGGBB' (alpha assumed 1.0).
        '''
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
            'tags': set(tags or id or []),
        }
        self._register_tags(item_id)
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
        color: str = '#000000',
        width_mm: float = 0.25,
        dash: bool = False,
        dash_pattern_mm: Tuple[float, float] = (2.0, 2.0),
        tags: Optional[Iterable[str]] = None,
        id: Optional[Iterable[str]] = None,
    ) -> int:
        '''Add a straight line segment between two points in mm.

        Colors are hex strings like '#RRGGBB'. Dash pattern is in mm.
        '''
        item_id = self._new_item_id()
        group = InstructionGroup()
        self._items_group.add(group)

        self._items[item_id] = {
            'type': 'line',
            'group': group,
            'points_mm': [float(x1_mm), float(y1_mm), float(x2_mm), float(y2_mm)],
            'color': self._parse_color(color),
            'w_mm': float(width_mm),
            'smooth': False,
            'close': False,
            'dash': bool(dash),
            'dash_mm': (float(dash_pattern_mm[0]), float(dash_pattern_mm[1])),
            'tags': set(tags or id or []),
        }
        self._register_tags(item_id)
        self._draw_order.append(item_id)
        self._redraw_item(item_id)
        return item_id

    def add_polyline(
        self,
        points_mm: Iterable[float],
        *,
        color: str = '#000000',
        width_mm: float = 0.25,
        dash: bool = False,
        dash_pattern_mm: Tuple[float, float] = (2.0, 2.0),
        tags: Optional[Iterable[str]] = None,
        id: Optional[Iterable[str]] = None,
    ) -> int:
        '''Add a polyline/path defined by a list of mm points [x0,y0,x1,y1,...].

        Raises ValueError if points list length is odd or < 4.
        '''
        pts = list(map(float, points_mm))
        if len(pts) < 4 or len(pts) % 2 != 0:
            raise ValueError('add_path requires an even-length list with at least two points')
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
            'tags': set(tags or id or []),
        }
        self._register_tags(item_id)
        self._draw_order.append(item_id)
        self._redraw_item(item_id)
        return item_id

    def add_polygon(
        self,
        points_mm: Iterable[float],
        *,
        fill: bool = False,
        fill_color: str = '#000000',
        outline: bool = True,
        outline_color: str = '#000000',
        outline_width_mm: float = 0.25,
        tags: Optional[Iterable[str]] = None,
        id: Optional[Iterable[str]] = None,
    ) -> int:
        '''
        Add a polygon. Points in mm [x0,y0, x1,y1, ...].
        Fill uses a triangle fan (suitable for convex polygons).
        '''
        pts = list(map(float, points_mm))
        if len(pts) < 6:
            raise ValueError('add_polygon requires at least 3 points')
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
            'tags': set(tags or id or []),
        }
        self._register_tags(item_id)
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
        anchor: str = 'top_left',
        color: str = '#000000',
        tags: Optional[Iterable[str]] = None,
        id: Optional[Iterable[str]] = None,
    ) -> int:
        '''Add a text label.

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
        - Font is fixed to 'Courier New' in pianoTAB. you can only use one good readable font.
        - Hit-testing uses the un-rotated bounding box (rotation ignored for clicks).
        '''
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
            'tags': set(tags or id or []),
        }
        self._register_tags(item_id)
        self._draw_order.append(item_id)
        self._redraw_item(item_id)
        return item_id

    # ----- Tags API -----

    def get_item(self, item_handle: int) -> Optional[Dict[str, Any]]:
        '''Return the stored item dict by internal handle.'''
        return self._items.get(item_handle)

    def add_tag(self, item_handle: int, tag: str):
        if item_handle in self._items:
            self._items[item_handle]['tags'].add(tag)
            self._tag_index.setdefault(tag, set()).add(item_handle)

    def remove_tag(self, item_handle: int, tag: str):
        if item_handle in self._items:
            self._items[item_handle]['tags'].discard(tag)
        if tag in self._tag_index:
            self._tag_index[tag].discard(item_handle)
            if not self._tag_index[tag]:
                del self._tag_index[tag]

    def find_by_tag(self, tag: str) -> List[int]:
        return sorted(self._tag_index.get(tag, set()))

    def delete_by_tag(self, tag: str):
        '''Delete all items with the specified tag.'''
        item_ids = list(self._tag_index.get(tag, set()))
        for item_id in item_ids:
            self.delete(item_id)

    def tag_draw_order(self, tags: List[str]):
        '''Reorder items so that items with the specified tags are drawn in the given order.
        
        Items with tags earlier in the list will be drawn first (behind).
        Items with tags later in the list will be drawn last (on top).
        Items not matching any tag in the list maintain their relative order at the end.
        
        Args:
            tags: List of tags in the desired drawing order (first = bottom, last = top)
        
        Example:
            canvas.tag_draw_order(['staveThreeLines', 'staveTwoLines', 'staveClefLines'])
            # staveThreeLines will be drawn first (at the back)
            # staveClefLines will be drawn last (on top)
        '''
        # Build a new draw order
        new_order = []
        used_ids = set()
        
        # First, add items in tag order
        for tag in tags:
            tag_items = self.find_by_tag(tag)
            for item_id in tag_items:
                if item_id not in used_ids and item_id in self._draw_order:
                    new_order.append(item_id)
                    used_ids.add(item_id)
        
        # Then add remaining items that weren't matched by any tag
        for item_id in self._draw_order:
            if item_id not in used_ids:
                new_order.append(item_id)
        
        # Update draw order
        self._draw_order = new_order
        
        # Rebuild the items group in the new order
        self._items_group.clear()
        for item_id in self._draw_order:
            if item_id in self._items:
                self._items_group.add(self._items[item_id]['group'])

    def delete(self, item_handle: int):
        '''Delete an item by internal handle.'''
        item = self._items.pop(item_handle, None)
        if not item:
            return
        group: InstructionGroup = item['group']
        self._items_group.remove(group)
        for tag in list(item.get('tags', [])):
            self.remove_tag(item_handle, tag)
        if item_handle in self._draw_order:
            self._draw_order.remove(item_handle)

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
        '''Change the logical canvas size (in mm) and relayout/redraw.

        If reset_scroll is True, vertical scroll offset resets to 0.

        Marks updates that originate from the Editor so _update_layout_and_redraw
        won't immediately trigger another zoom_refresh and create a feedback loop.
        '''
        self.width_mm = float(width_mm)
        self.height_mm = float(height_mm)
        if reset_scroll:
            self._scroll_px = 0.0

        # Prevent feedback loop when Editor.render() resizes the canvas
        self._updating_from_editor = True
        try:
            self._update_layout_and_redraw()
        finally:
            self._updating_from_editor = False

    def set_scale_to_width(self, enabled: bool):
        '''Enable/disable scale-to-width + vertical scrolling behavior.'''
        self.scale_to_width = bool(enabled)
        if not self.scale_to_width:
            # Reset scroll when disabling
            self._scroll_px = 0.0
        self._update_layout_and_redraw()
        # Update scrollbar visibility
        if hasattr(self, 'custom_scrollbar'):
            self.custom_scrollbar.update_layout()

    def set_quarter_note_spacing_mm(self, spacing_mm: float):
        '''Set the quarter note spacing in mm for musical scrolling.'''
        self._quarter_note_spacing_mm = float(spacing_mm)

    # ----- Events -----

    def on_item_click(self, item_id: Optional[int], touch, pos_mm: Tuple[float, float]):
        '''Default handler (no-op). Bind to this event to handle clicks.'''
        pass

    def on_touch_down(self, touch):
        # Only handle if inside our widget
        if not self.collide_point(*touch.pos):
            return super().on_touch_down(touch)

        # Let custom scrollbar handle touch events first
        if self.custom_scrollbar.on_touch_down(touch):
            return True

        # Only continue with canvas logic if within the view area (excluding scrollbar)
        if not self._point_in_view_px(*touch.pos):
            return super().on_touch_down(touch)

        # Mouse wheel vertical scrolling in scale_to_width mode
        if self.scale_to_width and hasattr(touch, 'button') and touch.button in ('scrollup', 'scrolldown'):
            content_h = self._content_height_px()
            if content_h > self._view_h:  # scrolling only if content taller than viewport
                # Calculate scroll step based on current grid step
                grid_step_px = self._calculate_grid_step_pixels()
                # Use exact grid step in pixels (rounded), allow fractional scales; clamp to at least 1px
                step = max(1, int(round(grid_step_px)))
                max_scroll = max(0.0, content_h - self._view_h)
                if touch.button == 'scrollup':
                    # macOS natural: scroll up gesture moves content down (show lower parts)
                    new_scroll = min(max_scroll, self._scroll_px + step)
                    self._scroll_px = self._snap_scroll_to_grid(new_scroll)
                elif touch.button == 'scrolldown':
                    new_scroll = max(0.0, self._scroll_px - step)
                    self._scroll_px = self._snap_scroll_to_grid(new_scroll)
                
                # Ensure we stay within bounds after snapping
                self._scroll_px = max(0.0, min(max_scroll, self._scroll_px))
                # Redraw items and border with new scroll
                self._redraw_all()
                self._update_border()
                # Update scrollbar to reflect new position
                self.custom_scrollbar.update_layout()
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

    def on_touch_move(self, touch):
        # Let scrollbar handle move events first
        if self.custom_scrollbar.on_touch_move(touch):
            return True
        return super().on_touch_move(touch)

    def on_touch_up(self, touch):
        # Let scrollbar handle up events first
        if self.custom_scrollbar.on_touch_up(touch):
            return True
        return super().on_touch_up(touch)

    def on_mouse_motion(self, window, pos):
        '''Handle mouse motion - set cursor for non-editor canvases.'''
        mouse_x, mouse_y = pos

        # Check if mouse is over the canvas drawable view area (excluding scrollbar)
        if self._point_in_view_px(mouse_x, mouse_y):
            # Mouse is over the canvas content area
            ed = getattr(self, 'piano_roll_editor', None)
            
            # For non-editor Canvas (e.g., print preview) - set arrow cursor
            # Editor canvas cursor is handled by Editor._update_cursor_on_hover
            if ed is None:
                Window.set_system_cursor('arrow')

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
            # Try calculating scale without scrollbar first
            available_width = self.width
            px_per_mm_without_scrollbar = max(1e-6, available_width / self.width_mm)
            content_height_without_scrollbar = int(round(max(0.0, self.height_mm * px_per_mm_without_scrollbar)))
            
            # If content fits without scrollbar, use that calculation
            if content_height_without_scrollbar <= self.height:
                self._px_per_mm = px_per_mm_without_scrollbar
                available_width = self.width  # No scrollbar needed
            else:
                # Content doesn't fit; reserve space for a non-overlapping scrollbar
                if hasattr(self, 'custom_scrollbar'):
                    available_width -= getattr(self.custom_scrollbar, 'scrollbar_width', 40)
                self._px_per_mm = max(1e-6, available_width / self.width_mm)
            
            view_w = int(round(available_width))
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

        # Canvas handles scaling internally via _px_per_mm and viewport culling.
        # Items are stored in mm coordinates and auto-scale when _px_per_mm changes.
        # No need to notify editor or trigger expensive recalculations - _redraw_all() 
        # handles everything efficiently with viewport culling.

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

        # Update scrollbar layout
        if hasattr(self, 'custom_scrollbar'):
            self.custom_scrollbar.update_layout()

        # Redraw all items with new scale
        self._redraw_all()

    def _mm_to_px_point(self, x_mm: float, y_mm_top: float) -> Tuple[float, float]:
        '''Convert a top-left mm point to Kivy bottom-left px point.'''
        x_px = self._view_x + x_mm * self._px_per_mm
        # Anchor at viewport top, positive scroll moves content up (showing lower parts)
        anchor_px = self._view_y + self._view_h + (self._scroll_px if self.scale_to_width else 0.0)
        y_px = anchor_px - y_mm_top * self._px_per_mm
        return x_px, y_px

    def _px_to_mm(self, x_px: float, y_px: float) -> Tuple[float, float]:
        '''Convert a Kivy px point to top-left mm coordinates.'''
        mm_x = (x_px - self._view_x) / self._px_per_mm
        anchor_px = self._view_y + self._view_h + (self._scroll_px if self.scale_to_width else 0.0)
        mm_y = (anchor_px - y_px) / self._px_per_mm
        return mm_x, mm_y

    def _point_in_view_px(self, x_px: float, y_px: float) -> bool:
        # Use the computed view width directly; it already accounts for scrollbar when visible
        right_boundary = self._view_x + self._view_w

        return (self._view_x <= x_px <= right_boundary) and (
            self._view_y <= y_px <= self._view_y + self._view_h
        )

    # ---------- Internal: drawing ----------

    def _new_item_id(self) -> int:
        nid = self._next_id
        self._next_id += 1
        return nid

    def _register_tags(self, item_handle: int):
        for tag in self._items[item_handle]['tags']:
            self._tag_index.setdefault(tag, set()).add(item_handle)

    def _redraw_all(self):
        '''Redraw all items with viewport culling optimization.
        
        Only redraws items that are currently visible in the viewport,
        significantly improving performance for large vertical piano rolls.
        '''
        if self.scale_to_width and self._view_h > 0:
            # Calculate visible Y range in mm coordinates
            visible_y_min_mm, visible_y_max_mm = self._get_visible_y_range_mm()
            
            # Add buffer zone above and below viewport for smoother scrolling
            buffer_mm = 50.0  # 50mm buffer (~2 inches) above/below visible area
            cull_y_min_mm = max(0.0, visible_y_min_mm - buffer_mm)
            cull_y_max_mm = min(self.height_mm, visible_y_max_mm + buffer_mm)
            
            # Only redraw items that intersect the visible range
            visible_count = 0
            for item_id in self._items.keys():
                if self._item_in_y_range(item_id, cull_y_min_mm, cull_y_max_mm):
                    self._redraw_item(item_id)
                    visible_count += 1
                else:
                    # Clear item group to save GPU memory
                    item = self._items.get(item_id)
                    if item and 'group' in item:
                        item['group'].clear()
        else:
            # No culling when not in scale_to_width mode or viewport not ready
            for item_id in self._items.keys():
                self._redraw_item(item_id)

    def _get_visible_y_range_mm(self) -> Tuple[float, float]:
        '''Calculate the visible Y range in mm coordinates based on current scroll.
        
        Returns (y_min_mm, y_max_mm) where y is measured from top (0) downward.
        '''
        if self._view_h <= 0 or self._px_per_mm <= 0:
            return (0.0, self.height_mm)
        
        # Visible viewport in mm
        viewport_height_mm = self._view_h / self._px_per_mm
        
        # Current scroll offset in mm (how far down we've scrolled)
        scroll_mm = self._scroll_px / self._px_per_mm
        
        # Visible Y range in mm coordinates (top-left origin)
        y_min_mm = scroll_mm
        y_max_mm = scroll_mm + viewport_height_mm
        
        return (y_min_mm, y_max_mm)
    
    def _item_in_y_range(self, item_id: int, y_min_mm: float, y_max_mm: float) -> bool:
        '''Check if an item intersects the given Y range in mm.
        
        Returns True if the item should be drawn, False if it can be culled.
        '''
        item = self._items.get(item_id)
        if not item:
            return False
        
        item_type = item.get('type')
        
        # Get item Y bounds based on type
        if item_type in ('rectangle', 'oval'):
            item_y_min = item['y_mm']
            item_y_max = item['y_mm'] + item['h_mm']
        
        elif item_type in ('line', 'path', 'polygon'):
            points_mm = item.get('points_mm', [])
            if not points_mm:
                return True  # Draw empty items to be safe
            
            # Extract all Y coordinates (odd indices in flat list)
            y_coords = [points_mm[i] for i in range(1, len(points_mm), 2)]
            item_y_min = min(y_coords)
            item_y_max = max(y_coords)
        
        elif item_type == 'text':
            # Text baseline is at y_mm; approximate height from font size
            item_y_min = item['y_mm']
            # Rough estimate: text height ~= font_size_pt * 0.35mm (assuming ~72 DPI)
            font_size_mm = item.get('font_pt', 12) * 0.35
            item_y_max = item['y_mm'] + font_size_mm
        
        else:
            # Unknown type - draw it to be safe
            return True
        
        # Check intersection: item intersects range if NOT (completely above OR completely below)
        intersects = not (item_y_max < y_min_mm or item_y_min > y_max_mm)
        return intersects

    def _content_height_px(self) -> int:
        '''Height in pixels of the logical content at current scale.'''
        return int(round(max(0.0, self.height_mm * self._px_per_mm)))

    def _update_border(self):
        '''Update border color/width and rectangle position according to current layout and scroll.'''
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
        width_px = max(0.2, item['w_mm'] * self._px_per_mm)
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
        width_px = max(0.2, item['w_mm'] * self._px_per_mm)
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

        # Build CoreLabel for texture (bold to match PDF appearance)
        lbl = CoreLabel(text=text, font_name=self._get_courier_bold_font(), font_size=font_px, color=color_rgba)
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
            lbl = CoreLabel(text=item['text'], font_name=self._get_courier_bold_font(), font_size=font_px)
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
        '''Return bottom-left offsets (dx, dy) from the given anchor to the text box.

        Anchor names (case-insensitive):
        - 'top_left'|'tl', 'top'|'tc', 'top_right'|'tr'
        - 'left'|'cl', 'center'|'cc', 'right'|'cr'
        - 'bottom_left'|'bl', 'bottom'|'bc', 'bottom_right'|'br'
        '''
        a = (anchor or 'top_left').strip().lower()
        mapping = {
            'top_left': (0.0, -h_px), 'tl': (0.0, -h_px), 'nw': (0.0, -h_px),
            'top': (-w_px / 2.0, -h_px), 'tc': (-w_px / 2.0, -h_px), 'n': (-w_px / 2.0, -h_px),
            'top_right': (-w_px, -h_px), 'tr': (-w_px, -h_px), 'ne': (-w_px, -h_px),
            'left': (0.0, -h_px / 2.0), 'cl': (0.0, -h_px / 2.0), 'w': (0.0, -h_px / 2.0),
            'center': (-w_px / 2.0, -h_px / 2.0), 'cc': (-w_px / 2.0, -h_px / 2.0), 'c': (-w_px / 2.0, -h_px / 2.0),
            'right': (-w_px, -h_px / 2.0), 'cr': (-w_px, -h_px / 2.0), 'e': (-w_px, -h_px / 2.0),
            'bottom_left': (0.0, 0.0), 'bl': (0.0, 0.0), 'sw': (0.0, 0.0),
            'bottom': (-w_px / 2.0, 0.0), 'bc': (-w_px / 2.0, 0.0), 's': (-w_px / 2.0, 0.0),
            'bottom_right': (-w_px, 0.0), 'br': (-w_px, 0.0), 'se': (-w_px, 0.0),
        }
        return mapping.get(a, (0.0, -h_px))

    @staticmethod
    def _dist_point_to_segment(px, py, x1, y1, x2, y2) -> float:
        '''Distance from point P to segment AB (in mm).'''
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
        '''Ray casting algorithm (mm).'''
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
        '''Parse a '#RRGGBB' or '#RRGGBBAA' hex color into RGBA floats.'''
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
        '''Render a dashed polyline given points in px using on/off dash lengths.
        
        Applies viewport culling to skip creating dash segments outside the visible area,
        dramatically improving performance for long dashed lines (e.g., stave clef lines).
        Only applies Y-axis culling to predominantly vertical lines.
        '''
        if len(pts_px) < 4:
            return
        
        # Determine if this is a predominantly vertical line
        # Only apply Y-axis viewport culling to vertical lines
        x1, y1 = pts_px[0], pts_px[1]
        x2, y2 = pts_px[-2], pts_px[-1]
        dx = abs(x2 - x1)
        dy = abs(y2 - y1)
        is_vertical = dy > dx  # More vertical than horizontal
        
        # Get visible viewport bounds in pixels for Y-axis culling
        visible_y_min_px = None
        visible_y_max_px = None
        if is_vertical and self.scale_to_width and hasattr(self, '_view_h') and self._view_h > 0:
            # The pixel coordinates from _mm_to_px_point already include scroll offset in their calculation
            # So we just need to check against the widget's fixed viewport bounds
            buffer_px = 200.0  # Buffer zone to draw dashes slightly outside viewport
            
            # Viewport in Kivy coordinates (fixed widget bounds)
            viewport_bottom_y = self._view_y  # Bottom edge of widget viewport
            viewport_top_y = self._view_y + self._view_h  # Top edge of widget viewport
            
            # Visible range with buffer
            visible_y_min_px = viewport_bottom_y - buffer_px
            visible_y_max_px = viewport_top_y + buffer_px
        
        # Iterate segments
        on = True
        remaining = on_px
        cx, cy = pts_px[0], pts_px[1]
        dash_count = 0
        culled_count = 0
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
                    
                    # Viewport culling: only create Line if dash segment is visible
                    create_line = True
                    if visible_y_min_px is not None and visible_y_max_px is not None:
                        # Check if dash segment intersects visible Y range
                        seg_y_min = min(y1, y2)
                        seg_y_max = max(y1, y2)
                        if seg_y_max < visible_y_min_px or seg_y_min > visible_y_max_px:
                            create_line = False  # Skip this dash - outside viewport
                            culled_count += 1
                    
                    if create_line:
                        g.add(Line(points=[x1, y1, x2, y2], width=width_px))
                        dash_count += 1
                
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

    # ---------- Grid-based cursor snapping ----------
    
    def _snap_to_grid(self, time_position_mm: float) -> float:
        '''Snap a time position to the current grid step.'''
        # Use the same corrected calculation as the scroll system
        # to ensure cursor snapping matches the actual visual grid
        
        # Convert mm to quarters using the canvas' configured quarter spacing
        mm_per_quarter = float(self._quarter_note_spacing_mm)
        quarters = time_position_mm / mm_per_quarter
        # Get quarter note length from score if available
        quarter_note_length = 256.0
        if hasattr(self, 'piano_roll_editor') and self.piano_roll_editor and getattr(self.piano_roll_editor, 'score', None):
            ql = getattr(self.piano_roll_editor.score, 'quarterNoteLength', None)
            if isinstance(ql, (int, float)) and ql > 0:
                quarter_note_length = float(ql)
        
        # Convert quarters to ticks using the score's quarterNoteLength
        ticks = quarters * quarter_note_length

        # DEBUG: Print what's happening with detailed grid step info
        grid_step_ticks = self._get_grid_step_ticks()

        # Snap to grid step
        snapped_ticks = round(ticks / grid_step_ticks) * grid_step_ticks

        # Convert snapped ticks back to mm using the same quarter spacing
        snapped_mm = (snapped_ticks / quarter_note_length) * mm_per_quarter

        return snapped_mm
    
    def _update_cursor_position(self, touch_x_px: float):
        '''Update cursor position based on touch position with grid snapping.'''
        # Convert touch position to mm coordinates (we only care about x)
        mm_x, _ = self._px_to_mm(touch_x_px, 0)  # y doesn't matter for cursor position
        
        # Snap to grid
        snapped_mm_x = self._snap_to_grid(mm_x)
        
        # Store cursor position
        self._cursor_x_mm = snapped_mm_x
        
        # Redraw cursor if visible
        if self._cursor_visible:
            self._draw_cursor()
    
    def _draw_cursor(self):
        '''Draw or update the cursor line.'''
        # Remove existing cursor line if it exists
        if self._cursor_line_instr:
            self._items_group.remove(self._cursor_line_instr)
            self._cursor_line_instr = None
        
        if not self._cursor_visible:
            return
            
        # Convert cursor position to pixel coordinates (use any y for conversion)
        cursor_x_px, _ = self._mm_to_px_point(self._cursor_x_mm, 0)
        
        # Create dashed line from top to bottom of the editor area
        self._cursor_line_instr = InstructionGroup()
        
        # Set cursor color (accent color with transparency)
        cursor_color = (*ACCENT_COLOR[:3], 0.7)  # Add transparency
        self._cursor_line_instr.add(Color(*cursor_color))
        
        # Draw dashed vertical line
        y_top = self._view_y + self._view_h
        y_bottom = self._view_y
        
        # Use dashed line for cursor
        dash_length = 5.0  # 5px on
        gap_length = 3.0   # 3px off
        points = [cursor_x_px, y_bottom, cursor_x_px, y_top]
        self._draw_dashed_polyline(self._cursor_line_instr, points, 1.0, dash_length, gap_length)
        
        # Add cursor to the items group
        self._items_group.add(self._cursor_line_instr)
    
    def show_cursor(self):
        '''Show the cursor line.'''
        self._cursor_visible = True
        self._draw_cursor()
    
    def hide_cursor(self):
        '''Hide the cursor line.'''
        self._cursor_visible = False
        if self._cursor_line_instr:
            self._items_group.remove(self._cursor_line_instr)
            self._cursor_line_instr = None
    
    def get_cursor_position_mm(self) -> float:
        '''Get the current cursor position in mm.'''
        return self._cursor_x_mm
    
    def _calculate_grid_step_pixels(self) -> float:
        '''Calculate scroll step in pixels to exactly match visual grid spacing.
        
        This should match the exact visual distance between grid lines in the editor.
        Uses direct pixel calculation to avoid double conversion.
        '''
        # Get values directly from the score
        quarter_note_length = 256.0  # Default
        if hasattr(self, 'piano_roll_editor') and self.piano_roll_editor and hasattr(self.piano_roll_editor, 'score'):
            score = self.piano_roll_editor.score
            if score and hasattr(score, 'quarterNoteLength'):
                quarter_note_length = score.quarterNoteLength

        # Calculate how many quarter notes this grid step represents using editor grid selector when available
        grid_step_ticks = self._get_grid_step_ticks()
        grid_step_quarters = grid_step_ticks / quarter_note_length

        # Visual step in pixels should follow current canvas scale
        mm_per_quarter = float(self._quarter_note_spacing_mm)
        grid_step_pixels = grid_step_quarters * mm_per_quarter * max(1e-6, self._px_per_mm)

        return grid_step_pixels
