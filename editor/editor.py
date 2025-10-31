from __future__ import annotations
from typing import Optional, Dict, Any, Tuple, Callable
from kivy.clock import Clock

from file.SCORE import SCORE
from utils.canvas import Canvas

class Editor:
    """
    Controller: mediates between View (Canvas/widgets) and Model (SCORE).
    Owns no drawing; instructs Canvas to render the SCORE.
    Owns the SCORE object - the single source of truth for the musical data.
    """
    def __init__(self, editor_canvas: Canvas, score: Optional[SCORE] = None):
        self.editor_canvas: Canvas = editor_canvas
        self.score: SCORE = score if score is not None else SCORE()
