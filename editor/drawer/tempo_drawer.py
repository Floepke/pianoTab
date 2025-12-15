'''
Tempo drawing mixin for the Editor class.

Handles drawing tempo events on the piano roll canvas.
'''
from __future__ import annotations
from typing import TYPE_CHECKING

from gui.colors import DARK_HEX, LIGHT_HEX

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
            self._draw_single_tempo(stave_idx, tempo)

    def _draw_single_tempo(self, stave_idx: int, tempo: Tempo) -> None:
        '''Draw a single tempo event.

        Args:
            stave_idx: Index of the stave containing the tempo.
            tempo: The tempo event to draw.
        '''
        # Convert tempo time to y-coordinate
        y = self.time_to_y(tempo.time)

        # Compute tags and hitbox
        base_tag = str(tempo.id)
        x1 = self.editor_margin + self.stave_width + 10
        y1 = y
        x2 = self.editor_margin + self.stave_width + 15
        y2 = y + 10 + .25

        # Draw tempo marker block
        self.canvas.add_rectangle(
            x1_mm=x1,
            y1_mm=y1,
            x2_mm=x2,
            y2_mm=y2,
            fill=True,
            fill_color=LIGHT_HEX,
            outline=False,  # Light gray with some transparency
            tags=['tempo', base_tag]
        )

        # Register detection rectangle for hit-testing
        try:
            self.detection_rects[tempo.id] = (x1, y1, x2, y2)
        except Exception:
            pass

        # time position line
        self.canvas.add_line(
            x1_mm=self.editor_margin + self.stave_width,
            y1_mm=y,
            x2_mm=self.editor_margin + self.stave_width + 15,
            y2_mm=y,
            color=DARK_HEX,
            dash=True,
            dash_pattern_mm=[2, 2],
            width_mm=0.2,
            tags=['tempo', base_tag]
        )

        # Draw tempo text
        self.canvas.add_text(
            text=f"BPM:{tempo.bpm}",
            x_mm=self.editor_margin + self.stave_width + 15,  # Small offset from left margin
            y_mm=y+.5,
            font_size_pt=12,
            color=(0.5, 0.5, 0.5, 1),
            tags=['tempo', base_tag],
            angle_deg=90
        )