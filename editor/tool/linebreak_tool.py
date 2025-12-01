"""
Line Break Tool - Add and remove line breaks.
"""

from editor.tool.base_tool import BaseTool
from file.lineBreak import LineBreak
from typing import Optional


class LineBreakTool(BaseTool):
    """Tool for adding and removing line breaks."""
    
    def __init__(self, editor):
        super().__init__(editor)
        self.edit_linebreak = None  # Line break being created/edited during drag
    
    @property
    def name(self) -> str:
        return "Line-break"
    
    @property
    def cursor(self) -> str:
        return 'crosshair'
    
    def on_activate(self):
        """Called when this tool becomes active."""
        super().on_activate()
    
    def on_deactivate(self):
        """Called when switching away from this tool."""
        super().on_deactivate()
        # Delete cursor drawing
        self.editor.canvas.delete_by_tag('cursor')
    
    def on_mouse_move(self, x: float, y: float) -> bool:
        """Handle mouse movement (hover, no buttons pressed)."""
        # Call parent's drag detection first
        if super().on_mouse_move(x, y):
            return True  # Parent is handling drag - stop here
        
        # Guard against startup race condition
        if not self.score:
            return False
        
        # Get time from mouse position
        pitch, time = self.get_pitch_and_time(x, y)
        
        # Clamp time to valid range
        score_length = self.editor.get_score_length_in_ticks()
        if time > score_length:
            time = score_length
        if time < 0:
            time = 0
        
        # Create cursor line break
        cursor = LineBreak(time=time)
        
        # Draw cursor
        self._draw_cursor(cursor, type='cursor')
        
        return True
    
    def on_left_press(self, x: float, y: float, item_id: Optional[int] = None) -> bool:
        """
        Called when left mouse button is pressed down.
        
        Used for starting line break creation or editing existing line breaks.
        """
        super().on_left_press(x, y)
        
        # Clear any existing selection
        if hasattr(self.editor, 'selection_manager'):
            self.editor.selection_manager.clear_selection()
        
        # Guard: Prevent creating a new line break if one is already being edited
        if self.edit_linebreak is not None:
            print(f"LineBreakTool: Ignoring duplicate on_left_press (linebreak {self.edit_linebreak.id} already being edited)")
            return True
        
        # Check if we clicked on an existing line break
        element, elem_type, stave_idx = self.get_element_at_position(x, y, element_types=['line_break'])
        
        if element and elem_type == 'line_break':
            # EDIT MODE: Start editing existing line break
            self.edit_linebreak = element
            
            # Redraw in 'edit' mode for visual feedback
            self.editor._draw_single_line_break(self.edit_linebreak, draw_mode='edit')
            
            print(f"LineBreakTool: Editing linebreak {element.id}")
        else:
            # CREATE MODE: Start creating new line break
            pitch, time = self.get_pitch_and_time(x, y)
            
            # Clamp time to valid range
            score_length = self.editor.get_score_length_in_ticks()
            if time > score_length:
                time = score_length
            if time < 0:
                time = 0
            
            # Create new line break using auto-generated factory method
            self.edit_linebreak = self.score.new_linebreak(time=time)
            
            # Draw in 'edit' mode
            self.editor._draw_single_line_break(self.edit_linebreak, draw_mode='edit')
            
            print(f"LineBreakTool: Creating new linebreak {self.edit_linebreak.id} at time={time}")
        
        return True
    
    def on_drag(self, x: float, y: float, start_x: float, start_y: float) -> bool:
        """Called continuously while dragging WITH button pressed."""
        if self.edit_linebreak is None:
            return False
        
        # Update line break position
        pitch, time = self.get_pitch_and_time(x, y)
        
        # Clamp time to valid range
        score_length = self.editor.get_score_length_in_ticks()
        if time > score_length:
            time = score_length
        if time < 0:
            time = 0
        
        # Update line break
        self.edit_linebreak.time = time
        
        # Redraw with updated position
        self.editor._draw_single_line_break(self.edit_linebreak, draw_mode='edit')
        
        return True
    
    def on_drag_end(self, x: float, y: float) -> bool:
        """Called when drag finishes (button released after dragging)."""
        if self.edit_linebreak is None:
            return False
        
        # Finalize line break position
        pitch, time = self.get_pitch_and_time(x, y)
        
        # Clamp time to valid range
        score_length = self.editor.get_score_length_in_ticks()
        if time > score_length:
            time = score_length
        if time < 0:
            time = 0
        
        # Update line break
        self.edit_linebreak.time = time
        
        # Clear edit state
        self.edit_linebreak = None
        
        # Redraw everything
        self.editor.redraw_pianoroll()
        self.editor.on_modified()
        
        print(f"LineBreakTool: Finalized linebreak")
        
        return True
    
    def on_left_unpress(self, x: float, y: float) -> bool:
        """Called when left mouse button is released without having dragged."""
        if self.edit_linebreak is None:
            return False
        
        # Clear edit state (line break was created on press)
        self.edit_linebreak = None
        
        # Redraw everything
        self.editor.redraw_pianoroll()
        self.editor.on_modified()
        
        return True
    
    def on_right_click(self, x: float, y: float) -> bool:
        """Called when right mouse button is clicked (without drag)."""
        # Find line break at position
        element, elem_type, stave_idx = self.get_element_at_position(x, y, element_types=['line_break'])
        
        if element and elem_type == 'line_break':
            # Delete the line break
            self.score.lineBreak.remove(element)
            
            # Redraw everything
            self.editor.redraw_pianoroll()
            self.editor.on_modified()
            
            print(f"LineBreakTool: Deleted linebreak {element.id}")
            return True
        
        return False
    
    def _draw_cursor(self, linebreak: LineBreak, type: str = 'cursor') -> None:
        """Draw cursor line break preview."""
        if not self.score:
            return
        
        # Draw using the drawer mixin
        self.editor._draw_single_line_break(linebreak, draw_mode=type)
