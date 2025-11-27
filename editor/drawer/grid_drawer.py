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
        '''Draw barlines and grid lines based on baseGrid configuration.'''
        
        # Initialize time cursor
        time_cursor = 0.0
        unit = self.score.fileSettings.quarterNoteUnit
        
        for grid in self.score.baseGrid:
            
            # Values from baseGrid
            num = grid.numerator
            den = grid.denominator
            grid_times = grid.gridTimes
            amount = grid.measureAmount
            visible = grid.timeSignatureIndicatorVisible
            
            # How long is one measure?
            meas_length = (unit * 4) * (num / den)
            
            for meas_no in range(amount):
                
                # Draw barline at start of measure
                barline_y = self.time_to_y(time_cursor)
                
                # Only draw if within viewport
                if 0 <= barline_y <= self.canvas.height_mm + self.editor_margin:
                    self.canvas.add_line(
                        x1_mm=self.editor_margin, 
                        y1_mm=barline_y,
                        x2_mm=self.editor_margin + self.stave_width, 
                        y2_mm=barline_y,
                        color=self.barline_color,
                        width_mm=self.score.properties.globalBasegrid.barlineWidthMm,
                        tags=['barline', f'barline_{int(time_cursor)}']
                    )
                    
                    # Draw measure number if visible
                    if visible:
                        self.canvas.add_text(
                            x_mm=self.editor_margin - 10,  # Position to the left of the barline
                            y_mm=barline_y,  # Slightly below the barline
                            text=str(meas_no + 1),
                            font_size_pt=15,
                            anchor='top_left',
                            color=self.score.properties.globalMeasureNumbering.color,
                            tags=['measurenumber', f'measurenumber_{int(time_cursor)}']
                        )
                
                # Draw grid lines at subdivision points defined in gridTimes
                for i, grid_time in enumerate(grid_times):
                    # Skip if grid_time is 0 (that's the barline position)
                    if grid_time == 0:
                        continue
                    
                    # Calculate absolute time position
                    grid_tick_position = time_cursor + grid_time
                    grid_y = self.time_to_y(grid_tick_position)
                    
                    # Only draw if within viewport
                    if 0 <= grid_y <= self.canvas.height_mm + self.editor_margin:
                        self.canvas.add_line(
                            x1_mm=self.editor_margin, 
                            y1_mm=grid_y,
                            x2_mm=self.editor_margin + self.stave_width, 
                            y2_mm=grid_y,
                            color=self.gridline_color,
                            width_mm=self.gridline_width,
                            dash=True,  # Dashed gridlines
                            dash_pattern_mm=tuple(self.gridline_dash_pattern),
                            tags=['gridline', f'gridline_{int(grid_tick_position)}_{i}']
                        )
                
                # Move time cursor forward by one measure
                time_cursor += meas_length
        
        # Draw final barline at the end of the score (double thickness)
        final_y_pos = self.time_to_y(time_cursor)
        if 0 <= final_y_pos <= self.canvas.height_mm + self.editor_margin:
            self.canvas.add_line(
                x1_mm=self.editor_margin, 
                y1_mm=final_y_pos,
                x2_mm=self.editor_margin + self.stave_width, 
                y2_mm=final_y_pos,
                color=self.barline_color,
                width_mm=self.score.properties.globalBasegrid.barlineWidthMm * 2,  # Double thickness
                tags=['barline', 'endBarline']
            )
