from __future__ import annotations
from typing import Optional, Dict, Any, Tuple, Callable, List
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.metrics import sp
import math

from file.SCORE import SCORE
from file.note import Note
from utils.canvas import Canvas
from utils.CONSTANTS import (
    PHYSICAL_SEMITONE_POSITIONS, BE_GAPS, BLACK_KEYS, PIANOTICK_QUARTER,
    MIDI_KEY_OFFSET, PIANO_KEY_COUNT,
    get_visual_semitone_positions
)
from editor.tool_manager import ToolManager
from editor.selection_manager import SelectionManager
from editor.drawer import (
    StaveDrawerMixin, GridDrawerMixin, NoteDrawerMixin, GraceNoteDrawerMixin,
    BeamDrawerMixin, SlurDrawerMixin, TextDrawerMixin, TempoDrawerMixin,
    CountLineDrawerMixin, LineBreakDrawerMixin
)


class Editor(
    StaveDrawerMixin, 
    GridDrawerMixin,
    NoteDrawerMixin,
    GraceNoteDrawerMixin,
    BeamDrawerMixin,
    SlurDrawerMixin,
    TextDrawerMixin,
    TempoDrawerMixin,
    CountLineDrawerMixin,
    LineBreakDrawerMixin
):
    '''
    Vertical Piano Roll Editor based on the original Tkinter design.
    
    Layout follows your specific design patterns:
    - 88 piano keys with 103 physical semitone positions meaning that 
        some key positions (BE_GAPS) are skipped (are no valid positions)
    - BE gaps for visual spacing between key groups
    - Specific line patterns (two-line, three-line, clef-line)
    - Time flows vertically (top to bottom)
    - Pitch flows horizontally with your custom spacing
    '''
    
    def __init__(self, editor_canvas: Canvas, score: SCORE = None, gui=None):
        self.canvas: Canvas = editor_canvas
        self.score: SCORE = None  # Will be initialized via new_score() or load_score()
        self.gui = gui
        
        # Initialize dimensions from canvas
        # Zoom: single source of truth is SCORE.properties.editorZoomPixelsQuarter (px per quarter)
        # Will be set from SCORE in _apply_settings_from_score() below
        self.pixels_per_quarter = 250.0  # Temporary safe default
        
        # Stave & grid configuration defaults (overridden by SCORE properties below)
        self.stave_two_color = '#000000'
        self.stave_three_color = '#000000'
        self.stave_clef_color = '#000000'
        self.stave_two_width = 0.125
        self.stave_three_width = 0.25
        self.stave_clef_width = 0.125

        self.barline_color = '#000000'
        self.barline_width = 0.25
        self.gridline_color = '#000000'
        self.gridline_width = 0.125
        self.gridline_dash_pattern = [2, 2]
        self.clef_dash_pattern = [2, 2]

        # Immediately apply preferences (incl. zoom) from SCORE model to avoid mismatch
        self._apply_settings_from_score()
        
        # Current view state
        self.scroll_time_offset: float = 0.0
        self.selected_notes: List[Note] = []
        
        # Initialize tool system
        self.tool_manager = ToolManager(self)
        self.tool_manager.set_active_tool('Note')  # Default tool
        
        # Initialize selection manager (universal selection across all tools)
        self.selection_manager = SelectionManager(self)
        
        # Mouse tracking for drag detection
        self._mouse_button_down: Optional[str] = None  # 'left' or 'right' when button is down
        self._mouse_down_pos: Optional[Tuple[float, float]] = None  # (x_mm, y_mm) where button went down
        
        # Cursor management for hover (restore tool cursor on enter/leave)
        self._is_hovering = False
        Window.bind(mouse_pos=self._update_cursor_on_hover)

        # all pianoroll variables here:
        self.total_time: float = 0.0
        
        # Initialize layout
        self._calculate_layout()
        
        # Mark editor as ready for drawing (all initialization complete)
        self._ready: bool = True
        
        # TEST: Verify freeze_updates blocks frame rendering (REMOVE AFTER TESTING)
        # Uncomment to test - mouse cursor should freeze for 3 seconds
        # Clock.schedule_once(lambda dt: self.canvas.test_freeze_at_startup(3.0), 1.0)

    def _apply_settings_from_score(self):
        '''Synchronize editor state from SCORE.properties.

        - Zoom (editorZoomPixelsQuarter)
        - Stave visuals (globalStave)
        - Grid/barline visuals (globalBasegrid)
        Called in __init__ and whenever SCORE/properties change so drawing uses the
        SCORE's values from the start. Fallbacks use safe defaults when properties are missing.
        '''
        if not self.score or not hasattr(self.score, 'properties'):
            return

        properties = self.score.properties

        # Zoom (px per quarter) - ALWAYS read from SCORE
        if hasattr(properties, 'editorZoomPixelsQuarter'):
            try:
                self.pixels_per_quarter = float(properties.editorZoomPixelsQuarter)
            except Exception:
                # Keep current value on parse error
                pass

        # Stave (line widths, colors, dash pattern)
        if hasattr(properties, 'globalStave') and properties.globalStave is not None:
            stave = properties.globalStave
            self.stave_two_color = getattr(stave, 'twoLineColor', self.stave_two_color)
            self.stave_three_color = getattr(stave, 'threeLineColor', self.stave_three_color)
            self.stave_clef_color = getattr(stave, 'clefColor', self.stave_clef_color)

            self.stave_two_width = getattr(stave, 'twoLineWidth', self.stave_two_width)
            self.stave_three_width = getattr(stave, 'threeLineWidth', self.stave_three_width)
            self.stave_clef_width = getattr(stave, 'clefWidth', self.stave_clef_width)

            self.clef_dash_pattern = getattr(stave, 'clefDashPattern', self.clef_dash_pattern)

        # Grid (bar/grid line widths, colors, dash)
        if hasattr(properties, 'globalBasegrid') and properties.globalBasegrid is not None:
            basegrid = properties.globalBasegrid
            self.barline_color = getattr(basegrid, 'barlineColor', self.barline_color)
            self.barline_width = getattr(basegrid, 'barlineWidth', self.barline_width)
            self.gridline_color = getattr(basegrid, 'gridlineColor', self.gridline_color)
            self.gridline_width = getattr(basegrid, 'gridlineWidth', self.gridline_width)
            self.gridline_dash_pattern = getattr(basegrid, 'gridlineDashPattern', self.gridline_dash_pattern)

    # Defer zoom refresh until the canvas attaches us and scale is known.
    
    def load_score(self, score: SCORE):
        '''Load a new score into the editor and redraw.'''
        self.score = score
        print(f'Editor: load_score() called with score containing {len(score.baseGrid)} baseGrids')
        if score.baseGrid:
            print(f'Editor: First baseGrid has {score.baseGrid[0].measureAmount} measures')
        self.gui.set_properties_score(self.score)
        self._apply_settings_from_score()
        
        # Clear any active selection from previous file
        if hasattr(self, 'selection_manager') and self.selection_manager:
            self.selection_manager.clear_selection()
        
        # Reset scroll position to the beginning
        self.scroll_time_offset = 0.0
        # Trigger a full redraw with the new score
        print('Editor: Calling redraw_pianoroll() from load_score()')
        self.redraw_pianoroll()

    def new_score(self):
        '''Create a new empty score and load it into the editor.'''
        print('Editor: Creating new SCORE')
        self.load_score(SCORE())
        self.gui._simulate_snap_drag()
    
    # Defer zoom refresh until the canvas attaches us and scale is known.
    
    def _calculate_layout(self):
        '''Calculate layout dimensions based on the old Tkinter design.'''
        # Skip if canvas not sized yet (widget not laid out)
        if self.canvas.width <= 1 or self.canvas.height <= 1:
            print(f'Editor: _calculate_layout() skipped - canvas not sized yet (w={self.canvas.width}px, h={self.canvas.height}px)')
            return
            
        self.editor_margin = self.canvas.width_mm / 6  # Your margin calculation
        
        # Calculate stave dimensions using shared constants
        # The stave should span the full visual width
        visual_semitone_positions = get_visual_semitone_positions()  # Returns 98
        total_width = self.canvas.width_mm - (2 * self.editor_margin)
        self.semitone_width = total_width / visual_semitone_positions
        # Stave width spans the full width (no reduction)
        self.stave_width = total_width
        
        # Effective editor width equals logical canvas width in mm.
        # When a scrollbar is visible, Canvas reduces px-per-mm so x=width_mm maps to
        # the right boundary before the scrollbar automatically.
        self.editor_width = self.canvas.width_mm
        
        # Update canvas quarter note spacing for musical scrolling in millimeters
        # Convert pixels to mm: pixels_per_quarter / pixels_per_mm = mm_per_quarter
        # Derive mm-per-quarter using nominal px/mm based on full widget width
        # This decouples quarter spacing from scrollbar presence, preventing height inflation.
        px_per_mm_nominal = max(1e-6, float(self.canvas.width) / max(1e-6, float(self.canvas.width_mm)))
        quarter_note_mm = float(self.pixels_per_quarter) / px_per_mm_nominal
        self.canvas.set_quarter_note_spacing_mm(quarter_note_mm)
    
    @property
    def width(self) -> float:
        '''Canvas width in mm.'''
        return self.canvas.width_mm
    
    @property 
    def height(self) -> float:
        '''Canvas height in mm.'''
        return self.canvas.height_mm
    
    def pitch_to_x(self, key_number: int) -> float:
        '''Convert piano key number (1-88) to X position using your spacing algorithm.'''
        # Build x_positions list exactly like x_to_pitch does (must match!)
        x_pos = self.editor_margin - self.semitone_width
        x_positions = [x_pos]  # Start with initial position at index 0
        
        for n in range(1, PIANO_KEY_COUNT + 1):
            # Add extra space at BE gaps (your specific spacing)
            if n in BE_GAPS:
                x_pos += self.semitone_width
            x_pos += self.semitone_width
            x_positions.append(x_pos)
        
        # x_to_pitch returns (index + 1), so to reverse it:
        # If x_to_pitch found x_positions[index] and returned (index + 1) as the key,
        # then pitch_to_x should return x_positions[key_number - 1]
        if 1 <= key_number <= PIANO_KEY_COUNT:
            return x_positions[key_number - 1]
        return self.editor_margin
    
    def x_to_pitch(self, x_mm: float) -> int:
        '''Convert X coordinate to piano key number (1-88) using your algorithm.'''
        # Recreate the x_positions list from your Tkinter code
        x_pos = self.editor_margin - self.semitone_width
        x_positions = [x_pos]
        
        # create center positions for all 88 keys
        for n in range(1, PIANO_KEY_COUNT + 1):
            if n in BE_GAPS:
                x_pos += self.semitone_width
            x_pos += self.semitone_width
            x_positions.append(x_pos)

        # Find the closest center position
        if x_positions:
            closest_x = min(x_positions, key=lambda y: abs(y - x_mm))
            closest_x_index = x_positions.index(closest_x)
            return closest_x_index + 1
        
        # Default to key 1 if no positions found
        print('DEBUG: x_to_key_number found no positions, defaulting to key 1')
        return 1
    
    def time_to_y(self, time_ticks: float) -> float:
        '''Convert time in ticks to Y coordinate in millimeters (top-left origin).'''
        mm_per_quarter = getattr(self.canvas, '_quarter_note_spacing_mm', None)
        if not isinstance(mm_per_quarter, (int, float)) or mm_per_quarter <= 0:
            # Fallback derive from score zoom and current canvas scale
            px_per_mm = getattr(self.canvas, '_px_per_mm', 3.7795)
            mm_per_quarter = (self.pixels_per_quarter) / max(1e-6, px_per_mm)
        ql = getattr(self.score, 'quarterNoteLength', PIANOTICK_QUARTER)
        time_quarters = time_ticks / max(1e-6, ql)
        result = self.editor_margin + (time_quarters * mm_per_quarter) - (self.scroll_time_offset * mm_per_quarter)
        return result
    
    def y_to_time(self, y_mm: float) -> float:
        '''Convert Y coordinate to time in ticks (inverse of time_to_y_mm).'''
        mm_per_quarter = getattr(self.canvas, '_quarter_note_spacing_mm', None)
        if not isinstance(mm_per_quarter, (int, float)) or mm_per_quarter <= 0:
            px_per_mm = getattr(self.canvas, '_px_per_mm', 3.7795)
            mm_per_quarter = (self.pixels_per_quarter) / max(1e-6, px_per_mm)
        time_quarters = (y_mm - self.editor_margin) / mm_per_quarter + self.scroll_time_offset
        ql = getattr(self.score, 'quarterNoteLength', PIANOTICK_QUARTER)
        return time_quarters * ql
    
    def auto_scroll_if_near_edge(self, y_mm: float) -> bool:
        '''Auto-scroll the editor if mouse is near the top or bottom edge.
        
        Args:
            y_mm: Current mouse Y position in mm coordinates
            
        Returns:
            True if scrolling occurred, False otherwise
        '''
        canvas = self.canvas
        
        # Convert mm mouse position to widget pixel coordinates
        _, y_widget_px = canvas._mm_to_px_point(0, y_mm)
        
        scroll_margin_px = 40  # pixels from edge to trigger auto-scroll
        scroll_speed_mm = 2.5  # mm to scroll per call
        
        # Get viewport bounds in px
        viewport_bottom_px = canvas._view_y
        viewport_top_px = canvas._view_y + canvas._view_h
        
        scrolled = False
        
        # Scroll down if near bottom of widget
        if y_widget_px < viewport_bottom_px + scroll_margin_px:
            content_height_px = canvas._content_height_px()
            viewport_height_px = canvas.height
            max_scroll = max(0, content_height_px - viewport_height_px)
            new_scroll = min(max_scroll, canvas._scroll_px + scroll_speed_mm * canvas._px_per_mm)
            canvas._scroll_px = new_scroll
            canvas._redraw_all()
            # Update scrollbar handle position
            if hasattr(canvas, 'custom_scrollbar'):
                canvas.custom_scrollbar.update_layout()
            scrolled = True
        # Scroll up if near top of widget
        elif y_widget_px > viewport_top_px - scroll_margin_px:
            new_scroll = max(0, canvas._scroll_px - scroll_speed_mm * canvas._px_per_mm)
            canvas._scroll_px = new_scroll
            canvas._redraw_all()
            # Update scrollbar handle position
            if hasattr(canvas, 'custom_scrollbar'):
                canvas.custom_scrollbar.update_layout()
            scrolled = True
        
        return scrolled
    
    def get_score_length_in_ticks(self) -> float:
        '''Calculate total score length in ticks based on your algorithm.'''
        total_ticks = 0.0
        for grid in self.score.baseGrid:
            ql = getattr(self.score, 'quarterNoteLength', PIANOTICK_QUARTER)
            measure_ticks = (ql * 4) * (grid.numerator / grid.denominator)
            total_ticks += measure_ticks * grid.measureAmount
        return total_ticks
    
    def get_barline_positions(self) -> List[float]:
        '''Get list of barline positions in ticks.
        
        This method calculates where barlines occur in the score based on the
        baseGrid configuration. It can be reused by the editor and engraver.
        
        Returns:
            List of tick positions where barlines should be drawn.
        '''
        barline_positions = []
        total_ticks = 0.0
        
        for grid in self.score.baseGrid:
            ql = getattr(self.score, 'quarterNoteLength', PIANOTICK_QUARTER)
            measure_ticks = (ql * 4) * (grid.numerator / grid.denominator)
            
            for _ in range(grid.measureAmount):
                # Barline at the end of this measure
                barline_positions.append(total_ticks)
                total_ticks += measure_ticks
        
        return barline_positions
    
    def redraw_pianoroll(self):
        '''Redraw the complete piano roll with all elements.
        
        This is the main rendering method. It:
        1. Syncs zoom from SCORE.properties.editorZoomPixelsQuarter
        2. Recalculates layout (margins, spacing, etc.)
        3. Clears and redraws all canvas elements
        '''
        
        # Guard: don't draw if no score loaded yet
        if self.score is None:
            print('Editor: redraw_pianoroll() called but no score loaded yet')
            return
        
        # Always sync zoom from SCORE first
        try:
            props = getattr(self.score, 'properties', None)
            if props is not None and hasattr(props, 'editorZoomPixelsQuarter'):
                self.pixels_per_quarter = float(props.editorZoomPixelsQuarter)
        except Exception:
            pass
        
        # Recalculate layout with current zoom
        self._calculate_layout()
        
        # Clear any existing content
        self.canvas.clear()
        
        # Calculate required dimensions
        self.total_time = self.get_score_length_in_ticks()
        print(f'Editor: Calculated total_time={self.total_time} ticks from {len(self.score.baseGrid)} baseGrids')
        # Content height must not depend on scroll offset; compute using mm/quarter directly
        mm_per_quarter = getattr(self.canvas, '_quarter_note_spacing_mm', None)
        if not isinstance(mm_per_quarter, (int, float)) or mm_per_quarter <= 0:
            px_per_mm = getattr(self.canvas, '_px_per_mm', 3.7795)
            mm_per_quarter = (self.pixels_per_quarter) / max(1e-6, px_per_mm)
            print(f'Editor: Calculated mm_per_quarter={mm_per_quarter} from pixels_per_quarter={self.pixels_per_quarter} / px_per_mm={px_per_mm}')
        ql = getattr(self.score, 'quarterNoteLength', PIANOTICK_QUARTER)
        content_height_mm = (self.total_time / max(1e-6, ql)) * mm_per_quarter
        total_height_mm = content_height_mm + (2.0 * self.editor_margin)  # top + bottom margin equal to editor_margin
        
        # Reconcile canvas height to desired content height (shrink or grow).
        # Use tolerance to avoid thrashing on tiny deltas; preserve scroll position.
        desired_height_mm = float(total_height_mm)
        current_height_mm = float(self.canvas.height_mm)
        if abs(desired_height_mm - current_height_mm) > 0.1:
            action = 'Expanding' if desired_height_mm > current_height_mm else 'Shrinking'
            # Keep scroll; Canvas clamps if out-of-bounds. Avoid reset to prevent jumpiness.
            self.canvas.set_size_mm(self.canvas.width_mm, desired_height_mm, reset_scroll=False)
        
        # Draw all elements:
        self._draw_stave()
        self._draw_barlines_and_grid()
        self._draw_notes()
        self._draw_grace_notes()
        self._draw_beams()
        self._draw_slurs()
        self._draw_texts()
        self._draw_tempos()
        self._draw_count_lines()
        self._draw_line_breaks()

        # Force canvas redraw with culling now that all items are added
        self.canvas._redraw_all()
    
    # Removed update_drawing_order() - no longer needed!
    # Drawing order is now set automatically by tags when items are created.
    
    # Zoom and interaction methods (simplified for initial implementation)
    def zoom_in(self, factor: float = 1.2):
        '''Increase SCORE.properties.editorZoomPixelsQuarter by factor (px per quarter).'''
        try:
            current = float(self.pixels_per_quarter)
            new_ppq = max(1.0, current * float(factor))
            self.pixels_per_quarter = new_ppq
            self._update_score_zoom()
            self._calculate_layout()
            self.redraw_pianoroll()
        except Exception as e:
            print(f'DEBUG: zoom_in failed: {e}')
    
    def zoom_out(self, factor: float = 1.2):
        '''Decrease SCORE.properties.editorZoomPixelsQuarter by factor (px per quarter).'''
        try:
            current = float(self.pixels_per_quarter)
            new_ppq = max(1.0, current / float(factor))
            self.pixels_per_quarter = new_ppq
            self._update_score_zoom()
            self._calculate_layout()
            self.redraw_pianoroll()
        except Exception as e:
            print(f'DEBUG: zoom_out failed: {e}')
    
    def set_zoom_pixels_per_quarter(self, pixels: float):
        '''Set the zoom level directly (px per quarter) and update SCORE + layout.'''
        try:
            self.pixels_per_quarter = max(1.0, float(pixels))
            self._update_score_zoom()
            self._calculate_layout()
            self.redraw_pianoroll()
        except Exception as e:
            print(f'DEBUG: set_zoom_pixels_per_quarter failed: {e}')

    def zoom_refresh(self):
        '''Re-apply current zoom without changing SCORE's editorZoomPixelsQuarter.

        This performs the same processing pipeline as zoom_in/zoom_out but keeps
        the SCORE.properties.editorZoomPixelsQuarter value unchanged. Useful when
        the canvas scale (px-per-mm) changes or after (re)attaching the editor.
        Ensures Canvas view/scale have finished updating before re-rendering so
        widget size changes are reflected correctly.
        '''
        try:
            cv = self.canvas

            # Defer until Canvas has applied latest size/scale; retry briefly if not ready.
            def _attempt(_dt, attempts: int = 0, last_px_per_mm: float = None):
                try:
                    px_per_mm = float(getattr(cv, '_px_per_mm', 0.0))
                    view_w = int(getattr(cv, '_view_w', 0))
                    view_h = int(getattr(cv, '_view_h', 0))

                    # Ready when we have non-zero scale and a sized viewport.
                    ready = px_per_mm > 0.0 and view_w > 0 and view_h > 0
                    # If scale is still changing between frames, wait one more frame.
                    scale_changed = (last_px_per_mm is not None) and (abs(px_per_mm - last_px_per_mm) > 1e-6)

                    if (not ready or scale_changed) and attempts < 20:
                        Clock.schedule_once(lambda dt: _attempt(dt, attempts + 1, px_per_mm), 0)
                        # Only bail out early if not ready; if only scale_changed, allow settle next frame
                        if not ready:
                            return

                    # Keep internal state in sync with SCORE without persisting any change
                    # Keep internal state in sync with SCORE without persisting any change
                    try:
                        props = getattr(self.score, 'properties', None)
                        if props is not None and hasattr(props, 'editorZoomPixelsQuarter'):
                            self.pixels_per_quarter = float(props.editorZoomPixelsQuarter)
                    except Exception:
                        pass

                    # Recompute layout with current canvas scale and re-render content height
                    self._calculate_layout()
                    self.redraw_pianoroll()
                except Exception as inner_e:
                    print(f'DEBUG: zoom_refresh inner failed: {inner_e}')

            # Kick off on next frame to let any pending canvas layout settle
            Clock.schedule_once(lambda dt: _attempt(dt, 0, float(getattr(cv, '_px_per_mm', 0.0))), 0)
        except Exception as e:
            print(f'DEBUG: zoom_refresh failed: {e}')
    
    def _update_score_zoom(self):
        '''Persist current pixels_per_quarter to SCORE.properties.editorZoomPixelsQuarter.'''
        if (hasattr(self.score, 'properties') and 
            hasattr(self.score.properties, 'editorZoomPixelsQuarter')):
            self.score.properties.editorZoomPixelsQuarter = float(self.pixels_per_quarter)
    
    # === Interaction support ===
    def on_item_click(self, item_id: int, touch_pos_mm: Tuple[float, float]) -> bool:
        '''Handle click on canvas items.'''
        if item_id in self.canvas._items:
            canvas_item = self.canvas._items[item_id]
            item_tags = canvas_item.get('tags', set())
            
            for tag in item_tags:
                if tag.startswith('note_'):
                    parts = tag.split('_')
                    if len(parts) >= 3:
                        stave_idx = int(parts[1])
                        note_id = int(parts[2])
                        note = self.find_note_by_id(stave_idx, note_id)
                        if note:
                            self._select_note(note)
                            return True
        return False

    def on_key_press(self, key: str, x: float, y: float, modifiers: list = None) -> bool:
        """Handle keyboard events and dispatch to active tool.
        
        Args:
            key: The key that was pressed
            x: Current mouse x position in mm
            y: Current mouse y position in mm
            modifiers: List of modifier keys currently pressed (e.g., ['ctrl'], ['meta'])
            
        Returns:
            True if handled by tool, False otherwise
        """
        if modifiers is None:
            modifiers = []
        
        # First, let selection manager try to handle (for copy/paste/delete/arrows/escape)
        if self.selection_manager.on_key_press(key, x, y, modifiers):
            return True
        
        # If Escape wasn't handled by selection (no active selection), request app exit
        if key == 'escape':
            try:
                from kivy.app import App
                app = App.get_running_app()
                if hasattr(app, 'file_manager') and app.file_manager:
                    app.file_manager.exit_app()
                    return True
            except Exception:
                return False
        
        # Otherwise, dispatch to active tool
        if self.tool_manager:
            return self.tool_manager.on_key_press(key, x, y)
        return False
    
    def find_note_by_id(self, stave_idx: int, note_id: int) -> Optional[Note]:
        '''Find a note by stave index and note ID.'''
        if 0 <= stave_idx < len(self.score.stave):
            for note in self.score.stave[stave_idx].event.note:
                if note.id == note_id:
                    return note
        return None
    
    def _select_note(self, note: Note):
        '''Select a note for editing.'''
        self.selected_notes.clear()
        self.selected_notes.append(note)
        print(f'Selected note: Key={note.pitch-20}, Time={note.time}, Duration={note.duration}')

    def get_grid_step_ticks(self) -> float:
        '''Return current grid step in ticks from grid_selector/canvas.'''
        try:
            gs = getattr(self, 'grid_selector', None)
            if gs is not None and hasattr(gs, 'get_grid_step'):
                val = gs.get_grid_step()
                if isinstance(val, (int, float)) and val > 0:
                    return float(val)
        except Exception:
            pass
        # Fallback to canvas' grid step
        try:
            if hasattr(self.canvas, 'get_grid_step'):
                val = self.canvas.get_grid_step()
                if isinstance(val, (int, float)) and val > 0:
                    return float(val)
        except Exception:
            pass
        return float(PIANOTICK_QUARTER)

    def get_grid_step(self) -> float:
        '''Expose grid step for other components (canvas fallback).'''
        return self.get_grid_step_ticks()

    # === Tool System Event Handlers ===
    
    def handle_mouse_down(self, x: float, y: float, button: str) -> bool:
        """
        Handle mouse button press.
        
        Args:
            x, y: Mouse position in mm coordinates
            button: 'left' or 'right'
            
        Returns:
            True if event was handled
        """
        print(f"DEBUG Editor.handle_mouse_down: button={button}, pos=({x:.1f}, {y:.1f})")
        
        # Track which button is down and where
        self._mouse_button_down = button
        self._mouse_down_pos = (x, y)
        
        if button == 'left':
            # Check if selection manager wants to handle this (Shift key pressed)
            if self.selection_manager.on_left_press(x, y):
                return True  # Selection manager is handling it
            
            # Otherwise, dispatch to active tool
            return self.tool_manager.dispatch_left_press(x, y)
        elif button == 'right':
            # Track right press for potential drag-to-select
            self.selection_manager.on_right_press(x, y)
            # Don't consume - let tool handle click if no drag occurs
            return False
        return False
    
    def handle_mouse_up(self, x: float, y: float, button: str, was_dragging: bool = False) -> bool:
        """
        Handle mouse button release.
        
        Args:
            x, y: Mouse position in mm coordinates
            button: 'left' or 'right'
            was_dragging: Whether this was a drag operation
            
        Returns:
            True if event was handled
        """
        print(f"DEBUG Editor.handle_mouse_up: button={button}, _mouse_button_down={self._mouse_button_down}, pos=({x:.1f}, {y:.1f})")
        # Check if this was the button that was down
        if self._mouse_button_down != button:
            print(f"DEBUG Editor.handle_mouse_up: Button mismatch, returning False")
            return False
        
        # Determine if it was a drag based on tool's internal state
        # The tool's on_mouse_move already detected and handled dragging
        # We just need to dispatch the release event
        if button == 'left':
            # Check if selection manager wants to handle this (if it's drawing rectangle)
            if self.selection_manager.on_left_release(x, y):
                # Clear tracking state
                self._mouse_button_down = None
                self._mouse_down_pos = None
                return True  # Selection manager handled it
            
            # Otherwise, dispatch to active tool
            result = self.tool_manager.dispatch_left_release(x, y)
            # If not dragging, also dispatch click
            active_tool = self.tool_manager.get_active_tool()
            if active_tool and not active_tool._is_dragging:
                self.tool_manager.dispatch_left_click(x, y)
        elif button == 'right':
            # Check if selection manager is finishing rectangle selection
            if self.selection_manager.on_right_release(x, y):
                # Clear tracking state
                self._mouse_button_down = None
                self._mouse_down_pos = None
                return True  # Selection manager handled it
            
            # Right-click without drag - check if tool handled an element deletion
            # If not, clear selection (right-click in empty space)
            active_tool = self.tool_manager.get_active_tool()
            
            # First, dispatch to active tool
            result = self.tool_manager.dispatch_right_release(x, y)
            
            # If not dragging, also dispatch click to tool
            if active_tool and not active_tool._is_dragging:
                tool_handled = self.tool_manager.dispatch_right_click(x, y)
                
                # If tool didn't handle it (no element at position), clear selection
                if not tool_handled:
                    print(f"DEBUG Editor: Right-click in empty space, clearing selection")
                    self.selection_manager.clear_selection()
                    result = True  # We handled it by clearing selection
        else:
            result = False
        
        # Clear tracking state
        self._mouse_button_down = None
        self._mouse_down_pos = None
        
        return result
        
        return result
    
    def handle_mouse_move(self, x: float, y: float) -> bool:
        """
        Handle mouse movement.
        
        Args:
            x, y: Mouse position in mm coordinates
            
        Returns:
            True if event was handled
        """
        # Auto-scroll when mouse is near top or bottom edge (40px margin)
        # Trigger for both left (tool drag) and right (selection rectangle) mouse buttons
        if self._mouse_button_down in ('left', 'right'):
            self.auto_scroll_if_near_edge(y)
        
        # Always track mouse position for selection manager
        self.selection_manager.on_mouse_move(x, y)
        
        # Check if selection manager is handling drag
        if self._mouse_button_down == 'left' and self._mouse_down_pos:
            if self.selection_manager.on_left_drag(x, y):
                return True  # Selection manager is handling the drag
        elif self._mouse_button_down == 'right' and self._mouse_down_pos:
            if self.selection_manager.on_right_drag(x, y):
                return True  # Selection manager is handling the drag
        
        # Otherwise, dispatch to active tool
        return self.tool_manager.dispatch_mouse_move(x, y)
    
    def handle_double_click(self, x: float, y: float) -> bool:
        """
        Handle double-click event.
        
        Args:
            x, y: Mouse position in mm coordinates
            
        Returns:
            True if event was handled
        """
        # Forward to active tool
        return self.tool_manager.dispatch_double_click(x, y)
    
    def set_active_tool(self, tool_name: str) -> bool:
        """
        Set the active tool by name.
        
        Args:
            tool_name: Name of the tool to activate
            
        Returns:
            True if tool was activated successfully
        """
        result = self.tool_manager.set_active_tool(tool_name)
        
        # Update cursor if mouse is currently over editor
        if result and self._is_hovering:
            active_tool = self.tool_manager.get_active_tool()
            if active_tool:
                Window.set_system_cursor(active_tool.cursor)
        
        return result
    
    def _update_cursor_on_hover(self, window, pos):
        """
        Update cursor based on whether mouse is over editor canvas.
        
        Called automatically when mouse position changes.
        Sets the active tool's cursor when over editor view.
        Does nothing when outside to preserve other cursor configurations (sash resize, etc.).
        Also forwards mouse movement to the active tool for hover previews.
        """
        # Check if mouse is within the actual editor view area (excluding scrollbar)
        if not hasattr(self.canvas, '_point_in_view_px'):
            return
        
        # Use Canvas's _point_in_view_px which excludes the scrollbar area
        is_hovering = self.canvas._point_in_view_px(*pos)
        
        # Only set cursor when over editor view
        # When outside, do nothing to preserve other widget's cursor settings
        if is_hovering:
            active_tool = self.tool_manager.get_active_tool()
            if active_tool:
                Window.set_system_cursor(active_tool.cursor)
            
            # Forward mouse position to tool system (for hover previews, etc.)
            if hasattr(self.canvas, '_px_to_mm'):
                try:
                    # Convert pixel coordinates to mm
                    mm_x, mm_y = self.canvas._px_to_mm(*pos)
                    # Dispatch to active tool
                    self.handle_mouse_move(mm_x, mm_y)
                except Exception as e:
                    print(f'EDITOR: mouse move dispatch failed: {e}')
        
        # Track state for potential future use
        self._is_hovering = is_hovering
