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
        # Create a trigger that coalesces multiple render requests into one
        self._render_trigger = Clock.create_trigger(self._render_next_frame, 0)
        # Optional callback when model mutates (for dirty tracking)
        self.on_modified: Optional[Callable[[], None]] = None

    # View -> Controller (pointer/tool)
    def on_pointer(self, x: float, y: float, action: str, tool: str, **kw):
        # Example: place note on click
        if action == 'down' and tool == 'note':
            time, pitch = self._hit_to_time_pitch(x, y)
            self.add_note(time, pitch)

    # Controller -> Model
    def add_note(self, time: float, pitch: int):
        self.score.new_note(time=time, pitch=pitch)
        self.render_async()
        self._notify_modified()

    def set_property(self, path: str, value: Any):
        # e.g. "properties.globalNote.color"
        obj = self.score
        parts = path.split('.')
        for p in parts[:-1]:
            obj = getattr(obj, p)
        setattr(obj, parts[-1], value)
        self.render_async()
        self._notify_modified()

    # File ops (called from menu callbacks)
    def load_score(self, score: SCORE):
        """Replace current score with a loaded one (e.g., from JSON)."""
        self.score = score
        self.render_async()

    def new_score(self):
        """Replace current score with a fresh empty score."""
        self.score = SCORE()  # Auto-attaches references via @model_validator
        self.render_async()
        self._notify_modified()

    # Controller -> View
    def render(self):
        self.editor_canvas.draw_score(self.score)

    def render_async(self):
        """Schedule render on next frame; coalesces multiple calls."""
        self._render_trigger()

    def _render_next_frame(self, dt):
        """Internal callback for Clock trigger."""
        self.render()

    def _notify_modified(self):
        try:
            if self.on_modified:
                self.on_modified()
        except Exception:
            pass

    # Helpers
    def _hit_to_time_pitch(self, x: float, y: float) -> Tuple[float, int]:
        # Map view coords to model units; placeholder
        time = self._x_to_time(x)
        pitch = self._y_to_pitch(y)
        return time, pitch

    def _x_to_time(self, x: float) -> float:
        return float(x)  # replace with grid mapping

    def _y_to_pitch(self, y: float) -> int:
        return max(1, min(88, int(y)))  # replace with stave mapping