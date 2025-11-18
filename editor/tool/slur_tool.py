"""
Slur Tool - Add, edit, and remove slurs.
"""

from editor.tool.base_tool import BaseTool
# from file.slur import Slur


class SlurTool(BaseTool):
    """Tool for adding and editing slurs."""
    
    def __init__(self, editor):
        super().__init__(editor)
        self._slur_start_pos = None
    
    @property
    def name(self) -> str:
        return "Slur"
    
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
        self._slur_start_pos = None
    
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
        
        Used for starting slur creation or editing existing slurs.
        """
        super().on_left_press(x, y)
        self._slur_start_pos = (x, y)
        print(f"SlurTool: Start slur at ({x}, {y})")
        return False
    
    def on_left_click(self, x: float, y: float) -> bool:
        """Called when left mouse button is clicked (pressed and released without dragging)."""
        # TODO: Handle click (if needed for slurs)
        return False
    
    def on_left_unpress(self, x: float, y: float) -> bool:
        """Called when left mouse button is released without having dragged."""
        # TODO: Finalize slur on click (no drag)
        return False
    
    def on_left_release(self, x: float, y: float) -> bool:
        """Called when left mouse button is released (after drag or click)."""
        # Let parent handle the drag_end vs unpress logic
        result = super().on_left_release(x, y)
        return result
    
    def on_right_click(self, x: float, y: float) -> bool:
        """Called when right mouse button is clicked (without drag)."""
        # TODO: Remove slur at the clicked position
        print(f"SlurTool: Remove slur at ({x}, {y})")
        return False  # Return False until implemented - allows selection clearing
    
    def on_double_click(self, x: float, y: float) -> bool:
        """Called when mouse is double-clicked."""
        # TODO: Edit slur properties on double-click
        return False
    
    def on_drag_start(self, x: float, y: float, start_x: float, start_y: float) -> bool:
        """Called when drag first starts (mouse moved beyond threshold with button down)."""
        # TODO: Initialize slur preview
        return False
    
    def on_drag(self, x: float, y: float, start_x: float, start_y: float) -> bool:
        """Called continuously while dragging WITH button pressed."""
        # TODO: Show slur preview while dragging
        print(f"SlurTool: Preview slur from ({start_x}, {start_y}) to ({x}, {y})")
        return True
    
    def on_drag_end(self, x: float, y: float) -> bool:
        """Called when drag finishes (button released after dragging)."""
        if self._slur_start_pos:
            start_x, start_y = self._slur_start_pos
            print(f"SlurTool: Create slur from ({start_x}, {start_y}) to ({x}, {y})")
            
            # TODO: Create slur between start and end positions
            # slur = Slur(start_x=start_x, start_y=start_y, end_x=x, end_y=y)
            # self.score.add_slur(slur)
            # self.refresh_canvas()
            
            self._slur_start_pos = None
            return True
        
        return False
