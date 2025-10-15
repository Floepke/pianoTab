from editor.editordrawer import EditorDrawer
from file.SCORE import SCORE
from utils.canvas_tkinter2pymupdf import PdfCanvas

class Editor:
    def __init__(self, canvas: PdfCanvas, score: SCORE):
        self.canvas = canvas
        self.canvas.disable_pdf_mode()  # Disable PDF mode for editor
        self.score = score
        self.drawer = EditorDrawer(canvas, score)

        # Set up the scroll region (adjust as needed)
        self.canvas.configure(scrollregion=(0, 0, self.canvas.winfo_width(), self.canvas.winfo_height()))

        # Bind mouse wheel for vertical scrolling
        self.canvas.bind('<MouseWheel>', self._on_mouse_wheel)  # Windows/macOS
        self.canvas.bind('<Button-4>', self._on_mouse_wheel)    # Linux scroll up
        self.canvas.bind('<Button-5>', self._on_mouse_wheel)    # Linux scroll down

    def _on_mouse_wheel(self, event):
        '''Handle mouse wheel scrolling.'''
        if event.num == 4 or event.delta > 0:  # Scroll up
            self.canvas.yview_scroll(-1, 'units')
        elif event.num == 5 or event.delta < 0:  # Scroll down
            self.canvas.yview_scroll(1, 'units')