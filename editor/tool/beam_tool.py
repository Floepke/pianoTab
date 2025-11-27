"""
Beam Tool - Add, edit, and remove beams.
"""

from editor.tool.base_tool import BaseTool
from file.beam import Beam


class BeamTool(BaseTool):
    """Tool for adding and editing beam custom grouping."""
    
    @property
    def name(self) -> str:
        return "Beam"
    
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
        # Call parent's drag detection first
        if super().on_mouse_move(x, y):
            return True  # Parent is handling drag - stop here
        
        # Guard against startup race condition (mouse moves before file loaded)
        if not self.score:
            return False
        
        # draw the cursor
        pitch, time = self.get_pitch_and_time(x, y)
        duration = 0
        
        if pitch < 40: hand = '<'
        else: hand = '>'
        
        cursor = Beam(time=time, duration=duration, hand=hand)
        
        # redraw cursor
        self._draw_cursor(cursor, type='cursor')
        
        # TODO: Show hover preview (only when not dragging)
        return False
    
    def on_left_press(self, x: float, y: float) -> bool:
        """
        Called when left mouse button is pressed down.
        
        Used for starting beam creation or editing existing beams.
        """
        super().on_left_press(x, y)
        # TODO: Handle mouse down (before knowing if it's click or drag)
        return False
    
    def on_left_click(self, x: float, y: float) -> bool:
        """Called when left mouse button is clicked (pressed and released without dragging)."""
        # TODO: Add a new beam at the clicked position
        print(f"BeamTool: Add beam at ({x}, {y})")
        return True
    
    def on_left_unpress(self, x: float, y: float) -> bool:
        """Called when left mouse button is released without having dragged."""
        # TODO: Finalize beam creation on click (no drag)
        return False
    
    def on_left_release(self, x: float, y: float) -> bool:
        """Called when left mouse button is released (after drag or click)."""
        # Let parent handle the drag_end vs unpress logic
        result = super().on_left_release(x, y)
        return result
    
    def on_right_click(self, x: float, y: float) -> bool:
        """Called when right mouse button is clicked (without drag)."""
        # TODO: Remove beam at the clicked position
        print(f"BeamTool: Remove beam at ({x}, {y})")
        return False  # Return False until implemented - allows selection clearing
    
    def on_double_click(self, x: float, y: float) -> bool:
        """Called when mouse is double-clicked."""
        # TODO: Edit beam properties on double-click
        return False
    
    def on_drag_start(self, x: float, y: float, start_x: float, start_y: float) -> bool:
        """Called when drag first starts (mouse moved beyond threshold with button down)."""
        # TODO: Initialize drag operation
        return False
    
    def on_drag(self, x: float, y: float, start_x: float, start_y: float) -> bool:
        """Called continuously while dragging WITH button pressed."""
        super().on_drag(x, y, start_x, start_y)

        ...

        return False
    
    def on_drag_end(self, x: float, y: float) -> bool:
        """Called when drag finishes (button released after dragging)."""
        # TODO: Finalize drag operation
        return False
    
    def _draw_cursor(self, cursor: Beam, type: str = 'cursor') -> None:
        """Draw the beam cursor on the canvas.

        Args:
            cursor: The Beam object representing the cursor.
            type: Type of cursor ('cursor' or 'preview').
        """
        self.editor._draw_single_beam(0, cursor)