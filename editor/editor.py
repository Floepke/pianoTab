from __future__ import annotations
from typing import Optional, Dict, Any, Tuple, Callable, List
from kivy.clock import Clock
from kivy.metrics import sp
import math

from file.SCORE import SCORE
from file.note import Note
from utils.canvas import Canvas
from utils.CONSTANTS import (
    PHYSICAL_SEMITONE_POSITIONS, BE_GAPS, BLACK_KEYS, PIANOTICK_QUARTER,
    MIDI_KEY_OFFSET, PIANO_KEY_COUNT, DEFAULT_PIXELS_PER_QUARTER,
    get_visual_semitone_positions, midi_to_key_number, key_number_to_midi,
    ticks_to_quarters, quarters_to_ticks, is_black_key, has_be_gap
)

class Editor:
    '''
    Vertical Piano Roll Editor based on the original Tkinter design.
    
    Layout follows your specific design patterns:
    - 88 piano keys with 103 physical semitone positions
    - BE gaps for visual spacing between key groups
    - Specific line patterns (two-line, three-line, clef-line)
    - Time flows vertically (top to bottom)
    - Pitch flows horizontally with your custom spacing
    '''
    
    def __init__(self, editor_canvas: Canvas, score: SCORE = None):
        self.canvas: Canvas = editor_canvas  # Fixed: use consistent attribute name
        self.score: SCORE = score if score is not None else self._create_default_score_template()
        
        # Initialize dimensions from canvas
        # Zoom: single source of truth is SCORE.properties.editorZoomPixelsQuarter (px per quarter)
        # Start with a safe default; _apply_settings_from_score will sync from SCORE
        self.pixels_per_quarter = float(DEFAULT_PIXELS_PER_QUARTER)
        
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
        # Timeline cursor state (ticks from start; None = hidden)
        self.cursor_time: Optional[float] = None
        self._cursor_item_id: Optional[int] = None
        
        # Initialize layout
        self._calculate_layout()

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

        # Zoom (px per quarter)
        if hasattr(properties, 'editorZoomPixelsQuarter') and properties.editorZoomPixelsQuarter:
            try:
                self.pixels_per_quarter = float(properties.editorZoomPixelsQuarter)
                print(f'DEBUG: Using SCORE editorZoomPixelsQuarter: {self.pixels_per_quarter} pixels')
            except Exception:
                # Keep current/default on parse error
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
    
    def _create_default_score_template(self) -> SCORE:
        '''Create a default score with a single stave and exactly one base grid.'''
        score = SCORE()
        
        # Ensure single known stave name
        if score.stave:
            score.stave[0].name = 'Single Piano Stave'
        
        # SCORE.__post_init__ already ensures a default BaseGrid exists.
        # Avoid doubling the time length: normalize to exactly ONE baseGrid and set desired signature/length.
        if score.baseGrid:
            bg = score.baseGrid[0]
            bg.numerator = 4
            bg.denominator = 4
            bg.measureAmount = 32
            # Keep gridTimes as provided by SCORE defaults
            score.baseGrid = [bg]
        else:
            score.new_basegrid(numerator=4, denominator=4, measureAmount=32)

        # create linebreaks in groups of 4 measures
        score.new_linebreak(time=1024*4)
        score.new_linebreak(time=1024*8)
        score.new_linebreak(time=1024*12)
        score.new_linebreak(time=1024*16)
        score.new_linebreak(time=1024*20)
        score.new_linebreak(time=1024*24)
        score.new_linebreak(time=1024*28)

        return score
    
    # Defer zoom refresh until the canvas attaches us and scale is known.
    
    def _calculate_layout(self):
        '''Calculate layout dimensions based on the old Tkinter design.'''
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
    
    def key_to_x_position(self, key_number: int) -> float:
        '''Convert piano key number (1-88) to X position using your spacing algorithm.'''
        x_positions = []
        x_pos = self.editor_margin - self.semitone_width
        
        for n in range(1, PIANO_KEY_COUNT + 1):
            # Add extra space at BE gaps (your specific spacing)
            if has_be_gap(n):
                x_pos += self.semitone_width
            x_pos += self.semitone_width
            x_positions.append(x_pos)
        
        if 1 <= key_number <= PIANO_KEY_COUNT:
            return x_positions[key_number - 1]
        return self.editor_margin
    
    def _time_to_y_mm(self, time_ticks: float) -> float:
        '''Convert time in ticks to Y coordinate in millimeters (top-left origin).'''
        mm_per_quarter = getattr(self.canvas, '_quarter_note_spacing_mm', None)
        if not isinstance(mm_per_quarter, (int, float)) or mm_per_quarter <= 0:
            # Fallback derive from score zoom and current canvas scale
            px_per_mm = getattr(self.canvas, '_px_per_mm', 3.7795)
            mm_per_quarter = (self.pixels_per_quarter) / max(1e-6, px_per_mm)
        ql = getattr(self.score, 'quarterNoteLength', PIANOTICK_QUARTER)
        time_quarters = time_ticks / max(1e-6, ql)
        return self.editor_margin + (time_quarters * mm_per_quarter) - (self.scroll_time_offset * mm_per_quarter)
    
    def _get_score_length_in_ticks(self) -> float:
        '''Calculate total score length in ticks based on your algorithm.'''
        total_ticks = 0.0
        for grid in self.score.baseGrid:
            ql = getattr(self.score, 'quarterNoteLength', PIANOTICK_QUARTER)
            measure_ticks = (ql * 4) * (grid.numerator / grid.denominator)
            total_ticks += measure_ticks * grid.measureAmount
        return total_ticks
    
    def render(self):
        '''Render the complete piano roll with all elements.'''
        print('DEBUG: Starting render()')
        
        # Clear any existing content
        self.canvas.clear()
        
        # Calculate required dimensions
        piano_width = (self.width - 2 * self.editor_margin)
        total_time = self._get_score_length_in_ticks()
        # Content height must not depend on scroll offset; compute using mm/quarter directly
        mm_per_quarter = getattr(self.canvas, '_quarter_note_spacing_mm', None)
        if not isinstance(mm_per_quarter, (int, float)) or mm_per_quarter <= 0:
            px_per_mm = getattr(self.canvas, '_px_per_mm', 3.7795)
            mm_per_quarter = (self.pixels_per_quarter) / max(1e-6, px_per_mm)
        ql = getattr(self.score, 'quarterNoteLength', PIANOTICK_QUARTER)
        content_height_mm = (total_time / max(1e-6, ql)) * mm_per_quarter
        total_height_mm = content_height_mm + (2.0 * self.editor_margin)  # top + bottom margin equal to editor_margin
        
        print(f'DEBUG: Canvas size: {self.width}mm x {self.height}mm')
        print(f'DEBUG: Piano width: {piano_width}mm (margin: {self.editor_margin}mm)')
        print(f'DEBUG: Calculated content height: {content_height_mm}mm')
        print(f'DEBUG: Total logical page height (with margins): {total_height_mm}mm')
        print(f'DEBUG: Total time in ticks: {total_time}')
        
        # Reconcile canvas height to desired content height (shrink or grow).
        # Use tolerance to avoid thrashing on tiny deltas; preserve scroll position.
        desired_height_mm = float(total_height_mm)
        current_height_mm = float(self.canvas.height_mm)
        if abs(desired_height_mm - current_height_mm) > 0.1:
            action = 'Expanding' if desired_height_mm > current_height_mm else 'Shrinking'
            print(f'DEBUG: {action} canvas height from {current_height_mm}mm to {desired_height_mm}mm')
            # Keep scroll; Canvas clamps if out-of-bounds. Avoid reset to prevent jumpiness.
            self.canvas.set_size_mm(self.canvas.width_mm, desired_height_mm, reset_scroll=False)
        
        # Draw stave lines (piano keys)
        stave_lines = self._draw_stave()
        
        # Draw barlines and grid
        barlines = self._draw_barlines_and_grid()
        
        # Set proper drawing order: stave lines at back, then gridlines, barlines, measure numbers, notes on top
        self.canvas.tag_draw_order([
            'staveThreeLines',
            'staveTwoLines',
            'staveClefLines',
            'gridlines',
            'barlines',
            'measureNumbers',
            'notes'
        ])

        # Draw horizontal timeline cursor on top if present
        self._draw_cursor()
        
    
    
    def _draw_stave(self):
        '''Draw the 88-key stave with your specific line patterns.'''
        total_ticks = self._get_score_length_in_ticks()
        mm_per_quarter = getattr(self.canvas, '_quarter_note_spacing_mm', None)
        if not isinstance(mm_per_quarter, (int, float)) or mm_per_quarter <= 0:
            px_per_mm = getattr(self.canvas, '_px_per_mm', 3.7795)
            mm_per_quarter = (self.pixels_per_quarter) / max(1e-6, px_per_mm)
        # Stave height independent of scroll offset
        ql = getattr(self.score, 'quarterNoteLength', PIANOTICK_QUARTER)
        stave_height = (total_ticks / max(1e-6, ql)) * mm_per_quarter
        print(f'   Stave height: {stave_height}mm (score length: {total_ticks} ticks)')
        
        lines_drawn = 0
        key = 2  # Start from key 2 as in your algorithm
        for k in range(1, PIANO_KEY_COUNT):
            x_pos = self.key_to_x_position(k)
            
            # Determine if we need to draw a line for the current key
            key_ = key % 12
            # Skip drawing lines for the last key position to avoid extra line
            if key_ in [2, 5, 7, 10, 0] and k < PIANO_KEY_COUNT:  # Don't draw line for last key
                
                # Set color, width, dash pattern, and category tag according to your pattern
                is_clef_line = False
                category_tag = None
                if key_ in [2, 10, 0]:  # Three-line (F#, G#, A#)
                    color = self.stave_three_color
                    width = self.stave_three_width
                    category_tag = 'staveThreeLines'
                elif key_ in [5, 7] and k not in [41, 43]:  # Two-line (not central C#, D#)
                    color = self.stave_two_color
                    width = self.stave_two_width
                    category_tag = 'staveTwoLines'
                else:  # Central C# and D# lines (clef lines)
                    color = self.stave_clef_color
                    width = self.stave_clef_width
                    is_clef_line = True
                    category_tag = 'staveClefLines'
                
                # Draw the line with correct dash pattern from SCORE model
                self.canvas.add_line(
                    x1_mm=x_pos, y1_mm=self.editor_margin,
                    x2_mm=x_pos, y2_mm=self.editor_margin + stave_height,
                    stroke_color=color,
                    stroke_width_mm=width,
                    stroke_dash=is_clef_line,  # Only clef lines are dashed
                    stroke_dash_pattern_mm=tuple(self.clef_dash_pattern) if is_clef_line else (2.0, 2.0),
                    tags=[category_tag]
                )
                lines_drawn += 1
            
            key += 1
        
        return lines_drawn
    
    def _draw_barlines_and_grid(self):
        '''Draw barlines and grid lines based on your Tkinter algorithm.'''
        # Calculate barline positions (your get_editor_barline_positions equivalent)
        barline_positions = []
        total_ticks = 0.0
        
        for grid in self.score.baseGrid:
            ql = getattr(self.score, 'quarterNoteLength', PIANOTICK_QUARTER)
            measure_ticks = (ql * 4) * (grid.numerator / grid.denominator)
            for _ in range(grid.measureAmount):
                y_pos = self._time_to_y_mm(total_ticks)
                barline_positions.append((y_pos, len(barline_positions) + 1))  # (position, measure_number)
                total_ticks += measure_ticks
        
        barlines_drawn = 0
        # Draw barlines with measure numbers
        for y_pos, measure_number in barline_positions:
            if 0 <= y_pos <= self.canvas.height_mm + self.editor_margin:
                # Barline
                self.canvas.add_line(
                    x1_mm=self.editor_margin, y1_mm=y_pos,
                    x2_mm=self.editor_margin + self.stave_width, y2_mm=y_pos,
                    stroke_color=self.barline_color,
                    stroke_width_mm=self.barline_width,
                    tags=['barlines', f'barline_{measure_number}']
                )
                
                # Measure number (positioned at right edge before scrollbar)
                self.canvas.add_text(
                    text=str(measure_number),
                    x_mm=self.editor_width, 
                    y_mm=y_pos,
                    font_size_pt=sp(12) * 2,  # Kivy font * 2, then convert back to pt for canvas
                    color=self.barline_color,
                    anchor='ne',
                    tags=['measureNumbers', f'measure_number_{measure_number}']
                )
        
        # Calculate and draw gridlines (your get_editor_gridline_positions equivalent)
        total_ticks = 0.0
        for grid in self.score.baseGrid:
            ql = getattr(self.score, 'quarterNoteLength', PIANOTICK_QUARTER)
            measure_ticks = (ql * 4) * (grid.numerator / grid.denominator)
            subdivision_ticks = measure_ticks / grid.numerator
            
            for _ in range(grid.measureAmount):
                for i in range(1, grid.numerator):  # Skip first beat (that's the barline)
                    grid_ticks = total_ticks + i * subdivision_ticks
                    y_pos = self._time_to_y_mm(grid_ticks)
                    
                    if 0 <= y_pos <= self.canvas.height_mm + self.editor_margin:
                        self.canvas.add_line(
                            x1_mm=self.editor_margin, y1_mm=y_pos,
                            x2_mm=self.editor_margin + self.stave_width, y2_mm=y_pos,
                            stroke_color=self.gridline_color,
                            stroke_width_mm=self.gridline_width,
                            stroke_dash=True,  # Dashed gridlines
                            stroke_dash_pattern_mm=tuple(self.gridline_dash_pattern),  # Use SCORE model pattern
                            tags=['gridlines', f'gridline_{total_ticks}_{i}']
                        )
                total_ticks += measure_ticks
        
        # Draw end barline (thicker)
        final_y_pos = self._time_to_y_mm(self._get_score_length_in_ticks())
        if 0 <= final_y_pos <= self.canvas.height_mm + self.editor_margin:
            self.canvas.add_line(
                x1_mm=self.editor_margin, y1_mm=final_y_pos,
                x2_mm=self.editor_margin + self.stave_width, y2_mm=final_y_pos,
                stroke_color=self.barline_color,
                stroke_width_mm=self.barline_width * 2,  # Double thickness for end barline
                tags=['barlines', 'endBarline']
            )
    
    # Zoom and interaction methods (simplified for initial implementation)
    def zoom_in(self, factor: float = 1.2):
        '''Increase SCORE.properties.editorZoomPixelsQuarter by factor (px per quarter).'''
        try:
            current = float(self.pixels_per_quarter)
            new_ppq = max(1.0, current * float(factor))
            self.pixels_per_quarter = new_ppq
            self._update_score_zoom()
            self._calculate_layout()
            self.render()
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
            self.render()
        except Exception as e:
            print(f'DEBUG: zoom_out failed: {e}')
    
    def set_zoom_pixels_per_quarter(self, pixels: float):
        '''Set the zoom level directly (px per quarter) and update SCORE + layout.'''
        try:
            self.pixels_per_quarter = max(1.0, float(pixels))
            self._update_score_zoom()
            self._calculate_layout()
            self.render()
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
                    self.render()
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
            print(f'DEBUG: Updated SCORE editorZoomPixelsQuarter to: {self.pixels_per_quarter} pixels')
    
    def scroll_to_time(self, time_ticks: float):
        '''Scroll to a specific time position (in ticks).'''
        self.scroll_time_offset = ticks_to_quarters(time_ticks)
        self.render()
    
    def x_to_key_number(self, x_mm: float) -> int:
        '''Convert X coordinate to piano key number (1-88) using your algorithm.'''
        # Recreate the x_positions list from your Tkinter code
        x_positions = []
        x_pos = self.editor_margin - self.semitone_width
        
        for n in range(1, PIANO_KEY_COUNT + 1):
            if has_be_gap(n):
                x_pos += self.semitone_width
            x_pos += self.semitone_width
            x_positions.append(x_pos)
        
        # Find the closest position
        if x_positions:
            closest_x = min(x_positions, key=lambda y: abs(y - x_mm))
            closest_x_index = x_positions.index(closest_x)
            return closest_x_index + 1
        return 1
    
    def y_to_ticks(self, y_mm: float) -> float:
        '''Convert Y coordinate to time in ticks (inverse of _time_to_y_mm).'''
        mm_per_quarter = getattr(self.canvas, '_quarter_note_spacing_mm', None)
        if not isinstance(mm_per_quarter, (int, float)) or mm_per_quarter <= 0:
            px_per_mm = getattr(self.canvas, '_px_per_mm', 3.7795)
            mm_per_quarter = (self.pixels_per_quarter) / max(1e-6, px_per_mm)
        time_quarters = (y_mm - self.editor_margin) / mm_per_quarter + self.scroll_time_offset
        ql = getattr(self.score, 'quarterNoteLength', PIANOTICK_QUARTER)
        return time_quarters * ql
    
    # Interaction support
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
                        note = self._find_note_by_id(stave_idx, note_id)
                        if note:
                            self._select_note(note)
                            return True
        return False
    
    def _find_note_by_id(self, stave_idx: int, note_id: int) -> Optional[Note]:
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
    
    def add_note_at_position(self, key_number: int, time_ticks: float, duration_ticks: float = PIANOTICK_QUARTER, stave_idx: int = 0):
        '''Add a new note at the specified position.'''
        if 1 <= key_number <= PIANO_KEY_COUNT and 0 <= stave_idx < len(self.score.stave):
            midi_pitch = key_number_to_midi(key_number)
            new_note = self.score.new_note(
                stave_idx=stave_idx,
                time=time_ticks,
                pitch=midi_pitch,
                duration=duration_ticks
            )
            self.render()
            return new_note
        return None

    def _get_grid_step_ticks(self) -> float:
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
        return self._get_grid_step_ticks()

    def update_cursor_from_mouse_mm(self, y_mm: float):
        '''Update cursor_time from mouse Y in mm with grid snapping.'''
        try:
            raw_ticks = self.y_to_ticks(float(y_mm))
            step = max(1e-6, self._get_grid_step_ticks())
            snapped = math.floor(raw_ticks / step) * step
            # Clamp within score
            snapped = max(0.0, snapped)
            total = float(self._get_score_length_in_ticks())
            snapped = min(total, snapped)
            self.cursor_time = snapped
            self._draw_cursor()
        except Exception as e:
            print(f'CURSOR DEBUG: update failed: {e}')

    def clear_cursor(self):
        '''Hide cursor and remove from canvas.'''
        self.cursor_time = None
        if getattr(self, '_cursor_item_id', None):
            try:
                self.canvas.delete(self._cursor_item_id)
            except Exception:
                pass
            self._cursor_item_id = None

    def _draw_cursor(self):
        '''Draw or update the dashed horizontal cursor at cursor_time.'''
        # Remove existing
        if getattr(self, '_cursor_item_id', None):
            try:
                self.canvas.delete(self._cursor_item_id)
            except Exception:
                pass
            self._cursor_item_id = None
        if self.cursor_time is None:
            return
        # Compute Y in mm
        y_mm = self._time_to_y_mm(self.cursor_time)
        # X extents: full editor view (0 to logical width)
        x1 = 0.0
        x2 = float(self.editor_width)
        if x2 <= x1:
            return
        try:
            self._cursor_item_id = self.canvas.add_line(
                x1_mm=x1,
                y1_mm=y_mm,
                x2_mm=x2,
                y2_mm=y_mm,
                stroke_color='#000000',
                stroke_width_mm=0.25,
                stroke_dash=True,
                stroke_dash_pattern_mm=(2.0, 2.0),
                tags=['cursorLine']
            )
            # Kept on top by being added after raise_in_order in render()
        except Exception as e:
            print(f'CURSOR DEBUG: draw failed: {e}')


