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

class PianoRollEditor:
    """
    Vertical Piano Roll Editor based on the original Tkinter design.
    
    Layout follows your specific design patterns:
    - 88 piano keys with 103 physical semitone positions
    - BE gaps for visual spacing between key groups
    - Specific line patterns (two-line, three-line, clef-line)
    - Time flows vertically (top to bottom)
    - Pitch flows horizontally with your custom spacing
    """
    
    def __init__(self, editor_canvas: Canvas, score: Optional[SCORE] = None):
        self.canvas: Canvas = editor_canvas  # Fixed: use consistent attribute name
        self.score: SCORE = score if score is not None else self._create_default_score()
        
        # Initialize dimensions from canvas
        # Piano roll configuration using shared constants
        self.pixels_per_quarter: float = self._get_zoom_from_score()  # Read from SCORE model
        self.zoom_factor: float = 1.0
        
        # Stave line configuration - use exact GlobalStave defaults from globalProperties.py
        self.stave_two_color = "#000000"      # Default from GlobalStave 
        self.stave_three_color = "#000000"    # Default from GlobalStave
        self.stave_clef_color = "#000000"     # Default from GlobalStave
        self.stave_two_width = 0.125          # Exact default from GlobalStave.twoLineWidth
        self.stave_three_width = 0.25         # Exact default from GlobalStave.threeLineWidth
        self.stave_clef_width = 0.125         # Exact default from GlobalStave.clefWidth
        
        # Grid configuration - use exact GlobalBasegrid defaults
        self.barline_color = "#000000"        # Default from GlobalBasegrid
        self.barline_width = 2.0              # Default from GlobalBasegrid.barlineWidth
        self.gridline_color = "#000000"       # Default from GlobalBasegrid.gridlineColor
        self.gridline_width = 1.0             # Default from GlobalBasegrid.gridlineWidth
        self.gridline_dash_pattern = [4, 4]   # Default from GlobalBasegrid.gridlineDashPattern
        
        # Clef line dash pattern - use exact GlobalStave default
        self.clef_dash_pattern = [2, 2]       # Default from GlobalStave.clefDashPattern
        
        # Current view state
        self.scroll_time_offset: float = 0.0
        self.selected_notes: List[Note] = []
        
        # Initialize layout
        self._calculate_layout()
    
    def _create_default_score(self) -> SCORE:
        """Create a default score with a single stave and proper base grid setup."""
        score = SCORE()
        
        # SCORE already creates one default stave, so we don't need to add another
        # Just configure the existing stave name if needed
        if score.stave:
            score.stave[0].name = 'Piano Single'
        
        # Add some default base grid (4/4 time signature, 4 measures for cleaner start)
        score.new_basegrid(numerator=4, denominator=4, measureAmount=4)
        
        return score
    
    def _get_zoom_from_score(self) -> float:
        """Read editorZoomPixelsQuarter from SCORE model, with fallback to default."""
        if (hasattr(self.score, 'properties') and 
            hasattr(self.score.properties, 'editorZoomPixelsQuarter')):
            zoom_value = self.score.properties.editorZoomPixelsQuarter
            print(f"DEBUG: Using SCORE editorZoomPixelsQuarter: {zoom_value} pixels")
            return float(zoom_value)
        else:
            print(f"DEBUG: No editorZoomPixelsQuarter found in SCORE, using default: {DEFAULT_PIXELS_PER_QUARTER} pixels")
            return DEFAULT_PIXELS_PER_QUARTER
    
    def _calculate_layout(self):
        """Calculate layout dimensions based on your Tkinter design."""
        self.editor_margin = self.canvas.width_mm / 6  # Your margin calculation
        
        # Calculate stave dimensions using shared constants
        # The stave should span the full visual width
        visual_semitone_positions = get_visual_semitone_positions()  # Returns 98
        total_width = self.canvas.width_mm - (2 * self.editor_margin)
        self.semitone_width = total_width / visual_semitone_positions
        # Stave width spans the full width (no reduction)
        self.stave_width = total_width
        
        # Calculate editor width (right edge of editor = left edge of scrollbar)
        scrollbar_width_mm = self.canvas.custom_scrollbar.scrollbar_width * self.canvas._mm_per_pixel
        self.editor_width = self.canvas.width_mm - scrollbar_width_mm
        
        # Update canvas quarter note spacing for musical scrolling
        # Convert pixels to mm: pixels_per_quarter / pixels_per_mm = quarter_note_mm
        if hasattr(self.canvas, '_px_per_mm') and self.canvas._px_per_mm > 0:
            quarter_note_mm = (self.pixels_per_quarter * self.zoom_factor) / self.canvas._px_per_mm
            self.canvas.set_quarter_note_spacing_mm(quarter_note_mm)
            
            # Debug: Check consistency with editor's time calculation (disabled)
            # pixels_per_quarter_mm_editor = self.pixels_per_quarter * 0.264583 * self.zoom_factor
            # print(f"DEBUG: Quarter note spacing - Canvas: {quarter_note_mm:.2f}mm, Editor: {pixels_per_quarter_mm_editor:.2f}mm")
            # print(f"DEBUG: pixels_per_quarter: {self.pixels_per_quarter}, zoom_factor: {self.zoom_factor}")
            # print(f"DEBUG: canvas._px_per_mm: {self.canvas._px_per_mm:.3f}, hardcoded: {1/0.264583:.3f}")
    
    @property
    def width(self) -> float:
        """Canvas width in mm."""
        return self.canvas.width_mm
    
    @property 
    def height(self) -> float:
        """Canvas height in mm."""
        return self.canvas.height_mm
    
    def key_to_x_position(self, key_number: int) -> float:
        """Convert piano key number (1-88) to X position using your spacing algorithm."""
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
        """Convert time in ticks to Y coordinate in millimeters."""
        # Convert your pixels_per_quarter to mm (assuming 96 DPI)
        pixels_per_quarter_mm = self.pixels_per_quarter * 0.264583 * self.zoom_factor
        time_quarters = ticks_to_quarters(time_ticks)
        return self.editor_margin + (time_quarters * pixels_per_quarter_mm) - (self.scroll_time_offset * pixels_per_quarter_mm)
    
    def _get_score_length_in_ticks(self) -> float:
        """Calculate total score length in ticks based on your algorithm."""
        total_ticks = 0.0
        for grid in self.score.baseGrid:
            measure_ticks = (PIANOTICK_QUARTER * 4) * (grid.numerator / grid.denominator)
            total_ticks += measure_ticks * grid.measureAmount
        return total_ticks
    
    def render(self):
        """Render the complete piano roll with all elements."""
        print("DEBUG: Starting render()")
        
        # Clear any existing content
        self.canvas.clear()
        
        # Calculate required dimensions
        piano_width = (self.width - 2 * self.editor_margin)
        total_time = self._calculate_total_time()
        piano_height = self._time_to_y_mm(total_time)
        
        print(f"DEBUG: Canvas size: {self.width}mm x {self.height}mm")
        print(f"DEBUG: Piano width: {piano_width}mm (margin: {self.editor_margin}mm)")
        print(f"DEBUG: Calculated height needed: {piano_height}mm")
        print(f"DEBUG: Total time in ticks: {total_time}")
        
        # Update canvas size if needed
        if piano_height > self.height:
            print(f"DEBUG: Expanding canvas height from {self.height}mm to {piano_height + 20}mm")
            self.canvas.set_size_mm(self.width, piano_height + 20, reset_scroll=True)
        
        # Draw stave lines (piano keys)
        stave_lines = self._draw_stave()
        
        # Draw barlines and grid
        barlines = self._draw_barlines_and_grid()
        
        # Draw notes
        notes_drawn = self._draw_notes()
        
        # Set proper drawing order: stave lines at back, then gridlines, barlines, measure numbers, notes on top
        self.canvas.raise_in_order([
            'staveThreeLines',
            'staveTwoLines', 
            'staveClefLines',
            'gridlines',
            'barlines',
            'measureNumbers',
            'notes'
        ])
        
    def _calculate_total_time(self):
        """Calculate the total time span needed for the score."""
        if not self.score.baseGrid:
            return quarters_to_ticks(4.0)  # Default to 4 quarter notes if no grid
        
        total_ticks = 0.0
        for grid in self.score.baseGrid:
            measure_ticks = (PIANOTICK_QUARTER * 4) * (grid.numerator / grid.denominator)
            total_ticks += measure_ticks * grid.measureAmount
        
        return total_ticks
    
    def _draw_stave(self):
        """Draw the 88-key stave with your specific line patterns."""
        stave_height = ticks_to_quarters(self._get_score_length_in_ticks()) * self.pixels_per_quarter * 0.264583 * self.zoom_factor
        print(f"   Stave height: {stave_height}mm (score length: {self._get_score_length_in_ticks()} ticks)")
        
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
                    id=[category_tag]
                )
                lines_drawn += 1
            
            key += 1
        
        return lines_drawn
    
    def _draw_barlines_and_grid(self):
        """Draw barlines and grid lines based on your Tkinter algorithm."""
        # Calculate barline positions (your get_editor_barline_positions equivalent)
        barline_positions = []
        total_ticks = 0.0
        
        for grid in self.score.baseGrid:
            measure_ticks = (PIANOTICK_QUARTER * 4) * (grid.numerator / grid.denominator)
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
                    id=['barlines', f"barline_{measure_number}"]
                )
                
                # Measure number (positioned at right edge before scrollbar)
                self.canvas.add_text(
                    text=str(measure_number),
                    x_mm=self.editor_width, 
                    y_mm=y_pos,
                    font_size_pt=sp(12) * 2,  # Kivy font * 2, then convert back to pt for canvas
                    color=self.barline_color,
                    anchor='ne',
                    id=['measureNumbers', f"measure_number_{measure_number}"]
                )
        
        # Calculate and draw gridlines (your get_editor_gridline_positions equivalent)
        total_ticks = 0.0
        for grid in self.score.baseGrid:
            measure_ticks = (PIANOTICK_QUARTER * 4) * (grid.numerator / grid.denominator)
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
                            id=['gridlines', f"gridline_{total_ticks}_{i}"]
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
                id=['barlines', 'endBarline']
            )
    
    def _draw_notes(self):
        """Draw notes from the SCORE model."""
        for stave_idx, stave in enumerate(self.score.stave):
            for note in stave.event.note:
                self._draw_single_note(note, stave_idx)
    
    def _draw_single_note(self, note: Note, stave_idx: int):
        """Draw a single note using your coordinate system."""
        # Convert MIDI pitch to key number using constants
        key_number = midi_to_key_number(note.pitch)
        
        if 1 <= key_number <= PIANO_KEY_COUNT:
            x_pos = self.key_to_x_position(key_number)
            y_pos = self._time_to_y_mm(note.time)
            
            # Note dimensions
            note_width = self.semitone_width * 0.8  # Slightly smaller than key width
            note_height = ticks_to_quarters(note.duration) * self.pixels_per_quarter * 0.264583 * self.zoom_factor
            
            # Note color (use your model's color system)
            note_color = note.color if hasattr(note, 'color') and note.color else "#4080FF"
            
            # Only draw if visible
            if (0 <= y_pos <= self.canvas.height_mm + self.editor_margin and
                self.editor_margin <= x_pos <= self.editor_margin + self.stave_width):
                
                self.canvas.add_rectangle(
                    x1_mm=x_pos - note_width/2, y1_mm=y_pos,
                    x2_mm=x_pos + note_width/2, y2_mm=y_pos + note_height,
                    fill=True,
                    fill_color=note_color,
                    outline=True,
                    outline_color="#000000",
                    outline_width_mm=0.05,
                    id=['notes', f"note_{stave_idx}_{note.id}"]
                )
    
    # Zoom and interaction methods (simplified for initial implementation)
    def zoom_in(self, factor: float = 1.2):
        """Zoom in on the time axis."""
        self.zoom_factor *= factor
        self._update_score_zoom()
        self._calculate_layout()  # Update canvas quarter note spacing
        self.render()
    
    def zoom_out(self, factor: float = 1.2):
        """Zoom out on the time axis."""
        self.zoom_factor /= factor
        self._update_score_zoom()
        self._calculate_layout()  # Update canvas quarter note spacing
        self.render()
    
    def set_zoom_pixels_per_quarter(self, pixels: float):
        """Set the zoom level directly in pixels per quarter note."""
        self.pixels_per_quarter = float(pixels)
        self.zoom_factor = 1.0  # Reset zoom factor when setting absolute value
        self._update_score_zoom()
        self._calculate_layout()  # Update canvas quarter note spacing
        self.render()
    
    def _update_score_zoom(self):
        """Update the editorZoomPixelsQuarter value in the SCORE model."""
        if (hasattr(self.score, 'properties') and 
            hasattr(self.score.properties, 'editorZoomPixelsQuarter')):
            effective_zoom = self.pixels_per_quarter * self.zoom_factor
            self.score.properties.editorZoomPixelsQuarter = effective_zoom
            print(f"DEBUG: Updated SCORE editorZoomPixelsQuarter to: {effective_zoom} pixels")
    
    def scroll_to_time(self, time_ticks: float):
        """Scroll to a specific time position (in ticks)."""
        self.scroll_time_offset = ticks_to_quarters(time_ticks)
        self.render()
    
    def x_to_key_number(self, x_mm: float) -> int:
        """Convert X coordinate to piano key number (1-88) using your algorithm."""
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
        """Convert Y coordinate to time in ticks."""
        pixels_per_quarter_mm = self.pixels_per_quarter * 0.264583 * self.zoom_factor
        time_quarters = (y_mm - self.editor_margin) / pixels_per_quarter_mm + self.scroll_time_offset
        return quarters_to_ticks(time_quarters)
    
    # Interaction support
    def on_item_click(self, item_id: int, touch_pos_mm: Tuple[float, float]) -> bool:
        """Handle click on canvas items."""
        if item_id in self.canvas._items:
            canvas_item = self.canvas._items[item_id]
            item_tags = canvas_item.get('id', set())
            
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
        """Find a note by stave index and note ID."""
        if 0 <= stave_idx < len(self.score.stave):
            for note in self.score.stave[stave_idx].event.note:
                if note.id == note_id:
                    return note
        return None
    
    def _select_note(self, note: Note):
        """Select a note for editing."""
        self.selected_notes.clear()
        self.selected_notes.append(note)
        print(f"Selected note: Key={note.pitch-20}, Time={note.time}, Duration={note.duration}")
    
    def add_note_at_position(self, key_number: int, time_ticks: float, duration_ticks: float = PIANOTICK_QUARTER, stave_idx: int = 0):
        """Add a new note at the specified position."""
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


