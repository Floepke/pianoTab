"""
Note Tool - Add, edit, and remove notes.
"""

from editor.tool.base_tool import BaseTool
# from file.note import Note


class NoteTool(BaseTool):
    """Tool for adding and editing notes."""
    
    @property
    def name(self) -> str:
        return "Note"
    
    @property
    def cursor(self) -> str:
        return 'crosshair'
    
    def on_left_click(self, x: float, y: float) -> bool:
        """Add a new note at the clicked position."""
        # TODO: Convert x, y to score coordinates (tick, key, stave)
        # TODO: Create and add note to score
        
        print(f"NoteTool: Add note at ({x}, {y})")
        
        # Example implementation:
        # tick = self.editor.x_to_tick(x)
        # key, stave = self.editor.y_to_key_and_stave(y)
        # note = Note(tick=tick, key=key, ...)
        # self.score.add_note(note)
        # self.refresh_canvas()
        
        return True
    
    def on_right_click(self, x: float, y: float) -> bool:
        """Remove note at the clicked position."""
        # TODO: Find note at position
        # TODO: Remove from score
        
        print(f"NoteTool: Remove note at ({x}, {y})")
        
        # Example implementation:
        # note = self.get_element_at_position(x, y, element_types=[Note])
        # if note:
        #     self.score.remove_note(note)
        #     self.refresh_canvas()
        #     return True
        
        return True
    
    def on_drag(self, x: float, y: float, start_x: float, start_y: float) -> bool:
        """Preview note while dragging."""
        # TODO: Could show a preview of the note being placed
        return False
