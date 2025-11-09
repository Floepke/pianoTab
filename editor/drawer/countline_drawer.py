'''
Count line drawing mixin for the Editor class.

Handles drawing count line events on the piano roll canvas.
'''
from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from file.SCORE import SCORE, CountLine
    from utils.canvas import Canvas


class CountLineDrawerMixin:
    '''Mixin for drawing count lines.'''
    
    # Type hints for Editor attributes used by this mixin
    if TYPE_CHECKING:
        score: SCORE
        canvas: Canvas
        editor_margin: float
        stave_width: float
        
        def time_to_y_mm(self, time: float) -> float: ...
    
    def _draw_count_lines(self) -> None:
        '''Draw all count line events from all staves.'''
        if not self.score:
            return
        
        # Draw each count line
        for stave_idx, stave in enumerate(self.score.stave):
            for countline in stave.event.countLine:
                self._draw_single_count_line(stave_idx, countline)

    def _draw_single_count_line(self, stave_idx: int, countline: CountLine) -> None:
        '''Draw a single count line event.

        Args:
            stave_idx: Index of the stave containing the count line.
            countline: The count line event to draw.
        '''
        # TODO: Implement count line drawing
        # - Calculate y position: self.time_to_y_mm(countline.time)
        # - Draw vertical line at specified position
        # - Use self.canvas.add_line(...)
        # - Tag with ['countLines', f'countline_{stave_idx}_{countline.id}']
        pass
