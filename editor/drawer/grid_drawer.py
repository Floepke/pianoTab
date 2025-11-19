'''
Grid and barline drawing mixin for the Editor class.

Handles drawing barlines, measure numbers, and gridlines.
'''

from kivy.metrics import sp
from utils.CONSTANTS import PIANOTICK_QUARTER


class GridDrawerMixin:
    '''
        Mixin for drawing barlines and grid lines.
    '''
    
    def _draw_barlines_and_grid(self):
        '''Draw barlines and grid lines based on your Tkinter algorithm.'''
        print(f'Editor: _draw_barlines_and_grid() called, score has {len(self.score.baseGrid)} baseGrids')
        # Calculate barline positions (your get_editor_barline_positions equivalent)
        barline_positions = []
        total_ticks = 0.0
        
        for grid in self.score.baseGrid:
            ql = self.score.fileSettings.quarterNoteUnit if (self.score and hasattr(self.score, 'fileSettings')) else PIANOTICK_QUARTER
            measure_ticks = (ql * 4) * (grid.numerator / grid.denominator)
            print(f'Editor: baseGrid: {grid.measureAmount} measures of {grid.numerator}/{grid.denominator}, measure_ticks={measure_ticks}')
            for _ in range(grid.measureAmount):
                # Draw barline at the end of this measure
                y_pos = self.time_to_y(total_ticks)
                barline_positions.append((y_pos, len(barline_positions) + 1))  # (position, measure_number)
                total_ticks += measure_ticks
        
        print(f'Editor: Calculated {len(barline_positions)} barline positions')
        if barline_positions:
            print(f'Editor: First 3 barline y positions: {[y for y, _ in barline_positions[:3]]}')
        # Draw barlines with measure numbers
        barlines_drawn = 0
        for y_pos, measure_number in barline_positions:
            if 0 <= y_pos <= self.canvas.height_mm + self.editor_margin:
                # Barline
                self.canvas.add_line(
                    x1_mm=self.editor_margin, y1_mm=y_pos,
                    x2_mm=self.editor_margin + self.stave_width, y2_mm=y_pos,
                    color=self.barline_color,
                    width_mm=self.score.properties.globalBasegrid.barlineWidthMm,
                    tags=['barline', f'barline_{measure_number}']
                )
                barlines_drawn += 1
                if barlines_drawn <= 3:
                    print(f'Editor: Drew barline {measure_number} at y={y_pos}mm, x from {self.editor_margin}mm to {self.editor_margin + self.stave_width}mm')
                
                # Measure number (positioned at right edge before scrollbar)
                self.canvas.add_text(
                    text=str(measure_number),
                    x_mm=1, 
                    y_mm=y_pos,
                    font_size_pt=sp(12),  # Kivy font * 2, then convert back to pt for canvas
                    color=self.barline_color,
                    anchor='nw',
                    tags=['measurenumber', f'measure_number_{measure_number}']
                )
        
        print(f'Editor: Actually drew {barlines_drawn} barlines (filtered by viewport height={self.canvas.height_mm}mm + margin={self.editor_margin}mm)')
        
        # Calculate and draw gridlines (your get_editor_gridline_positions equivalent)
        total_ticks = 0.0
        for grid in self.score.baseGrid:
            ql = self.score.fileSettings.quarterNoteUnit if (self.score and hasattr(self.score, 'fileSettings')) else PIANOTICK_QUARTER
            measure_ticks = (ql * 4) * (grid.numerator / grid.denominator)
            subdivision_ticks = measure_ticks / grid.numerator
            
            for _ in range(grid.measureAmount):
                for i in range(1, grid.numerator):  # Skip first beat (that's the barline)
                    grid_ticks = total_ticks + (i * subdivision_ticks)
                    y_pos = self.time_to_y(grid_ticks)
                    
                    if 0 <= y_pos <= self.canvas.height_mm + self.editor_margin:
                        self.canvas.add_line(
                            x1_mm=self.editor_margin, y1_mm=y_pos,
                            x2_mm=self.editor_margin + self.stave_width, y2_mm=y_pos,
                            color=self.gridline_color,
                            width_mm=self.gridline_width,
                            dash=True,  # Dashed gridlines
                            dash_pattern_mm=tuple(self.gridline_dash_pattern),  # Use SCORE model pattern
                            tags=['gridline', f'gridline_{total_ticks}_{i}']
                        )
                total_ticks += measure_ticks
        
        # Draw end barline (thicker)
        # Final barline at the end of the score
        final_y_pos = self.time_to_y(self.get_score_length_in_ticks())
        if 0 <= final_y_pos <= self.canvas.height_mm + self.editor_margin:
            self.canvas.add_line(
                x1_mm=self.editor_margin, y1_mm=final_y_pos,
                x2_mm=self.editor_margin + self.stave_width, y2_mm=final_y_pos,
                color=self.barline_color,
                width_mm=self.score.properties.globalBasegrid.barlineWidthMm * 2,  # Double thickness for end barline
                tags=['barline', 'endBarline']
            )
