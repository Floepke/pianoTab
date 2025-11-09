'''
Slur drawing mixin for the Editor class.

Handles drawing slur events on the piano roll canvas.
'''
from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from file.SCORE import SCORE, Slur
    from utils.canvas import Canvas


class SlurDrawerMixin:
    '''Mixin for drawing slurs.'''
    
    # Type hints for Editor attributes used by this mixin
    if TYPE_CHECKING:
        score: SCORE
        canvas: Canvas
        
        def key_number_to_x_mm(self, pitch: int) -> float: ...
        def time_to_y_mm(self, time: float) -> float: ...
    
    def _draw_slurs(self) -> None:
        '''Draw all slur events from all staves.'''
        if not self.score:
            return
        
        # Draw each slur
        for stave_idx, stave in enumerate(self.score.stave):
            for slur in stave.event.slur:
                self._draw_single_slur(stave_idx, slur)

    def _draw_single_slur(self, stave_idx: int, slur: Slur) -> None:
        '''Draw a single slur event.

        Args:
            stave_idx: Index of the stave containing the slur.
            slur: The slur event to draw.
        '''
        # TODO: Implement slur drawing
        # - Draw curved line from slur.time to slur.y4_time
        # - Use Bezier curve for smooth arc
        # - Tag with ['slurs', f'slur_{stave_idx}_{slur.id}']
        pass
