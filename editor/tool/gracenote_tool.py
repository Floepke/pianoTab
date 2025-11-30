"""
Grace Note Tool - Add, edit, and remove grace notes.
"""

from editor.tool.base_tool import BaseTool
from file.graceNote import GraceNote
from typing import Optional


class GraceNoteTool(BaseTool):
    """Tool for adding and editing grace notes."""
    
    def __init__(self, editor):
        super().__init__(editor)
        self.edit_gracenote = None  # Grace note being created/edited during drag
        self.edit_stave_idx = None  # Stave index of grace note being edited
    
    @property
    def name(self) -> str:
        return "Grace-note"
    
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
        
        # Get pitch and time from mouse position
        pitch, time = self.get_pitch_and_time(x, y)
        
        # Clamp time to valid range
        score_length = self.editor.get_score_length_in_ticks()
        if time > score_length:
            time = score_length
        if time < 0:
            time = 0
        
        # Create cursor grace note
        cursor = GraceNote(pitch=pitch, time=time)
        
        # Draw cursor
        self._draw_cursor(cursor, type='cursor')
        
        return True
    
    def on_left_press(self, x: float, y: float, item_id: Optional[int] = None) -> bool:
        """
        Called when left mouse button is pressed down.
        
        Used for starting grace note creation or editing existing grace notes.
        """
        super().on_left_press(x, y)
        
        # Clear any existing selection
        if hasattr(self.editor, 'selection_manager'):
            self.editor.selection_manager.clear_selection()
        
        # Guard: Prevent creating a new grace note if one is already being edited
        if self.edit_gracenote is not None:
            print(f"GraceNoteTool: Ignoring duplicate on_left_press (gracenote {self.edit_gracenote.id} already being edited)")
            return True
        
        # Check if we clicked on an existing grace note
        element, elem_type, stave_idx = self.get_element_at_position(x, y, element_types=['graceNote'])

        if element and elem_type == 'graceNote':
            # EDIT MODE: Start editing existing grace note
            self.edit_gracenote = element
            self.edit_stave_idx = stave_idx
            
            # Redraw in 'edit' mode for visual feedback
            self.editor._draw_single_gracenote(stave_idx, self.edit_gracenote, draw_mode='edit')
            
            print(f"GraceNoteTool: Editing gracenote {element.id} from stave {stave_idx}")
        else:
            # CREATE MODE: Start creating new grace note
            pitch, time = self.get_pitch_and_time(x, y)
            
            # Clamp time to valid range
            score_length = self.editor.get_score_length_in_ticks()
            if time > score_length:
                time = score_length
            if time < 0:
                time = 0
            
            # Get stave index
            stave_idx = self.score.fileSettings.get_rendered_stave_index(
                num_staves=len(self.score.stave)
            )
            
            # Create new grace note using auto-generated factory method
            self.edit_gracenote = self.score.new_grace_note(
                stave_index=stave_idx,
                pitch=pitch,
                time=time
            )
            self.edit_stave_idx = stave_idx
            
            # Draw in 'edit' mode
            self.editor._draw_single_gracenote(stave_idx, self.edit_gracenote, draw_mode='edit')
            
            print(f"GraceNoteTool: Creating new gracenote {self.edit_gracenote.id} at pitch={pitch}, time={time}")
        
        return True
    
    def on_drag(self, x: float, y: float, start_x: float, start_y: float) -> bool:
        """Called continuously while dragging WITH button pressed."""
        if self.edit_gracenote is None:
            return False
        
        # Update grace note position
        pitch, time = self.get_pitch_and_time(x, y)
        
        # Clamp time to valid range
        score_length = self.editor.get_score_length_in_ticks()
        if time > score_length:
            time = score_length
        if time < 0:
            time = 0
        
        # Update grace note
        self.edit_gracenote.pitch = pitch
        self.edit_gracenote.time = time
        
        # Redraw with updated position
        self.editor._draw_single_gracenote(self.edit_stave_idx, self.edit_gracenote, draw_mode='edit')
        
        return True
    
    def on_drag_end(self, x: float, y: float) -> bool:
        """Called when drag finishes (button released after dragging)."""
        if self.edit_gracenote is None:
            return False
        
        # Finalize grace note position
        pitch, time = self.get_pitch_and_time(x, y)
        
        # Clamp time to valid range
        score_length = self.editor.get_score_length_in_ticks()
        if time > score_length:
            time = score_length
        if time < 0:
            time = 0
        
        # Update grace note
        self.edit_gracenote.pitch = pitch
        self.edit_gracenote.time = time
        
        # Clear edit state
        self.edit_gracenote = None
        self.edit_stave_idx = None
        
        # Redraw everything
        self.editor.redraw_pianoroll()
        self.editor.on_modified()
        
        print(f"GraceNoteTool: Finalized gracenote")
        
        return True
    
    def on_left_unpress(self, x: float, y: float) -> bool:
        """Called when left mouse button is released without having dragged."""
        if self.edit_gracenote is None:
            return False
        
        # Clear edit state (note was created on press)
        self.edit_gracenote = None
        self.edit_stave_idx = None
        
        # Redraw everything
        self.editor.redraw_pianoroll()
        self.editor.on_modified()
        
        return True
    
    def on_right_click(self, x: float, y: float) -> bool:
        """Called when right mouse button is clicked (without drag)."""
        # Find grace note at position
        element, elem_type, stave_idx = self.get_element_at_position(x, y, element_types=['grace_note'])

        if element and elem_type == 'grace_note':
            # Delete the grace note
            stave = self.score.stave[stave_idx]
            # Event list attribute is camelCase 'graceNote'
            stave.event.graceNote.remove(element)
            
            # Redraw everything
            self.editor.redraw_pianoroll()
            self.editor.on_modified()
            
            print(f"GraceNoteTool: Deleted gracenote {element.id}")
            return True
        
        return False
    
    def _draw_cursor(self, gracenote: GraceNote, type: str = 'cursor') -> None:
        """Draw cursor grace note preview."""
        if not self.score:
            return
        
        # Get current stave index
        stave_idx = self.score.fileSettings.get_rendered_stave_index(
            num_staves=len(self.score.stave)
        )
        
        # Draw using the drawer mixin
        self.editor._draw_single_gracenote(stave_idx, gracenote, draw_mode=type)
