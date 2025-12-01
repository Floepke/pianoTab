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
        elif draw_mode == 'cursor':
            self.canvas.delete_by_tag('cursor')
            base_tag = 'cursor'
        else:  # 'edit'
            self.canvas.delete_by_tag('edit')
            base_tag = 'edit'
        
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
            x1 = 10.25
            x2 = 12
        else: 
            x1 = self.editor_margin * 2 + self.stave_width - 10.25
            x2 = self.editor_margin * 2 + self.stave_width - 12

        # Draw the beam line
        self.canvas.add_line(
            x1_mm=x1,
            y1_mm=y_start,
            x2_mm=x2,
            y2_mm=y_end,
            color=color,
            width_mm=1,
            tags=[base_tag, 'beam_line']
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
            tags=[base_tag, 'beam_start_marker']
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
            tags=[base_tag, 'beam_end_marker']
        )
        
        # Register detection rectangle (the main beam line area, only for real beams)
        if draw_mode in ('beam', 'selected'):
            # Detection area covers the main beam line with some margin
            detect_x1 = min(x1, x2) - 1  # Add 1mm margin on each side
            detect_x2 = max(x1, x2) + 1
            detect_y1 = min(y_start, y_end)
            detect_y2 = max(y_start, y_end)
            self.detection_rects[beam.id] = (detect_x1, detect_y1, detect_x2, detect_y2)