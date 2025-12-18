'''
Stave drawing mixin for the Editor class.

Handles drawing the 88-key piano stave lines with specific line patterns.
'''
from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from file.SCORE import SCORE
    from utils.canvas import Canvas

from utils.CONSTANTS import PIANO_KEY_AMOUNT, PIANOTICK_QUARTER
from gui.colors import DARK_HEX, DARK_LIGHTER_HEX, LIGHT_HEX, rgba_to_hex, LIGHT_DARKER, LIGHT_DARKER_HEX, ACCENT_HEX, make_darker_hex


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
        def _get_score_length_in_ticks(self) -> float: ...
    
    def _draw_stave(self):
        '''Draw the 88-key stave with your specific line patterns.'''
        # Calculate total stave height based on score length
        total_ticks = self._get_score_length_in_ticks()

        # calculate stave_height in mm
        mm_per_quarter = getattr(self.canvas, '_quarter_note_spacing_mm', None)
        if not isinstance(mm_per_quarter, (int, float)) or mm_per_quarter <= 0:
            px_per_mm = getattr(self.canvas, '_px_per_mm', 3.7795)
            mm_per_quarter = (self.pixels_per_quarter) / max(1e-6, px_per_mm)
        stave_height_mm = (total_ticks / max(1e-6, PIANOTICK_QUARTER)) * mm_per_quarter
        
        # Set stave boundaries (useful for cursor and other tools)
        self.stave_left = self.editor_margin
        self.stave_right = self.editor_margin + self.stave_width

        for key in range(1, PIANO_KEY_AMOUNT):
            x_pos = self.pitch_to_x(key)
            
            # Determine if we need to draw a line for the current key
            key_ = key % 12  # Use 'key', not 'k' - tracks musical pattern
            
            # Check if this is a clef line position (central C# and D#)
            is_clef_line = (key in [41, 43])  # C# and D# around middle C
            
            # Skip drawing lines for the last key position to avoid extra line
            # Include clef positions (6, 8) in the pattern check for k=41, 43
            if (key_ in [2, 5, 7, 10, 0] or is_clef_line) and key < PIANO_KEY_AMOUNT:
                
                # Set color, width, dash pattern, and category tag according to your pattern
                category_tag = None
                if key_ in [2, 10, 0]:  # Three-line (F#, G#, A#)
                    color = DARK_HEX
                    width = self.semitone_width / 16
                    category_tag = 'stavethreeline'
                    dash_pattern = None
                elif is_clef_line:  # Clef lines (C# and D#)
                    color = DARK_HEX
                    width = self.semitone_width / 6
                    category_tag = 'staveclefline'
                    dash_pattern = [0, 2]
                else:
                    # two-line
                    color = DARK_HEX
                    width = self.semitone_width / 16
                    category_tag = 'stavetwoline'
                    dash_pattern = [2, 1]
                
                # Draw the line with correct dash pattern from SCORE model
                y1 = self.editor_margin
                y2 = self.editor_margin + stave_height_mm
                self.canvas.add_line(
                    x1_mm=x_pos, y1_mm=y1,
                    x2_mm=x_pos, y2_mm=y2,
                    color=color,
                    width_mm=width,
                    dash=True if dash_pattern else False,  # Only clef lines are dashed
                    dash_pattern_mm=dash_pattern,
                    tags=[category_tag]
                )

        return
