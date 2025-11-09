"""
Beam Tool - Add, edit, and remove beams.
"""

from editor.tool.base_tool import BaseTool
# from file.beam import Beam


class BeamTool(BaseTool):
    """Tool for adding and editing beams."""
    
    @property
    def name(self) -> str:
        return "Beam"
    
    @property
    def cursor(self) -> str:
        return 'crosshair'
    
    def on_left_click(self, x: float, y: float) -> bool:
        """Add a new beam at the clicked position."""
        print(f"BeamTool: Add beam at ({x}, {y})")
        
        # TODO: Implement beam creation
        # beam = Beam(...)
        # self.score.add_beam(beam)
        # self.refresh_canvas()
        
        return True
    
    def on_right_click(self, x: float, y: float) -> bool:
        """Remove beam at the clicked position."""
        print(f"BeamTool: Remove beam at ({x}, {y})")
        
        # TODO: Implement beam removal
        # beam = self.get_element_at_position(x, y, element_types=[Beam])
        # if beam:
        #     self.score.remove_beam(beam)
        #     self.refresh_canvas()
        #     return True
        
        return True
