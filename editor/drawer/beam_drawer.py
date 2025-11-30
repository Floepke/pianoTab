'''
Beam drawing mixin for the Editor class.

Handles drawing beam events on the piano roll canvas.
'''
from __future__ import annotations
from typing import TYPE_CHECKING, Optional, Literal
from gui.colors import ACCENT_COLOR_HEX

if TYPE_CHECKING:
    from file.SCORE import SCORE, Beam
    from utils.canvas import Canvas


class BeamDrawerMixin:
    '''Mixin for drawing beams.'''
    
    # Type hints for Editor attributes used by this mixin
    if TYPE_CHECKING:
        score: SCORE
        canvas: Canvas
        editor_margin: float
        stave_width: float
        
        def time_to_y(self, time: float) -> float: ...
    
    def _draw_beams(self) -> None:
        '''Draw all beam events from all staves.'''
        if not self.score:
            return
        
        # Get the currently rendered stave index
        stave_idx = self.score.fileSettings.get_rendered_stave_index(
            num_staves=len(self.score.stave)
        )
        
        # Draw beams from the currently rendered stave
        stave = self.score.stave[stave_idx]
        for beam in stave.event.beam:
            self._draw_single_beam_marker(stave_idx, beam)

    def _draw_single_beam_marker(self, stave_idx: int, beam: Beam, 
                          draw_mode: Optional[Literal['beam', 'cursor', 'edit', 'selected']] = 'beam') -> None:
        '''Draw a single beam event.

        Args:
            stave_idx: Index of the stave containing the beam.
            beam: The beam event to draw.
            draw_mode: The drawing mode ('beam', 'cursor', 'edit', or 'selected')
        '''
        # Setup: tags and color
        if draw_mode in ('beam', 'selected'):
            self.canvas.delete_by_tag(str(beam.id))
            base_tag = str(beam.id)
            marker_tag = 'beam'  # Regular beams don't use beam_marker tag
        elif draw_mode == 'cursor':
            self.canvas.delete_by_tag('cursor')
            self.canvas.delete_by_tag('beam_marker')
            base_tag = 'cursor'
            marker_tag = 'beam_marker'
        else:  # 'edit'
            self.canvas.delete_by_tag('edit')
            self.canvas.delete_by_tag('beam_marker')
            base_tag = 'edit'
            marker_tag = 'beam_marker'
        
        # Determine color
        if draw_mode in ('cursor', 'edit', 'selected'):
            color = ACCENT_COLOR_HEX
        else:
            # Use beam's color if set, otherwise use a default
            color = beam.color if hasattr(beam, 'color') and beam.color else ACCENT_COLOR_HEX
        
        time = beam.time
        duration = beam.duration
        hand = beam.hand
        y_start = self.time_to_y(time)
        y_end = self.time_to_y(time + duration)
        
        if hand == '<': 
            x1 = 8.25
            x2 = 10
        else: 
            x1 = self.editor_margin * 2 + self.stave_width - 8.25
            x2 = self.editor_margin * 2 + self.stave_width - 10

        # Draw the beam line
        self.canvas.add_line(
            x1_mm=x1,
            y1_mm=y_start,
            x2_mm=x2,
            y2_mm=y_end,
            color=color,
            width_mm=1,
            tags=[base_tag, marker_tag]
        )

        # Draw the start and end point guide lines
        self.canvas.add_line(
            x1_mm=self.editor_margin + self.stave_width if hand == '>' else self.editor_margin,
            y1_mm=y_start,
            x2_mm=x1,
            y2_mm=y_start,
            color=color,
            width_mm=.25,
            dash=True,
            dash_pattern_mm=[1, 2],
            tags=[base_tag, marker_tag]
        )
        self.canvas.add_line(
            x1_mm=self.editor_margin + self.stave_width if hand == '>' else self.editor_margin,
            y1_mm=y_end,
            x2_mm=x2,
            y2_mm=y_end,
            color=color,
            width_mm=.25,
            dash=True,
            dash_pattern_mm=[1, 2],
            tags=[base_tag, marker_tag]
        )