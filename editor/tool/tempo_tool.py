"""
Tempo Tool - Add, edit, and remove tempo markings.
"""

from editor.tool.base_tool import BaseTool
# from file.tempo import Tempo


class TempoTool(BaseTool):
    """Tool for adding and editing tempo markings."""
    
    @property
    def name(self) -> str:
        return "Tempo"
    
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
        """Called when left mouse button is pressed down."""
        super().on_left_press(x, y)
        # TODO: Handle mouse down (before knowing if it's click or drag)
        return False
    
    def on_left_click(self, x: float, y: float) -> bool:
        """Called when left mouse button is clicked (pressed and released without dragging)."""
        # TODO: Add a new tempo marking (probably needs a dialog for BPM input)
        print(f"TempoTool: Add tempo at ({x}, {y})")
        return True
    
    def on_left_release(self, x: float, y: float) -> bool:
        """Called when left mouse button is released."""
        super().on_left_release(x, y)
        # TODO: Handle mouse up (after click or drag)
        return False
    
    def on_right_click(self, x: float, y: float) -> bool:
        """Called when right mouse button is clicked."""
        # TODO: Remove tempo marking at the clicked position
        print(f"TempoTool: Remove tempo at ({x}, {y})")
        return False  # Return False until implemented - allows selection clearing
    
    def on_double_click(self, x: float, y: float) -> bool:
        """Called when mouse is double-clicked."""
        # TODO: Edit existing tempo on double-click (open tempo editing dialog)
        print(f"TempoTool: Edit tempo at ({x}, {y})")
        return True
    
    def on_drag_start(self, x: float, y: float, start_x: float, start_y: float) -> bool:
        """Called when drag first starts (mouse moved beyond threshold with button down)."""
        # TODO: Initialize drag operation
        return False
    
    def on_drag(self, x: float, y: float, start_x: float, start_y: float) -> bool:
        """Called continuously while dragging."""
        # TODO: Update drag preview
        return False
    
    def on_drag_end(self, x: float, y: float) -> bool:
        """Called when drag finishes (button released after dragging)."""
        # TODO: Finalize drag operation
        return False
