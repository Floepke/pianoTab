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
    
    def on_left_press(self, x: float, y: float) -> bool:
        """Start defining a slur."""
        self._slur_start_pos = (x, y)
        print(f"SlurTool: Start slur at ({x}, {y})")
        return super().on_left_press(x, y)
    
    def on_drag(self, x: float, y: float, start_x: float, start_y: float) -> bool:
        """Show slur preview while dragging."""
        print(f"SlurTool: Preview slur from ({start_x}, {start_y}) to ({x}, {y})")
        
        # TODO: Draw temporary slur preview
        
        return True
    
    def on_drag_end(self, x: float, y: float) -> bool:
        """Finalize slur creation."""
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
    
    def on_right_click(self, x: float, y: float) -> bool:
        """Remove slur at the clicked position."""
        print(f"SlurTool: Remove slur at ({x}, {y})")
        
        # TODO: Implement slur removal
        # slur = self.get_element_at_position(x, y, element_types=[Slur])
        # if slur:
        #     self.score.remove_slur(slur)
        #     self.refresh_canvas()
        #     return True
        
        return True
    
    def on_deactivate(self):
        """Clean up when switching away from slur tool."""
        super().on_deactivate()
        self._slur_start_pos = None
