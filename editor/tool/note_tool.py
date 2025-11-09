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
    
    def on_activate(self):
        """Called when this tool becomes active."""
        super().on_activate()
        # TODO: Initialize tool-specific state
        pass
    
    def on_deactivate(self):
        """Called when switching away from this tool."""
        super().on_deactivate()
        # TODO: Clean up tool-specific state
        pass
    
    def on_mouse_move(self, x: float, y: float) -> bool:
        """Handle mouse movement (hover, no buttons pressed)."""
        # Call parent first - handles time cursor and drag detection
        if super().on_mouse_move(x, y):
            return True  # Parent is handling drag - stop here
        
        pitch, time = self.get_pitch_and_time(x, y)
        
        
        
        return False
    
    def on_left_press(self, x: float, y: float) -> bool:
        """Called when left mouse button is pressed down."""
        super().on_left_press(x, y)
        # TODO: Handle mouse down (before knowing if it's click or drag)
        return False
    
    def on_left_click(self, x: float, y: float) -> bool:
        """Called when left mouse button is clicked (pressed and released without dragging)."""
        # TODO: Add a new note at the clicked position
        print(f"NoteTool: Add note at ({x}, {y})")
        
        # Example implementation:
        # tick = self.editor.x_to_tick(x)
        # key, stave = self.editor.y_to_key_and_stave(y)
        # note = Note(tick=tick, key=key, ...)
        # self.score.add_note(note)
        # self.refresh_canvas()
        
        return True
    
    def on_left_release(self, x: float, y: float) -> bool:
        """Called when left mouse button is released."""
        super().on_left_release(x, y)
        # TODO: Handle mouse up (after click or drag)
        return False
    
    def on_right_click(self, x: float, y: float) -> bool:
        """Called when right mouse button is clicked."""
        # TODO: Remove note at the clicked position
        print(f"NoteTool: Remove note at ({x}, {y})")
        
        # Example implementation:
        # note = self.get_element_at_position(x, y, element_types=[Note])
        # if note:
        #     self.score.remove_note(note)
        #     self.refresh_canvas()
        #     return True
        
        return True
    
    def on_double_click(self, x: float, y: float) -> bool:
        """Called when mouse is double-clicked."""
        # TODO: Edit note properties on double-click
        print(f"NoteTool: Edit note at ({x}, {y})")
        return False
    
    def on_drag_start(self, x: float, y: float, start_x: float, start_y: float) -> bool:
        """Called when drag first starts (mouse moved beyond threshold with button down)."""
        # TODO: Initialize drag operation
        print(f"NoteTool: Start drag from ({start_x}, {start_y}) to ({x}, {y})")
        return False
    
    def on_drag(self, x: float, y: float, start_x: float, start_y: float) -> bool:
        """Called continuously while dragging."""
        # TODO: Update drag preview
        print(f"NoteTool: Dragging from ({start_x}, {start_y}) to ({x}, {y})")
        return False
    
    def on_drag_end(self, x: float, y: float) -> bool:
        """Called when drag finishes (button released after dragging)."""
        # TODO: Finalize drag operation
        print(f"NoteTool: End drag at ({x}, {y})")
        return False
    
    def _draw_note_cursor(self, x: float, y: float):
        """Draw a note cursor at the given position."""
        ...
