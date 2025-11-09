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
    
    def on_left_click(self, x: float, y: float) -> bool:
        """Add a new tempo marking at the clicked position."""
        print(f"TempoTool: Add tempo at ({x}, {y})")
        
        # TODO: Implement tempo creation (probably needs a dialog for BPM input)
        # tempo = Tempo(x=x, y=y, bpm=120)
        # self.score.add_tempo(tempo)
        # self.refresh_canvas()
        
        return True
    
    def on_right_click(self, x: float, y: float) -> bool:
        """Remove tempo marking at the clicked position."""
        print(f"TempoTool: Remove tempo at ({x}, {y})")
        
        # TODO: Implement tempo removal
        # tempo = self.get_element_at_position(x, y, element_types=[Tempo])
        # if tempo:
        #     self.score.remove_tempo(tempo)
        #     self.refresh_canvas()
        #     return True
        
        return True
    
    def on_double_click(self, x: float, y: float) -> bool:
        """Edit existing tempo on double-click."""
        print(f"TempoTool: Edit tempo at ({x}, {y})")
        
        # TODO: Open tempo editing dialog
        # tempo = self.get_element_at_position(x, y, element_types=[Tempo])
        # if tempo:
        #     self._open_tempo_editor(tempo)
        #     return True
        
        return True
