"""
Line Break Tool - Add and remove line breaks.
"""

from editor.tool.base_tool import BaseTool
# from file.lineBreak import LineBreak


class LineBreakTool(BaseTool):
    """Tool for adding and removing line breaks."""
    
    @property
    def name(self) -> str:
        return "Line-break"
    
    @property
    def cursor(self) -> str:
        return 'crosshair'
    
    def on_left_click(self, x: float, y: float) -> bool:
        """Add a line break at the clicked position."""
        print(f"LineBreakTool: Add line break at ({x}, {y})")
        
        # TODO: Implement line break creation
        # line_break = LineBreak(...)
        # self.score.add_line_break(line_break)
        # self.refresh_canvas()
        
        return True
    
    def on_right_click(self, x: float, y: float) -> bool:
        """Remove line break at the clicked position."""
        print(f"LineBreakTool: Remove line break at ({x}, {y})")
        
        # TODO: Implement line break removal
        # line_break = self.get_element_at_position(x, y, element_types=[LineBreak])
        # if line_break:
        #     self.score.remove_line_break(line_break)
        #     self.refresh_canvas()
        #     return True
        
        return True
