'''
Line break drawing mixin for the Editor class.

Handles drawing line break indicators on the piano roll canvas.
'''
from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from file.SCORE import SCORE, LineBreak
    from utils.canvas import Canvas


class LineBreakDrawerMixin:
    '''Mixin for drawing line break indicators.'''
    
    # Type hints for Editor attributes used by this mixin
    if TYPE_CHECKING:
        score: SCORE
        canvas: Canvas
        editor_margin: float
        stave_width: float
        
        def time_to_y(self, time: float) -> float: ...
    
    def _draw_line_breaks(self) -> None:
        '''Draw all line break indicators.'''
        if not self.score:
            return
        
        # Draw each line break
        for linebreak in self.score.lineBreak:
            self._draw_single_line_break(linebreak)

    def _draw_single_line_break(self, linebreak: LineBreak) -> None:
        '''Draw a single line break indicator.

        Args:
            linebreak: The line break to draw.
        '''
        # TODO: Implement line break drawing
        # - Calculate y position: self.time_to_y_mm(linebreak.time)
        # - Draw visual indicator at line break position
        # - Distinguish between 'manual' and 'locked' types (linebreak.type)
        # - Use different colors or styles for different types
        # - Tag with ['lineBreaks', f'linebreak_{linebreak.id}']
        pass
