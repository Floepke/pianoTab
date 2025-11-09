"""
Text Tool - Add, edit, and remove text annotations.
"""

from editor.tool.base_tool import BaseTool
# from file.text import Text


class TextTool(BaseTool):
    """Tool for adding and editing text annotations."""
    
    @property
    def name(self) -> str:
        return "Text"
    
    @property
    def cursor(self) -> str:
        return 'ibeam'
    
    def on_left_click(self, x: float, y: float) -> bool:
        """Add new text at the clicked position."""
        print(f"TextTool: Add text at ({x}, {y})")
        
        # TODO: Implement text creation (probably needs a dialog for input)
        # text = Text(x=x, y=y, content="New Text")
        # self.score.add_text(text)
        # self.refresh_canvas()
        
        return True
    
    def on_right_click(self, x: float, y: float) -> bool:
        """Remove text at the clicked position."""
        print(f"TextTool: Remove text at ({x}, {y})")
        
        # TODO: Implement text removal
        # text = self.get_element_at_position(x, y, element_types=[Text])
        # if text:
        #     self.score.remove_text(text)
        #     self.refresh_canvas()
        #     return True
        
        return True
    
    def on_double_click(self, x: float, y: float) -> bool:
        """Edit existing text on double-click."""
        print(f"TextTool: Edit text at ({x}, {y})")
        
        # TODO: Open text editing dialog
        # text = self.get_element_at_position(x, y, element_types=[Text])
        # if text:
        #     self._open_text_editor(text)
        #     return True
        
        return True
