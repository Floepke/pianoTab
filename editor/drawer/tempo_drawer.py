'''
Tempo drawing mixin for the Editor class.

Handles drawing tempo events on the piano roll canvas.
'''
from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from file.SCORE import SCORE, Tempo
    from utils.canvas import Canvas


class TempoDrawerMixin:
    '''Mixin for drawing tempo markings.'''
    
    # Type hints for Editor attributes used by this mixin
    if TYPE_CHECKING:
        score: SCORE
        canvas: Canvas
        editor_margin: float
        
        def time_to_y(self, time: float) -> float: ...
    
    def _draw_tempos(self) -> None:
        '''Draw all tempo events from all staves.'''
        if not self.score:
            return
        
        # Get the currently rendered stave index
        stave_idx = self.score.fileSettings.get_rendered_stave_index(
            num_staves=len(self.score.stave)
        ) if (self.score and hasattr(self.score, 'fileSettings')) else 0
        
        # Draw tempos from the currently rendered stave
        stave = self.score.stave[stave_idx]
        for tempo in stave.event.tempo:
            self._draw_single_tempo(tempo)

    def _draw_single_tempo(self, stave_idx: int, tempo: Tempo) -> None:
        '''Draw a single tempo event.

        Args:
            stave_idx: Index of the stave containing the tempo.
            tempo: The tempo event to draw.
        '''
        # TODO: Implement tempo drawing
        # - Calculate y position: self.time_to_y_mm(tempo.time)
        # - Draw tempo marking (text + optional metronome symbol)
        # - Use self.canvas.add_text(...)
        # - Tag with ['tempos', f'tempo_{stave_idx}_{tempo.id}']
        pass
