'''
Text drawing mixin for the Editor class.

Handles drawing text events on the piano roll canvas.
'''
from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from file.SCORE import SCORE, Text
    from utils.canvas import Canvas


class TextDrawerMixin:
    '''Mixin for drawing text annotations.'''
    
    # Type hints for Editor attributes used by this mixin
    if TYPE_CHECKING:
        score: SCORE
        canvas: Canvas
        editor_margin: float
        
        def time_to_y(self, time: float) -> float: ...
    
    def _draw_texts(self) -> None:
        '''Draw all text events from all staves.'''
        if not self.score:
            return
        
        # Draw each text
        for stave_idx, stave in enumerate(self.score.stave):
            for text in stave.event.text:
                self._draw_single_text(stave_idx, text)

    def _draw_single_text(self, stave_idx: int, text: Text) -> None:
        '''Draw a single text event.

        Args:
            stave_idx: Index of the stave containing the text.
            text: The text event to draw.
        '''
        # TODO: Implement text drawing
        # - Calculate y position: self.time_to_y_mm(text.time)
        # - Draw text at the specified position
        # - Use self.canvas.add_text(...)
        # - Tag with ['texts', f'text_{stave_idx}_{text.id}']
        pass
