from utils.canvas_tkinter2pymupdf import PdfCanvas
from file.SCORE import SCORE
from utils.calculations import calc_editor_height_in_pixels

class EditorDrawer:
    def __init__(self, canvas: PdfCanvas, score: SCORE):
        self.editor_canvas = canvas
        self.score = score

        # editor dimensions
        self.editor_width = self.editor_canvas.winfo_width()
        self.editor_height = calc_editor_height_in_pixels(self.score)
        self.editor_margin = self.editor_width / 6

        # Initial drawing
        self.update()
        
    def update(self):
        self.editor_canvas.delete("all")
        
        # Set page dimensions
        self.editor_width = self.editor_canvas.winfo_width()
        self.editor_height = calc_editor_height_in_pixels(self.score)
        
        # update margin based on new width
        self.editor_margin = self.editor_width / 6

        self.editor_canvas.set_page_dimensions(self.editor_width, self.editor_height + (2 * self.editor_margin))
        self.draw_stave()

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
        '''Draw the stave lines on the editor canvas.'''
        
        #