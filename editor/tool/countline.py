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
    
    def on_left_click(self, x: float, y: float) -> bool:
        """Add a count line at the clicked position."""
        print(f"CountLineTool: Add count line at ({x}, {y})")
        
        # TODO: Implement count line creation
        # count_line = CountLine(...)
        # self.score.add_count_line(count_line)
        # self.refresh_canvas()
        
        return True
    
    def on_right_click(self, x: float, y: float) -> bool:
        """Remove count line at the clicked position."""
        print(f"CountLineTool: Remove count line at ({x}, {y})")
        
        # TODO: Implement count line removal
        # count_line = self.get_element_at_position(x, y, element_types=[CountLine])
        # if count_line:
        #     self.score.remove_count_line(count_line)
        #     self.refresh_canvas()
        #     return True
        
        return True
