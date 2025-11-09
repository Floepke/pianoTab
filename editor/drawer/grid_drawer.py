'''
Grid and barline drawing mixin for the Editor class.

Handles drawing barlines, measure numbers, and gridlines.
'''

from kivy.metrics import sp
from utils.CONSTANTS import PIANOTICK_QUARTER


class GridDrawerMixin:
    '''Mixin for drawing barlines and grid lines.'''
    
    def _draw_barlines_and_grid(self):
        '''Draw barlines and grid lines based on your Tkinter algorithm.'''
        # Calculate barline positions (your get_editor_barline_positions equivalent)
        barline_positions = []
        total_ticks = 0.0
        
        for grid in self.score.baseGrid:
            ql = getattr(self.score, 'quarterNoteLength', PIANOTICK_QUARTER)
            measure_ticks = (ql * 4) * (grid.numerator / grid.denominator)
            for _ in range(grid.measureAmount):
                y_pos = self.time_to_y_mm(total_ticks)
                barline_positions.append((y_pos, len(barline_positions) + 1))  # (position, measure_number)
                total_ticks += measure_ticks
        
        # Draw barlines with measure numbers
        for y_pos, measure_number in barline_positions:
            if 0 <= y_pos <= self.canvas.height_mm + self.editor_margin:
                # Barline
                self.canvas.add_line(
                    x1_mm=self.editor_margin, y1_mm=y_pos,
                    x2_mm=self.editor_margin + self.stave_width, y2_mm=y_pos,
                    color=self.barline_color,
                    width_mm=self.barline_width,
                    tags=['barlines', f'barline_{measure_number}']
                )
                
                # Measure number (positioned at right edge before scrollbar)
                self.canvas.add_text(
                    text=str(measure_number),
                    x_mm=1, 
                    y_mm=y_pos,
                    font_size_pt=sp(12),  # Kivy font * 2, then convert back to pt for canvas
                    color=self.barline_color,
                    anchor='nw',
                    tags=['measureNumbers', f'measure_number_{measure_number}']
                )
        
        # Calculate and draw gridlines (your get_editor_gridline_positions equivalent)
        total_ticks = 0.0
        for grid in self.score.baseGrid:
            ql = getattr(self.score, 'quarterNoteLength', PIANOTICK_QUARTER)
            measure_ticks = (ql * 4) * (grid.numerator / grid.denominator)
            subdivision_ticks = measure_ticks / grid.numerator
            
            for _ in range(grid.measureAmount):
                for i in range(1, grid.numerator):  # Skip first beat (that's the barline)
                    grid_ticks = total_ticks + i * subdivision_ticks
                    y_pos = self.time_to_y_mm(grid_ticks)
                    
                    if 0 <= y_pos <= self.canvas.height_mm + self.editor_margin:
                        self.canvas.add_line(
                            x1_mm=self.editor_margin, y1_mm=y_pos,
                            x2_mm=self.editor_margin + self.stave_width, y2_mm=y_pos,
                            color=self.gridline_color,
                            width_mm=self.gridline_width,
                            dash=True,  # Dashed gridlines
                            dash_pattern_mm=tuple(self.gridline_dash_pattern),  # Use SCORE model pattern
                            tags=['gridlines', f'gridline_{total_ticks}_{i}']
                        )
                total_ticks += measure_ticks
        
        # Draw end barline (thicker)
        final_y_pos = self.time_to_y_mm(self.get_score_length_in_ticks())
        if 0 <= final_y_pos <= self.canvas.height_mm + self.editor_margin:
            self.canvas.add_line(
                x1_mm=self.editor_margin, y1_mm=final_y_pos,
                x2_mm=self.editor_margin + self.stave_width, y2_mm=final_y_pos,
                color=self.barline_color,
                width_mm=self.barline_width * 2,  # Double thickness for end barline
                tags=['barlines', 'endBarline']
            )
