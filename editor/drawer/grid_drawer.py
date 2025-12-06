'''
Grid and barline drawing mixin for the Editor class.

Handles drawing barlines, measure numbers, and gridlines.
'''

from kivy.metrics import sp
from gui.colors import DARK_LIGHTER_HEX, LIGHT_DARKER_HEX, LIGHT_HEX, rgba_to_hex
from utils.CONSTANTS import PIANOTICK_QUARTER
from utils.operator import OperatorThreshold


class GridDrawerMixin:
    '''
        Mixin for drawing barlines and grid lines.
    '''
    
    def _draw_barlines_and_grid(self):
        '''Draw barlines and grid lines based on baseGrid configuration.'''
        
        # Initialize
        time = 0.0
        unit = PIANOTICK_QUARTER
        barlines = self._get_barline_positions()
        
        for grid in self.score.baseGrid:
            
            # Values from baseGrid
            num = grid.numerator
            den = grid.denominator
            g_count = grid.gridCountsEnabled
            amount = grid.measureAmount
            tsig_indicator_visible = grid.timeSignatureIndicatorVisible
            
            # How long is one measure?
            meas_length = (unit * 4) * (num / den)

            barline_y = self.time_to_y(time)

            # Draw time-signature-indicator:
            # numerator
            self.canvas.add_text(
                x_mm=self.editor_margin - 10,  # Slightly right of stave left
                y_mm=barline_y,  # Slightly above the barline
                text=f"{num}",
                font_size_pt=16,
                anchor='bc',
                color='#000000',
                tags=['time_signature_indicator', f'time_signature_indicator_{int(time)}']
            )
            # divide line
            self.canvas.add_line(
                x1_mm=self.editor_margin - 7.5,
                y1_mm=barline_y,
                x2_mm=self.editor_margin - 12.5,
                y2_mm=barline_y,
                color='#000000',
                width_mm=0.25,
                tags=['time_signature_indicator', f'time_signature_indicator_{int(time)}']
            )
            # denominator
            self.canvas.add_text(
                x_mm=self.editor_margin - 10,
                y_mm=barline_y,
                text=f"{den}",
                font_size_pt=16,
                anchor='tc',
                color='#000000',
                tags=['time_signature_indicator', f'time_signature_indicator_{int(time)}']
            )
            
            for meas_idx in range(amount):
                # Measure-relative start time
                time = time
                barline_y = self.time_to_y(time)

                # Draw barline only if '1' is present in gridCountsEnabled; always draw measure number
                if 0 <= barline_y <= self.canvas.height_mm + self.editor_margin:
                    if any(c == 1 for c in g_count):
                        self.canvas.add_line(
                            x1_mm=self.editor_margin,
                            y1_mm=barline_y,
                            x2_mm=self.editor_margin + self.stave_width,
                            y2_mm=barline_y,
                            color=self.barline_color,
                            width_mm=self.score.properties.globalBasegrid.barlineWidthMm,
                            tags=['barline', f'barline_{int(time)}']
                        )

                    # Measure number at the start of the measure regardless of barline drawing
                    self.canvas.add_text(
                        x_mm=1,
                        y_mm=barline_y,
                        text=str(meas_idx + 1),
                        font_size_pt=16,
                        anchor='top_left',
                        color=self.score.properties.globalMeasureNumbering.color,
                        tags=['measurenumber', f'measurenumber_{int(time)}']
                    )

                # Draw grid lines at subdivision points defined in gridCountsEnabled
                beat = meas_length / num
                for i, count_idx in enumerate(g_count):
                    # Interpret: 1 = barline (handled above), >1 up to numerator = gridlines, 0 = ignored
                    if count_idx == 1 or count_idx == 0:
                        continue
                    if 1 < count_idx <= num:
                        grid_tick_position = time + (count_idx - 1) * beat
                        y1 = self.time_to_y(grid_tick_position)
                        if 0 <= y1 <= self.canvas.height_mm + self.editor_margin:
                            self.canvas.add_line(
                                x1_mm=self.editor_margin,
                                y1_mm=y1,
                                x2_mm=self.editor_margin + self.stave_width,
                                y2_mm=y1,
                                color=self.score.properties.globalBasegrid.gridlineColor,
                                width_mm=self.score.properties.globalBasegrid.gridlineWidthMm,
                                dash=True,
                                dash_pattern_mm=self.score.properties.globalBasegrid.gridlineDashPatternMm,
                                tags=['gridline', f'gridline_{int(grid_tick_position)}_{i}']
                            )

                # draw grid 3 based on the grid unit
                beat_count = self.grid_selector.get_grid_step()
                grid_step_cursor = 0.0
                color = self._color_lighter_hex(LIGHT_DARKER_HEX)
                is_color = True
                while OperatorThreshold().less(grid_step_cursor, meas_length):
                    start_tick = grid_step_cursor
                    end_tick = grid_step_cursor + beat_count

                    # Find first barline inside this measure slice (convert to measure-relative)
                    next_barline_in_range = None
                    time_threshold = .00001
                    for barline_pos_abs in barlines:
                        barline_pos_rel = barline_pos_abs - time  # make relative to this measure
                        # inside (start, end) with tolerance; allow boundary hit
                        if (barline_pos_rel > start_tick + time_threshold) and (barline_pos_rel < end_tick - time_threshold):
                            next_barline_in_range = barline_pos_rel
                            break
                        # handle exact boundary equality
                        if abs(barline_pos_rel - end_tick) <= time_threshold:
                            next_barline_in_range = barline_pos_rel
                            break

                    y1 = self.time_to_y(time + start_tick)
                    y2 = self.time_to_y(time + end_tick)

                    if next_barline_in_range is not None:
                        y2 = self.time_to_y(time + next_barline_in_range)

                    if 0 <= y1 <= self.canvas.height_mm + self.editor_margin and not is_color:
                        self.canvas.add_rectangle(
                            x1_mm=self.editor_margin,
                            y1_mm=y1,
                            x2_mm=self.editor_margin + self.stave_width,
                            y2_mm=y2,
                            fill=True,
                            fill_color=color,
                            outline=False,
                            tags=['cursor_grid']
                        )

                    if next_barline_in_range is not None:
                        break

                    is_color = not is_color
                    grid_step_cursor += beat_count
                
                # Move time cursor forward by one measure after finishing drawing
                time += meas_length
        
        # Draw final barline at the end of the score (double thickness)
        final_y_pos = self.time_to_y(time)
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

    def _color_lighter_hex(self, hex_color, factor=0.10) -> str:
        '''Return a lighter version of the given hex color without external helpers.
        
        Accepts `#RRGGBB` or `#RRGGBBAA`; alpha (if present) is ignored.
        Factor should be between 0.0 (no change) and 1.0 (white).
        '''
        if not isinstance(hex_color, str):
            return '#FFFFFF'
        s = hex_color.strip().lstrip('#')
        if len(s) not in (6, 8):
            return '#FFFFFF'
        try:
            r = int(s[0:2], 16)
            g = int(s[2:4], 16)
            b = int(s[4:6], 16)
        except ValueError:
            return '#FFFFFF'
        # Clamp factor
        factor = max(0.0, min(1.0, float(factor)))
        # Move each channel towards 255 by factor
        r = int(round(r + (255 - r) * factor))
        g = int(round(g + (255 - g) * factor))
        b = int(round(b + (255 - b) * factor))
        return f'#{r:02X}{g:02X}{b:02X}'
