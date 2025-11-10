'''
Note drawing mixin for the Editor class.

Handles drawing note events on the piano roll canvas.
'''
from __future__ import annotations
from typing import TYPE_CHECKING

from file import note
from gui.colors import ACCENT_COLOR
from utils.CONSTANTS import BLACK_KEYS

if TYPE_CHECKING:
    from file.SCORE import SCORE
    from file.note import Note
    from utils.canvas import Canvas


class NoteDrawerMixin:
    '''
        Mixin for drawing notes.

        notes:
            - pitch_to_x and x_to_pitch for x positioning
            - time_to_y and y_to_time for vertical positioning
    '''
    
    # Type hints for Editor attributes used by this mixin
    if TYPE_CHECKING:
        score: SCORE
        canvas: Canvas
        semitone_width: float
        
        def pitch_to_x(self, pitch: int) -> float: ...
        def time_to_y(self, time: float) -> float: ...
    
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
                          is_cursor_or_selected: bool = False) -> None:
        '''Draw a single note event.

        Args:
            stave_idx: Index of the stave containing the note.
            note: The note event to draw.
        '''
        # determine color:
        if is_cursor_or_selected:
            color = ACCENT_COLOR
        else:
            color = note.color

        # position
        x = self.pitch_to_x(note.pitch)
        y = self.time_to_y(note.time)
        y_note_stop = self.time_to_y(note.time + note.duration)

        # draw the midinote
        semitone_width = self.semitone_width * 2
        self.canvas.add_rectangle(
            x1_mm=x - semitone_width / 2,
            y1_mm=y,
            x2_mm=x + semitone_width / 2,
            y2_mm=y_note_stop,
            fill=True,
            fill_color=note.colorMidiNote,
            outline=False,
            tags=['midinote', str(note.id)]
        )

        # draw the notehead + leftdot
        notehead_length = semitone_width
        if note.pitch in BLACK_KEYS:
            semitone_width *= 0.75  # slightly smaller notehead for black keys
        if note.blackNoteDirection == '^' and note.pitch in BLACK_KEYS:
            y -= notehead_length # black note is above the stem
        self.canvas.add_oval(
            x1_mm=x - semitone_width / 2,
            y1_mm=y,
            x2_mm=x + semitone_width / 2,
            y2_mm=y + notehead_length,
            fill=True,
            fill_color=color if note.pitch in BLACK_KEYS else '#FFFFFF',
            outline=True,
            outline_width_mm=self.score.properties.globalNote.stemWidthMm,
            outline_color=color,
            tags=['notehead', str(note.id)]
        )
        if note.hand == '<':
            # left dot - centered in the notehead
            dot_diameter = semitone_width * self.score.properties.globalNote.leftDotSizeScale  # using SCORE property
            center_y = y + notehead_length / 2  # Center of the notehead vertically
            
            self.canvas.add_oval(
                x1_mm=x - dot_diameter / 2,
                y1_mm=center_y - dot_diameter / 2,
                x2_mm=x + dot_diameter / 2,
                y2_mm=center_y + dot_diameter / 2,
                fill=True,
                fill_color=color if note.pitch not in BLACK_KEYS else '#FFFFFF',
                outline=False,
                tags=['leftdot', str(note.id)]
            )
        
        # draw the stem
        if note.blackNoteDirection == '^' and note.pitch in BLACK_KEYS:
            y += notehead_length # we need to change y back for stem drawing
        if note.hand == '<': xx = x - note.stemLengthMm
        else: xx = x + note.stemLengthMm
        # left hand - stem to the left side
        self.canvas.add_line(
            x1_mm=x,
            y1_mm=y,
            x2_mm=xx,
            y2_mm=y,
            width_mm=self.score.properties.globalNote.stemWidthMm,
            color=color,
            tags=['stem', str(note.id)]
        )
