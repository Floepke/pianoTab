'''
Note drawing mixin for the Editor class.

Handles drawing note events on the piano roll canvas.
'''
from __future__ import annotations
from typing import TYPE_CHECKING, Literal, Optional

from file import note
from gui.colors import ACCENT_COLOR_HEX
from utils.CONSTANTS import BLACK_KEYS
from utils.operator import OperatorThreshold

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
    
    # Threshold-based comparison operator for time values
    _time_op = OperatorThreshold(threshold=0.001)
    
    # Type hints for Editor attributes used by this mixin
    if TYPE_CHECKING:
        score: SCORE
        canvas: Canvas
        semitone_width: float
        
        def pitch_to_x(self, pitch: int) -> float: ...
        def time_to_y(self, time: float) -> float: ...
        def get_barline_positions(self) -> list[float]: ...
    
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
                          draw_mode: Optional[Literal['note', 'cursor', 'select/edit', 'selected']] = 'note') -> None:
        '''Draw a single note event.

        Args:
            stave_idx: Index of the stave containing the note.
            note: The note event to draw.
            draw_mode: The type of single note ('note', 'cursor' or 'select/edit')
                - 'note': regular note drawing
                - 'cursor': draw as cursor (accent color), don't draw the midinote
                - 'select/edit': draw as select/edit note (accent color)
                - 'selected': draw as selected note (accent color)
        '''
        # attempt to delete existing drawing of this note + set base_tag
        if draw_mode in ('note', 'selected'):
            self.canvas.delete_by_tag(str(note.id))
            base_tag = str(note.id)
        elif draw_mode == 'cursor':
            self.canvas.delete_by_tag('cursor')
            base_tag = 'cursor'
        else: # 'select/edit'
            self.canvas.delete_by_tag('select/edit')
            base_tag = 'select/edit'

        # determine color:
        if draw_mode in ('cursor', 'select/edit', 'selected'):
            color = ACCENT_COLOR_HEX
        else:
            color = note.color

        # position
        x = self.pitch_to_x(note.pitch)
        y = self.time_to_y(note.time)
        y_note_stop = self.time_to_y(note.time + note.duration)

        # draw the midinote
        semitone_width = self.semitone_width * 2
        if draw_mode in ('note', 'select/edit', 'selected'):
            self.canvas.add_rectangle(
                x1_mm=x - semitone_width / 2,
                y1_mm=y + semitone_width / 2 if note.blackNoteDirection == 'v' else y,
                x2_mm=x + semitone_width / 2,
                y2_mm=y_note_stop,
                fill=True,
                fill_color=note.colorMidiNote if draw_mode == 'note' else color,
                outline=False,
                tags=['midinote', base_tag]
            )

        # draw notestop - only if followed by a rest in the same hand
        if self._is_followed_by_rest(stave_idx, note):
            self.canvas.add_polygon(
                points_mm=[
                    x - semitone_width / 2, y_note_stop,
                    x + semitone_width / 2, y_note_stop,
                    x, y_note_stop - semitone_width
                ],
                fill=True,
                fill_color=color,
                outline=False,
                tags=['stopsign', base_tag]
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
            tags=['notehead', base_tag]
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
                tags=['leftdot', base_tag]
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
            tags=['stem', base_tag]
        )

        # draw continuation dots
        self._draw_note_continuation_dot(stave_idx, note, draw_mode=draw_mode)

    def _is_followed_by_rest(self, stave_idx: int, note: Note) -> bool:
        '''Check if a note is followed by a rest (gap) in the same hand.
        
        Args:
            stave_idx: Index of the stave containing the note.
            note: The note to check.
            
        Returns:
            True if there's a gap after this note before the next note in the same hand,
            False if another note in the same hand starts immediately at or before this note ends.
        '''
        # Get the stave's note list
        if stave_idx >= len(self.score.stave):
            return True  # Default to showing note stop if stave not found
        
        stave = self.score.stave[stave_idx]
        if not hasattr(stave.event, 'note'):
            return True  # Default to showing note stop if no notes
        
        note_list = stave.event.note
        note_end_time = note.time + note.duration
        
        # Find the next note in the same hand that starts at or after this note ends
        next_note_in_hand = None
        min_time_gap = float('inf')
        
        for other_note in note_list:
            # Skip the current note itself
            if other_note.id == note.id:
                continue
            
            # Only check notes in the same hand
            if other_note.hand != note.hand:
                continue
            
            # Check if this note starts at or after the current note ends (using threshold)
            if self._time_op.greater_or_equal(other_note.time, note_end_time):
                time_gap = other_note.time - note_end_time
                if time_gap < min_time_gap:
                    min_time_gap = time_gap
                    next_note_in_hand = other_note
        
        # If no next note found, there's a rest (show note stop)
        if next_note_in_hand is None:
            return True
        
        # If there's a gap (rest) before the next note, show note stop
        # If the next note starts immediately (gap ~= 0 within threshold), don't show note stop
        return self._time_op.greater(min_time_gap, 0)

    def _draw_note_continuation_dot(self, stave_idx: int, note: Note, 
                                 draw_mode: Optional[Literal['note', 'cursor', 'select/edit', 'selected']] = 'note') -> None:
        '''Draw a note continuation dot for a single note event.

        Args:
            stave_idx: Index of the stave containing the note.
            note: The note event that is being drawn.
                - we need to check if there is another note starting somewhere in the middle of this note
                - we use an efficient looping system to loop first backwards from the current notes index
                    (we always keep the notelist sorted on time key) and look forward.
                - if another note time is later than this notes time + duration we can break the loop (no dot needed)
                - if another note time is found in the duration range we draw the dot at that time position on the current midinote.
                - if another note time+duration is found in the duration range we draw the dot at that time position on the current midinote.

            draw_mode: The type of single note ('note', 'cursor', 'select/edit' or 'selected')
                - 'note': regular note drawing
                - 'cursor': draw as cursor (accent color), don't draw the midinote
                - 'select/edit': draw as select/edit note (accent color)
                - 'selected': draw as selected note (accent color)
        '''
        # Don't draw continuation dots for cursor mode
        if draw_mode == 'cursor':
            return
        
        # Get the stave's note list
        if stave_idx >= len(self.score.stave):
            return
        
        stave = self.score.stave[stave_idx]
        if not hasattr(stave.event, 'note'):
            return
        
        note_list = stave.event.note
        
        # Find current note's index in the list
        try:
            current_idx = note_list.index(note)
        except ValueError:
            return  # Note not found in list
        
        # Calculate the time range we're checking
        note_start = note.time
        note_end = note.time + note.duration
        
        # List to store times where we need to draw dots
        dot_times = []
        
        # Search backwards from current note
        for i in range(current_idx - 1, -1, -1):
            other_note = note_list[i]
            other_start = other_note.time
            other_end = other_note.time + other_note.duration
            
            # If other note ends before our note starts, we can stop looking backwards (using threshold)
            if self._time_op.less_or_equal(other_end, note_start):
                break
            
            # Only consider notes from the same hand
            if other_note.hand != note.hand:
                continue
            
            # Check if other note starts within our duration range (using threshold)
            if self._time_op.less(note_start, other_start) and self._time_op.less(other_start, note_end):
                dot_times.append(other_start)
            
            # Check if other note ends within our duration range (using threshold)
            if self._time_op.less(note_start, other_end) and self._time_op.less(other_end, note_end):
                dot_times.append(other_end)
        
        # Search forwards from current note
        for i in range(current_idx + 1, len(note_list)):
            other_note = note_list[i]
            other_start = other_note.time
            other_end = other_note.time + other_note.duration
            
            # If other note starts after our note ends, we can stop looking forward (using threshold)
            if self._time_op.greater_or_equal(other_start, note_end):
                break
            
            # Only consider notes from the same hand
            if other_note.hand != note.hand:
                continue
            
            # Check if other note starts within our duration range (using threshold)
            if self._time_op.less(note_start, other_start) and self._time_op.less(other_start, note_end):
                dot_times.append(other_start)
            
            # Check if other note ends within our duration range (using threshold)
            if self._time_op.less(note_start, other_end) and self._time_op.less(other_end, note_end):
                dot_times.append(other_end)
        
        # Check for barline crossings
        barline_positions = self.get_barline_positions()
        for barline_time in barline_positions:
            # Check if barline falls within this note's duration (using threshold)
            if self._time_op.less(note_start, barline_time) and self._time_op.less(barline_time, note_end):
                dot_times.append(barline_time)
        
        # Remove duplicates and sort
        dot_times = sorted(set(dot_times))
        
        # Draw dots at each position
        if not dot_times:
            return  # No dots needed
        
        # Determine base tag and color (same as in _draw_single_note)
        if draw_mode in ('note', 'selected'):
            base_tag = str(note.id)
        else:  # 'select/edit'
            base_tag = 'select/edit'
        
        if draw_mode in ('select/edit', 'selected'):
            color = ACCENT_COLOR_HEX
        else:
            color = note.color
        
        # Calculate x position
        x = self.pitch_to_x(note.pitch)
        
        # Dot size
        dot_diameter = self.semitone_width * .80  # Adjust size as needed
        
        # Draw a dot at each intersection time
        for dot_time in dot_times:
            y = self.time_to_y(dot_time)
            
            self.canvas.add_oval(
                x1_mm=x - dot_diameter / 2,
                y1_mm=y - dot_diameter / 2 + self.semitone_width,
                x2_mm=x + dot_diameter / 2,
                y2_mm=y + dot_diameter / 2 + self.semitone_width,
                fill=True,
                fill_color=color,
                outline=False,
                tags=['leftdot', base_tag]
            )
            print('dot drawn at time:', dot_time)

    def _redraw_overlapping_notes(self, stave_idx: int, note: Note) -> None:
        '''Redraw all notes that overlap with the given note's time range.
        
        This is needed to update continuation dots when a note is added/modified/deleted.
        Also redraws notes that need note stop updates (previous note in same hand).
        
        Args:
            stave_idx: Index of the stave
            note: The note whose overlapping neighbors should be redrawn
        '''
        if stave_idx >= len(self.score.stave):
            return
        
        stave = self.score.stave[stave_idx]
        if not hasattr(stave.event, 'note'):
            return
        
        note_list = stave.event.note
        note_start = note.time
        note_end = note.time + note.duration
        
        notes_to_redraw = set()
        
        # Find all notes that overlap with this note's time range
        for other_note in note_list:
            if other_note.id == note.id:
                continue  # Skip the note itself
            
            # Only consider notes from the same hand (continuation dots only appear for same hand)
            if other_note.hand != note.hand:
                continue
            
            other_start = other_note.time
            other_end = other_note.time + other_note.duration
            
            # Check if time ranges overlap (using threshold operators)
            # Two ranges [a,b] and [c,d] overlap if: a < d AND c < b
            if self._time_op.less(note_start, other_end) and self._time_op.less(other_start, note_end):
                # This note overlaps - needs redraw for continuation dots
                notes_to_redraw.add(other_note.id)
        
        # Find notes in the same hand that might need note stop updates
        # Any note in the same hand that could have considered this note as "next" needs redrawing
        # This includes notes that end before this note AND notes that start after this note
        for other_note in note_list:
            if other_note.id == note.id:
                continue
            
            if other_note.hand == note.hand:
                other_start = other_note.time
                other_end = other_note.time + other_note.duration
                
                # If other note ends at or before this note starts, it might have checked
                # this note as its "next note" for note stop calculation
                if self._time_op.less_or_equal(other_end, note_start):
                    notes_to_redraw.add(other_note.id)
                
                # If other note starts at or after this note ends, it might have been
                # the "next note" that this note was checking
                elif self._time_op.greater_or_equal(other_start, note_end):
                    notes_to_redraw.add(other_note.id)
        
        # Redraw all affected notes
        for other_note in note_list:
            if other_note.id in notes_to_redraw:
                self._draw_single_note(stave_idx, other_note, draw_mode='note')
