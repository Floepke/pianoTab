"""
Note Tool - Add, edit, and remove notes.
"""

from editor.tool.base_tool import BaseTool
from file.note import Note
from typing import Optional, Literal


class NoteTool(BaseTool):
    """Tool for adding and editing notes."""
    
    def __init__(self, editor):
        super().__init__(editor)
        self.hand_cursor = '<'  # Default to left hand
        self.edit_note = None  # Note being created/edited during drag
    
    @property
    def name(self) -> str:
        return "Note"
    
    @property
    def cursor(self) -> str:
        return 'crosshair'
    
    def on_activate(self):
        """Called when this tool becomes active."""
        super().on_activate()
        # Reset to default hand
        self.hand_cursor = '<'
    
    def on_deactivate(self):
        """Called when switching away from this tool."""
        super().on_deactivate()
    
    def on_key_press(self, key: str, x: float, y: float) -> bool:
        """Handle key press events."""
        if key == 'left':
            self.hand_cursor = '<'
            # Redraw cursor at current mouse position
            pitch, time = self.get_pitch_and_time(x, y)
            cursor = Note(time=time, pitch=pitch, hand=self.hand_cursor)
            self._draw_note_cursor(cursor, type='cursor')
            return True  # We handled this key
        elif key == 'right':
            self.hand_cursor = '>'
            # Redraw cursor at current mouse position
            pitch, time = self.get_pitch_and_time(x, y)
            cursor = Note(time=time, pitch=pitch, hand=self.hand_cursor)
            self._draw_note_cursor(cursor, type='cursor')
            return True  # We handled this key
        
        return False  # We didn't handle this key
    
    def on_mouse_move(self, x: float, y: float) -> bool:
        """Handle mouse movement (hover, no buttons pressed)."""
        # Call parent first - handles time cursor and drag detection
        if super().on_mouse_move(x, y):
            return True  # Parent is handling drag - stop here
        
        # draw note cursor using current hand setting
        pitch, time = self.get_pitch_and_time(x, y)
        cursor = Note(time=time, pitch=pitch, hand=self.hand_cursor)
        
        # redraw cursor
        self._draw_note_cursor(cursor, type='cursor')
        
        return False
    
    
    def on_left_click(self, x: float, y: float) -> bool:
        """Called when left mouse button is clicked (pressed and released without dragging)."""
        # TODO: Add a new note at the clicked position
        print(f"NoteTool: Add note at ({x}, {y})")
        
        # Example implementation:
        # tick = self.editor.x_to_tick(x)
        # key, stave = self.editor.y_to_key_and_stave(y)
        # note = Note(tick=tick, key=key, ...)
        # self.score.add_note(note)
        # self.refresh_canvas()
        
        return True
    
    def on_left_press(self, x: float, y: float, item_id: Optional[int] = None) -> bool:
        """Called when left mouse button is pressed down."""
        super().on_left_press(x, y)
        
        # Get position
        pitch, time = self.get_pitch_and_time(x, y)
        
        # Create new note using SCORE's factory method
        self.edit_note = self.editor.score.new_note(
            stave_idx=0,  # TODO: determine correct stave
            time=time,
            pitch=pitch,
            hand=self.hand_cursor,
            duration=self.editor.grid_selector.get_grid_step(),  # Default quarter note
            velocity=100
        )
        
        # Draw in 'select/edit' mode
        self.editor._draw_single_note(0, self.edit_note, draw_mode='select/edit')

        # delete any existing cursor drawing
        self.editor.canvas.delete_by_tag('cursor')
        
        return True

    def on_drag(self, x: float, y: float, start_x: float, start_y: float) -> bool:
        """Called continuously while dragging."""
        if self.edit_note is None:
            return False
        
        # get mouse position
        pitch, time = self.get_pitch_and_time(x, y)

        # specific editor mouse behavior
        self.edit_note.duration = max(self.editor.grid_selector.get_grid_step(), time - self.edit_note.time)
        if time < self.edit_note.time or y < self.editor.editor_margin: 
            # we edit the pitch in this case
            self.edit_note.pitch = pitch
        
        # Redraw in 'select/edit' mode
        self.editor._draw_single_note(0, self.edit_note, draw_mode='select/edit')

        # delete any existing cursor drawing
        self.editor.canvas.delete_by_tag('cursor')
        
        return True

    def on_left_release(self, x: float, y: float) -> bool:
        """Called when left mouse button is released."""
        super().on_left_release(x, y)
        
        if self.edit_note is None:
            return False
        
        # Delete 'select/edit' drawing and redraw as 'note'
        self.editor.canvas.delete_by_tag('select/edit')
        self.editor._draw_single_note(0, self.edit_note, draw_mode='note')
        
        # Mark as modified
        if hasattr(self.editor, 'on_modified') and self.editor.on_modified:
            self.editor.on_modified()
        
        # Clear reference
        self.edit_note = None
        
        return True
    
    def on_right_click(self, x: float, y: float) -> bool:
        """Called when right mouse button is clicked."""
        
        # delete any existing cursor drawing
        self.editor.canvas.delete_by_tag('cursor')

        # Check if we clicked on an existing note
        element, elem_type, stave_idx = self.get_element_at_position(x, y, element_types=['note'])
        
        if element and elem_type == 'note':
            # Found a note to delete
            print(f"NoteTool: Deleting note {element.id} from stave {stave_idx}")
            
            # Remove from SCORE
            if stave_idx is not None and stave_idx < len(self.editor.score.stave):
                stave = self.editor.score.stave[stave_idx]
                if hasattr(stave.event, 'note') and element in stave.event.note:
                    stave.event.note.remove(element)
                    
                    # Delete the visual representation
                    self.editor.canvas.delete_by_tag(str(element.id))
                    
                    # Mark as modified
                    if hasattr(self.editor, 'on_modified') and self.editor.on_modified:
                        self.editor.on_modified()
                    
                    print(f"NoteTool: Note {element.id} deleted successfully")
                    return True
            
            print(f"NoteTool: Failed to delete note {element.id}")
            return False
        
        # No note found at click position
        print(f"NoteTool: No note found at ({x}, {y})")
        return False
    
    def on_double_click(self, x: float, y: float) -> bool:
        """Called when mouse is double-clicked."""
        # TODO: Edit note properties on double-click
        print(f"NoteTool: Edit note at ({x}, {y})")
        return False
    
    def on_drag_start(self, x: float, y: float, start_x: float, start_y: float) -> bool:
        """Called when drag first starts (mouse moved beyond threshold with button down)."""
        # TODO: Initialize drag operation
        print(f"NoteTool: Start drag from ({start_x}, {start_y}) to ({x}, {y})")
        return False
    
    def on_drag_end(self, x: float, y: float) -> bool:
        """Called when drag finishes (button released after dragging)."""
        # TODO: Finalize drag operation
        print(f"NoteTool: End drag at ({x}, {y})")
        return False
    
    def _draw_note_cursor(self, cursor: Note, type: Optional[Literal['note', 'cursor', 'selected/edit']] = 'cursor'):
        """Draw a note cursor at the given position."""
        self.editor.canvas.delete_by_tag('cursor')
        self.editor._draw_single_note(0, cursor, draw_mode=type)

    