# Maintain backward compatibility and integrate with main app
class Editor(PianoRollEditor):
    """
    Main Editor class that integrates PianoRollEditor with the PianoTab application.
    
    This class:
    - Inherits piano roll functionality from PianoRollEditor
    - Connects to the SCORE model for line thickness and color settings
    - Integrates with the main GUI and file management system
    - Handles callbacks for score modifications
    """
    
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
        """Set a new score and update the display."""
        self.score = score
        self.pixels_per_quarter = self._get_zoom_from_score()  # Update zoom from new score
        self._update_line_settings_from_score()
        self.render()
        if self.on_modified:
            self.on_modified()
    
    def _update_line_settings_from_score(self):
        """Update line thickness and colors from the SCORE's properties to match paper output exactly."""
        if not self.score or not hasattr(self.score, 'properties'):
            print("DEBUG: No score.properties found, using defaults")
            return
        
        properties = self.score.properties
        
        # Update stave line settings from properties.globalStave - use exact mm values from SCORE model
        if hasattr(properties, 'globalStave'):
            stave = properties.globalStave
            self.stave_two_color = getattr(stave, 'twoLineColor', '#000000')
            self.stave_three_color = getattr(stave, 'threeLineColor', '#000000') 
            self.stave_clef_color = getattr(stave, 'clefColor', '#000000')
            
            # Use exact line widths from SCORE model (in mm) - these match paper output
            self.stave_two_width = getattr(stave, 'twoLineWidth', 0.125)    # Exact default 0.125mm
            self.stave_three_width = getattr(stave, 'threeLineWidth', 0.25) # Exact default 0.25mm  
            self.stave_clef_width = getattr(stave, 'clefWidth', 0.125)      # Exact default 0.125mm
            
            # Use clef dash pattern from SCORE model
            self.clef_dash_pattern = getattr(stave, 'clefDashPattern', [2, 2])  # Default [2, 2]mm
            
            print(f"DEBUG: Using SCORE line widths - two: {self.stave_two_width}mm, three: {self.stave_three_width}mm, clef: {self.stave_clef_width}mm")
            print(f"DEBUG: Using SCORE clef dash pattern: {self.clef_dash_pattern}mm")
        
        # Update grid settings from properties.globalBasegrid - use exact mm values
        if hasattr(properties, 'globalBasegrid'):
            basegrid = properties.globalBasegrid
            self.barline_color = getattr(basegrid, 'barlineColor', '#000000')
            self.barline_width = getattr(basegrid, 'barlineWidth', 2.0)     # Default 2.0mm
            self.gridline_color = getattr(basegrid, 'gridlineColor', '#000000')
            self.gridline_width = getattr(basegrid, 'gridlineWidth', 1.0)   # Default 1.0mm
            self.gridline_dash_pattern = getattr(basegrid, 'gridlineDashPattern', [4, 4])  # Default [4, 4]mm
            
            print(f"DEBUG: Using SCORE grid widths - barline: {self.barline_width}mm, gridline: {self.gridline_width}mm")
            print(f"DEBUG: Using SCORE gridline dash pattern: {self.gridline_dash_pattern}mm")
    
    def _initial_render(self, dt):
        """Perform initial render after app has loaded."""
        try:
            self.render()
            print(f"Editor: Initial render complete for score with {len(self.score.stave)} staves")
        except Exception as e:
            print(f"Editor: Initial render error: {e}")
            import traceback
            traceback.print_exc()
    
    def add_note(self, stave_idx: int, pitch: int, time: float, duration: float, hand: str = '>'):
        """Add a new note to the score and update the display."""
        try:
            self.score.new_note(stave_idx, time, pitch, duration, hand)
            self.render()
            if self.on_modified:
                self.on_modified()
        except Exception as e:
            print(f"Editor: Error adding note: {e}")
    
    def delete_selected_notes(self):
        """Delete currently selected notes and update the display."""
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
            print(f"Editor: Error deleting notes: {e}")
    
    def refresh_display(self):
        """Refresh the display after score changes."""
        self._update_line_settings_from_score()
        self.render()
