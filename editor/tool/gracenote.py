"""
Grace Note Tool - Add, edit, and remove grace notes.
"""

from editor.tool.base_tool import BaseTool
# from file.graceNote import GraceNote


class GraceNoteTool(BaseTool):
    """Tool for adding and editing grace notes."""
    
    @property
    def name(self) -> str:
        return "Grace-note"
    
    @property
    def cursor(self) -> str:
        return 'crosshair'
    
    def on_left_click(self, x: float, y: float) -> bool:
        """Add a new grace note at the clicked position."""
        print(f"GraceNoteTool: Add grace note at ({x}, {y})")
        
        # TODO: Implement grace note creation
        # grace_note = GraceNote(...)
        # self.score.add_grace_note(grace_note)
        # self.refresh_canvas()
        
        return True
    
    def on_right_click(self, x: float, y: float) -> bool:
        """Remove grace note at the clicked position."""
        print(f"GraceNoteTool: Remove grace note at ({x}, {y})")
        
        # TODO: Implement grace note removal
        # grace_note = self.get_element_at_position(x, y, element_types=[GraceNote])
        # if grace_note:
        #     self.score.remove_grace_note(grace_note)
        #     self.refresh_canvas()
        #     return True
        
        return True
