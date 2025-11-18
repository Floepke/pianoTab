
"""
Count Line Tool - Add and remove count lines.
"""

from editor.tool.base_tool import BaseTool
# from file.countLine import CountLine


class CountLineTool(BaseTool):
    """Tool for adding and removing count lines."""
    
    @property
    def name(self) -> str:
        return "Count-line"
    
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
        
        # TODO: Show hover preview (only when not dragging)
        return False
    
    def on_left_press(self, x: float, y: float) -> bool:
        """
        Called when left mouse button is pressed down.
        
        Used for starting count line creation or editing existing count lines.
        """
        super().on_left_press(x, y)
        # TODO: Handle mouse down (before knowing if it's click or drag)
        return False
    
    def on_left_click(self, x: float, y: float) -> bool:
        """Called when left mouse button is clicked (pressed and released without dragging)."""
        # TODO: Add a count line at the clicked position
        print(f"CountLineTool: Add count line at ({x}, {y})")
        return True
    
    def on_left_unpress(self, x: float, y: float) -> bool:
        """Called when left mouse button is released without having dragged."""
        # TODO: Finalize count line creation on click (no drag)
        return False
    
    def on_left_release(self, x: float, y: float) -> bool:
        """Called when left mouse button is released (after drag or click)."""
        # Let parent handle the drag_end vs unpress logic
        result = super().on_left_release(x, y)
        return result
    
    def on_right_click(self, x: float, y: float) -> bool:
        """Called when right mouse button is clicked (without drag)."""
        # TODO: Remove count line at the clicked position
        print(f"CountLineTool: Remove count line at ({x}, {y})")
        return False  # Return False until implemented - allows selection clearing
    
    def on_double_click(self, x: float, y: float) -> bool:
        """Called when mouse is double-clicked."""
        # TODO: Edit count line properties on double-click
        return False
    
    def on_drag_start(self, x: float, y: float, start_x: float, start_y: float) -> bool:
        """Called when drag first starts (mouse moved beyond threshold with button down)."""
        # TODO: Initialize drag operation
        return False
    
    def on_drag(self, x: float, y: float, start_x: float, start_y: float) -> bool:
        """Called continuously while dragging WITH button pressed."""
        # TODO: Update drag preview
        return False
    
    def on_drag_end(self, x: float, y: float) -> bool:
        """Called when drag finishes (button released after dragging)."""
        # TODO: Finalize drag operation
        return False
