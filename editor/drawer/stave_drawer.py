'''
Stave drawing mixin for the Editor class.

Handles drawing the 88-key piano stave lines with specific line patterns.
'''
from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from file.SCORE import SCORE
    from utils.canvas import Canvas

from utils.CONSTANTS import PIANO_KEY_COUNT, PIANOTICK_QUARTER
from gui.colors import rgba_to_hex, LIGHT_DARKER


class StaveDrawerMixin:
    '''Mixin for drawing piano stave lines.'''
    
    # Type hints for Editor attributes used by this mixin
    if TYPE_CHECKING:
        score: SCORE
        canvas: Canvas
        editor_margin: float
        stave_width: float
        pixels_per_quarter: float
        stave_two_color: str
        stave_two_width: float
        stave_three_color: str
        stave_three_width: float
        stave_clef_color: str
        stave_clef_width: float
        clef_dash_pattern: list
        
        def pitch_to_x(self, key_number: int) -> float: ...
        def get_score_length_in_ticks(self) -> float: ...
    
    def _draw_stave(self):
        '''Draw the 88-key stave with your specific line patterns.'''
        total_ticks = self.get_score_length_in_ticks()
        mm_per_quarter = getattr(self.canvas, '_quarter_note_spacing_mm', None)
        if not isinstance(mm_per_quarter, (int, float)) or mm_per_quarter <= 0:
            px_per_mm = getattr(self.canvas, '_px_per_mm', 3.7795)
            mm_per_quarter = (self.pixels_per_quarter) / max(1e-6, px_per_mm)
        # Stave height independent of scroll offset
        ql = self.score.fileSettings.quarterNoteUnit if (self.score and hasattr(self.score, 'fileSettings')) else PIANOTICK_QUARTER
        stave_height = (total_ticks / max(1e-6, ql)) * mm_per_quarter
        
        # Set stave boundaries (useful for cursor and other tools)
        self.stave_left = self.editor_margin
        self.stave_right = self.editor_margin + self.stave_width

        for key in range(1, PIANO_KEY_COUNT):
            x_pos = self.pitch_to_x(key)
            
            # Determine if we need to draw a line for the current key
            key_ = key % 12  # Use 'key', not 'k' - tracks musical pattern
            
            # Check if this is a clef line position (central C# and D#)
            is_clef_line = (key in [41, 43])  # C# and D# around middle C
            
            # Skip drawing lines for the last key position to avoid extra line
            # Include clef positions (6, 8) in the pattern check for k=41, 43
            if (key_ in [2, 5, 7, 10, 0] or is_clef_line) and key < PIANO_KEY_COUNT:
                
                # Set color, width, dash pattern, and category tag according to your pattern
                category_tag = None
                if is_clef_line:
                    # Central C# and D# lines (clef lines) - always dashed
                    color = self.stave_clef_color
                    width = self.stave_clef_width
                    category_tag = 'staveclefline'
                elif key_ in [2, 10, 0]:  # Three-line (F#, G#, A#)
                    color = self.stave_three_color
                    width = self.stave_three_width
                    category_tag = 'stavethreeline'
                else:  # key_ in [5, 7] - Two-line (C#, D#) but not central
                    color = self.stave_two_color
                    width = self.stave_two_width
                    category_tag = 'stavetwoline'
                
                # Draw the line with correct dash pattern from SCORE model
                y1 = self.editor_margin
                y2 = self.editor_margin + stave_height
                if is_clef_line and not hasattr(self, '_clef_debug_printed'):
                    self._clef_debug_printed = True
                self.canvas.add_line(
                    x1_mm=x_pos, y1_mm=y1,
                    x2_mm=x_pos, y2_mm=y2,
                    color=color,
                    width_mm=width,
                    dash=is_clef_line,  # Only clef lines are dashed
                    dash_pattern_mm=tuple(self.clef_dash_pattern) if is_clef_line else (2.0, 2.0),
                    tags=[category_tag]
                )

        return