# Maintain backward compatibility and integrate with main app
class Editor(Editor):
    '''
    Main Editor class that integrates PianoRollEditor with the pianoTAB application.
    
    This class:
    - Inherits piano roll functionality from PianoRollEditor
    - Connects to the SCORE model for line thickness and color settings
    - Integrates with the main GUI and file management system
    - Handles callbacks for score modifications
    '''
    
    def __init__(self, editor_canvas: Canvas, score: Optional[SCORE] = None):
        # Initialize the piano roll editor
        super().__init__(editor_canvas, score)
        
        # Callback for when the score is modified
        self.on_modified: Optional[Callable] = None
        
        # Connect to SCORE model line thickness settings
        self._update_line_settings_from_score()
        
        # Schedule initial render
        Clock.schedule_once(self._initial_render, 0.2)
    
    def set_score(self, score: SCORE):
        '''Set a new score and update the display.'''
        self.score = score
        # Sync all visuals and zoom from new score
        self._apply_settings_from_score()
        self.render()
        if self.on_modified:
            self.on_modified()
    
    def _update_line_settings_from_score(self):
        '''Update settings from SCORE; kept for backward-compatibility.

        Delegates to _apply_settings_from_score() which now syncs both zoom and
        visual line settings from the model to ensure the editor matches paper output.
        '''
        self._apply_settings_from_score()
        
    def load_score(self, score: SCORE):
        '''Load an existing SCORE into the editor and refresh the display.'''
        try:
            # Use existing pipeline to apply the new score, zoom, and styles
            self.set_score(score)
            # Reset view related state
            self.scroll_time_offset = 0.0
            try:
                self.cursor_time = None
            except Exception:
                pass
        except Exception as e:
            print(f'Editor: load_score error: {e}')

    def new_score(self):
        '''Create a new default SCORE and display it.'''
        try:
            score = self._create_default_score_template()
            self.set_score(score)
            # Reset view related state
            self.scroll_time_offset = 0.0
            try:
                self.cursor_time = None
            except Exception:
                pass
        except Exception as e:
            print(f'Editor: new_score error: {e}')
    
    def _initial_render(self, dt):
        '''Perform initial render after app has loaded.'''
        try:
            self.render()
            print(f'Editor: Initial render complete for score with {len(self.score.stave)} staves')
        except Exception as e:
            print(f'Editor: Initial render error: {e}')
            import traceback
            traceback.print_exc()
    
    def add_note(self, stave_idx: int, pitch: int, time: float, duration: float, hand: str = '>'):
        '''Add a new note to the score and update the display.'''
        try:
            self.score.new_note(stave_idx, time, pitch, duration, hand)
            self.render()
            if self.on_modified:
                self.on_modified()
        except Exception as e:
            print(f'Editor: Error adding note: {e}')
    
    def delete_selected_notes(self):
        '''Delete currently selected notes and update the display.'''
        if not self.selected_notes:
            return
        
        try:
            # Remove notes from score
            for note in self.selected_notes:
                for stave in self.score.stave:
                    if note in stave.event.note:
                        stave.event.note.remove(note)
                        break
            
            # Clear selection and re-render
            self.selected_notes.clear()
            self.render()
            if self.on_modified:
                self.on_modified()
        except Exception as e:
            print(f'Editor: Error deleting notes: {e}')
    
    def refresh_display(self):
        '''Refresh the display after score changes.'''
        self._apply_settings_from_score()
        self.render()
