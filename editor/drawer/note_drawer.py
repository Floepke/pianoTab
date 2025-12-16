'''
Note drawing mixin for the Editor class.

Handles drawing note events on the piano roll canvas.
'''
from __future__ import annotations
from typing import TYPE_CHECKING, Literal, Optional

from file import note
from gui.colors import ACCENT_HEX, DARK_HEX, LIGHT_DARKER_HEX, LIGHT_HEX, make_darker_hex
from utils.CONSTANTS import BLACK_KEYS, CF_KEYS, OPERATOR_TRESHOLD, BE_KEYS
from utils.operator import Operator

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
    _time_op = Operator(threshold=OPERATOR_TRESHOLD)
    
    # Type hints for Editor attributes used by this mixin
    if TYPE_CHECKING:
        score: SCORE
        canvas: Canvas
        semitone_width: float
        
        def pitch_to_x(self, pitch: int) -> float: ...
        def time_to_y(self, time: float) -> float: ...
        def _get_barline_positions(self) -> list[float]: ...
    
    def _draw_notes(self) -> None:
        '''Draw all note events from the currently rendered stave.'''
        # Access the score from the Editor instance
        if not self.score:
            return
        
        # Get the currently rendered stave index
        stave_idx = self.score.fileSettings.get_rendered_stave_index(
            num_staves=len(self.score.stave)
        )
        
        # Draw notes from the currently rendered stave
        stave = self.score.stave[stave_idx]
        for note in stave.event.note:
            self._draw_single_note(stave_idx, note)

    def _draw_single_note(self, stave_idx: int, note: Note, 
                          draw_mode: Optional[Literal['note', 'cursor', 'edit', 'selected']] = 'note') -> None:
        '''Draw a single note event.

        Args:
            stave_idx: Index of the stave containing the note.
            note: The note event to draw.
            draw_mode: The type of single note ('note', 'cursor' or 'edit')
                - 'note': regular note drawing
                - 'cursor': draw as cursor (accent color), don't draw the midinote
                - 'edit': draw as edit note (accent color)
                - 'selected': draw as selected note (accent color)
        '''
        # Guard against startup race condition
        if not self.score:
            return
        
        # Setup: tags and color
        base_tag, color = self._setup_note_drawing(note, draw_mode)
        
        # Draw all note elements (order doesn't matter - each calculates its own position)
        self._draw_midinote(note, draw_mode, base_tag, color)
        self._draw_notestop(stave_idx, note, base_tag, color)
        self._draw_notehead(note, base_tag, color)
        self._draw_accidental(note, base_tag, color)
        #self._draw_solid_guide(note, base_tag, color)
        #self._draw_connect_stem(stave_idx, note, base_tag, color)
        #self._draw_stem(note, base_tag, color)
        #self._draw_stem_whitespace(note, base_tag)
        #self._draw_velocity_indicator(note, base_tag)
        #self._draw_note_continuation_dot(stave_idx, note, draw_mode=draw_mode)
        #self._draw_centered_dashed_guide(stave_idx, note, base_tag=base_tag, color=color)
        #self._draw_left_dot(note, base_tag, color)
    
    def _setup_note_drawing(self, note: Note, draw_mode: str) -> tuple[str, str]:
        '''Setup drawing by deleting old elements and determining tag and color.
        
        Returns:
            tuple: (base_tag, color)
        '''
        # Delete existing drawing and set base_tag
        if draw_mode in ('note', 'selected'):
            self.canvas.delete_by_tag(str(note.id))
            base_tag = str(note.id)
        elif draw_mode == 'cursor':
            self.canvas.delete_by_tag('cursor')
            base_tag = 'cursor'
        else:  # 'edit'
            self.canvas.delete_by_tag('edit')
            base_tag = 'edit'
        
        # Determine color
        if draw_mode in ('cursor', 'edit', 'selected'):
            color = ACCENT_HEX
        else:
            color = note.color
        
        return base_tag, color

    def _draw_velocity_indicator(self, note: Note, base_tag: str) -> None:
        '''Draw the velocity indicator.'''
        # Calculate positions
        x = self.pitch_to_x(note.pitch)
        y = self.time_to_y(note.time)
        y_note_stop = self.time_to_y(note.time + note.duration)
        
        # Calculate dimensions
        semitone_width = self.semitone_width
        velocity_height = 20
        
        # set darker color for black keys
        if note.pitch in BLACK_KEYS:
            c = make_darker_hex(note.colorMidiNote, 0.2)
        else:
            c = note.colorMidiNote
        
        # Calculate velocity percentage
        velocity_percentage = note.velocity / 127
        
        self.canvas.add_text(
            text=f"{note.velocity}",
            x_mm=x,
            y_mm=y - 1,
            font_size_pt=5,
            anchor='center',
            tags=['velocity_indicator', base_tag]
        )
    
    def _draw_midinote(self, note: Note, draw_mode: str, base_tag: str, color: str) -> None:
        '''Draw the midinote rectangle (background note representation).'''
        if draw_mode in ('note', 'edit', 'selected'):
            # Calculate positions
            x = self.pitch_to_x(note.pitch)
            y = self.time_to_y(note.time)
            y_note_stop = self.time_to_y(note.time + note.duration)
            
            # Calculate dimensions
            semitone_width = self.semitone_width
            
            # setting coords
            x1 = x - semitone_width / 2
            y1 = y
            x2 = x + semitone_width / 2
            y2 = y_note_stop

            # # setting coord x1 & x2 to avoid white-over-white overlap
            # pitch_class = note.pitch % 12
            # if pitch_class in CF_KEYS:
            #     x1 = x - semitone_width / 2 * .5
            # elif pitch_class in BE_KEYS:
            #     x2 = x + semitone_width / 2 * .5

            # set darker color for black keys
            if note.pitch in BLACK_KEYS:
                c = make_darker_hex(note.colorMidiNote, 0.2)
            else:
                c = note.colorMidiNote
            
            self.canvas.add_rectangle(
                x1_mm=x1,
                y1_mm=y1,
                x2_mm=x2,
                y2_mm=y2,
                fill=True,
                fill_color=c if draw_mode == 'note' else color,
                outline=False,
                tags=['midi_note', base_tag]
            )
            
            # Register detection rectangle (only for real notes, not cursor/edit)
            if draw_mode in ('note', 'selected'):
                self.detection_rects[note.id] = (x1, y1, x2, y2)
    
    def _draw_notestop(self, stave_idx: int, note: Note, base_tag: str, color: str) -> None:
        '''Draw the note stop sign (triangle) if followed by a rest or a large single pitch jump.'''
        if self._is_followed_by_rest(stave_idx, note):
            # Calculate positions
            x = self.pitch_to_x(note.pitch)
            y_note_stop = self.time_to_y(note.time + note.duration)
            
            # Calculate dimensions
            semitone_width = self.semitone_width

            # calc width coords
            if note.pitch in BE_KEYS or note.pitch in CF_KEYS:
                x1 = x - self.semitone_width * .5
                x2 = x + self.semitone_width * .5
            else:
                x1 = x - self.semitone_width * .5
                x2 = x + self.semitone_width * .5
            
            self.canvas.add_polygon(
                points_mm=[
                    x1, y_note_stop,
                    x2, y_note_stop,
                    x, y_note_stop - semitone_width
                ],
                fill=True,
                fill_color=color,
                outline=False,
                tags=['stop_sign', base_tag]
            )
    
    def _draw_notehead(self, note: Note, base_tag: str, color: str) -> None:
        '''Draw the notehead (oval).'''
        # Calculate positions
        x = self.pitch_to_x(note.pitch)
        y = self.time_to_y(note.time)
        
        # determine tag for notehead type
        tag = 'notehead_black' if note.pitch in BLACK_KEYS else 'notehead_white'

        # notehead width
        '''Design 1: best design to my opinion'''
        if note.pitch in BE_KEYS:
            # Trim right side (E/B sit to the left of a white gap)
            x1 = x - self.semitone_width
            x2 = x + self.semitone_width * .5
        elif note.pitch in CF_KEYS:
            # Trim left side (C/F sit to the right of a white gap) - opposite of BE_GAPS
            x1 = x - self.semitone_width * .5
            x2 = x + self.semitone_width
        elif note.pitch in BLACK_KEYS:
            # Black keys are narrower
            x1 = x - self.semitone_width * .5
            x2 = x + self.semitone_width * .5
        else:
            # Regular width
            x1 = x - self.semitone_width * .75
            x2 = x + self.semitone_width * .75
        # notehead length
        if note.pitch in BLACK_KEYS:
            notehead_length = self.semitone_width * 1.5
        else:
            notehead_length = self.semitone_width * 1.5
        
        # Adjust y position for black notes above stem
        if base_tag == 'cursor' and note.pitch in BLACK_KEYS and self.score.properties.globalNote.blackNoteDirection == '^':
            y -= self.semitone_width * 1.5
        elif note.blackNoteDirection == '^' and note.pitch in BLACK_KEYS:
            y -= self.semitone_width * 1.5

        # Draw the notehead
        self.canvas.add_oval(
            x1_mm=x1,
            y1_mm=y,
            x2_mm=x2,
            y2_mm=y + notehead_length,
            fill=True,
            fill_color=color if note.pitch in BLACK_KEYS else LIGHT_HEX,
            outline=True,
            outline_width_mm=self.score.properties.globalNote.stemWidthMm,
            outline_color=color,
            tags=[tag, base_tag]
        )

        # '''Design 2: pure rectangle widths and triangle handles'''
        # x1 = x - self.semitone_width * .5
        # x2 = x + self.semitone_width * .5
        # notehead_length = self.semitone_width
        
        # if note.pitch in BLACK_KEYS:
        #     self.canvas.add_polygon(
        #         points_mm=[
        #             x1, y,
        #             x2, y,
        #             x, y + notehead_length
        #         ],
        #         fill=True,
        #         fill_color=DARK_HEX,
        #         outline=False,
        #         tags=[tag, base_tag]
        #     )
        # else:
        #     outline_w = .1
        #     self.canvas.add_polygon(
        #         points_mm=[
        #             x1+outline_w, y,
        #             x2-outline_w, y,
        #             x, y + notehead_length - outline_w
        #         ],
        #         fill=True,
        #         fill_color=LIGHT_HEX,
        #         outline=True,
        #         outline_width_mm=.1,
        #         outline_color=DARK_HEX,
        #         tags=[tag, base_tag]
        #     )

        '''Design 3: start line'''
        x1 = x - self.semitone_width * .5
        x2 = x + self.semitone_width * .5

        self.canvas.add_line(
            x1_mm=x1,
            y1_mm=y,
            x2_mm=x2,
            y2_mm=y,
            width_mm=self.score.properties.globalNote.stemWidthMm,
            color=color,
            tags=[tag, base_tag]
        )
    
    def _draw_left_dot(self, note: Note, base_tag: str, color: str) -> None:
        '''
            Draw the left hand indicator dot inside the notehead. Only drawn if
            a note from the opposite hand is starting at the same time and the
            pitch is < the current note's pitch + 3.

        '''
        if note.hand == '<':
            # # Check if there is a note from the opposite hand starting at the same time
            # for other_note in self.score.stave[0].event.note:
            #     # Skip myself
            #     if other_note.id == note.id:
            #         continue

            #     if self._time_op.equal(other_note.time, note.time) and other_note.hand == '>':
            #         if other_note.pitch <= note.pitch + 2:
            #             break
            #     else:
            #         return  # No matching note found, skip drawing the dot

            # Calculate positions
            x = self.pitch_to_x(note.pitch)
            y = self.time_to_y(note.time)
            
            # Calculate dimensions
            semitone_width = self.semitone_width * 2
            notehead_length = semitone_width
            if note.pitch in BLACK_KEYS:
                semitone_width *= 0.75
            
            # Adjust y position for black notes above stem
            if base_tag == 'cursor' and note.pitch in BLACK_KEYS and self.score.properties.globalNote.blackNoteDirection == '^':
                y -= notehead_length
            elif note.blackNoteDirection == '^' and note.pitch in BLACK_KEYS:
                y -= notehead_length
            
            # Calculate dot dimensions
            dot_diameter = semitone_width * self.score.properties.globalNote.leftDotSizeScale
            center_y = y + notehead_length / 2
            
            # Draw the dot
            self.canvas.add_oval(
                x1_mm=x - dot_diameter / 2,
                y1_mm=center_y - dot_diameter / 2,
                x2_mm=x + dot_diameter / 2,
                y2_mm=center_y + dot_diameter / 2,
                fill=True,
                fill_color=color if note.pitch not in BLACK_KEYS else '#FFFFFF',
                outline=False,
                tags=['left_dot', base_tag]
            )

    def _draw_stem(self, note: Note, base_tag: str, color: str) -> None:
        '''Draw the stem line.'''
        # Calculate positions
        x = self.pitch_to_x(note.pitch)
        y = self.time_to_y(note.time)

        # Calculate stem endpoint
        if note.hand == '<':
            stem_end_x = x - self.score.properties.globalNote.stemLengthMm
        else:
            stem_end_x = x + self.score.properties.globalNote.stemLengthMm
        
        # Draw the stem
        self.canvas.add_line(
            x1_mm=x,
            y1_mm=y,
            x2_mm=stem_end_x,
            y2_mm=y,
            width_mm=self.score.properties.globalNote.stemWidthMm,
            color=color,
            tags=['stem', base_tag]
        )
    
    def _draw_accidental(self, note: Note, base_tag: str, color: str) -> None:
        '''Draw the accidental line (sharp/flat indicator).
        
        The accidental value indicates the source pitch (semitones away):
        '''
        # validation
        a = note.accidental
        p = note.pitch
        t = note.time
        if a+p in BLACK_KEYS or abs(a) > 2 or a == 0:
            return  # No accidentals on black keys
        
        # Calculate positions
        x_note = self.pitch_to_x(p)
        y_note = self.time_to_y(t)
        x_from = self.pitch_to_x(p + a)
        y_from = self.time_to_y(t)

        # Draw the accidental line
        self.canvas.add_line(
            x1_mm=x_from,
            y1_mm=y_from + self.semitone_width * 2,
            x2_mm=x_note,
            y2_mm=y_note + self.semitone_width,
            width_mm=self.score.properties.globalNote.stemWidthMm,
            color=color,
            tags=['accidental', base_tag]
        )
    
    def _draw_solid_guide(self, note: Note, base_tag: str, color: str) -> None:
        '''Draw the horizontal stem line.'''
        # Calculate positions (stem is at note time, not adjusted for black notes)
        x = self.pitch_to_x(note.pitch)
        y = self.time_to_y(note.time)

        # skip if note starts at barline or grid positions
        if any(self._time_op.equal(note.time, pos) for pos in self._get_barline_and_grid_positions()):
            return
        
        # Calculate dimensions
        semitone_width = self.semitone_width * 2
        
        # setting coords
        x1 = x - semitone_width / 2
        x2 = x + semitone_width / 2
        if note.pitch in BE_KEYS:
            x2 = x + semitone_width / 2 * 0.5
        elif note.pitch in CF_KEYS:
            x1 = x - semitone_width / 2 * 0.5
        
        self.canvas.add_line(
            x1_mm=x1,
            y1_mm=y,
            x2_mm=x2,
            y2_mm=y,
            width_mm=self.score.properties.globalNote.stemWidthMm,
            color=color,
            tags=['stem', base_tag]
        )
    
    def _draw_stem_whitespace(self, note: Note, base_tag: str) -> None:
        '''Draw stem whitespace to highlight stem on barlines.'''
        if any(self._time_op.equal(note.time, barline_time) for barline_time in self._get_barline_positions()):
            # Calculate positions
            x = self.pitch_to_x(note.pitch)
            y = self.time_to_y(note.time)
            
            # Calculate stem endpoint
            if note.hand == '<':
                xx = x - note.stemLengthMm
                self.canvas.add_line(
                    x1_mm=x + 3,
                    y1_mm=y,
                    x2_mm=xx - 2,
                    y2_mm=y,
                    width_mm=self.score.properties.globalBasegrid.barlineWidthMm,
                    color=LIGHT_DARKER_HEX,
                    tags=['stem_white_space', base_tag],
                    cap='flat'
                )
            else:
                xx = x + note.stemLengthMm
                self.canvas.add_line(
                    x1_mm=xx + 2,
                    y1_mm=y,
                    x2_mm=x - 3,
                    y2_mm=y,
                    width_mm=self.score.properties.globalBasegrid.barlineWidthMm,
                    color=LIGHT_DARKER_HEX,
                    tags=['stem_white_space', base_tag],
                    cap='flat'
                )

    def _draw_centered_dashed_guide(self, stave_idx: int, note: Note, base_tag: str, color: str) -> None:
        '''Draw a centered connection guide line between the outer notes that form a chord (same start time).
        
        Args:
            stave_idx: Index of the stave containing the note
            note: The note to check for chord connections or single note guide
            base_tag: Tag for canvas items
            color: Color for the connection line
        '''
        # Guard against startup race condition
        if not self.score:
            return
        
        if stave_idx >= len(self.score.stave):
            return
        
        # check if note starts at barline or grid positions
        if any(self._time_op.equal(note.time, pos) for pos in self._get_barline_and_grid_positions()):
            return  # Don't draw chord guide on barline/grid positions
        
        note_list = self.score.stave[stave_idx].event.note
        
        # Find all notes with the same start time
        same_time_notes = [n for n in note_list if self._time_op.equal(n.time, note.time)]

        if len(same_time_notes) < 2:
            return  # No chord, only a single note
        
        # Find the lowest pitch note in the chord
        lowest_note = min(same_time_notes, key=lambda n: n.pitch)
        
        # Only draw if this is the lowest note - prevents drawing multiple times
        if note.id != lowest_note.id:
            return
        
        # Find the highest pitch note in the chord
        highest_note = max(same_time_notes, key=lambda n: n.pitch)
        
        # Calculate positions for the chord guide line
        x1 = self.pitch_to_x(lowest_note.pitch)
        y1 = self.time_to_y(lowest_note.time)
        
        x2 = self.pitch_to_x(highest_note.pitch)
        y2 = self.time_to_y(highest_note.time)  # Should be same as y1 within threshold
        
        # Draw connection line between the lowest and highest notes
        guide_overspan = self.semitone_width * 4  # Extend beyond noteheads
        self.canvas.add_line(
            x1_mm=x1 - guide_overspan,
            y1_mm=y1,
            x2_mm=x2 + guide_overspan,
            y2_mm=y2,
            width_mm=self.score.properties.globalBasegrid.gridlineWidthMm, # 2 times thinner than stem by design
            color='#000000',
            tags=['chord_guide', base_tag],
            dash=True,
            dash_pattern_mm=self.score.properties.globalBasegrid.gridlineDashPatternMm
        )

    def _draw_connect_stem(self, stave_idx: int, note: Note, base_tag: str, color: str) -> None:
        '''Draw a centered connection guide line between the outer notes that form a chord (same start time).
        
        Args:
            stave_idx: Index of the stave containing the note
            note: The note to check for chord connections or single note guide
            base_tag: Tag for canvas items
            color: Color for the connection line
        '''
        # Guard against startup race condition
        if not self.score:
            return
        
        if stave_idx >= len(self.score.stave):
            return
        
        # # check if note starts at barline or grid positions
        # if any(self._time_op.equal(note.time, pos) for pos in self._get_barline_and_grid_positions()):
        #     return  # Don't draw chord guide on barline/grid positions
        
        note_list = [n for n in self.score.stave[stave_idx].event.note if n.hand == note.hand]
        
        # Find all notes with the same start time
        same_time_notes = [n for n in note_list if self._time_op.equal(n.time, note.time)]

        if len(same_time_notes) < 2:
            return  # No chord, only a single note
        
        # Find the lowest pitch note in the chord
        lowest_note = min(same_time_notes, key=lambda n: n.pitch)
        
        # Only draw if this is the lowest note - prevents drawing multiple times
        if note.id != lowest_note.id:
            return
        
        # Find the highest pitch note in the chord
        highest_note = max(same_time_notes, key=lambda n: n.pitch)
        
        # Calculate positions for the chord guide line
        x1 = self.pitch_to_x(lowest_note.pitch)
        y1 = self.time_to_y(lowest_note.time)
        
        x2 = self.pitch_to_x(highest_note.pitch)
        y2 = self.time_to_y(highest_note.time)  # Should be same as y1 within threshold
        
        # Draw connection line between the lowest and highest notes
        #x2 -= self.score.properties.globalNote.stemLengthMm
        self.canvas.add_line(
            x1_mm=x1,
            y1_mm=y1,
            x2_mm=x2,
            y2_mm=y2,
            width_mm=self.score.properties.globalBasegrid.barlineWidthMm, # 2 times thinner than stem by design
            color=color,
            tags=['chord_connect', base_tag],
            dash=False
        )

    def _a_following_notes_diff_is_less_then_interval(self, stave_idx: int, note: Note, interval: int = 12) -> bool:
        '''Check if the next note that starts on the current notes end time is less than the given interval away.
        
        Args:
            stave_idx: Index of the stave containing the note.
            note: The note to check.
        Returns:
            True if the next note that starts on the current notes end time in the same hand is more than an octave apart,
            False otherwise.
        '''
        # Guard against startup race condition
        if not self.score:
            return True  # Default to showing note stop
        # Get the stave's note list
        if stave_idx >= len(self.score.stave):
            return True  # Default to showing note stop if stave not found
        
        stave = self.score.stave[stave_idx]
        answer = False
        if not hasattr(stave.event, 'note'):
            return True  # Default to showing note stop if no notes
        
        note_list = stave.event.note
        note_end_time = note.time + note.duration
        for other_note in note_list:
            # Skip the current note itself
            if other_note.id == note.id:
                continue
            
            # Only check notes in the same hand
            if other_note.hand != note.hand:
                continue
            
            # Check if this note starts at the current note's end time (using threshold)
            if self._time_op.equal(other_note.time, note_end_time):
                # Check if pitch difference is more than an octave
                if abs(other_note.pitch - note.pitch) <= interval:
                    answer = True
                    break # found a note within an octave
        return answer

    def _is_followed_by_rest(self, stave_idx: int, note: Note) -> bool:
        '''Check if a note is followed by a rest (gap) in the same hand.
        
        Args:
            stave_idx: Index of the stave containing the note.
            note: The note to check.
            
        Returns:
            True if there's a gap after this note before the next note in the same hand,
            False if another note in the same hand starts immediately at or before this note ends.
        '''
        # Guard against startup race condition
        if not self.score:
            return True  # Default to showing note stop
        
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
                                 draw_mode: Optional[Literal['note', 'cursor', 'edit', 'selected']] = 'note') -> None:
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

            draw_mode: The type of single note ('note', 'cursor', 'edit' or 'selected')
                - 'note': regular note drawing
                - 'cursor': draw as cursor (accent color), don't draw the midinote
                - 'edit': draw as edit note (accent color)
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
        
        note_list = sorted(stave.event.note, key=lambda n: n.time)
        
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
            if other_note.hand != note.hand or other_note.id == note.id:
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
            if other_note.hand != note.hand or other_note.id == note.id:
                continue
            
            # Check if other note starts within our duration range (using threshold)
            if self._time_op.less(note_start, other_start) and self._time_op.less(other_start, note_end):
                dot_times.append(other_start)
            
            # Check if other note ends within our duration range (using threshold)
            if self._time_op.less(note_start, other_end) and self._time_op.less(other_end, note_end):
                dot_times.append(other_end)
        
        # Check for barline crossings
        barline_positions = self._get_barline_positions()
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
        else:  # 'edit'
            base_tag = 'edit'
        
        if draw_mode in ('edit', 'selected'):
            color = ACCENT_HEX
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
                tags=['left_dot', base_tag]
            )

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

    def _this_interval__pitch_is_overlapping(self, note: Note, interval: int) -> bool:
        '''Check if there is an overlapping note at pitch = note.pitch + interval in the same hand.

        Uses a bidirectional efficient scan around the current note (sorted by time),
        stopping early when the search leaves the overlap window.

        Args:
            note: The reference note.
            interval: The pitch interval to check (target pitch = note.pitch + interval).

        Returns:
            True if a note with pitch = note.pitch + interval overlaps in time with the given note (same hand),
            False otherwise.
        '''
        # Guard against startup race condition
        if not self.score:
            return False

        # Resolve the currently rendered stave index (consistent with other methods)
        stave_idx = self.score.fileSettings.get_rendered_stave_index(
            num_staves=len(self.score.stave)
        )
        if stave_idx >= len(self.score.stave):
            return False

        stave = self.score.stave[stave_idx]
        if not hasattr(stave.event, 'note'):
            return False

        # Prepare search
        target_pitch = note.pitch + interval
        note_list = sorted(stave.event.note, key=lambda n: n.time)

        # Try to locate the exact object in the sorted list
        try:
            current_idx = note_list.index(note)
        except ValueError:
            # Fallback: no index, do a full scan (still safe)
            note_start = note.time
            note_end = note.time + note.duration
            for other in note_list:
                if other.id == note.id or other.hand != note.hand:
                    continue
                # quick pitch check
                if other.pitch != target_pitch:
                    continue
                other_start = other.time
                other_end = other.time + other.duration
                # overlap: [a,b] overlaps [c,d] if a < d and c < b (with threshold)
                if self._time_op.less(note_start, other_end) and self._time_op.less(other_start, note_end):
                    return True
            return False

        # Time window for overlap
        note_start = note.time
        note_end = note.time + note.duration

        # Scan backwards until other_end <= note_start (no more overlaps possible)
        for i in range(current_idx - 1, -1, -1):
            other = note_list[i]
            if other.id == note.id or other.hand != note.hand:
                continue

            other_start = other.time
            other_end = other.time + other.duration

            # If other note ends before or at our start, remaining earlier notes can't overlap
            if self._time_op.less_or_equal(other_end, note_start):
                break

            # Only check matching pitch
            if other.pitch != target_pitch:
                continue

            # Overlap condition
            if self._time_op.less(note_start, other_end) and self._time_op.less(other_start, note_end):
                return True

        # Scan forwards until other_start >= note_end (no more overlaps possible)
        for i in range(current_idx + 1, len(note_list)):
            other = note_list[i]
            if other.id == note.id or other.hand != note.hand:
                continue

            other_start = other.time
            other_end = other.time + other.duration

            # If other note starts at or after our end, remaining later notes can't overlap
            if self._time_op.greater_or_equal(other_start, note_end):
                break

            # Only check matching pitch
            if other.pitch != target_pitch:
                continue

            # Overlap condition
            if self._time_op.less(note_start, other_end) and self._time_op.less(other_start, note_end):
                return True

        return False
