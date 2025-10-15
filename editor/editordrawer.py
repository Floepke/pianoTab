from utils.canvas_tkinter2pymupdf import PdfCanvas
from file.SCORE import SCORE
from gui.grid_selector import GridSelector
from utils.calculations import (get_editor_height_in_pixels,
                                get_editor_barline_positions,
                                get_editor_gridline_positions,
                                get_score_length_in_ticks,
                                get_ticks2pixels)
from utils.CONSTANT import (PHYSICAL_SEMITONE_POSITIONS, BE)
from logger import log

class EditorDrawer:
    def __init__(self, canvas: PdfCanvas, score: SCORE, grid_selector: GridSelector):
        self.editor_canvas = canvas
        self.score = score
        self.grid_selector = grid_selector

        # editor dimensions
        self.editor_width = self.editor_canvas.winfo_width()
        self.editor_height_pixels = get_editor_height_in_pixels(self.score)
        self.editor_margin = self.editor_width / 6

        # Initial drawing
        self.update()
        
    def update(self):
        self.editor_canvas.delete("all")
        
        # Set page dimensions
        self.editor_width = self.editor_canvas.winfo_width()
        self.editor_height_pixels = get_editor_height_in_pixels(self.score)
        
        # update margin based on new width
        self.editor_margin = self.editor_width / 6

        self.editor_canvas.set_page_dimensions(self.editor_width, 
                                               self.editor_height_pixels + (2 * self.editor_margin))
        
        self.draw_stave()
        self.draw_barlines_grid_timesignatureIndicator()

        # Get the bounding box of all items
        bbox = self.editor_canvas.bbox("all")
        if bbox:
            x_min, y_min, x_max, y_max = bbox
            # Apply margin only on the Y-axis
            y_min -= self.editor_margin
            y_max += self.editor_margin
            # Set the scroll region with adjusted Y values
            self.editor_canvas.configure(scrollregion=(x_min, y_min, x_max, y_max))

    def draw_stave(self):
        '''Draw the stave lines and grid on the editor canvas.'''
        
        # Calculate dimensions
        stave_width = self.editor_width - (2 * self.editor_margin)
        stave_height = self.editor_height_pixels
        x = self.editor_margin
        y = self.editor_margin

        # get colors from file:
        stave_three_color = self.score.properties.globalStave.threeLineColor
        stave_two_color = self.score.properties.globalStave.twoLineColor
        stave_clef_color = self.score.properties.globalStave.clefColor
        stave_dash_pattern = self.score.properties.globalStave.clefDashPattern
        
        # Draw the stave:
        visual_semitone_positions = PHYSICAL_SEMITONE_POSITIONS - 5 # 5 positions are not drawn (below A0 and above C8)
        semitone_width = stave_width / visual_semitone_positions
        key = 2
        for k in range(1, 88):
            if k in BE:
                x += semitone_width
            key_class = key % 12
            if key_class in [2, 5, 7, 10, 0]:  # A#, C#, D#, F#, G#
                # Set width 4 for A#, F#, G#, else 2
                if key_class in [2, 10, 0]:  # A#, F#, G#
                    w = 2
                    c = stave_three_color
                else:
                    w = 1
                if key_class in [5, 7] and not key in [41, 43]:  # C#, D#
                    c = stave_two_color
                if key in [41, 43]:  # F#, G# (clef lines)
                    c = stave_clef_color
                self.editor_canvas.add_line(x, y, x, y + stave_height, 
                                            color=c,
                                            width=w,
                                            dash_pattern=stave_dash_pattern if key in [41, 43] else None)
            key += 1
            x += semitone_width
            
    def draw_barlines_grid_timesignatureIndicator(self):
        '''Draw the grid lines on the editor canvas according to the file settings.'''
        # get properties from file:
        barline_color = self.score.properties.globalBasegrid.barlineColor
        barline_width = self.score.properties.globalBasegrid.barlineWidth
        gridline_color = self.score.properties.globalBasegrid.gridlineColor
        gridline_width = self.score.properties.globalBasegrid.gridlineWidth
        gridline_dash_pattern = self.score.properties.globalBasegrid.gridLineDashPattern

        # Calculate dimensions
        stave_width = self.editor_width - (2 * self.editor_margin)

        # horizontal grid lines:
        for grid in self.score.baseGrid:
            # timesignature indicator:
            numerator = grid.numerator
            denominator = grid.denominator #TODO

            # barlines + numbering:
            bl_pos = get_editor_barline_positions(self.score)
            for y in bl_pos:
                self.editor_canvas.add_line(self.editor_margin, self.editor_margin + y, 
                                            self.editor_margin + stave_width, self.editor_margin + y,
                                            color=barline_color,
                                            width=barline_width)
                
                measure_number = bl_pos.index(y) + 1
                self.editor_canvas.add_text(5, self.editor_margin + y + 5,
                                            text=str(measure_number),
                                            size=24,
                                            color=barline_color,
                                            anchor='nw',
                                            font='Courier New')
            
            # calculate gridline positions:
            gr_pos = get_editor_gridline_positions(self.score)

            # draw gridlines:
            for y in gr_pos:
                self.editor_canvas.add_line(self.editor_margin, self.editor_margin + y, 
                                            self.editor_margin + stave_width, self.editor_margin + y,
                                            color=gridline_color,
                                            width=gridline_width,
                                            dash_pattern=gridline_dash_pattern)
                log(gridline_dash_pattern)

        # draw endbarline:
        last_y_position = get_ticks2pixels(get_score_length_in_ticks(self.score), self.score)
        self.editor_canvas.add_line(self.editor_margin, self.editor_margin + last_y_position, 
                                    self.editor_margin + stave_width, self.editor_margin + last_y_position,
                                    color=barline_color,
                                    width=barline_width * 2)  # end barline is thicker

