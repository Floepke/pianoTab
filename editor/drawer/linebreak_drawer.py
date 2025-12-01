'''
Line break drawing mixin for the Editor class.

Handles drawing line break indicators on the piano roll canvas.
'''
from __future__ import annotations
from typing import TYPE_CHECKING
from gui.colors import ACCENT_COLOR_HEX

if TYPE_CHECKING:
    from file.SCORE import SCORE, LineBreak
    from utils.canvas import Canvas


class LineBreakDrawerMixin:
    '''Mixin for drawing line break indicators.'''
    
    # Type hints for Editor attributes used by this mixin
    if TYPE_CHECKING:
        score: SCORE
        canvas: Canvas
        editor_margin: float
        stave_width: float
        
        def time_to_y(self, time: float) -> float: ...
    
    def _draw_line_breaks(self) -> None:
        '''Draw all line break indicators.'''
        if not self.score:
            return
        
        # Draw each line break
        for linebreak in self.score.lineBreak:
            self._draw_single_line_break(linebreak)

    def _draw_single_line_break(self, linebreak: LineBreak, 
                                draw_mode: str = 'line_break') -> None:
        '''Draw a single line break indicator.

        Args:
            linebreak: The line break to draw.
            draw_mode: The type of drawing ('line_break', 'cursor', 'edit', 'selected')
                - 'line_break': regular line break drawing
                - 'cursor': draw as cursor (accent color)
                - 'edit': draw as edit line break (accent color)
                - 'selected': draw as selected line break (accent color)
        '''
        
        # Guard against startup race condition
        if not self.score:
            return
        
        # Setup: tags and color
        if draw_mode in ('line_break', 'selected'):
            self.canvas.delete_by_tag(str(linebreak.id))
            base_tag = str(linebreak.id)
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
            color = linebreak.color if hasattr(linebreak, 'color') else '#000000'
        
        # Position: horizontal line at the linebreak time
        y = self.time_to_y(linebreak.time)

        # From right side of stave to the outer right of editor view
        x_start = self.editor_margin + self.stave_width
        x_end = self.editor_margin * 2 + self.stave_width
        
        # Draw dashed guide line
        self.canvas.add_line(
            x1_mm=x_start,
            y1_mm=y,
            x2_mm=x_end,
            y2_mm=y,
            color=color,
            width_mm=0.25,
            dash=True,
            dash_pattern_mm=[1, 2],
            tags=['line_break', base_tag]
        )
        # draw linebreak indicator:
        indicator_x1 = x_end - 1
        indicator_y1 = y
        indicator_x2 = x_end - 6 - 1
        indicator_y2 = y + 6
        
        self.canvas.add_rectangle(
            x1_mm=indicator_x1,
            y1_mm=indicator_y1,
            x2_mm=indicator_x2,
            y2_mm=indicator_y2,
            fill=False,
            outline=True,
            outline_color=color,
            outline_width_mm=0.25,
            tags=['line_break', base_tag]
        )
        self.canvas.add_text(
            x_mm=x_end - 3 - 1,
            y_mm=y,
            text='B',
            font_size_pt=16,
            anchor='tc',
            color=color,
            tags=['line_break', base_tag]
        )
        
        # Register detection rectangle (only for real elements, not cursor/edit)
        if draw_mode in ('line_break', 'selected'):
            self.detection_rects[linebreak.id] = (indicator_x1, indicator_y1, indicator_x2, indicator_y2)
