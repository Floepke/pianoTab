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
            self._draw_single_gracenote(stave_idx, gracenote)

    def _draw_single_gracenote(self, stave_idx: int, gracenote: GraceNote, 
                               draw_mode: str = 'grace_note') -> None:
        '''Draw a single grace note event.

        Args:
            stave_idx: Index of the stave containing the grace note.
            gracenote: The grace note event to draw.
            draw_mode: The type of drawing ('grace_note', 'cursor', 'edit', 'selected')
                - 'grace_note': regular grace note drawing
                - 'cursor': draw as cursor (accent color)
                - 'edit': draw as edit grace note (accent color)
                - 'selected': draw as selected grace note (accent color)
        '''
        from gui.colors import ACCENT_HEX
        from utils.CONSTANTS import BLACK_KEYS
        
        # Guard against startup race condition
        if not self.score:
            return
        
        # Setup: tags and color
        if draw_mode in ('grace_note', 'selected'):
            self.canvas.delete_by_tag(str(gracenote.id))
            base_tag = str(gracenote.id)
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
            color = gracenote.color
        
        # Calculate positions
        x = self.pitch_to_x(gracenote.pitch)
        y = self.time_to_y(gracenote.time)
        
        # Calculate dimensions - scale down to 0.6 of normal note size
        scale = 0.75
        semitone_width = self.semitone_width * 2 * scale
        notehead_length = semitone_width
        
        # Determine tag for notehead type
        if gracenote.pitch in BLACK_KEYS:
            tag = 'gracenote_head_black'
        else:
            tag = 'gracenote_head_white'
        
        # Detection rectangle coordinates
        detect_x1 = x - semitone_width / 2
        detect_y1 = y
        detect_x2 = x + semitone_width / 2
        detect_y2 = y + notehead_length
        
        # Draw the notehead (scaled down, no stem, no left_dot)
        self.canvas.add_oval(
            x1_mm=detect_x1,
            y1_mm=detect_y1,
            x2_mm=detect_x2,
            y2_mm=detect_y2,
            fill=True,
            fill_color=color if gracenote.pitch in BLACK_KEYS else '#FFFFFF',
            outline=True,
            outline_width_mm=self.score.properties.globalNote.stemWidthMm * scale,
            outline_color=color,
            tags=[tag, 'grace_note', base_tag]
        )
        
        # Register detection rectangle (only for real grace notes, not cursor/edit)
        if draw_mode in ('grace_note', 'selected'):
            self.detection_rects[gracenote.id] = (detect_x1, detect_y1, detect_x2, detect_y2)
