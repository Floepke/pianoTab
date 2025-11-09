'''
Note drawing mixin for the Editor class.

Handles drawing note events on the piano roll canvas.
'''
from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from file.SCORE import SCORE, Note
    from utils.canvas import Canvas


class NoteDrawerMixin:
    '''Mixin for drawing notes.'''
    
    # Type hints for Editor attributes used by this mixin
    if TYPE_CHECKING:
        score: SCORE
        canvas: Canvas
        semitone_width: float
        
        def key_number_to_x_mm(self, pitch: int) -> float: ...
        def time_to_y_mm(self, time: float) -> float: ...
    
    def _draw_notes(self) -> None:
        '''Draw all note events from all staves.'''
        # Access the score from the Editor instance
        if not self.score:
            return
        
        # Draw each note
        for stave_idx, stave in enumerate(self.score.stave):
            for note in stave.event.note:
                self._draw_single_note(stave_idx, note)

    def _draw_single_note(self, stave_idx: int, note: Note, 
                          is_cursor: bool = False) -> None:
        '''Draw a single note event.

        Args:
            stave_idx: Index of the stave containing the note.
            note: The note event to draw.
        '''
        # TODO: Implement note drawing
        # - Calculate x position: self.key_number_to_x_mm(note.pitch)
        # - Calculate y position: self.time_to_y_mm(note.time)
        # - Calculate height: self.time_to_y_mm(note.time + note.duration) - y
        # - Draw rectangle: self.canvas.add_rectangle(...)
        # - Tag with ['notes', f'note_{stave_idx}_{note.id}']
        pass
