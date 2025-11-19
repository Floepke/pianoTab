'''
Grace note drawing mixin for the Editor class.

Handles drawing grace note events on the piano roll canvas.
'''
from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from file.SCORE import SCORE, GraceNote
    from utils.canvas import Canvas


class GraceNoteDrawerMixin:
    '''Mixin for drawing grace notes.'''
    
    # Type hints for Editor attributes used by this mixin
    if TYPE_CHECKING:
        score: SCORE
        canvas: Canvas
        semitone_width: float
        
        def pitch_to_x(self, pitch: int) -> float: ...
        def time_to_y(self, time: float) -> float: ...
    
    def _draw_grace_notes(self) -> None:
        '''Draw all grace note events from all staves.'''
        if not self.score:
            return
        
        # Get the currently rendered stave index
        stave_idx = self.score.fileSettings.get_rendered_stave_index(
            num_staves=len(self.score.stave)
        ) if (self.score and hasattr(self.score, 'fileSettings')) else 0
        
        # Draw grace notes from the currently rendered stave
        stave = self.score.stave[stave_idx]
        for gracenote in stave.event.graceNote:
            self._draw_single_grace_note(stave_idx, gracenote)

    def _draw_single_grace_note(self, stave_idx: int, gracenote: GraceNote) -> None:
        '''Draw a single grace note event.

        Args:
            stave_idx: Index of the stave containing the grace note.
            gracenote: The grace note event to draw.
        '''
        # TODO: Implement grace note drawing
        # - Grace notes are typically smaller than regular notes
        # - Calculate x position: self.key_number_to_x_mm(gracenote.pitch)
        # - Calculate y position: self.time_to_y_mm(gracenote.time)
        # - Draw smaller rectangle: self.canvas.add_rectangle(...)
        # - Tag with ['graceNotes', f'gracenote_{stave_idx}_{gracenote.id}']
        pass
